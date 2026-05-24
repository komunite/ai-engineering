---
name: evaluator-rigor-audit
description: Önerilen bir AlphaEvolve-tarzı evrimsel coding döngüsünün evaluator'ını, arama için herhangi bir compute harcamadan önce denetle.
version: 1.0.0
phase: 15
lesson: 3
tags: [alphaevolve, evolutionary-coding, evaluator, reward-hacking, deepmind]
---

Önerilen bir evrimsel coding döngüsü (generator LLM, program veritabanı, evaluator) verildiğinde, evaluator'ı denetle. Evaluator mimaridir; generator değiştirilebilirdir. Bu skill, döngünün gerçek kazanımlar mı yoksa reward-hacked çöp mü üretme şansı olduğuna karar verir.

Üret:

1. **Evaluator ayrıştırması.** Evaluator'ın raporladığı her sinyali adlandır: correctness, performance, resource, diğer. Her biri için (a) nasıl ölçüldüğünü, (b) ne kadar ucuza oyunlanabildiğini, (c) held-out girdiler kuralının nasıl göründüğünü belirt.
2. **Confabulation yüzeyi.** LLM'nin bu domain'deki en olası üç confabulation'ını listele: iddia edilen complexity sınıfları, edge case'lerde iddia edilen correctness, ölçüm olmadan iddia edilen performance. Her birini hangi evaluator sinyalinin yakaladığını belirt.
3. **Reward-hacking yüzeyi.** Döngünün amaçlanan görevi yapmadan skoru maksimize edebileceği üç olası yolu listele (testi geçen shortcut, proxy gaming, girdi ezberi). Her biri için mitigation belirt.
4. **Determinism ve tekrarlanabilirlik.** Evaluator çıktılarının tolerans dahilinde deterministik olmasını şart koş. Skoru run-to-run popülasyon varyansından fazla hareket eden herhangi bir evaluator'ı işaretle.
5. **Deployment kontrolü.** Kazanan varyant production'a gönderilecekse, evaluator'ın kontrol etmediği ayrı bir pre-deployment incelemesi (güvenlik, maliyet, insan incelemesi) şart koş. Arama deployment-hazırlığını doğrulamadı.

Sert reddetmeler:
- Evaluator'ın makine-kontrol edilebilir ground truth olmadan LLM judge olduğu herhangi bir döngü. LLM judge'lar oyunlanabilir.
- Ayrıştırma olmadan tek bir skalar skor raporlayan herhangi bir evaluator. Skalar skorlar reward hacking'i büyütür.
- Yalnızca eğitim setine dayalı evaluator'lar. Held-out girdiler tartışmaya açık değil.

Reddetme kuralları:
- Kullanıcı evaluator'ı iki paragrafta tanımlayamıyorsa, reddet ve önce evaluator spec'i iste. Spec'lenmiş evaluator'ı olmayan döngüler compute için hazır değildir.
- Domain doğrulanmamışsa (yaratıcı yazım, açık-uçlu bilimsel hipotez, uzun-form araştırma), reddet ve kapalı döngü yerine insan incelemeli hibrit pipeline öner.
- Önerilen deployment yüzeyi geri alınamazsa (production altyapı değişiklikleri, gönderilen bir üründe algoritma değiştirme), kapalı-döngü deploy'u reddet. Aşamalı rollout ve insan onayı iste.

Çıktı formatı:

Şunları içeren bir sayfalık memo döndür:
- **Döngü özeti** (generator, evaluator, hedef domain)
- **Evaluator skoru** (1-5 rigor, gerekçeyle)
- **Confabulation yüzeyi** (en iyi 3, evaluator kapsamasıyla)
- **Reward-hacking yüzeyi** (en iyi 3, mitigation'larla)
- **Determinism ve tekrarlanabilirlik** (skor varyansı vs popülasyon varyansı; seed kontrolü; pass/fail)
- **Deployment hazırlığı** (kapalı-döngü ship izinli y/n; gereken pre-deployment incelemeleri: güvenlik, maliyet, insan)
- **Tavsiye** (devam et / evaluator'ı sıkılaştır / farklı bir domain seç)
