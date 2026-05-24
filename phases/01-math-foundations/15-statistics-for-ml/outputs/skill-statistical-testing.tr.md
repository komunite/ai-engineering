---
name: skill-statistical-testing
description: ML modellerini karşılaştırmak ve deneyleri değerlendirmek için doğru istatistiksel testi seç
version: 1.0.0
phase: 1
lesson: 15
tags: [statistics, hypothesis-testing, model-comparison]
---

# ML için İstatistiksel Test

Modelleri karşılaştırırken, A/B deneyleri yürütürken ya da sonuçları doğrularken doğru testi nasıl seçersin.

## Karar Kontrol Listesi

1. Ne karşılaştırıyorsun? Ortalamalar, oranlar, dağılımlar ya da korelasyonlar?
2. Kaç grup var? Bir örnek vs referans, iki grup ya da çoklu grup?
3. Gözlemler eşleştirilmiş mi (aynı test seti, aynı fold'lar) yoksa bağımsız mı?
4. Veri normal dağılımlı mı? n < 30 ve net olarak normal değilse, non-parametric kullan.
5. Veri sürekli, sıralı (ordinal) ya da kategorik mi?
6. Kaç test çalıştırıyorsun? Birden fazlaysa düzeltme uygula.

## Karar ağacı

```text
Ortalamalar mı karşılaştırılıyor?
  İki grup mu?
    Eşleştirilmiş (aynı veri split'leri)? --> Paired t-test (normal değilse Wilcoxon signed-rank)
    Bağımsız? --> Welch's t-test (normal değilse Mann-Whitney U)
  Çoklu grup mu?
    Eşleştirilmiş? --> Repeated measures ANOVA (ya da Friedman testi)
    Bağımsız? --> One-way ANOVA (ya da Kruskal-Wallis)

Oranlar mı karşılaştırılıyor?
  İki grup? --> Chi-squared testi ya da Fisher's exact (küçük n)
  Çoklu grup? --> Chi-squared testi

Dağılımlar mı karşılaştırılıyor?
  Bir dağılım referans mı? --> Kolmogorov-Smirnov testi
  İkisi de empirik mi? --> İki örnekli KS testi

İlişki ölçülüyor mu?
  İkisi de sürekli, kabaca normal? --> Pearson korelasyon
  Ordinal ya da normal değil? --> Spearman rank korelasyon
  Kategorik x Kategorik? --> Bağımsızlık için Chi-squared testi

Çok test mi çalıştırılıyor?
  Bonferroni düzeltmesi uygula: alpha_adjusted = alpha / test_sayısı
  Ya da Holm-Bonferroni kullan (daha az muhafazakar, yine de family-wise error'u kontrol eder)
```

## Hangi testi ne zaman kullanmalı

| Test | Veri tipi | Varsayımlar | ML kullanımı |
|---|---|---|---|
| Paired t-test | Sürekli, eşleştirilmiş | Normal farklar | Aynı k-fold split'lerinde 2 modeli karşılaştırma |
| Wilcoxon signed-rank | Sürekli/ordinal, eşleştirilmiş | Yok (non-parametric) | 2 modeli karşılaştır, küçük k (5-10 fold) |
| Welch's t-test | Sürekli, bağımsız | Kabaca normal | İki ayrı veri seti üzerinde modeli karşılaştır |
| Mann-Whitney U | Sürekli/ordinal, bağımsız | Yok | Latency dağılımlarını karşılaştır |
| ANOVA | Sürekli, 3+ grup | Normal, eşit varyans | Çoklu model mimarisi karşılaştır |
| Kruskal-Wallis | Sürekli/ordinal, 3+ grup | Yok | Çoklu model karşılaştır, normal olmayan metrik |
| Chi-squared | Kategorik sayımlar | Beklenen sayım >= 5 | Sınıf dağılımları, confusion matris karşılaştırma |
| Fisher's exact | Kategorik sayımlar | Küçük örneklem | Nadir olay karşılaştırma |
| KS testi | Sürekli | Yok | Tahminlerin beklenen dağılımı izleyip izlemediğini kontrol |
| Bootstrap CI | Herhangi bir istatistik | Yok | AUC, F1, herhangi bir metrik için güven aralığı |
| McNemar's test | Eşleştirilmiş binary | Yok | Aynı test setinde iki sınıflandırıcıyı karşılaştır |

## Model karşılaştırma tarifi

1. Deney çalıştırmadan önce metrik ve significance level'ı tanımla (alpha = 0.05).
2. Her iki modeli aynı k-fold çapraz doğrulama split'lerinde çalıştır (k = 5 ya da 10).
3. Eşleştirilmiş skorları topla: (a_1, b_1), (a_2, b_2), ..., (a_k, b_k).
4. Farkları hesapla: d_i = b_i - a_i.
5. Paired test çalıştır (k <= 10 için Wilcoxon, k > 10 ya da normal farklar için paired t-test).
6. Raporla: p-değeri, ortalama fark, %95 güven aralığı, effect size (Cohen's d).
7. p < alpha VE effect size anlamlıysa, fark gerçek ve uygulamaya değer.

## Yaygın hatalar

- Veri eşleştirilmişken bağımsız test kullanmak. Her iki model aynı test fold'larında değerlendirildiyse paired test kullanmak ZORUNDASIN. Bağımsız testler eşleştirmeyi atar ve istatistiksel gücü kaybeder.
- Effect size olmadan p < 0.05 raporlamak. İstatistiksel olarak anlamlı %0.1 accuracy iyileşmesi deploy etmeye değmez. Her zaman Cohen's d ya da ham ortalama fark hesapla.
- Modelleri farklı test setlerinde karşılaştırmak. Test seti her iki model için aynı OLMAK ZORUNDA. Farklı test setleri karşılaştırmayı anlamsız kılar.
- 20 karşılaştırma çalıştırıp Bonferroni düzeltmesi olmadan en iyisini raporlamak. alpha = 0.05'te 20 testle şans eseri 1 false positive beklersin.
- Dengesiz veride accuracy kullanmak. %99 çoğunluk sınıfında trivial bir sınıflandırıcı %99 alır. F1, precision-recall AUC ya da Matthews correlation coefficient kullan.
- Cross-validation fold'larını bağımsız örnekler gibi muamele etmek. Eğitim verisi paylaşırlar, bu da bağımsızlık varsayımını ihlal eder. Düzeltilmiş resampled t-test bunu hesaba katar.

## Hızlı referans: effect size yorumlaması

| Cohen's d | Yorum |
|---|---|
| 0.2 | Küçük etki |
| 0.5 | Orta etki |
| 0.8 | Büyük etki |
| > 1.0 | Çok büyük etki |

| Ne raporlanır | Neden |
|---|---|
| p-değeri | Fark gerçek mi? |
| Güven aralığı | Fark ne kadar büyük olabilir? |
| Effect size (Cohen's d) | Fark anlamlı mı? |
| Örneklem büyüklüğü (n ya da k fold) | Sonuca güvenebilir miyiz? |
