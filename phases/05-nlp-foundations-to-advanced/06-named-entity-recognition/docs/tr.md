# Named Entity Recognition

> İsimleri çek. Belirsiz sınırlarla, iç içe varlıklarla ve alan jargonuyla uğraşana kadar kolay görünür.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 02 (BoW + TF-IDF), Faz 5 · 03 (Word Embedding'ler)
**Süre:** ~75 dakika

## Sorun

"Apple sued Google over its iPhone search deal in the US." Beş entity: Apple (ORG), Google (ORG), iPhone (PRODUCT), search deal (belki), US (GPE). İyi bir NER sistemi hepsini doğru tiplerle çıkarır. Kötü bir tanesi iPhone'u kaçırır, Apple'ı meyve ile Apple'ı şirket olarak karıştırır ve "US"i PERSON olarak etiketler.

NER her yapılı çıkarım pipeline'ının altındaki iş atıdır. CV ayrıştırma, compliance log tarama, tıbbi kayıt anonimleştirme, arama sorgusu anlama, chatbot yanıtları için grounding, hukuki sözleşme çıkarımı. Onu hiç tam göremezsin; her zaman ona bağımlısındır.

Bu ders klasik yolu (kural tabanlı, HMM, CRF) modern olana (BiLSTM-CRF, sonra transformer'lar) yürür. Her adım kendisinden öncekinin belirli bir sınırlamasını çözer. Desen, dersin kendisidir.

## Kavram

**BIO tagging** (ya da BILOU), entity çıkarımını sequence labeling problemine çevirir. Her token'ı `B-TYPE` (entity başlangıcı), `I-TYPE` (entity içinde) ya da `O` (herhangi bir entity'nin dışında) ile etiketle.

```
Apple    B-ORG
sued     O
Google   B-ORG
over     O
its      O
iPhone   B-PRODUCT
search   O
deal     O
in       O
the      O
US       B-GPE
.        O
```

Çoklu token entity'ler zincirlenir: `New B-GPE`, `York I-GPE`, `City I-GPE`. BIO'yu anlayan bir model rastgele span'lar çıkarabilir.

Mimari ilerleyişi:

- **Kural tabanlı.** Regex + gazetteer lookup'ları. Bilinen entity'lerde yüksek precision, yenilerinde sıfır kapsama.
- **HMM.** Hidden Markov Model. Tag verildiğinde token'ın emisyon olasılığı, tag-to-tag geçiş olasılığı. Viterbi decode. Etiketli veride eğitilir.
- **CRF.** Conditional Random Field. HMM gibi ama discriminative, böylece rastgele feature'lar (kelime şekli, büyük harf, komşu kelimeler) karıştırabilirsin. Düşük kaynaklı deploy'lar için 2026'da hâlâ klasik üretim iş atı.
- **BiLSTM-CRF.** El yapımı yerine sinirsel feature'lar. LSTM cümleyi her iki yönde okur, üstünde bir CRF katmanı tutarlı tag dizilerini dayatır.
- **Transformer tabanlı.** BERT'i bir token-classification head ile fine-tune et. En iyi doğruluk. En çok compute.

## İnşa Et

### Adım 1: BIO tagging yardımcıları

```python
def spans_to_bio(tokens, spans):
    labels = ["O"] * len(tokens)
    for start, end, label in spans:
        labels[start] = f"B-{label}"
        for i in range(start + 1, end):
            labels[i] = f"I-{label}"
    return labels


def bio_to_spans(tokens, labels):
    spans = []
    current = None
    for i, label in enumerate(labels):
        if label.startswith("B-"):
            if current:
                spans.append(current)
            current = (i, i + 1, label[2:])
        elif label.startswith("I-") and current and current[2] == label[2:]:
            current = (current[0], i + 1, current[2])
        else:
            if current:
                spans.append(current)
                current = None
    if current:
        spans.append(current)
    return spans
```

```python
>>> tokens = ["Apple", "sued", "Google", "over", "iPhone", "sales", "."]
>>> labels = ["B-ORG", "O", "B-ORG", "O", "B-PRODUCT", "O", "O"]
>>> bio_to_spans(tokens, labels)
[(0, 1, 'ORG'), (2, 3, 'ORG'), (4, 5, 'PRODUCT')]
```

### Adım 2: el yapımı feature'lar

Klasik (sinirsel olmayan) NER için, feature'lar oyunun kendisidir. Kullanışlı olanlar:

```python
def token_features(token, prev_token, next_token):
    return {
        "lower": token.lower(),
        "is_upper": token.isupper(),
        "is_title": token.istitle(),
        "has_digit": any(c.isdigit() for c in token),
        "suffix_3": token[-3:].lower(),
        "shape": word_shape(token),
        "prev_lower": prev_token.lower() if prev_token else "<BOS>",
        "next_lower": next_token.lower() if next_token else "<EOS>",
    }


def word_shape(word):
    out = []
    for c in word:
        if c.isupper():
            out.append("X")
        elif c.islower():
            out.append("x")
        elif c.isdigit():
            out.append("d")
        else:
            out.append(c)
    return "".join(out)
```

`word_shape("iPhone")` `xXxxxx` döndürür. `word_shape("USA-2024")` `XXX-dddd` döndürür. Büyük harf desenleri özel isimler için yüksek sinyaldir.

### Adım 3: basit kural tabanlı + sözlük baseline'ı

```python
ORG_GAZETTEER = {"Apple", "Google", "Microsoft", "OpenAI", "Meta", "Amazon", "Netflix"}
GPE_GAZETTEER = {"US", "USA", "UK", "India", "Germany", "France"}
PRODUCT_GAZETTEER = {"iPhone", "Android", "Windows", "ChatGPT", "Claude"}


def rule_based_ner(tokens):
    labels = []
    for token in tokens:
        if token in ORG_GAZETTEER:
            labels.append("B-ORG")
        elif token in GPE_GAZETTEER:
            labels.append("B-GPE")
        elif token in PRODUCT_GAZETTEER:
            labels.append("B-PRODUCT")
        else:
            labels.append("O")
    return labels
```

Üretim gazetteer'ları Wikipedia ve DBpedia'dan kazınmış milyonlarca girdiye sahiptir. Kapsama iyi. Disambiguation (`Apple` şirket vs meyve) berbat. Bu nedenle istatistiksel modeller kazandı.

### Adım 4: CRF adımı (taslak, tam impl değil)

50 satırda sıfırdan tam CRF, olasılık teorisi temelleri olmadan aydınlatıcı değil. Yerine `sklearn-crfsuite` kullan:

```python
import sklearn_crfsuite

def to_features(tokens):
    out = []
    for i, tok in enumerate(tokens):
        prev = tokens[i - 1] if i > 0 else ""
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        out.append({
            "word.lower()": tok.lower(),
            "word.isupper()": tok.isupper(),
            "word.istitle()": tok.istitle(),
            "word.isdigit()": tok.isdigit(),
            "word.suffix3": tok[-3:].lower(),
            "word.shape": word_shape(tok),
            "prev.word.lower()": prev.lower(),
            "next.word.lower()": nxt.lower(),
            "BOS": i == 0,
            "EOS": i == len(tokens) - 1,
        })
    return out


crf = sklearn_crfsuite.CRF(algorithm="lbfgs", c1=0.1, c2=0.1, max_iterations=100, all_possible_transitions=True)
X_train = [to_features(s) for s in sentences_tokenized]
crf.fit(X_train, bio_labels_train)
```

`c1` ve `c2` L1 ve L2 regularization'dır. `all_possible_transitions=True`, modelin yasadışı dizilerin (örneğin `O`'dan sonra `I-ORG`) muhtemel olmadığını öğrenmesine izin verir; bu, bir CRF'nin sen kısıtlamayı yazmadan BIO tutarlılığını nasıl dayattığıdır.

### Adım 5: BiLSTM-CRF neyi ekler

Feature'lar öğrenilmiş hale gelir. Girdiler: token embedding'leri (GloVe ya da fastText). LSTM soldan sağa ve sağdan sola okur. Birleştirilmiş hidden state'ler bir CRF çıktı katmanından geçer. CRF hâlâ tag dizisi tutarlılığını dayatır; LSTM el yapımı feature'ları öğrenilmiş olanlarla değiştirir.

```python
import torch
import torch.nn as nn


class BiLSTM_CRF_Head(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, n_labels):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, bidirectional=True, batch_first=True)
        self.fc = nn.Linear(hidden_dim * 2, n_labels)

    def forward(self, token_ids):
        e = self.embed(token_ids)
        h, _ = self.lstm(e)
        emissions = self.fc(h)
        return emissions
```

CRF katmanı için, `torchcrf.CRF` kullan (pip install pytorch-crf). El yapımı CRF üzerindeki kazanım ölçülebilir ama on binlerce etiketli cümlen olmadıkça beklediğinden daha küçük.

## Kullan

spaCy kutudan çıkar çıkmaz üretim seviyesi NER içerir.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Apple sued Google over its iPhone search deal in the US.")
for ent in doc.ents:
    print(f"{ent.text:20s} {ent.label_}")
```

```
Apple                ORG
Google               ORG
iPhone               ORG
US                   GPE
```

`iPhone`'un `PRODUCT` yerine `ORG` olarak etiketlendiğine dikkat et — spaCy'nin küçük modelinin ürün-entity kapsaması zayıftır. Büyük model (`en_core_web_lg`) daha iyi yapar. Transformer model (`en_core_web_trf`) daha da iyi yapar.

BERT tabanlı NER için Hugging Face:

```python
from transformers import pipeline

ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
print(ner("Apple sued Google over its iPhone in the US."))
```

```
[{'entity_group': 'ORG', 'word': 'Apple', ...},
 {'entity_group': 'ORG', 'word': 'Google', ...},
 {'entity_group': 'MISC', 'word': 'iPhone', ...},
 {'entity_group': 'LOC', 'word': 'US', ...}]
```

`aggregation_strategy="simple"` bitişik B-X, I-X token'larını bir span'a birleştirir. O olmadan token seviyesi etiketler alırsın ve kendin birleştirmek zorunda kalırsın.

### LLM tabanlı NER (2026 seçeneği)

Zero-shot ve few-shot LLM NER artık birçok alanda fine-tune edilmiş modellerle rekabetçi, etiketli veri kıt olduğunda ise dramatik biçimde daha iyi.

- **Zero-shot prompting.** LLM'e bir entity tip listesi ve örnek bir şema ver. JSON çıktı iste. Kutudan çıkar çıkmaz çalışır; doğruluk yeni alanlarda orta düzeydedir.
- **ZeroTuneBio tarzı prompting.** Görevi aday çıkarma → anlam açıklama → yargı → tekrar kontrol olarak ayrıştır. Çok aşamalı bir prompt (one-shot değil) biyomedikal NER'de doğruluğu önemli ölçüde yükseltir. Aynı desen hukuki, finansal ve bilimsel alanlarda çalışır.
- **RAG ile dinamik prompting.** Her çıkarım çağrısı için küçük bir etiketli tohum setinden en benzer etiketli örnekleri getir; few-shot prompt'u anlık olarak kur. 2026 benchmark'larında bu, GPT-4 biyomedikal NER F1'ini statik prompting'in üstünde %11-12 yükseltir.
- **Entity tipi başına ayrıştırma.** Uzun belgeler için, tüm entity tiplerini tek seferde çıkaran tek bir çağrı uzunluk arttıkça recall kaybeder. Entity tipi başına bir çıkarım pass'i çalıştır. Daha yüksek çıkarım maliyeti, önemli ölçüde daha yüksek doğruluk. Bu klinik notlar ve hukuki sözleşmeler için standart desendir.

2026 itibarıyla üretim önerisi: eğitim verisi toplamadan önce bir LLM zero-shot baseline ile başla. Çoğu zaman F1 yeterince iyidir, asla fine-tune'a ihtiyacın olmaz.

### Klasik NER hâlâ ne zaman kazanır

LLM'ler mevcut olsa bile, klasik NER kazanır:

- Latency bütçesi 50ms'nin altındaysa.
- Binlerce etiketli örneğin varsa ve %98+ F1'e ihtiyacın varsa.
- Alan, önceden eğitilmiş bir CRF ya da BiLSTM'in iyi transfer ettiği stabil bir ontoloji'ye sahipse.
- Düzenleyici kısıtlamalar on-prem, non-generative bir model gerektiriyorsa.

### Nerede dağılır

- **Domain shift.** CoNLL'da eğitilmiş NER, hukuki sözleşmelerde bir gazetteer'dan daha kötü performans gösterir. Kendi alanında fine-tune et.
- **İç içe entity'ler.** "Bank of America Tower" aynı anda hem ORG hem FACILITY'dir. Standart BIO örtüşen span'ları temsil edemez. Nested NER'e (multi-pass ya da span tabanlı modeller) ihtiyacın var.
- **Uzun entity'ler.** "United States Federal Deposit Insurance Corporation." Token seviyesi modeller bazen bunu böler. `aggregation_strategy` kullan ya da post-process et.
- **Seyrek tipler.** DRUG_BRAND, ADVERSE_EVENT, DOSE gibi tıbbi NER etiketleri. Genel amaçlı modellerin fikri yoktur. Scispacy ve BioBERT orada başlangıç noktalarıdır.

## Yayınla

`outputs/skill-ner-picker.md` olarak kaydet:

```markdown
---
name: ner-picker
description: Pick the right NER approach for a given extraction task.
version: 1.0.0
phase: 5
lesson: 06
tags: [nlp, ner, extraction]
---

Given a task description (domain, label set, language, latency, data volume), output:

1. Approach. Rule-based + gazetteer, CRF, BiLSTM-CRF, or transformer fine-tune.
2. Starting model. Name it (spaCy model ID, Hugging Face checkpoint ID, or "custom, trained from scratch").
3. Labeling strategy. BIO, BILOU, or span-based. Justify in one sentence.
4. Evaluation. Use `seqeval`. Always report entity-level F1 (not token-level).

Refuse to recommend fine-tuning a transformer for under 500 labeled examples unless the user already has a pretrained domain model. Flag nested entities as needing span-based or multi-pass models. Require a gazetteer audit if the user mentions "production scale" and labels are unchanged from CoNLL-2003.
```

## Alıştırmalar

1. **Kolay.** `bio_to_spans`'i (`spans_to_bio`'nun tersi) uygula ve 10 cümlede gidiş-dönüş tutarlılığını doğrula.
2. **Orta.** Yukarıdaki sklearn-crfsuite CRF'sini CoNLL-2003 İngilizce NER veri setinde eğit. `seqeval` kullanarak entity başına F1 raporla. Tipik sonuç: ~84 F1.
3. **Zor.** `distilbert-base-cased`'i alana özgü bir NER veri setinde (tıbbi, hukuki ya da finansal) fine-tune et. spaCy küçük modeline karşı karşılaştır. Veri sızıntısı kontrollerini belgele ve seni neyin şaşırttığını yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| NER | İsimleri çıkar | Token span'larını tiplerle etiketle (PERSON, ORG, GPE, DATE, ...). |
| BIO | Etiketleme şeması | `B-X` başlatır, `I-X` devam ettirir, `O` dışında. |
| BILOU | Daha iyi BIO | Daha temiz sınırlar için `L-X` (son), `U-X` (birim) ekler. |
| CRF | Yapılı sınıflandırıcı | Yalnızca emisyonları değil etiketler arası geçişleri de modeller. Geçerli dizileri dayatır. |
| Nested NER | Örtüşen entity'ler | Bir span, alt-span'ından farklı bir entity'dir. BIO bunu ifade edemez. |
| Entity seviyesi F1 | Doğru NER metriği | Tahmin edilen span gerçek span'la tam eşleşmeli. Token seviyesi F1 doğruluğu abartır. |

## İleri Okuma

- [Lample et al. (2016). Neural Architectures for Named Entity Recognition](https://arxiv.org/abs/1603.01360) — BiLSTM-CRF makalesi. Kanonik.
- [Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805) — standart hale gelen token-classification desenini tanıtır.
- [spaCy linguistic features — named entities](https://spacy.io/usage/linguistic-features#named-entities) — `Doc.ents` ve `Span` üzerindeki her attribute için pratik referans.
- [seqeval](https://github.com/chakki-works/seqeval) — doğru metrik kütüphanesi. Her zaman kullan.
