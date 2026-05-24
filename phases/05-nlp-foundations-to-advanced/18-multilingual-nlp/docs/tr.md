# Çok Dilli NLP

> Tek model, 100+ dil, çoğu için sıfır eğitim verisi. Cross-lingual transfer 2020'lerin pratik mucizesidir.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 04 (GloVe, FastText, Subword), Faz 5 · 11 (Makine Çevirisi)
**Süre:** ~45 dakika

## Sorun

İngilizce'nin milyarlarca etiketli örneği var. Urduca'nın binlerce var. Maithili'nin neredeyse hiç yok. Küresel bir kitleye hizmet eden herhangi bir pratik NLP sistemi, göreve özgü eğitim verisi olmayan uzun kuyruktaki dillerde çalışmak zorundadır.

Çok dilli modeller bunu birçok dili aynı anda tek bir modelde eğiterek çözer. Paylaşılan temsil, modelin yüksek kaynaklı dillerde öğrendiği becerileri düşük kaynaklılara aktarmasını sağlar. Modeli İngilizce duygu analizi üzerinde fine-tune et, Urduca'da kutudan çıkar çıkmaz şaşırtıcı derecede iyi duygu tahminleri üretir. Bu zero-shot cross-lingual transfer'dir ve NLP'nin dünyaya nasıl gönderildiğini yeniden şekillendirdi.

Bu ders tradeoff'ları, kanonik modelleri ve çok dilli işe yeni başlayan ekipleri yoldan çıkaran tek kararı adlandırır: transfer için bir kaynak dil seçimi.

## Kavram

![Paylaşılan çok dilli embedding uzayı yoluyla cross-lingual transfer](../assets/multilingual.svg)

**Paylaşılan vocabulary.** Çok dilli modeller, tüm hedef dillerden gelen metin üzerinde eğitilmiş bir SentencePiece ya da WordPiece tokenleştiricisi kullanır. Vocabulary paylaşılır: aynı subword birimi ilgili diller arasında aynı morfemi temsil eder. İngilizce ve İtalyanca'daki `anti-` aynı token'ı alır.

**Paylaşılan temsil.** Birçok dil arasında masked language modeling üzerinde önceden eğitilmiş bir transformer, farklı dillerdeki semantik olarak benzer cümlelerin benzer hidden state'ler ürettiğini öğrenir. mBERT, XLM-R ve NLLB hepsi bunu sergiler. İngilizce'deki "cat" için embedding'ler Fransızca'daki "chat" ve İspanyolca'daki "gato"ya yakın kümelenir, tam cümle embedding'leri de öyle.

**Zero-shot transfer.** Modeli bir dilde etiketli veride (genellikle İngilizce) fine-tune et. Çıkarımda modelin desteklediği herhangi bir başka dilde çalıştır. Hedef dil etiketi gerekmez. Sonuçlar tipolojik olarak ilgili diller için güçlü, uzak olanlar için zayıftır.

**Few-shot fine-tuning.** Hedef dilde 100-500 etiketli örnek ekle. Sınıflandırma görevlerinde doğruluk İngilizce baseline'ının %95-98'ine sıçrar. Çok dilli NLP'deki tek başına en maliyet-etkin koldur.

## Modeller

| Model | Yıl | Kapsama | Notlar |
|-------|------|----------|-------|
| mBERT | 2018 | 104 dil | Wikipedia üzerinde eğitildi. İlk pratik çok dilli LM. Düşük kaynakta zayıf. |
| XLM-R | 2019 | 100 dil | CommonCrawl üzerinde eğitildi (Wikipedia'dan çok daha büyük). Cross-lingual baseline'ı kuruyor. Base 270M, Large 550M. |
| XLM-V | 2023 | 100 dil | 1M token vocabulary'li XLM-R (250k yerine). Düşük kaynakta daha iyi. |
| mT5 | 2020 | 101 dil | Çok dilli üretim için T5 mimarisi. |
| NLLB-200 | 2022 | 200 dil | Meta'nın çeviri modeli; 55 düşük-kaynaklı dil içeriyor. |
| BLOOM | 2022 | 46 dil + 13 programlama | Çok dilli olarak eğitilmiş açık 176B LLM. |
| Aya-23 | 2024 | 23 dil | Cohere'in çok dilli LLM'i. Arapça, Hintçe, Swahili'de güçlü. |

Kullanım durumuna göre seç. Sınıflandırma akıllı varsayılan olarak XLM-R-base ile iyi çalışır. Üretim görevleri çeviri vs açık üretim'e göre mT5 ya da NLLB çağırır. LLM tarzı iş açık çok dilli prompt'lama ile Aya-23 ya da Claude'la eşleşir.

## Kaynak dil kararı (2026 araştırması)

Çoğu ekip fine-tuning kaynağı olarak İngilizce'yi varsayılır. Son araştırma (2026) bunun sıklıkla yanlış olduğunu gösteriyor.

Dil benzerliği transfer kalitesini ham corpus boyutundan daha iyi tahmin ediyor. Slavik hedefler için, Almanca ya da Rusça sıklıkla İngilizce'yi yener. Indic hedefler için, Hintçe sıklıkla İngilizce'yi yener. **qWALS** benzerlik metriği (2026, World Atlas of Language Structures özelliklerine dayalı) bunu nicelleştirir. **LANGRANK** (Lin et al., ACL 2019), aday kaynak dilleri dilbilimsel benzerlik, corpus boyutu ve genetik akrabalığın bir kombinasyonundan sıralayan ayrı, daha erken bir yöntemdir.

Pratik kural: hedef dilinin tipolojik olarak yakın yüksek-kaynaklı bir akrabası varsa, önce o üzerinde fine-tune etmeyi dene, sonra İngilizce fine-tune ile karşılaştır.

## İnşa Et

### Adım 1: zero-shot cross-lingual sınıflandırma

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tok = AutoTokenizer.from_pretrained("joeddav/xlm-roberta-large-xnli")
model = AutoModelForSequenceClassification.from_pretrained("joeddav/xlm-roberta-large-xnli")


def classify(text, candidate_labels, hypothesis_template="This text is about {}."):
    scores = {}
    for label in candidate_labels:
        hypothesis = hypothesis_template.format(label)
        inputs = tok(text, hypothesis, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits[0]
        entail_score = torch.softmax(logits, dim=-1)[2].item()
        scores[label] = entail_score
    return dict(sorted(scores.items(), key=lambda x: -x[1]))


print(classify("I love this product!", ["positive", "negative", "neutral"]))
print(classify("मुझे यह उत्पाद पसंद है!", ["positive", "negative", "neutral"]))
print(classify("J'adore ce produit !", ["positive", "negative", "neutral"]))
```

Tek model, üç dil, aynı API. NLI verisi üzerinde eğitilmiş XLM-R, entailment numarası yoluyla sınıflandırmaya iyi transfer eder.

### Adım 2: çok dilli embedding uzayı

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

pairs = [
    ("The cat is sleeping.", "Le chat dort."),
    ("The cat is sleeping.", "El gato está durmiendo."),
    ("The cat is sleeping.", "Die Katze schläft."),
    ("The cat is sleeping.", "The dog is barking."),
]

for eng, other in pairs:
    emb_eng = model.encode([eng], normalize_embeddings=True)[0]
    emb_other = model.encode([other], normalize_embeddings=True)[0]
    sim = float(np.dot(emb_eng, emb_other))
    print(f"  {eng!r} <-> {other!r}: cos={sim:.3f}")
```

Çeviriler embedding uzayında yakın iniyor. Farklı bir İngilizce cümle daha uzağa iniyor. Cross-lingual retrieval, kümeleme ve benzerliği çalıştıran şey budur.

### Adım 3: few-shot fine-tuning stratejisi

```python
from transformers import TrainingArguments, Trainer
from datasets import Dataset


def few_shot_finetune(base_model, base_tokenizer, examples):
    ds = Dataset.from_list(examples)

    def tokenize_fn(ex):
        out = base_tokenizer(ex["text"], truncation=True, max_length=128)
        out["labels"] = ex["label"]
        return out

    ds = ds.map(tokenize_fn)
    args = TrainingArguments(
        output_dir="out",
        per_device_train_batch_size=8,
        num_train_epochs=5,
        learning_rate=2e-5,
        save_strategy="no",
    )
    trainer = Trainer(model=base_model, args=args, train_dataset=ds)
    trainer.train()
    return base_model
```

100-500 hedef-dil örneği için, `num_train_epochs=5` ve `learning_rate=2e-5` güvenli varsayılanlardır. Daha yüksek learning rate çok dilli hizalanmanın çökmesine sebep olur ve İngilizce-only bir model elde edersin.

## Gerçekten işe yarayan değerlendirme

- **Held-out setlerde dil başına doğruluk.** Toplanmamış. Toplam uzun kuyruğu saklar.
- **Monolingual baseline'a karşı benchmark.** Yeterli verisi olan diller için, sıfırdan eğitilmiş monolingual bir model bazen çok dilli olanı yener. Test et.
- **Entity seviyesi testler.** Hedef dilde named entity'ler. Çok dilli modeller sıklıkla Latin'den uzak script'ler için zayıf tokenleştirmeye sahiptir.
- **Cross-lingual tutarlılık.** İki dilde aynı anlam aynı tahmini üretmeli. Açığı ölç.

## Kullan

2026 stack'i:

| Görev | Önerilen |
|-----|-------------|
| Sınıflandırma, 100 dil | Fine-tune edilmiş XLM-R-base (~270M) |
| Zero-shot metin sınıflandırma | `joeddav/xlm-roberta-large-xnli` |
| Çok dilli cümle embedding'leri | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Çeviri, 200 dil | `facebook/nllb-200-distilled-600M` (bkz ders 11) |
| Generative çok dilli | Claude, GPT-4, Aya-23, mT5-XXL |
| Düşük kaynaklı dil NLP | XLM-V ya da ilgili yüksek-kaynaklı dilde alana özgü fine-tune |

Performans önemliyse her zaman hedef dilde fine-tuning için bütçe ayır. Zero-shot bir başlangıç noktasıdır, nihai cevap değil.

### Tokenleştirme vergisi (düşük kaynaklı diller için ne ters gider)

Çok dilli modeller tüm dilleri arasında bir tokenleştiriciyi paylaşır. O vocabulary İngilizce, Fransızca, İspanyolca, Çince, Almanca'nın hâkim olduğu bir corpus üzerinde eğitilir. Baskın setin dışındaki herhangi bir dil için, üç vergi sessizce birikir:

- **Fertility vergisi.** Düşük kaynaklı dil metni, İngilizce'den kelime başına çok daha fazla token'a tokenleşir. Bir Hintçe cümlesi eşdeğer bir İngilizce cümleden 3-5 kat daha fazla token'a ihtiyaç duyabilir. O 3-5 kat bağlam pencereni, eğitim verimliliğini ve latency'yi yer.
- **Varyant kurtarma vergisi.** Her yazım hatası, diacritic varyantı, Unicode normalizasyon uyumsuzluğu ya da büyük-küçük harf varyasyonu embedding uzayında soğuk başlangıçlı ilgisiz bir dizi haline gelir. Model, ana dili konuşan birinin açık aldığı ortografik karşılıkları öğrenemez.
- **Kapasite taşma vergisi.** 1 ve 2'nci vergiler bağlam pozisyonlarını, katman derinliğini ve embedding boyutlarını tüketir. Gerçek mantık yürütme için kalan sistematik olarak yüksek kaynaklı bir dilin aynı modelden aldığından daha küçüktür.

Pratik semptom: modelin Hintçe'de normal eğitilir, loss eğrisi doğru görünür, eval perplexity makul görünür ve üretim çıktıları incelikle yanlış olur. Morfoloji cümle ortasında çöker. Nadir çekimler kurtarılamaz kalır. **Bozuk bir tokenleştiriciden veri ölçeklendirme yoluyla çıkamazsın.**

Azaltımlar: hedef dilin için iyi kapsamı olan bir tokenleştirici seç (XLM-V'nin 1M token vocabulary'si doğrudan bir düzeltme); eğitimden önce held-out hedef metinde tokenleştirme fertility'sini doğrula; gerçek uzun kuyruk script'leri için byte seviyesi fallback (SentencePiece `byte_fallback=True`, GPT-2 tarzı byte-level BPE) kullan, böylece hiçbir şey asla OOV olmaz.

## Yayınla

`outputs/skill-multilingual-picker.md` olarak kaydet:

```markdown
---
name: multilingual-picker
description: Pick source language, target model, and evaluation plan for a multilingual NLP task.
version: 1.0.0
phase: 5
lesson: 18
tags: [nlp, multilingual, cross-lingual]
---

Given requirements (target languages, task type, available labeled data per language), output:

1. Source language for fine-tuning. Default English; check LANGRANK or qWALS if target language has a typologically close high-resource language.
2. Base model. XLM-R (classification), mT5 (generation), NLLB (translation), Aya-23 (generative LLM).
3. Few-shot budget. Start with 100-500 target-language examples if available. Zero-shot only if labeling is infeasible.
4. Evaluation plan. Per-language accuracy (not aggregate), cross-lingual consistency, entity-level F1 on non-Latin scripts.

Refuse to ship a multilingual model without per-language evaluation — aggregate metrics hide long-tail failures. Flag scripts with low tokenization coverage (Amharic, Tigrinya, many African languages) as needing a model with byte-fallback (SentencePiece with byte_fallback=True, or byte-level tokenizer like GPT-2).
```

## Alıştırmalar

1. **Kolay.** İngilizce, Fransızca, Hintçe ve Arapça'da dil başına 10 cümle üzerinde zero-shot sınıflandırma pipeline'ını çalıştır. Her birinde doğruluğu raporla. Güçlü Fransızca, makul Hintçe, değişken Arapça görmelisin.
2. **Orta.** Küçük bir karışık dilli corpus üzerinde cross-lingual retriever kurmak için `paraphrase-multilingual-MiniLM-L12-v2` kullan. İngilizce'de sorgu yap, herhangi bir dilde belge al. Recall@5'i ölç.
3. **Zor.** Bir Hintçe sınıflandırma görevi için İngilizce-kaynak ve Hintçe-kaynak fine-tuning'i karşılaştır. Her iki rejim altında few-shot fine-tuning için 500 hedef-dil örneği kullan. Hangi kaynağın daha iyi Hintçe doğruluğu ürettiğini ve ne kadar olduğunu raporla. Bu minyatürde LANGRANK tezidir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Çok dilli model | Tek model, birçok dil | Diller arası paylaşılan vocabulary ve parametreler. |
| Cross-lingual transfer | Bir dilde eğit, başka birinde çalıştır | Kaynakta fine-tune et, hedef-dil etiketleri olmadan hedefte değerlendir. |
| Zero-shot | Hedef-dil etiketi yok | Hedef dilde fine-tuning olmadan transfer. |
| Few-shot | Küçük hedef etiketler | Fine-tuning için kullanılan 100-500 hedef-dil örneği. |
| mBERT | İlk çok dilli LM | Wikipedia üzerinde önceden eğitilmiş 104-dilli BERT. |
| XLM-R | Standart cross-lingual baseline | CommonCrawl üzerinde önceden eğitilmiş 100-dilli RoBERTa. |
| NLLB | Meta'nın 200-dilli MT'si | No Language Left Behind. 55 düşük kaynaklı dil içerir. |

## İleri Okuma

- [Conneau et al. (2019). Unsupervised Cross-lingual Representation Learning at Scale](https://arxiv.org/abs/1911.02116) — XLM-R makalesi.
- [Pires, Schlinger, Garrette (2019). How Multilingual is Multilingual BERT?](https://arxiv.org/abs/1906.01502) — cross-lingual transfer araştırma hattını başlatan analiz makalesi.
- [Costa-jussà et al. (2022). No Language Left Behind](https://arxiv.org/abs/2207.04672) — NLLB-200 makalesi.
- [Üstün et al. (2024). Aya Model: An Instruction Finetuned Open-Access Multilingual Language Model](https://arxiv.org/abs/2402.07827) — Aya, Cohere'in çok dilli LLM'i.
- [Language Similarity Predicts Cross-Lingual Transfer Learning Performance (2026)](https://www.mdpi.com/2504-4990/8/3/65) — qWALS / LANGRANK kaynak dil makalesi.
