---
name: codebase-rag
description: AST-aware chunking, hybrid retrieval, incremental yeniden index'leme ve atıflı yanıtlarla cross-repo semantic search sistemi kur.
version: 1.0.0
phase: 19
lesson: 02
tags: [capstone, rag, code-search, tree-sitter, qdrant, bm25, hybrid-retrieval]
---

Toplamda en az 2M satır kod içeren 10+ repo verildiğinde, bir ingestion pipeline'ı, bir hybrid index ve doğrulanabilir file:line anchor'larıyla cross-repo soruları yanıtlayan citation-zorlamalı bir query agent kur.

Build planı:

1. Her dosyayı tree-sitter ile parse et. Function ve class node sınırlarında chunk'la. `{repo, path, start_line, end_line, symbol, body}` sakla.
2. Her chunk'ı prompt-cache'lenmiş system prompt'larla Claude Haiku 4.5 veya Gemini 2.5 Flash ile özetle. Tek cümlelik özeti chunk'ın yanında sakla.
3. Üç yapıya index'le: Qdrant (dense, Voyage-code-3 veya nomic-embed-code), Tantivy (alan ağırlıklı BM25) ve kuzu (import, call, inheritance için symbol graph edge'leri).
4. Üç node'lu bir LangGraph query agent kur: retrieve (paralel dense + BM25), rerank (Cohere rerank-3 veya bge-reranker-v2-gemma-2b), synth (prompt caching ve file:line citation zorunluluğuyla Claude Sonnet 4.7).
5. Post-filter: doğrulanabilir `(repo/path:start-end)` anchor'ı olmayan iddiayı reddet; yeniden sor ya da düş.
6. Symbol seviyesinde diff hesaplayan ve yalnızca değişen chunk'ları yeniden embed eden bir git push webhook bağla. Hedef: 2M-LOC filoda 50 dosyalık commit 60s altında aranabilir olsun.
7. 100 soruluk held-out set ile değerlendir. MRR@10, nDCG@10, citation sadakati ve latency yüzdeliklerini raporla.
8. Eval'i yeniden çalıştıran ve MRR@10 düşüşü %5'i aştığında alarm veren haftalık bir drift job çalıştır.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Retrieval kalitesi | 100 soruluk held-out set üzerinde MRR@10 ve nDCG@10 |
| 20 | Citation sadakati | Doğrulanabilir file:line anchor'ına sahip yanıt iddialarının oranı |
| 20 | Latency ve scale | Index'lenmiş corpus boyutunda 10k QPS'de p95 query latency |
| 20 | Incremental indexing doğruluğu | 50 dosyalık commit'te git push'tan aranabilir olmaya kadar geçen süre |
| 15 | UX ve yanıt formatlama | Citation tıklanabilirliği, snippet önizlemeleri, takip imkanı |

Sert ret durumları:

- AST-aware chunking yerine sabit boyutlu token chunking. Generated-code yoğun corpus'ları zehirler.
- BM25 veya rerank olmadan yalnızca cosine retrieval. Tam symbol-name sorgularında başarısız olduğu bilinir.
- Zorunlu file:line citation'ı olmayan yanıtlar.
- Her git push'ta full-corpus yeniden embedding; incremental olmak zorunda.

Reddetme kuralları:

- Lisansını okumadan repo index'lemeyi reddet. Bazıları üçüncü taraf vector store'larda embed etmeyi yasaklar.
- Index'in hiç görmediği dosyalara atıf yaptığını iddia eden sorgulara yanıt vermeyi reddet; her zaman anchor'ı dönmeden önce doğrula.
- p95'i 4s'nin üzerinde yanıt sunmayı reddet; bunun yerine takip handle'ı olan kısmi sonuç döndür.

Çıktı: ingestion pipeline'ını, LangGraph query agent'ını, 100 soruluk etiketli eval setini, Langfuse dashboard link'ini ve düzelttiğin üç retrieval failure mode'unu (generated-code zehirlenmesi, long-tail symbol recall, cross-repo symbol resolution) ve her birini düzelten kesin değişikliği adlandıran bir yazımı içeren bir repo.
