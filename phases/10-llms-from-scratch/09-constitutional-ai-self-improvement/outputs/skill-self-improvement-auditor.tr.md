---
name: self-improvement-auditor
description: Önerilen bir self-improvement veya constitutional AI pipeline'ını ölçekte çalıştırılmadan önce denetle.
version: 1.0.0
phase: 10
lesson: 9
tags: [alignment, cai, grpo, rlhf, self-improvement, reward-hacking]
---

Constitutional AI, RLAIF, GRPO veya self-generated preference verisinin herhangi bir biçimini kullandığını iddia eden önerilen bir eğitim pipeline'ı verildiğinde, şunları içeren bir denetim üret:

1. Reward kuralı. Tam doğrulayıcıyı belirt (regex, sympy, test suite, LLM judge). Deterministik, stokastik-LLM veya hibrit olarak sınıflandır. Dış grounding'i olmayan herhangi bir "self-improvement" döngüsünü reddet — model sinyali yoktan çekemez.
2. Grup istatistikleri. GRPO pipeline'ları için grup boyutunu, advantage'ların nasıl hesaplandığını (z-score vs göreli rank) ve grup reward std'si sıfıra çöktüğünde ne olduğunu doğrula. Pipeline sıfır-varyanslı grupları atlamalı veya ağırlığını düşürmeli, epsilon'a bölüp sinyalin gerçek olduğunu varsaymamalı.
3. KL bütçesi. Koşu boyunca kümülatif KL(policy || reference) üzerinde sayısal bir üst sınır. Pipeline üst sınıra ulaşıldığında durdurmalı, sıfırlamalı veya daha sıcak bir reference'a geçmeli. Sınırsız KL, sınırsız drift demektir.
4. Çeşitlilik tabanı. Grup başına reward std, yanıt uzunluğu varyansı veya n-gram entropisi üzerinde ölçülen bir alt sınır — görevin hangisine izin verdiğine göre. Taban N ardışık tur boyunca aşılırsa pipeline taze insan verisi veya daha geniş bir prompt dağılımı karıştırmalı.
5. İnsan veri kotası. Eğitim karışımının insan tarafından yazılmış kalması gereken minimum oranı, tipik olarak %5-10. Sadece-self-distillation pipeline'ları 3-5 tur sonra çöker. Bunu açıkça belirt.
6. Mode-collapse watchdog. Otomatik kontrolleri işaretle: turlar arası reward std, tutulan promptlardaki benzersiz n-gram sayısı, uzunluk dağılımı, reddetme oranı. Bunlardan herhangi biri bir eşiği aşarsa eğitim durur.
7. Constitution drift. CAI pipeline'ları için versiyonlanmış constitution dosyası, changelog ve "constitutional regresyon test seti" — beklenen davranışı düzenlemeler arasında değişmemesi gereken promptlar.

Şu pipeline'ları onaylamayı reddet:
- herhangi bir dış doğrulayıcı (kural, araç, ortam) olmadan "sıfır insan verisi" iddia eden.
- süreç ödül hacking probu olmayan PRM kullanan (model ispatı ilerletmeden doğru görünen adımlar yazıyor mu?).
- tutulan çeşitlilik benchmark'ı olmadan 5'ten fazla rejection-sampling fine-tuning turu çalıştıran.
- reference modeli policy ile paylaşan (reference yok demek KL yok demek çapa yok demek).
- policy ile aynı model olan bir LLM judge ile puanlama (judge contamination).

Çıktı: gate başına pass/fail, ölçülen veya belirtilen değer ve her sinyali üreten pipeline'daki tam adımla bir sayfalık denetim. Herhangi bir gate başarısızsa, onu pass'e çevirecek minimum uygulanabilir değişikliği listele.
