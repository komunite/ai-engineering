# Embedding Modelleri — 2026 Derinlemesine İnceleme

> Word2Vec sana kelime başına bir vektör verdi. Modern embedding modelleri sana pasaj başına bir vektör veriyor, cross-lingual, sparse, dense ve çoklu-vektör görünümleriyle, indeksine sığacak boyutta. Yanlış seç ve RAG'in yanlış şeyi getirir.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 03 (Word2Vec), Faz 5 · 14 (Bilgi Erişimi)
**Süre:** ~60 dakika

## Sorun

RAG sistemin %40 oranında yanlış pasajı getiriyor. Suçlu nadiren vector database ya da prompt'tur. Embedding modelidir.

2026'da bir embedding seçmek, beş eksen arasında seçim yapmak anlamına gelir:

1. **Dense vs sparse vs multi-vector.** Pasaj başına bir vektör, ya da token başına bir, ya da sparse ağırlıklı kelime torbası.
2. **Dil kapsaması.** Monolingual İngilizce modeller hâlâ İngilizce-only görevlerde kazanıyor. Çok dilli modeller corpus'lar karışıkken kazanıyor.
3. **Bağlam uzunluğu.** 512 token vs 8,192 vs 32,768 — ve gerçek etkili kapasite sıklıkla reklam edilen max'ın %60-70'idir.
4. **Boyut bütçesi.** Tam precision'da 3,072 float = vektör başına 12 KB. 100M vektörde, depolama $1,300/ay. Matryoshka truncation bunu 4x keser.
5. **Açık vs hosted.** Açık ağırlık stack ve veriyi senin kontrol etmen anlamına gelir. Hosted her zaman en yenisi için kontrolden vazgeçmen demek.

Bu ders tradeoff'ları adlandırır, böylece geçen çeyrek ne popülerse ona değil, kanıta göre seçebilirsin.

## Kavram

![Dense, sparse ve multi-vector embedding'ler](../assets/embedding-modes.svg)

**Dense embedding'ler.** Pasaj başına bir vektör (genellikle 384-3,072 boyut). Cosine similarity pasajları semantik yakınlığa göre sıralar. OpenAI `text-embedding-3-large`, BGE-M3 dense modu, Voyage-3. Varsayılan seçim.

**Sparse embedding'ler.** SPLADE tarzı. Bir transformer her vocab token'ı için bir ağırlık tahmin eder, sonra çoğunu sıfırlar. Sonuç |vocab| boyutunda sparse vektördür. Lexical eşleşmeyi yakalar (BM25 gibi) ama öğrenilmiş term ağırlıklarıyla. Anahtar kelime ağırlıklı sorgularda güçlü.

**Multi-vector (late interaction).** ColBERTv2, Jina-ColBERT. Token başına bir vektör. MaxSim ile puanlama: her sorgu token'ı için en benzer belge token'ını bul, skorları topla. Saklama ve puanlama daha pahalı, ama uzun sorgular ve alana özgü corpus'larda kazanır.

**BGE-M3: tümü birden.** Tek model dense, sparse ve multi-vector temsilleri eşzamanlı çıkarır. Her biri bağımsız sorgulanabilir; skorlar ağırlıklı toplam yoluyla füzyonlanır. Tek bir checkpoint'ten esneklik istediğin zaman 2026 varsayılanı.

**Matryoshka Representation Learning.** Vektörün ilk N boyutu kendi başına kullanışlı bir bağımsız embedding oluşturacak şekilde eğitilmiş. 1,536 boyutlu vektörü 256 boyuta truncate et ve 6x depolama tasarrufu için ~%1 doğruluk öde. OpenAI text-3, Cohere v4, Voyage-4, Jina v5, Gemini Embedding 2, Nomic v1.5+ tarafından desteklenir.

### MTEB leaderboard kısmi bir hikaye anlatır

Massive Text Embedding Benchmark — lansmanda (2022) 8 görev türünde 56 görev, MTEB v2'de 100+ göreve genişledi. 2026 başında, Gemini Embedding 2 retrieval'da en üstte (67.71 MTEB-R). Cohere embed-v4 genelde liderdir (65.2 MTEB). BGE-M3 açık ağırlık çok dilli liderdir (63.0). Leaderboard gereklidir ama yeterli değildir — her zaman alanında benchmark et.

### Üç katmanlı desen

| Kullanım durumu | Desen |
|----------|---------|
| Hızlı ilk geçiş | Dense bi-encoder (BGE-M3, text-3-small) |
| Recall artırma | Sparse (SPLADE, BGE-M3 sparse) + RRF fuse |
| Top-50'de precision | Multi-vector (ColBERTv2) ya da cross-encoder reranker |

Çoğu üretim stack'i üçünü de kullanır.

## İnşa Et

### Adım 1: baseline — Sentence-BERT ile dense embedding'ler

```python
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")
corpus = [
    "The first iPhone launched in 2007.",
    "Apple released the iPod in 2001.",
    "Android is an operating system from Google.",
]
emb = encoder.encode(corpus, normalize_embeddings=True)

query = "When was the iPhone released?"
q_emb = encoder.encode([query], normalize_embeddings=True)[0]
scores = emb @ q_emb
print(sorted(enumerate(scores), key=lambda x: -x[1]))
```

`normalize_embeddings=True` nokta çarpımını cosine similarity'ye eşitler. Her zaman ayarla.

### Adım 2: Matryoshka truncation

```python
def truncate(vectors, dim):
    out = vectors[:, :dim]
    return out / np.linalg.norm(out, axis=1, keepdims=True)

emb_256 = truncate(emb, 256)
emb_128 = truncate(emb, 128)
```

Truncation sonrası yeniden normalize et. Nomic v1.5, OpenAI text-3 ve Voyage-4, bu ilk birkaç seviye için kayıpsız olacak şekilde eğitilmiştir. Matryoshka olmayan modeller (orijinal Sentence-BERT) truncate edildiğinde keskin biçimde bozulur.

### Adım 3: BGE-M3 çoklu işlevsellik

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

output = model.encode(
    corpus,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True,
)
# output["dense_vecs"]:    (n_docs, 1024)
# output["lexical_weights"]: dict listesi {token_id: weight}
# output["colbert_vecs"]:  (n_tokens, 1024) array listesi
```

Üç indeks, tek çıkarım çağrısı. Skor füzyonu:

```python
dense_score = ... # dense_vecs üzerinde cosine
sparse_score = model.compute_lexical_matching_score(q_lex, d_lex)
colbert_score = model.colbert_score(q_col, d_col)
final = 0.4 * dense_score + 0.2 * sparse_score + 0.4 * colbert_score
```

Ağırlıkları alanın için ayarla.

### Adım 4: özel bir görevde MTEB eval

```python
from mteb import MTEB

tasks = ["ArguAna", "SciFact", "NFCorpus"]
evaluation = MTEB(tasks=tasks)
results = evaluation.run(encoder, output_folder="./mteb-results")
```

Aday modellerini *temsili* bir alt sette çalıştır. Yalnızca leaderboard rank'ına güvenme — alanın önemli.

### Adım 5: sıfırdan elle yapılmış cosine

`code/main.py`'a bak. Ortalanmış Hashing Trick embedding'leri (yalnızca stdlib). Transformer embedding'leriyle rekabetçi değil, ama şekli gösterir: tokenleştir → vektör → normalize → nokta çarpımı.

## Tuzaklar

- **Sorgu ve belge için aynı model.** Bazı modeller (Voyage, Jina-ColBERT) asimetrik encoding kullanır — sorgu ve belge farklı yollardan geçer. Her zaman model kartını kontrol et.
- **Eksik prefix.** `bge-*` modelleri sorgulardan önce `"Represent this sentence for searching relevant passages: "` eklenmesini gerektirir. Unutursan 3-5 puan recall açığı.
- **Aşırı Matryoshka truncation'ı.** 1,536 → 256 genellikle güvenli. 1,536 → 64 değil. Kendi eval setinde doğrula.
- **Bağlam truncation'ı.** Çoğu model sessizce max uzunlukları üzerindeki girdileri truncate eder. Uzun belgeler chunking gerektirir (bkz. ders 23).
- **Latency kuyruğunu yok sayma.** MTEB skorları p99 latency'yi saklar. 600M model 335M modeli 2 puanla yenebilir ama sorgu başına 3x daha pahalıya patlar.

## Kullan

2026 stack'i:

| Durum | Seç |
|-----------|------|
| İngilizce-only, hızlı, API | `text-embedding-3-large` ya da `voyage-3-large` |
| Açık ağırlık, İngilizce | `BAAI/bge-large-en-v1.5` |
| Açık ağırlık, çok dilli | `BAAI/bge-m3` ya da `Qwen3-Embedding-8B` |
| Uzun bağlam (32k+) | Voyage-3-large, Cohere embed-v4, Qwen3-Embedding-8B |
| Yalnızca CPU deploy | Nomic Embed v2 (137M params, MoE) |
| Depolama kısıtlı | Matryoshka-truncate edilmiş + int8 kuantizasyon |
| Anahtar kelime ağırlıklı sorgular | SPLADE sparse ekle, dense ile RRF-fuse |

2026 deseni: BGE-M3 ya da text-3-large ile başla, MTEB ile alanında değerlendir, alana özgü bir model 3 puandan fazla kazanıyorsa değiştir.

## Yayınla

`outputs/skill-embedding-picker.md` olarak kaydet:

```markdown
---
name: embedding-picker
description: Pick embedding model, dimension, and retrieval mode for a given corpus and deployment.
version: 1.0.0
phase: 5
lesson: 22
tags: [nlp, embeddings, retrieval]
---

Given a corpus (size, languages, domain, avg length), deployment target (cloud / edge / on-prem), latency budget, and storage budget, output:

1. Model. Named checkpoint or API. One-sentence reason.
2. Dimension. Full / Matryoshka-truncated / int8-quantized. Reason tied to storage budget.
3. Mode. Dense / sparse / multi-vector / hybrid. Reason.
4. Query prefix / template if required by the model card.
5. Evaluation plan. MTEB tasks relevant to domain + held-out domain eval with nDCG@10.

Refuse recommendations that truncate Matryoshka to <64 dims without domain validation. Refuse ColBERTv2 for corpora under 10k passages (overhead not justified). Flag long-document corpora (>8k tokens) routed to models with 512-token windows.
```

## Alıştırmalar

1. **Kolay.** `bge-small-en-v1.5` ile 100 cümleyi tam boyutta (384) encode et, sonra Matryoshka 128'de. 10 sorguda MRR düşüşünü ölç.
2. **Orta.** Alanından 500 pasajda BGE-M3 dense, sparse ve colbert'i karşılaştır. Hangisi recall@10'da kazanır? RRF füzyonu en iyi tek modu yener mi?
3. **Zor.** Üç aday modeli alanının top-2 görevinde MTEB'de çalıştır. MTEB skorunu, 100 sorgu batch'inde p99 latency'yi ve $/1M sorgu raporla. Pareto-optimal olanı seç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Dense embedding | Vektör | Metin başına bir sabit boyutlu vektör. Sıralama için cosine similarity. |
| Sparse embedding | Öğrenilmiş BM25 | Vocab token başına bir ağırlık; çoğunlukla sıfırlar; end-to-end eğitilmiş. |
| Multi-vector | ColBERT tarzı | Token başına bir vektör; MaxSim puanlama; daha büyük indeks, daha iyi recall. |
| Matryoshka | Rus bebek numarası | İlk N boyut kendi başına geçerli daha küçük bir embedding'dir. |
| MTEB | Benchmark | Massive Text Embedding Benchmark — lansmanda 56 görev, v2'de 100+. |
| BEIR | Retrieval benchmark | 18 zero-shot retrieval görev; alanlar arası dayanıklılık için sıklıkla alıntılanır. |
| Asimetrik encoding | Sorgu ≠ belge yolu | Model sorgular ve belgeler için farklı projeksiyonlar kullanır. |

## İleri Okuma

- [Reimers, Gurevych (2019). Sentence-BERT](https://arxiv.org/abs/1908.10084) — bi-encoder makalesi.
- [Muennighoff et al. (2022). MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316) — leaderboard makalesi.
- [Chen et al. (2024). BGE-M3: Multi-lingual, Multi-functionality, Multi-granularity](https://arxiv.org/abs/2402.03216) — birleşik üç-modlu model.
- [Kusupati et al. (2022). Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147) — boyut-merdiveni eğitim hedefi.
- [Santhanam et al. (2022). ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction](https://arxiv.org/abs/2112.01488) — üretimde late interaction.
- [MTEB leaderboard on Hugging Face](https://huggingface.co/spaces/mteb/leaderboard) — canlı sıralamalar.
