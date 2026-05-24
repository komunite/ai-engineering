# Word Embedding'ler — Sıfırdan Word2Vec

> Bir kelime, beraberinde geçtiği topluluktur. Bu fikir üzerine sığ bir ağ eğit, geometri kendiliğinden ortaya çıkar.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 02 (BoW + TF-IDF), Faz 3 · 03 (Sıfırdan Backpropagation)
**Süre:** ~75 dakika

## Sorun

TF-IDF, `dog` ve `puppy`'nin farklı kelimeler olduğunu bilir. Neredeyse aynı anlama geldiklerini bilmez. `dog` üzerinde eğitilmiş bir sınıflandırıcı, `puppy` hakkındaki bir değerlendirmeye genelleyemez. Eş anlamlıları listeleyerek bunu örtbas edebilirsin ama nadir terimlerde, alan jargonunda ve öngörmediğin her dilde başarısız olur.

`dog` ve `puppy`'nin uzayda yakın inişe geçtiği bir temsil istiyorsun. `king - man + woman`'ın `queen`'in yakınına indiği. `dog` üzerinde eğitilmiş bir modelin `puppy`'ye bedavadan sinyal aktardığı.

Word2Vec bize o uzayı verdi. İki katmanlı sinir ağı, trilyon token'lık eğitim koşuları, 2013'te yayınlandı. Mimari neredeyse utanç verici şekilde basit. Sonuçlar NLP'yi on yıl yeniden şekillendirdi.

## Kavram

**Dağılım hipotezi** (Firth, 1957): "Bir kelimeyi, beraberinde geçtiği topluluktan tanırsın." İki kelime benzer bağlamlarda geçiyorsa, muhtemelen benzer anlamlara gelirler.

Word2Vec'in iki tadı vardır, ikisi de bu fikri sömürür.

- **Skip-gram.** Bir merkez kelime verildiğinde, etrafındaki kelimeleri tahmin et. Pencere boyutu 2 ile `cat -> (the, sat, on)`.
- **CBOW (continuous bag of words).** Etrafındaki kelimeler verildiğinde, merkezi tahmin et. `(the, sat, on) -> cat`.

Skip-gram eğitimi daha yavaştır ama nadir kelimeleri daha iyi ele alır. Varsayılan oldu.

Ağın bir gizli katmanı vardır, nonlinearity yoktur. Girdi, vocabulary üzerinde one-hot bir vektördür. Çıktı, vocabulary üzerinde bir softmax'tır. Eğitimden sonra çıktı katmanını atarsın. Gizli katman ağırlıkları embedding'lerdir.

```
one-hot(center) ── W ──▶ hidden (d-dim) ── W' ──▶ softmax(vocab)
                          ^
                          embedding budur
```

İşin püfü: 100k kelime üzerinde softmax, yasaklayıcı şekilde pahalıdır. Word2Vec, bunu binary classification görevine çevirmek için **negative sampling** kullanır. "Bu context kelime, bu merkez kelimenin yakınında geçti mi, evet mi hayır mı"yı tahmin et. Tüm vocabulary üzerinde softmax hesaplamak yerine her eğitim çifti için birkaç negatif (birlikte geçmeyen) kelime örnekle.

## İnşa Et

### Adım 1: bir corpus'tan eğitim çiftleri

```python
def skipgram_pairs(docs, window=2):
    pairs = []
    for doc in docs:
        for i, center in enumerate(doc):
            for j in range(max(0, i - window), min(len(doc), i + window + 1)):
                if i == j:
                    continue
                pairs.append((center, doc[j]))
    return pairs
```

```python
>>> skipgram_pairs([["the", "cat", "sat", "on", "mat"]], window=2)
[('the', 'cat'), ('the', 'sat'),
 ('cat', 'the'), ('cat', 'sat'), ('cat', 'on'),
 ('sat', 'the'), ('sat', 'cat'), ('sat', 'on'), ('sat', 'mat'),
 ...]
```

Bir penceredeki her (center, context) çifti pozitif bir eğitim örneğidir.

### Adım 2: embedding tabloları

İki matris. `W`, merkez kelime embedding tablosudur (sakladığın). `W'`, context kelime tablosudur (sık sık atılır, bazen `W` ile ortalanır).

```python
import numpy as np


def init_embeddings(vocab_size, dim, seed=0):
    rng = np.random.default_rng(seed)
    W = rng.normal(0, 0.1, size=(vocab_size, dim))
    W_prime = rng.normal(0, 0.1, size=(vocab_size, dim))
    return W, W_prime
```

Küçük rastgele init. Vocab boyutu 10k ve boyut 100 gerçekçidir; öğretim için, 50 vocab x 16 boyut geometriyi görmek için yeterlidir.

### Adım 3: negative sampling hedefi

Her pozitif çift `(center, context)` için, vocabulary'den `k` rastgele kelimeyi negatif olarak örnekle. Modeli, `W[center] · W'[context]` nokta çarpımı pozitifler için yüksek ve negatifler için düşük olacak şekilde eğit.

```python
def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def train_pair(W, W_prime, center_idx, context_idx, negative_indices, lr):
    v_c = W[center_idx]
    u_pos = W_prime[context_idx]
    u_negs = W_prime[negative_indices]

    pos_score = sigmoid(v_c @ u_pos)
    neg_scores = sigmoid(u_negs @ v_c)

    grad_center = (pos_score - 1) * u_pos
    for i, u in enumerate(u_negs):
        grad_center += neg_scores[i] * u

    W[context_idx] = W[context_idx]
    W_prime[context_idx] -= lr * (pos_score - 1) * v_c
    for i, neg_idx in enumerate(negative_indices):
        W_prime[neg_idx] -= lr * neg_scores[i] * v_c
    W[center_idx] -= lr * grad_center
```

Sihirli formül: pozitif çift üzerinde lojistik loss (sigmoid 1'e yakın olsun) artı negatif çiftler üzerinde lojistik loss (sigmoid 0'a yakın olsun). Gradyanlar her iki tabloya akar. Tam türetme orijinal makalededir; sıkışmasını istiyorsan bir kez kalem kâğıtla baştan aşağı yürü.

### Adım 4: oyuncak bir corpus üzerinde eğit

```python
def train(docs, dim=16, window=2, k_neg=5, epochs=100, lr=0.05, seed=0):
    vocab = build_vocab(docs)
    vocab_size = len(vocab)
    rng = np.random.default_rng(seed)
    W, W_prime = init_embeddings(vocab_size, dim, seed=seed)
    pairs = skipgram_pairs(docs, window=window)

    for epoch in range(epochs):
        rng.shuffle(pairs)
        for center, context in pairs:
            c_idx = vocab[center]
            ctx_idx = vocab[context]
            negs = rng.integers(0, vocab_size, size=k_neg)
            negs = [n for n in negs if n != ctx_idx and n != c_idx]
            train_pair(W, W_prime, c_idx, ctx_idx, negs, lr)
    return vocab, W
```

Büyük bir corpus üzerinde yeterli epoch sonra, bağlam paylaşan kelimeler benzer merkez embedding'lere sahip olur. Oyuncak bir corpus'ta etkiyi hafifçe görürsün. Milyarlarca token'da ise dramatik biçimde görürsün.

### Adım 5: analoji numarası

```python
def nearest(vocab, W, target_vec, topk=5, exclude=None):
    exclude = exclude or set()
    inv_vocab = {i: w for w, i in vocab.items()}
    norms = np.linalg.norm(W, axis=1, keepdims=True) + 1e-9
    W_norm = W / norms
    target = target_vec / (np.linalg.norm(target_vec) + 1e-9)
    sims = W_norm @ target
    order = np.argsort(-sims)
    out = []
    for i in order:
        if i in exclude:
            continue
        out.append((inv_vocab[i], float(sims[i])))
        if len(out) == topk:
            break
    return out


def analogy(vocab, W, a, b, c, topk=5):
    v = W[vocab[b]] - W[vocab[a]] + W[vocab[c]]
    return nearest(vocab, W, v, topk=topk, exclude={vocab[a], vocab[b], vocab[c]})
```

Önceden eğitilmiş 300d Google News vektörlerinde:

```python
>>> analogy(vocab, W, "man", "king", "woman")
[('queen', 0.71), ('monarch', 0.62), ('princess', 0.59), ...]
```

`king - man + woman = queen`. Model krallığın ne olduğunu bildiği için değil. `(king - man)` vektörü "kraliyet" benzeri bir şey yakaladığı ve onu `woman`'a eklemenin kraliyet-dişi bölgesinin yakınına indirdiği için.

## Kullan

Word2Vec'i sıfırdan yazmak öğretimdir. Üretim NLP'si `gensim` kullanır.

```python
from gensim.models import Word2Vec

sentences = [
    ["the", "cat", "sat", "on", "the", "mat"],
    ["the", "dog", "ran", "across", "the", "room"],
]

model = Word2Vec(
    sentences,
    vector_size=100,
    window=5,
    min_count=1,
    sg=1,
    negative=5,
    workers=4,
    epochs=30,
)

print(model.wv["cat"])
print(model.wv.most_similar("cat", topn=3))
```

Gerçek iş için, neredeyse hiç Word2Vec'i kendin eğitmezsin. Önceden eğitilmiş vektörleri indirirsin.

- **GloVe** — Stanford'un co-occurrence matrisi faktorizasyon yaklaşımı. 50d, 100d, 200d, 300d checkpoint'ler. İyi genel kapsama. Ders 04 özellikle GloVe'u ele alır.
- **fastText** — Facebook'un karakter n-gram'larını gömen Word2Vec uzantısı. Vocabulary dışı kelimeleri subword'leri birleştirerek ele alır. Ders 04.
- **Google News üzerinde önceden eğitilmiş Word2Vec** — 300d, 3M kelime vocabulary, 2013'te yayınlandı. Hâlâ her gün indiriliyor.

### Word2Vec 2026'da hâlâ ne zaman kazanır

- Hafif, alana özgü retrieval. Bir laptop'ta bir saatte tıp makaleleri üzerinde eğit, hiçbir genel modelin yakalamadığı uzmanlaşmış vektörler elde et.
- Analoji tarzı feature engineering. `gender_vector = mean(man - woman pairs)`. Cinsiyet nötr bir eksen elde etmek için onu diğer kelimelerden çıkar. Hâlâ fairness araştırmalarında kullanılıyor.
- Yorumlanabilirlik. 100d, PCA ya da t-SNE ile çizmek ve kümelerin oluştuğunu gerçekten görmek için yeterince küçüktür.
- Çıkarımın GPU olmadan cihazda çalışması gereken her yer. Word2Vec lookup'ı tek bir satır çekme işlemidir.

### Word2Vec nerede başarısız olur

Polisemi duvarı. `bank`'in tek bir vektörü vardır. `river bank` ve `financial bank` onu paylaşır. `table` (spreadsheet vs mobilya) onu paylaşır. Aşağı yöndeki bir sınıflandırıcı vektörden anlamları ayırt edemez.

Contextual embedding'ler (ELMo, BERT, o günden beri her transformer) bunu kelimenin her geçişi için çevre bağlama göre farklı bir vektör üreterek çözdü. Word2Vec'ten BERT'e sıçrama budur: statik'ten contextual'a. Faz 7 transformer kısmını ele alır.

Vocabulary dışı problemi diğer başarısızlıktır. Word2Vec, `Zoomer-approved` eğitim verisinde yoksa onu hiç görmemiştir. Fallback yok. fastText bunu subword kompozisyonuyla düzeltir (ders 04).

## Yayınla

`outputs/skill-embedding-probe.md` olarak kaydet:

```markdown
---
name: embedding-probe
description: Inspect a word2vec model. Run analogies, find neighbors, diagnose quality.
version: 1.0.0
phase: 5
lesson: 03
tags: [nlp, embeddings, debugging]
---

You probe trained word embeddings to verify they are working. Given a `gensim.models.KeyedVectors` object and a vocabulary, you run:

1. Three canonical analogy tests. `king : man :: queen : woman`. `paris : france :: tokyo : japan`. `walking : walked :: swimming : ?`. Report the top-1 result and its cosine.
2. Five nearest-neighbor tests on domain-specific words the user supplies. Print top-5 neighbors with cosines.
3. One symmetry check. `similarity(a, b) == similarity(b, a)` to within float precision.
4. One degenerate check. If any embedding has a norm below 0.01 or above 100, the model has a training bug. Flag it.

Refuse to declare a model good on analogy accuracy alone. Analogy benchmarks are gameable and do not transfer to downstream tasks. Recommend intrinsic + downstream evaluation together.
```

## Alıştırmalar

1. **Kolay.** Eğitim döngüsünü minik bir corpus (kediler ve köpekler hakkında 20 cümle) üzerinde çalıştır. 200 epoch sonra, `nearest(vocab, W, W[vocab["cat"]])`'in `dog`'u top 3'ünde döndürdüğünü doğrula. Değilse, epoch'u ya da vocabulary'yi artır.
2. **Orta.** Sık kelimelerin subsampling'ini ekle. Frekansı `10^-5`'in üstünde olan kelimeler, frekanslarıyla orantılı bir olasılıkla eğitim çiftlerinden düşürülür. Nadir kelime benzerliğine etkisini ölç.
3. **Zor.** 20 Newsgroups corpus'unda bir model eğit. İki bias ekseni hesapla: `he - she` ve `doctor - nurse`. Meslek kelimelerini her iki eksene yansıt. En büyük bias açığına sahip mesleklerin hangileri olduğunu raporla. Bu fairness araştırmacılarının kullandığı tipte bir prob'dur.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Word embedding | Vektör olarak kelime | Bağlamdan öğrenilen yoğun, düşük boyutlu (tipik olarak 100-300) bir temsil. |
| Skip-gram | Word2Vec numarası | Merkez kelimeden bağlam kelimelerini tahmin et. CBOW'dan yavaş, nadir kelimeler için daha iyi. |
| Negative sampling | Eğitim kısayolu | Tam vocab üzerinde softmax'ı `k` rastgele kelimeye karşı binary classification ile değiştir. |
| Statik embedding | Kelime başına tek vektör | Bağlamdan bağımsız aynı vektör. Polisemi'de başarısız olur. |
| Contextual embedding | Bağlama duyarlı vektör | Çevre kelimelere göre her geçiş için farklı vektör. Transformer'ların ürettiği şey. |
| OOV | Vocabulary dışı | Eğitimde görülmeyen kelime. Word2Vec bunlar için vektör üretemez. |

## İleri Okuma

- [Mikolov et al. (2013). Distributed Representations of Words and Phrases and their Compositionality](https://arxiv.org/abs/1310.4546) — negative-sampling makalesi. Kısa ve okunaklı.
- [Rong, X. (2014). word2vec Parameter Learning Explained](https://arxiv.org/abs/1411.2738) — gradyanların en net türetimi, orijinal makalenin matematiği yoğun gelirse.
- [gensim Word2Vec tutorial](https://radimrehurek.com/gensim/models/word2vec.html) — gerçekten işe yarayan üretim eğitim ayarları.
