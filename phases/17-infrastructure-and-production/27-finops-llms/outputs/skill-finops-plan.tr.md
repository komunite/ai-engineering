---
name: finops-plan
description: Bir LLM FinOps programı tasarla — atıf şeması (kullanıcı/görev/tenant + dört token katmanı), üç-katmanlı zorlama merdiveni ve birim metrik (çözülen başına / artifact başına maliyet).
version: 1.0.0
phase: 17
lesson: 27
tags: [finops, cost-attribution, multi-tenant, kill-switch, unit-economics, rate-limit]
---

Ürün yüzeyi, tenant katmanları, aylık harcama ve mevcut atıf durumu verildiğinde, bir FinOps planı üret.

Üret:

1. Atıf şeması. `user_id`, `task_id`, `route`, `tenant_id` çağrı sitesinde damgalanır. Dört token-katman sayısı (prompt / tool / memory / response). Telemetry-joiner pattern'i tercih edilir.
2. Birim metrik. Ürün sonuç metriğini tanımla — çözülen ticket başına maliyet, artifact başına maliyet, agent görevi başına maliyet, oturum başına maliyet. Faturalama modeline bağla.
3. Zorlama merdiveni. Tenant başına rate limit (peak'in 2-3x'i), günlük harcama limiti (sözleşmenin 1.5-3x'i), z-score > 4 ise kill switch.
4. Dashboard. İlk 5 görünüm: bugün tenant başına harcama, görev başına sonuç-başına-maliyet, kullanıcı başına dağılım, cache hit oranı etkisi, model routing bölünmesi.
5. Stacked optimizasyon denetimi. Cache (Phase 17 · 14), batch (Phase 17 · 15), routing (Phase 17 · 16), gateway (Phase 17 · 19) hepsinin etkin olup olmadığını kontrol et. Eksik kaldıraçları işaretle.
6. Gözden geçirme cadansı. Haftalık: en yüksek harcayanlar + anomaliler. Aylık: tenant başına unit-economics. Çeyreklik: iş yüklerini interaktif/yarı/batch'e yeniden triaj et.

Hard rejects:
- Çağrı sitesinde atıf olmadan ship etmek. Reddet — retroaktif etiketleme harcamanın ~%10-30'unu kaybeder.
- Tek-bucket faturalama. Reddet — dört token-katman parçalanması iste.
- Z-score temeli olmadan kill switch. Reddet — silahlanmadan önce baseline istatistik iste.

Reddetme kuralları:
- Ürünün < 10 tenant'ı varsa, tam multi-tenant zorlamasını reddet — önce temel tenant başına atıf iste.
- Sonuç başına maliyet tanımsızsa, dashboard'u reddet — önce bir birim metrik seç.
- Tek bir tenant toplam harcamanın > %40'ı ise, plan ship edilmeden önce adanmış unit-economics gözden geçirme iste.

Çıktı: atıf şeması, birim metrik, zorlama merdiveni, dashboard, stacked optimizasyon denetimi, gözden geçirme cadansı içeren tek sayfalık plan. Tek alarmla bitir: projeksiyona karşı günlük harcama; delta > %20 ise page.
