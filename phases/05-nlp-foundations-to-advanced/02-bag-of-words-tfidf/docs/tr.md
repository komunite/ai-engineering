# Bag of Words, TF-IDF ve Metin Temsili

> Önce say, sonra düşün. TF-IDF, 2026'da hâlâ iyi tanımlanmış görevlerde embedding'leri yeniyor.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 01 (Metin İşleme), Faz 2 · 02 (Sıfırdan Linear Regression)
**Süre:** ~75 dakika

## Sorun

Modelin sayılara ihtiyacı var. Senin elinde string'ler var.

Her NLP pipeline'ı aynı soruyu cevaplamak zorunda. Değişken uzunluklu bir token akışını, bir sınıflandırıcının tüketebileceği sabit boyutlu bir vektöre nasıl çevireceğiz. Alanın oturduğu ilk cevap, işe yarayan en aptal olanıydı. Kelimeleri say. Bir vektör yap.

O vektör, herhangi bir embedding modelinden daha fazla üretim NLP'sini taşıdı. Spam filtreleri, topic sınıflandırıcılar, log anomali tespiti, arama sıralaması (BM25'ten önce), duygu analizinin ilk dalgası, akademik NLP benchmark'larının ilk on yılı. 2026 uygulayıcıları hâlâ dar sınıflandırma görevlerinde önce buna uzanıyor. Hızlı, yorumlanabilir ve kelime varlığının önemli olduğu görevlerde çoğu zaman 400M parametreli bir embedding modelinden ayırt edilemez.

Bu ders, önce bag of words'ü sonra TF-IDF'i sıfırdan inşa eder. Sonra scikit-learn'ün aynı şeyi üç satırda yaptığını gösterir. Sonra seni embedding'lere uzandıran başarısızlık modunu adlandırır.

## Kavram

**Bag of Words (BoW)** sırayı atar. Her belge için, her vocabulary kelimesinin kaç kez geçtiğini say. Vektör uzunluğu vocabulary boyutudur. Pozisyon `i`, kelime `i`'nin sayımıdır.

**TF-IDF**, BoW'u yeniden ağırlıklandırır. Her belgede geçen bir kelime bilgi vermiyor, o yüzden ağırlığını düşür. Corpus genelinde nadir ama tek bir belgede sık olan bir kelime sinyaldir, o yüzden ağırlığını yükselt.

```
TF-IDF(w, d) = TF(w, d) * IDF(w)
             = count(w in d) / |d| * log(N / df(w))
```

`TF`, belgedeki terim frekansı; `df`, document frequency (kelimeyi içeren belge sayısı); `N`, toplam belge sayısı. `log`, yaygın kelimeler için ağırlığı sınırlı tutar.

Anahtar özellik: ikisi de yorumlanabilir eksenli seyrek vektörler üretir. Eğitilmiş bir sınıflandırıcının ağırlıklarına bakıp hangi kelimelerin bir belgeyi hangi sınıfa ittiğini okuyabilirsin. Bunu 768 boyutlu bir BERT embedding'iyle yapamazsın.

## İnşa Et

### Adım 1: vocabulary'yi kur

```python
def build_vocab(docs):
    vocab = {}
    for doc in docs:
        for token in doc:
            if token not in vocab:
                vocab[token] = len(vocab)
    return vocab
```

Girdi: tokenleştirilmiş belge listesi (herhangi bir kelime seviyesi tokenleştirici işe yarar; bu dersteki `code/main.py` basitleştirilmiş küçük harfli bir varyant kullanıyor). Çıktı: `{word: index}` dict. Stabil ekleme sırası, kelime indeksi 0'ın ilk belgede görülen ilk kelime olduğu anlamına gelir. Konvansiyon değişir; scikit-learn alfabetik sıralar.

### Adım 2: bag of words

```python
def bag_of_words(docs, vocab):
    matrix = [[0] * len(vocab) for _ in docs]
    for i, doc in enumerate(docs):
        for token in doc:
            if token in vocab:
                matrix[i][vocab[token]] += 1
    return matrix
```

```python
>>> docs = [["cat", "sat", "on", "mat"], ["cat", "cat", "ran"]]
>>> vocab = build_vocab(docs)
>>> bag_of_words(docs, vocab)
[[1, 1, 1, 1, 0], [2, 0, 0, 0, 1]]
```

Satırlar belgelerdir. Sütunlar vocabulary indekslerdir. Giriş `[i][j]`, "kelime `j`, belge `i`'de kaç kez geçer"dir. Belge 1'de `cat` iki kez var çünkü öyle. Belge 0'da `ran` sıfır kez var çünkü yok.

### Adım 3: term frequency ve document frequency

```python
import math


def term_frequency(doc_bow, doc_length):
    return [c / doc_length if doc_length else 0 for c in doc_bow]


def document_frequency(bow_matrix):
    df = [0] * len(bow_matrix[0])
    for row in bow_matrix:
        for j, count in enumerate(row):
            if count > 0:
                df[j] += 1
    return df


def inverse_document_frequency(df, n_docs):
    return [math.log((n_docs + 1) / (d + 1)) + 1 for d in df]
```

Adı anılmaya değer iki smoothing hilesi. `(n+1)/(d+1)`, `log(x/0)`'dan kaçınır. Sondaki `+1`, her belgede geçen bir kelimenin hâlâ IDF 1'e (0 değil) sahip olmasını sağlar, scikit-learn'ün varsayılanıyla eşleşir. Diğer implementasyonlar ham `log(N/df)` kullanır. İkisi de çalışır; smooth edilmiş sürüm daha cana yakındır.

### Adım 4: TF-IDF

```python
def tfidf(bow_matrix):
    n_docs = len(bow_matrix)
    df = document_frequency(bow_matrix)
    idf = inverse_document_frequency(df, n_docs)
    out = []
    for row in bow_matrix:
        length = sum(row)
        tf = term_frequency(row, length)
        out.append([tf_j * idf_j for tf_j, idf_j in zip(tf, idf)])
    return out
```

```python
>>> docs = [
...     ["the", "cat", "sat"],
...     ["the", "dog", "sat"],
...     ["the", "cat", "ran"],
... ]
>>> vocab = build_vocab(docs)
>>> bow = bag_of_words(docs, vocab)
>>> tfidf(bow)
```

Üç belge, beş vocab kelimesi (`the`, `cat`, `sat`, `dog`, `ran`). `the` üçünde de geçer, IDF'i düşüktür. `dog` birinde geçer, IDF'i yüksektir. Vektörler seyrektir (çoğu giriş küçüktür) ve ayırt edici kelimeler öne çıkar.

### Adım 5: satırları L2-normalize et

```python
def l2_normalize(matrix):
    out = []
    for row in matrix:
        norm = math.sqrt(sum(x * x for x in row))
        out.append([x / norm if norm else 0 for x in row])
    return out
```

Normalizasyon olmadan, daha uzun bir belge daha büyük bir vektör alır ve benzerlik skorlarına hâkim olur. L2 normalizasyon her belgeyi birim hiper küre üzerine koyar. Satırlar arasındaki cosine similarity artık sadece bir nokta çarpımıdır.

## Kullan

scikit-learn üretim sürümünü içerir.

```python
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

docs = ["the cat sat on the mat", "the dog sat on the mat", "the cat ran"]

bow_vectorizer = CountVectorizer()
bow = bow_vectorizer.fit_transform(docs)
print(bow_vectorizer.get_feature_names_out())
print(bow.toarray())

tfidf_vectorizer = TfidfVectorizer()
tfidf = tfidf_vectorizer.fit_transform(docs)
print(tfidf.toarray().round(3))
```

`CountVectorizer` tokenleştirmeyi, vocabulary'yi ve BoW'u tek çağrıda yapar. `TfidfVectorizer`, IDF ağırlıklandırması ve L2 normalizasyonu ekler. İkisi de seyrek matrisler döndürür. 100k belge için, dense sürüm belleğe sığmaz; sınıflandırıcı dense talep edene kadar seyrek kal.

Her şeyi değiştiren ayarlar:

| Arg | Etki |
|-----|--------|
| `ngram_range=(1, 2)` | Bigram'ları dahil et. Genellikle sınıflandırmayı artırır. |
| `min_df=2` | 2'den az belgede geçen kelimeleri at. Gürültülü veride vocabulary'yi budar. |
| `max_df=0.95` | Belgelerin %95'inden fazlasında geçen kelimeleri at. Sabit kodlu liste olmadan stopword temizliğine yaklaşır. |
| `stop_words="english"` | scikit-learn'ün dahili stopword listesi. Göreve bağımlı — duygu analizi olumsuzlukları *atmamalı*. |
| `sublinear_tf=True` | Ham `tf` yerine `1 + log(tf)` kullan. Bir terim bir belgede çok kez tekrarlanıyorsa yardımcı olur. |

### TF-IDF hâlâ ne zaman kazanır (2026 itibarıyla)

- Spam tespiti, topic etiketleme, log anomali işaretleme. Kelime varlığı önemli; semantik nüans değil.
- Düşük veri rejimleri (yüzlerce etiketli örnek). TF-IDF artı logistic regression'ın pretraining maliyeti yoktur.
- Latency'nin önemli olduğu her yerde. TF-IDF artı bir lineer model mikrosaniyelerde cevap verir. Bir belgeyi transformer üzerinden embed etmek 10-100ms sürer.
- Tahminlerini açıklamak zorunda olan sistemler. Sınıflandırıcının katsayılarını incele. En üst pozitif kelimeler sebeptir.

### TF-IDF ne zaman başarısız olur

Semantik körlük başarısızlığı. Şu iki belgeyi düşün:

- "The movie was not good at all."
- "The movie was excellent."

Biri negatif bir değerlendirme. Biri pozitif. TF-IDF örtüşmeleri tam olarak `{the, movie, was}`. Bir bag-of-words sınıflandırıcısı, `good` yakınındaki `not` kelimesinin etiketi tersine çevirdiğini ezberlemek zorunda. Yeterli veride bunu öğrenebilir ama söz dizimini anlayan bir model kadar zarif olmaz.

Diğer başarısızlık: çıkarımda vocabulary dışı kelimeler. IMDb değerlendirmeleri üzerinde eğitilmiş bir BoW modeli, `Zoomer-approved` token'ı eğitimde geçmediyse onunla ne yapacağını bilmez. Subword embedding'leri (ders 04) bununla başa çıkar. TF-IDF çıkamaz.

### Hibrit: TF-IDF ağırlıklı embedding'ler

2026 pragmatik varsayılan, orta ölçekli sınıflandırma için: TF-IDF ağırlıklarını word embedding'ler üzerinde attention olarak kullan.

```python
def tfidf_weighted_embedding(doc, tfidf_scores, embedding_table, dim):
    vec = [0.0] * dim
    total_weight = 0.0
    for token in doc:
        if token not in embedding_table or token not in tfidf_scores:
            continue
        weight = tfidf_scores[token]
        emb = embedding_table[token]
        for i in range(dim):
            vec[i] += weight * emb[i]
        total_weight += weight
    if total_weight == 0:
        return vec
    return [v / total_weight for v in vec]
```

Embedding'lerden semantik kapasiteyi, TF-IDF'ten nadir kelime vurgusunu alırsın. Sınıflandırıcı havuzlanmış vektör üzerinde eğitilir. Bu, 50k civarı etiketli örneğin altında duygu, topic ve niyet sınıflandırması için her ikisini de tek başına geçer.

## Yayınla

`outputs/prompt-vectorization-picker.md` olarak kaydet:

```markdown
---
name: vectorization-picker
description: Given a text-classification task, recommend BoW, TF-IDF, embeddings, or a hybrid.
phase: 5
lesson: 02
---

You recommend a text-vectorization strategy. Given a task description, output:

1. Representation (BoW, TF-IDF, transformer embeddings, or a hybrid). Explain why in one sentence.
2. Specific vectorizer configuration. Name the library. Quote the arguments (`ngram_range`, `min_df`, `max_df`, `sublinear_tf`, `stop_words`).
3. One failure mode to test before shipping.

Refuse to recommend embeddings when the user has under 500 labeled examples unless they show evidence of semantic failure in a TF-IDF baseline. Refuse to remove stopwords for sentiment analysis (negations carry signal). Flag class imbalance as needing more than a vectorizer change.

Example input: "Classifying 30k customer support tickets into 12 categories. Most tickets are 2-3 sentences. English only. Need explainability for audit logs."

Example output:

- Representation: TF-IDF. 30k examples is not small; explainability requirement rules out dense embeddings.
- Config: `TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.95, sublinear_tf=True, stop_words=None)`. Keep stopwords because category keywords sometimes are stopwords ("not working" vs "working").
- Failure to test: verify `min_df=3` does not drop rare category keywords. Run `get_feature_names_out` filtered by class and eyeball.
```

## Alıştırmalar

1. **Kolay.** L2-normalize edilmiş TF-IDF çıktısı üzerinde `cosine_similarity(doc_vec_a, doc_vec_b)`'yi uygula. Özdeş belgelerin 1.0 ve ayrık vocabulary belgelerinin 0.0 skor aldığını doğrula.
2. **Orta.** `bag_of_words`'a `n-gram` desteği ekle. `n` parametresi, `n`-gram'lar üzerinde sayımları üretir. `n=2` ile `["the", "cat", "sat"]` üzerinde `["the cat", "cat sat"]` için bigram sayımlarını ürettiğini test et.
3. **Zor.** Yukarıdaki TF-IDF ağırlıklı embedding hibridini GloVe 100d vektörleriyle kur (bir kez indir, cache'le). 20 Newsgroups veri setinde düz TF-IDF ve düz ortalama havuzlanmış embedding'lere karşı sınıflandırma doğruluğunu karşılaştır. Hangisinin nerede kazandığını raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| BoW | Kelime frekans vektörü | Bir belgedeki vocabulary kelime sayımları. Sırayı atar. |
| TF | Term frequency | Bir belgedeki bir kelimenin sayımı, opsiyonel olarak belge uzunluğuyla normalize edilmiş. |
| DF | Document frequency | Kelimeyi en az bir kez içeren belge sayısı. |
| IDF | Inverse document frequency | Smooth edilmiş `log(N / df)`. Her yerde geçen kelimeleri aşağı çeker. |
| Seyrek vektör | Çoğunlukla sıfır | Vocabulary tipik olarak 10k-100k kelimedir; çoğu, herhangi bir belgede yoktur. |
| Cosine similarity | Vektör açısı | L2-normalize edilmiş vektörlerin nokta çarpımı. 1 özdeş, 0 ortogonal. |

## İleri Okuma

- [scikit-learn — feature extraction from text](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction) — kanonik API referansı, artı her ayar üzerine notlar.
- [Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval](https://www.sciencedirect.com/science/article/pii/0306457388900210) — TF-IDF'i on yıl varsayılan yapan makale.
- ["Why TF-IDF Still Beats Embeddings" — Ashfaque Thonikkadavan (Medium)](https://medium.com/@cmtwskb/why-tf-idf-still-beats-embeddings-ad85c123e1b2) — eski yöntemin ne zaman ve neden kazandığına dair 2026 yorumu.
