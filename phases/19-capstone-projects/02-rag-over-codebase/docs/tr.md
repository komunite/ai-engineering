# Capstone 02 — Codebase Üzerinde RAG (Cross-Repo Semantik Arama)

> 2026'da her ciddi mühendislik organizasyonu, sadece string'leri değil anlamı anlayan dahili bir kod arama çalıştırıyor. Sourcegraph Amp, Cursor'ın codebase yanıtları, Augment'ın enterprise graph'ı, Aider'ın repomap'i, Pinterest'in dahili MCP'si — aynı şekil. Çok sayıda repo'yu ingest et, tree-sitter ile parse et, function- ve class-seviyesinde chunk'ları embed et, hybrid-search yap, re-rank uygula, citation'larla cevapla. Bu capstone senden 10 repo boyunca 2M satır kodu işleyen ve her git push'ta incremental re-indexing'i atlatan bir tane inşa etmeni istiyor.

**Tür:** Bitirme
**Diller:** Python (ingestion), TypeScript (API + UI)
**Ön koşullar:** Faz 5 (NLP temelleri), Faz 7 (transformer'lar), Faz 11 (LLM engineering), Faz 13 (tools), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P5 · P7 · P11 · P13 · P17
**Süre:** 30 saat

## Sorun

2026'ya gelindiğinde her frontier coding agent bir codebase retrieval katmanıyla geliyor çünkü context window'lar tek başına cross-repo soruları çözmüyor. Claude'un 1M-token context'i yardımcı oluyor; sıralı retrieval ihtiyacını ortadan kaldırmıyor. Ham chunk'lar üzerinde naif cosine arama; generated code'da, monorepo duplikasyonunda ve nadiren import edilen sembollerin long tail'inde sonuçları zehirler. Üretimdeki cevap, AST-aware chunk'lar üzerinde re-ranker'lı hybrid (dense + BM25) arama, arkasında sembol referansları graph'ıyla.

Bunu, bir tutorial repo'su değil, gerçek bir fleet'i index'leyerek ve MRR@10'u, citation faithfulness'ı ve incremental freshness'ı ölçerek öğreniyorsun. Başarısızlık modları altyapısal: 100k-dosyalık bir monorepo, dosyaların yarısına tekrar dokunan bir push, doğru cevaplamak için dört repo'yu geçmesi gereken bir sorgu.

## Kavram

AST-aware bir ingestion pipeline'ı her dosyayı tree-sitter ile parse eder, function ve class node'larını çıkarır ve sabit token window'ları yerine node sınırlarında chunk'lar. Her chunk üç gösterim alır: bir dense embedding (Voyage-code-3 veya nomic-embed-code), sparse BM25 terimleri ve kısa bir doğal-dil özeti. Özet, üçüncü bir retrievable modalite ekler — kullanıcılar "X nasıl yetkilendiriliyor" diye sorduğunda, kod sadece `check_permission`'a sahip olsa bile özet "authz"den bahseder.

Retrieval hybrid'dir. Bir sorgu hem dense hem BM25 aramasını ateşler, top-k'yi birleştirir ve birleşimi bir cross-encoder re-ranker'a (Cohere rerank-3 veya bge-reranker-v2-gemma-2b) verir. Re-rank'li liste, her iddianın dosya ve satır aralığıyla citation verilmesi talimatıyla long-context bir sentezleyiciye (prompt caching'li Claude Sonnet 4.7 veya self-hosted Llama 3.3 70B) gider. Citation'sız cevaplar bir post-filter tarafından reddedilir.

Incremental freshness altyapı sorunu. Git push bir diff tetikler: hangi dosyalar değişti, hangi semboller değişti. Sadece etkilenen chunk'lar yeniden embed edilir. Etkilenen cross-file sembol kenarları (import'lar, method çağrıları) yeniden hesaplanır. Index, her commit'te 2M satırı yeniden işlemeden tutarlı kalır.

## Mimari

```
git push --> webhook --> ingest worker (LlamaIndex Workflow)
                           |
                           v
             tree-sitter parse + AST chunk
                           |
            +--------------+----------------+
            v              v                v
          dense        BM25 index       özet (LLM)
        (Voyage / bge)  (Tantivy)        (Haiku 4.5)
            |              |                |
            +------> Qdrant / pgvector <----+
                            |
                            v
                      sembol graph (Neo4j / kuzu)
                            |
  sorgu --> LangGraph agent (retrieve -> rerank -> synth)
                            |
                            v
                 Claude Sonnet 4.7 1M context
                            |
                            v
                 cevap + dosya:satır citation'ları
```

## Stack

- Parsing: 17 dil grammar'ıyla tree-sitter (Python, TS, Rust, Go, Java, C++, vs.)
- Dense embedding'ler: Voyage-code-3 (hosted) veya nomic-embed-code-v1.5 (self-host), bge-code-v1 fallback
- Sparse index: sembol ismi vs gövde üzerinde field-weighted BM25F ile Tantivy (Rust)
- Vector DB: hybrid search ile Qdrant 1.12 veya 50M vektör altındaki ekipler için pgvector + pgvectorscale
- Chunk özet modeli: Claude Haiku 4.5 veya Gemini 2.5 Flash, prompt-cached
- Re-ranker: Cohere rerank-3 veya self-hosted bge-reranker-v2-gemma-2b
- Orkestrasyon: ingestion için LlamaIndex Workflows, sorgu agent'ı için LangGraph
- Sentezleyici: prompt caching'li Claude Sonnet 4.7 (1M context)
- Sembol graph'ı: import ve call kenarları için Neo4j (managed) veya kuzu (embedded)
- Observability: retrieval + synthesis adımı başına Langfuse span'ları

## İnşa Et

1. **Ingestion walker.** Her push hook'unda git history'yi iterate et. Değişen dosyaları topla. Her dosyayı tree-sitter ile parse et, full source span'larıyla function ve class node'larını çıkar. Chunk kayıtları emit et `{repo, path, start_line, end_line, symbol, body}`.

2. **Chunk özetleyici.** System preamble üzerinde prompt caching ile chunk'ları Haiku 4.5 çağrılarına batch'le. Prompt: "Bu fonksiyonu tek cümlede özetle, public contract'ını ve side effect'lerini isimlendir." Özeti chunk'la birlikte sakla.

3. **Embedding havuzu.** İki paralel kuyruk: dense (Voyage-code-3 batch 128) ve özet (aynı model, ama özet string'inde). Vektörleri Qdrant'a payload `{repo, path, start_line, end_line, symbol, kind}` ile yaz.

4. **BM25 index.** Field-weighted Tantivy index: sembol ismi ağırlık 4, sembol gövdesi ağırlık 1, özet ağırlık 2. "X adlı fonksiyonu bul" sorgularını "X yapan fonksiyonu bul" sorgularıyla birlikte mümkün kılar.

5. **Sembol graph'ı.** Her chunk için kenarları kaydet: import'lar (bu dosya repo Z'den Y sembolünü kullanır), call'lar (bu fonksiyon C sınıfında M method'unu çağırır), inheritance. kuzu'da sakla. Sorgu zamanında retrieval'ı repo sınırları arasında genişletmek için kullanılır.

6. **Sorgu agent'ı.** Üç node'lu LangGraph. `retrieve` paralel olarak dense + BM25 ateşler, (repo, path, symbol) ile dedup'lar. `rerank` top-50'de cross-encoder çalıştırır ve top-10'u tutar. `synth` reranked chunk'ları context'te tutarak Claude Sonnet 4.7'yi çağırır, system prompt'u cache'ler, dosya:satır citation'ları zorunlu kılar.

7. **Citation zorlaması.** Model çıktısını parse et; `(repo/path:start-end)` anchor'ı olmayan herhangi bir iddia yeniden-sorma için flag'lenir veya düşürülür. Kullanıcıya sadece-citation'lı cevap döndür.

8. **Incremental re-index.** Her webhook'ta sembol-seviyesinde diff hesapla. Sadece metni değişen chunk'ları yeniden embed et. Import'ları değişen chunk'lar için sembol kenarlarını yeniden hesapla. Ölç: 2M-LOC'luk bir fleet için 50-dosyalık bir push 60 saniyenin altında yeniden index'lenmiş.

9. **Eval.** 100 cross-repo sorusunu gold dosya:satır cevaplarıyla etiketle. MRR@10, nDCG@10, citation faithfulness (doğrulanabilir anchor'lı iddiaların oranı) ve p50/p99 gecikme ölç.

## Kullan

```
$ code-rag ask "S3 multipart abort retry bütçemize nasıl bağlanmış?"
[retrieve]  12 dense chunk + 7 bm25 chunk, dedup sonrası 16 benzersiz
[rerank]    top-5 tutuldu (cohere rerank-3)
[synth]     claude-sonnet-4.7, cache hit oranı %68, 2.1s
cevap:
  Multipart abort'lar services/uploader/retry.go:122-148'deki
  `AbortMultipartOnFail` tarafından tetikleniyor, bu da
  config/budgets.yaml:34-51'de tanımlı per-bucket retry bütçesini düşürüyor...
  citation'lar: [services/uploader/retry.go:122-148, config/budgets.yaml:34-51,
              libs/s3client/multipart.ts:44-61]
```

## Yayınla

Teslim skill'i `outputs/skill-codebase-rag.md`. Bir repo korpusu verildiğinde, ingestion pipeline'ını, hybrid index'i ve sorgu agent'ını ayağa kaldırır ve herhangi bir cross-repo sorusu için citation'lı bir cevap döndürür. Rubrik:

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Retrieval kalitesi | 100-soruluk holdout set'te MRR@10 ve nDCG@10 |
| 20 | Citation faithfulness'ı | Doğrulanabilir dosya:satır anchor'lı cevap iddialarının oranı |
| 20 | Latency ve ölçek | Index'lenen korpus boyutunda 10k QPS'te p95 sorgu gecikmesi |
| 20 | Incremental indexing doğruluğu | 50-dosyalık commit'te git push'tan aranabilir olmaya kadar geçen süre |
| 15 | UX ve cevap formatlama | Citation tıklanabilirliği, snippet preview'leri, takip imkanı |
| **100** | | |

## Alıştırmalar

1. Voyage-code-3'ü self-hosted nomic-embed-code ile değiştir. MRR@10 delta'sını ölç. Re-ranking enable edildiğinde gap'in kapanıp kapanmadığını raporla.

2. Korpusa %20 generated code (LLM-üretimi boilerplate) enjekte et ve yeniden değerlendir. Retrieval zehirlenmesini gözlemle. Payload'a bir "generated" flag ekle ve o hit'leri down-weight et.

3. Senin korpus boyutunda Qdrant hybrid search vs pgvector + pgvectorscale benchmark et. Batch size 1'de p99 raporla.

4. Sampling-tabanlı drift check ekle: haftalık olarak 100-soruluk eval'i yeniden çalıştır. MRR@10 düşüşü > %5'te alert ver.

5. Cross-language sembol çözümüne extend et: gRPC üzerinden bir Go service'i çağıran bir Python fonksiyonu. Onları linklemek için sembol graph'ını kullan.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| AST-aware chunking | "Function-seviyesinde split'ler" | Sabit token window'ları yerine tree-sitter node sınırlarında kodu kesme |
| Hybrid search | "Dense + sparse" | BM25 ve vector search'ü paralel çalıştır, top-k birleştir, rerank et |
| Cross-encoder rerank | "İkinci aşama sıralama" | Her (query, candidate) çiftini birlikte skorlayan model, cosine'dan daha doğru |
| Prompt caching | "Cache'lenmiş system prompt" | 2026 Claude / OpenAI özelliği; tekrarlayan prefix token'larını %90'a kadar indirim yapar |
| Sembol graph'ı | "Code graph" | Dosyalar ve repo'lar arasında import'lar, call'lar, inheritance için kenarlar |
| Citation faithfulness | "Grounded answer rate" | Kullanıcının anchor'a tıklayıp referans verilen span'i okuyarak doğrulayabileceği iddiaların oranı |
| Incremental re-index | "Push-to-search süresi" | git push'tan değişen sembollerin sorgulanabilir olmasına kadar geçen wall-clock |

## İleri Okuma

- [Sourcegraph Amp](https://ampcode.com) — üretim cross-repo kod intelligence
- [Sourcegraph Cody RAG mimarisi](https://sourcegraph.com/blog/how-cody-understands-your-codebase) — bu capstone için referans deep-dive
- [Aider repo-map](https://aider.chat/docs/repomap.html) — tree-sitter ranked repo view
- [Augment Code enterprise graph](https://www.augmentcode.com) — ticari sembol-graph RAG
- [Qdrant hybrid search dokümantasyonu](https://qdrant.tech/documentation/concepts/hybrid-queries/) — referans implementasyon
- [Voyage AI code embedding'leri](https://docs.voyageai.com/docs/embeddings) — Voyage-code-3 detayları
- [Cohere rerank-3](https://docs.cohere.com/reference/rerank) — cross-encoder referansı
- [Pinterest MCP dahili arama](https://medium.com/pinterest-engineering) — dahili-platform referansı
