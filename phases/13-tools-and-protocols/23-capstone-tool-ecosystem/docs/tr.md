# Capstone — Tam Bir Tool Ekosistemi İnşa Et

> Faz 13 her parçayı öğretti. Bu capstone onları tek bir üretim-şekilli sisteme bağlar: tools + resources + prompts + tasks + UI olan bir MCP sunucusu, kenarda OAuth 2.1, bir RBAC gateway, bir multi-server client, bir A2A sub-agent çağrısı, bir collector'a OTel tracing, CI'da tool-poisoning algılama ve bir AGENTS.md + SKILL.md bundle. Sonunda her mimari seçimi savunabileceksin.

**Tür:** Bitirme
**Diller:** Python (stdlib, end-to-end ekosistem harness)
**Ön koşullar:** Faz 13 · 01 ile 21 arası
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Bir `ui://` app ile tools, resources, prompts ve bir task açan bir MCP sunucusu compose et.
- Sunucunun önünde RBAC ve pinlenmiş hash'leri zorlayan bir OAuth 2.1 gateway koy.
- End-to-end OTel GenAI attribute'larıyla trace eden bir multi-server client yaz.
- Workload'un bir bölümünü bir A2A sub-agent'a delege et; opaklığın korunduğunu doğrula.
- Tüm yığını AGENTS.md + SKILL.md ile paketle, böylece diğer agent'lar onu sürebilsin.

## Sorun

"Araştır ve raporla" sistemini yayınla:

- Kullanıcı sorar: "agent protokolleri üzerine en çok atıf alan üç 2026 arXiv makalesini özetle."
- Sistem: MCP üzerinden arXiv'i ara; makale özetlemeyi A2A üzerinden uzmanlaşmış bir writer agent'ına delege et; sonuçları agregat et; interaktif bir raporu MCP Apps `ui://` resource'u olarak render et; her adımı OTel'e log'la.

Faz 13'ten tüm primitive'ler görünür. Bu bir toy değil — 2026'da Anthropic (Claude Research ürünü), OpenAI (Apps SDK ile GPT'ler) ve üçüncü partiler tarafından yayınlanan üretim research-assistant sistemlerinin tam olarak bu şekli var.

## Kavram

### Mimari

```
[user] -> [client] -> [gateway (OAuth 2.1 + RBAC)] -> [research MCP server]
                                                      |
                                                      +- MCP tool: arxiv_search (pure)
                                                      +- MCP resource: notes://recent
                                                      +- MCP prompt: /research_topic
                                                      +- MCP task: generate_report (long)
                                                      +- MCP Apps UI: ui://report/current
                                                      +- A2A call: writer-agent (tasks/send)
                                                      |
                                                      +- OTel GenAI spans
```

### Trace hiyerarşisi

```
agent.invoke_agent
 ├── llm.chat (kick off)
 ├── mcp.call -> tools/call arxiv_search
 ├── mcp.call -> resources/read notes://recent
 ├── mcp.call -> prompts/get research_topic
 ├── a2a.tasks/send -> writer-agent
 │    └── task transitions (opaque internals)
 ├── mcp.call -> tools/call generate_report (task-augmented)
 │    └── tasks/status polling
 │    └── tasks/result (completed, returns ui:// resource)
 └── llm.chat (final synthesis)
```

Bir trace id. Her span'ın doğru `gen_ai.*` attribute'ları var.

### Güvenlik duruşu

- Audience'ı gateway'e pinleyen resource indicator'lı OAuth 2.1 + PKCE.
- Gateway upstream credential'ları tutar; kullanıcı asla görmez.
- RBAC: `alice` `research:read`, `research:write` sahip, tüm tool'ları çağırabilir. `bob` `research:read` sahip, `generate_report`'u çağıramaz.
- Pinned description manifest: tool hash'leri değişen herhangi bir sunucuyu düşürdü.
- Rule of Two audit: hiçbir tool untrusted input, sensitive data ve consequential action'ı birleştirmez.

### Render

Nihai `generate_report` task'ı content blokları artı bir `ui://report/current` resource döndürür. Client'ın host'u (Claude Desktop, vb.) interaktif dashboard'u sandbox iframe'de render eder. Dashboard sıralanmış bir makale listesi, citation sayıları ve kullanıcının tıkladığı herhangi bir makale için `host.callTool('summarize_paper', {arxiv_id})`'i çağıran bir buton içerir.

### Paketleme

Her şey şu şekilde yayınlanır:

```
research-system/
  AGENTS.md                     # proje konvansiyonları
  skills/
    run-research/
      SKILL.md                  # top-level workflow
  servers/
    research-mcp/               # MCP sunucusu
      pyproject.toml
      src/
  agents/
    writer/                     # A2A agent'ı
  gateway/
    config.yaml                 # RBAC + pinlenmiş manifest
```

Kullanıcılar `docker compose up` ile deploy eder. Claude Code, Cursor, Codex ve opencode kullanıcıları `run-research` skill'ini çağırarak sistemi sürebilir.

### Her Faz 13 dersinin katkısı

| Ders | Capstone'un kullandığı |
|--------|------------------------|
| 01-05 | Tool interface, sağlayıcı-portability, paralel çağrılar, şemalar, linting |
| 06-10 | MCP primitive'leri, sunucu, client, transport'lar, resource'lar + prompt'lar |
| 11-14 | Sampling, root'lar + elicitation, async task'lar, `ui://` app'leri |
| 15-17 | Tool poisoning, OAuth 2.1, gateway + registry |
| 18 | A2A sub-agent delegasyonu |
| 19 | OTel GenAI tracing |
| 20 | LLM katmanı için routing gateway |
| 21 | SKILL.md + AGENTS.md paketleme |

## Kullan

`code/main.py` önceki derslerin desenlerini tek bir çalıştırılabilir demoya birleştirir. Tüm stdlib, hepsi in-process, böylece baştan sona okuyabilirsin. Research-and-report senaryosu için tam akışı çalıştırır: gateway ile handshake, OAuth 2.1 simüle edildi, tools/list merge edildi, task olarak generate_report, writer'a A2A çağrısı, ui:// resource'u döndürüldü, OTel span'leri yayındı.

Bakılacak şeyler:

- Her hop'ta tek trace id.
- Gateway policy ikinci bir kullanıcının yazmasını blokluyor.
- Task lifecycle'ı working → completed gidiyor ve hem text hem ui:// content döndürüyor.
- A2A çağrısının iç state'i orchestrator'a opak.
- AGENTS.md ve SKILL.md başka bir agent'ın workflow'u yeniden üretmek için ihtiyaç duyduğu tek dosyalar.

## Yayınla

Bu ders `outputs/skill-ecosystem-blueprint.md` üretir. Bir ürün ihtiyacı verildiğinde (araştırma, özetleme, otomasyon), skill tam mimariyi üretir: hangi MCP primitive'leri, hangi gateway kontrolleri, hangi A2A çağrıları, hangi telemetri, hangi paketleme.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Tek trace id'yi ve span'lerin nasıl nest olduğunu not et. Demonun Faz 13'ten kaç primitive'e dokunduğunu say.

2. Demoyu genişlet: ikinci bir backend MCP sunucusu ekle (örn. `bibliography`) ve gateway'in tool'larını aynı namespace'e merge ettiğini doğrula.

3. Sahte A2A writer agent'ını bir subprocess'te çalışan gerçek biri ile değiştir. Ders 19 harness'ını kullan.

4. Orchestrator ve LLM arasında routing gateway'inde bir PII redaction adımı ekle. Kullanıcı sorgusundaki e-postaların temizlendiğini doğrula.

5. Bu sistemi sürdürecek bir takım arkadaşı için bir AGENTS.md yaz. Okuması beş dakikadan kısa olmalı ve onlara capstone'u Cursor ya da Codex'te sürmek için ihtiyaç duydukları her şeyi vermeli.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Capstone | "Faz-13 entegrasyon demosu" | Her primitive'i kullanan end-to-end sistem |
| Research and report | "Senaryo" | Search, summarize, render pattern'i |
| Ekosistem | "Tüm parçalar birlikte" | Server + client + gateway + sub-agent + telemetri + paket |
| Trace hiyerarşisi | "Tek trace id" | Her hop'un span'i trace'i paylaşır; span id'leri üzerinden parent-child |
| Gateway-verilmiş token | "Transitive auth" | Client yalnızca gateway'in token'ını görür; gateway upstream credential'ları tutar |
| Merged namespace | "Tek düz listede tüm tool'lar" | Gateway'de multi-server merge, collision'da prefix |
| Opacity boundary | "A2A çağrısı iç bileşenleri gizler" | Sub-agent'ın muhakemesi orchestrator'a görünmez |
| Üç katmanlı yığın | "AGENTS.md + SKILL.md + MCP" | Proje bağlamı + workflow + tool'lar |
| Defense-in-depth | "Birden fazla güvenlik katmanı" | Pinlenmiş hash'ler, OAuth, RBAC, Rule of Two, audit log |
| Spec compliance matrisi | "Spec'in gerektirdiğinden yayınladığımız" | 2025-11-25 gereksinimlerine deliverable'ları haritalayan checklist |

## İleri Okuma

- [MCP — Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — konsolide referans
- [MCP blog — 2026 roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — protokolün gittiği yer
- [a2a-protocol.org](https://a2a-protocol.org/latest/) — A2A v1.0 referansı
- [OpenTelemetry — GenAI semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — kanonik tracing conventions
- [Anthropic — Claude Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) — production agent runtime desenleri
