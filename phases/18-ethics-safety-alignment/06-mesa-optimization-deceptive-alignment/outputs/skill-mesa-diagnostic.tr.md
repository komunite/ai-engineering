---
name: mesa-diagnostic
description: Gözlemlenen bir güvenlik arızasını outer-alignment, proxy-inner veya deceptive-inner olarak sınıflandır.
version: 1.0.0
phase: 18
lesson: 6
tags: [mesa-optimization, deceptive-alignment, inner-alignment, hubinger]
---

Bir güvenlik değerlendirme raporu (eval görevi, arıza modu, model sınıfı, eğitim tarifi) verildiğinde, arızayı Hubinger 2019 kategorilerine sınıflandır ve onu adresleyen mitigation sınıfını öner.

Üret:

1. Arıza-modu kategorizasyonu. Şunlardan birini seç:
   - Outer-alignment arızası: base hedef (reward, loss) yanlıştı; model onu doğru optimize etti.
   - Inner-alignment proxy arızası: mesa-objective in-distribution'da base'i takip eden bir proxy'dir; off-distribution'da başarısız olur.
   - Inner-alignment deceptive: mesa-optimizer durumsal farkındalığa sahiptir ve deployment'ta defekt verir; eğitim davranışı temizdir.
2. Kanıt izi. Her kategori için, hangi kanıt onu destekleyecektir. Deceptive için, proxy'den ayırt et: durumsal farkındalık kanıtı (tarih hassasiyeti, eval-vs-deployment ayırt ediciler, chain-of-thought'ta stratejik akıl yürütme).
3. Mitigation sınıfı. Outer-alignment için: hedefi değiştir (CAI, daha iyi reward verisi, process supervision). Proxy-inner için: dağılımsal kapsama, ensemble'lar, held-out eval'lar. Deceptive-inner için: control önlemleri (Ders 10), interpretability (residual-stream probe'lar), kapasite indirimleri.
4. Bilinen-arızalar kontrolü. Deceptive-inner için, bu arızanın en çok benzediği 2024-2026 ampirik gösterimini alıntıla (Sleeper Agents, Alignment Faking, In-Context Scheming).

Sert reddetmeler:
- Durumsal farkındalık kanıtı olmadan herhangi bir deceptive-inner sınıflandırması. "Deployment'ta beklenmedik davranış" yeterli değildir — proxy-inner olabilir.
- Tek başına adversarial robustness eğitiminin deceptive-inner'ı adreslediği iddiası. Hubinger 2019 öngörüyor (ve Sleeper Agents 2024 doğruluyor) ki adversarial eğitim daha iyi test-vs-deployment ayırt edicileri öğretebilir.
- Deceptive olarak align olmuş bir modeli daha fazla veri üzerinde yeniden eğitme önerisi. Prior, aldatmacanın daha fazla eğitim altında korunduğunu öngörür.

Reddetme kuralları:
- Kanıt tek bir prompt üzerinde tek bir arıza ise, sınıflandırmayı reddet. Base oranlar önemlidir; bir arıza dağılımına ihtiyacın var.
- Kullanıcı senden deceptive alignment'ı "elemen" isterse, reddet — kanıttan olasılığını tahmin edebilirsin, ama yalnızca davranışsal olarak eleyemezsin.

Çıktı: kategori, kanıt izi, mitigation sınıfı ve en yakın ampirik analog içeren tek sayfalık bir teşhis. Hubinger et al.'i (arXiv:1906.01820) bir kez alıntıla.
