---
name: bounded-loop-review
description: Önerilen bir sınırlı self-improvement döngüsünü dört-primitif stack'ine (invariant'lar, anchor, çok-amaçlı, regression tespiti) karşı denetle.
version: 1.0.0
phase: 15
lesson: 8
tags: [bounded-self-improvement, invariants, alignment-anchor, rsi-safety]
---

Önerilen bir self-improvement döngüsü verildiğinde, ICLR 2026 RSI Workshop tarafından belirlenen dört sınırlandırma primitif'ine karşı puanla ve somut bir gap analizi üret.

Üret:

1. **Invariant envanteri.** Döngünün uyguladığı her invariant'ı listele. Her biri için (a) neyin kontrol edildiğini, (b) kontrolün nerede çalıştığını (agent erişiminin içinde/dışında), (c) bir ihlalin ne yaptığını (hard reject, pause, log-only) adlandır.
2. **Anchor tanımlama.** Alignment anchor'ını adlandır (amaç ifadesi, anayasa, intent açıklaması). Storage konumunu belirt ve döngünün onu düzenleyemediğini doğrula. Anchor yoksa, eksik olarak işaretle.
3. **Çok-amaçlı eksenler.** Döngünün değerlendirdiği her ekseni listele. Performance'ın yanı sıra safety, fairness ve robustness'ın mevcut olduğunu doğrula. Tek-eksenli bir döngü bu kontrolden geçemez.
4. **Regression politikası.** Tarihsel pencereyi, eksen başına toleransı ve bir düşüş tespit edildiğinde ne olacağını belirt. Regression kontrollerinin yalnızca iç tarih değil, harici bir karşılaştırma seti kullandığını doğrula.
5. **Gap analizi.** Eksik her primitif için, ilk hangi failure sınıfının ortaya çıkacağını öngör. Invariant yok → smuggled capability veya tool drift. Anchor yok → amaç yeniden yorumlanması. Çok-amaçlı yok → performance kazanımını maskeleyen safety regression. Regression yok → sessiz capability kaybı.

Sert reddetmeler:
- Sıfır invariant'lı herhangi bir döngü.
- Edit yüzeyinin dışında alignment anchor'ı olmayan herhangi bir döngü.
- Tek bir skalar skoru optimize eden herhangi bir döngü.
- Regression kontrolü yalnızca kendi tarihinden okuyan herhangi bir döngü (döngü "normal"i tanımlar).

Reddetme kuralları:
- Kullanıcı "henüz bozulmadı"yı safety kanıtı olarak ele alıyorsa, reddet ve herhangi bir compute harcanmadan önce açık gate tasarımı iste.
- Kullanıcı invariant listesini 15 dakikada üretemezse, reddet — döngünün invariant'ı yok.
- Döngü dört primitif olmadan production'da çalıştırılması öneriliyorsa (gerçek kullanıcıları veya altyapıyı etkiliyor), reddet ve önce monitoring ile staging iste.

Çıktı formatı:

Şunları içeren puanlı bir inceleme döndür:
- **Invariant skoru** (0-5, açık listeyle)
- **Anchor skoru** (0-5, storage ve doğrulama yöntemiyle)
- **Çok-amaçlı skoru** (0-5, eksenler listelenmiş)
- **Regression skoru** (0-5, tolerans ve pencereyle)
- **Gap analizi** (öngörülen ilk failure, mitigation planı)
- **Deployment hazırlığı** (production / staging / yalnızca araştırma)
