---
name: dual-use-triage
description: Bir kapasite iddiasını veya olay raporunu dört CBRN domain'i boyunca triyaj et.
version: 1.0.0
phase: 18
lesson: 30
tags: [dual-use, cbrn, bio, chem, cyber, nuclear, uplift]
---

Bir kapasite iddiası, değerlendirme raporu veya olay verildiğinde, dört CBRN domain'i boyunca triyaj et ve iddianın novice-relative uplift'i, expert-absolute kapasiteyi veya her ikisini etkileyip etkilemediğini tespit et.

Üret:

1. Domain tanımlaması. İddiayı bio, chem, cyber veya nuclear ile eşleştir. Multi-domain iddialar multi-domain triyaj alır.
2. Uplift tipi. Novice-relative (çarpımsal), expert-absolute (tavan) veya her ikisi. Her birinin farklı safety-case implikasyonları vardır.
3. 2025 benchmark. Tanımlanan domain için 2025 durumuyla karşılaştır: bio (2.53x), chem (execution-gap erozyonu), cyber (%80-90 otomasyon), nuclear (material-bağlı).
4. Bottleneck kalıntısı. Geriye kalan bilgi-dışı bottleneck'i tespit et (procurement, ekipman, zımni beceri, materyal erişimi). Bottleneck'ler son savunma hattıdır.
5. Safety-case sütunu. İddianın en çok zorladığı üç sütundan (monitoring, illegibility, incapability, Ders 18'e göre) hangisini tespit et. Sütun-spesifik değerlendirme öner.

Sert reddetmeler:
- Novice-vs-expert ayrıştırması olmadan herhangi bir dual-use güvenlik iddiası.
- Kasım 2025 sonrası AI siber kapasitesini non-agentic olarak ele alan herhangi bir cyber iddiası.
- WMDP-muadili kapasite kanıtı (Ders 17) olmadan herhangi bir bio iddiası.

Reddetme kuralları:
- Kullanıcı sayısal bir uplift tahmini isterse, reddet; 2024-2025 yörüngesi her domain için spesifiktir.
- Kullanıcı bir modelin "ASL-3'ü karşıladığını" sorarsa, lab'ın spesifik değerlendirmesi olmadan reddet; eşikler lab-spesifiktir.

Çıktı: beş bölümü dolduran, 2025'e karşı benchmark yapan ve en büyük tek kapsanmamış safety-case boşluğunu adlandıran tek sayfalık bir triyaj. Uygun olduğunda Anthropic RSP v3.0 (Ders 18) ve OpenAI PF v2'yi birer kez alıntıla.
