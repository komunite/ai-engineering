---
name: virtual-memory
description: Doğru eviction, citation ve untrusted-input işleme ile herhangi bir hedef runtime için MemGPT-şekilli iki katmanlı bellek sistemi (main context + archival store + memory tools) iskelele.
version: 1.0.0
phase: 14
lesson: 07
tags: [memory, memgpt, virtual-context, archival, citations]
---

Bir hedef runtime (Python, Node, Rust), bir model provider (Anthropic, OpenAI, local) ve bir storage backend (in-memory, SQLite, vector DB, KV, graph) verildiğinde, doğru bir MemGPT-şekilli bellek sistemi üret.

Üret:

1. Bir `core` dict (isimlendirilmiş kalıcı bölümler) ve bir `messages` listesi (FIFO) içeren bir `MainContext` tipi. Boyut sınırında otomatik evict; evict edilen turlar `conversation_search` ile geri alınabilir kalır.
2. Ekleme ve arama içeren bir `ArchivalStore`. Kayıtlar `id`, `text`, `tags`, `session_id`, `turn_id`, `created_at` taşımalıdır. Her write, citation için saklanan id'yi döndürür.
3. MemGPT yüzeyiyle eşleşen beş memory tool'u: `core_memory_append`, `core_memory_replace`, `archival_memory_insert`, `archival_memory_search`, `conversation_search`. Modele her birinin ne zaman kullanılacağını söyleyen `description` metniyle sun.
4. Bir citation kontratı: her archival retrieval, metnin yanında record id'leri döndürmelidir VE agent bunları nihai cevaplarda alıntılamalıdır. Citation'sız cevaplar yumuşak bir başarısızlıktır.
5. Bir consolidation kancası (v1'de no-op olabilir) böylece Lesson 08 sleep-time agent'leri yeniden bağlantı kurmadan takılabilir. `list_records_since(timestamp)` ve `delete(id)` sun.

Sert ret durumları:

- Tam prompt'lu LLM scoring ile archival arama. Uygun bir retrieval backend kullan (BM25, vector similarity). LLM re-ranking yalnızca top-k shortlist üzerinde, tüm corpus üzerinde değil.
- Eviction politikası olmayan main context. Sınırsız main context sessizce pencerenin ötesine büyür.
- Geri alınan içeriği sanki kullanıcı talimatıymış gibi saklamak. Tüm archival içerik güvenilmez metindir (Lesson 27). Modele system prompt olarak değil, observation olarak ver.
- Tüm bölümleri silen bir `core_memory_clear` tool'u yazmak. Core load-bearing'dir; temizleme bir ayağa kurşun sıkmadır. `clear` değil, `replace` destekle.

Reddetme kuralları:

- Kullanıcı "citation yok, sadece cevaplar" isterse, kaynak atfının önemli olduğu herhangi bir alan için reddet (tıbbi, hukuki, politika, finansal). Bir uzlaşma sun: citation'lar inline yerine footnote olarak render edilsin.
- Kullanıcı "geri alınan tüm içeriği filtrelemeden archival'a geri yaz" isterse, reddet ve Lesson 27'ye yönlendir. Geri alınan içerik saldırgan-erişilebilirdir; toptan write-back memory poisoning'dir.
- Runtime'da persistence katmanı yoksa, "uzun süreli belleği" olduğu anlatılan bir agent göndermeyi reddet. Implementation'ı değil, ürün açıklamasını düşür.

Çıktı: bileşen başına bir dosya (`main_context.*`, `archival_store.*`, `memory_tools.*`, `agent.*`) artı eviction politikasını, citation kontratını ve Lesson 08'i (sleep-time consolidation) ve Lesson 09'u (Mem0 fusion) nereye takacağını açıklayan bir `README.md`. "Bundan sonra ne okumalı" notu ile bitir: agent üç katman veya async consolidation gerektiriyorsa Lesson 08, vector+KV+graph fusion gerektiriyorsa Lesson 09.
