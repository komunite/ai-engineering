# Dialogue State Tracking

> "I want a cheap restaurant in the north... actually make it moderate... and add Italian." Üç tur, üç state güncellemesi. DST, slot-value dict'ini senkronize tutar, böylece rezervasyon çalışır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 17 (Chatbot'lar), Faz 5 · 20 (Yapılı Çıktılar)
**Süre:** ~75 dakika

## Sorun

Görev odaklı bir diyalog sisteminde, kullanıcının amacı slot-value çiftlerinin bir seti olarak encode edilir: `{cuisine: italian, area: north, price: moderate}`. Her kullanıcı turu bir slot ekleyebilir, değiştirebilir ya da kaldırabilir. Sistem tüm konuşmayı okumak ve mevcut state'i doğru çıkarmak zorundadır.

Tek bir slot'u yanlış yap, sistem yanlış restoranı rezerve eder, yanlış uçuşu zamanlar ya da yanlış kartı çeker. DST kullanıcının söylediği ile arka ucun çalıştırdığı arasındaki menteşedir.

LLM'lere rağmen 2026'da neden hâlâ önemli:

- Compliance-duyarlı alanlar (bankacılık, sağlık, havayolu rezervasyonu) serbest formlu üretim değil, deterministik slot değerleri gerektirir.
- Tool-use agent'ları hâlâ API çağırmadan önce slot çözümlemesine ihtiyaç duyar.
- Multi-turn düzeltme göründüğünden daha zordur: "actually no, make it Thursday."

Modern pipeline: klasik DST kavramları + LLM extractor'lar + yapılı çıktı guardrail'ları.

## Kavram

![DST: dialog geçmişi → slot-value state](../assets/dst.svg)

**Görev yapısı.** Bir şema domain'leri (restaurant, hotel, taxi) ve slot'larını (cuisine, area, price, people) tanımlar. Her slot boş olabilir, kapalı bir setten bir değerle doldurulabilir (price: {cheap, moderate, expensive}) ya da serbest formlu bir değer alabilir (name: "The Copper Kettle").

**İki DST formülasyonu.**

- **Sınıflandırma.** Her (slot, candidate_value) çifti için, evet/hayır tahmin et. Kapalı vocab slot'ları için çalışır. 2020 öncesi standart.
- **Üretim.** Diyalog verildiğinde, slot değerlerini serbest metin olarak üret. Açık vocab slot'ları için çalışır. Modern varsayılan.

**Metrik.** Joint Goal Accuracy (JGA) — *her* slot'un doğru olduğu turların oranı. Hep ya da hiç. MultiWOZ 2.4 leaderboard'u 2026'da ~%83 civarında.

**Mimariler.**

1. **Kural tabanlı (slot regex + anahtar kelime).** Dar alanlar için güçlü baseline. Debug edilebilir.
2. **TripPy / BERT-DST.** BERT encoding'li copy tabanlı üretim. LLM öncesi standart.
3. **LDST (LLaMA + LoRA).** Domain-slot prompting ile instruction-tuned LLM. MultiWOZ 2.4'te ChatGPT seviyesi kaliteye ulaşır.
4. **Ontology-free (2024–26).** Şemayı atla; slot adlarını ve değerleri doğrudan üret. Açık alanları ele alır.
5. **Prompt + yapılı çıktı (2024–26).** Pydantic şema + kısıtlı decoding ile LLM. 5 satır kod, üretim hazır.

### Klasik başarısızlık modları

- **Turlar arası co-reference.** "Let's stay with the first option." Hangi seçeneği çözümlemesi gerekir.
- **Üzerine yazma vs ekleme.** Kullanıcı "add Italian" diyor. Cuisine'i değiştirir misin yoksa ekler misin?
- **Örtük onaylar.** "OK cool" — bu sunulan rezervasyonu kabul etti mi?
- **Düzeltme.** "Actually make it 7 pm." Diğer slot'ları temizlemeden saati güncellemeli.
- **Önceki sistem söyleyişine coreference.** "Yes, that one." Hangi "that"?

## İnşa Et

### Adım 1: kural tabanlı slot çıkarıcı

`code/main.py`'a bak. Regex + eş anlam sözlükleri dar alanlarda kanonik söyleyişlerin %70'ini kapsar:

```python
CUISINE_SYNONYMS = {
    "italian": ["italian", "pasta", "pizza", "italy"],
    "chinese": ["chinese", "chow mein", "noodles"],
}


def extract_cuisine(utterance):
    for canonical, synonyms in CUISINE_SYNONYMS.items():
        if any(syn in utterance.lower() for syn in synonyms):
            return canonical
    return None
```

Kanonik vocabulary dışında kırılgan. Deterministik slot onayları için çalışır.

### Adım 2: state güncelleme döngüsü

```python
def update_state(state, utterance):
    new_state = dict(state)
    for slot, extractor in SLOT_EXTRACTORS.items():
        value = extractor(utterance)
        if value is not None:
            new_state[slot] = value
    for slot in NEGATION_CLEARS:
        if is_negated(utterance, slot):
            new_state[slot] = None
    return new_state
```

Üç invariant:

- Kullanıcının dokunmadığı bir slot'u asla resetleme.
- Açık olumsuzluk ("never mind the cuisine") temizlemeli.
- Kullanıcı düzeltmesi ("actually...") üzerine yazmalı, eklememeli.

### Adım 3: yapılı çıktıyla LLM güdümlü DST

```python
from pydantic import BaseModel
from typing import Literal, Optional
import instructor

class RestaurantState(BaseModel):
    cuisine: Optional[Literal["italian", "chinese", "indian", "thai", "any"]] = None
    area: Optional[Literal["north", "south", "east", "west", "center"]] = None
    price: Optional[Literal["cheap", "moderate", "expensive"]] = None
    people: Optional[int] = None
    day: Optional[str] = None


def llm_dst(history, llm):
    prompt = f"""You track the slot values of a restaurant booking across turns.
Dialogue so far:
{render(history)}

Update the state based on the latest user turn. Output only the JSON state."""
    return llm(prompt, response_model=RestaurantState)
```

Instructor + Pydantic geçerli bir state nesnesi garantiler. Regex yok, şema uyumsuzlukları yok, halüsinasyon slot'ları yok.

### Adım 4: JGA değerlendirmesi

```python
def joint_goal_accuracy(predicted_states, gold_states):
    correct = sum(1 for p, g in zip(predicted_states, gold_states) if p == g)
    return correct / len(predicted_states)
```

Kalibre et: turların yüzde kaçında sistem TÜM slot'ları doğru alıyor? MultiWOZ 2.4 için, 2026'nın üst sistemleri: %80-83. Senin in-domain sistemin dar vocabulary'nde bunu aşmalı yoksa LLM baseline'ı seni yener.

### Adım 5: düzeltmeyi ele alma

```python
CORRECTION_CUES = {"actually", "no wait", "on second thought", "change that to"}


def is_correction(utterance):
    return any(cue in utterance.lower() for cue in CORRECTION_CUES)
```

Tespit edilen bir düzeltmede, eklemek yerine son-güncellenen slot'un üzerine yaz. LLM yardımı olmadan doğru yapmak zordur. Modern desen: LLM'in artımlı güncelleme yerine her zaman tüm state'i geçmişten yeniden üretmesine izin ver — bu doğal olarak düzeltmeleri ele alır.

## Tuzaklar

- **Tam geçmiş yeniden üretim maliyeti.** LLM'in her tur state'i yeniden üretmesine izin vermek toplam O(n²) token'a mal olur. Geçmişi kap ya da eski turları özetle.
- **Şema kayması.** Sonradan yeni slot'lar eklemek eski eğitim verisini bozar. Şemanı versiyonla.
- **Büyük-küçük harf duyarlılığı.** "Italian" vs "italian" vs "ITALIAN" — her yerde normalize et.
- **Örtük miras.** Kullanıcı önceden "for 4 people" belirttiyse, farklı bir saat için yeni bir istek people'ı temizlememeli. Her zaman tam geçmişi geç.
- **Serbest form vs kapalı set.** Adlar, saatler ve adresler serbest form slot'lar gerektirir; mutfaklar ve alanlar kapalıdır. Şemada her ikisini de karıştır.

## Kullan

2026 stack'i:

| Durum | Yaklaşım |
|-----------|----------|
| Dar alan (bir ya da iki niyet) | Kural tabanlı + regex |
| Geniş alan, etiketli veri var | LDST (MultiWOZ tarzı veride LLaMA + LoRA) |
| Geniş alan, etiket yok, üretim hazır | LLM + Instructor + Pydantic şema |
| Konuşulan / ses | ASR + normalizer + LLM-DST |
| Çok alanlı rezervasyon akışı | Domain başına Pydantic modelleriyle şema güdümlü LLM |
| Compliance duyarlı | Kural tabanlı birincil, onay akışıyla LLM fallback |

## Yayınla

`outputs/skill-dst-designer.md` olarak kaydet:

```markdown
---
name: dst-designer
description: Design a dialogue state tracker — schema, extractor, update policy, evaluation.
version: 1.0.0
phase: 5
lesson: 29
tags: [nlp, dialogue, task-oriented]
---

Given a use case (domain, languages, vocab openness, compliance needs), output:

1. Schema. Domain list, slots per domain, open vs closed vocabulary per slot.
2. Extractor. Rule-based / seq2seq / LLM-with-Pydantic. Reason.
3. Update policy. Regenerate-whole-state / incremental; correction handling; negation handling.
4. Evaluation. Joint Goal Accuracy on a held-out dialogue set, slot-level precision/recall, confusion on the hardest slot.
5. Confirmation flow. When to explicitly ask the user to confirm (destructive actions, low-confidence extractions).

Refuse LLM-only DST for compliance-sensitive slots without a rule-based secondary check. Refuse any DST that cannot roll back a slot on user correction. Flag schemas without version tags.
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki kural tabanlı state tracker'ı 3 slot için (cuisine, area, price) kur. 10 elle hazırlanmış diyalogda test et. JGA ölç.
2. **Orta.** Aynı veri seti Instructor + Pydantic + küçük bir LLM ile. JGA'yı karşılaştır. En zor turları incele.
3. **Zor.** İkisini de uygula ve yönlendir: kural tabanlı birincil, kural tabanlı güvenle <2 slot çıkardığında LLM fallback. Birleşik JGA'yı ve tur başına çıkarım maliyetini ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| DST | Dialogue state tracking | Diyalog turları boyunca slot-value dict'ini koru. |
| Slot | Kullanıcı niyetinin birimi | Arka ucun ihtiyaç duyduğu adlandırılmış parametre (cuisine, date). |
| Domain | Görev alanı | Restaurant, hotel, taxi — slot setleri. |
| JGA | Joint Goal Accuracy | Her slot'un doğru olduğu turların oranı. Hep ya da hiç. |
| MultiWOZ | Benchmark | Multi-domain WOZ veri seti; standart DST değerlendirmesi. |
| Ontology-free DST | Şema yok | Slot adları ve değerleri doğrudan üret, sabit liste yok. |
| Düzeltme | "Actually..." | Önceden doldurulmuş bir slot'un üzerine yazan tur. |

## İleri Okuma

- [Budzianowski et al. (2018). MultiWOZ — A Large-Scale Multi-Domain Wizard-of-Oz](https://arxiv.org/abs/1810.00278) — kanonik benchmark.
- [Feng et al. (2023). Towards LLM-driven Dialogue State Tracking (LDST)](https://arxiv.org/abs/2310.14970) — DST için LLaMA + LoRA instruction tuning.
- [Heck et al. (2020). TripPy — A Triple Copy Strategy for Value Independent Neural Dialog State Tracking](https://arxiv.org/abs/2005.02877) — copy tabanlı DST iş atı.
- [King, Flanigan (2024). Unsupervised End-to-End Task-Oriented Dialogue with LLMs](https://arxiv.org/abs/2404.10753) — EM tabanlı unsupervised TOD.
- [MultiWOZ leaderboard](https://github.com/budzianowski/multiwoz) — kanonik DST sonuçları.
