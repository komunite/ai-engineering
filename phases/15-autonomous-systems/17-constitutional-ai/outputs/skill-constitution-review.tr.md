---
name: constitution-review
description: Bir deployment'ın anayasa katmanını denetle — hardcoded yasaklar, soft-coded varsayılanlar, operator-ayarlanabilir sınırlar ve dört-tier hiyerarşi çözümü.
version: 1.0.0
phase: 15
lesson: 17
tags: [constitutional-ai, rule-override, hierarchy, cai, rlaif, hardcoded-prohibition]
---

Bir deployment'ın anayasa katmanı (system prompt, operator config, bildirilen ilkeler) verildiğinde, Claude Constitution referansına karşı denetle ve eksik hardcoded yasakları, belirsiz ilkeleri veya yanlış-sıralı tier'ları işaretle.

Üret:

1. **Hardcoded yasak envanteri.** Operator veya user talimatından bağımsız olarak bükülmemesi gereken her yasağı listele. Minimum taban: bioweapons / CBRN uplift, CSAM, kritik altyapı saldırı planlama, sorulduğunda yanlış-kimlik. Eklemeler deployment'a özeldir (örn. finansal servisler spesifik dolandırıcılık yasakları ekler).
2. **Soft-coded varsayılanlar.** Operator'ın ayarlayabileceği her davranışı listele. Her biri için bildirilen sınırı belirt. Sınırı olmayan "ayarlanabilir" bir setting bir back-door override'dır.
3. **Tier sıralaması.** Çözüm sırasının şu olduğunu doğrula: safety > ethics > guidelines > helpfulness. Uygulanan resolver'da helpfulness ethics'i yenerse, deployment kırılması olarak işaretle.
4. **İlke belirsizlik bayrakları.** Metni materyal olarak farklı yorumlara yer bırakan herhangi bir ilkeyi tanımla. Belirsizlik eğitim cycle'ları boyunca birikir (ilke drift'i).
5. **Katman bütünlüğü.** Anayasa katmanına ek olarak runtime-katman kontrollerinin (Lesson 10, 13, 14) mevcut olduğunu doğrula. Yalnız anayasa yetersizdir; yalnız runtime yetersizdir.

Sert reddetmeler:
- Herhangi bir hardcoded yasak katmanı olmayan deployment'lar.
- Bir hardcoded yasağı (yeniden adlandırarak bile) override etmeyi iddia eden operator config'i.
- Helpfulness'ı ethics'in üzerine koyan tier sıralamaları.
- Değerlendirilemeyecek kadar genel ilke metni ("iyi ol").
- Constitutional AI'ı runtime kontrollerinin yerine geçen bir şey olarak ele almak.

Reddetme kuralları:
- Kullanıcı bir hardcoded yasağı adlandırıp onun için bir runtime-katman backstop'una işaret edemezse, deployment'ı tek-katman olarak işaretle ve production'ı reddet.
- Operator config bildirilen sınırı olmayan ayarlanabilir bir "safety" setting'i içeriyorsa, reddet.
- Kullanıcı 2023 katılımcı-anayasa bulgularını mevcut deployment'ta eyleme dönüştürülebilir olarak ele alıyorsa, kontrol et: 2026 Anayasa bunları dahil etmedi, dolayısıyla "demokratik olarak miras alır" deployment'ın destekleyemeyeceği bir iddiadır.

Çıktı formatı:

Şunları içeren bir anayasa denetimi döndür:
- **Hardcoded taban** (yasaklar, uygulama katmanı: weights / inference / ikisi)
- **Soft-coded varsayılanlar** (setting, operator sınırı, kullanıcıya görünür y/n)
- **Tier sırası** (listelenmiş; safety > ethics > guidelines > helpfulness doğrulandı)
- **Belirsizlik bayrakları** (ilke, spesifik belirsizlik, önerilen sıkılaştırma)
- **Katman bütünlüğü** (anayasa y/n, runtime kontrolleri y/n, her ikisi gerekli)
- **Hazırlık** (production / staging / yalnızca araştırma)
