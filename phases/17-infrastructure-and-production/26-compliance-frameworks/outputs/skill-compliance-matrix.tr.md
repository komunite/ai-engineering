---
name: compliance-matrix
description: Müşteri coğrafyası, segment ve sözleşme kapsamı verildiğinde bir LLM SaaS için gerekli-framework matrisi üret. SOC 2, HIPAA, GDPR, PCI-DSS, EU AI Act, Colorado AI Act, ISO 42001 üzerinde kontrolleri haritala.
version: 1.0.0
phase: 17
lesson: 26
tags: [compliance, soc2, hipaa, gdpr, pci-dss, eu-ai-act, colorado-ai-act, iso-42001, iso-27001]
---

Müşteri coğrafyası (ABD / AB / Global veya spesifik ABD eyaletleri), segment (SaaS / sağlık / fintech), sözleşme kapsamı (enterprise vs SMB) ve mevcut uyumluluk durumu verildiğinde, gerekli-framework matrisini üret.

Üret:

1. Gerekli framework'ler. Gerekçeyle (coğrafya, segment, müşteri profili) elde edilmesi gereken her framework'ü listele.
2. Zaman çizelgesi. Her framework için mevcut durumu belirt (yok / Type I / denetimde / Type II). Boşluğu adlandır.
3. Çapraz-framework kontrol haritalama. Her gerekli framework için, birden fazlasını karşılayan kontrolleri belirle (erişim log'u, şifreleme, audit log, değişiklik yönetimi).
4. EU AI Act tutumu. Ürünün risk katmanını sınıflandır (kabul edilemez / yüksek / sınırlı / minimum). Yüksek-risk ise, 2 Ağustos 2026 yürürlük tarihinden önce conformity-assessment yolunu iste.
5. PII / PHI işleme. Gerçek zamanlı çıkarım-katmanı redaksiyonunu doğrula (Phase 17 · 25) — post-processing GDPR-savunulabilir değildir. PHI'ye dokunan tüm AI vendor'lar için BAA'ları doğrula.
6. Denetim tooling'i. Çapraz-framework otomasyonu için Drata / Vanta / Secureframe. Çoklu-framework kapsamında maliyete değer.

Hard rejects:
- Enterprise satın alma için SOC 2 Type I'nin "SOC 2 uyumlu" olduğunu iddia etmek. Reddet — Type II gate'tir.
- BAA olmadan bir sağlayıcıya PHI göndermek. Reddet — HIPAA ihlali.
- GDPR tutumu olarak post-processing PII scrubbing'i. Reddet — gerçek zamanlı iste.

Reddetme kuralları:
- Ürün GDPR Madde 30 kayıtları olmadan AB kullanıcılarına hizmet veriyorsa, kayıtlar kurulana kadar AB müşterilerine ship etmeyi reddet.
- Ürün kredi/istihdam/konut/eğitim/temel hizmetlerde Colorado sakinlerine hizmet veriyorsa, lansmandan önce 30 Haziran 2026'ya kadar tamamlanmış bir impact assessment kanıtı iste (SB25B-004 ile değiştirilen SB24-205 altındaki Colorado AI Act yürürlük tarihi).
- Ürün EU AI Act altında yüksek-riskli ise ve takımın conformity-assessment planı yoksa, adlandırılmış bir uygulama partneri olmadan Ağustos 2026 hazırlığını vaat etmeyi reddet.

Çıktı: gerekli framework'ler, mevcut durum, boşluklar, zaman çizelgesi, çapraz-framework kontrolleri, EU AI Act katmanı, PII tutumu, tooling içeren tek sayfalık matris. 12 aylık yol haritasıyla bitir: framework-bazında çeyreklik kilometre taşları.
