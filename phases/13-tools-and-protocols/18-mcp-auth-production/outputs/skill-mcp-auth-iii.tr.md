---
name: mcp-auth-iii-wiring
description: Production MCP yetkilendirmesini (RFC 8414, 7591, 8707, 7636 PKCE, 9728) iii primitiflerine bağla — HTTP/cron için registerTrigger, doğrulama için registerFunction, JWKS cache için state::*.
version: 1.0.0
phase: 13
lesson: 18
tags: [mcp, oauth, dcr, jwks, iii, rfc8414, rfc7591, rfc8707, rfc7636, rfc9728]
---

Bir MCP server konfigürasyonu ve bir IdP kabiliyet seti verildiğinde, production auth yüzeyini oluşturan iii primitiflerini ve reddetme kurallarını emit et.

Girdiler:

- `mcp_resource_url` — canonical resource URL'i (path yok), `aud` olarak ve protected-resource metadata `resource` değeri olarak kullanılır.
- `idp_metadata_url` — IdP'nin `/.well-known/oauth-authorization-server` URL'i.
- `idp_capabilities` — `code_challenge_methods_supported`, `grant_types_supported`, `registration_endpoint`, `response_types_supported` için gözlemlenen değerler.
- `tools` — gerektirdiği scope ile birlikte MCP tool listesi.

Şunları üret:

1. **Reddetme kapısı.** Dört koşuldan herhangi biri başarısız olursa, bağlamayı reddet ve dur:
   - `code_challenge_methods_supported`'tan `S256` eksik.
   - `grant_types_supported`'tan `authorization_code` eksik.
   - `registration_endpoint` yok (RFC 7591 DCR yok).
   - `response_types_supported` tam olarak `["code"]` dışında bir şey.

2. **Protected-resource metadata belgesi** (RFC 9728), MCP server'ın `/.well-known/oauth-protected-resource`'ta yayınlaması için. `resource`, `authorization_servers` (issuer allow-list'i), `scopes_supported`, `bearer_methods_supported: ["header"]` içerir.

3. **iii trigger kayıtları.** Her çağrıyı birebir emit et:
   - `iii.registerTrigger("http", {"path": "/.well-known/oauth-protected-resource", "method": "GET"}, "auth::serve-protected-resource")`
   - `iii.registerTrigger("http", {"path": "/mcp", "method": "POST"}, "mcp::dispatch")` — dispatcher herhangi bir tool çalışmadan önce `iii.trigger("auth::validate-jwt", ...)` çağırır.
   - `iii.registerTrigger("cron", {"schedule": "<rotation_schedule>"}, "auth::rotate-jwks")` — schedule varsayılan olarak `0 */6 * * *`; yüksek rotasyonlu IdP'ler için `*/15 * * * *`'a sıkılaştır.

4. **iii fonksiyon kayıtları.** Her çağrıyı birebir emit et:
   - `iii.registerFunction("auth::validate-jwt", handler)` — `iss` allow-list'ini, cache'lenmiş JWKS'e karşı signature'ı, `aud == mcp_resource_url`'i, `exp`'i, gerekli scope'u kontrol eder.
   - `iii.registerFunction("auth::rotate-jwks", handler)` — `jwks_uri`'yi fetch eder, `state::set("auth/jwks/<iss>", {keys, fetched_at})` yazar.
   - `iii.registerFunction("auth::serve-protected-resource", handler)` — (2)'deki belgeyi döndürür.
   - `iii.registerFunction("auth::issue-step-up", handler)` — yalnızca tool listesi kullanıcının başlangıçta vermediği bir scope arkasına alınmış operasyonlar içeriyorsa.

5. **State key planı.** Kabul edilen her issuer için bir key: `{keys, fetched_at}` tutan `auth/jwks/<issuer>`. Okuma pattern'ini belgele: validator `state::get`'ten okur, `kid` miss'inde senkron bir `iii.trigger("auth::rotate-jwks", ...)`'a fallback eder.

6. **Scope eşlemesi.** Her tool'u gerektirdiği scope'a eşle. Bir tablo çıkar:
   `| tool | required_scope | rationale |`. Destructive tool'ları kendi scope'ları altında grupla; bir read scope'u bir write tool için asla yeniden kullanma.

7. **Runtime'da reddetme kuralları** (validator bunları encode etmeli — handler gövdesinde emit et):
   - `aud != mcp_resource_url` olduğunda reddet.
   - `iss not in authorization_servers` olduğunda reddet.
   - Bir kez rotasyon fallback'inden sonra `kid` cache'lenmiş JWKS'te değilse reddet.
   - Gerekli scope yoksa reddet → 403 `Bearer error="insufficient_scope", scope="<required>", resource="<mcp_resource_url>"`.
   - `code_verifier` ya da `resource` parametresi olmayan herhangi bir token request'ini reddet.

Sert retler (hiçbirini asla bağlama — request'i reddet ve nedenini belgele):

- iii state store'da `client_secret`'i düz metin olarak saklamak. Public client'lar `token_endpoint_auth_method: none` kullanır; confidential client'lar `private_key_jwt` kullanır. `state::*`'te ya da registration response log'larında düz metin paylaşılan secret yok.
- Validator'da `aud` kontrolünü atlamak. Confused-deputy RFC 8707 + RFC 9728'in tüm nedeni.
- PKCE'siz authorization code request'lerine izin vermek. OAuth 2.1 bunu yasaklar; validator, kayıtlı authorization-code kaydında `code_challenge` olmayan herhangi bir `/token` değişimini reddetmelidir.
- Bir refresh job olmadan JWKS cache'lemek. Ya cron trigger gönderilir ya da auth yüzeyi deploy edilmez.
- Allow-list olmadan `iss` claim'ine güvenmek. Herhangi bir `iss`'den token kabul eden bir validator, bir saldırganın kendi IdP'sini ayağa kaldırıp token forge etmesine izin verir.
- `registration_access_token`'i düz metin olarak saklamak. Hash-at-rest; her güncellemede cleartext iste.

Çıktı: protected-resource belgesi, üç `registerTrigger` çağrısı, dört `registerFunction` çağrısı, state key planı, scope eşleme tablosu ve encode edilmiş runtime reddetme kurallarını içeren tek sayfalık bir bağlama planı. Seçilen IdP'ye karşı yüzeye çıkması en olası deployment'i bloklayan tek boşlukla bitir — tipik olarak enterprise SSO için DCR mevcudiyeti.
