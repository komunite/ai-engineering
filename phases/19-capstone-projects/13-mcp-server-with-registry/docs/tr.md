# Capstone 13 — Registry ve Governance ile MCP Server

> Model Context Protocol 2026'da gelecek olmaktan çıkıp default tool-use spec'i oldu. Anthropic, OpenAI, Google ve her major IDE MCP client'ları yayınlıyor. Pinterest dahili MCP sunucu ekosistemini yayınladı. AAIF Registry capability metadata'sını `.well-known`'da formalize etti. AWS ECS referans stateless deployment'ı yayınladı. Block'un goose-agent'ı aynı protokolü hosted bir asistanın içine koydu. 2026 üretim şekli: StreamableHTTP transport, OAuth 2.1 scope'ları, OPA policy gating ve platform ekiplerinin sunucuları discover, validate ve enable etmesine izin veren bir registry. Bunu uçtan uca inşa et.

**Tür:** Bitirme
**Diller:** Python (sunucu, FastMCP üzerinden) veya TypeScript (@modelcontextprotocol/sdk), Go (registry service)
**Ön koşullar:** Faz 11 (LLM engineering), Faz 13 (tools ve MCP), Faz 14 (agent'lar), Faz 17 (infrastructure), Faz 18 (safety)
**Egzersize edilen fazlar:** P11 · P13 · P14 · P17 · P18
**Süre:** 25 saat

## Sorun

MCP tool-use lingua franca'sı oldu. Claude Code, Cursor 3, Amp, OpenCode, Gemini CLI ve her managed agent şimdi MCP sunucularını consume ediyor. Üretim zorlukları sunucu yazmak değil (FastMCP onu kolaylaştırıyor) ama enterprise gereksinimleriyle ölçekte deploy etmek: per-tenant OAuth scope'ları, yıkıcı tool'larda OPA policy'si, StreamableHTTP stateless scaling, discovery için bir registry, tool call başına audit log'lar. Pinterest'in dahili MCP ekosistemi ve AAIF Registry spec'i 2026 çıtasını koydu.

10 dahili tool expose eden bir MCP sunucusu (Postgres read-only, S3 listing, Jira, Linear, Datadog, vs.), platform discovery için bir registry UI'si ve yıkıcı tool'lar için bir insan-onay gate'i inşa edeceksin. Yük testi StreamableHTTP horizontal scaling'i gösterir. Audit trail bir enterprise security review'unu tatmin eder.

## Kavram

MCP 2026 revizyonu StreamableHTTP'yi default transport olarak zorunlu kılar. Daha önceki stdio-and-SSE şeklinin aksine, StreamableHTTP default'ta stateless: tek bir HTTP endpoint JSON-RPC istekleri kabul eder, response'ları stream eder ve notification'lar için uzun-ömürlü bağlantıları destekler. Stateless, load balancer arkasında horizontal scalable demek.

Authorization, per-tool scope'lu OAuth 2.1. Bir token `jira:read`, `s3:list`, `postgres:query:readonly` gibi scope'ları taşır. MCP sunucusu scope'ları sadece oturum başlangıcında değil, tool-call zamanında kontrol eder. Yüksek-riskli tool'lar için sunucu, scope'u son N dakika içinde `approved:by:human`'a yükseltilmemiş herhangi bir çağrıyı reddeder — o yükselme bir Slack inceleme kartından gelir.

Registry ayrı bir servis. Her MCP sunucusu tool manifest'i, transport URL'i, auth gereksinimleriyle bir `.well-known/mcp-capabilities` dokümanı expose eder. Registry poll'lar, validate eder ve index'ler. Platform ekipleri hangi tool'ların erişilebilir olduğunu, hangi scope'lara ihtiyaç duyduklarını ve hangi ekiplerin sahip olduğunu görmek için registry UI'sini kullanır.

## Mimari

```
MCP client (Claude Code, Cursor 3, ...)
          |
          v
HTTPS üzerinden StreamableHTTP (JSON-RPC + streaming)
          |
          v
Load balancer arkasında MCP sunucusu (FastMCP)
          |
   +------+------+---------+----------+------------+
   v             v         v          v            v
Postgres    S3 listing  Jira       Linear     Datadog
(read-only) (paged)     (read)     (read)     (query)
          |
   +------+-------------+
   v                    v
 OPA policy gate   yıkıcı tool MCP (ayrı sunucu)
                        |
                        v
                   Slack üzerinden insan onayı
                        |
                        v
                   audit log (append-only, per-tenant)

  registry service
     |
     v  Her sunucudan GET /.well-known/mcp-capabilities
     v
     UI: arama / validate / enable-disable / ownership
```

## Stack

- Sunucu framework'ü: FastMCP (Python) veya `@modelcontextprotocol/sdk` (TypeScript)
- Transport: HTTPS üzerinden StreamableHTTP (stateless)
- Auth: SPIFFE / SPIRE üzerinden workload identity'li OAuth 2.1
- Policy: tool başına OPA / Rego kuralları; istek başına policy decision service
- Registry: self-hosted, `.well-known/mcp-capabilities` manifest'lerini consume eder
- İnsan onayı: yıkıcı tool'lar için Slack interactive message
- Deployment: AWS ECS Fargate veya Fly.io, tenant başına bir sunucu veya tenant scoping ile paylaşılan
- Audit: per-call lineage'li per-tenant bucket'ta yapılı JSONL

## İnşa Et

1. **Tool yüzeyi.** 10 dahili tool expose et: Postgres read-only query, S3 list objects, Jira search/fetch, Linear search/fetch, Datadog metric query, PagerDuty on-call lookup, GitHub read-only, Notion search, Slack search, Salesforce read. Her tool tipli bir şemaya ve scope label'ına sahip.

2. **FastMCP sunucusu.** Tool'ları mount et. StreamableHTTP transport'unu configure et. OAuth token introspection ve scope enforcement için bir middleware ekle.

3. **OPA policy.** Tool başına Rego policy: hangi scope'lar invocation'a izin veriyor, hangi PII redaction uygulanıyor, hangi payload-size cap'leri uygulanıyor. Her tool call'da çağrılan decision service.

4. **Registry service.** Kayıtlı sunuculardan `.well-known/mcp-capabilities`'i poll'layan, JSON Schema ile validate eden ve bir list / search / validate / enable-disable UI'si expose eden ayrı Go veya TS servisi.

5. **Capability manifest'i.** Her sunucu şunlarla `.well-known/mcp-capabilities` expose eder: tool listesi, auth gereksinimleri, transport URL'i, sahip ekip, SLO.

6. **Yıkıcı tool ayrımı.** State'i mutate eden tool'lar (Jira create, Linear create, Postgres write) daha sıkı bir auth akışıyla ikinci bir MCP sunucusunda yaşar: token'lar 15 dakika içinde Slack kart üzerinden yükseltilmiş bir `approved:by:human` scope'una sahip olmalı.

7. **Audit log.** Tenant başına append-only JSONL: `{timestamp, user, tool, args_redacted, response_redacted, outcome}`. Yazmadan önce Presidio üzerinden PII redaction.

8. **Yük testi.** StreamableHTTP'de 100 eşzamanlı client. İkinci bir replica ekleyerek horizontal scaling'i göster; load balancer'ın session stickiness olmadan yeniden dağıttığını göster.

9. **Conformance test'leri.** Her iki sunucuya karşı resmi MCP conformance suite'i çalıştır. Tüm zorunlu bölümleri geç.

## Kullan

```
$ curl -H "Authorization: Bearer eyJhbGc..." \
       -X POST https://mcp.internal.example.com/ \
       -d '{"jsonrpc":"2.0","method":"tools/call",
            "params":{"name":"postgres.readonly","arguments":{"sql":"SELECT 1"}}}'
[registry]   capability validate edildi: postgres.readonly v1.2
[policy]    scope postgres:query:readonly mevcut; izin verildi
[audit]     loglandı: user=u42 tool=postgres.readonly outcome=ok
response:    { "result": { "rows": [[1]] } }
```

## Yayınla

`outputs/skill-mcp-server.md` teslimat'ı açıklar. OAuth 2.1 scope'ları ve OPA gating ile dahili tool'lar için üretim-grade bir MCP sunucusu + registry + audit katmanı.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Spec uyumluluğu | StreamableHTTP + capability manifest'i MCP conformance test'lerini geçer |
| 20 | Güvenlik | Scope enforcement, her tool'da OPA kapsamı, secret hijyeni |
| 20 | Observability | PII redaction'lı per-tool-call audit log |
| 20 | Ölçek | 100-client yük testi horizontal scale göstergesi |
| 15 | Registry UX'i | Discover / validate / enable-disable workflow'u |
| **100** | | |

## Alıştırmalar

1. Yeni bir tool (Confluence search) ekle. Core sunucuya dokunmadan registry validation akışı boyunca gönder.

2. `email`, `ssn` veya `phone` adlı kolonlar içeren Postgres sorgu sonuçlarını redact eden bir OPA policy yaz. Bir probe sorgusuyla egzersize et.

3. Local gecikmede StreamableHTTP vs stdio benchmark'la. Çağrı başına p50/p95 raporla.

4. Per-tenant quota implement et: tenant başına tool başına dakikada maksimum N çağrı. İkinci bir OPA kuralıyla zorla.

5. [mcp-conformance-tests](https://github.com/modelcontextprotocol/conformance)'tan MCP conformance suite'i çalıştır ve her başarısızlığı düzelt.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| StreamableHTTP | "2026 MCP transport'u" | Stateless HTTP + streaming; networked sunucular için SSE + stdio'yu değiştirir |
| Capability manifest | "Well-known doc" | Tool listesi, auth, transport URL'i ile `.well-known/mcp-capabilities` |
| OPA / Rego | "Policy engine" | Tool çağrılarını harici kurallara karşı yetkilendirmek için Open Policy Agent |
| Scope elevation | "Approved-by-human" | Slack onayı üzerinden verilen kısa-ömürlü scope, yıkıcı tool'lar için gerekli |
| Registry | "Tool discovery" | MCP sunucularını capability manifest'lerinden index'leyen servis |
| Workload identity | "SPIFFE / SPIRE" | OAuth token issuance için cryptographic service identity |
| Conformance suite | "Spec test'leri" | StreamableHTTP + tool manifest doğruluğu için resmi MCP test battery'si |

## İleri Okuma

- [Model Context Protocol 2026 Roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — StreamableHTTP, capability metadata, registry
- [AAIF MCP Registry spec'i](https://github.com/modelcontextprotocol/registry) — 2026 registry spec'i
- [AWS ECS referans deployment'ı](https://aws.amazon.com/blogs/containers/deploying-model-context-protocol-mcp-servers-on-amazon-ecs/) — referans üretim deployment'ı
- [Pinterest dahili MCP ekosistemi](https://www.infoq.com/news/2026/04/pinterest-mcp-ecosystem/) — referans dahili deployment
- [Block `goose` MCP kullanımı](https://block.github.io/goose/) — referans agent consumption pattern'i
- [FastMCP](https://github.com/jlowin/fastmcp) — Python sunucu framework'ü
- [Open Policy Agent](https://www.openpolicyagent.org/) — policy engine referansı
- [SPIFFE / SPIRE](https://spiffe.io) — workload identity referansı
