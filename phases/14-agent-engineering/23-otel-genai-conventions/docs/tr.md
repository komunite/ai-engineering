# OpenTelemetry GenAI Semantik Konvansiyonları

> OpenTelemetry'nin GenAI SIG'i (Nisan 2024 yayında) agent telemetrisi için standart şemayı tanımlar. Span adları, attribute'lar ve content-capture kuralları vendor'lar arasında yakınsar, böylece agent trace'leri Datadog, Grafana, Jaeger ve Honeycomb'da aynı anlama gelir.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 13 (LangGraph), Faz 14 · 24 (Observability Platform'ları)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- GenAI span kategorilerini adlandır: model/client, agent, tool.
- `invoke_agent` CLIENT vs INTERNAL span'leri ayır ve her birinin ne zaman uygulandığını.
- Top-level GenAI attribute'larını listele: provider name, request model, data-source ID.
- Content-capture kontratını açıkla: opt-in, `OTEL_SEMCONV_STABILITY_OPT_IN`, dış-referans önerisi.

## Sorun

Her vendor kendi span adlarını icat eder. Ops ekipleri framework-başına dashboard kurmakla biter. OpenTelemetry'nin GenAI SIG'i tüm ekosistemin hedeflediği bir standart tanımlayarak bunu düzeltir.

## Kavram

### Span kategorileri

1. **Model / client span'leri.** Ham LLM çağrılarını kapsar. Sağlayıcı SDK'ları (Anthropic, OpenAI, Bedrock) ve framework model adapter'ları tarafından yayılır.
2. **Agent span'leri.** `create_agent` (agent kurulduğunda) ve `invoke_agent` (çalıştığında).
3. **Tool span'leri.** Tool invocation başına bir; parent-child ilişkisi ile agent span'ine bağlı.

### Agent span adlandırma

- Span adı: adlandırılmışsa `invoke_agent {gen_ai.agent.name}`; fallback `invoke_agent`.
- Span kind:
  - **CLIENT** — remote agent service'ler için (OpenAI Assistants API, Bedrock Agents).
  - **INTERNAL** — in-process agent framework'ler için (LangChain, CrewAI, local ReAct).

### Anahtar attribute'lar

- `gen_ai.provider.name` — `anthropic`, `openai`, `aws.bedrock`, `google.vertex`.
- `gen_ai.request.model` — model ID.
- `gen_ai.response.model` — çözümlenmiş model (routing nedeniyle request'ten farklı olabilir).
- `gen_ai.agent.name` — agent identifier.
- `gen_ai.operation.name` — `chat`, `completion`, `invoke_agent`, `tool_call`.
- `gen_ai.data_source.id` — RAG için: hangi corpus ya da store sorgulandı.

Teknoloji-spesifik konvansiyonlar Anthropic, Azure AI Inference, AWS Bedrock, OpenAI için var.

### Content capture

Varsayılan kural: instrumentation'lar input'ları/output'ları varsayılan olarak yakalamamalı (SHOULD NOT). Yakalama şununla opt-in:

- `gen_ai.system_instructions`
- `gen_ai.input.messages`
- `gen_ai.output.messages`

Önerilen üretim deseni: içeriği dışta sakla (S3, log store'un), span'lerde referansları (pointer ID'ler, düz yazı değil) kaydet. Bu Ders 27 content-poisoning savunmasının observability'e kablolanmış hali.

### Stabilite

Çoğu konvansiyon Mart 2026 itibariyle deneysel. Stable preview'e opt-in yap:

```
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
```

Datadog v1.37+ GenAI attribute'larını kendi LLM Observability şemasına native eşliyor. Diğer backend'ler (Grafana, Honeycomb, Jaeger) ham attribute'ları destekler.

### Bu desen nerede ters gider

- **Tam prompt'ları span'lerde yakalamak.** Ops'un okuyabileceği trace'lerde PII, secret, müşteri verisi. Dışta sakla.
- **`gen_ai.provider.name` yok.** Attribution eksik olunca multi-provider dashboard'lar bozulur.
- **Parent link'siz span'ler.** Yetim tool span'leri. Her zaman context'i propagate et.
- **Stability opt-in'i belirlememek.** Backend yükseltmesinde attribute'ların yeniden adlandırılabilir.

## İnşa Et

`code/main.py` GenAI konvansiyonlarına eşleşen bir stdlib span emitter uyguluyor:

- GenAI attribute şemasıyla `Span`.
- `start_span`, nested context'lerle `Tracer`.
- Şunları yayan scripted bir agent koşusu: `create_agent`, `invoke_agent` (INTERNAL), tool-başına span'ler, LLM çağrıları için `chat` span'leri.
- Prompt'ları dışta saklayan ve span'lerde ID'leri kaydeden bir content-capture modu.

Çalıştır:

```
python3 code/main.py
```

Çıktı: tüm gerekli GenAI attribute'larıyla bir span tree ve opt-in content referanslarını gösteren bir "dış store."

## Kullan

- **Datadog LLM Observability** (v1.37+) attribute'ları native eşliyor.
- **Langfuse / Phoenix / Opik** (Ders 24) — ekosistemi auto-instrument et.
- **Jaeger / Honeycomb / Grafana Tempo** — ham OTel trace'leri; GenAI attribute'larından dashboard kur.
- **Self-hosted** — GenAI processor'lı OTel Collector çalıştır.

## Yayınla

`outputs/skill-otel-genai.md` content-capture varsayılanları ve dış-referans storage ile mevcut bir agent'a OTel GenAI span'leri kablolar.

## Alıştırmalar

1. Ders 01 ReAct döngünü `invoke_agent` (INTERNAL) + tool-başına span'lerle instrumente et. Bir Jaeger instance'a gönder.
2. "References only" modunda content capture ekle: prompt'lar SQLite'a, span attribute'ları yalnızca row ID'leri taşır.
3. `gen_ai.data_source.id` spec'ini oku. Ders 09 Mem0 search'üne kablola.
4. `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` ayarla ve attribute'larının collector tarafından yeniden adlandırılmadığını doğrula.
5. Bir dashboard kur: yalnızca GenAI attribute'larından "hangi tool hataları hangi modellerle korele ediyor."

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| GenAI SIG | "OpenTelemetry GenAI grubu" | Şemayı tanımlayan OTel working group |
| invoke_agent | "Agent span'i" | Bir agent koşusunu temsil eden span adı |
| CLIENT span | "Remote call" | Remote bir agent service'ine çağrı için span |
| INTERNAL span | "In-process" | In-process bir agent koşusu için span |
| gen_ai.provider.name | "Provider" | anthropic / openai / aws.bedrock / google.vertex |
| gen_ai.data_source.id | "RAG kaynağı" | Bir retrieval'ın hangi corpus/store'a vurduğu |
| Content capture | "Prompt logging" | Mesajların opt-in yakalanması; üretimde dışta sakla |
| Stability opt-in | "Preview mode" | Deneysel konvansiyonları sabitlemek için env var |

## İleri Okuma

- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — spec
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — varsayılan GenAI span'leri
- [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — built-in OTel span'leri
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) — W3C trace context propagation
