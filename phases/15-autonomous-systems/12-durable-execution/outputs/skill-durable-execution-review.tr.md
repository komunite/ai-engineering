---
name: durable-execution-review
description: Önerilen uzun-süreli bir agent deployment'ını doğru durable-execution şekli için incele (activity'ler, determinism, checkpoint backend, human-input state, HITL-on-resume).
version: 1.0.0
phase: 15
lesson: 12
tags: [durable-execution, workflows, checkpointing, temporal, langgraph, agents-sdk]
---

Önerilen uzun-süreli bir agent deployment'ı (Temporal + OpenAI Agents SDK, PostgreSQL checkpointer'lı LangGraph, Microsoft Agent Framework, Claude Code Routines, Cloudflare Durable Objects veya in-house eşdeğeri) verildiğinde, tasarımı durable-execution pattern'ına karşı denetle.

Üret:

1. **Activity envanteri.** Her activity'yi (LLM çağrısı, tool çağrısı, HTTP isteği, dosya yazımı) listele. Her biri için, retry policy, timeout ve idempotency key ile activity olarak sarıldığını doğrula. Activity zarfının dışındaki ham LLM çağrıları bir güvenilirlik deliğidir.
2. **Workflow determinism'i.** Workflow kodu içindeki her non-deterministic read'i belirle (wall clock, random, harici state). Her biri side-effect activity olarak kaydedilmeli, böylece replay aynı değeri döndürür. Gizli non-determinism replay drift'inin en yaygın nedenidir.
3. **Checkpoint backend.** Backend'i adlandır (PostgreSQL, SQLite, Redis, Durable Objects). Deploy'ları atlattığını doğrula. SQLite yalnızca dev'dir. Redis AOF veya snapshot config gerektirir. Cloudflare Durable Objects şeffaftır ama benzersiz key disiplini gerektirir.
4. **Human-input state.** HITL pause'larının polling loop değil, first-class workflow state olduğunu doğrula. Workflow harici bir signal'da (approval queue, webhook, `interrupt()` primitive) blok olmalı, ve onay geldiğinde tam olarak devam etmeli.
5. **HITL-on-resume policy'si.** Bir crash'ten sonra herhangi bir resume için, bir sonraki activity execute olmadan önce taze HITL gerekli mi belirt. Bu olmadan, durable execution artı crash öncesi verilen bir onay, bağlam değiştiğinde onaylanmış bir eylemi yeniden tetikleyebilir. Uzun horizon'lar için kritiktir.

Sert reddetmeler:
- LLM çağrılarının activity olarak sarılmadığı Agent SDK kullanımı.
- Deploy'u atlatamayan checkpoint backend'leri.
- Wall clock veya random'ı activity sarmalaması olmadan gömen workflow'lar.
- Polling loop olarak modellenen human-input (signal yerine).
- HITL-on-resume policy'si olmayan uzun-horizon run'ları (bir saatin üzerinde).
- Durability'nin üzerine katmanlanmış bütçe kill switch'i olmayan run'lar (Lesson 13).

Reddetme kuralları:
- Kullanıcı side-effect activity'lerde açık idempotency olmadan bir durable workflow öneriyorsa, reddet ve önce idempotency key'leri iste. Aksi takdirde retry'lar çift-execute olur.
- Kullanıcı bir replay test'i gösteremezse (workflow'u çalıştır, run ortasında crash et, replay et, çift side effect olmadığını assert et), reddet ve production'dan önce o testi iste.
- Kullanıcı HITL checkpoint'i olmayan 24-saatlik unattended run öneriyorsa, reddet. 35-dakikalık degradation (Lesson 12 notları) durability doğru olsa bile bunu bir güvenilirlik sorunu yapar.

Çıktı formatı:

Şunları içeren bir tasarım-inceleme memo'su döndür:
- **Activity tablosu** (activity, retry policy, timeout, idempotency key)
- **Determinism denetimi** (non-deterministic read'ler ve her biri nasıl ele alındı)
- **Checkpoint backend** (ad, deploy'u atlatır y/n, replay-test durumu)
- **HITL state şekli** (first-class state / polling / eksik)
- **HITL-on-resume policy'si** (açık, gerekçeyle)
- **Hazırlık** (production / staging / yalnızca araştırma)
