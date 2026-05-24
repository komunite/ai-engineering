---
name: llm-observability
description: OpenTelemetry GenAI span'lerini alan, eval çalıştıran ve enjekte edilen regression'ları beş dakika altında yakalayan self-hosted LLM observability dashboard'u kur.
version: 1.0.0
phase: 19
lesson: 11
tags: [capstone, observability, otel, langfuse, phoenix, evals, drift, clickhouse]
---

En az altı SDK ailesinde (OpenAI, Anthropic, Google GenAI, LangChain, LlamaIndex, vLLM) production LLM trafiği verildiğinde, OTLP GenAI-semconv span'lerini alan, eval çalıştıran, drift tespit eden ve alarm veren self-hosted bir observability plane deploy et.

Build planı:

1. OTLP HTTP receiver, tail-sampling processor (hataların %100'ünü, başarının %10'unu, yüksek-toksisite/PII'nin %100'ünü tut), ClickHouse + S3'e exporter'lar ile OpenTelemetry Collector.
2. GenAI semconv'i yansıtan ClickHouse span şeması: gen_ai.system, gen_ai.request.model, usage.input/output_tokens, latency_ms, user_id, app_id artı prompt/completion için JSON bag.
3. App, user, session, annotation queue için Postgres metadata store.
4. SDK ailesi başına bir client app üzerinde OpenLLMetry auto-instrumentation; kanonik span'lerin geldiğini doğrula.
5. Sample edilmiş trace'ler üzerinde planlanan DeepEval + RAGAS + Phoenix evaluator paketi; PII ve off-policy için custom LLM-judge.
6. Pool edilmiş prompt embedding'leri üzerinde haftalık PSI / KL drift detector; 0.2 alarm eşiği.
7. Eval skor aggregate'leri ve latency yüzdelikleri için Prometheus exporter; Alertmanager'dan Slack'e (warning) + PagerDuty'ye (critical).
8. Next.js 15 App Router dashboard: overview, trace search + waterfall, eval trendleri, drift chart, alarmlar.
9. Regression probe: %1 oranında sahte SSN sızdıran yanıt örüntüsü enjekte et; MTTR'ı (alarm-tetikleme süresi) ölç.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Trace-şema kapsamı | Kanonik GenAI span üreten SDK ailelerinin sayısı (hedef 6+) |
| 20 | Eval doğruluğu | Elle etiketlenmiş sete karşı DeepEval / RAGAS skorları |
| 20 | Dashboard UX | Enjekte edilmiş regression'da MTTR (hedef 5 dakika altı) |
| 20 | Maliyet / scale | Backlog olmadan sürdürülen 1k span/sn ingest |
| 15 | Alarm + drift tespiti | Prometheus/Alertmanager zinciri uçtan uca egzersize edildi |

Sert ret durumları:

- OpenTelemetry GenAI semconv'da olmayan attribute name'leri uydurun span şemaları.
- Hataları düşüren tail-sampling politikaları (bilinen anti-pattern).
- Sampling olmadan ingest oranında çalışan eval'ler (kabul edilemez maliyet).
- p50/p95/p99 ayrımı olmadan "latency" gösteren dashboard'lar.

Reddetme kuralları:

- PII redaction politikası olmadan prompt veya completion persist etmeyi reddet.
- SDK başına kanonik span regression testi olmadan "multi-SDK desteği" iddia etmeyi reddet.
- Baseline window olmadan drift detection göndermeyi reddet; zero-shot drift kullanışsızdır.

Çıktı: collector config'i, ClickHouse şeması, Next.js 15 dashboard'u, eval job'ları, drift detector, alarm zinciri, annotated regression'larla 10k-trace demo dataset'i ve enjekte edilen PII regression'ı için MTTR'ı belgeleyen artı iterasyon boyunca MTTR'ı düşüren en kritik üç dashboard UX iyileştirmesini içeren bir yazımı içeren bir repo.
