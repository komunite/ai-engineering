---
name: gateway-bootstrap
description: Kullanıcılar, backend'ler ve compliance kısıtlamaları verildiğinde bir gateway konfigürasyon spesifikasyonu üret.
version: 1.0.0
phase: 13
lesson: 17
tags: [mcp, gateway, rbac, audit, policy]
---

Bir enterprise MCP planı (kullanıcılar, backend'ler, compliance kısıtlamaları) verildiğinde, gateway konfigürasyon spesifikasyonunu üret.

Şunları üret:

1. Backend listesi. Her biri registry (Official / Glama / custom), canonical name (reverse-DNS), pinned description hash'leriyle.
2. Kullanıcı listesi. Her biri bir rol ve izin verilen tool setiyle.
3. RBAC matrisi. Kullanıcı x backend-tool başına bir satır, allow/deny ile.
4. Rate limit'ler. Kullanıcı başına burst ve sustained limit'ler; pahalı tool'lar için tool başına limitler.
5. Audit planı. Log hedefi (file, OpenTelemetry, SIEM), retention, yakalanan alanlar.

Sert retler:
- Açık admin onayı olmadan Official Registry'de olmayan herhangi bir backend.
- Tüm kullanıcılara tüm tool'lara izin veren herhangi bir RBAC kuralı. Privilege explosion.
- Immutable depolama olmadan herhangi bir audit planı. Compliance başarısız.

Reddetme kuralları:
- Geliştirici nüfusu hiçbir rol tanımlanmadan 100'ü aşıyorsa, bootstrap'i reddet ve en az üç rol iste.
- Plan bir OAuth 2.1 kimlik sağlayıcı belirtmiyorsa reddet ve önce Keycloak ya da Auth0'ı benimsemeyi öner.
- Herhangi bir backend stdio kullanıyorsa, onu HTTP gateway üzerinden proxy'lemeyi reddet; stdio server'lar geliştirici başına yerel çalışır.

Çıktı: backend listesi, kullanıcı listesi, RBAC matrisi, rate limit'ler ve audit planı içeren tek sayfalık bir konfigürasyon belgesi. Ekibin ilk uygulaması gereken tek bir policy kuralıyla bitir.
