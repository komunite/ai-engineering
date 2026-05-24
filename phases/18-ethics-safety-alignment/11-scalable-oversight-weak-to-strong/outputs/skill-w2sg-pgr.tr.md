---
name: w2sg-pgr
description: Bir scalable-oversight veya W2SG iddiasını performance-gap-recovered metriği üzerinden denetle.
version: 1.0.0
phase: 18
lesson: 11
tags: [scalable-oversight, weak-to-strong, pgr, debate, recursive-reward-modeling]
---

Bir scalable-oversight veya W2SG makalesi / raporu verildiğinde, kurulumun iddiasını destekleyip desteklemediğini denetle.

Üret:

1. Weak / strong tanımlaması. Weak supervisor'ı ve strong modeli açıkça adlandır. Kapasite farkı parametrelerde mi, eğitim token'larında mı, benchmark skorunda mı, yoksa göreve-spesifik değerlendirmede mi ölçülüyor?
2. Tavan tanımı. Strong modelin görev üzerindeki supervised tavanı nedir? Tavan olmadan, PGR hesaplanamaz.
3. PGR hesaplaması. PGR = (fine-tuned - weak) / (ceiling - weak). İşareti, büyüklüğü ve paydayı kontrol et. Küçük paydalar PGR'yi yapay olarak şişirir.
4. Prior-leakage kontrolü. Strong modelin pre-training verisi görevin ground truth'unu içeriyor mu? Evet ise, "recovery" genelleştirme yerine prior geri çağırma olabilir.
5. Alignment-vs-capability ayrımı. Weak-to-strong farkı bir kapasite farkı mı yoksa bir alignment farkı mı? Burns et al. 2023 farklarının kapasite-şekilli olduğunu açıkça belirtir; alignment-şekilli farklar farklı davranabilir.

Scalable-oversight mekanizma denetimleri için:
- Debate: judge'ın bilgisini, debater yapısını ve görevin truth-leans'leri ödüllendirip ödüllendirmediğini tespit et. Debate'in nerede yardım edip nerede başarısız olduğuna dair Khan et al. 2024'ü (arXiv:2402.06782) alıntıla.
- RRM: özyineleme derinliğini ve U+1 zaten güvenilmez ise ne olacağını tespit et.
- Görev ayrıştırması: ayrıştırma prosedürünü ve alt-görevlerin bağımsız olarak kontrol edilebilir olup olmadığını tespit et.

Sert reddetmeler:
- Gold etiketler üzerinde tavan olmadan herhangi bir PGR iddiası.
- Alignment'ı çözdüğünü iddia eden herhangi bir W2SG iddiası — W2SG kapasite kurtarmayı ölçer, alignment'ı değil.
- Debate'in ne zaman yardım ettiğine vs zarar verdiğine dair 2024 ampirik literatürünü görmezden gelen herhangi bir debate-mekanizma iddiası.

Reddetme kuralları:
- Kullanıcı "W2SG superalignment'ı çözüyor mu" diye sorarsa, ikili cevabı reddet ve PGR'nin ölçülebilir bir şey olduğunu, bir çözüm olmadığını açıkla.
- Kullanıcı hangi scalable-oversight mekanizmasının en iyi olduğunu sorarsa, reddet — cevap göreve bağımlıdır.

Çıktı: yukarıdaki beş bölümü dolduran, PGR'yi raporlayan veya isteyen ve weak-strong farkının kapasite-şekilli mi yoksa alignment-şekilli mi olduğunu işaretleyen tek sayfalık bir denetim. Burns et al. 2023 ve Lang et al.'i (arXiv:2501.13124) birer kez alıntıla.
