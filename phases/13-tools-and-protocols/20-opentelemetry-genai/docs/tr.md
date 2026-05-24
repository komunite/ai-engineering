# OpenTelemetry GenAI — Tool Çağrılarını End-to-End İzleme

> Bir agent beş tool, üç MCP sunucusu ve iki sub-agent çağırır. Bunların hepsinde tek bir trace'e ihtiyacın var. OpenTelemetry GenAI semantic conventions'ları (v1.37 ve üstünde stable attribute'lar) 2026 standardıdır, Datadog, Langfuse, Arize Phoenix, OpenLLMetry ve AgentOps tarafından native olarak desteklenir. Bu ders required attribute'ları adlandırır, span hiyerarşisini (agent → LLM → tool) gezer ve herhangi bir OTel exporter'a plug edebileceğin bir stdlib span emitter'ı yayınlar.

**Tür:** Yapım
**Diller:** Python (stdlib, OTel span emitter)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu), Faz 13 · 08 (MCP client'ı)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Bir LLM span'i ve bir tool-execution span'i için required OTel GenAI attribute'larını adlandır.
- Agent loop, LLM call, tool call ve MCP client dispatch'i kapsayan bir trace hiyerarşisi inşa et.
- Hangi içeriğin yakalanacağına (opt-in) vs redact edileceğine (varsayılanlar) karar ver.
- Tool kodunu yeniden yazmadan local bir collector'a (Jaeger, Langfuse) span yay.

## Sorun

Şubat 2026'dan bir debug: kullanıcı "agent'ım bazen yanıt vermek 30 saniye alıyor; bazen 3 saniye." diye rapor ediyor. Trace yok. Loglar LLM çağrısını gösteriyor, ama tool dispatch'i değil, MCP sunucu round-trip'i değil, sub-agent değil. Tahmin ediyorsun. Sonunda buluyorsun: bir MCP sunucusu zaman zaman cold-start'ta hang oluyor.

End-to-end tracing olmadan bunu bulamazsın. OTel GenAI bunu düzeltir.

Conventions'lar 2025-2026'da OpenTelemetry semantic-conventions grubu altında oturdu. Datadog, Langfuse, Phoenix, OpenLLMetry ve AgentOps'un hepsi aynı span'leri parse etsin diye stabil attribute isimleri tanımlarlar. Bir kere instrument et; herhangi bir backend'e yayınla.

## Kavram

### Span hiyerarşisi

```
agent.invoke_agent  (top, INTERNAL span)
 ├── llm.chat       (CLIENT span)
 ├── tool.execute   (INTERNAL)
 │    └── mcp.call  (CLIENT span)
 ├── llm.chat       (CLIENT span)
 └── subagent.invoke (INTERNAL)
```

Hepsi tek bir trace id altında nest olur. Span id'leri parent-child ilişkilerini link'ler.

### Required attribute'lar

2025-2026 semconv başına:

- `gen_ai.operation.name` — `"chat"`, `"text_completion"`, `"embeddings"`, `"execute_tool"`, `"invoke_agent"`.
- `gen_ai.provider.name` — `"openai"`, `"anthropic"`, `"google"`, `"azure_openai"`.
- `gen_ai.request.model` — talep edilen model string'i (örn. `"gpt-4o-2024-08-06"`).
- `gen_ai.response.model` — gerçekten servis edilen model.
- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`.
- `gen_ai.response.id` — korelasyon için sağlayıcı response id'si.

Tool span'leri için:

- `gen_ai.tool.name` — tool tanımlayıcısı.
- `gen_ai.tool.call.id` — belirli call id.
- `gen_ai.tool.description` — tool açıklaması (opsiyonel).

Agent span'leri için:

- `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.agent.description`.

### Span kind'lar

- Process sınırını aşan çağrılar için `SpanKind.CLIENT` (LLM sağlayıcı, MCP sunucusu).
- Agent'ın kendi loop adımları ve tool yürütme için `SpanKind.INTERNAL`.

### Opt-in content yakalama

Varsayılan olarak, span'ler metric'ler ve timing taşır — prompt'ları ya da completion'ları değil. Büyük payload'lar ve PII varsayılan olarak kapalı. İçeriği dahil etmek için `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` ve belirli content-capture env var'ları ayarla. Üretimde etkinleştirmeden önce dikkatli incele.

### Span'lerde event'ler

Token-seviyesi event'ler span event'leri olarak eklenebilir:

- `gen_ai.content.prompt` — input mesajları.
- `gen_ai.content.completion` — output mesajları.
- `gen_ai.content.tool_call` — kaydedilmiş tool call.

Event'ler ayrıntılı replay için bir span içinde zaman-sıralanır.

### Exporter'lar

OTel span'leri şunlara export eder:

- **Jaeger / Tempo.** OSS, on-prem.
- **Langfuse.** LLM-observability-spesifik; token kullanımını görselleştirir.
- **Arize Phoenix.** Eval'lar + tracing birleştirilmiş.
- **Datadog.** Commercial; `gen_ai.*` attribute'larını native parse eder.
- **Honeycomb.** Column-oriented; query-friendly.

Hepsi wire formatı OTLP konuşur. Kodun umursamaz.

### MCP boyunca propagation

Bir MCP client bir sunucuyu çağırdığında, W3C traceparent header'ını request'e enjekte et. Streamable HTTP standart header'ları destekler. Stdio HTTP header'larını native taşımaz; spec'in 2026 roadmap'i JSON-RPC çağrılarında bir `_meta.traceparent` alanı eklemeyi tartışıyor.

O yayınlanana kadar: her request'in `_meta`'sında traceparent'i elle dahil et. Sunucu trace id'yi log'lar.

### Metric'ler

Span'lerin yanında, GenAI semconv metric'ler tanımlar:

- `gen_ai.client.token.usage` — histogram.
- `gen_ai.client.operation.duration` — histogram.
- `gen_ai.tool.execution.duration` — histogram.

Çağrı başına ayrıntıya ihtiyaç duymayan dashboard'lar için bunları kullan.

### AgentOps katmanı

AgentOps (2024'te kuruldu) GenAI observability'sinde uzmanlaşıyor. Popüler framework'leri (LangGraph, Pydantic AI, CrewAI) otomatik olarak OTel span'leri yayacak şekilde sarar. Yığının desteklenen bir framework kullanıyorsa yararlı; aksi halde manuel instrumentation kullan.

## Kullan

`code/main.py` bir LLM çağıran, iki tool dispatch eden ve bir MCP round-trip yapan bir agent için stdout'a OTel-şekilli span'ler (OTLP-JSON-benzeri formatta) yayar. Gerçek exporter yok — ders span şekline ve attribute kümesine odaklanır. Çıktıyı bir OTLP-uyumlu viewer'a yapıştır ya da sadece oku.

Bakılacak şeyler:

- Trace id tüm span'ler boyunca paylaşılır.
- Parent-child link'leri `parentSpanId` üzerinden kodlanır.
- Required `gen_ai.*` attribute'ları doldurulur.
- Content capture varsayılan olarak kapalı; bir senaryo env var üzerinden açar.

## Yayınla

Bu ders `outputs/skill-otel-genai-instrumentation.md` üretir. Bir agent codebase verildiğinde, skill bir instrumentation planı üretir: span'leri nereye eklemek, hangi attribute'ları doldurmak ve hangi exporter'ları hedeflemek.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Span'leri say ve hangisinin CLIENT vs INTERNAL olduğunu tanımla.

2. Content capture'ı aç (env var) ve `gen_ai.content.prompt` ve `gen_ai.content.completion` event'lerinin göründüğünü doğrula. PII için implikasyonları not et.

3. Tool-execution metric'i `gen_ai.tool.execution.duration` ekle ve çağrı başına bir histogram örneği olarak yay.

4. Bir parent agent span'inden bir traceparent'i bir MCP request'inin `_meta.traceparent` alanına propagate et. MCP sunucusunun aynı trace id'yi göreceğini doğrula.

5. OTel GenAI semconv spec'ini oku. Semconv'da listelenen ama bu dersin kodunun YAYMADIĞI bir attribute'u tanımla. Onu ekle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| OTel | "OpenTelemetry" | Trace'ler, metric'ler, log'lar için açık standart |
| GenAI semconv | "GenAI semantic conventions" | LLM / tool / agent span'leri için stabil attribute isimleri |
| `gen_ai.*` | "Attribute namespace'i" | Tüm GenAI attribute'ları bu prefix'i paylaşır |
| Span | "Zamanlı operasyon" | Başlangıç, bitiş ve attribute'lı bir iş birimi |
| Trace | "Cross-span ancestry" | Trace id paylaşan span ağacı |
| SpanKind | "CLIENT / SERVER / INTERNAL" | Span yönü hakkında ipuçları |
| OTLP | "OpenTelemetry Line Protocol" | Exporter'lar için wire formatı |
| Opt-in content | "Prompt / completion yakalama" | Varsayılan kapalı; etkinleştirmek için env var |
| traceparent | "W3C header'ı" | Trace context'i servisler arasında propagate eder |
| Exporter | "Backend-spesifik shipper" | Span'leri Jaeger / Datadog / vb.'ye gönderen bileşen |

## İleri Okuma

- [OpenTelemetry — GenAI semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — GenAI span'leri, metric'ler ve event'ler için kanonik conventions
- [OpenTelemetry — GenAI spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) — LLM ve tool-execution span attribute listesi
- [OpenTelemetry — GenAI agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/) — agent-seviyesi `invoke_agent` span'i
- [open-telemetry/semantic-conventions — GenAI spans](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-spans.md) — GitHub-hostlu source of truth
- [Datadog — LLM OTel semantic convention](https://www.datadoghq.com/blog/llm-otel-semantic-convention/) — production entegrasyon gezintisi
