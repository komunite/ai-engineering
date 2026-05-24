# MCP Gateway'leri ve Registry'leri — Enterprise Control Plane'leri

> Enterprise'lar her dev'in random MCP sunucuları yüklemesine izin veremez. Bir gateway auth, RBAC, audit, rate limiting, caching ve tool-poisoning algılamayı merkezileştirir, sonra birleştirilmiş tool yüzeyini tek bir MCP endpoint'i olarak açar. Resmi MCP Registry'si (Anthropic + GitHub + PulseMCP + Microsoft, namespace-doğrulanmış) kanonik upstream'dir. Bu ders bir gateway'in nereye uyduğunu adlandırır, minimal bir implementasyonu gezer ve 2026 vendor landscape'ini gözden geçirir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, minimal gateway)
**Ön koşullar:** Faz 13 · 15 (tool poisoning), Faz 13 · 16 (OAuth 2.1)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Bir MCP gateway'in nerede oturduğunu açıkla (MCP client'ları ile birden fazla backend MCP sunucusu arasında).
- Beş gateway sorumluluğunu implemente et: auth, RBAC, audit, rate limit, policy.
- Gateway katmanında pinned-tool-hash manifest'i zorla.
- Resmi MCP Registry'sini metaregistry'lerden (Glama, MCPMarket, MCP.so, Smithery, LobeHub) ayırt et.

## Sorun

Bir Fortune 500'ün 30 onaylanmış MCP sunucusu, 5000 geliştiricisi, compliance ve audit gereksinimleri ve merkezi policy isteyen bir güvenlik takımı var. Her geliştiricinin IDE'lerinde keyfi sunucular yüklemesine izin vermek başlangıçta kaybediliyor.

Gateway deseni:

1. Gateway, geliştiricilerin bağlandığı tek bir Streamable HTTP endpoint olarak çalışır.
2. Gateway her backend MCP sunucusu için credential'lar tutar.
3. Her geliştirici request'i gateway'in kendi OAuth'u üzerinden authenticate ve scope edilir.
4. Gateway çağrıyı backend sunucusuna yönlendirir, policy uygulayarak.
5. Tüm çağrılar audit için loglanır.

Cloudflare MCP Portals, Kong AI Gateway, IBM ContextForge, MintMCP, TrueFoundry, Envoy AI Gateway — hepsi 2025-2026'da gateway'ler ya da gateway feature'ları yayınladı.

Bu sırada, Resmi MCP Registry kanonik upstream olarak launch oldu: gateway'in çekebileceği curated, namespace-doğrulanmış, reverse-DNS-isimli sunucular. Metaregistry'ler (Glama, MCPMarket, MCP.so, Smithery, LobeHub) birden fazla kaynak boyunca sunucuları agregat eder.

## Kavram

### Beş gateway sorumluluğu

1. **Auth.** Geliştiriciyi tanımlamak için OAuth 2.1; kullanıcı rollerine map'ler.
2. **RBAC.** Kullanıcı başına policy: hangi sunucular, hangi tool'lar, hangi scope'lar.
3. **Audit.** Her çağrı kim, ne, ne zaman, sonuç ile loglanır.
4. **Rate limit.** Kötüye kullanımı önlemek için kullanıcı / tool / sunucu başına sınırlar.
5. **Policy.** Zehirlenmiş açıklamaları reddet, Rule of Two zorla, PII redact et.

### Tek endpoint olarak gateway

Geliştiricilere, gateway tek bir MCP sunucusu gibi görünür. Dahili olarak N backend'e yönlendirir. Session id'leri (Faz 13 · 09) sınırda yeniden yazılır.

### Credential vaulting

Geliştiriciler asla backend token'ları görmez. Gateway onları tutar (ya da yapan bir identity provider'a proxy'ler). Gateway'de `notes:read` olan bir geliştirici, gateway'in kendi backend credential'larıyla notes MCP sunucusuna geçişli olarak erişebilir — ama yalnızca geçişli erişimi bağlayan policy altında.

### Gateway'de tool-hash pinning

Gateway, onaylanmış tool açıklamalarının (SHA256 hash'leri) bir manifest'ini tutar. Discovery zamanında, her backend'in `tools/list`'ini fetch eder, hash'leri manifest'e karşı karşılaştırır ve açıklaması mutate olmuş herhangi bir tool'u kaldırır. Bu, merkezi olarak uygulanan Faz 13 · 15'ten rug-pull savunmasıdır.

### Policy-as-code

İleri gateway'ler policy'yi OPA/Rego, Kyverno ya da Styra'da ifade eder. "Kullanıcı `alice`, `acme` org'undaki repo'larda yalnızca `github.open_pr` çağırabilir" gibi kurallar bildirimsel olarak kodlanır. Basit gateway'ler el-kodlanmış Python kullanır. İki şekil de geçerlidir.

### Session-aware routing

Bir kullanıcının session'ı bir sunucu karışımı içerdiğinde, gateway multipleks eder: geliştiricinin tek MCP session'ı N backend session'ı tutar, sunucu başına bir tane. Herhangi bir backend'den notification'lar gateway üzerinden geliştiricinin session'ına yönlendirilir.

### Namespace merging

Gateway'ler tüm backend'lerden tool namespace'lerini, tipik olarak collision'da prefix ile merge eder. `github.open_pr`, `notes.search`. Bu routing'i belirsizliksiz yapar.

### Registry'ler

- **Resmi MCP Registry (`registry.modelcontextprotocol.io`).** Anthropic, GitHub, PulseMCP, Microsoft stewardship altında launch oldu. Namespace-doğrulanmış (reverse-DNS: `io.github.user/server`). Temel kalite için ön-filtreli.
- **Glama.** Birçok kaynağı agregat eden arama-merkezli metaregistry.
- **MCPMarket.** Vendor listing'leriyle ticari-eğilimli dizin.
- **MCP.so.** Topluluk dizini; açık submission'lar.
- **Smithery.** Package-manager-style yükleme akışı.
- **LobeHub.** LobeChat uygulamasında UI-entegre registry.

Enterprise gateway'ler varsayılan olarak Resmi Registry'den çeker, metaregistry'lerden admin-curated eklemelere izin verir ve pinlenmemiş herhangi bir şeyi reddeder.

### Reverse-DNS naming

Resmi Registry public sunucular için reverse-DNS isimleri zorunlu kılar: `io.github.alice/notes`. Namespace'ler squatting'i önler ve trust delegation'ı daha net yapar.

### Vendor anketi, Nisan 2026

| Vendor | Güçlü yön |
|--------|----------|
| Cloudflare MCP Portals | Edge-hostlu; OAuth entegre; free tier |
| Kong AI Gateway | K8s-native; ince-tanecikli policy; OpenTelemetry'e log'lar |
| IBM ContextForge | Enterprise IAM; compliance; audit export |
| TrueFoundry | DevOps-eğilimli; metrics-first |
| MintMCP | Developer-platform yönelimli |
| Envoy AI Gateway | Açık kaynak; özelleştirilebilir filter'lar |

Faz 17 (production infrastructure) gateway operasyonlarında daha derine dalar.

## Kullan

`code/main.py` ~150 satırda minimal bir gateway yayınlar: kullanıcıları sahte bir Bearer token ile authenticate eder, kullanıcı başına bir RBAC policy tutar, request'leri iki backend MCP sunucusuna yönlendirir, her çağrıyı bir audit log'a yazar, bir rate limit zorlar ve açıklama hash'i pinned manifest ile eşleşmeyen herhangi bir backend tool'u reddeder.

Bakılacak şeyler:

- İzin verilen `server_tool` girdileriyle `user_id` ile keyed `RBAC` dict.
- `AUDIT_LOG` append-only bir event listesi.
- Rate limit kullanıcı başına bir token bucket kullanır.
- Pinned manifest `server::tool -> hash` dict'idir.

## Yayınla

Bu ders `outputs/skill-gateway-bootstrap.md` üretir. Bir enterprise MCP planı verildiğinde (kullanıcılar, backend'ler, compliance), skill bir gateway konfigürasyon spec'i üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. İzin verilen bir kullanıcı olarak bir çağrı yap; sonra izin verilmeyen bir kullanıcı; sonra rate-limit-aşılmış bir burst. Üç akışı da doğrula.

2. Sonuçları client'a döndürmeden önce PII'yi redact eden bir policy ekle. SSN-şekilli string'ler için basit bir regex pass kullan; boşluğu not et (e-postalar, telefon numaraları).

3. Audit log'unu OpenTelemetry GenAI span'leri yayacak şekilde genişlet. Faz 13 · 20 tam attribute'ları ele alır.

4. Beş backend'i (notes, github, postgres, jira, slack) olan 50-geliştiricili bir takım için bir RBAC policy tasarla. Her birinde read-only kim alır? Write kim alır?

5. Cloudflare enterprise MCP yazısını baştan sona oku. Cloudflare'in yayınladığı ve bu stdlib gateway'in yapmadığı bir feature'ı tanımla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Gateway | "MCP proxy" | Client'lar ve backend'ler arasında merkezileştiren sunucu |
| Credential vaulting | "Backend token'ları sunucu-tarafında kalır" | Geliştiriciler asla upstream token'ları görmez |
| Session-aware routing | "Çoklu-backend session" | Gateway geliştirici session'ı başına N backend session'ı multipleks eder |
| Tool-hash pinning | "Onaylanmış manifest" | Her onaylanmış tool açıklamasının SHA256'sı; rug-pull'ları merkezi olarak blokla |
| RBAC | "Kullanıcı başına policy" | Tool'lar ve sunucular için role-based access control |
| Policy-as-code | "Bildirimsel kurallar" | Gateway'de zorlanan OPA/Rego, Kyverno, Styra policy'leri |
| Audit log | "Kim, ne, ne zaman" | Compliance için append-only event log |
| Rate limit | "Kullanıcı başına token bucket" | Kötüye kullanımı önlemek için dakika başına sınırlar |
| Resmi MCP Registry | "Kanonik upstream" | `registry.modelcontextprotocol.io`, namespace-doğrulanmış |
| Reverse-DNS naming | "Registry namespace" | `io.github.user/server` konvansiyonu |

## İleri Okuma

- [Official MCP Registry](https://registry.modelcontextprotocol.io/) — kanonik upstream, namespace-doğrulanmış
- [Cloudflare — Enterprise MCP](https://blog.cloudflare.com/enterprise-mcp/) — OAuth ve policy ile gateway deseni
- [agentic-community — MCP gateway registry](https://github.com/agentic-community/mcp-gateway-registry) — açık kaynak referans gateway
- [TrueFoundry — What is an MCP gateway?](https://www.truefoundry.com/blog/what-is-mcp-gateway) — feature karşılaştırma makalesi
- [IBM — MCP context forge](https://github.com/IBM/mcp-context-forge) — IBM'den enterprise gateway
