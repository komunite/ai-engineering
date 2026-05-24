---
name: obs-platform-wiring
description: Bir observability platformu (Langfuse, Phoenix, Opik, Datadog) seç ve trace'leri + eval'leri + prompt versiyonlarını mevcut bir agent'a bağla.
version: 1.0.0
phase: 14
lesson: 24
tags: [observability, langfuse, phoenix, opik, datadog, tracing]
---

Bir agent runtime ve ürün gereksinimleri verildiğinde, bir observability platformu seç ve bağlantıyı iskelele.

Karar:

1. Prompt yönetimi + session replay'i tek yerde gerek -> **Langfuse**.
2. Derin RAG relevancy + drift/anomali tespiti gerek -> **Phoenix**.
3. Otomatik prompt optimizasyonu + PII guardrails gerek -> **Opik**.
4. Zaten Datadog çalıştırıyorsun -> **Datadog LLM Observability** (v1.37+'dan itibaren GenAI'yi nativ olarak haritalar).
5. ELv2-free lisans gerek -> **Langfuse** (MIT) veya **Opik** (Apache 2.0); saf OSS dağıtım için Phoenix'ten kaçın.

Üret:

1. OTel GenAI enstrümantasyonu (Lesson 23) — bu, ortak alt katmandır.
2. Platforma özgü SDK veya OTel exporter yapılandırması.
3. Alanın için LLM-judge rubric'i (factual doğruluk, scope, ton, ret kalitesi).
4. Trace'lere bağlı prompt versiyonlama (Langfuse) veya trace clustering config'i (Phoenix) veya experiment tanımları (Opik).
5. Loglanan içerikte guardrails: PII redaksiyon, secret temizleme.
6. Dashboard'lar: session sağlığı, failure taksonomisi, latency dağılımı, session başına maliyet.

Sert ret durumları:

- Eval'siz göndermek. Tek başına tracing pahalı logging'dir.
- Harici doğrulama olmadan kendi yazdığın LLM-judge kullanmak. CRITIC pattern (Lesson 05): judge'ların factual grounding için harici tool'lara ihtiyacı var.
- PII'yi span gövdelerinde saklamak. Her zaman harici store + reference ID'ler.

Reddetme kuralları:

- Kullanıcı "her şey için tek platform" isterse, reddet ve yukarıdaki kararı sun. Hiçbir tek platform üç eksende de hakim değil.
- Ürünün her agent görevi için kabul kriteri yoksa, eval göndermeyi reddet. LLM-judge'ın rubric'e ihtiyacı var; rubric'in ürün kararlarına ihtiyacı var.
- Kullanıcı "sampling yok, her şeyi yakala" isterse, reddet. Trace hacmi trafikle lineer büyür; ölçekte sampling (head-based veya tail-based) gerekli.

Çıktı: `instrumentation.py`, `judge.py`, `dashboards.md`, platform seçimini, rubric'i, sampling stratejisini ve incident response'u açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 30 (eval-driven development) veya Lesson 26 (failure-mode taksonomisi).
