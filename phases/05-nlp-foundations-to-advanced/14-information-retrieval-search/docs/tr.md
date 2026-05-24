# Bilgi Erişimi ve Arama

> BM25 precise ama kırılgan. Dense geniş ağ atar ama anahtar kelimeleri kaçırır. Hibrit 2026 varsayılanıdır. Geri kalan her şey ayardır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 02 (BoW + TF-IDF), Faz 5 · 04 (GloVe, FastText, Subword)
**Süre:** ~75 dakika

## Sorun

Kullanıcı "what happens if someone lies to get money" yazıyor ve gerçekten bunu kapsayan kanunu bulmayı bekliyor: "Section 420 IPC." Bir anahtar kelime aramasını tamamen kaçırır (paylaşılan vocabulary yok). Embedding'ler hukuki metin üzerinde eğitilmediyse semantik arama da onu kaçırır. Gerçek aramanın ikisini de ele alması gerekir.

IR, her RAG sisteminin, her arama çubuğunun, her docs sitesinin fuzzy lookup'ının altındaki pipeline'dır. Üretimde çalışan 2026 mimarisi tek bir yöntem değil. Tamamlayıcı yöntemler zinciridir, her biri kendisinden öncekinin başarısızlıklarını yakalar.

Bu ders her parçayı kurar ve her birinin hangi başarısızlıkları yakaladığını adlandırır.

## Kavram

![Hibrit retrieval: BM25 + dense + RRF + cross-encoder rerank](../assets/retrieval.svg)

Dört katman. İhtiyacın olanları seç.

1. **Sparse retrieval (BM25).** Hızlı, tam eşleşmelerde precise, semantikte berbat. Inverted index üzerinde çalıştır. Milyonlarca belgede sorgu başına 10ms altı. Kanun referanslarını, ürün kodlarını, hata mesajlarını, named entity'leri doğru getirir.
2. **Dense retrieval.** Sorgu ve belgeleri vektörlere encode et. Nearest neighbor araması. Paraphrase'leri ve semantik benzerliği yakalar. Bir karakter farklı tam anahtar kelime eşleşmelerini kaçırır. FAISS ya da bir vector DB ile sorgu başına 50-200ms.
3. **Fusion.** Sparse ve dense'ten sıralı listeleri birleştir. Reciprocal Rank Fusion (RRF) kolay varsayılandır çünkü ham skorları (farklı ölçeklerde yaşar) yok sayar ve yalnızca rank pozisyonlarını kullanır. Bir sinyalin alanında hâkim olduğunu bildiğinde ağırlıklı fusion bir seçenektir.
4. **Cross-encoder rerank.** Fusion'dan top-30'u al. Bir cross-encoder çalıştır (sorgu + belge birlikte, her çifti puanla). Top-5'i tut. Cross-encoder'lar çift başına bi-encoder'lardan daha yavaş ama çok daha doğru. Yalnızca top-30'da çalıştırarak amortize edersin.

Üç yönlü retrieval (BM25 + dense + SPLADE gibi learned-sparse) 2026 benchmark'larında iki yönlüyü geçer ama learned-sparse indeksler için altyapı gerektirir. Çoğu ekip için iki yönlü artı cross-encoder rerank tatlı noktadır.

## İnşa Et

### Adım 1: sıfırdan BM25

```python
import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return TOKEN_RE.findall(text.lower())


class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        if not corpus:
            raise ValueError("corpus must not be empty")
        self.corpus = [tokenize(d) for d in corpus]
        self.k1 = k1
        self.b = b
        self.n_docs = len(self.corpus)
        self.avg_dl = sum(len(d) for d in self.corpus) / self.n_docs
        self.df = Counter()
        for doc in self.corpus:
            for term in set(doc):
                self.df[term] += 1

    def idf(self, term):
        n = self.df.get(term, 0)
        return math.log(1 + (self.n_docs - n + 0.5) / (n + 0.5))

    def score(self, query, doc_idx):
        q_tokens = tokenize(query)
        doc = self.corpus[doc_idx]
        dl = len(doc)
        freq = Counter(doc)
        score = 0.0
        for term in q_tokens:
            f = freq.get(term, 0)
            if f == 0:
                continue
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
            score += self.idf(term) * numerator / denominator
        return score

    def rank(self, query, top_k=10):
        scored = [(self.score(query, i), i) for i in range(self.n_docs)]
        scored.sort(reverse=True)
        return scored[:top_k]
```

Bilmeye değer iki parametre. `k1=1.5`, term frekans doygunluğunu kontrol eder; daha yüksek terim tekrarına daha çok ağırlık demek. `b=0.75`, uzunluk normalizasyonunu kontrol eder; 0 belge uzunluğunu yok sayar, 1 tamamen normalize eder. Varsayılanlar orijinal makaledeki Robertson'ın önerileridir ve nadiren ayarlama gerekir.

### Adım 2: bi-encoder ile dense retrieval

```python
from sentence_transformers import SentenceTransformer
import numpy as np


def build_dense_index(corpus, model_id="sentence-transformers/all-MiniLM-L6-v2"):
    encoder = SentenceTransformer(model_id)
    embeddings = encoder.encode(corpus, normalize_embeddings=True)
    return encoder, embeddings


def dense_search(encoder, embeddings, query, top_k=10):
    q_emb = encoder.encode([query], normalize_embeddings=True)
    sims = (embeddings @ q_emb.T).flatten()
    order = np.argsort(-sims)[:top_k]
    return [(float(sims[i]), int(i)) for i in order]
```

Embedding'leri L2-normalize et, böylece nokta çarpımı cosine'a eşit olur. `all-MiniLM-L6-v2` 384 boyutlu, hızlı ve çoğu İngilizce retrieval için yeterince güçlü. Çok dilli iş için `paraphrase-multilingual-MiniLM-L12-v2` kullan. En yüksek doğruluk için `bge-large-en-v1.5` ya da `e5-large-v2`.

### Adım 3: Reciprocal Rank Fusion

```python
def reciprocal_rank_fusion(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, (_, doc_idx) in enumerate(ranking):
            scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (k + rank + 1)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(score, doc_idx) for doc_idx, score in fused]
```

`k=60` sabiti orijinal RRF makalesinden gelir. Daha yüksek `k` rank farklarının katkısını düzleştirir; daha düşük `k` üst rank'ları hâkim kılar. 60 yayınlanmış varsayılandır ve nadiren ayarlama gerekir.

### Adım 4: hibrit arama + rerank

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def hybrid_search(query, bm25, encoder, dense_embeddings, corpus, top_k=5, pool_size=30, reranker=reranker):
    sparse_ranking = bm25.rank(query, top_k=pool_size)
    dense_ranking = dense_search(encoder, dense_embeddings, query, top_k=pool_size)
    fused = reciprocal_rank_fusion([sparse_ranking, dense_ranking])[:pool_size]

    pairs = [(query, corpus[doc_idx]) for _, doc_idx in fused]
    scores = reranker.predict(pairs)
    reranked = sorted(zip(scores, [doc_idx for _, doc_idx in fused]), reverse=True)
    return reranked[:top_k]
```

Üç aşama birleştirildi. BM25 lexical eşleşmeleri bulur. Dense semantik eşleşmeleri bulur. RRF, skor kalibrasyonuna ihtiyaç duymadan iki sıralamayı birleştirir. Cross-encoder, top-30'u sorgu-belge çiftlerini birlikte kullanarak yeniden puanlar; bu, bi-encoder'ın kaçırdığı ince taneli relevance'ı yakalar. Top-5'i tut.

### Adım 5: değerlendirme

| Metrik | Anlamı |
|--------|---------|
| Recall@k | Doğru belgenin var olduğu sorgulardan, ne sıklıkla top-k'da? |
| MRR (Mean Reciprocal Rank) | İlk ilgili belgenin 1/rank'ının ortalaması. |
| nDCG@k | Yalnızca ikili relevant/değil değil, relevance gradasyonlarını hesaba katar. |

Özellikle RAG için, retriever'ın **Recall@k**'sı en önemli sayıdır. Doğru pasaj getirilen sette yoksa reader cevap veremez.

Debug ipucu: başarısız sorgular için sparse ve dense sıralamalarını fark al. Biri doğru belgeyi buluyor diğeri bulmuyorsa, bir vocabulary uyumsuzluğun (düzeltme: eksik yarıyı ekle) ya da bir semantik belirsizliğin (düzeltme: daha iyi embedding'ler ya da bir reranker) var.

## Kullan

2026 stack'i:

| Ölçek | Stack |
|-------|-------|
| 1k-100k belge | Bellek içi BM25 + `all-MiniLM-L6-v2` embedding'leri + RRF. Ayrı DB yok. |
| 100k-10M belge | Dense için FAISS ya da pgvector + BM25 için Elasticsearch / OpenSearch. Paralel çalıştır. |
| 10M+ belge | Hibrit destekli Qdrant / Weaviate / Vespa / Milvus. Top-30'da cross-encoder rerank. |
| En iyi kalite sınırı | Üç yönlü (BM25 + dense + SPLADE) + ColBERT late-interaction yeniden sıralama |

Ne seçersen seç, değerlendirme için bütçe ayır. End-to-end RAG doğruluğunu benchmark etmeden önce retrieval recall'unu benchmark et. Bir reader, retriever'ın kaçırdığını düzeltemez.

### 2026 üretim RAG'inden zor kazanılmış dersler

- **RAG başarısızlıklarının %80'i model değil, ingestion ve chunking'e dayanır.** Ekipler LLM'leri değiştirmek ve prompt ayarlamakla haftalar geçirir, retrieval ise sessizce her üç sorguda bir yanlış bağlamı döndürür. Önce chunking'i düzelt.
- **Chunking stratejisi chunk boyutundan daha önemlidir.** Sabit boyutlu split'ler tabloları, kodu ve iç içe başlıkları bozar. Cümle-farkında varsayılandır; semantik ya da LLM tabanlı chunking teknik docs ve ürün kılavuzları için kâr getirir.
- **Parent-doc deseni.** Precision için küçük "child" chunk'ları getir. Aynı parent bölümünden birden çok child göründüğünde, bağlamı korumak için parent bloğunu yerleştir. Bu, yeniden eğitmeden cevap kalitesini tutarlı biçimde yükseltir.
- **k_rerank=3 genellikle optimaldir.** O noktadan sonraki her ekstra chunk, cevap kalitesini yükseltmeden token maliyeti ve üretim latency'si ekler. Senin için k=8 hâlâ k=3'ten daha iyiyse, reranker yetersiz performans gösteriyor demektir.
- **HyDE / sorgu genişletme.** Sorgudan hipotetik bir cevap üret, onu embed et, getir. Kısa sorular ve uzun belgeler arasındaki ifade açığını köprüler. Eğitim olmadan bedavadan precision artışı.
- **8K token altında bağlam bütçesi.** O sınırda tutarlı vuruşlar, reranker eşiğinin çok gevşek olduğu anlamına gelir.
- **Her şeyin sürümünü tut.** Prompt'lar, chunking kuralları, embedding modeli, reranker. Herhangi bir kayma sessizce cevap kalitesini bozar. Faithfulness, context precision ve cevaplanmamış-soru oranı üzerindeki CI gate'leri kullanıcılar görmeden önce regresyonları engeller.
- **Üç yönlü retrieval (BM25 + dense + SPLADE gibi learned-sparse) 2026 benchmark'larında iki yönlüyü geçer**, özellikle özel isimleri semantik ile karıştıran sorgular için. Altyapı SPLADE indekslerini destekliyorsa gönder.

Uygun retrieval tasarımı, 2026 endüstri ölçümlerine göre halüsinasyonları %70-90 azaltır. Çoğu RAG performans kazancı, model fine-tuning'inden değil, daha iyi retrieval'dan gelir.

## Yayınla

`outputs/skill-retrieval-picker.md` olarak kaydet:

```markdown
---
name: retrieval-picker
description: Pick a retrieval stack for a given corpus and query pattern.
version: 1.0.0
phase: 5
lesson: 14
tags: [nlp, retrieval, rag, search]
---

Given requirements (corpus size, query pattern, latency budget, quality bar, infra constraints), output:

1. Stack. BM25 only, dense only, hybrid (BM25 + dense + RRF), hybrid + cross-encoder rerank, or three-way (BM25 + dense + learned-sparse).
2. Dense encoder. Name the specific model. Match to language(s), domain, and context length.
3. Reranker. Name the specific cross-encoder model if used. Flag that rerank adds 30-100ms latency on top-30.
4. Evaluation plan. Recall@10 is the primary retriever metric. MRR for multi-answer. Baseline first, incremental improvements measured against it.

Refuse to recommend dense-only for corpora with named entities, error codes, or product SKUs unless the user has evidence dense handles exact matches. Refuse to skip reranking for high-stakes retrieval (legal, medical) where the final top-5 decides the user's answer.
```

## Alıştırmalar

1. **Kolay.** Yukarıdaki `hybrid_search`'ü 500-belgelik bir corpus üzerinde uygula. 20 sorgu test et. 5'teki recall'u BM25-only, dense-only ve hibrit arasında karşılaştır.
2. **Orta.** MRR hesaplaması ekle. Bilinen doğru belgesi olan her test sorgusu için, doğru belgenin BM25, dense ve hibrit sıralamalarındaki rank'ını bul. Her biri için MRR raporla.
3. **Zor.** MultipleNegativesRankingLoss kullanarak (Sentence Transformers) bir dense encoder'ı kendi alanında fine-tune et. 500 sorgu-belge çiftinden bir eğitim seti kur. Fine-tune öncesi ve sonrası recall'u karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| BM25 | Anahtar kelime araması | Okapi BM25. Belgeleri term frekansı, IDF ve uzunluğa göre puanlar. |
| Dense retrieval | Vektör araması | Sorgu + belgeyi vektörlere encode et, nearest neighbor'ları bul. |
| Bi-encoder | Embedding modeli | Sorgu ve belgeyi bağımsız encode eder. Sorgu zamanında hızlı. |
| Cross-encoder | Reranker modeli | Sorgu + belgeyi birlikte encode eder. Yavaş ama doğru. |
| RRF | Rank fusion | İki sıralamayı `1/(k + rank)` toplayarak birleştir. |
| Recall@k | Retrieval metriği | İlgili bir belgenin top-k'da olduğu sorguların oranı. |

## İleri Okuma

- [Robertson and Zaragoza (2009). The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf) — kesin BM25 işlemesi.
- [Karpukhin et al. (2020). Dense Passage Retrieval for Open-Domain QA](https://arxiv.org/abs/2004.04906) — DPR, kanonik bi-encoder.
- [Formal et al. (2021). SPLADE: Sparse Lexical and Expansion Model](https://arxiv.org/abs/2107.05720) — dense ile açığı kapatan learned-sparse retriever.
- [Cormack, Clarke, Büttcher (2009). Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — RRF makalesi.
- [Khattab and Zaharia (2020). ColBERT: Efficient and Effective Passage Search](https://arxiv.org/abs/2004.12832) — late-interaction retrieval.
