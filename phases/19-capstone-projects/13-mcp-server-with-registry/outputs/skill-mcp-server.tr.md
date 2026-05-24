---
name: mcp-server-platform
description: StreamableHTTP, OAuth 2.1 scope'ları, OPA policy, destructive tool'lar için insan-onay gate'i ve keşif için registry ile production MCP server deploy et.
version: 1.0.0
phase: 19
lesson: 13
tags: [capstone, mcp, fastmcp, streamablehttp, oauth, opa, registry, governance]
---

Bir enterprise ortam verildiğinde, 10 dahili tool'lu bir MCP server, keşif için bir registry servisi ve destructive tool'ları Slack onayıyla gate'leyen bir governance katmanı gönder.

Build planı:

1. 10 read-only tool'u (Postgres, S3, Jira, Linear, Datadog, PagerDuty, GitHub, Notion, Slack, Salesforce) tipli şema ve gerekli scope ile yayan FastMCP server.
2. StreamableHTTP transport, load balancer arkasında stateless.
3. OAuth 2.1 token introspection middleware; SPIFFE / SPIRE üzerinden workload identity.
4. Her tool çağrısında OPA / Rego policy kararları: scope zorlanması, PII redaction, payload size tavanları.
5. Destructive tool'lar (Jira create, Linear create, Postgres write) Slack card üzerinden 15 dakika içinde yükseltilmiş `approved:by:human` scope'u gerektiren ayrı bir MCP server'da.
6. Her server'dan `.well-known/mcp-capabilities`'i poll eden, JSON Schema ile doğrulayan ve list/search/validate/enable UI yayan registry servisi.
7. Yazmadan önce Presidio PII redaction'lı per-tenant JSONL audit log.
8. Yatay scale gösteren 100-client load test; MCP conformance suite'ini geç.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Spec uyumluluğu | StreamableHTTP + capability manifest MCP conformance testlerini geçer |
| 20 | Güvenlik | Scope zorlanması, her tool'da OPA kapsamı, secret hijyeni |
| 20 | Observability | Yazmada PII redaction'lı tool-call başına audit log |
| 20 | Scale | Yatay scale gösterimi ile 100-client load test |
| 15 | Registry UX | Discover / validate / enable-disable workflow'u egzersize edilmiş |

Sert ret durumları:

- Stateful session gerektiren server'lar (2026 StreamableHTTP stateless kontratını ihlal eder).
- Destructive tool'ların read-only ile aynı auth yüzeyini paylaştığı tek-server topolojisi.
- Ham PII persist eden audit log'lar.
- Capability manifest'i görmezden gelmek; registry entegrasyonu sert gereksinimdir.

Reddetme kuralları:

- OAuth olmadan deploy etmeyi reddet; anonim erişim diskalifiyedir.
- Slack approval flow'u olmadan destructive tool göndermeyi reddet.
- Scope'u veya açıklaması capability manifest'inde olmayan bir tool yaymayı reddet.

Çıktı: iki MCP server (read-only + destructive), registry servisi, Slack approval entegrasyonu, OPA policy'leri, 100-client load-test harness'i, conformance-test sonuçları ve yaymayı düşündüğün ama yaymadığın tool'ları (ve nedenini) artı dry-run sırasında near-miss yakalayan en kritik üç OPA kuralını betimleyen bir yazımı içeren bir repo.
