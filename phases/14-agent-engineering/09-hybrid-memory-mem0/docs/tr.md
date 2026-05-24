# Hybrid Memory: Vector + Graph + KV (Mem0)

> Mem0 (Chhikara et al., 2025) belleği paralel üç store olarak ele alır — semantik benzerlik için vector, hızlı olgu lookup için KV, entity-relationship akıl yürütme için graph. Retrieval'de bir skorlama katmanı üçünü birleştirir. Bu, dış bellek için 2026 üretim standardı.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 07 (MemGPT), Faz 14 · 08 (Letta Block'lar)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Tek bir store'un (yalnızca vector, yalnızca graph, yalnızca KV) agent belleği için neden yetersiz olduğunu açıkla.
- Mem0'ın üç paralel store'unu ve her birinin ne için optimize ettiğini adlandır.
- Mem0'ın fusion skorlamasını açıkla — relevance, importance, recency — ve neden bir hiyerarşi değil, ağırlıklı toplam olduğunu.
- Hepsine yazan bir `add()` ve sonuçları birleştiren bir `search()` ile stdlib'de oyuncak bir üç-store bellek uygula.

## Sorun

Tek store üç sorgu sınıfından biri için yanlış:

- **Semantik benzerlik** — "geçen hafta agent drift hakkında ne tartıştık?" Vector kazanır; KV ve graph kaçırır.
- **Olgu lookup** — "kullanıcının telefon numarası nedir?" KV kazanır; vector israf, graph aşırı.
- **İlişki akıl yürütme** — "hangi müşteriler aynı billing entity'sini paylaşıyor?" Graph kazanır; vector ve KV yanıtlayamaz.

Üretim agent'ları bir oturumda üçünü de çıkarır. Tek-store bellek bunların ikisi için her zaman yanlış. Mem0'ın katkısı, üçünü tek bir `add`/`search` yüzeyinin arkasında onları birleştiren bir skorlama fonksiyonu ile kablolamak.

## Kavram

### Paralel üç store

Mem0 (arXiv:2504.19413, Nisan 2025) `add(text, user_id, metadata)`'ta:

1. Metinden aday olguları çıkar (LLM-driven adım).
2. Her olguyu semantik arama için vector store'a yaz (embedding).
3. Her olguyu O(1) lookup için (user_id, fact_type, entity) ile anahtarlanan KV store'a yaz.
4. Her olguyu ilişki sorguları için tipli edge'ler olarak graph store'a (Mem0g) yaz.

`search(query, user_id)`'da:

1. Vector store embedding cosine'a göre top-k döndürür.
2. KV store query-türetilmiş (user_id, type, entity) ile anahtarlanmış direkt hit'leri döndürür.
3. Graph store sorgu entity'lerinden erişilebilir subgraph'ı döndürür.
4. Bir skorlama katmanı üçünü birleştirir.

### Fusion skorlama

```
score = w_relevance * relevance(q, record)
      + w_importance * importance(record)
      + w_recency * recency(record)
```

- **Relevance** — vector cosine, KV tam eşleşme, graph path ağırlığı.
- **Importance** — yazma zamanında etiketlenmiş ya da öğrenilmiş (bazı olgular daha önemli: adlar, ID'ler, policy'ler).
- **Recency** — son yazma ya da okumadan bu yana zaman üzerinde üstel decay.

Ağırlıklar ürün başına ayarlanır. Chat agent'lar için daha yüksek `w_recency`; compliance agent'lar için daha yüksek `w_importance`; retrieval agent'lar için daha yüksek `w_relevance`.

### Mem0g ve zamansal akıl yürütme

Mem0g bir conflict detector ekler. Yeni bir olgu mevcut bir edge ile çeliştiğinde, mevcut edge invalid olarak işaretlenir ama silinmez. Zamansal sorgular ("kullanıcının Mart'taki şehri neydi?") valid-at-time subgraph'ı dolaşır.

Bu, Letta'nın invalidation deseninin genelleştirdiği compliance-derece davranış.

### Benchmark sayıları

Mem0 makalesi raporluyor (2025):

- **LoCoMo** (long-form conversation memory): 91.6
- **LongMemEval** (long-horizon episodic memory): 93.4
- **BEAM 1M** (1M-token bellek benchmark'ı): 64.1

Karşılaştırma baseline'ları (full-context 128k LLM, düz vector store, düz KV) hepsi 10+ puan kaybeder. Tek başına benchmark'lar tercih için yeterli değil — operasyonel şekil yeterli — ama sayılar fusion tasarımının bir yuvarlama hatası olmadığını gösterir.

### Scope taksonomisi

Mem0 belleği scope'a göre ayırır:

- **User memory** — oturumlar arasında kalıcı, `user_id` ile anahtarlanır.
- **Session memory** — bir thread içinde kalıcı.
- **Agent memory** — agent instance başına state.

Her yazı bir scope seçer. Retrieval scope-başına ağırlıklarla scope'lar arasında sorgulayabilir. Scope'ları düşünmeden karıştırmak "asistan Alice'e Bob'un projesinden bahsetti" olaylarını alma şeklin.

### Bu desen nerede ters gider

- **Embedding drift.** İlk yüz sorguda doğru görünen vector sonuçları corpus büyüdükçe degrade eder. En çok-kullanılan top-N kaydın periyodik yeniden-embed'lenmesini ekle.
- **KV şema creep.** `(user_id, type, entity)` basit görünür ama her ekip kendi `type`'ını ekler. Type setini üç ayda bir denetle.
- **Graph patlaması.** Gürültülü bir extractor mesaj başına 50 edge ekler. `add` çağrısı başına graph yazılarını tavanla; düşük-güven edge'leri at.

## İnşa Et

`code/main.py` stdlib'de üç-store desenini uyguluyor:

- `VectorStore` — embedding yerine geçen naive token-overlap benzerlik.
- `KVStore` — `(user_id, fact_type, entity)` ile anahtarlanmış dict.
- `GraphStore` — tipli edge'ler (subject, relation, object, valid).
- `Mem0` — `add()`, `search()`, fusion skorlama ve scope-aware retrieval'li top-level facade.
- Multi-user, multi-session bir konuşma üzerinde işlenmiş bir trace.

Çalıştır:

```
python3 code/main.py
```

Çıktı üç ayrı recall yolu artı birleştirilmiş top-k'yı gösterir. `main()`'in üstündeki skorlama ağırlıklarını çevir ve sıralamanın değiştiğini izle.

## Kullan

- **Mem0 (Apache 2.0)** — üretim-hazır. Postgres + Qdrant + Neo4j ile self-host ya da yönetilen bulut kullan.
- **Letta** — üç-katmanlı core/recall/archival; kendi vector ve graph backend'lerini getir.
- **Zep** — temporal KG ve fact extraction'lı ticari alternatif.
- **Custom build'ler** — extractor üzerinde tam kontrole (compliance) ya da fusion ağırlıklarına (recency baskın olan voice agent'lar) ihtiyacın olduğunda.

## Yayınla

`outputs/skill-hybrid-memory.md` fusion scorer, scope taksonomisi ve temporal invalidation kablolanmış üç-store bellek iskelesi üretir.

## Alıştırmalar

1. Oyuncak vector benzerliğini gerçek bir embedding modeliyle değiştir (sentence-transformers, Ollama, OpenAI embeddings). Sentetik uzun bir konuşmada recall@10'u ölç. Sıralama 1000 yazı üzerinde drift eder mi?
2. Zamansal bir sorgu ekle: `search(query, as_of=timestamp)`. Yalnızca o zamana ya da öncesine valid kayıtları döndür. Hangi store en çok iş gerektiriyor?
3. Bir conflict detector uygula: gelen bir olgu bir graph edge ile çelişiyorsa, eski edge'i invalidate et ve ikisini de logla. "kullanıcı Berlin'de yaşıyor" -> "kullanıcı Lisbon'da yaşıyor" üzerinde test et.
4. Fusion scorer'ı bir `user_feedback` boyutu (alınan kayıtlara thumbs-up) içerecek şekilde taşı. Oyun'u (agent yalnızca beğendiği kayıtları döndürmesi) nasıl önlersin?
5. Mem0 dokümanlarını oku (`docs.mem0.ai`). Oyuncağı `mem0` client çağrılarına taşı. Aynı 20 test sorgusunda retrieval kalitesini karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Hybrid memory | "Vector artı graph artı KV" | Paralel yazılan, retrieval'de birleştirilen üç store |
| Fact extraction | "Bellek ingestion" | Metni (entity, relation, fact) tuple'larına ayıran LLM adımı |
| Fusion skorlama | "Relevance sıralaması" | Relevance, importance, recency'nin ağırlıklı toplamı |
| Scope | "Bellek namespace" | user / session / agent — kimin neyi gördüğünü belirler |
| Mem0g | "Bellek grafiği" | İlişki sorguları için zamansal geçerlilikli tipli edge'ler |
| Temporal invalidation | "Soft delete" | Çelişen edge'leri invalid işaretle; asla silme |
| Embedding drift | "Retrieval rot" | Corpus büyüdükçe vector kalitesi degrade eder; periyodik yeniden-embed |

## İleri Okuma

- [Chhikara et al., Mem0 (arXiv:2504.19413)](https://arxiv.org/abs/2504.19413) — orijinal makale
- [Mem0 docs](https://docs.mem0.ai/platform/overview) — üretim API, SDK'lar, yönetilen bulut
- [Packer et al., MemGPT (arXiv:2310.08560)](https://arxiv.org/abs/2310.08560) — sanal-bağlam öncülü
- [Letta, Memory Blocks blog](https://www.letta.com/blog/memory-blocks) — üç-katmanlı kardeş tasarım
