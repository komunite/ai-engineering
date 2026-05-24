# Natural Language Inference — Metinsel Entailment

> "t entails h", t'yi okuyan bir insanın h'nin doğru olduğu sonucuna varacağı anlamına gelir. NLI, entailment / contradiction / neutral'i tahmin etme görevidir. Yüzeyde sıkıcı, üretimde yük taşıyıcı.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 05 (Duygu Analizi), Faz 5 · 13 (Soru-Cevap)
**Süre:** ~60 dakika

## Sorun

Bir özetleyici kurdun. Bir özet üretti. Özetin halüsinasyon içermediğini nereden bilirsin?

Bir chatbot kurdun. "yes" cevapladı. Cevabın getirilen pasaj tarafından desteklendiğini nereden bilirsin?

10,000 haber makalesini topic'e göre sınıflandırman gerek. Eğitim etiketin yok. Bir modeli yeniden kullanabilir misin?

Üç problem de Natural Language Inference'a indirgenir. NLI sorar: bir premise `t` ve bir hipotez `h` verildiğinde, `h`, `t` tarafından entail ediliyor mu, çelişiyor mu, yoksa neutral (ilgisiz) mı?

- **Hallucination kontrolü:** `t` = kaynak belge, `h` = özet iddiası. Entailment değil = halüsinasyon.
- **Temellendirilmiş QA:** `t` = getirilen pasaj, `h` = üretilen cevap. Entailment değil = uydurma.
- **Zero-shot sınıflandırma:** `t` = belge, `h` = sözelleştirilmiş etiket ("This is about sports"). Entailment = tahmin edilen etiket.

Tek görev, üç üretim kullanımı. Her RAG değerlendirme framework'ünün altında bir NLI modeli göndermesinin sebebi budur.

## Kavram

![NLI: üç yönlü sınıflandırma, premise vs hipotez](../assets/nli.svg)

**Üç etiket.**

- **Entailment.** `t` → `h`. "The cat is on the mat", "There is a cat"i entail eder.
- **Contradiction.** `t` → ¬`h`. "The cat is on the mat", "There is no cat"i çelir.
- **Neutral.** İki yönde de çıkarım yok. "The cat is on the mat", "The cat is hungry"e neutral'dır.

**Mantıksal entailment değil.** NLI *natural* dil çıkarımıdır — tipik bir insan okurun çıkaracağı şey, katı mantık değil. "John walked his dog" NLI'da "John has a dog"u entail eder, ama katı birinci-mertebe mantık bunu yalnızca sahipliği aksiyomatize edersen kabul eder.

**Veri setleri.**

- **SNLI** (2015). 570k insan-anote pair, premise olarak resim altyazıları. Dar alan.
- **MultiNLI** (2017). 10 türde 433k çift. 2026'da standart eğitim corpus'u.
- **ANLI** (2019). Adversarial NLI. İnsanlar mevcut modelleri bozmak için özellikle tasarlanmış örnekler yazdı. Daha zor.
- **DocNLI, ConTRoL** (2020–21). Belge uzunluğunda premise'ler. Multi-hop ve uzun mesafeli çıkarımı test eder.

**Mimari.** Bir transformer encoder (BERT, RoBERTa, DeBERTa), `[CLS] premise [SEP] hypothesis [SEP]` okur. `[CLS]` temsili 3 yönlü bir softmax'a beslenir. MNLI'da eğit, held-out benchmark'larda değerlendir, in-distribution çiftlerde %90+ doğruluk al.

**NLI yoluyla zero-shot.** Bir belge ve aday etiketler verildiğinde, her etiketi bir hipoteze çevir ("This text is about sports"). Her biri için entailment olasılığını hesapla. Max'ı seç. Bu Hugging Face'in `zero-shot-classification` pipeline'ının arkasındaki mekanizmadır.

## İnşa Et

### Adım 1: önceden eğitilmiş bir NLI modeli çalıştır

```python
from transformers import pipeline

nli = pipeline("text-classification",
               model="facebook/bart-large-mnli",
               top_k=None)  # tüm etiketleri döndür; deprecated return_all_scores=True'yu değiştirir

premise = "The cat is sleeping on the couch."
hypothesis = "There is a cat in the room."

result = nli({"text": premise, "text_pair": hypothesis})[0]
print(result)
# [{'label': 'entailment', 'score': 0.97},
#  {'label': 'neutral', 'score': 0.02},
#  {'label': 'contradiction', 'score': 0.01}]
```

Üretim NLI için, `facebook/bart-large-mnli` ve `microsoft/deberta-v3-large-mnli` açık varsayılanlardır. DeBERTa-v3 leaderboard'lara hâkimdir.

### Adım 2: zero-shot sınıflandırma

```python
zs = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

text = "The stock market rallied after the central bank cut interest rates."
labels = ["finance", "sports", "politics", "technology"]

result = zs(text, candidate_labels=labels)
print(result)
# {'labels': ['finance', 'politics', 'technology', 'sports'],
#  'scores': [0.92, 0.05, 0.02, 0.01]}
```

Şablon varsayılan olarak "This example is about {label}."dir. `hypothesis_template` ile özelleştir. Eğitim verisi gerekmez. Fine-tuning yok. Kutudan çıkar çıkmaz çalışır.

### Adım 3: RAG için faithfulness kontrolü

```python
def is_faithful(answer, context, threshold=0.5):
    result = nli({"text": context, "text_pair": answer})[0]
    entail = next(s for s in result if s["label"] == "entailment")
    return entail["score"] > threshold
```

Bu RAGAS faithfulness'ın çekirdeğidir. Üretilen cevabı atomik iddialara böl. Her iddiayı getirilen bağlama karşı kontrol et. Entail eden oranı raporla.

### Adım 4: elle yapılmış NLI sınıflandırıcı (kavramsal)

`code/main.py`'a yalnızca stdlib oyuncak için bak: premise ve hipotez lexical örtüşme + olumsuzluk tespiti yoluyla karşılaştırılır. Transformer modellerle rekabetçi değil — ama görevin şeklini gösterir: iki metin girer, 3 yönlü etiket çıkar, loss = `{entail, contradict, neutral}` üzerinde cross-entropy.

## Tuzaklar

- **Yalnızca-hipotez kısayolları.** Modeller, "not", "nobody", "never" contradiction ile korele olduğu için SNLI'da yalnızca hipotezden ~%60'ta etiketi tahmin edebilir. Etiket sızıntısı tespiti için güçlü baseline.
- **Lexical örtüşme heuristic'i.** Subsequence heuristic'i ("her subsequence entail edilir") SNLI'yı geçer ama HANS/ANLI'da başarısız olur. Adversarial benchmark'lar kullan.
- **Belge uzunluğu bozulması.** Tek-cümle NLI modelleri belge uzunluğundaki premise'lerde 20+ F1 düşer. Uzun bağlam için DocNLI-eğitilmiş modeller kullan.
- **Zero-shot şablon duyarlılığı.** "This example is about {label}" vs "{label}" vs "The topic is {label}" doğruluğu 10+ puan sallayabilir. Şablonu ayarla.
- **Alan uyumsuzluğu.** MNLI genel İngilizce'de eğitilir. Hukuki, tıbbi ve bilimsel metin alana özgü NLI modelleri (örn. SciNLI, MedNLI) gerektirir.

## Kullan

2026 stack'i:

| Kullanım durumu | Model |
|---------|-------|
| Genel amaçlı NLI | `microsoft/deberta-v3-large-mnli` |
| Hızlı / edge | `cross-encoder/nli-deberta-v3-base` |
| Zero-shot sınıflandırma (hafif) | `facebook/bart-large-mnli` |
| Belge seviyesi NLI | `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` |
| Çok dilli | `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` |
| RAG'de halüsinasyon tespiti | RAGAS / DeepEval içindeki NLI katmanı |

2026 meta-deseni: NLI, metin anlamanın koli bandıdır. "A, B'yi destekliyor mu?" ya da "A, B ile çelişiyor mu?" gerektiğinde — başka bir LLM çağrısına uzanmadan önce NLI'a uzan.

## Yayınla

`outputs/skill-nli-picker.md` olarak kaydet:

```markdown
---
name: nli-picker
description: Pick an NLI model, label template, and evaluation setup for a classification / faithfulness / zero-shot task.
version: 1.0.0
phase: 5
lesson: 21
tags: [nlp, nli, zero-shot]
---

Given a use case (faithfulness check, zero-shot classification, document-level inference), output:

1. Model. Named NLI checkpoint. Reason tied to domain, length, language.
2. Template (if zero-shot). Verbalization pattern. Example.
3. Threshold. Entailment cutoff for the decision rule. Reason based on calibration.
4. Evaluation. Accuracy on held-out labeled set, hypothesis-only baseline, adversarial subset.

Refuse to ship zero-shot classification without a 100-example labeled sanity check. Refuse to use a sentence-level NLI model on document-length premises. Flag any claim that NLI solves hallucination — it reduces it; it does not eliminate it.
```

## Alıştırmalar

1. **Kolay.** `facebook/bart-large-mnli`'yi üç sınıfı da kapsayan elle hazırlanmış 20 (premise, hipotez, etiket) üçlüsü üzerinde çalıştır. Doğruluğu ölç. Adversarial "subsequence heuristic" tuzakları ("I did not eat the cake" vs "I ate the cake") ekle ve bozulup bozulmadığını gör.
2. **Orta.** 100 AG News başlığında zero-shot şablon `"This text is about {label}"`'i `"The topic is {label}"` ve `"{label}"`'a karşı karşılaştır. Doğruluk salınımını raporla.
3. **Zor.** Bir RAG faithfulness denetçisi kur: atomik-iddia ayrıştırma + iddia başına NLI. Gold bağlamla 50 RAG-üretimi cevap üzerinde değerlendir. El etiketlerine karşı false-positive ve false-negative oranlarını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| NLI | Natural Language Inference | Premise-hipotez ilişkisinin 3 yönlü sınıflandırılması. |
| RTE | Recognizing Textual Entailment | NLI için eski isim; aynı görev. |
| Entailment | "t, h'yi içeriyor" | Tipik bir okur t verildiğinde h'nin doğru olduğu sonucuna varır. |
| Contradiction | "t, h'yi dışlıyor" | Tipik bir okur t verildiğinde h'nin yanlış olduğu sonucuna varır. |
| Neutral | "kararsız" | t'den h'ye iki yönde de çıkarım yok. |
| Zero-shot sınıflandırma | Sınıflandırıcı olarak NLI | Etiketleri hipotez olarak sözelleştir, max entailment'i seç. |
| Faithfulness | Cevap destekleniyor mu? | (getirilen bağlam, üretilen cevap) üzerinde NLI. |

## İleri Okuma

- [Bowman et al. (2015). A large annotated corpus for learning natural language inference](https://arxiv.org/abs/1508.05326) — SNLI.
- [Williams, Nangia, Bowman (2017). A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference](https://arxiv.org/abs/1704.05426) — MultiNLI.
- [Nie et al. (2019). Adversarial NLI](https://arxiv.org/abs/1910.14599) — ANLI benchmark'ı.
- [Yin, Hay, Roth (2019). Benchmarking Zero-shot Text Classification](https://arxiv.org/abs/1909.00161) — sınıflandırıcı olarak NLI.
- [He et al. (2021). DeBERTa: Decoding-enhanced BERT with Disentangled Attention](https://arxiv.org/abs/2006.03654) — 2026 NLI iş atı.
