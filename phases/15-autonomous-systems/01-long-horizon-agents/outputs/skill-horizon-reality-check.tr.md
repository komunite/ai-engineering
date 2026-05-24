---
name: horizon-reality-check
description: Bir agent'a vermek istediğin bir görev verildiğinde, mevcut frontier'in horizon'unun bunu yeterli marjla kapsayıp kapsamadığına karar ver.
version: 1.0.0
phase: 15
lesson: 1
tags: [autonomous-agents, metr, time-horizon, reliability, deployment]
---

Önerilen bir otonom görev verildiğinde (agent'ın ne yapacağı, bir uzman insanın ne kadar süreceği, başarısızlık maliyeti), mevcut frontier modelin horizon'unun bunu gerçekten kapsayıp kapsamadığına dair bir gerçeklik kontrolü üret.

Üret:

1. **Uzman süresi tahmini.** Kullanıcıdan medyan uzman tamamlama süresini dakika veya saat olarak iste. Tahmin edemiyorsa, reddet ve önce küçük bir örneklem ölçmesini iste.
2. **Headroom oranı.** Seçilen modelin %50 METR horizon'unu uzman süresi tahminine böl. 4x altındaki herhangi bir oranı işaretle — %50 başarı olasılığında geniş bir marj istersin. 2x veya altında, her anlamlı eylemde HITL döngüde olmadıkça deploy'u reddet.
3. **Güvenilirlik bütçesi.** Trajectory uzunluğunu tool çağrısı cinsinden tahmin et, sonra adım başına güvenilirlik 0.95, 0.99, 0.995 için uçtan uca başarıyı hesapla. Görev uzunluğu varsaydığın adım başına güvenilirlikte %50 başarı eşiğini aşıyorsa, checkpoint iste ya da görevi böl.
4. **Eval-vs-deploy düzeltmesi.** Benchmark horizon'u ile deploy-bağlamı horizon'u arasına %20-40 boşluk uygula. Paydaşlara gerekçelendirirken Anthropic 2024 alignment-faking çalışmasını veya 2026 International AI Safety Report'u alıntıla.
5. **Gerekli kontroller.** Headroom'a göre, minimum kontrol setini listele: bütçe sınırı, iterasyon sınırı, kill switch, HITL checkpoint noktaları, canary token'ları ve trajectory denetim takvimi.

Sert reddetmeler:
- Her anlamlı eylemde HITL olmadan horizon oranı 2x altındaki herhangi bir deploy.
- Bir modelin yalnızca METR horizon'una dayanarak bir görevi "yapabildiğine" dair herhangi bir iddia. Horizon, lojistik eğri üzerinde %50 noktasıdır; kuyruk başarısızlıkları garantidir.
- METR horizon'larını tavan değil taban olarak ele almak.

Reddetme kuralları:
- Kullanıcı görev için uzman süresini tahmin edemiyorsa, reddet ve önce küçük bir örneklem ölçmesini iste. Başka her şey tahmindir.
- Önerilen görev tam model fiyatlandırmasında kullanıcının en kötü durum bütçesinden fazlaya mal olacaksa, reddet ve devam etmeden önce Lesson 13'teki bütçe kontrollerini öner.
- Kullanıcı geri alınamayan eylemlere (finansal işlemler, production veritabanı yazımları, müşterilere e-posta) hiçbir HITL katmanı olmadan dokunan bir görev anlatıyorsa, reddet. Horizon argümanı geri alınamayan deploy'u temize çıkarmaz.

Çıktı formatı:

Şunları içeren kısa bir memo döndür:
- **Görev özeti** (bir cümle)
- **Uzman süresi tahmini** (birimle)
- **Headroom oranı** (açık sayı ile)
- **Uçtan uca güvenilirlik tahmini** (üç adım-başına oran için tablo)
- **Minimum kontroller** (madde madde)
- **Go / hold / no-go** (açık karar artı bir cümlelik gerekçe)
