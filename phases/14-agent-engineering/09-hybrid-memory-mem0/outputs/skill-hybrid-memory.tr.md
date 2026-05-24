---
name: hybrid-memory
description: Bir fusion scorer, scope taksonomisi ve temporal invalidation ile Mem0-şekilli üç-store bellek sistemi (vector + KV + graph) üret.
version: 1.0.0
phase: 14
lesson: 09
tags: [memory, mem0, vector, graph, kv, fusion, scope]
---

Bir hedef runtime, bir vector backend (Qdrant, pgvector, Chroma, sqlite-vec), bir KV backend (Postgres, Redis, dict) ve bir graph backend (Neo4j, in-memory edges) verildiğinde, fuse edilmiş bir bellek sistemi üret.

Üret:

1. Bir `add(text, user_id, session_id, scope, importance, tags)` cephesi arkasında üç store sınıfı. Write'da, extractor `text`'i kayıtlara, KV triple'larına ve graph triple'larına ayrıştırır. Hiçbir store opsiyonel değildir.
2. Bir fusion scorer `score = w_rel * relevance + w_imp * importance + w_rec * recency`. Üç ağırlığı da config olarak sun. Çağrı başına değil, ürün başına ayarla.
3. Scope taksonomisi: `user`, `session`, `agent`. Retrieval scope'a uymalıdır. Bir kullanıcı sorgusu asla başka bir kullanıcının kayıtlarını sızdırmamalıdır.
4. Temporal invalidation. Çelişkiler eski edge'leri/kayıtları invalid olarak işaretler; asla silme. Tarihsel sorgular için `search(query, as_of=timestamp)` sun.
5. Bir extractor arayüzü. Varsayılan LLM-tabanlı olabilir; testler için deterministik regex fallback'ine izin ver. Patlamayı önlemek için `add()` başına graph edge'lerini sınırla.

Sert ret durumları:

- "Mem0-şekilli" olarak tarif edilen tek-store bellek. Yalnızca vector, yalnızca KV, yalnızca graph ürünleri tamamdır ama hybrid memory değildir. Yanlış isimlendirme.
- Scope başına ağırlıklar veya açık `scope=` filtresi olmadan cross-scope retrieval. Scope sızıntısı bir compliance ve gizlilik olayıdır.
- Çelişkide silmek. Invalidate et ve time-stamp at. Silme bug'ları gizler ve denetimleri bozar.

Reddetme kuralları:

- Kullanıcı "importance ağırlığı yok" isterse, reddet. Milyon kayıt üzerinde flat relevance ranking bekleyen bir retrieval başarısızlığıdır.
- Graph backend'in çelişki dedektörü yoksa, ortaya çıkan sistemi "Mem0-şekilli" olarak adlandırmayı reddet. İsmi düşür.
- Ürün PII içeriyorsa (tıbbi, hukuki, HR), ürün sahibi tarafından denetlenmemiş bir extractor ile göndermeyi reddet.

Çıktı: store başına bir dosya artı `memory.py` (cephe), `config.py` (ağırlıklar), fusion ağırlıklarını, scope politikasını, extractor kontratını ve invalidation semantiklerini açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: agent yeni skill'ler öğrenmesi gerekiyorsa Lesson 10, memory operasyonlarında OTel span'leri gerekiyorsa Lesson 23 veya retrieval'da untrusted-input işleme için Lesson 27.
