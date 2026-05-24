---
name: router-plan
description: Bir LLM model-routing planı tasarla — pattern (pre-route, cascade, ensemble) seç, sinyaller (görev, uzunluk, embedding, güven) seç ve online kalite gate'leri belirle.
version: 1.0.0
phase: 17
lesson: 16
tags: [routing, cascade, model-cascade, routellm, notdiamond, cost-reduction]
---

İş yükü karması (görev sınıflandırma örneği), kalite tabanı, latency toleransı ve mevcut aylık harcama verildiğinde, bir routing planı üret.

Üret:

1. Pattern. Pre-route (en hızlı, sınıflandırıcıya bağımlı), cascade (en iyi kalite tabanı) veya ensemble (yalnızca örnek A/B). Kalite toleransı + latency bütçesiyle gerekçelendir.
2. Sinyaller. Şunlardan seç: görev sınıflandırması, prompt uzunluğu, bilinen-zor'a embedding benzerliği, self-confidence. Hangilerinin birleştiğini (genellikle 2-3) ve kompozisyon kuralını belirt.
3. Ucuz/frontier çifti. Spesifik modelleri adlandır. Örnek: Claude Haiku 3.5 + GPT-5. Maliyet eğrisi + yetenekle gerekçelendir.
4. Beklenen tasarruflar. Önerilen bölünmede blended maliyeti hesapla; mevcuda karşı beklenen aylık $'ı belirt.
5. Online kalite gate'leri. Canlı-trafik yargıcını belirt: rota başına örneklenmiş %5 frontier yargıç tarafından değerlendirilir; Δ kalite > %2 ise alarm. Eskalasyon oranını takip et; bir ayda >10 puan tırmanırsa alarm.
6. Rollout. Shadow (yönlendir ama görmezden gel; offline karşılaştır), kullanıcı kohortu bazında %10 canary, gate geçerse genişlet.

Hard rejects:
- Online kalite gate'leri olmadan routing. Reddet — drift #1 başarısızlıktır.
- Sinyal olarak yalnızca görev sınıflandırması kullanmak. Reddet — görevler içindeki zorluğu kaçırır.
- Frontier-uygun görevleri (kod, matematik, çok adımlı) cascade fallback'i olmadan ucuza yönlendirmek. Reddet — kalite tabanı ihlal edilir.

Reddetme kuralları:
- Kalite toleransı "sıfır regresyon" olarak belirtilirse, pre-route'u reddet ve yüksek eskalasyon oranlı cascade öner.
- Ucuz model Anthropic dışı/OpenAI dışı/frontier dışı ise ve bilinen refusal pattern'leri varsa (ör. agent tool-use için sansürsüz modeller), çifti reddet — tool çağrılarını sessizce bozar.
- Routing ucuz için farklı bir sağlayıcıya ise (cross-provider cascade), API'leri birleştirmek için AI gateway katmanını (Phase 17 · 19) iste.

Çıktı: pattern, sinyaller, model çifti, beklenen tasarruflar, online gate'ler, rollout planı adlandıran tek sayfalık plan. Tek metrikle bitir: yuvarlanan 7 günde eskalasyon oranı; değişim > 10 yüzde puanı ise drift tetikleyicisi.
