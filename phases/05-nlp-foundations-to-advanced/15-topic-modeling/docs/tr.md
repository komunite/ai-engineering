# Topic Modeling — LDA ve BERTopic

> LDA: belgeler topic karışımlarıdır, topic'ler kelimeler üzerinde dağılımlardır. BERTopic: belgeler embedding uzayında kümelenir, kümeler topic'lerdir. Aynı amaç, farklı primitif'ler.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 02 (BoW + TF-IDF), Faz 5 · 03 (Word2Vec)
**Süre:** ~45 dakika

## Sorun

10,000 müşteri destek bileti, 50,000 haber makalesi ya da 200,000 tweet'in var. Onları okumadan koleksiyonun ne hakkında olduğunu bilmen gerekiyor. Etiketli kategoriler yok. Kaç kategori olduğunu bile bilmiyorsun.

Topic modeling bunu denetimsiz cevaplar. Ona bir corpus ver, küçük bir tutarlı topic seti ve her belge için o topic'ler üzerinde bir dağılım al.

İki algoritmik aile hâkim. LDA (2003) her belgeyi gizli topic'lerin bir karışımı ve her topic'i kelimeler üzerinde bir dağılım olarak ele alır. Çıkarım Bayesian'dır. Karışık üyelik topic atamaları ve açıklanabilir kelime seviyesi olasılık dağılımlarına ihtiyacın olduğu üretimde hâlâ gönderiliyor.

BERTopic (2020) belgeleri BERT ile encode eder, UMAP ile boyutu indirger, HDBSCAN ile kümeler ve sınıf tabanlı TF-IDF yoluyla topic kelimelerini çıkarır. Kısa metin, sosyal medya ve semantik benzerliğin kelime örtüşmesinden daha önemli olduğu her şeyde kazanır. Bir belge bir topic alır, bu uzun-form içerik için bir sınırlamadır.

Bu ders her ikisi için sezgi kurar ve verilen bir corpus için hangisini seçeceğini adlandırır.

## Kavram

![LDA karışım modeli vs BERTopic kümeleme](../assets/topic-modeling.svg)

**LDA generative hikayesi.** Her topic kelimeler üzerinde bir dağılımdır. Her belge topic'lerin bir karışımıdır. Bir belgede bir kelime üretmek için, belgenin karışımından bir topic örnekle, sonra o topic'in dağılımından bir kelime örnekle. Çıkarım bunu tersine çevirir: gözlemlenen kelimeler verildiğinde, belge başına topic dağılımını ve topic başına kelime dağılımını çıkar. Collapsed Gibbs sampling ya da variational Bayes matematik işini yapar.

Anahtar LDA çıktısı:

- `doc_topic`: matris `(n_docs, n_topics)`, her satır 1'e toplanır (belgenin topic karışımı).
- `topic_word`: matris `(n_topics, vocab_size)`, her satır 1'e toplanır (topic'in kelime dağılımı).

**BERTopic pipeline'ı.**

1. Her belgeyi bir sentence transformer (örneğin `all-MiniLM-L6-v2`) ile encode et. 384 boyutlu vektörler.
2. UMAP ile boyutu ~5 boyuta indir. BERT embedding'leri kümeleme için çok yüksek boyutludur.
3. HDBSCAN ile kümele. Yoğunluk tabanlı, değişken boyutlu kümeler ve bir "outlier" etiketi üretir.
4. Her küme için, top kelimeleri çıkarmak üzere kümenin belgeleri üzerinde sınıf tabanlı TF-IDF hesapla.

Çıktı belge başına bir topic'tir (artı bir -1 outlier etiketi). İsteğe bağlı olarak, HDBSCAN'in olasılık vektörü yoluyla soft üyelik.

## İnşa Et

### Adım 1: scikit-learn ile LDA

```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np


def fit_lda(documents, n_topics=5, max_features=1000):
    cv = CountVectorizer(
        max_features=max_features,
        stop_words="english",
        min_df=2,
        max_df=0.9,
    )
    X = cv.fit_transform(documents)
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=50,
        learning_method="online",
    )
    doc_topic = lda.fit_transform(X)
    feature_names = cv.get_feature_names_out()
    return lda, cv, doc_topic, feature_names


def print_top_words(lda, feature_names, n_top=10):
    for idx, topic in enumerate(lda.components_):
        top_idx = np.argsort(-topic)[:n_top]
        words = [feature_names[i] for i in top_idx]
        print(f"topic {idx}: {' '.join(words)}")
```

Dikkat: stopword'ler kaldırıldı, min_df ve max_df nadir ve yaygın terimleri filtreliyor, TfidfVectorizer değil CountVectorizer çünkü LDA ham sayımlar bekliyor.

### Adım 2: BERTopic (üretim)

```python
from bertopic import BERTopic

topic_model = BERTopic(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    min_topic_size=15,
    verbose=True,
)

topics, probs = topic_model.fit_transform(documents)
info = topic_model.get_topic_info()
print(info.head(20))
valid_topics = info[info["Topic"] != -1]["Topic"].tolist()
for topic_id in valid_topics[:5]:
    print(f"topic {topic_id}: {topic_model.get_topic(topic_id)[:10]}")
```

`Topic != -1` filtresi BERTopic'in outlier kovasını (HDBSCAN'in kümeleyemediği belgeler) atar. `min_topic_size` HDBSCAN'in minimum küme boyutunu kontrol eder; BERTopic kütüphane varsayılanı 10'dur. Bu örnek dersin ölçeği için onu açıkça 15'e ayarlıyor. 10,000 belge üstündeki corpus'lar için 50 ya da 100'e çıkar.

### Adım 3: değerlendirme

Her iki yöntem de topic kelimeleri çıkarır. Soru, o kelimelerin tutarlı olup olmadığıdır.

- **Topic coherence (c_v).** Top kelime çiftlerinin NPMI'sini (normalized pointwise mutual information) sliding-window bağlamları üzerinden birleştirir, skorları topic vektörlerine toplar ve o vektörleri cosine similarity ile karşılaştırır. Yüksek daha iyidir. `gensim.models.CoherenceModel`'i `coherence="c_v"` ile kullan.
- **Topic diversity.** Tüm topic'lerin top kelimeleri arasındaki benzersiz kelimelerin oranı. Yüksek daha iyidir (topic'ler örtüşmüyor).
- **Niteliksel inceleme.** Her topic'in top kelimelerini oku. Gerçek bir şeyi adlandırıyorlar mı? İnsan yargısı hâlâ son savunma hattıdır.

## Hangisini seçmeli

| Durum | Seç |
|-----------|------|
| Kısa metin (tweet'ler, değerlendirmeler, başlıklar) | BERTopic |
| Topic karışımlı uzun belgeler | LDA |
| GPU yok / sınırlı compute | LDA ya da NMF |
| Belge seviyesi çoklu topic dağılımları gerekli | LDA |
| Topic etiketleme için LLM entegrasyonu | BERTopic (doğrudan destek) |
| Kaynak-kısıtlı edge deploy | LDA |
| Maks semantik coherence | BERTopic |

En büyük pratik düşünce belge uzunluğudur. BERT embedding'leri truncate eder; LDA sayımları her uzunlukta çalışır. Embedding modelinin bağlamından daha uzun belgeler için, ya chunk + aggregate yap ya da LDA kullan.

## Kullan

2026 stack'i:

- **BERTopic.** Kısa metin ve semantiğin önemli olduğu her şey için varsayılan.
- **`gensim.models.LdaModel`.** Üretim için klasik LDA, olgun, savaşta test edilmiş.
- **`sklearn.decomposition.LatentDirichletAllocation`.** Deneyler için kolay LDA.
- **NMF.** Non-negative matrix factorization. LDA'ya hızlı alternatif, kısa metinde karşılaştırılabilir kalite.
- **Top2Vec.** BERTopic'e benzer tasarım. Daha küçük topluluk ama bazı benchmark'larda iyi.
- **FASTopic.** Çok büyük corpus'larda BERTopic'ten daha yeni, daha hızlı.
- **LLM tabanlı etiketleme.** Herhangi bir kümeleme çalıştır, sonra her kümeyi adlandırmak için bir modele prompt ver.

## Yayınla

`outputs/skill-topic-picker.md` olarak kaydet:

```markdown
---
name: topic-picker
description: Pick LDA or BERTopic for a corpus. Specify library, knobs, evaluation.
version: 1.0.0
phase: 5
lesson: 15
tags: [nlp, topic-modeling]
---

Given a corpus description (document count, avg length, domain, language, compute budget), output:

1. Algorithm. LDA / NMF / BERTopic / Top2Vec / FASTopic. One-sentence reason.
2. Configuration. Number of topics: `recommended = max(5, round(sqrt(n_docs)))`, clamped to 200 for corpora under 40,000 docs; permit >200 only when the corpus is genuinely large (>40k) and note the increased compute cost. `min_df` / `max_df` filters and embedding model for neural approaches also belong here.
3. Evaluation. Topic coherence (c_v) via `gensim.models.CoherenceModel`, topic diversity, and a 20-sample human read.
4. Failure mode to probe. For LDA, "junk topics" absorbing stopwords and frequent terms. For BERTopic, the -1 outlier cluster swallowing ambiguous documents.

Refuse BERTopic on documents longer than the embedding model's context window without a chunking strategy. Refuse LDA on very short text (tweets, reviews under 10 tokens) as coherence collapses. Flag any n_topics choice below 5 as likely wrong; flag >200 on corpora under 40k docs as likely over-splitting.
```

## Alıştırmalar

1. **Kolay.** 20 Newsgroups veri setinde 5 topic'le LDA fit et. Topic başına top 10 kelimeyi yazdır. Her topic'i elle etiketle. Algoritma gerçek kategorileri buldu mu?
2. **Orta.** Aynı 20 Newsgroups alt setinde BERTopic fit et. Bulunan topic sayısını, top kelimeleri ve niteliksel coherence'ı LDA'ya karşı karşılaştır. Hangisi gerçek kategorileri daha temiz çıkarıyor?
3. **Zor.** Corpus'unda LDA ve BERTopic için c_v coherence hesapla. Her birini 5, 10, 20, 50 topic'le çalıştır. Coherence vs topic sayısı çiz. Hangi yöntemin topic sayıları arasında daha stabil olduğunu raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Topic | Corpus'un hakkında olduğu bir şey | Kelimeler üzerinde olasılık dağılımı (LDA) ya da benzer belgelerin bir kümesi (BERTopic). |
| Karışık üyelik | Belge birden çok topic | LDA her belgeye tüm topic'ler üzerinde bir dağılım atar. |
| UMAP | Boyut indirgeme | Yerel yapıyı koruyan manifold öğrenme; BERTopic'te kullanılır. |
| HDBSCAN | Yoğunluk kümeleme | Değişken boyutlu kümeler bulur; outlier'lar için "noise" etiketi (-1) üretir. |
| c_v coherence | Topic kalite metriği | Sliding pencereler içinde top topic kelimelerinin ortalama pointwise mutual information'ı. |

## İleri Okuma

- [Blei, Ng, Jordan (2003). Latent Dirichlet Allocation](https://www.jmlr.org/papers/volume3/blei03a/blei03a.pdf) — LDA makalesi.
- [Grootendorst (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure](https://arxiv.org/abs/2203.05794) — BERTopic makalesi.
- [Röder, Both, Hinneburg (2015). Exploring the Space of Topic Coherence Measures](https://svn.aksw.org/papers/2015/WSDM_Topic_Evaluation/public.pdf) — c_v ve dostlarını tanıtan makale.
- [BERTopic documentation](https://maartengr.github.io/BERTopic/) — üretim referansı. Mükemmel örnekler.
