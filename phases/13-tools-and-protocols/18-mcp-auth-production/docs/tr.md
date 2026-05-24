# Üretimde MCP Auth — DCR, JWKS Rotation, iii Primitive'leri Üzerinde Audience-Pinned Token'lar

> Ders 16 OAuth 2.1 state machine'ini bellekte ayağa kaldırdı. 2026'ya gelindiğinde, gerçek bir org'a yayınladığın her MCP sunucusu üretim auth'unun arkasında oturuyor: dynamic client registration (RFC 7591), authorization-server metadata discovery (RFC 8414), 3'te bir token doğrulamasını bozmayan JWKS rotation ve confused-deputy yeniden kullanımı reddeden audience-pinned token'lar. Bu ders bunların hepsini iii primitive'leri üzerinden bağlar — HTTP ve cron için `iii.registerTrigger`, auth mantığı için `iii.registerFunction`, cache'lenmiş key'ler için `state::set/get` — böylece auth yüzeyi engine'deki her diğer workload gibi observable, restart edilebilir ve replay edilebilir.

**Tür:** Yapım
**Diller:** Python (stdlib, iii primitive'leri ders ortamı için mock'lanmış)
**Ön koşullar:** Faz 13 · 16 (OAuth 2.1 state machine), Faz 13 · 17 (gateway'ler)
**Süre:** ~90 dakika

## Öğrenme Hedefleri

- RFC 8414 metadata'sı üzerinden bir authorization server'ı keşfet ve sözleşmeyi doğrula.
- MCP client'larının admin müdahalesi olmadan kaydolması için RFC 7591 dynamic client registration implemente et.
- Signature doğrulaması key roll-over'ı atlatsın diye bir cron trigger kullanarak JWKS key'leri cache'le ve rotate et.
- Token'ları tek bir MCP resource'una RFC 8707 resource indicator'larla pinle ve confused-deputy yeniden kullanımı reddet.
- Her endpoint ve background job'u iii primitive'leri olarak bağla — HTTP trigger'lar, cron trigger'lar, isimlendirilmiş fonksiyonlar ve `state::*` okumaları — böylece tek bir restart auth yüzeyini yeniden inşa eder.
- Bir IdP capability matrisi oku ve IdP MCP'nin auth profilini tatmin edemediğinde deploy etmeyi reddet.

## Sorun

Ders 16 simülatörü OAuth 2.1'i bellekte çalıştırır. Üretimin bellek-only bir simülatörün görmediği üç operasyonel boşluğu vardır.

Birinci boşluk enrollment'tır. Gerçek bir org yüzlerce MCP sunucusu ve binlerce MCP client çalıştırır. Operatörler her Cursor kullanıcısını OAuth client olarak elle kaydetmez. RFC 7591 dynamic client registration, bir client'ın authorization server'a karşı `POST /register` yapmasına ve anında bir `client_id` (ve opsiyonel olarak `client_secret`) almasına izin verir. Sunucu RFC 8414 metadata'sında `registration_endpoint` yayınlar; client onu out-of-band konfigürasyon olmadan keşfeder.

İkinci boşluk key rotation'dır. JWT doğrulaması, JSON Web Key Set (JWKS) olarak yayınlanan authorization server'ın signing key'lerine bağlıdır. Authorization server bunları bir programda rotate eder (genellikle saatlik, bazen incident response altında daha hızlı). Boot'ta JWKS'i bir kez fetch eden bir MCP sunucusu rotation penceresine kadar iyi doğrular — sonra her request restart'a kadar başarısız olur. Üretim, JWKS'i, önceki key'ler expire olmadan cache'i overwrite eden bir refresh job ile cache'lenmiş bir değer olarak bağlar, artı cache'ten daha yeni bir key tarafından imzalanmış bir token geldiğinde için cache miss'te bir fall-back fetch.

Üçüncü boşluk audience binding'dir. Ders 16 RFC 8707 resource indicator'larını tanıttı. Üretimde, o indicator her request'te sert bir claim kontrolü olur. MCP sunucusu `token.aud`'u kendi kanonik resource URL'siyle karşılaştırır ve mismatch'leri HTTP 401 ile reddeder. Bu, aynı trust mesh'teki bir upstream MCP sunucusunun (ya da bir sunucu için olan bir token'ı tutan kötü niyetli bir client'ın) o token'ı başka bir sunucuya replay etmesine karşı tek savunmadır.

Bu ders, bu boşlukların her birini bir iii primitive'i olarak ele alır. Metadata dokümanı bir fonksiyonun çıktısını döndüren bir HTTP trigger'dır. JWKS rotation, `auth::rotate-jwks`'i çağıran bir cron trigger'dır, bu da `state::set("auth/jwks/<issuer>", ...)`'a yazar. JWT doğrulaması başkalarının `iii.trigger("auth::validate-jwt", token)` üzerinden çağırdığı bir fonksiyondur. MCP sunucusunun kendisi dispatch'ten önce doğrulamayı çağıran bir başka HTTP trigger'dır. Engine'i restart et: trigger registry'si yeniden inşa olur; state hayatta kalır; auth yüzeyi manuel reconciliation olmadan operasyoneldir.

## Kavram

### RFC 8414 — OAuth Authorization Server Metadata

`/.well-known/oauth-authorization-server`'daki bir doküman client'ın ihtiyaç duyduğu her şeyi tanımlar:

```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
  "registration_endpoint": "https://auth.example.com/register",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "scopes_supported": ["mcp:tools.read", "mcp:tools.invoke"],
  "token_endpoint_auth_methods_supported": ["none", "private_key_jwt"]
}
```

Bir MCP resource URL'si verilen bir client discovery'yi zincirler: RFC 9728'den `oauth-protected-resource` (resource server'ın dokümanı) issuer'ı adlandırır, sonra `oauth-authorization-server` (bu RFC) her endpoint'i adlandırır. Client asla bir authorization URL'sini hard-code etmez.

Bir IdP'ye MCP için güvenmeden önce doğruladığın sözleşme:

- `code_challenge_methods_supported` `S256` (RFC 7636 başına PKCE) içerir.
- `grant_types_supported` `authorization_code` içerir ve `password` ile `implicit`'i reddeder.
- `registration_endpoint` mevcuttur (RFC 7591 desteği).
- `response_types_supported` OAuth 2.1 için tam olarak `["code"]`'dur.

Bunlardan herhangi biri eksikse, MCP sunucusu bu IdP'ye karşı deploy etmeyi reddeder. Deployment manifest yanlış, kod değil.

### RFC 9728 (özet) — Protected Resource Metadata

Ders 16 RFC 9728'i ele aldı. Üretimdeki delta: bu doküman, client'ın *bu* MCP sunucusu tarafından güvenilen authorization sunucularını bulmak için baktığı tek yerdir. Tek bir MCP sunucusu birden fazla IdP'den token kabul edebilir (biri staff için, biri partner'lar için). RFC 9728 o kümeyi bildirir; RFC 8414 her IdP'nin neyi desteklediğini belgeler.

```json
{
  "resource": "https://notes.example.com",
  "authorization_servers": ["https://auth.example.com", "https://partners.example.com"],
  "scopes_supported": ["mcp:tools.invoke"],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://notes.example.com/docs"
}
```

### RFC 7591 — Dynamic Client Registration

DCR olmadan, her MCP client'ı (Cursor, Claude Desktop, custom bir agent) IdP admin'i ile out-of-band bir değişim gerektirir. DCR ile, client post eder:

```json
POST /register
Content-Type: application/json

{
  "redirect_uris": ["http://127.0.0.1:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "scope": "mcp:tools.invoke",
  "client_name": "Cursor",
  "software_id": "com.cursor.cursor",
  "software_version": "0.42.0"
}
```

Sunucu `client_id` ve sonraki güncellemeler için bir `registration_access_token` ile yanıt verir:

```json
{
  "client_id": "c_3e7f1a",
  "client_id_issued_at": 1769472000,
  "redirect_uris": ["http://127.0.0.1:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "registration_access_token": "regt_b2...",
  "registration_client_uri": "https://auth.example.com/register/c_3e7f1a"
}
```

`token_endpoint_auth_method: none`, kullanıcının cihazında çalışan MCP client'ları için doğru varsayılandır. Yalnızca bir `client_id` alırlar — exfiltrate edilecek `client_secret` yok. PKCE public client'ların ihtiyaç duyduğu proof-of-possession'u sağlar.

Üç üretim tuzağı:

- Registration endpoint kaynak IP ile rate-limit yapmalıdır. Onsuz, kötü niyetli bir aktör milyonlarca sahte kayıt scriptler ve `client_id` namespace'ini tüketir. iii bunu önemsiz yapar: registration HTTP trigger'ı registrar'a dispatch etmeden önce bir `auth::rate-limit` fonksiyonu çağırır.
- `software_statement` (client için kefil olan imzalı bir JWT) bazı enterprise IdP'ler tarafından gereklidir. Dersin mock'u bunu atlar; üretim, localhost redirect URI'larından başka her şeyden gelen imzasız kayıtları reddeden bir doğrulama adımı bağlar.
- `registration_access_token`, plaintext değil, hash olarak saklanmalıdır. Bu token'ın çalınması, saldırganın client'ın redirect URI'larını yeniden yazabileceği anlamına gelir.

### RFC 8707 (özet) — Resource Indicator'lar

Ders 16 şekli belirledi. Üretim kuralı: her token request'i `resource=<canonical-mcp-url>` içerir ve MCP sunucusu her çağrıda `token.aud`'un kendi resource URL'siyle eşleştiğini doğrular. MCP sunucusu `https://notes.example.com/mcp`'de erişilebilirse, kanonik URL `https://notes.example.com`'dur — yol bileşeni hariç tutulur, böylece tek bir sunucu bir audience altında birden fazla yol host eder.

### RFC 7636 (özet) — PKCE

PKCE OAuth 2.1'de zorunludur. Dersin authorization-code akışı her zaman `code_challenge` ve `code_verifier` taşır. Sunucu verifier'sız ya da saklanan challenge'a hash'lenmeyen verifier'lı herhangi bir token request'ini reddeder.

### MCP Spec 2025-11-25 Auth Profili

MCP spec'i (2025-11-25) bir MCP sunucusunun authorization katmanının ne yapması gerektiği konusunda kesindir:

- `/.well-known/oauth-protected-resource` yayınla (RFC 9728).
- Token'ları yalnızca `Authorization: Bearer ...` üzerinden kabul et.
- Request başına `aud`, `iss`, `exp` ve gerekli scope'ları doğrula.
- Her 401 ve 403 için `Bearer error=...` taşıyan `WWW-Authenticate` ile yanıt ver, gerektiğinde `scope=` ve `resource=` parametreleri dahil.
- `aud`'u kanonik resource ile eşleşmeyen token'ları reddet.
- `iss`'i protected-resource metadata'sının `authorization_servers` listesinde olmayan token'ları reddet.

OAuth 2.1 draft substrat'tır; RFC 8414/7591/8707/9728 + RFC 7636 yüzeydir; MCP spec'i profildir.

### IdP capability matrisi

Her IdP tam MCP profilini desteklemez. Aşağıdaki matris 2025-11-25 spec'i itibarıyla olgusal capability ifadelerini belgeler. Bir *deployment gate*'dir, bir tavsiye değildir.

| IdP kategorisi | RFC 8414 metadata | RFC 7591 DCR | RFC 8707 resource | RFC 7636 S256 PKCE | Notlar |
|---|---|---|---|---|---|
| Self-hosted (Keycloak) | evet | evet | evet (24.x'ten beri) | evet | Bu derste MCP profili için referans IdP; her RFC'yi end-to-end destekler. |
| Enterprise SSO (Microsoft Entra ID) | evet | evet (premium tier'lar) | evet | evet | DCR mevcudiyeti tenant tier'a göre değişir; deploy etmeden önce hedef tenant'ta doğrula. |
| Enterprise SSO (Okta) | evet | evet (Okta CIC / Auth0) | evet | evet | DCR Auth0'da mevcut (şimdi Okta CIC); classic Okta org'lar admin ön-kaydı gerektirir. |
| Sosyal login IdP'leri (genel) | değişir | nadiren | nadiren | evet | Sosyal IdP'lerin çoğu client'ları statik partner olarak ele alır; DCR'a güvenme. Yalnızca identity source olarak kullan, üstüne kendi MCP-aware authorization server'ını katmanla. |
| Custom / homegrown | bağlı | bağlı | bağlı | bağlı | Kendin yayınlıyorsan, tam profili yayınla. Yukarıdaki dört RFC'den herhangi birini atlamak MCP auth sözleşmesini bozar. |

Deployment manifest için ret kuralı: seçilen IdP `registration_endpoint` döndürmüyorsa ve `code_challenge_methods_supported`'da `S256` listelemiyorsa, MCP sunucusu başlamayı reddeder. Degraded mod yoktur.

### iii ile JWKS rotation deseni

Üretim başarısızlık modu eski bir JWKS cache'idir. Bir cron trigger ve bir `state::*` cache ile çöz:

```python
iii.registerTrigger(
    "cron",
    {"schedule": "0 */6 * * *", "name": "auth::jwks-refresh"},
    "auth::rotate-jwks",
)
```

Her altı saatte bir, cron trigger `auth::rotate-jwks`'i çağırır, bu da `<issuer>/.well-known/jwks.json`'u fetch eder ve `state::set("auth/jwks/<issuer>", {keys, fetched_at})`'a yazar. Validator `state::get`'ten okur. `kid`'i cache'ten eksik olan bir token, fall-back olarak senkron bir `auth::rotate-jwks` çağrısı tetikler. Bu iki durumu birden ele alır: scheduled rotation (cron) ve key-overlap pencereleri (senkron fall-back).

State şekli:

```json
{
  "auth/jwks/https://auth.example.com": {
    "keys": [
      {"kid": "k_2026_03", "kty": "RSA", "n": "...", "e": "AQAB", "alg": "RS256", "use": "sig"},
      {"kid": "k_2026_04", "kty": "RSA", "n": "...", "e": "AQAB", "alg": "RS256", "use": "sig"}
    ],
    "fetched_at": 1772668800
  }
}
```

Bir anda iki key steady state'tir. Authorization sunucuları, eski key altında verilen token'lar expire olana kadar geçerli kalsın diye, öncekini (`k_2026_03`) emekli etmeden bir sonraki key'i (`k_2026_04`) tanıtarak rotate eder. Cache birleşimi tutar; validator `kid` ile seçer.

### iii primitive wiring (bu dersin gerçekten konusu)

Beş primitive auth yüzeyini compose eder:

```python
# 1. RFC 8414 metadata document
iii.registerTrigger(
    "http",
    {"path": "/.well-known/oauth-authorization-server", "method": "GET"},
    "auth::serve-asm",
)

# 2. RFC 7591 dynamic client registration
iii.registerTrigger(
    "http",
    {"path": "/register", "method": "POST"},
    "auth::register-client",
)

# 3. JWT validation as a callable function (the resource server triggers it)
iii.registerFunction("auth::validate-jwt", validate_jwt_handler)

# 4. Step-up issuance for incremental scope (SEP-835 from L16)
iii.registerFunction("auth::issue-step-up", issue_step_up_handler)

# 5. Cron-driven JWKS rotation
iii.registerTrigger(
    "cron",
    {"schedule": "0 */6 * * *"},
    "auth::rotate-jwks",
)
iii.registerFunction("auth::rotate-jwks", rotate_jwks_handler)
```

MCP sunucusunun kendisi doğrulamayı asla doğrudan çağırmaz. Şunu yapar:

```python
result = iii.trigger("auth::validate-jwt", {"token": bearer_token, "resource": self.resource})
if not result["valid"]:
    return {"status": 401, "WWW-Authenticate": result["www_authenticate"]}
```

Bu indirection iii'nin bahsidir. Yarın validator'ı paralel olarak iki IdP'ye danışan bir fanout ile değiştirirsin ya da bir span emitter eklersin ya da pozitif doğrulamaları cache'lersin. MCP sunucusu değişmez.

### Audience binding ile confused-deputy gezintisi

Sunucu A (`notes.example.com`) ve Sunucu B (`tasks.example.com`) ikisi de aynı authorization server'a karşı kayıtlı. Sunucu A kompromize. Saldırgan kullanıcının notes token'ını alır ve Sunucu B'ye karşı replay eder.

Sunucu B'nin validator'ı:

1. JWT'yi decode et, JWKS'i `kid` ile fetch et, signature'ı doğrula.
2. `iss`'i protected-resource metadata'sının `authorization_servers`'una karşı kontrol et. (Geçer — aynı IdP.)
3. `aud == "https://tasks.example.com"`'u kontrol et. (Fail — token'ın `aud`'ı `https://notes.example.com`.)
4. `WWW-Authenticate: Bearer error="invalid_token", error_description="audience mismatch"` ile 401 döndür.

Audience claim'i protokol katmanında bu saldırıya karşı tek savunmadır. Performans için atlamak en yaygın üretim hatasıdır; validator yalnızca session başında değil, her request'te çalışmalıdır.

### Başarısızlık modları

- **Eski JWKS.** Validator key rotation'dan sonra geçerli token'ları reddeder. Düzeltme yukarıdaki cron+fall-back desenidir. JWKS'i refresh job olmadan asla cache'leme.
- **Eksik `aud` claim.** Bazı IdP'ler `resource` token request'inde yoksa varsayılan olarak `aud`'u atlar. Validator eksik `aud`'lu token'ları reddetmelidir, yokluğu wildcard olarak ele almamalıdır.
- **Scope upgrade race.** Aynı kullanıcı için iki eşzamanlı step-up akışı ikisi de başarılı olabilir ve farklı scope'lu iki access token üretebilir. Validator request'te sunulan token'ı kullanmalıdır, "kullanıcının mevcut scope'unu" aramamalıdır — bu bir TOCTOU penceresi yaratır.
- **Registration token theft.** Sızdırılmış bir `registration_access_token` saldırganın redirect URI'larını yeniden yazmasına izin verir. Bunları at-rest hash'le; her güncellemede client'ın cleartext sunmasını gerektir; şüphede rotate et.
- **`iss` pinlenmemiş.** Herhangi bir `iss`'i kabul eden bir validator, saldırganın kendi authorization server'ını ayağa kaldırmasına, hedef audience için bir client kaydetmesine ve token vermesine izin verir. Protected-resource metadata'sının `authorization_servers` listesi allow-list'tir; zorla.

## Kullan

`code/main.py` tam üretim akışını stdlib Python ve `iii.registerFunction`, `iii.registerTrigger`, `iii.trigger` ve `state::set/get`'i taklit eden ufak bir `iii_mock` registry'si ile gezer. Akış:

1. Authorization server `/.well-known/oauth-authorization-server`'da RFC 8414 metadata'sını yayınlar.
2. MCP client metadata endpoint'ini çağırır, registration endpoint'ini keşfeder.
3. MCP client `/register`'a post eder (RFC 7591) ve bir `client_id` alır.
4. MCP client `resource` indicator'lı (RFC 8707) PKCE-korumalı authorization code akışını (RFC 7636) çalıştırır.
5. MCP client `Authorization: Bearer ...` ile MCP sunucusunda bir tool çağırır.
6. MCP sunucusu `auth::validate-jwt`'ı tetikler, bu da `state::get`'ten JWKS okur.
7. Cron trigger `auth::rotate-jwks`'i tetikler, state'teki JWKS'i değiştirir.
8. Sonraki çağrı restart olmadan yeni key'lere karşı doğrular.
9. Farklı bir MCP resource'una karşı bir confused-deputy denemesi audience mismatch ile 401 alır.

Burada mock JWT shared secret'lı HS256 kullanır (böylece ders yalnızca stdlib'de çalışır). Üretim yukarıdaki JWKS deseniyle RS256 ya da EdDSA kullanır; doğrulama mantığı diğer açılardan aynıdır.

## Yayınla

Bu ders `outputs/skill-mcp-auth-iii.md` üretir. Bir MCP sunucu config'i ve bir IdP capability kümesi verildiğinde, skill kaydolacak iii primitive'lerini, JWKS rotation programını, scope mapping'i ve IdP tam RFC profilini desteklemediğinde uygulanacak ret kurallarını yayınlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. 9 adımlı akışı izle. `auth::rotate-jwks` onu overwrite etmeden hemen önce `state::get`'in eski veri döndürdüğü yeri ve sonraki request'in nasıl yeni key'e karşı doğruladığını not et.

2. Protected-resource metadata'sının `authorization_servers` listesine yeni bir IdP ekle. Yeni IdP tarafından imzalanmış bir token ver ve validator'ın kabul ettiğini doğrula. Listelenmemiş bir IdP tarafından imzalanmış bir token ver ve validator'ın `WWW-Authenticate: Bearer error="invalid_token", error_description="iss not allowed"` ile reddettiğini doğrula.

3. `auth::rate-limit`'i bir iii fonksiyonu olarak implemente et ve registration HTTP trigger'ının içinden registrar çalışmadan önce çağır. `state::set("auth/ratelimit/<ip>", ...)`'da tutulan kaynak IP başına bir token-bucket kullan.

4. RFC 7591'i oku ve dersin `/register` handler'ının doğrulamadığı iki alanı tanımla. Doğrulamayı ekle. (İpucu: `software_statement` ve `redirect_uris` URI şeması.)

5. MCP spec'i 2025-11-25 authorization bölümünü oku. Dersin validator'ının şu anda yaymadığı `WWW-Authenticate` header'ları üzerindeki bir normatif gereksinimi bul. Onu ekle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| ASM | "OAuth metadata dokümanı" | RFC 8414 `/.well-known/oauth-authorization-server` JSON |
| DCR | "Self-service client kaydı" | RFC 7591 `POST /register` akışı |
| JWKS | "JWT doğrulaması için public key'ler" | JSON Web Key Set, `jwks_uri`'dan fetch'lenir, `kid` ile indekslenir |
| Resource indicator | "Audience parametresi" | Token'ı bir sunucuya pinleyen RFC 8707 `resource` parametresi |
| `aud` claim | "Audience" | Validator'ın kanonik resource URL ile karşılaştırdığı JWT claim'i |
| Confused deputy | "Token replay" | Sunucu A için verilen bir token'ın Sunucu B'ye sunulduğu saldırı |
| `iss` allow-list | "Güvenilen authorization sunucuları" | Protected-resource metadata'sının `authorization_servers`'ında adlandırılan küme |
| Key rotation | "Rolling JWKS" | Overlap pencereleri ile signing key'lerin periyodik değiştirilmesi |
| Public client | "Native ya da browser client'ı" | `client_secret`'siz OAuth client; PKCE telafi eder |
| `WWW-Authenticate` | "401/403 yanıt header'ı" | Client recovery'sini süren `Bearer error=...` direktifleri taşır |

## İleri Okuma

- [MCP — Authorization spec (2025-11-25)](https://modelcontextprotocol.io/specification/draft/basic/authorization) — bu dersin implemente ettiği MCP auth profili
- [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414) — discovery sözleşmesi
- [RFC 7591 — OAuth 2.0 Dynamic Client Registration Protocol](https://datatracker.ietf.org/doc/html/rfc7591) — DCR
- [RFC 7636 — Proof Key for Code Exchange (PKCE)](https://datatracker.ietf.org/doc/html/rfc7636) — public-client proof-of-possession
- [RFC 8707 — Resource Indicators for OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc8707) — audience pinning
- [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728) — resource server discovery
- [OAuth 2.1 draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1) — konsolide OAuth substrat'ı
