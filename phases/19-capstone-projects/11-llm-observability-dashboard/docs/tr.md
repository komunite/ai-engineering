# Capstone 11 — LLM Observability & Eval Dashboard'u

> Langfuse open-core oldu. Arize Phoenix 2026 GenAI semconv mapping'lerini yayınladı. Helicone ve Braintrust her ikisi de per-user maliyet attribution'a yöneldi. Traceloop'un OpenLLMetry'si de-facto SDK instrumentation oldu. Üretim şekli trace'ler için ClickHouse, metadata için Postgres, UI için Next.js ve örneklenmiş trace'ler üzerinde çalışan küçük bir eval job ordusu (DeepEval, RAGAS, LLM-judge). Bir tane self-hosted inşa et, en az dört SDK ailesinden ingest et ve enjekte edilen bir regresyonu beş dakika altında yakaladığını göster.

**Tür:** Bitirme
**Diller:** TypeScript (UI), Python / TypeScript (ingest + eval'ler), SQL (ClickHouse)
**Ön koşullar:** Faz 11 (LLM engineering), Faz 13 (tools), Faz 17 (infrastructure), Faz 18 (safety)
**Egzersize edilen fazlar:** P11 · P13 · P17 · P18
**Süre:** 25 saat

## Sorun

2026'da üretim trafiği çalıştıran her yapay zeka ekibi modelin yanında bir observability plane'i tutar. Cost attribution. Hallucination tespiti. Drift monitoring. Jailbreak sinyali. SLO dashboard'ları. PII leak alert'leri. Açık kaynak referansları — Langfuse, Phoenix, OpenLLMetry — ingest şeması olarak OpenTelemetry GenAI semantic conventions'a yakınsadı. Artık OpenAI, Anthropic, Google, LangChain, LlamaIndex ve vLLM'i tek bir SDK ile instrument edebilir ve uyumlu span'lar gönderebilirsin.

En az dört SDK ailesinden ingest eden, örneklenmiş trace'ler üzerinde küçük bir eval job set'i çalıştıran, drift tespit eden ve alert veren bir self-hosted dashboard inşa edeceksin. Ölçüm çıtası: kasıtlı enjekte edilen bir regresyon (PII üretmeye başlayan bir prompt) verildiğinde, dashboard onu yakalar ve beş dakika altında bir alert ateşler.

## Kavram

Ingest OTLP HTTP. SDK GenAI-semconv span'ları üretir: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.response.id`, `llm.prompts`, `llm.completions`. Span'lar columnar analytics için ClickHouse'a iner; metadata (kullanıcılar, oturumlar, uygulamalar) Postgres'e iner.

Eval'ler örneklenmiş trace'ler üzerinde batch job'lar olarak çalışır. DeepEval faithfulness, toxicity ve answer relevance skorlar. RAGAS, trace retrieval context taşırken retrieval metriklerini skorlar. Custom LLM-judge'ler domain-spesifik kontroller çalıştırır (PII leak, off-policy yanıt). Eval run'lar aynı ClickHouse'a parent trace'e linked eval span'ları olarak geri yazar.

Drift tespiti zaman boyunca embedding-uzayı dağılımlarını izler (prompt embedding'lerinde PSI veya KL divergence) artı eval-skor trendleri. Alert'ler Prometheus Alertmanager'a ve sonra Slack / PagerDuty'a besler. UI Recharts'lı Next.js 15.

## Mimari

```
üretim uygulamaları:
  OpenAI SDK  +  Anthropic SDK  +  Google GenAI SDK
  LangChain + LlamaIndex + vLLM
       |
       v
  GenAI semconv'lı OpenTelemetry SDK
       |
       v  OTLP HTTP
  collector (ingest, sample, fan-out)
       |
       +-------------+-----------+
       v             v           v
   ClickHouse    Postgres    S3 archive
   (span'lar)    (metadata)  (raw event'ler)
       |
       +---> eval job'ları (DeepEval, RAGAS, LLM-judge)
       |     örneklenmiş veya tüm-trace
       |     eval span'larını geri yaz
       |
       +---> drift detector (prompt embedding'lerinde PSI / KL)
       |
       +---> Prometheus metrik'leri -> Alertmanager -> Slack / PagerDuty
       |
       v
   Next.js 15 dashboard (Recharts)
```

## Stack

- Ingest: GenAI semantic conventions'lı OpenTelemetry SDK'ları; OTLP HTTP transport
- Collector: tail-sampling processor'lı OpenTelemetry Collector (maliyet kontrolü için)
- Storage: span'lar için ClickHouse, metadata için Postgres, raw event arşivi için S3
- Eval'ler: DeepEval, RAGAS 0.2, Arize Phoenix evaluator pack, custom LLM-judge
- Drift: pool'lanmış prompt embedding'lerinde PSI / KL (sentence-transformers) haftalık
- Alerting: Prometheus Alertmanager -> Slack / PagerDuty
- UI: Next.js 15 App Router + Recharts + server action'ları
- Out of the box desteklenen SDK'lar: OpenAI, Anthropic, Google GenAI, LangChain, LlamaIndex, vLLM

## İnşa Et

1. **Collector config.** OTLP HTTP receiver'lı, errored trace'lerin %100'ünü ve başarıların %10'unu tutan bir tail-sampler'lı ve ClickHouse ve S3'e exporter'lı OpenTelemetry Collector.

2. **ClickHouse şeması.** GenAI semconv'ı yansıtan column'larla `spans` tablosu: `gen_ai_system`, `gen_ai_request_model`, `input_tokens`, `output_tokens`, `latency_ms`, `prompt_hash`, `trace_id`, `parent_span_id`, artı uzun payload'lar için JSON bag. user_id ve app_id ile secondary index'ler ekle.

3. **SDK kapsam testi.** OpenLLMetry auto-instrument ile her SDK'yı (OpenAI, Anthropic, Google, LangChain, LlamaIndex, vLLM) kullanan küçük bir client uygulaması yaz. Her birinin ClickHouse'a inen kanonik GenAI span'ları ürettiğini doğrula.

4. **Eval job'ları.** Scheduled bir job son-15-dk örneklenmiş trace'leri okur ve DeepEval faithfulness, toxicity ve answer relevance çalıştırır. Çıktılar parent trace'e linked eval span'ları.

5. **Custom LLM-judge.** Bir PII-leak judge'i: bir yanıt verildiğinde, PII leak olasılığını skorlamak için bir guard LLM çağır. Yüksek-skorlu yanıtlar bir triage queue'una iner.

6. **Drift tespiti.** Haftalık job bu haftanın pool'lanmış prompt embedding'leri ile takip eden 4-haftalık baseline arasındaki PSI'yi hesaplar. PSI eşik üzerindeyse, alert.

7. **Dashboard.** Sayfalı Next.js 15: overview (span/sec, kullanıcı başına maliyet, p95 gecikme), trace'ler (arama + waterfall), eval'ler (faithfulness trendi, toxicity), drift (zaman boyunca PSI), alert'ler.

8. **Alerting zinciri.** Prometheus exporter eval skor aggregate'lerini ve latency percentile'larını okur; Alertmanager warning'leri için Slack'e ve kritik ihlaller için PagerDuty'a route eder.

9. **Regresyon probe'u.** Bir bug enjekte et: değerlendirilen chatbot zamanın %1'inde sahte SSN sızdırmaya başlar. MTTR ölç: bug deploy'undan Slack alert'ine.

## Kullan

```
$ curl -X POST https://my-otel-collector/v1/traces -d @trace.json
[collector]  1 trace, 3 span kabul edildi
[clickhouse] 3 span insert edildi (app=chat, user=u_42)
[eval]       DeepEval faithfulness 0.82, toxicity 0.03
[drift]      haftalık PSI 0.08 (0.2 eşiğinin altında)
[ui]         canlı https://obs.example.com
```

## Yayınla

Teslimat `outputs/skill-llm-observability.md`. Bir LLM uygulaması verildiğinde, dashboard onun trace'lerini ingest eder, eval'ler çalıştırır, drift'te alert verir ve Next.js'te maliyet/kullanıcı breakdown'u yüzeyler.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Trace-şema kapsamı | Kanonik GenAI span'ları üreten SDK aile sayısı (hedef: 6+) |
| 20 | Eval doğruluğu | El-etiketli set'e karşı DeepEval / RAGAS skorları |
| 20 | Dashboard UX'i | Enjekte edilen regresyonda MTTR (5 dakika altı hedef) |
| 20 | Maliyet / ölçek | 1k span/sec sürdürülen ingest, backlog yok |
| 15 | Alerting + drift tespiti | Prometheus/Alertmanager zinciri uçtan uca egzersiz edildi |
| **100** | | |

## Alıştırmalar

1. Haystack framework'ü için custom instrumentation ekle. Sadık `gen_ai.*` attribute'larıyla kanonik span'ların ClickHouse'a indiğini doğrula.

2. Aynı trace'lerde DeepEval'i Phoenix evaluator'lara değiştir. İki eval motoru arasında skor drift'ini ölç.

3. Drift detector'ı keskinleştir: PSI'yi global yerine app-id başına hesapla. Per-app drift trail'leri göster.

4. Bir "user impact" sayfası ekle: sparkline'larla kullanıcı başına maliyet ve kullanıcı başına başarısızlık oranı.

5. Toxicity > 0.5 olan trace'lerin %100'ünü artı geri kalanın %10'luk stratified örneklenmiş bir tail-sampling policy'si inşa et. Tanıtılan sampling bias'ını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| GenAI semconv | "OTel LLM attribute'ları" | LLM span attribute'ları için 2025 OpenTelemetry spec'i (system, model, token'lar) |
| Tail sampling | "Post-trace sample" | Collector bir trace'i tamamlandıktan sonra tutmaya veya düşürmeye karar verir (hataları gözetleyebilir) |
| PSI | "Population stability index" | İki dağılımı karşılaştıran drift metriği; > 0.2 tipik olarak anlamlı drift sinyali verir |
| LLM-judge | "Model olarak eval" | Bir rubrik üzerinde başka bir LLM'in çıktısını skorlayan bir LLM (faithfulness, toxicity, PII) |
| Tail-sampling policy | "Keep-rule" | Hangi trace'lerin persist edileceğine veya düşürüleceğine karar veren kural; errored + sample-rate |
| Eval span | "Linked eval trace" | Orijinal LLM çağrı span'ına linked bir eval skoru taşıyan child span |
| Cost per user | "Unit economics" | Bir window üzerinde bir user_id'ye atfedilen dolar maliyeti; kilit ürün metriği |

## İleri Okuma

- [Langfuse](https://github.com/langfuse/langfuse) — referans open-core observability platformu
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — güçlü drift destekli alternatif referans
- [OpenLLMetry (Traceloop)](https://github.com/traceloop/openllmetry) — auto-instrumentation SDK ailesi
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — ingest şeması
- [Helicone](https://www.helicone.ai) — alternatif hosted observability
- [Braintrust](https://www.braintrust.dev) — alternatif eval-öncelikli platform
- [ClickHouse dokümantasyonu](https://clickhouse.com/docs) — columnar span store
- [DeepEval](https://github.com/confident-ai/deepeval) — evaluator kütüphanesi
