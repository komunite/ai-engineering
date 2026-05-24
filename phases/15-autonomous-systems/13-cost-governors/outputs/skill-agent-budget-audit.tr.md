---
name: agent-budget-audit
description: Bir agent deployment'ının cost-governor stack'ini denetle ve unattended run'ları etkinleştirmeden önce eksik katmanları işaretle.
version: 1.0.0
phase: 15
lesson: 13
tags: [cost-governors, denial-of-wallet, budgets, claude-code-sdk, agent-governance]
---

Önerilen bir agent deployment'ı verildiğinde, cost-governor stack'ini on iki katmanlı referansa karşı denetle ve hangi katmanların eksik, az-ayarlanmış veya aşırı-ayarlanmış olduğunu işaretle.

Üret:

1. **Katman envanteri.** On iki referans katmanın her biri için (request başına sınır, task başına token bütçesi, task başına dolar bütçesi, tool başına sınır, iterasyon sınırı, dakika/saat/gün/ay başına rolling sınırlar, velocity limit, tiered routing, prompt caching, context windowing, HITL checkpoint'leri, kill switch), yapılandırılıp yapılandırılmadığını ve hangi değerde olduğunu belirt.
2. **Failure-mode haritalaması.** Her zaman-ölçeği failure'ı için (runaway loop, slow leak, bad release, legitimate surge), onu yakalayan spesifik katmanı ve ne kadar hızlı olduğunu adlandır.
3. **Tool-özel sınırlar.** Agent'ın çağırabileceği her tool'u listele. Her biri için, session başına sınır ve bir sebep adlandır. Açık sınırı olmayan herhangi bir tool açık bir loop'tur.
4. **Alert eşikleri.** Sınırlardan ayrı: hangi spend rate'inde bir insan page'leniyor? Gözlenen e-ticaret durumu ($1,200 → $4,800) bir haftalık büyüme problemiydi, aylık sınır problemi değildi.
5. **Kill-switch yolu.** Bir sınır tetiklendiğinde ne olur? Clean abort, rollback, alert, yeniden etkinleştirme prosedürü. Kill switch'in agent'a harici olduğunu doğrula (agent kendi sınırını düzenleyemez).

Sert reddetmeler:
- Task başına dolar bütçesi olmayan herhangi bir otonom deployment.
- Velocity limit olmayan herhangi bir unattended uzun-horizon run.
- Yeni (<30 gün) bir tool eklemesinde tool başına sınırı olmayan tool yüzeyleri.
- Agent'ın kendisinin değiştirebileceği kill switch'ler.
- Tek sınır olarak aylık sınır (diğer her zaman ölçeği korumasız).

Reddetme kuralları:
- Kullanıcı bugünkü model fiyatlarında en-kötü-durum run'ını fiyatlayamazsa, reddet ve maliyetli bir tahmin iste.
- Önerilen bütçe kuruluşun tek bir hata için kabul edilebilir kaybını aşıyorsa, reddet ve daha düşük sınır iste.
- Kullanıcı Auto Mode classifier'ını (Lesson 10) bütçelerin yerine geçen bir şey olarak ele alıyorsa, reddet. Classifier maliyete ortogonal; her iki katman da gerekli.

Çıktı formatı:

Şunları içeren bir cost-governor denetimi döndür:
- **Katman tablosu** (katman adı, yapılandırılmış y/n, değer)
- **Failure-mode kapsaması** (4 satır: loop / leak / release / surge)
- **Tool başına sınırlar** (tool, sınır, sebep)
- **Alert eşikleri** (oran, sahip, kanal)
- **Kill-switch yolu** (tetikleyici, eylem, yeniden etkinleştirme prosedürü)
- **Hazırlık** (production / staging / yalnızca araştırma)
