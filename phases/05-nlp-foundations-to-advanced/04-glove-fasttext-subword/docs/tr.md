# GloVe, FastText ve Subword Embedding'ler

> Word2Vec kelime başına bir embedding eğitti. GloVe co-occurrence matrisini faktorize etti. FastText parçaları gömdü. BPE transformer'lara köprü oldu.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 03 (Sıfırdan Word2Vec)
**Süre:** ~45 dakika

## Sorun

Word2Vec iki açık soru bıraktı.

Birincisi, online skip-gram güncellemeleri yerine doğrudan co-occurrence matrisini faktorize eden paralel bir araştırma hattı vardı (LSA, HAL). Word2Vec'in yinelemeli yaklaşımı temelde daha mı iyiydi, yoksa fark iki yöntemin sayımları ele alış biçiminin bir yan ürünü müydü? **GloVe** bunu cevapladı: dikkatle seçilmiş bir loss ile matris faktorizasyonu Word2Vec'i yakalar ya da geçer ve eğitimi daha az maliyetlidir.

İkincisi, hiçbir yöntemin daha önce görmediği kelimeler için bir hikayesi yoktu. `Zoomer-approved`, `dogecoin`, geçen hafta türetilen herhangi bir özel isim, nadir bir kökün her çekim formu. **FastText** bunu karakter n-gram'larını gömerek düzeltti: bir kelime parçalarının (morfem'ler dahil) toplamıdır, böylece vocabulary dışı kelimeler bile mantıklı bir vektör alır.

Üçüncüsü, transformer'lar geldikten sonra soru tekrar değişti. Kelime seviyesi vocabulary'ler bir milyon girdi civarında doyuma ulaşır; gerçek dil ondan daha açıktır. **Byte-pair encoding (BPE)** ve akrabaları bunu, her şeyi kapsayan sık subword birimlerinden oluşan bir vocabulary öğrenerek çözdü. Her modern LLM için her modern tokenleştirici bir subword tokenleştiricisidir.

Bu ders üçünü de gezer, sonra hangisine ne zaman uzanacağını açıklar.

## Kavram

**GloVe (Global Vectors).** Kelime-kelime co-occurrence matrisi `X`'i kur, burada `X[i][j]`, `j` kelimesinin `i` kelimesinin bağlamında ne sıklıkla geçtiğidir. Vektörleri `v_i · v_j + b_i + b_j ≈ log(X[i][j])` olacak şekilde eğit. Loss'u, sık çiftler hâkim olmayacak şekilde ağırlıklandır. Bitti.

**FastText.** Bir kelime, karakter n-gram'larının artı kelimenin kendisinin toplamıdır. `where`, `<wh, whe, her, ere, re>, <where>` olur. Kelime vektörü bu bileşen vektörlerin toplamıdır. Word2Vec gibi eğit. Fayda: görülmemiş kelimeler (`whereupon`) bilinen n-gram'lardan bileşenir.

**BPE (Byte-Pair Encoding).** Tek tek byte'lardan (ya da karakterlerden) oluşan bir vocabulary ile başla. Corpus'taki her komşu çifti say. En sık çifti yeni bir token'a birleştir. `k` yineleme tekrarla. Sonuç: sık dizilerin (`ing`, `tion`, `the`) tek token olduğu ve nadir kelimelerin tanıdık parçalara bölündüğü `k + 256` token'lık bir vocabulary. Her cümle bir şeye tokenleşir.

## İnşa Et

### GloVe: co-occurrence matrisini faktorize et

```python
import numpy as np
from collections import Counter


def build_cooccurrence(docs, window=5):
    pair_counts = Counter()
    vocab = {}
    for doc in docs:
        for token in doc:
            if token not in vocab:
                vocab[token] = len(vocab)
    for doc in docs:
        indexed = [vocab[t] for t in doc]
        for i, center in enumerate(indexed):
            for j in range(max(0, i - window), min(len(indexed), i + window + 1)):
                if i != j:
                    distance = abs(i - j)
                    pair_counts[(center, indexed[j])] += 1.0 / distance
    return vocab, pair_counts


def glove_train(vocab, pair_counts, dim=16, epochs=100, lr=0.05, x_max=100, alpha=0.75, seed=0):
    n = len(vocab)
    rng = np.random.default_rng(seed)
    W = rng.normal(0, 0.1, size=(n, dim))
    W_tilde = rng.normal(0, 0.1, size=(n, dim))
    b = np.zeros(n)
    b_tilde = np.zeros(n)

    for epoch in range(epochs):
        for (i, j), x_ij in pair_counts.items():
            weight = (x_ij / x_max) ** alpha if x_ij < x_max else 1.0
            diff = W[i] @ W_tilde[j] + b[i] + b_tilde[j] - np.log(x_ij)
            coef = weight * diff

            grad_W_i = coef * W_tilde[j]
            grad_W_tilde_j = coef * W[i]
            W[i] -= lr * grad_W_i
            W_tilde[j] -= lr * grad_W_tilde_j
            b[i] -= lr * coef
            b_tilde[j] -= lr * coef

    return W + W_tilde
```

Adı anılmaya değer iki hareketli parça. Ağırlıklandırma fonksiyonu `f(x) = (x/x_max)^alpha`, çok sık çiftleri (`(the, and)` gibi) aşağı çeker ki loss'a hâkim olmasınlar. Nihai embedding `W` (merkez) ve `W_tilde` (bağlam) tablolarının toplamıdır. İkisinin toplamı yayınlanmış bir numaradır ve sadece birini kullanmaktan daha iyi performans gösterme eğilimindedir.

### FastText: subword-farkında embedding'ler

```python
def char_ngrams(word, n_min=3, n_max=6):
    wrapped = f"<{word}>"
    grams = {wrapped}
    for n in range(n_min, n_max + 1):
        for i in range(len(wrapped) - n + 1):
            grams.add(wrapped[i:i + n])
    return grams
```

```python
>>> char_ngrams("where")
{'<where>', '<wh', 'whe', 'her', 'ere', 're>', '<whe', 'wher', 'here', 'ere>', '<wher', 'where', 'here>'}
```

Her kelime, n-gram'larının (tipik olarak 3-6 karakter) seti tarafından temsil edilir. Kelime embedding'i n-gram embedding'lerinin toplamıdır. Skip-gram eğitimi için, Word2Vec'in tek vektör kullandığı yere bunu tak.

```python
def fasttext_vector(word, ngram_table):
    grams = char_ngrams(word)
    vecs = [ngram_table[g] for g in grams if g in ngram_table]
    if not vecs:
        return None
    return np.sum(vecs, axis=0)
```

Görülmemiş bir kelime için, n-gram'larının bir kısmı biliniyorsa yine bir vektör elde edersin. `whereupon`, `where` ile `<wh`, `her`, `ere` ve `<where`'ı paylaşır, böylece ikisi birbirinin yakınına iner.

### BPE: öğrenilmiş subword vocabulary

```python
def learn_bpe(corpus, k_merges):
    vocab = Counter()
    for word, freq in corpus.items():
        tokens = tuple(word) + ("</w>",)
        vocab[tokens] = freq

    merges = []
    for _ in range(k_merges):
        pair_freq = Counter()
        for tokens, freq in vocab.items():
            for a, b in zip(tokens, tokens[1:]):
                pair_freq[(a, b)] += freq
        if not pair_freq:
            break
        best = pair_freq.most_common(1)[0][0]
        merges.append(best)

        new_vocab = Counter()
        for tokens, freq in vocab.items():
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i + 1 < len(tokens) and (tokens[i], tokens[i + 1]) == best:
                    new_tokens.append(tokens[i] + tokens[i + 1])
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            new_vocab[tuple(new_tokens)] = freq
        vocab = new_vocab
    return merges


def apply_bpe(word, merges):
    tokens = list(word) + ["</w>"]
    for a, b in merges:
        new_tokens = []
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens) and tokens[i] == a and tokens[i + 1] == b:
                new_tokens.append(a + b)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens = new_tokens
    return tokens
```

```python
>>> corpus = Counter({"low": 5, "lower": 2, "newest": 6, "widest": 3})
>>> merges = learn_bpe(corpus, k_merges=10)
>>> apply_bpe("lowest", merges)
['low', 'est</w>']
```

İlk yineleme en yaygın komşu çifti birleştirir. Yeterli yinelemeden sonra, sık alt diziler (`low`, `est`, `tion`) tek token olur ve nadir kelimeler temiz biçimde bölünür.

Gerçek GPT / BERT / T5 tokenleştiricileri 30k-100k merge öğrenir. Sonuç: herhangi bir metin sınırlı uzunlukta bilinen ID'lerden oluşan bir diziye tokenleşir, asla OOV olmaz.

## Kullan

Pratikte, bunların hiçbirini kendin nadiren eğitirsin. Önceden eğitilmiş checkpoint'leri yüklersin.

```python
import fasttext.util
fasttext.util.download_model("en", if_exists="ignore")
ft = fasttext.load_model("cc.en.300.bin")
print(ft.get_word_vector("whereupon").shape)
print(ft.get_word_vector("zoomerapproved").shape)
```

Transformer döneminde BPE tarzı subword tokenleştirme için:

```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("gpt2")
print(tok.tokenize("unbelievably tokenized"))
```

```
['un', 'bel', 'iev', 'ably', 'Ġtoken', 'ized']
```

`Ġ` öneki kelime sınırlarını işaretler (GPT-2 konvansiyonu). Her modern tokenleştirici bir BPE varyantı, WordPiece (BERT) ya da SentencePiece (T5, LLaMA)'dir.

### Hangisini seçmeli

| Durum | Seç |
|-----------|------|
| Önceden eğitilmiş genel amaçlı kelime vektörleri, OOV toleransı gerekmiyor | GloVe 300d |
| Önceden eğitilmiş genel amaçlı kelime vektörleri, yazım hatalarını / neologizmleri / morfolojik olarak zengin dilleri ele almalı | FastText |
| Bir transformer'a giren her şey (eğitim ya da çıkarım) | Modelin geldiği tokenleştirici neyse o. Asla değiştirme. |
| Sıfırdan kendi dil modelini eğitme | Önce corpus'unda bir BPE ya da SentencePiece tokenleştiricisi eğit |
| Linear model ile üretim metin sınıflandırması | Hâlâ TF-IDF. Ders 02. |

## Yayınla

`outputs/skill-embeddings-picker.md` olarak kaydet:

```markdown
---
name: tokenizer-picker
description: Pick a tokenization approach for a new language model or text pipeline.
version: 1.0.0
phase: 5
lesson: 04
tags: [nlp, tokenization, embeddings]
---

Given a task and dataset description, you output:

1. Tokenization strategy (word-level, BPE, WordPiece, SentencePiece, byte-level). One-sentence reason.
2. Vocabulary size target (e.g., 32k for an English-only LM, 64k-100k for multilingual).
3. Library call with the exact training command. Name the library. Quote the arguments.
4. One reproducibility pitfall. Tokenizer-model mismatch is the single most common silent production bug; call out which pair must be used together.

Refuse to recommend training a custom tokenizer when the user is fine-tuning a pretrained LLM. Refuse to recommend word-level tokenization for any model targeting production inference. Flag non-English / multi-script corpora as needing SentencePiece with byte fallback.
```

## Alıştırmalar

1. **Kolay.** `char_ngrams("playing")` ve `char_ngrams("played")`'i çalıştır. İki n-gram setinin Jaccard örtüşmesini hesapla. Önemli ortak parçalar (`pla`, `lay`, `play`) görmelisin; bu, FastText'in morfolojik varyantlar arasında neden iyi transfer ettiğinin sebebidir.
2. **Orta.** `learn_bpe`'yi vocabulary büyümesini izleyecek şekilde genişlet. Merge sayısının bir fonksiyonu olarak corpus karakteri başına token'ı çiz. Önce hızlı sıkıştırma, ~2-3 karakter/token civarında asimptot görmelisin.
3. **Zor.** Shakespeare'in tüm eserleri üzerinde 1k merge'lik bir BPE eğit. Yaygın kelimeler ile nadir özel isimlerin tokenleştirmesini karşılaştır. Öncesinde ve sonrasında kelime başına ortalama token'ı ölç. Seni neyin şaşırttığını yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Co-occurrence matrisi | Kelime-kelime frekans tablosu | `X[i][j]` = `j` kelimesinin `i` kelimesinin etrafındaki bir pencerede ne sıklıkla geçtiği. |
| Subword | Bir kelimenin parçası | Bir karakter n-gram'ı (FastText) ya da öğrenilmiş token (BPE/WordPiece/SentencePiece). |
| BPE | Byte-pair encoding | Vocabulary hedef boyuta ulaşana kadar en sık komşu çiftlerinin yinelemeli birleştirilmesi. |
| OOV | Vocabulary dışı | Modelin daha önce görmediği kelime. Word2Vec/GloVe başarısız olur. FastText ve BPE bununla başa çıkar. |
| Byte-level BPE | Ham byte'lar üzerinde BPE | GPT-2'nin şeması. Vocabulary 256 byte ile başlar, böylece hiçbir şey asla OOV olmaz. |

## İleri Okuma

- [Pennington, Socher, Manning (2014). GloVe: Global Vectors for Word Representation](https://nlp.stanford.edu/pubs/glove.pdf) — GloVe makalesi, yedi sayfa, hâlâ loss'un en iyi türetimi.
- [Bojanowski et al. (2017). Enriching Word Vectors with Subword Information](https://arxiv.org/abs/1607.04606) — FastText.
- [Sennrich, Haddow, Birch (2016). Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — BPE'yi modern NLP'ye sokan makale.
- [Hugging Face tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary) — BPE, WordPiece ve SentencePiece'in pratikte gerçekten nasıl farklılaştığı.
