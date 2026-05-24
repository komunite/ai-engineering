# OpenAI Agents SDK: Handoff'lar, Guardrails, Tracing

> OpenAI Agents SDK Responses API üzerine kurulu hafif çoklu-agent framework'ü. Beş primitif: Agent, Handoff, Guardrail, Session, Tracing. Handoff'lar `transfer_to_<agent>` adlı tool'lar. Guardrail'ler input ya da output'ta tetiklenir. Tracing varsayılan açık.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 06 (Tool Use)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- OpenAI Agents SDK'nın beş primitifini adlandır.
- Handoff'ları açıkla: neden tool olarak modellendiler, modelin gördüğü ad şekli ve context'in nasıl transfer olduğu.
- Input guardrails, output guardrails ve tool guardrails'i ayır; `run_in_parallel` vs blocking mode'u açıkla.
- Handoff'lar + guardrails + span-tarzı tracing'li bir stdlib runtime uygula.

## Sorun

Temiz delege edemeyen agent'lar her şeyi tek prompt'a tıkıştırmakla sonlanır. Guardrail'siz agent'lar PII, policy-ihlal eden çıktı yayar ya da sonsuza kadar döngü kurar. OpenAI'ın SDK'sı çoklu-agent işi tractable yapan üç primitifi kodifiye eder.

## Kavram

### Beş primitif

1. **Agent.** LLM + talimatlar + tool'lar + handoff'lar.
2. **Handoff.** Başka bir agent'a delegasyon. Modele `transfer_to_<agent_name>` adlı bir tool olarak temsil edilir.
3. **Guardrail.** Input (yalnızca ilk agent), output (yalnızca son agent) ya da tool invocation (function tool başına) üzerinde doğrulama.
4. **Session.** Turlar arası otomatik konuşma geçmişi.
5. **Tracing.** LLM generation'ları, tool çağrıları, handoff'lar, guardrail'ler için built-in span'ler.

### Tool olarak handoff'lar

Model tool listesinde `transfer_to_billing_agent`'ı görür. Onu çağırmak runtime'a şunu sinyaller:

1. Konuşma context'ini kopyala (ya da `nest_handoff_history` beta ile çök).
2. Hedef agent'ı talimatlarıyla initialize et.
3. Koşuyu hedef agent ile devam ettir.

Bu supervisor pattern (Ders 13 / Ders 28) ürünleştirilmiş.

### Guardrail'ler

Üç çeşit:

- **Input guardrails.** İlk agent'ın input'unda çalışır. Güvensiz ya da scope-dışı istekleri herhangi bir LLM çağrısından önce reddet.
- **Output guardrails.** Son agent'ın output'unda çalışır. PII sızıntıları, policy ihlalleri, bozuk yanıtları yakala.
- **Tool guardrails.** Function-tool başına çalışır. Argümanları doğrula, izinleri kontrol et, yürütmeyi audit et.

Mod:

- **Paralel** (varsayılan). Guardrail LLM ana LLM ile yan yana çalışır. Daha düşük tail latency. Tetiklenirse ana LLM'in işi atılır (token israfı).
- **Blocking** (`run_in_parallel=False`). Guardrail LLM önce çalışır. Tetiklenirse ana çağrıda token israf edilmez.

Tripwire'lar `InputGuardrailTripwireTriggered` / `OutputGuardrailTripwireTriggered` raise eder.

### Tracing

Varsayılan açık. Her LLM generation, tool çağrısı, handoff ve guardrail bir span yayar. `OPENAI_AGENTS_DISABLE_TRACING=1` opt-out eder. `add_trace_processor(processor)` span'leri kendi backend'ine OpenAI'ınkiyle yan yana fan'lar.

### Session'lar

`Session` konuşma geçmişini bir backend'de (SQLite, Redis, custom) saklar. `Runner.run(agent, input, session=session)` otomatik yükler ve append eder.

### Bu desen nerede ters gider

- **Handoff drift'i.** Agent A Agent B'ye handoff yapar, o da Agent A'ya geri verir. Bir hop counter ekle.
- **Guardrail bypass.** Tool guardrail'leri yalnızca function tool'larda tetiklenir; built-in tool'lar (file reader, web fetch) ayrı policy gerektirir.
- **Aşırı-tracing.** Span'lerde hassas içerik. OTel GenAI content-capture kurallarıyla eşleştir (Ders 23) — dışta sakla, ID ile referans ver.

## İnşa Et

`code/main.py` SDK şeklini stdlib'de uyguluyor:

- `Agent`, `FunctionTool`, `Handoff` (transfer semantiği ile function tool olarak).
- Input/output/tool guardrail'li, handoff dispatch'li ve hop counter'lı `Runner`.
- Trace şeklini göstermek için basit bir span emitter.
- Kullanıcının sorgusuna göre billing ya da support'a handoff yapan bir triage agent; bir input'ta guardrail tetiklenir.

Çalıştır:

```
python3 code/main.py
```

Trace iki başarılı handoff, bir input guardrail tetiklenmesi ve gerçek SDK'nın yaydığını yansıtan bir span tree'sini gösterir.

## Kullan

- **OpenAI Agents SDK** OpenAI-first ürünleri için.
- **Claude Agent SDK** (Ders 17) Claude-first ürünleri için.
- **LangGraph** (Ders 13) açık state ve dayanıklı resume istediğinde.
- **Custom** tam kontrole ihtiyacın olduğunda (voice, multi-provider, federe deployment'lar).

## Yayınla

`outputs/skill-agents-sdk-scaffold.md` bir triage agent'ı, handoff'ları, input/output/tool guardrail'leri, session store'u ve trace processor'ı ile bir Agents SDK uygulamasını iskeler.

## Alıştırmalar

1. Bir handoff hop counter ekle: N transfer sonrası reddet. Davranışı trace et.
2. `nest_handoff_history`'yi bir opsiyon olarak uygula — transfer'den önce önceki mesajları tek bir özete çök.
3. Bloklayan bir output guardrail yaz. Onu tetikleyecek prompt'larda vs geçecek olanlarda latency'yi karşılaştır.
4. `add_trace_processor`'ı bir JSON logger'a kablola. Span başına ne şekil yayıyor?
5. SDK dokümanlarını oku. Stdlib oyuncağını `openai-agents-python`'a taşı. Neyi yanlış modelledin?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Agent | "LLM + talimatlar" | SDK'da Agent tipi; tool'ları ve handoff'ları sahiplenir |
| Handoff | "Transfer" | Modelin başka bir agent'a delege etmek için çağırdığı tool |
| Guardrail | "Policy check" | Input / output / tool invocation'da doğrulama |
| Tripwire | "Guardrail tetiklenmesi" | Guardrail reddettiğinde raise edilen exception |
| Session | "Geçmiş store'u" | Koşular arası persist eden konuşma belleği |
| Tracing | "Span'ler" | LLM + tool + handoff + guardrail üzerinde built-in observability |
| Blocking guardrail | "Sıralı check" | Guardrail önce çalışır; tetiklenmede token israfı yok |
| Paralel guardrail | "Eşzamanlı check" | Guardrail yan yana çalışır; daha düşük latency, tetiklenmede token israfı |

## İleri Okuma

- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) — primitifler, handoff'lar, guardrails, tracing
- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — Claude-flavored karşılık
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — handoff'lara ne zaman uzanmalı
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — Agents SDK span'lerinin eşleştiği standart
