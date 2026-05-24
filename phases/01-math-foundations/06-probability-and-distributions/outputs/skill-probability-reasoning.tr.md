---
name: skill-probability-reasoning
description: Bir ML problemi için doğru olasılık dağılımını seç
version: 1.0.0
phase: 1
lesson: 6
tags: [probability, distributions, modeling]
---

# Olasılık Dağılımı Seçimi

Veri modellerken, loss fonksiyonu tasarlarken ya da prior belirlerken doğru dağılımı nasıl seçersin.

## Karar Kontrol Listesi

1. Çıktı kesikli mi (kategori, sayım) yoksa sürekli mi (ölçüm, skor)?
2. Çıktı sınırlı mı (örn. [0, 1]) yoksa sınırsız mı?
3. Kaç olası çıktı var? İki? k? Sonsuz?
4. Veri simetrik mi yoksa çarpık mı?
5. Olaylar bağımsız mı yoksa ilişkili mi?
6. Bir hızı mı, sayımı mı, oranı mı yoksa ölçümü mü modelliyorsun?

## Dağılım karar ağacı

```
Değişken kesikli mi?
  Evet --> Sadece 2 çıktı mı? --> Bernoulli (p)
     |    k çıktı, tek deneme? --> Kategorik (p1...pk)
     |    k çıktı, n deneme? --> Multinomial (n, p1...pk)
     |    n denemede başarı sayısı? --> Binomial (n, p)
     |    Aralık başına olay sayısı? --> Poisson (lambda)
     |    İlk başarıya kadar deneme sayısı? --> Geometrik (p)
     |    r başarıya kadar deneme sayısı? --> Negatif Binomial (r, p)
  Hayır --> Simetrik, çan şeklinde mi? --> Normal (mu, sigma)
     |   Pozitif değerler, sağa çarpık? --> Log-normal ya da Exponential
     |   [0, 1] aralığında mı? --> Beta (alpha, beta)
     |   Pozitif değerler, esnek şekil? --> Gamma (alpha, beta)
     |   Olaylar arası süre? --> Exponential (lambda)
     |   Ağır kuyruk gerekiyor mu? --> Student's t (nu) ya da Cauchy
     |   Çok değişkenli, çan şekli? --> Multivariate Normal
     |   Simplex üzerinde (toplam 1)? --> Dirichlet (alpha)
```

## Gerçek dünya ML senaryolarını dağılımlarla eşleştirme

| Senaryo | Dağılım | Parametreler |
|---|---|---|
| Binary sınıflandırma çıktısı | Bernoulli | p = sigmoid(logit) |
| Çok sınıflı sınıflandırma çıktısı | Kategorik | p = softmax(logits) |
| Dil modellerinde token tahmini | Kelime dağarcığı üzerinde Kategorik | softmax'ten p |
| Piksel yoğunluğu (normalize) | Beta veya Uniform [0, 1] | Görüntü istatistiklerine bağlı |
| Bir belgedeki kelime sayısı | Poisson | lambda = ortalama kelime sayısı |
| Kullanıcı istekleri arası süre | Exponential | lambda = istek oranı |
| Ölçüm hatası | Normal | mu = 0, sigma veriden |
| Ağırlık başlatma (initialization) | Normal veya Uniform | Kaiming/Xavier kuralları |
| VAE latent uzay prior'u | Standart Normal | mu = 0, sigma = 1 |
| Oranlar için Bayesçi prior | Beta | inanca göre alpha, beta |
| Kategori ağırlıkları için Bayesçi prior | Dirichlet | alpha vektörü |
| Regresyon hedeflerinde gürültü | Normal | mu = 0, sigma tahminli |
| Outlier'a dayanıklı regresyon | Student's t | düşük serbestlik derecesi |
| Süre / yaşam modelleme | Weibull ya da Gamma | shape ve scale |
| Belge başına konu dağılımı (LDA) | Dirichlet | seyrek için alpha < 1 |

## Dağılımlar nerede yanlış gider

- Verinin sert bir alt sınırı olduğunda Normal kullanmak (örn. fiyatlar, mesafeler). Normal negatif değerlere sıfır olmayan olasılık atar. Onun yerine log-normal ya da gamma kullan.
- Varyans ortalamadan farklıyken Poisson kullanmak. Poisson mean = variance varsayar. Varyans > ortalama ise negatif binomial kullan.
- Çok sınıflı problemler için Bernoulli kullanmak. Bernoulli yalnızca ikilidir. k > 2 için kategorik kullan.
- Gözlemler ilişkiliyken bağımsızlık varsaymak. Zaman serileri, mekansal veri ve gruplanmış veri bağımsızlığı ihlal eder. Autoregresif ya da hiyerarşik modeller kullan.

## Yaygın hatalar

- PDF değerlerini olasılıkla karıştırmak. PDF 1'i aşabilir. Olasılık, PDF'i bir aralık üzerinde integre ederek elde edilir.
- Softmax çıktılarının kategorik olasılıklar olduğunu unutmak; bağımsız Bernoulli olasılıkları değildirler. Yapı gereği toplamları 1'dir.
- Domain bilgin varken uniform prior kullanmak. Bilgilendirici prior'lar, iyi seçilirse sonucu sapmaya uğratmadan varyansı azaltır.
- Log-olasılıkları olasılık olarak görmek. Log-prob'lar her zaman negatiftir (ya da sıfır). Toplamları 1 etmez.

## Hızlı referans: dağılım özellikleri

| Dağılım | Destek (support) | Ortalama | Varyans | Anahtar özellik |
|---|---|---|---|---|
| Bernoulli(p) | {0, 1} | p | p(1-p) | En basit kesikli |
| Binomial(n, p) | {0..n} | np | np(1-p) | n Bernoulli toplamı |
| Poisson(lam) | {0, 1, 2, ...} | lam | lam | Mean = variance |
| Normal(mu, s^2) | (-inf, inf) | mu | s^2 | Verilen mean/var için max entropi |
| Exponential(lam) | [0, inf) | 1/lam | 1/lam^2 | Belleksiz (memoryless) |
| Beta(a, b) | [0, 1] | a/(a+b) | ab/((a+b)^2(a+b+1)) | Binomial'in eşleniği |
| Gamma(a, b) | (0, inf) | a/b | a/b^2 | Poisson'un eşleniği |
| Dirichlet(alpha) | Simplex | alpha_i/sum | (formüle bak) | Kategorik'in eşleniği |
