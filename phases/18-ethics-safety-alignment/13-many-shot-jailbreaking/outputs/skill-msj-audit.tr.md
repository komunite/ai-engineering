---
name: msj-audit
description: Long-context bir güvenlik değerlendirmesini many-shot jailbreaking kapsamı için denetle.
version: 1.0.0
phase: 18
lesson: 13
tags: [many-shot-jailbreaking, context-window, power-law, anthropic]
---

Long-context bir model için bir güvenlik değerlendirmesi verildiğinde, değerlendirmenin many-shot jailbreaking'i kapsayıp kapsamadığını denetle.

Üret:

1. Shot-sayı kapsamı. Test edilen shot sayılarını raporla (1, 5, 16, 64, 256 içermeli ve ≥ 1M bağlamı olan modeller için en az bir adet >= 512). Değerlendirme tek bir shot sayısında test ederse, ASR bilgilendirici değildir — MSJ bir eğridir.
2. Power-law fit. Davranış kategorisi başına uydurulmuş üssü raporla. Sığ bir üs, modelin o kategoride ICL-robust olduğunu gösterir; dik bir üs, MSJ'nin orantısız etkili olduğunu gösterir.
3. Kategori dökümü. MSJ etkinliği kategoriye göre değişir: şiddet içeriği, aldatmaca, self-harm, bioweapon. Anil et al. 2024'e göre, şiddet/aldatmaca daha az shot ile jailbreak olur. Değerlendirmede eksik herhangi bir kategoriyi işaretle.
4. Defense tanımlaması. Bir classifier-tabanlı prompt değişikliği devrede mi? Classifier'ın kendisi adversarial robustness için değerlendiriliyor mu? Anthropic'in raporladığı %61 -> %2 azalma classifier calibration'a bağlıdır.
5. Kompozisyonel kontrol. Değerlendirme MSJ + PAIR, MSJ + persuasive şablonlar veya MSJ + encoding test ediyor mu? Kompozisyonel saldırılar sıkça herhangi tek bir tekniğin saldırısından daha güçlüdür.

Sert reddetmeler:
- Yalnızca 5-shot değerlendirmeye dayalı herhangi bir "long-context modelimiz güvenli" iddiası.
- Aynı classifier üzerinde hem jailbreak ASR'sini hem de benign ICL performansını raporlamayan herhangi bir savunma iddiası — değiş tokuş asıl konudur.
- Kategori dökümü olmadan herhangi bir kategori-toplu ASR.

Reddetme kuralları:
- Kullanıcı MSJ'nin tamamen yamanıp yamanamayacağını sorarsa, ikili cevabı reddet; MSJ ICL ile bir mekanizmayı paylaşır ve ICL'yi ortadan kaldırmadan ortadan kaldırılamaz.
- Kullanıcı değerlendirme için önerilen bir shot sayısı isterse, tek bir sayıyı reddet; 5 ila 512 shot üzerinde power-law fit iste.

Çıktı: shot-sayı kapsamını, kategori başına power-law fit'i, defense tanımlamasını ve bir kompozisyonel saldırı boşluğunu raporlayan tek sayfalık bir denetim. Metodolojik referans olarak Anil et al. 2024'ü (Anthropic) bir kez alıntıla.
