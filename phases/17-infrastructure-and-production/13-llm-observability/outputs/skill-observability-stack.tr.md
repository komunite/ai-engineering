---
name: observability-stack
description: Stack, ölçek, bütçe ve lisans tutumu verildiğinde bir LLM observability stack'i (geliştirme platformu + gateway + opsiyonel ölçek katmanı) seç ve OpenTelemetry GenAI öznitelik setini tanımla.
version: 1.0.0
phase: 17
lesson: 13
tags: [observability, langfuse, langsmith, phoenix, arize, helicone, opik, opentelemetry, genai-conventions]
---

Stack (LangChain / DSPy / ham SDK), ölçek (trace/gün), bütçe, lisans tutumu (yalnızca MIT vs ticari OK) ve self-host gereksinimi verildiğinde, bir observability planı üret.

Üret:

1. Geliştirme platformu seçimi. Langfuse (OSS), LangSmith (LangChain-öncelikli ticari), Opik (Comet OSS) veya hiçbiri. Stack ve lisansla gerekçelendir.
2. Gateway/telemetry seçimi. Helicone (proxy + gateway), SigNoz (tam APM), OpenLLMetry (saf OTel). Zaten bir AI gateway (Phase 17 · 19) kullanılıyorsa, entegrasyonu adlandır.
3. Ölçek/lake katmanı. Opsiyonel; uzun vadeli analitik için Arize AX veya ham Iceberg, RAG drift için Phoenix.
4. OTel GenAI konvansiyonları. Minimum öznitelik setini belirt: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.request.temperature`, `gen_ai.response.finish_reasons`, artı organizasyona özgü (tenant_id, user_id, task).
5. Sampling politikası. %100 hata, %100 yüksek-maliyet (>$0.10/çağrı), %N başarı sampling oranı. Ham-saklama penceresi (14g / 30g / 90g). Agregalar daha uzun tutulur.
6. Alarm. Alarmı olması gereken beş metrik: hata oranı, P99 TTFT, istek başına maliyet, prompt-cache hit oranı, refusal oranı.

Hard rejects:
- OTel fallback olmadan framework-spesifik SDK içinde enstrümantasyon. Reddet — framework lock-in.
- Regüle olmayan bir iş yükü için >$500/ay Datadog-sınıfı fiyatlandırmada trace'lerin %100'ünü tutmak. Reddet — sampling öner.
- OpenTelemetry GenAI konvansiyonlarını görmezden gelmek. Reddet — 2026 interop bunları gerektirir.

Reddetme kuralları:
- Trace/gün > 5M ve takım tam Datadog saklamasında ısrar ederse, maliyet projeksiyonu olmadan reddet.
- Takım yalnızca MIT ise ve LangSmith seçerse, reddet — MIT eşdeğeri Langfuse'dur.
- Takımın AI gateway'i yoksa ve Helicone'u gateway VE observability olarak seçerse, kabul et — proxy ~500 RPS'e kadar gateway olarak çift görev yapar (Phase 17 · 19 gateway ölçeğini kapsar).

Çıktı: dev platformu, gateway, ölçek katmanı (varsa), OTel öznitelik seti, sampling kuralı, beş alarmı adlandıran tek sayfalık plan. Stack drift'ini sinyalleyen tek metrikle bitir: son 7 günde tam OTel GenAI öznitelikleriyle LLM çağrılarının yüzdesi.
