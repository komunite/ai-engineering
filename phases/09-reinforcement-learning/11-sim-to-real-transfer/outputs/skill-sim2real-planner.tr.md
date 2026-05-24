---
name: sim2real-planner
description: DR, SI ve güvenliği kapsayan, belirli bir robot + görev için sim-to-real transfer pipeline'ı planla.
version: 1.0.0
phase: 9
lesson: 11
tags: [rl, sim2real, robotics, domain-randomization]
---

Bir robot platformu, bir görev ve gerçek donanım zamanına erişim verildiğinde şu çıktıyı üret:

1. Reality gap envanteri. Beklenen etkiye göre sıralanmış şüpheli kaynaklar (kontak, algılama, actuation gecikmesi, görü).
2. DR parametreleri. Tam liste, aralıklar, dağılım. Her aralığı gerçek ölçümlere karşı gerekçelendir.
3. SI adımları. Hangi parametreleri ölçeceksin; ölçüm yöntemi.
4. Teacher/student ayrımı. Teacher'ın hangi privileged info'yu kullandığı; student'ın hangi gözlemi kullandığı.
5. Güvenlik zarfı. Düşük seviye limitler, acil durdurma, yedek controller.

(a) Sıfır-shot sim-variant testi, (b) güvenlik kalkanı, (c) rollback planı olmadan deploy etme. Ölçülen gerçek değişkenliğin 3 katından geniş herhangi bir DR aralığını muhtemelen aşırı rasgeleleştirilmiş olarak işaretle.
