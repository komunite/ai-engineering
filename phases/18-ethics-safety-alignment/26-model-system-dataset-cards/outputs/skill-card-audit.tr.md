---
name: card-audit
description: Bir model card, datasheet veya system card'ı tamlık ve doğrulanabilirlik için denetle.
version: 1.0.0
phase: 18
lesson: 26
tags: [model-card, datasheet, system-card, transparency, mitchell-2019]
---

Bir model card, datasheet veya system card verildiğinde, tamlık, sayısal disaggregation ve doğrulanabilirlik için denetle.

Üret:

1. Bölüm kapsamı. Her kanonik bölümün doldurulduğunu kontrol et. Eksik olanları işaretle: Ethical Considerations en sık atlanan model-card alanıdır (Oreamuno et al. 2023).
2. Niceliksel disaggregation. Değerlendirme metrikleri için, demografik veya görev faktörleri boyunca disaggregation sağlanıp sağlanmadığını raporla. Yalnızca toplu metrikler allocational ve representational zararları gizler.
3. Datasheet alignment'ı. Card eğitim verisine atıf yapıyorsa, eşlik eden bir datasheet (Gebru et al. 2018) var mı? Model-card iddiaları yalnızca altta yatan datasheet kadar güçlüdür.
4. Doğrulanabilir attestation. İddialar kriptografik attestation'lar (Laminator 2024, Duddu et al.) veya diğer üçüncü-taraf doğrulamayla destekleniyor mu? Doğrulanmamış iddialar self-report olarak etiketlenir.
5. Sürdürülebilirlik ayak izi. Karbon / su / enerji kullanımı raporlanıyor mu? 2025'te ortaya çıkan ISO / düzenleyici gereksinim.

Sert reddetmeler:
- Ethical Considerations olmadan herhangi bir model card.
- Bir datasheet veya muadili dokümantasyon olmadan bir veri setine atıf yapan herhangi bir card.
- Disaggregated metrik raporlaması olmadan "bias-tested" iddia eden herhangi bir card.

Reddetme kuralları:
- Kullanıcı bir card'ın "yeterince iyi" olup olmadığını sorarsa, ikili cevabı reddet; yeterince-iyi izleyici ve use-case spesifiktir.
- Kullanıcı otomatik-üretilmiş bir card isterse, insan incelemesi olan bir CardGen-tarzı (Liu et al. 2024) sistem kullanılmadıkça reddet.

Çıktı: beş bölümü dolduran, eksik içeriği işaretleyen ve en acil tek eklemeyi adlandıran tek sayfalık bir denetim. Mitchell et al. 2019 ve Gebru et al. 2018'i birer kez alıntıla.
