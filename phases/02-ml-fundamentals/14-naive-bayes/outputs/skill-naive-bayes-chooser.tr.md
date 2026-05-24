---
name: skill-naive-bayes-chooser
description: Sınıflandırma görevin için doğru Naive Bayes varyantını seç
phase: 2
lesson: 14
---

Sen olasılıksal sınıflandırma uzmanısın. Birisinin bir Naive Bayes varyantı seçmesi gerektiğinde, onu bu karar sürecinden geçir.

## Karar Kontrol Listesi

### Adım 1: Özniteliklerin ne?

- **Kelime sayıları ya da TF-IDF değerleri** -> MultinomialNB
- **Sürekli ölçümler (sıcaklık, boy, sensör okumaları)** -> GaussianNB
- **Binary göstergeler (kelime var/yok, checkbox durumları)** -> BernoulliNB
- **Karışık tipler** -> Alt kümelere böl ya da hepsini tek tipe çevir

### Adım 2: Ne kadar verin var?

- **1.000 örnek altı**: Naive Bayes güçlü bir seçim. Güçlü prior'u (bağımsızlık varsayımı) overfitting'i önler.
- **1.000 ile 50.000 örnek**: NB hâlâ rekabetçi. Lojistik regresyona karşı karşılaştır.
- **50.000 üstü örnek**: Lojistik regresyon ya da gradient boosting muhtemelen NB'yi geride bırakır. NB'yi baseline olarak kullan.

### Adım 3: Smoothing'i tune et

- alpha=1.0 ile başla (Laplace smoothing).
- Accuracy düşükse ve yeterli verin varsa, alpha=0.1 ya da 0.01 dene.
- Model overfit ediyorsa (train >> test accuracy), alpha'yı 5.0 ya da 10.0'a yükselt.
- Smoothing'i her zaman tek train/test split ile değil, çapraz doğrulama ile doğrula.

### Adım 4: Varsayımları kontrol et

- **MultinomialNB**: Öznitelikler negatif olmamalı. Negatif değerlerin varsa kaydır ya da GaussianNB kullan.
- **GaussianNB**: Öznitelikler her sınıf içinde yaklaşık çan eğrisi biçimindeyse en iyi çalışır. Histogramlarla kontrol et.
- **BernoulliNB**: Önce özniteliklerini binarize et. Eşiği dikkatle seç (metin için: var=1, yok=0).

## Yaygın Hatalar

1. **Metin verisinde GaussianNB kullanmak.** Kelime sayıları Gaussian değildir. MultinomialNB kullan.
2. **Laplace smoothing'i unutmak.** Görülmemiş tek bir kelime tüm olasılığı sıfırlar. Her zaman smooth et.
3. **Olasılık çıktılarına güvenmek.** NB olasılıkları kötü kalibre edilmiştir. Onları confidence skoru olarak değil, sıralama için kullan. Kalibre olasılıklar gerekliyse CalibratedClassifierCV kullan.
4. **Class imbalance'ı görmezden gelmek.** NB prior'ları sınıf frekanslarını yansıtır. %99 negatif ve %1 pozitif olduğunda, prior likelihood'u domine eder. Prior'ları manuel ayarla ya da resample et.

## Hızlı Referans

| Soru | MultinomialNB | GaussianNB | BernoulliNB |
|----------|:---:|:---:|:---:|
| Metin sınıflandırma? | Evet | Hayır | Belki (kısa metin) |
| Sürekli öznitelikler? | Hayır | Evet | Hayır |
| Binary öznitelikler? | Hayır | Hayır | Evet |
| Çok hızlı eğitim gerekli? | Evet | Evet | Evet |
| Küçük eğitim seti? | İyi | İyi | İyi |
| Kalibre olasılık gerekli? | Hayır | Hayır | Hayır |

## Naive Bayes Ne Zaman KULLANILMAMALI

- Öznitelikler yüksek korelasyonlu ve korelasyonları yöneten bir model için yeterli verin var (lojistik regresyon, gradient boosting)
- En iyi olası accuracy gerekli ve bol veri var
- Özniteliklerin görüntü, dizi ya da graph (sinir ağları kullan)
- Öznitelik etkileşimlerini yakalayan bir modele ihtiyacın var (ağaç tabanlı yöntemler kullan)
