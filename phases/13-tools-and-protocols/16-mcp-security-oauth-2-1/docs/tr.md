# MCP Güvenliği II — OAuth 2.1, Resource Indicator'lar, Incremental Scope'lar

> Uzak MCP sunucularının yalnızca authentication'a değil, authorization'a ihtiyacı var. 2025-11-25 spec'i OAuth 2.1 + PKCE + resource indicator'lar (RFC 8707) + protected-resource metadata (RFC 9728) ile hizalanır. SEP-835, 403 WWW-Authenticate üzerinde step-up authorization ile incremental scope onayı ekler. Bu ders step-up akışını bir state machine olarak implemente eder, böylece her hop'u görebilirsin.

**Tür:** Yapım
**Diller:** Python (stdlib, OAuth state machine simulator)
**Ön koşullar:** Faz 13 · 09 (transport'lar), Faz 13 · 15 (güvenlik I)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Resource server'ı authorization server sorumluluklarından ayırt et.
- PKCE-korumalı OAuth 2.1 authorization code akışını gez.
- Confused-deputy saldırılarını önlemek için `resource` (RFC 8707) ve protected-resource metadata (RFC 9728) kullan.
- Step-up authorization implemente et: sunucu daha yüksek bir scope isteyen WWW-Authenticate ile 403 yanıt verir; client kullanıcı onayını yeniden ister ve retry yapar.

## Sorun

Erken MCP (2025 öncesi) ad-hoc API key'leri ya da hiç auth olmadan uzak sunucular yayınladı. 2025-11-25 spec'i o boşluğu tam bir OAuth 2.1 profili ile kapatır.

Üç gerçek dünya ihtiyacı:

- **Sıradan uzak sunucular.** Kullanıcı Notion / GitHub / Gmail'lerine erişen uzak bir MCP sunucusu yükler. PKCE ile OAuth 2.1 doğru şekildir.
- **Scope yükseltme.** `notes:read` verilmiş bir notes sunucusu daha sonra belirli bir aksiyon için `notes:write`'a ihtiyaç duyabilir. Tüm akışı yeniden yapmak yerine, step-up (SEP-835) ek scope'u ister.
- **Confused deputy önleme.** Client, Sunucu A için audience-scope'lu bir token tutar. Sunucu A kötü niyetlidir ve token'ı Sunucu B'ye sunmaya çalışır. Resource indicator'lar (RFC 8707) token'ı amaçlanan audience'ına pinler.

OAuth 2.1 yeni değil. Yeni olan MCP'nin profili: belirli gerekli akışlar (yalnızca authorization code + PKCE; implicit yok, varsayılan olarak client credentials yok), her token request'inde zorunlu resource indicator'lar ve client'ların nereye gideceğini bilmesi için yayınlanan protected-resource metadata.

## Kavram

### Rol'ler

- **Client.** MCP client'ı (Claude Desktop, Cursor, vb.).
- **Resource server.** MCP sunucusu (notes, GitHub, Postgres, ne olursa).
- **Authorization server.** Token verir. Resource server ile aynı servis olabilir ya da ayrı bir IdP (Auth0, Keycloak, Cognito) olabilir.

MCP'nin profilinde, resource ve authorization sunucuları aynı host OLABİLİR ama URL'lerle ayırt edilMELİDİR.

### Authorization code + PKCE

Akış:

1. Client `code_verifier` (random) ve `code_challenge` (SHA256) üretir.
2. Client kullanıcıyı `/authorize?response_type=code&client_id=...&redirect_uri=...&scope=notes:read&code_challenge=...&resource=https://notes.example.com` adresine redirect eder.
3. Kullanıcı onaylar. Authorization server `redirect_uri?code=...` adresine redirect eder.
4. Client `/token?grant_type=authorization_code&code=...&code_verifier=...&resource=...` adresine POST eder.
5. Authorization server verifier'ın hash'ini saklanan challenge'a karşı doğrular ve bir access token verir.
6. Client token'ı kullanır: resource server'a her request'te `Authorization: Bearer ...`.

PKCE authorization-code interception saldırılarını önler. Resource indicator'lar token'ın başka yerde geçerli olmasını önler.

### Protected-resource metadata (RFC 9728)

Resource server bir `.well-known/oauth-protected-resource` dokümanı yayınlar:

```json
{
  "resource": "https://notes.example.com",
  "authorization_servers": ["https://auth.example.com"],
  "scopes_supported": ["notes:read", "notes:write", "notes:delete"]
}
```

Client authorization server'ı resource server'dan keşfeder. Konfigürasyonu azaltır — client yalnızca resource URL'ye ihtiyaç duyar.

### Resource indicator'lar (RFC 8707)

Token request'indeki `resource` parametresi token'ın amaçlanan audience'ını pinler. Verilen token `aud: "https://notes.example.com"` içerir. Bu token'ı alan başka bir MCP sunucusu `aud`'ı kontrol eder ve onu reddeder.

### Scope modeli

Scope'lar boşlukla ayrılmış string'lerdir. Yaygın MCP konvansiyonları:

- `notes:read`, `notes:write`, `notes:delete`
- Admin capability'leri için `admin:*` (idareli kullan)
- Kimlik için `profile:read`

Scope seçimi least-privilege olmalıdır: şu anda ihtiyacın olanı iste, daha fazlasına ihtiyacın olduğunda step-up yap.

### Step-up authorization (SEP-835)

Kullanıcı `notes:read` verir. Daha sonra agent'tan bir notu silmesini ister. Sunucu yanıt verir:

```
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope",
    scope="notes:delete", resource="https://notes.example.com"
```

Client insufficient_scope hatasını görür, kullanıcıya ek scope için bir onay diyaloğu prompt'lar, bunun için bir mini OAuth akışı gerçekleştirir, yeni token ile request'i retry eder.

### Token audience doğrulaması

Her request: sunucu `token.aud == self.resource_url` kontrol eder. Mismatch = 401. Bu cross-server token yeniden kullanımını durdurur.

### Kısa-ömürlü token'lar ve rotation

Access token'lar kısa-ömürlü OLMALIDIR (varsayılan 1 saat). Refresh token'lar her refresh'te rotate olur. Client arka planda sessiz refresh ele alır.

### Token passthrough yok

Sampling sunucuları (Faz 13 · 11) client'ın token'ını diğer servislere geçirMEMEliDİR. Sampling request sınırdır.

### Confused deputy önleme

Token `aud`'a bağlanır. Client `client_id`'ye bağlanır. Her request ikisine karşı doğrulanır. Spec, MCP öncesi uzak tool ekosistemlerinde yaygın olan eski "pass-the-token" desenini açıkça yasaklar.

### Client ID discovery

Her MCP client'ı metadata'sını sabit bir URL'de yayınlar. Authorization sunucuları client'ın metadata dokümanını redirect URI'leri ve contact bilgilerini keşfetmek için fetch edebilir. Bu manuel client kaydını kaldırır.

### Gateway'ler ve OAuth

Faz 13 · 17 bir enterprise gateway'in OAuth'u nasıl ele aldığını gösterir: gateway upstream sunucular için credential'lar tutar, client'a olan token'lar gateway-verilmiştir ve upstream token'lar asla gateway'i terk etmez. Bu güven modelini çevirir — kullanıcılar gateway ile bir kez authenticate olur; gateway N sunucu authorization'ını ele alır.

## Kullan

`code/main.py` tam OAuth 2.1 step-up akışını bir state machine olarak simüle eder. Şunları implemente eder:

- PKCE code-verifier / challenge üretimi.
- Resource indicator ile authorization code akışı.
- Protected-resource metadata endpoint'i.
- Audience kontrolü ile token doğrulaması.
- `insufficient_scope`'ta step-up.

Bu derste HTTP server yok; state machine bellekte çalışır, böylece her hop'u izleyebilirsin. Faz 13 · 17'nin gateway dersi onu gerçek bir transport'a bağlar.

## Yayınla

Bu ders `outputs/skill-oauth-scope-planner.md` üretir. Tool'lu uzak bir MCP sunucusu verildiğinde, skill scope kümesini, pinning kurallarını ve step-up policy'yi tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. İki-scope step-up akışını izle. Step-up'ta hangi hop'ların tekrarlandığını not et.

2. Refresh-token rotation ekle: her refresh yeni bir refresh token verir ve eskiyi geçersiz kılar. Rotation sonrası kullanılan çalınmış bir refresh token simüle et ve başarısız olduğunu doğrula.

3. Protected-resource metadata endpoint'ini stdlib http.server kullanarak gerçek bir HTTP yanıtı olarak implemente et. Ders 09'daki /mcp endpoint'ini yansıt.

4. Bir GitHub MCP sunucusu için bir scope hiyerarşisi tasarla: repo oku, PR yaz, PR onayla, PR merge, admin. Her seviye arasında step-up kullan.

5. RFC 8707 ve RFC 9728'i oku. MCP'nin 9728'in örneğinden farklı kullandığı tek alanı tanımla. (İpucu: `scopes_supported` ile ilgili.)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| OAuth 2.1 | "Modern OAuth" | PKCE'yi zorunlu kılan ve implicit akışı yasaklayan konsolide RFC |
| PKCE | "Proof-of-possession" | Authorization-code interception'ı yenen code verifier + challenge |
| Resource indicator | "Token audience" | Token'ı bir sunucuya pinleyen RFC 8707 `resource` parametresi |
| Protected-resource metadata | "Discovery doc" | RFC 9728 `.well-known/oauth-protected-resource` |
| Step-up authorization | "Incremental onay" | Talep üzerine scope eklemek için SEP-835 akışı |
| `insufficient_scope` | "WWW-Authenticate ile 403" | Daha büyük bir scope için yeniden-onay sunucu sinyali |
| Confused deputy | "Servisler arası token yeniden kullanımı" | Güvenilen bir tutucunun uygunsuzca bir token forward ettiği saldırı |
| Kısa-ömürlü token | "Access token TTL'i" | Hızlıca expire olan Bearer; refresh token yeniler |
| Scope hiyerarşisi | "Least privilege stack" | Seviyeler arası step-up'lı kademeli scope kümesi |
| Client ID metadata | "Client discovery doc" | Client'ın kendi OAuth metadata'sını yayınladığı URL |

## İleri Okuma

- [MCP — Authorization spec](https://modelcontextprotocol.io/specification/draft/basic/authorization) — kanonik MCP OAuth profili
- [den.dev — MCP November authorization spec](https://den.dev/blog/mcp-november-authorization-spec/) — 2025-11-25 değişikliklerinin gezintisi
- [RFC 8707 — Resource indicators for OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc8707) — audience-pinning RFC'si
- [RFC 9728 — OAuth 2.0 protected resource metadata](https://datatracker.ietf.org/doc/html/rfc9728) — discovery-doc RFC'si
- [Aembit — MCP OAuth 2.1, PKCE and the future of AI authorization](https://aembit.io/blog/mcp-oauth-2-1-pkce-and-the-future-of-ai-authorization/) — pratik step-up-flow gezintisi
