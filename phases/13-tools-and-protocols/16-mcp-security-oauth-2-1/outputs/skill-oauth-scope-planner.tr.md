---
name: oauth-scope-planner
description: Uzak bir MCP server için OAuth 2.1 scope setini, pinning kurallarını ve step-up policy'sini tasarla.
version: 1.0.0
phase: 13
lesson: 16
tags: [oauth, pkce, resource-indicators, step-up, sep-835]
---

Tool listesine sahip uzak bir MCP server verildiğinde, yetkilendirme modelini tasarla.

Şunları üret:

1. Scope hiyerarşisi. Kademeli scope seti (örneğin `read` -> `write` -> `delete` -> `admin`). Operasyon sınıfı başına bir scope; scope setini patlatma.
2. Scope-to-tool eşlemesi. Her tool gerekli scope'uyla annote edilmiş. Birden fazla scope gerektiren herhangi bir tool'u işaretle.
3. Step-up policy. Hangi operasyonların ilk consent yerine step-up gerektirdiği. Tipik: destructive operasyonlar step-up gerektirir.
4. Resource indicator değeri. `resource` parametresinde kullanılan canonical URL. URL'nin `.well-known/oauth-protected-resource` resource alanıyla eşleştiğinden emin ol.
5. Protected-resource metadata. `authorization_servers`, `scopes_supported` ve `resource` ile `.well-known/oauth-protected-resource` JSON taslağı.

Sert retler:
- Admin scope gerektiren ancak açık bir onay diyaloğu olmadan invoke edilen herhangi bir tool. Step-up gerektirir.
- Birden fazla operasyon sınıfını kapsayan herhangi bir scope. Privilege creep.
- Audience doğrulamasını atlayan herhangi bir server. Confused-deputy zafiyeti.

Reddetme kuralları:
- Server yerelse (stdio), OAuth'u reddet ve stdio'nun parent trust'ı miras aldığını belirt.
- Server legacy OAuth 2.0 implicit flow'una bağımlıysa reddet ve 2.1 + PKCE'ye geçişi zorunlu kıl.
- Kullanıcı şifresiz "sadece API key" auth isterse, uzak server'lar için reddet; kullanıcı yetkilendirmeli erişim için resource indicator'lı OAuth 2.1 authorization code + PKCE iste. Client credentials yalnızca kullanıcı delegasyonu olmayan makineler arası senaryolar için uygundur.

Çıktı: scope hiyerarşisi, scope-to-tool eşlemesi, step-up policy, resource indicator ve protected-resource metadata JSON'u içeren tek sayfalık bir yetkilendirme planı. Kullanıcıları ilk karşılaşmada şaşırtması en olası step-up operasyonuyla bitir.
