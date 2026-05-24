# Makine Öğrenmesi için İstatistik

> İstatistik, modelinin gerçekten çalışıp çalışmadığını ya da sadece şanslı olup olmadığını nasıl bildiğindir.

**Tür:** Yapım
**Dil:** Python
**Ön koşullar:** Faz 1, Ders 06 (Olasılık ve Dağılımlar), 07 (Bayes Teoremi)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Tanımlayıcı istatistikleri, Pearson/Spearman korelasyonunu ve kovaryans matrislerini sıfırdan hesapla
- Hipotez testleri (t-test, chi-kare) yap ve p-değerlerini ve confidence interval'ları doğru yorumla
- Dağılımsal varsayımlar olmadan herhangi bir metrik için confidence interval inşa etmek için bootstrap resampling kullan
- Effect size ölçüleri kullanarak istatistiksel anlamlılığı pratik anlamlılıktan ayır

## Sorun

İki model eğittin. Model A test setinde 0.87 puan alıyor. Model B 0.89 puan alıyor. Model B'yi deploy ediyorsun. Üç hafta sonra production metrikleri eskisinden daha kötü. Ne oldu?

Model B aslında Model A'dan iyi performans göstermedi. 0.02 fark gürültüydü. Test setin çok küçüktü ya da varyans çok yüksekti veya ikisi birden. İyileşme kılığına bürünmüş rastgeleliği yayınladın.

Bu sürekli oluyor. Kaggle leaderboard sarsıntıları. Yeniden üretilemeyen makaleler. Birkaç yüz örneğe dayanarak kazananları ilan eden A/B testleri. Temel sebep her zaman aynıdır: birisi istatistiği atladı.

İstatistik sana sinyali gürültüden ayırma araçlarını verir. Sana ne zaman bir farkın gerçek olduğunu, ne kadar emin olman gerektiğini ve bir sonuca güvenebilmen için ne kadar veriye ihtiyacın olduğunu söyler. Her ML pipeline'ı, her model karşılaştırması, her deneyin istatistiğe ihtiyacı vardır. Onsuz, tahmin ediyorsun.

## Kavram

### Tanımlayıcı İstatistikler: Verinizi Özetleme

Herhangi bir şey modellemeden önce, verinizin nasıl göründüğünü bilmeniz gerekir. Tanımlayıcı istatistikler bir veri setini şeklini yakalayan birkaç sayıya sıkıştırır.

**Merkezi eğilim ölçüleri** "orta nerede?" sorusunu cevaplar.

```
Mean (Ortalama): tüm değerlerin toplamı / sayım
                 mu = (1/n) * sum(x_i)

Median (Medyan): sıralandığında orta değer
                 Aykırı değerlere robust. [1, 2, 3, 4, 1000] varsa, mean 202
                 ama medyan 3'tür.

Mode (Mod):      en sık değer
                 Kategorik veri için yararlı. Sürekli veri için nadiren bilgilendirici.
```

Mean denge noktasıdır. Medyan yarı yol işaretidir. Farklılaştıklarında, dağılımın çarpıktır. Gelir dağılımlarının mean'i medyandan çok daha büyüktür (milyarderlerden sağa çarpıklık). Eğitim sırasında loss dağılımları genelde mean << medyan'a sahiptir (kolay örneklerden sola çarpıklık).

**Yayılım ölçüleri** "veri ne kadar dağılmış?" sorusunu cevaplar.

```
Varyans:    mean'den ortalama kare sapma
            sigma^2 = (1/n) * sum((x_i - mu)^2)

Standart sapma: varyansın karekökü
                sigma = sqrt(sigma^2)
                Veri ile aynı birimde, dolayısıyla daha yorumlanabilir.

Range:      max - min
            Aykırı değerlere duyarlı. Tek başına neredeyse hiç yararlı değil.

IQR:        Q3 - Q1 (interquartile range)
            Verinin orta %50'sinin aralığı.
            Aykırı değerlere robust. Box plot ve aykırı değer tespiti için kullanılır.
```

**Yüzdelikler** sıralanmış veriyi 100 eşit parçaya böler. 25. yüzdelik (Q1), değerlerin %25'inin bu noktanın altına düştüğü anlamına gelir. 50. yüzdelik medyandır. 75. yüzdelik Q3'tür.

```
Latency izleme için:
  P50 = medyan latency        (tipik kullanıcı deneyimi)
  P95 = 95. yüzdelik          (kötü ama en kötü durum değil)
  P99 = 99. yüzdelik          (kuyruk latency'si, sıklıkla medyanın 10 katı)
```

ML'de inference latency'si, tahmin güven dağılımları ve hata dağılımlarını anlama için yüzdeliklere önem verirsin. Ortalama hatası düşük ama berbat P99 hatası olan bir model güvenlik kritik uygulamalar için işe yaramaz olabilir.

**Örneklem vs popülasyon istatistikleri.** Bir örneklemden varyans hesaplarken, n yerine (n-1)'e böl. Bu Bessel düzeltmesidir. Örneklem ortalamanın gerçek popülasyon ortalaması olmamasını telafi eder. Paydada n olunca, gerçek varyansı sistematik olarak hafife alırsın. (n-1) olunca, tahmin yansızdır.

```
Popülasyon varyansı: sigma^2 = (1/N) * sum((x_i - mu)^2)
Örneklem varyansı:   s^2     = (1/(n-1)) * sum((x_i - x_bar)^2)
```

Pratikte: n büyükse (binlerce örnek), fark ihmal edilebilir. N küçükse (düzinelerce örnek), önemlidir.

### Korelasyon: Değişkenler Birlikte Nasıl Hareket Eder

Korelasyon iki değişken arasındaki lineer ilişkinin gücünü ve yönünü ölçer.

**Pearson korelasyon katsayısı** lineer ilişkiyi ölçer:

```
r = sum((x_i - x_bar)(y_i - y_bar)) / (n * s_x * s_y)

r = +1:  mükemmel pozitif lineer ilişki
r = -1:  mükemmel negatif lineer ilişki
r =  0:  lineer ilişki yok (ama lineer olmayan bir ilişki olabilir!)

Aralık: [-1, 1]
```

Pearson ilişkinin lineer olduğunu ve her iki değişkenin de yaklaşık olarak normal dağıldığını varsayar. Aykırı değerlere duyarlıdır. Tek bir aşırı nokta r'yi 0.1'den 0.9'a sürükleyebilir.

**Spearman rank korelasyonu** monoton ilişkiyi ölçer:

```
1. Her değeri rank'ı ile değiştir (1, 2, 3, ...)
2. Rank'larda Pearson korelasyonunu hesapla

Spearman, sadece lineer değil, herhangi bir monoton ilişkiyi yakalar.
y = x^3 ise, Pearson r < 1 verir ama Spearman rho = 1 verir.
```

**Hangisini ne zaman kullanmalı:**

```
Pearson:    Her iki değişken sürekli ve yaklaşık olarak normal.
            Özellikle lineer ilişkiye önem veriyorsun.
            Aşırı aykırı değer yok.

Spearman:   Sıralı veri (sıralamalar, derecelendirmeler).
            Veri normal dağılmamış.
            Monoton ama lineer olmayan bir ilişkiden şüpheleniyorsun.
            Aykırı değerler mevcut.
```

**Altın kural:** korelasyon nedensellik ima etmez. Dondurma satışları ve boğulma ölümleri ilişkilidir çünkü ikisi de yazın artar. Modelinin doğruluğu ve parametre sayısı ilişkilidir, ama parametre eklemek otomatik olarak doğruluğu iyileştirmez (bkz: overfitting).

### Kovaryans Matrisi

İki değişken arasındaki kovaryans birlikte nasıl değiştiklerini ölçer:

```
Cov(X, Y) = (1/n) * sum((x_i - x_bar)(y_i - y_bar))

Cov(X, Y) > 0:  X ve Y birlikte artma eğilimindedir
Cov(X, Y) < 0:  X arttığında, Y azalma eğilimindedir
Cov(X, Y) = 0:  lineer ortak hareket yok
```

D feature için kovaryans matrisi C, C[i][j] = Cov(feature_i, feature_j) olan d x d bir matristir. Diagonal girdiler C[i][i] her feature'ın varyanslarıdır.

```
C = | Var(x1)      Cov(x1,x2)  Cov(x1,x3) |
    | Cov(x2,x1)  Var(x2)      Cov(x2,x3) |
    | Cov(x3,x1)  Cov(x3,x2)  Var(x3)     |

Özellikler:
  - Simetrik: C[i][j] = C[j][i]
  - Pozitif yarı tanımlı: tüm eigenvalue'lar >= 0
  - Diagonal = varyanslar
  - Diagonal dışı = kovaryanslar
```

**PCA'ya bağlantı.** PCA kovaryans matrisini eigendecompose eder. Eigenvector'lar temel bileşenlerdir (maksimum varyans yönleri). Eigenvalue'lar sana her bileşenin ne kadar varyans yakaladığını söyler. Ders 10'da bunun tam olarak işlendi, ama şimdi kovaryans matrisinin neden ayrıştırılacak doğru şey olduğunu görüyorsun: verindeki tüm çift bazlı lineer ilişkileri kodlar.

**Korelasyona bağlantı.** Korelasyon matrisi, standartlaştırılmış değişkenlerin (her biri standart sapmasına bölünmüş) kovaryans matrisidir. Korelasyon, tüm değerler [-1, 1] aralığına düşecek şekilde kovaryansı normalize eder.

### Hipotez Testi

Hipotez testi belirsizlik altında karar vermek için bir çerçevedir. Bir iddiayla başlarsın, veri toplarsın ve verinin iddiayla tutarlı olup olmadığını belirlersin.

**Kurulum:**

```
Null hipotezi (H0):         varsayılan varsayım, genelde "etki yok"
Alternatif hipotez (H1):    göstermeye çalıştığın

Örnek:
  H0: Model A ve Model B aynı doğruluğa sahip
  H1: Model B, Model A'dan daha yüksek doğruluğa sahip
```

**P-değeri**, H0 doğru kabul edildiğinde gözlemlediğin kadar aşırı veri görme olasılığıdır. H0'ın doğru olma olasılığı DEĞİLDİR. Bu istatistikteki en yaygın yanlış anlamadır.

```
p-değeri = P(bu kadar aşırı veri | H0 doğru)

p-değeri < alpha (tipik olarak 0.05) ise:
    H0'ı reddet. Sonuç "istatistiksel olarak anlamlı"dır.
p-değeri >= alpha ise:
    H0'ı reddetmemekte başarısız ol. Yeterli kanıtın yok.
    Bu H0'ın doğru olduğu anlamına GELMEZ.
```

**Confidence interval'lar** bir parametre için makul değerlerin bir aralığını verir:

```
Mean için %95 confidence interval:
    x_bar +/- z * (s / sqrt(n))

burada %95 güven için z = 1.96

Yorum: bu deneyi birçok kez tekrarlasaydın, hesaplanan interval'ların %95'i
gerçek mean'i içerirdi. Bu, gerçek mean'in bu spesifik interval'da
olma olasılığının %95 olduğu anlamına GELMEZ.
```

Confidence interval'ın genişliği sana hassasiyet hakkında bilgi verir. Geniş interval'lar yüksek belirsizlik demektir. Dar interval'lar tahmininin hassas olduğu anlamına gelir (ama verin yanlı ise mutlaka doğru değil).

### t-test

T-test ortalamaları karşılaştırır. Birkaç çeşidi var.

**Tek örneklem t-test:** popülasyon ortalaması varsayılan bir değerden farklı mı?

```
t = (x_bar - mu_0) / (s / sqrt(n))

serbestlik derecesi = n - 1
```

**İki örneklem t-test (bağımsız):** iki grup ortalaması farklı mı?

```
t = (x_bar_1 - x_bar_2) / sqrt(s1^2/n1 + s2^2/n2)

Bu Welch t-test'idir, eşit varyans varsaymaz.
Eşit varyans için spesifik bir nedenin olmadıkça her zaman Welch'i kullan.
```

**Eşleştirilmiş t-test:** ölçümler çiftler halinde geldiğinde (aynı modelin aynı veri bölmelerinde değerlendirilmesi):

```
Her çift için d_i = x_i - y_i hesapla
Sonra d_i değerleri üzerinde mu_0 = 0'a karşı tek örneklem t-test çalıştır
```

ML'de eşleştirilmiş t-test yaygındır: her iki modeli aynı 10 cross-validation katlamasında çalıştırıp skorlarını çift bazlı karşılaştırırsın.

### Chi-kare Testi

Chi-kare testi gözlemlenen frekansların beklenen frekanslarla eşleşip eşleşmediğini kontrol eder. Kategorik veri için yararlıdır.

```
chi^2 = sum((gözlemlenen - beklenen)^2 / beklenen)

Örnek: bir dil modelinin çıktı dağılımı kategoriler boyunca
eğitim dağılımı ile eşleşir mi?

Kategori    Gözlemlenen   Beklenen
Pozitif        120          100
Negatif         80          100
chi^2 = (120-100)^2/100 + (80-100)^2/100 = 4 + 4 = 8

1 serbestlik derecesi ile chi^2 = 8 p < 0.005 verir.
Fark anlamlıdır.
```

### ML Modelleri için A/B Testi

ML'de A/B testi web A/B testi ile aynı değildir. Model karşılaştırmasının belirli zorlukları vardır:

```
1. Aynı test seti:       Her iki model de aynı veride değerlendirilmelidir.
                         Farklı test setleri karşılaştırmayı anlamsız kılar.

2. Birden fazla metrik:  Tek başına doğruluk yeterli değildir. Precision,
                         recall, F1, latency ve adalet metriklerine ihtiyacın var.

3. Varyans:              Her metriğin varyansını tahmin etmek için cross-validation
                         veya bootstrap kullan, sadece nokta tahminleri değil.

4. Veri sızıntısı:       Test seti model seçimi sırasında kullanıldıysa,
                         karşılaştırman yanlıdır. Son bir test setini ayrı tut.
```

**Prosedür:**

```
1. Metriğini ve anlamlılık seviyeni tanımla (alpha = 0.05)
2. Her iki modeli aynı k-fold cross-validation bölmelerinde çalıştır
3. Eşleştirilmiş skorları topla: [(a1, b1), (a2, b2), ..., (ak, bk)]
4. Farkları hesapla: d_i = b_i - a_i
5. Farklarda eşleştirilmiş t-test çalıştır
6. Kontrol et: mean fark 0'dan anlamlı şekilde farklı mı?
7. Mean farkı için bir confidence interval hesapla
8. Pratik anlamlılığı değerlendirmek için effect size (Cohen's d) hesapla
```

### İstatistiksel Anlamlılık vs Pratik Anlamlılık

Bir sonuç istatistiksel olarak anlamlı ama pratik olarak anlamsız olabilir. Yeterli veri ile, önemsiz bir fark bile istatistiksel olarak anlamlı hale gelir.

```
Örnek:
  Model A doğruluğu: 0.9234
  Model B doğruluğu: 0.9237
  n = 1.000.000 test örneği
  p-değeri = 0.001

İstatistiksel olarak anlamlı mı? Evet.
Pratik olarak anlamlı mı? %0.03'lük iyileşme yeni bir modeli deploy etmenin
mühendislik maliyetine değmez.
```

**Effect size** farkın ne kadar büyük olduğunu örneklem boyutundan bağımsız olarak nicelendirir:

```
Cohen's d = (mean_1 - mean_2) / pooled_std

d = 0.2:  küçük etki
d = 0.5:  orta etki
d = 0.8:  büyük etki
```

Her zaman hem p-değerini hem de effect size'ı raporla. P-değeri sana farkın gerçek olup olmadığını söyler. Effect size sana önemli olup olmadığını söyler.

### Çoklu Karşılaştırma Problemi

Çok sayıda hipotezi test ettiğinde, bazıları şans eseri "anlamlı" olur. Alpha = 0.05'te 20 şey test edersen, hiçbir şey gerçek olmasa bile 1 yanlış pozitif beklersin.

```
P(en az bir yanlış pozitif) = 1 - (1 - alpha)^m

m = 20 test, alpha = 0.05:
P(yanlış pozitif) = 1 - 0.95^20 = 0.64

En az bir yanlış pozitif olma şansın %64.
```

**Bonferroni düzeltmesi:** alpha'yı test sayısına böl.

```
Düzeltilmiş alpha = alpha / m = 0.05 / 20 = 0.0025

Sadece p-değeri < 0.0025 ise H0'ı reddet.
Muhafazakar ama basit. Testler bağımsız olduğunda çalışır.
```

ML'de bu, bir modeli birden fazla metrik boyunca karşılaştırdığında, birçok hiperparametre konfigürasyonunu test ettiğinde veya birden fazla veri seti üzerinde değerlendirdiğinde önemlidir.

### Bootstrap Yöntemleri

Bootstrap, verini yerine koyarak yeniden örnekleyerek bir istatistiğin örnekleme dağılımını tahmin eder. Altta yatan dağılım hakkında varsayım gerekmez.

**Algoritma:**

```
1. n veri noktan var
2. n örnek YERİNE KOYARAK çek (bazı noktalar birden fazla görünür,
   bazıları hiç görünmez)
3. Bu bootstrap örneğinde istatistiğini hesapla
4. B kez tekrarla (tipik olarak B = 1000 ile 10000 arası)
5. Bootstrap istatistiklerinin dağılımı
   örnekleme dağılımına yaklaşır
```

**Bootstrap confidence interval (yüzdelik yöntemi):**

```
B bootstrap istatistiğini sırala
%95 CI = [2.5. yüzdelik, 97.5. yüzdelik]
```

**Bootstrap ML için neden önemli:**

```
- Test seti doğruluğu bir nokta tahminidir. Bootstrap sana
  confidence interval'lar verir.
- Metrik dağılımlarının normal olduğunu varsayamazsın (özellikle
  AUC, F1, precision at k için).
- Bootstrap HERHANGİ bir istatistik için çalışır: medyan, iki mean'in oranı,
  iki model arasındaki AUC farkı.
- Kapalı form formülüne gerek yok.
```

**Model karşılaştırması için bootstrap:**

```
1. Model A ve Model B'den aynı test setinde tahminlerin var
2. Her bootstrap iterasyonu için:
   a. Test indekslerini yerine koyarak yeniden örnekle
   b. Yeniden örneklenmiş kümede metric_A ve metric_B hesapla
   c. diff = metric_B - metric_A sakla
3. Fark için %95 CI:
   [diff'lerin 2.5. yüzdeliği, diff'lerin 97.5. yüzdeliği]
4. CI 0 içermiyorsa, fark anlamlıdır
```

Bu eşleştirilmiş t-test'ten daha robust'tır çünkü dağılımsal varsayım yapmaz.

### Parametrik vs Parametrik Olmayan Testler

**Parametrik testler** belirli bir dağılım varsayar (genelde normal):

```
t-test:         normal dağılmış veri varsayar (veya CLT ile büyük n)
ANOVA:          normallik ve eşit varyans varsayar
Pearson r:      iki değişkenli normallik varsayar
```

**Parametrik olmayan testler** dağılımsal varsayım yapmaz:

```
Mann-Whitney U:        iki grubu karşılaştırır (bağımsız t-test'in yerine)
Wilcoxon signed-rank:  eşleştirilmiş veriyi karşılaştırır (eşleştirilmiş t-test'in yerine)
Spearman rho:          rank'larda korelasyon (Pearson'ın yerine)
Kruskal-Wallis:        birden fazla grubu karşılaştırır (ANOVA'nın yerine)
```

**Parametrik olmayan ne zaman kullanılır:**

```
- Küçük örneklem boyutu (n < 30) ve veri açıkça normal değil
- Sıralı veri (derecelendirmeler, sıralamalar)
- Kaldıramayacağın ağır aykırı değerler
- Çarpık dağılımlar
```

**Parametrik ne zaman kullanılır:**

```
- Büyük örneklem boyutu (CLT test istatistiğini yaklaşık olarak normal yapar)
- Veri ekstrem aykırı değerler olmadan kabaca simetrik
- Daha fazla istatistiksel güç (gerçek farkları tespit etmede daha iyi)
```

ML deneylerinde tipik olarak küçük n'in olur (5 veya 10 cross-validation katlaması), dolayısıyla Wilcoxon signed-rank gibi parametrik olmayan testler genelde t-test'lerden daha uygundur.

### Merkezi Limit Teoremi: Pratik Çıkarımlar

CLT, örneklem ortalamalarının dağılımının n büyüdükçe altta yatan popülasyon dağılımından bağımsız olarak normal dağılıma yaklaştığını söyler.

```
Eğer X_1, X_2, ..., X_n mean mu ve varyans sigma^2 olan iid ise:

    X_bar ~ Normal(mu, sigma^2 / n)    n -> sonsuza giderken

Çoğu durumda n >= 30 için çalışır.
Çok çarpık dağılımlar için n >= 100 gerekebilir.
```

**ML için neden önemli:**

```
1. Birleştirilmiş metrikler üzerinde confidence interval'lar ve t-test'leri haklı çıkarır
2. Bireysel katlamalar çılgınca değişse bile cross-validation katlamaları üzerinde
   ortalama almanın neden kararlı tahminler verdiğini açıklar
3. Mini-batch gradient descent çalışır çünkü bir batch üzerinde ortalama gradyan
   gerçek gradyana yaklaşır (CLT iş başında)
4. Ensemble yöntemleri: birçok modelden tahminlerin ortalamasını almak
   herhangi bir tek modelden daha kararlı çıktı verir
```

**CLT'nin YAPMADIĞI şeyler:**

```
- Verini normal YAPMAZ. Örneklerin ORTALAMASINI normal yapar.
- Sonsuz varyanslı ağır kuyruklu dağılımlar için ÇALIŞMAZ
  (Cauchy dağılımı).
- Bağımlı veriye UYGULANMAZ (düzeltme olmadan zaman serisi).
```

### ML Makalelerinde Yaygın İstatistiksel Hatalar

1. **Eğitim setinde test etmek.** Overfitting'i garantiler. Her zaman modelin eğitim sırasında asla görmediği veriyi ayrı tut.

2. **Confidence interval yok.** Belirsizlik olmadan tek bir doğruluk sayısı raporlamak sonuçları tekrar üretilemez ve doğrulanamaz yapar.

3. **Çoklu karşılaştırmaları yok saymak.** 50 konfigürasyonu test edip en iyisini düzeltme olmadan raporlamak yanlış pozitif oranlarını şişirir.

4. **İstatistiksel ve pratik anlamlılığı karıştırmak.** %0.01 doğruluk iyileştirmesinde 0.001 p-değeri anlamlı değildir.

5. **Dengesiz veride doğruluk kullanmak.** %99 negatif sınıfı olan bir veri setinde %99 doğruluk modelin hiçbir şey öğrenmediği anlamına gelir. Precision, recall, F1 veya AUC kullan.

6. **Cherry-picking metrikler.** Sadece modelinin kazandığı metriği raporlamak. Dürüst değerlendirme tüm ilgili metrikleri raporlar.

7. **Train/test bölmeleri arasında bilgi sızdırma.** Bölmeden önce normalleştirmek veya geçmişi tahmin etmek için gelecek veriyi kullanmak.

8. **Varyans tahmini olmadan küçük test setleri.** 100 örnekte değerlendirip %2 iyileşme iddia etmek sinyal değil gürültüdür.

9. **Veri bağımsız olmadığında bağımsızlık varsaymak.** Aynı hastadan tıbbi görüntüler, aynı belgeden birden fazla cümle. Bir grup içindeki gözlemler ilişkilidir.

10. **P-hacking.** p < 0.05 alana kadar farklı testler, alt kümeler veya hariç tutma kriterleri denemek. Sonuç aramanın bir eseridir.

## İnşa Etme

Şunları implemente edeceksin:

1. **Sıfırdan tanımlayıcı istatistikler** (mean, medyan, mod, standart sapma, yüzdelikler, IQR)
2. **Korelasyon fonksiyonları** (kovaryans matrisi ile birlikte Pearson ve Spearman)
3. **Hipotez testleri** (tek örneklem t-test, iki örneklem t-test, chi-kare testi)
4. **Bootstrap confidence interval'ları** (herhangi bir istatistik için, varsayım gerekmez)
5. **A/B test simülatörü** (veri üret, test et, Type I ve Type II hatalarını kontrol et)
6. **İstatistiksel vs pratik anlamlılık demosu** (büyük n'in her şeyi "anlamlı" yaptığını gösterir)

Hepsi sıfırdan, sadece `math` ve `random` kullanılarak. numpy yok, scipy yok.

## Anahtar Terimler

| Terim | Tanım |
|---|---|
| Mean (Ortalama) | Değerlerin toplamının sayıma bölünmesi. Aykırı değerlere duyarlı. |
| Medyan | Sıralanmış verinin orta değeri. Aykırı değerlere robust. |
| Standart sapma | Varyansın karekökü. Yayılımı orijinal birimlerde ölçer. |
| Yüzdelik | Verinin belirli bir yüzdesinin altına düştüğü değer. |
| IQR | Interquartile range. Q3 eksi Q1. Orta %50'nin yayılımı. |
| Pearson korelasyonu | İki değişken arasındaki lineer ilişkiyi ölçer. Aralık [-1, 1]. |
| Spearman korelasyonu | Rank'lar kullanarak monoton ilişkiyi ölçer. |
| Kovaryans matrisi | Tüm feature'lar arasındaki çift bazlı kovaryansların matrisi. |
| Null hipotezi | Hiç etki veya fark olmadığı varsayılan varsayım. |
| p-değeri | Null hipotezi doğru kabul edildiğinde bu kadar aşırı veri görme olasılığı. |
| Confidence interval | Belirli bir güven seviyesinde bir parametre için makul değerlerin aralığı. |
| t-test | Mean'lerin anlamlı şekilde farklı olup olmadığını test eder. T-dağılımı kullanır. |
| Chi-kare testi | Gözlemlenen frekansların beklenen frekanslardan farklı olup olmadığını test eder. |
| Effect size | Bir farkın büyüklüğü, örneklem boyutundan bağımsız. Cohen's d yaygındır. |
| Bonferroni düzeltmesi | Yanlış pozitifleri kontrol etmek için anlamlılık eşiğini test sayısına böler. |
| Bootstrap | Örnekleme dağılımlarını tahmin etmek için yerine koyarak yeniden örnekleme. |
| Type I hatası | Yanlış pozitif. H0 doğruyken reddetmek. |
| Type II hatası | Yanlış negatif. H0 yanlışken reddetmemekte başarısız olmak. |
| İstatistiksel güç | Yanlış bir H0'ı doğru reddetme olasılığı. Power = 1 eksi Type II hata oranı. |
| Merkezi limit teoremi | Örneklem boyutu büyüdükçe örneklem ortalamaları normal dağılıma yakınsar. |
| Parametrik test | Veri için belirli bir dağılım varsayar (genelde normal). |
| Parametrik olmayan test | Dağılımsal varsayım yapmaz. Rank'lar veya işaretler üzerinde çalışır. |
