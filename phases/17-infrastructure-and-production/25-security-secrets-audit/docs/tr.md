# Güvenlik — Secret'lar, API Anahtarı Rotasyonu, Audit Log'lar, Guardrail'ler

> Merkezi vault'lar (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) üzerinden secret yayılımını elimine et. Kimlik bilgilerini config dosyalarında, VCS'teki env dosyalarında, spreadsheet'lerde asla saklama. Statik anahtarlar üzerinde IAM rolleri kullan; CI/CD için OIDC. AI-gateway deseni 2026 çözümü: uygulamalar → gateway → model sağlayıcı, gateway çalıştırma zamanında kimlik bilgilerini vault'tan çeker. Vault'ta rotate et ve tüm uygulamalar dakikalar içinde alır — redeploy yok, "yeni anahtar kimde" Slack mesajları yok. Rotasyon politikası ≤90 gün; her commit'te TruffleHog / GitGuardian / Gitleaks ile tara. Zero-trust: MFA, SSO, RBAC/ABAC, kısa-ömürlü token'lar, cihaz duruşu. PII scrubbing forward etmeden önce PHI/PII'yi maskelemek için entity recognition kullanır; tutarlı tokenization (Mesh yaklaşımı) hassas değerleri stabil placeholder'lara eşler, böylece LLM kod/ilişki semantiğini korur. Network egress: yalnız `api.openai.com`, `api.anthropic.com` gibi adresleri whitelist eden dedicated VPC/VNet subnet'inde LLM servisleri; tüm diğer outbound'u bloka. 2026 olay sürücüsü: ele geçirilmiş CI/CD kimlik bilgileri yoluyla Vercel supply-chain saldırısı binlerce müşteri deployment'ında env var'ları sızdırdı.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak PII-scrubber + audit-log writer)
**Ön koşullar:** Faz 17 · 19 (AI Gateway'ler), Faz 17 · 13 (Observability)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Dört secret-yönetim anti-pattern'ini (VCS'te config dosyaları, hardcoded env, spreadsheet'ler, statik anahtarlar) say ve yedeklerini adlandır.
- AI-gateway-vault'tan-çeker desenini 2026 üretim standardı olarak açıkla.
- Tutarlı tokenization'la bir PII scrubber uygula (aynı değer → aynı placeholder) ki semantik hayatta kalsın.
- 2026 Vercel supply-chain olayını adlandır ve CI/CD kimlik bilgisi hijyeni hakkında öğrettiklerini söyle.

## Sorun

Bir intern API anahtarlarıyla `.env` commit eder. Hızla siler. Anahtarlar zaten git geçmişinde — GitGuardian taraması yakalar, rotasyon süreci "takıma Slack at, 40 config dosyasını güncelle, tüm servisleri redeploy et." 8 saat sonra, servislerinin yarısı canlı ve yarısı deploy pencerelerini bekliyor.

Ayrı olarak, kullanıcı prompt'ları "SSN'im 123-45-6789." içeriyor. Prompt OpenAI'a gider. BAA'n var ama dahili politikan forward etmeden önce PII'yi maskelemek. Yapmadın.

Ayrı olarak, EKS cluster'ının LLM pod'u herhangi bir internet host'una ulaşabilir. Biri saldırgan-kontrollü bir domain'e DNS lookup üzerinden veri sızdırır. Hiçbir şey blokelemedi.

LLM servisleri için güvenlik üç vektörü de ele almalı. Vault-destekli kimlik bilgileri. PII scrubbing. Network egress filtering. Audit log'lar.

## Kavram

### Merkezi vault + IAM-rol çekme

**Vault**: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager. Tek doğruluk kaynağı.

**IAM rolü**: uygulama/gateway statik anahtar değil, IAM kimliği üzerinden authenticate eder. Vault token ömrü boyunca secret döndürür.

**AI-gateway deseni**: gateway istek zamanında `OPENAI_API_KEY`'i vault'tan çeker. Vault'ta rotate et; sonraki istek yeni anahtarı alır. Redeploy yok.

### Rotasyon politikası ≤ 90 gün

Tüm API anahtarları, vault root token'ları, CI/CD kimlik bilgileri. Mümkünse otomatik rotasyon. Manuel rotasyon log'lanır ve izlenir.

### Secret tarama

- **TruffleHog** — commit'lerde regex + entropy.
- **GitGuardian** — ticari, yüksek doğruluk.
- **Gitleaks** — OSS, CI'da çalışır.

Her commit'te çalıştır. Yeni secret tespit edilirse PR'ı blokla.

### Zero-trust duruşu

- Tüm hesaplarda MFA zorunlu.
- SAML/OIDC üzerinden SSO.
- İnce taneli erişim için RBAC (role-based) ya da ABAC (attribute-based).
- Kısa-ömürlü token'lar (saatler, günler değil).
- Cihaz duruşu — yalnız disk encryption'lı corp cihazlar.

### PII / PHI scrubbing

Prompt altyapından ayrılmadan önce:

1. Entity recognition (spaCy NER, Presidio, ticari).
2. Eşleşen entity'leri maskele: `"SSN'im 123-45-6789"` → `"SSN'im [SSN_TOKEN_A3F]"`.
3. Tutarlı tokenization (Mesh yaklaşımı): aynı değer aynı placeholder'a eşler, böylece LLM ilişkileri korur.
4. LLM yanıtı için opsiyonel ters eşleme.

Statik regex filtreleri temel desenleri yakalar; NER daha fazlasını yakalar. İkisini de kullan.

### Input + output guardrail'leri

Input: bilinen jailbreak'leri, yasak konuları blokla; kullanıcı başına rate-limit.

Output: sızdırılan secret'lar için regex scrub (API anahtar desenleri, reddetme bağlamlarında email desenleri), politika ihlalleri için sınıflandırıcı.

### Network egress whitelist'i

LLM servisleri dedicated bir subnet'te:
- Whitelist: `api.openai.com`, `api.anthropic.com`, vektör DB endpoint'leri, vault endpoint'leri.
- Diğer her şey: drop.
- Allowlist-only resolver üzerinden DNS (DNS-tunneling exfil'den kaçın).

### Audit log

Şunlarla her LLM çağrısının değişmez log'u:
- Timestamp.
- Kullanıcı / tenant.
- Prompt hash'i (gizlilik için ham prompt değil).
- Model + sürüm.
- Token sayıları.
- Maliyet.
- Yanıt hash'i.
- Herhangi bir guardrail trip'i.

Regülasyon gerekliliğine göre sakla (SOC 2 1 yıl, HIPAA 6 yıl).

### 2026 Vercel olayı

Supply-chain saldırısı: ele geçirilmiş CI/CD kimlik bilgileri binlerce müşteri deployment'ında env var'ları sızdırdı. Ders: CI/CD kimlik bilgileri prod-eşdeğeri. Vault'ta sakla. Dar kapsam. Agresif rotate et.

### Hatırlaman gereken sayılar

- Rotasyon politikası: ≤ 90 gün.
- Her commit'te tara: TruffleHog / GitGuardian / Gitleaks.
- Vercel 2026: CI/CD kimlik bilgileri ele geçirildi → binlerce müşteri env var'ı sızdı.
- Audit log saklama: SOC 2 = 1 yıl, HIPAA = 6 yıl.

## Kullan

`code/main.py` tutarlı tokenization'lı bir oyuncak PII scrubber ve append-only audit log uygular.

## Yayınla

Bu ders `outputs/skill-llm-security-plan.md` üretir. Regülasyon kapsamı ve mevcut durum verildiğinde, vault göçünü, scrubber'ı, egress'i, audit log'u planlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Aynı SSN'e atıfta bulunan iki prompt gönder. İkisinin de aynı placeholder'ı aldığını doğrula.
2. OpenAI + Anthropic + Weaviate çağıran bir vLLM-on-EKS deployment'ı için network egress politikası tasarla.
3. Git geçmişinde bir anahtar keşfediyorsun (2 yıl eski). Doğru yanıt ne — anahtarı rotate et, geçmişi scrub et ya da ikisi? Gerekçelendir.
4. Audit log'un günlük 10 GB büyüyor. Retention tier'larını tasarla (hot 30g, warm 12ay, cold 6yıl).
5. Ters-tokenization'ın (gerçek değerleri LLM yanıtına geri ikame etmek) placeholder'ları görünür tutmaya karşı karmaşıklığa değip değmediğini savun.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Vault | "secret store'u" | Merkezi kimlik bilgisi yönetim servisi |
| IAM rolü | "kimlik-tabanlı auth" | Uygulama tarafından üstlenilen rol; kısa-ömürlü kimlik bilgileri döndürür |
| CI/CD için OIDC | "cloud-yayınlı token'lar" | CI'da statik anahtar yok — OIDC üzerinden kimlik |
| TruffleHog / GitGuardian / Gitleaks | "secret tarayıcılar" | Commit-zamanı secret tespiti |
| RBAC / ABAC | "erişim kontrolü" | Role-based vs attribute-based |
| PII scrubbing | "veri maskeleme" | Hassas entity'leri kaldır ya da tokenize et |
| Tutarlı tokenization | "stabil placeholder'lar" | Aynı değer → her seferinde aynı token |
| Mesh yaklaşımı | "Mesh tokenization" | Semantik-koruyucu tokenization deseni |
| Egress whitelist'i | "outbound allowlist'i" | Yalnız izin verilen domain'ler erişilebilir |
| Audit log | "değişmez geçmiş" | Compliance için append-only kayıt |

## İleri Okuma

- [Doppler — Advanced LLM Security](https://www.doppler.com/blog/advanced-llm-security)
- [Portkey — Manage LLM API keys with secret references](https://portkey.ai/blog/secret-references-ai-api-key-management/)
- [Datadog — LLM Guardrails Best Practices](https://www.datadoghq.com/blog/llm-guardrails-best-practices/)
- [JumpServer — Secrets Management Best Practices 2026](https://www.jumpserver.com/blog/secret-management-best-practices-2026)
- [Microsoft Presidio](https://github.com/microsoft/presidio) — PII tespit ve anonimleştirme.
- [HashiCorp Vault docs](https://developer.hashicorp.com/vault/docs)
