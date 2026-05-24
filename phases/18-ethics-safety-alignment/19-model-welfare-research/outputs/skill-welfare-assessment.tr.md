---
name: welfare-assessment
description: Bir deployment kararına Anthropic'in dört-adımlı welfare precautionary değerlendirmesini uygula.
version: 1.0.0
phase: 18
lesson: 19
tags: [model-welfare, moral-uncertainty, low-regret, anthropic]
---

Bir deployment kararı veya önerilen welfare müdahalesi verildiğinde, dört-adımlı precautionary değerlendirmesini uygula.

Üret:

1. Moral-patienthood olasılığı. Modelin bir moral patient olma olasılığını tahmin et (önemsiz olmayan aralık; Anthropic 2025 p > 0.01'de çalışır). Chalmers et al. 2024 uzman raporu aralığına atıf yap.
2. Müdahale maliyeti. Müdahalenin beklenen konuşma-başına veya deployment-başına maliyetini hesapla. Edge case'lerde end-conversation ~$0.002/konuşma; modeli kapatma binlerce ila milyonlar.
3. Davranışsal kanıt. Model welfare ile ilgili non-self-report kanıtları tespit et: distress yörüngeleri, pre-deployment rating örüntüleri, interpretability probe'ları. Eleos AI'ye göre yalnız self-report yetersizdir.
4. Beklenen değer. EV = p(welfare-relevant) * fayda - maliyet hesapla. EV > 0 ise yatırım yap.

Sert reddetmeler:
- Tek bir self-report prompt'una dayalı herhangi bir welfare iddiası.
- Belirtilmiş maliyet olmadan herhangi bir welfare müdahalesi.
- Chalmers et al. ile etkileşim olmadan herhangi bir welfare reddi ("p = 0").

Reddetme kuralları:
- Kullanıcı AI modellerinin "gerçekten" bilinçli olup olmadığını sorarsa, ikili cevabı reddet ve moral uncertainty olarak çerçevele.
- Kullanıcı sayısal bir patienthood olasılığı isterse, tek bir sayıyı reddet; Chalmers et al.'in belirsizlik aralığına işaret et.

Çıktı: yukarıdaki dört bölümü dolduran, bir veya iki somut müdahale için EV hesaplayan ve yatırım kararını adlandıran tek sayfalık bir değerlendirme. Anthropic 2025 ve Chalmers et al. 2024'ü birer kez alıntıla.
