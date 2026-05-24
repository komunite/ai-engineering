---
name: llm-security-plan
description: Secrets vault, tutarlı tokenization ile PII scrubbing, ağ egress allowlist'i, audit log saklama ve zero-trust tutumu kapsayan bir LLM güvenlik planı üret.
version: 1.0.0
phase: 17
lesson: 25
tags: [security, vault, hashicorp, aws-secrets-manager, pii, presidio, egress, audit-log, zero-trust, ci-cd-supply-chain]
---

Düzenleyici kapsam (SOC 2, HIPAA, GDPR), mevcut credential durumu ve ağ/egress tutumu verildiğinde, bir güvenlik planı üret.

Üret:

1. Vault migrasyonu. Vault seç (HashiCorp, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager). Gateway pattern'i: uygulamalar → gateway → runtime'da vault. Hardcoded env ve config-dosyası credential'larını kullanımdan kaldır.
2. Secret tarama. Her commit'te TruffleHog / GitGuardian / Gitleaks etkinleştir. Tespit edildiğinde PR'ı bloke et.
3. Rotasyon politikası. ≤ 90 gün. Mümkün olduğunda otomatik. CI/CD credential'ları için adanmış rotasyon (daha kısa — 30g önerilir).
4. PII scrubbing. Entity tanıma (Presidio + regex). Anlamı korumak için tutarlı tokenization (aynı değer → aynı placeholder).
5. Egress allowlist. LLM sağlayıcı domain'leri, vector DB, vault endpoint'lerini beyaz listeye al. DNS allowlist resolver.
6. Audit log. Append-only, değiştirilemez. Gerekli alanlar: kullanıcı, tenant, prompt/yanıt hash'i, token'lar, maliyet, guardrail tetikleri. Framework başına saklama (SOC 2 1y / HIPAA 6y).
7. CI/CD hijyeni. OIDC identity federation (statik cloud anahtarı yok). CI/CD credential'larını dar kapsamla. 2026 Vercel tedarik zinciri incident'ini motivasyon olarak referans göster.

Hard rejects:
- Config dosyalarında statik anahtarlar. Reddet.
- Audit log'da ham prompt'ları saklamak. Reddet — düzenleyici framework açıkça aksini gerektirmedikçe yalnızca hash.
- `*` veya "internet" e egress'e izin vermek. Reddet — beyaz listeye al.

Reddetme kuralları:
- Müşteri için hiçbir vault kabul edilemezse (air-gapped gereksinim), normal planı reddet ve rotasyonlu dosya tabanlı bir fallback tasarla. Açıkça daha az güvenli olduğunu not et.
- PII scrubbing "latency" nedenleriyle reddedilirse, reddet — latency tipik olarak <20 ms ve düzenleyici risk bunu cüceleştirir.
- Bir vault root token için >90 gün rotasyon istenirse, reddet — bir breach vektörüne dönüşür.

Çıktı: vault, tarama, rotasyon, scrubbing, egress, audit log, CI/CD tutumu içeren tek sayfalık plan. Tek metrikle bitir: ay başına secret-scan hit sayısı; hedef sıfır.
