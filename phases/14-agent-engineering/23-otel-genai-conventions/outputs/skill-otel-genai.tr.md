---
name: otel-genai
description: Bir agent'ı OpenTelemetry GenAI semantic convention'larıyla enstrümante et — doğru niteliklerle ve opt-in içerik yakalamayla invoke_agent, chat, tool_call span'leri.
version: 1.0.0
phase: 14
lesson: 23
tags: [opentelemetry, genai, observability, tracing, semantic-conventions]
---

Bir agent runtime verildiğinde, OTel GenAI semantic convention'larını bağla.

Üret:

1. Agent çalıştırması başına `invoke_agent` span'i. Remote agent servisleri için Kind CLIENT, in-process için INTERNAL. İsim: `invoke_agent {gen_ai.agent.name}`.
2. LLM çağrısı başına `chat` span'i, `gen_ai.operation.name=chat`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model` ile.
3. Tool çağrısı başına `tool_call` span'i, `gen_ai.tool.name` ile ve uygulanabilir olduğunda `gen_ai.data_source.id` (RAG corpus / memory store).
4. Opt-in içerik yakalaması: varsayılan KAPALI; AÇIK olduğunda, input/output'ları harici sakla ve span'lerde `*.reference_id` kaydet.
5. Context yayılımı: çoklu süreç çalıştırmalarının (Claude Agent SDK CLI subprocess) tek bir trace'e bağlanması için W3C trace context header'larını kullan.

Sert ret durumları:

- Varsayılan olarak tam prompt'ları/output'ları inline yakalama. PII ve secret sızıntı riski; ayrıca spec'i ihlal eder.
- Eksik `gen_ai.provider.name`. Çoklu-provider dashboard'ları bozulur.
- Yetim tool span'leri. Aktif context aracılığıyla her zaman parent-child ilişkisini ayarla.

Reddetme kuralları:

- Runtime context'i süreç sınırları arasında yayamıyorsa, reddet. Claude Agent SDK + CLI kullanıcıları için çoklu süreç trace bağlantısı gereklidir.
- Ürünün düzenleyici kısıtları varsa (HIPAA, GDPR), inline içerik yakalamasını reddet. Yalnızca erişim kontrollü harici store.
- Backend `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` ayarlamıyorsa, uyar: collector yükseltmesinde attribute isimleri değişebilir.

Çıktı: `tracer.py`, `attributes.py`, `content_store.py`, span yapısını, stability opt-in'ini ve içerik yakalama politikasını açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 24 (backend'ler: Langfuse, Phoenix, Opik) veya Claude Agent SDK trace-context yayılımı için Lesson 17.
