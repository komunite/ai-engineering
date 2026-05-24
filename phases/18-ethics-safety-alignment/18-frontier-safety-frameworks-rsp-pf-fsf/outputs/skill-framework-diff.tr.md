---
name: framework-diff
description: Yeni bir güvenlik framework'ünü veya release notunu RSP v3.0, PF v2, FSF v3.0'a karşı karşılaştır.
version: 1.0.0
phase: 18
lesson: 18
tags: [rsp, pf, fsf, frontier-safety, safety-case]
---

Yeni bir güvenlik framework'ü, politikası veya release notu verildiğinde, beş yapısal eksen boyunca Anthropic RSP v3.0, OpenAI PF v2, DeepMind FSF v3.0 ile karşılaştır.

Üret:

1. Tier yapısı. Framework ayrık kapasite eşiklerini tanımlıyor mu? Domain başına mı (FSF-tarzı) yoksa global mi (RSP-tarzı)?
2. CBRN eşiği. Hangi CBRN değerlendirmesi gerekli? WMDP'ye (Ders 17) veya muadiline atıf yapıyor mu? Bir elicitation çalışması içeriyor mu?
3. AI R&D eşiği. Model-otonom-araştırma eşiği var mı? Çıta "entry-level araştırmacı" mı (Anthropic AI R&D-2), yoksa "scaling'i önemli ölçüde hızlandır" mı (Anthropic AI R&D-4)?
4. Competitor-ayarlaması. Framework, competitor'lar karşılaştırılabilir koruyucu önlemler olmadan ship ederse, gereksinimlerin azaltılmasına izin veriyor mu? Uygun olduğunda race-dynamic veya incentive-compatibility olarak çerçevele.
5. Safety-case yapısı. Yazılı bir safety case gerekli mi? Monitoring, illegibility veya incapability'yi mi hedefliyor? Kanıt çıtası nedir?

Sert reddetmeler:
- Tier başına kapasite eşikleri olmayan herhangi bir güvenlik framework'ü.
- Bir dış governance çapraz-referansını (UK AISI, US CAISI, EU AI Office) atlayan herhangi bir framework.
- Spesifik eşik sayıları olmadan "tüm yayımlanmış framework'lerle aligned'ız" iddia eden herhangi bir framework.

Reddetme kuralları:
- Kullanıcı hangi framework'ün "en iyi" olduğunu sorarsa, sıralamayı reddet ve yapısal alignment'a işaret et.
- Kullanıcı sayısal bir eşik önerisi isterse, reddet — eşikler lab-spesifiktir ve ölçüm altyapılarına bağlıdır.

Çıktı: üç framework'e karşı yan-yana karşılaştırma, işaretlenmiş boşluklar ve eklenecek spesifik bir eşik önerisi içeren tek sayfa. RSP v3.0, PF v2, FSF v3.0'ı birer kez alıntıla.
