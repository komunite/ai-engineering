---
name: browser-agent-trust-boundary
description: Önerilen bir browser-agent deployment'ının kapsamını belirle — agent gerçek bir siteye dokunmadan önce trust zone'ları, yetkili yazımlar, gereken savunmalar.
version: 1.0.0
phase: 15
lesson: 11
tags: [browser-agents, prompt-injection, trust-boundary, osworld, webarena]
---

Önerilen bir browser-agent workflow'u verildiğinde, her read'i, her write'ı ve ilk run için gereken minimum savunma stack'ini sıralayan bir trust-boundary kapsam dokümanı üret.

Üret:

1. **Read yüzeyi.** Agent'ın fetch edeceği her origin'i listele. Her birini in-trust (kullanıcının kuruluşu tarafından işletilen birinci-taraf siteler) veya out-of-trust (herhangi bir üçüncü-taraf, herhangi bir user-generated content, herhangi bir arama sonucu) olarak sınıflandır. Tüm out-of-trust read'ler potansiyel prompt-injection kanalı olarak ele alınmalıdır.
2. **Write yüzeyi.** Agent'ın gerçekleştirme yetkisi olduğu her sonuçsal eylemi listele (form submit, içerik post'lama, backend tool çağırma, memory'ye yazma). Her biri için, blast radius'u ve eylemin geri alınabilir olup olmadığını belirt.
3. **Gerekli savunmalar.** Minimum stack: content sanitizer, read/write sınırı (content_origin out-of-trust ise write'lar taze onay gerektirir), task başına tool allowlist, scoped credential'larla session izolasyonu, kalıcı memory'de canary token'ları, geri alınamayan eylemlerde HITL.
4. **Benchmark-dağılım fit'i.** Agent BrowseComp, OSWorld veya WebArena-Verified skoru raporluyorsa, benchmark ile gerçek task arasındaki dağılım örtüşmesini adlandır. Yüksek BrowseComp skoru booking-flow güvenilirliğini öngörmez.
5. **Bilinen-saldırı checklist'i.** Deployment'ın şunlara karşı sertleştirildiğini doğrula: (a) görünür-metin injection, (b) URL-fragment / query injection, (c) memory-binding saldırılar (Tainted Memories sınıfı), (d) authenticated session'lara CSRF-şekilli saldırılar, (e) one-click hijack'lar. Her biri için spesifik savunmayı ve nerede çalıştığını adlandır.

Sert reddetmeler:
- Production credential'larına erişimi olan ve session izolasyonu olmayan browser agent'lar.
- Out-of-trust content'ten başlatılan bir write'ın taze HITL onayı gerektirmediği herhangi bir deployment.
- Yalnızca content sanitizer'a güvenen herhangi bir deployment (sanitizer'lar kolay saldırıları yakalar; sofistike payload'lar geçer).
- Canary entry'leri olmayan kalıcı memory.
- Finansal işlemlere veya müşteri verisine dokunan ve write'larda HITL olmayan workflow'lar.

Reddetme kuralları:
- Kullanıcı injection-driven yanlış bir write'ın blast radius'unu adlandıramıyorsa, reddet ve açık bir cümle iste.
- Kullanıcı scoped credential'ların mevcut olmadığı bir stack'te browser agent öneriyorsa, reddet ve önce ayrı bir identity iste.
- Kullanıcı bir benchmark skorunu (BrowseComp, OSWorld, WebArena) agent'ın bir production task'ını "yapabildiğine" dair kanıt olarak gösteriyorsa, reddet ve gerçek dağılımda iç eval'lar iste.

Çıktı formatı:

Şunları içeren bir trust-boundary memo'su döndür:
- **Read yüzey tablosu** (origin, in-trust / out-of-trust)
- **Write yüzey tablosu** (eylem, blast radius, geri alınabilir y/n)
- **Savunma stack'i** (yapılandırılmış katmanların madde madde listesi)
- **Benchmark-fit notu** (geçerliyse)
- **Bilinen-saldırı checklist'i** (beş satır, satır başına adlandırılmış savunma)
- **Deployment kararı** (production / staging / yalnızca araştırma)
