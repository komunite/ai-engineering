# Örnekleme Yöntemleri

> Örnekleme, yapay zekanın olasılıklar uzayını nasıl keşfettiğidir.

**Tür:** Yapım
**Dil:** Python
**Ön koşullar:** Faz 1, Ders 06-07 (Olasılık, Bayes Teoremi)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Sadece uniform rastgele sayıları kullanarak inverse CDF, rejection ve importance sampling'i sıfırdan implemente et
- Dil modeli token üretimi için temperature, top-k ve top-p (nucleus) sampling kur
- Reparameterization trick'i ve VAE'lerde örnekleme üzerinden backpropagation'ı neden mümkün kıldığını açıkla
- Normalize edilmemiş bir hedef dağılımdan örneklemek için Metropolis-Hastings MCMC çalıştır

## Sorun

Bir dil modeli prompt'unu işlemeyi bitirir ve 50.000 logit vektörü üretir. Kelime hazinesindeki her token için bir tane. Şimdi birini seçmesi lazım. Nasıl?

Her zaman en yüksek olasılıklı token'ı seçerse, her yanıt aynıdır. Deterministik. Sıkıcı. Uniform rastgele seçerse, çıktı saçmalıktır. Cevap bu uçlar arasında bir yerdedir ve oradaki yer örnekleme tarafından kontrol edilir.

Örnekleme metin üretimi ile sınırlı değildir. Reinforcement learning, yörüngeleri örnekleyerek policy gradient'larını tahmin eder. VAE'ler latent temsilleri öğrenilen dağılımlardan örnekleyerek ve rastgelelik üzerinden backpropagate ederek öğrenir. Diffusion modelleri gürültü örnekleyerek ve iteratif olarak gürültü gidererek görüntüler üretir. Monte Carlo yöntemleri kapalı form çözümü olmayan integralleri tahmin eder. MCMC algoritmaları enumeratıng yapılması imkansız yüksek boyutlu posterior dağılımları keşfeder.

Her generative AI sistemi bir örnekleme sistemidir. Örnekleme stratejisi çıktının kalitesini, çeşitliliğini ve kontrol edilebilirliğini belirler. Bu ders her büyük örnekleme yöntemini sıfırdan inşa eder, uniform rastgele sayılardan başlayıp modern LLM'leri ve generative modelleri güçlendiren tekniklerle biter.

## Kavram

### Örnekleme Neden Önemli

Örnekleme AI ve makine öğrenmesi boyunca dört temel rolde görünür:

**Üretim.** Dil modelleri, diffusion modelleri ve GAN'lar hepsi örnekleyerek çıktı üretir. Örnekleme algoritması doğrudan yaratıcılığı, tutarlılığı ve çeşitliliği kontrol eder. Temperature, top-k ve nucleus sampling mühendislerin her gün çevirdiği düğmelerdir.

**Eğitim.** Stochastic gradient descent mini-batch'leri örnekler. Dropout devre dışı bırakılacak nöronları örnekler. Veri çoğaltma rastgele dönüşümleri örnekler. Importance sampling reinforcement learning'de (PPO, TRPO) gradient varyansını azaltmak için örnekleri yeniden ağırlıklandırır.

**Tahmin.** ML'deki birçok büyüklüğün kapalı form çözümü yoktur. Bir veri dağılımı üzerinde beklenen loss, bir energy-based modelin partition fonksiyonu, Bayesçi çıkarımda evidence. Monte Carlo tahmini bunların hepsini örnekler üzerinden ortalama alarak yaklaşıklar.

**Keşif.** MCMC algoritmaları Bayesçi çıkarımda posterior dağılımları keşfeder. Evolutionary stratejiler parametre pertürbasyonlarını örnekler. Bandit'lerde Thompson sampling keşif ve sömürmeyi dengeler.

Temel zorluk: yalnızca basit dağılımlardan (uniform, normal) doğrudan örnekleyebilirsin. Diğer her şey için, basit örnekleri hedef dağılımdan örneklere çevirmek için bir yönteme ihtiyacın var.

### Uniform Rastgele Örnekleme

Her örnekleme yöntemi burada başlar. Bir uniform rastgele sayı üreteci [0, 1) aralığında her eşit uzunluktaki alt aralığın eşit olasılığa sahip olduğu değerler üretir.

```
U ~ Uniform(0, 1)

P(a <= U <= b) = b - a    0 <= a <= b <= 1 için

Özellikler:
  E[U] = 0.5
  Var(U) = 1/12
```

N öğeden oluşan kesikli bir kümeden uniform olarak örneklemek için, U üret ve floor(n * U)'yu döndür. Sürekli bir [a, b] aralığından örneklemek için, a + (b - a) * U hesapla.

Anahtar içgörü: tek bir uniform rastgele sayı, herhangi bir dağılımdan bir örnek üretmek için tam doğru miktarda rastgelelik içerir. İş, doğru dönüşümü bulmaktır.

### Inverse CDF Yöntemi (Inverse Transform Sampling)

Cumulative distribution function (CDF) değerleri olasılıklara eşler:

```
F(x) = P(X <= x)

Özellikler:
  F azalmayan
  F(-inf) = 0
  F(+inf) = 1
  F gerçek doğruyu [0, 1]'e eşler
```

Inverse CDF olasılıkları değerlere geri eşler. Eğer U ~ Uniform(0, 1) ise, o zaman X = F_inverse(U) hedef dağılımı takip eder.

```
Algoritma:
  1. u ~ Uniform(0, 1) üret
  2. F_inverse(u) döndür

Neden çalışır:
  P(X <= x) = P(F_inverse(U) <= x) = P(U <= F(x)) = F(x)
```

**Exponential dağılım örneği:**

```
PDF: f(x) = lambda * exp(-lambda * x),   x >= 0
CDF: F(x) = 1 - exp(-lambda * x)

F(x) = u'yu x için çöz:
  u = 1 - exp(-lambda * x)
  exp(-lambda * x) = 1 - u
  x = -ln(1 - u) / lambda

(1 - U) ve U aynı dağılıma sahip olduğundan:
  x = -ln(u) / lambda
```

Bu, F_inverse'i kapalı formda yazabildiğinde mükemmel çalışır. Normal dağılım için kapalı form inverse CDF yoktur, dolayısıyla diğer yöntemleri kullanırız (Box-Muller veya sayısal yaklaşım).

**Kesikli versiyon:** Kesikli dağılımlar için, CDF'i kümülatif toplam olarak inşa et, U üret ve kümülatif toplamın U'yu aştığı ilk indeksi bul. Ders 06'da `sample_categorical` böyle çalışır.

### Rejection Sampling

CDF'i tersine çeviremediğinde ama bir sabite kadar hedef PDF'i değerlendirebildiğinde, rejection sampling çalışır.

```
Hedef dağılım: p(x)  (değerlendirilebilir, muhtemelen normalize edilmemiş)
Proposal dağılım: q(x)  (örneklenebilir)
Sınır: tüm x'ler için p(x) <= M * q(x) olacak şekilde M

Algoritma:
  1. x ~ q(x) örnekle
  2. u ~ Uniform(0, 1) örnekle
  3. u < p(x) / (M * q(x)) ise, x'i kabul et
  4. Aksi halde, reddet ve adım 1'e git

Kabul oranı = 1/M
```

M sınırı ne kadar sıkıysa, kabul oranı o kadar yüksektir. Düşük boyutlarda (1-3), rejection sampling iyi çalışır. Yüksek boyutlarda, kabul oranı üstel olarak düşer çünkü proposal hacminin çoğu reddedilir. Bu rejection sampling için boyutluluğun lanetidir.

**Örnek: truncated normalden örnekleme.** Truncated aralık üzerinde uniform proposal kullan. Zarflayan M, o aralıktaki normal PDF'in maksimumudur.

**Örnek: yarım çemberden örnekleme.** Sınırlayıcı dikdörtgende uniform proposal yap. Nokta yarım çember içine düşerse kabul et. Monte Carlo pi'yi böyle hesaplar: kabul oranı pi/4 alan oranına eşittir.

### Importance Sampling

Bazen hedef dağılım p(x)'ten örneklere ihtiyacın yoktur. P(x) altında bir beklentiyi tahmin etmen lazımdır ve farklı bir dağılım q(x)'ten örneklerin vardır.

```
Hedef: E_p[f(x)] = integral f(x) * p(x) dx tahmin et

Yeniden yaz:
  E_p[f(x)] = integral f(x) * (p(x)/q(x)) * q(x) dx
            = E_q[f(x) * w(x)]

burada w(x) = p(x) / q(x) importance weight'leridir.

Tahmin edici:
  E_p[f(x)] ~ (1/N) * sum(f(x_i) * w(x_i))    burada x_i ~ q(x)
```

Bu reinforcement learning'de kritiktir. PPO'da (Proximal Policy Optimization), eski bir policy pi_old altında yörüngeler toplarsın ama yeni bir policy pi_new'i optimize etmek istersin. Importance weight pi_new(a|s) / pi_old(a|s)'tir. PPO bu weight'leri yeni policy'nin eskiden çok uzağa diverge etmesini önlemek için clip'ler.

Importance sampling tahminin varyansı q'nun p'ye ne kadar benzer olduğuna bağlıdır. Q, p'den çok farklıysa, birkaç örnek devasa weight'ler alır ve tahmine hakim olur. Self-normalized importance sampling bu problemi azaltmak için weight'lerin toplamına böler:

```
E_p[f(x)] ~ sum(w_i * f(x_i)) / sum(w_i)
```

### Monte Carlo Tahmini

Monte Carlo tahmini rastgele örneklerin ortalamasını alarak integralleri yaklaşıklar. Büyük sayılar yasası yakınsamayı garanti eder.

```
Hedef: I = D alanı üzerinde integral g(x) dx tahmin et

Yöntem:
  1. D'den uniform olarak x_1, ..., x_N örnekle
  2. I ~ (D'nin Hacmi / N) * sum(g(x_i))

Hata: boyuttan bağımsız olarak O(1 / sqrt(N))
```

Hata oranı boyut bağımsızdır. Bu yüzden Monte Carlo yöntemleri grid tabanlı integrasyonun imkansız olduğu yüksek boyutlarda hakimdir.

**Pi'yi tahmin etme:**

```
[-1, 1] x [-1, 1]'den uniform olarak (x, y) örnekle
Birim çemberin içine kaçının düştüğünü say: x^2 + y^2 <= 1
pi ~ 4 * (içerideki sayı) / (toplam sayı)
```

**Beklentileri tahmin etme:**

```
E[f(X)] ~ (1/N) * sum(f(x_i))    burada x_i ~ p(x)

Örneklem ortalaması gerçek beklentiye yakınsar.
Tahmin edicinin varyansı = Var(f(X)) / N
```

### Markov Chain Monte Carlo (MCMC): Metropolis-Hastings

MCMC, stationary dağılımı hedef dağılım p(x) olan bir Markov zinciri inşa eder. Yeterli adım sonra, zincirden örnekler (yaklaşık olarak) p(x)'ten örneklerdir.

```
Hedef: p(x)  (normalleştirme sabitine kadar biliniyor)
Proposal: q(x'|x)  (mevcut duruma göre sonraki durumu nasıl önereceği)

Metropolis-Hastings algoritması:
  1. Bir x_0'da başla
  2. t = 1, 2, ..., T için:
     a. x' ~ q(x'|x_t) öner
     b. Kabul oranını hesapla:
        alpha = [p(x') * q(x_t|x')] / [p(x_t) * q(x'|x_t)]
     c. min(1, alpha) olasılığıyla kabul et:
        - u < alpha ise (u ~ Uniform(0,1)): x_{t+1} = x'
        - Aksi halde: x_{t+1} = x_t
  3. İlk B örneği at (burn-in)
  4. Kalan örnekleri döndür
```

Simetrik proposal'lar için (q(x'|x) = q(x|x')), oran p(x')/p(x)'e sadeleşir. Bu orijinal Metropolis algoritmasıdır.

**Neden çalışır.** Kabul kuralı detailed balance'ı sağlar: x'te olup x'ye taşınma olasılığı x''nde olup x'e taşınma olasılığına eşittir. Detailed balance p(x)'in zincirin stationary dağılımı olduğunu ima eder.

**Pratik düşünceler:**
- Burn-in: zincir denge durumuna ulaşmadan önce erken örnekleri at
- Thinning: autocorrelation'ı azaltmak için her k. örneği tut
- Proposal ölçeği: çok küçük ve zincir yavaş hareket eder (yüksek kabul, yavaş keşif); çok büyük ve çoğu proposal reddedilir (düşük kabul, yerinde takılı)
- Yüksek boyutlarda Gauss proposal için optimal kabul oranı yaklaşık 0.234'tür

### Gibbs Sampling

Gibbs sampling çok değişkenli dağılımlar için MCMC'nin özel bir durumudur. Tüm boyutlarda aynı anda bir hareket önermek yerine, her seferinde bir değişkeni koşullu dağılımından günceller.

```
Hedef: p(x_1, x_2, ..., x_d)

Algoritma:
  Her t iterasyonu için:
    x_1^{t+1} ~ p(x_1 | x_2^t, x_3^t, ..., x_d^t) örnekle
    x_2^{t+1} ~ p(x_2 | x_1^{t+1}, x_3^t, ..., x_d^t) örnekle
    ...
    x_d^{t+1} ~ p(x_d | x_1^{t+1}, x_2^{t+1}, ..., x_{d-1}^{t+1}) örnekle
```

Gibbs sampling her koşullu dağılım p(x_i | x_{-i})'den örnekleyebilmeni gerektirir. Bu birçok model için basittir:
- Bayesçi ağlar: koşullular graf yapısından çıkar
- Gauss karışımları: koşullular Gauss'tur
- Ising modelleri: her spin'in koşullusu sadece komşularına bağlıdır

Kabul oranı her zaman 1'dir (her proposal kabul edilir) çünkü tam koşullu olandan örneklemek detailed balance'ı otomatik karşılar.

**Sınırlama.** Değişkenler yüksek ilişkili olduğunda, Gibbs sampling yavaş karışır çünkü her seferinde bir değişkeni güncellemek dağılım boyunca büyük diyagonal hareketler yapamaz.

### Temperature Sampling (LLM'lerde Kullanılır)

Dil modelleri kelime hazinesindeki her token için logit'ler z_1, ..., z_V çıkarır. Softmax bunları olasılıklara çevirir. Temperature softmax'tan önce logit'leri yeniden ölçekler:

```
p_i = exp(z_i / T) / sum(exp(z_j / T))

T = 1.0: standart softmax (orijinal dağılım)
T -> 0:  argmax (deterministik, her zaman en yüksek logit'i seçer)
T -> inf: uniform (tüm token'lar eşit olası)
T < 1.0: dağılımı keskinleştirir (daha güvenli, daha az çeşitli)
T > 1.0: dağılımı düzleştirir (daha az güvenli, daha çeşitli)
```

**Neden çalışır.** Logit'leri T < 1 ile bölmek logit'ler arasındaki farkları büyütür. z_1 = 2 ve z_2 = 1 ise, T = 0.5'e bölmek z_1/T = 4 ve z_2/T = 2 verir, boşluğu büyütür. Softmax sonrası en yüksek logit'li token çok daha büyük bir pay alır.

**Pratikte:**
- T = 0.0: greedy decoding, factual Q&A için en iyi
- T = 0.3-0.7: hafif yaratıcı, kod üretimi için iyi
- T = 0.7-1.0: dengeli, genel konuşma için iyi
- T = 1.0-1.5: yaratıcı yazım, beyin fırtınası
- T > 1.5: giderek daha rastgele, nadiren yararlı

Temperature hangi token'ların mümkün olduğunu değiştirmez. Her token'a tahsis edilen olasılık kütlesini değiştirir.

### Top-k Sampling

Top-k sampling aday setini en yüksek olasılıklı k token ile sınırlandırır, sonra yeniden normalleştirir ve o kısıtlı setten örnekler.

```
Algoritma:
  1. Tüm V token için softmax olasılıkları hesapla
  2. Token'ları olasılığa göre sırala (azalan)
  3. Sadece en üstteki k token'ı tut
  4. Yeniden normalleştir: p_i' = p_i / sum(p_j for j in top-k)
  5. Yeniden normalleştirilmiş dağılımdan örnekle

k = 1:  greedy decoding
k = V:  filtreleme yok (standart örnekleme)
k = 40: tipik ayar, olasısız token'ların uzun kuyruğunu kaldırır
```

Top-k modelin kelime hazinesi dağılımının uzun kuyruğunda var olan aşırı olasısız token'ları (yazım hataları, saçmalık) seçmesini önler. Sorun: bağlamdan bağımsız olarak k sabittir. Model güvenli olduğunda (bir token %95 olasılığa sahip), k = 40 hala 39 alternatife izin verir. Model belirsizken (olasılık 1000 token arasında dağılmış), k = 40 makul seçenekleri keser.

### Top-p (Nucleus) Sampling

Top-p sampling aday set boyutunu dinamik olarak ayarlar. Sabit sayıda token tutmak yerine, kümülatif olasılığı p'yi aşan en küçük token setini tutar.

```
Algoritma:
  1. Tüm V token için softmax olasılıkları hesapla
  2. Token'ları olasılığa göre sırala (azalan)
  3. En üstteki k olasılığın toplamı >= p olacak şekilde en küçük k bul
  4. Sadece o k token'ı tut
  5. Yeniden normalleştir ve örnekle

p = 0.9:  olasılık kütlesinin %90'ını kapsayan token'ları tutar
p = 1.0:  filtreleme yok
p = 0.1:  çok kısıtlayıcı, neredeyse greedy
```

Model güvenli olduğunda, nucleus sampling az token tutar (belki 2-3). Model belirsizken, çok tutar (belki 200). Bu adaptif davranış nucleus sampling'in genelde top-k'dan daha iyi metin üretmesinin sebebidir.

**Yaygın kombinasyonlar:**
- Temperature 0.7 + top-p 0.9: iyi genel amaçlı ayar
- Temperature 0.0 (greedy): deterministik görevler için en iyi
- Temperature 1.0 + top-k 50: Fan et al. (2018) orijinal makale ayarı

Top-k ve top-p birleştirilebilir. Önce top-k uygula, sonra kalan sette top-p.

### Reparameterization Trick (VAE'lerde Kullanılır)

Variational autoencoders (VAE'ler) girdileri latent uzayda bir dağılıma kodlayarak, o dağılımdan örnekleyerek ve örneği geri kodlayarak öğrenir. Sorun: bir örnekleme işlemi üzerinden backpropagate edemezsin.

```
Standart örnekleme (differentiable değil):
  z ~ N(mu, sigma^2)

  Rastgelelik gradient akışını engeller.
  d/d_mu [N(mu, sigma^2)'den örnek] = ???
```

Reparameterization trick rastgeleliği parametrelerden ayırır:

```
Reparameterize edilmiş örnekleme:
  epsilon ~ N(0, 1)          (sabit rastgele gürültü, parametre yok)
  z = mu + sigma * epsilon   (parametrelerin deterministik fonksiyonu)

  Şimdi z, mu ve sigma'nın deterministik, differentiable fonksiyonudur.
  d(z)/d(mu) = 1
  d(z)/d(sigma) = epsilon

  Gradient'ler mu ve sigma boyunca akar.
```

Bu çalışır çünkü N(mu, sigma^2), mu + sigma * N(0, 1) ile aynı dağılıma sahiptir. Anahtar içgörü: rastgeleliği parametre içermeyen bir kaynağa (epsilon) taşı, sonra örneği parametrelerin differentiable bir dönüşümü olarak ifade et.

**VAE eğitim döngüsünde:**
1. Encoder her girdi için mu ve log(sigma^2) çıkarır
2. epsilon ~ N(0, 1) örnekle
3. z = mu + sigma * epsilon hesapla
4. Girdiyi yeniden inşa etmek için z'yi decode et
5. Adım 4, 3, 2, 1 üzerinden backpropagate (adım 3 differentiable olduğu için mümkün)

Reparameterization trick olmadan, VAE'ler standart backpropagation ile eğitilemez. Bu tek içgörü VAE'leri pratik yaptı.

### Gumbel-Softmax (Differentiable Kategorik Örnekleme)

Reparameterization trick sürekli dağılımlar (Gauss) için çalışır. Kesikli kategorik dağılımlar için farklı bir yaklaşım gerekir. Gumbel-Softmax kategorik örneklemeye differentiable bir yaklaşım sağlar.

**Gumbel-Max trick'i (differentiable değil):**

```
Log-olasılıkları log(p_1), ..., log(p_k) olan kategorik dağılımdan örneklemek için:
  1. Her kategori için g_i ~ Gumbel(0, 1) örnekle
     (g = -log(-log(u)), burada u ~ Uniform(0, 1))
  2. argmax(log(p_i) + g_i) döndür

Bu kesin kategorik örnekler üretir.
```

**Gumbel-Softmax (differentiable yaklaşım):**

```
Sert argmax'ı yumuşak softmax ile değiştir:
  y_i = exp((log(p_i) + g_i) / tau) / sum(exp((log(p_j) + g_j) / tau))

tau (temperature) yaklaşımı kontrol eder:
  tau -> 0:  one-hot vektöre yaklaşır (sert kategorik)
  tau -> inf: uniform'a yaklaşır (1/k, 1/k, ..., 1/k)
  tau = 1.0: yumuşak yaklaşım
```

Gumbel-Softmax kesikli bir örneğin sürekli bir gevşemesini üretir. Çıktı sert one-hot yerine bir olasılık vektörüdür (yumuşak one-hot). Gradient'ler softmax boyunca akar. Eğitimde forward pass sırasında "straight-through" tahmin edicisini kullanabilirsin: forward pass için sert argmax kullan ama backward pass için yumuşak Gumbel-Softmax gradient'leri kullan.

**Uygulamalar:**
- VAE'lerde kesikli latent değişkenler
- Neural architecture search (kesikli işlemleri seçme)
- Sert attention mekanizmaları
- Kesikli action'larla reinforcement learning

### Stratified Sampling

Standart Monte Carlo örneklemesi şans eseri örneklem uzayında boşluklar bırakabilir. Stratified sampling uzayı strata'lara bölerek ve her birinden örnekleyerek eşit kapsam zorlar.

```
Standart Monte Carlo:
  [0, 1]'den uniform olarak N nokta örnekle
  Bazı bölgelerin kümeleri olabilir, diğerlerinin boşlukları

Stratified sampling:
  [0, 1]'i N eşit strata'ya böl: [0, 1/N), [1/N, 2/N), ..., [(N-1)/N, 1)
  Her strata içinde uniform olarak bir nokta örnekle
  x_i = (i + u_i) / N   burada u_i ~ Uniform(0, 1),  i = 0, ..., N-1
```

Stratified sampling standart Monte Carlo'ya kıyasla her zaman daha düşük veya eşit varyansa sahiptir:

```
Var(stratified) <= Var(standart Monte Carlo)

İyileşme f(x) yumuşak değiştiğinde en büyüktür.
Parçalı sabit fonksiyonlar için, stratified sampling kesindir.
```

**Uygulamalar:**
- Sayısal integrasyon (quasi-Monte Carlo)
- Eğitim verisi bölünmeleri (her katlamada sınıf dengesini sağlama)
- Stratifikasyon ile importance sampling (her iki tekniği birleştirme)
- NeRF (Neural Radiance Fields) kamera ışınları boyunca stratified sampling kullanır

### Diffusion Modellerine Bağlantı

Diffusion modelleri görüntüleri bir örnekleme süreciyle üretir. İleri süreç bir görüntüye T adım boyunca saf gürültü olana kadar Gauss gürültüsü ekler. Geri süreç gürültü gidermeyi öğrenir, orijinal görüntüyü adım adım kurtarır.

```
İleri süreç (bilinen):
  x_t = sqrt(alpha_t) * x_{t-1} + sqrt(1 - alpha_t) * epsilon
  burada epsilon ~ N(0, I)

  T adım sonra: x_T ~ N(0, I)  (saf gürültü)

Geri süreç (öğrenilen):
  x_{t-1} = (1/sqrt(alpha_t)) * (x_t - (1 - alpha_t)/sqrt(1 - alpha_bar_t) * epsilon_theta(x_t, t)) + sigma_t * z
  burada z ~ N(0, I)

  Her gürültü giderme adımı bir örnekleme adımıdır.
```

Bu derste yöntemlerle bağlantı:
- Her gürültü giderme adımı reparameterization trick'i kullanır (gürültü örnekle, deterministik dönüşüm uygula)
- Gürültü programı {alpha_t} bir temperature annealing biçimini kontrol eder
- Eğitim, ELBO'yu (evidence lower bound) yaklaşıklamak için Monte Carlo tahminini kullanır
- Diffusion modellerinde ancestral sampling bir Markov zinciridir (her adım sadece mevcut duruma bağlıdır)

Tüm görüntü üretim süreci iteratif örneklemedir: gürültüden başla ve her adımda öğrenilen gürültü giderme modeline göre biraz daha az gürültülü bir versiyon örnekle.

## İnşa Et

### Adım 1: Uniform ve inverse CDF örnekleme

```python
import math
import random

def sample_uniform(a, b):
    return a + (b - a) * random.random()

def sample_exponential_inverse_cdf(lam):
    u = random.random()
    return -math.log(u) / lam
```

10.000 exponential örnek üret ve mean'in 1/lambda olduğunu doğrula.

### Adım 2: Rejection sampling

```python
def rejection_sample(target_pdf, proposal_sample, proposal_pdf, M):
    while True:
        x = proposal_sample()
        u = random.random()
        if u < target_pdf(x) / (M * proposal_pdf(x)):
            return x
```

Truncated normal dağılımdan çekmek için rejection sampling kullan. Örnekleri histogramlayarak şekli doğrula.

### Adım 3: Importance sampling

```python
def importance_sampling_estimate(f, target_pdf, proposal_pdf, proposal_sample, n):
    total = 0
    for _ in range(n):
        x = proposal_sample()
        w = target_pdf(x) / proposal_pdf(x)
        total += f(x) * w
    return total / n
```

Uniform proposal kullanarak normal dağılım altında E[X^2]'yi tahmin et. Bilinen cevapla (mu^2 + sigma^2) karşılaştır.

### Adım 4: Pi'nin Monte Carlo tahmini

```python
def monte_carlo_pi(n):
    inside = 0
    for _ in range(n):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        if x*x + y*y <= 1:
            inside += 1
    return 4 * inside / n
```

### Adım 5: Metropolis-Hastings MCMC

```python
def metropolis_hastings(target_log_pdf, proposal_sample, proposal_log_pdf, x0, n_samples, burn_in):
    samples = []
    x = x0
    for i in range(n_samples + burn_in):
        x_new = proposal_sample(x)
        log_alpha = (target_log_pdf(x_new) + proposal_log_pdf(x, x_new)
                     - target_log_pdf(x) - proposal_log_pdf(x_new, x))
        if math.log(random.random()) < log_alpha:
            x = x_new
        if i >= burn_in:
            samples.append(x)
    return samples
```

Bimodal bir dağılımdan (iki Gauss karışımı) örnekle. Zincirin yörüngesini görselleştir.

### Adım 6: Gibbs sampling

```python
def gibbs_sampling_2d(conditional_x_given_y, conditional_y_given_x, x0, y0, n_samples, burn_in):
    x, y = x0, y0
    samples = []
    for i in range(n_samples + burn_in):
        x = conditional_x_given_y(y)
        y = conditional_y_given_x(x)
        if i >= burn_in:
            samples.append((x, y))
    return samples
```

### Adım 7: Temperature sampling

```python
def softmax(logits):
    max_l = max(logits)
    exps = [math.exp(z - max_l) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]

def temperature_sample(logits, temperature):
    scaled = [z / temperature for z in logits]
    probs = softmax(scaled)
    return sample_from_probs(probs)
```

Bir token logit'leri seti için temperature'ın çıktı dağılımını nasıl değiştirdiğini göster.

### Adım 8: Top-k ve top-p sampling

```python
def top_k_sample(logits, k):
    indexed = sorted(enumerate(logits), key=lambda x: -x[1])
    top = indexed[:k]
    top_logits = [l for _, l in top]
    probs = softmax(top_logits)
    idx = sample_from_probs(probs)
    return top[idx][0]

def top_p_sample(logits, p):
    probs = softmax(logits)
    indexed = sorted(enumerate(probs), key=lambda x: -x[1])
    cumsum = 0
    selected = []
    for token_idx, prob in indexed:
        cumsum += prob
        selected.append((token_idx, prob))
        if cumsum >= p:
            break
    sel_probs = [pr for _, pr in selected]
    total = sum(sel_probs)
    sel_probs = [pr / total for pr in sel_probs]
    idx = sample_from_probs(sel_probs)
    return selected[idx][0]
```

### Adım 9: Reparameterization trick

```python
def reparam_sample(mu, sigma):
    epsilon = random.gauss(0, 1)
    return mu + sigma * epsilon

def reparam_gradient(mu, sigma, epsilon):
    dz_dmu = 1.0
    dz_dsigma = epsilon
    return dz_dmu, dz_dsigma
```

Gradient'lerin reparameterize edilmiş örnek boyunca aktığını ama doğrudan örnekleme boyunca akmadığını göster.

### Adım 10: Gumbel-Softmax

```python
def gumbel_sample():
    u = random.random()
    return -math.log(-math.log(u))

def gumbel_softmax(logits, temperature):
    gumbels = [math.log(p) + gumbel_sample() for p in logits]
    return softmax([g / temperature for g in gumbels])
```

Temperature'ı azaltmanın çıktıyı bir one-hot vektöre yaklaştırdığını göster.

Tüm görselleştirmelerle birlikte tam implementasyonlar `code/sampling.py`'dedir.

## Kullan

NumPy ve SciPy ile üretim versiyonları:

```python
import numpy as np

rng = np.random.default_rng(42)

exponential_samples = rng.exponential(scale=2.0, size=10000)
print(f"Exponential mean: {exponential_samples.mean():.4f} (beklenen 2.0)")

from scipy import stats
normal = stats.norm(loc=0, scale=1)
print(f"1.96'da CDF: {normal.cdf(1.96):.4f}")
print(f"0.975'te Inverse CDF: {normal.ppf(0.975):.4f}")

logits = np.array([2.0, 1.0, 0.5, 0.1, -1.0])
temperature = 0.7
scaled = logits / temperature
probs = np.exp(scaled - scaled.max()) / np.exp(scaled - scaled.max()).sum()
token = rng.choice(len(logits), p=probs)
print(f"Örneklenen token indeksi: {token}")
```

Ölçekte MCMC için, özel kütüphaneler kullan:
- PyMC: NUTS ile tam Bayesçi modelleme (adaptif HMC)
- emcee: ensemble MCMC sampler
- NumPyro/JAX: GPU hızlandırmalı MCMC

Bunları sıfırdan inşa ettin. Artık kütüphane çağrılarının ne yaptığını biliyorsun.

## Alıştırmalar

1. Cauchy dağılımı için inverse CDF sampling implemente et. CDF F(x) = 0.5 + arctan(x)/pi. 10.000 örnek üret ve histogramı gerçek PDF'e karşı çiz. Ağır kuyrukları fark et (merkezden uzak aşırı değerler).

2. Uniform(0, 1) proposal kullanarak Beta(2, 5) dağılımından örnekler üretmek için rejection sampling kullan. Kabul edilen örnekleri gerçek Beta PDF'e karşı çiz. Teorik kabul oranı nedir?

3. Monte Carlo ile 0'dan pi'ye sin(x) integralini 1.000, 10.000 ve 100.000 örnek kullanarak tahmin et. Her seviyedeki hatayı karşılaştır. Hatanın O(1/sqrt(N)) olarak ölçeklendiğini doğrula.

4. 2B bir dağılımdan örneklemek için Metropolis-Hastings implemente et p(x, y), exp(-(x^2 * y^2 + x^2 + y^2 - 8*x - 8*y) / 2) ile orantılı. Örnekleri ve zincir yörüngesini çiz. Farklı proposal standart sapmaları ile dene.

5. Tam bir metin üretim demosu kur: logit'leri olan 10 kelimelik bir kelime hazinesi verildiğinde, (a) greedy, (b) temperature=0.7, (c) top-k=3, (d) top-p=0.9 kullanarak 20 token dizileri üret. 5 çalıştırma boyunca çıktıların çeşitliliğini karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne der | Aslında ne demek |
|------|----------------|----------------------|
| Örnekleme | "Rastgele değerler çekme" | Bir olasılık dağılımına göre değerler üretme. Tüm generative AI'ın arkasındaki mekanizma |
| Uniform dağılım | "Tümü eşit olası" | [a, b]'deki her değer eşit olasılık yoğunluğuna 1/(b-a) sahiptir. Tüm örnekleme yöntemlerinin başlangıç noktası |
| Inverse CDF | "Olasılık dönüşümü" | F_inverse(U) bir uniform örneği bilinen CDF'li herhangi bir dağılımdan örneğe çevirir. Kesin ve verimli |
| Rejection sampling | "Öner ve kabul et/reddet" | Basit bir proposal'dan üret, hedef/proposal oranıyla orantılı olasılıkla kabul et. Kesin ama örnekleri israf eder |
| Importance sampling | "Örnekleri yeniden ağırlıklandır" | Q(x)'ten örnekler kullanarak p(x) altında beklentileri her örneği p(x)/q(x) ile ağırlıklandırarak tahmin et. RL'de PPO'nun özü |
| Monte Carlo | "Rastgele örneklerin ortalaması" | İntegralleri örneklem ortalamaları olarak yaklaşıkla. Boyuttan bağımsız hata O(1/sqrt(N)) |
| MCMC | "Yakınsayan rastgele yürüyüş" | Stationary dağılımı hedef olan bir Markov zinciri inşa et. Metropolis-Hastings temel algoritma |
| Metropolis-Hastings | "Yokuş yukarıyı kabul et, bazen yokuş aşağıyı" | Hareketler öner, yoğunluk oranına dayalı kabul et. Detailed balance hedef dağılıma yakınsamayı sağlar |
| Gibbs sampling | "Her seferinde bir değişken" | Diğerleri sabit tutularak her değişkeni koşullu dağılımından güncelle. %100 kabul oranı |
| Temperature | "Güven düğmesi" | Softmax'tan önce logit'leri T'ye böler. T<1 keskinleştirir (daha güvenli), T>1 düzleştirir (daha çeşitli) |
| Top-k sampling | "En iyi k'yı tut" | En yüksek olasılıklı k token hariç tümünü sıfırla, yeniden normalleştir, örnekle. Sabit aday set boyutu |
| Nucleus sampling (top-p) | "Olası olanları tut" | Kümülatif olasılığı p'yi aşan en küçük token setini tut. Adaptif aday set boyutu |
| Reparameterization trick | "Rastgeleliği dışarı taşı" | z = mu + sigma * epsilon yaz, burada epsilon ~ N(0,1). Örneklemeyi differentiable yapar. VAE eğitimi için esastır |
| Gumbel-Softmax | "Yumuşak kategorik örnekleme" | Gumbel gürültüsü + temperature'lı softmax kullanarak kategorik örneklemeye differentiable yaklaşım |
| Stratified sampling | "Zorlanmış kapsama" | Örneklem uzayını strata'lara böl, her birinden örnekle. Her zaman naif Monte Carlo'dan daha düşük varyans |
| Burn-in | "Isınma periyodu" | Zincir stationary dağılımına ulaşmadan önce atılan ilk MCMC örnekleri |
| Detailed balance | "Tersinirlik koşulu" | p(x) * T(x->y) = p(y) * T(y->x). P'nin bir Markov zincirinin stationary dağılımı olması için yeterli koşul |
| Diffusion sampling | "İteratif gürültü giderme" | Gürültüden başlayarak ve öğrenilen gürültü giderme adımları uygulayarak veri üretme. Her adım koşullu örnekleme işlemi |

## İleri Okuma

- [Holbrook (2023): The Metropolis-Hastings Algorithm](https://arxiv.org/abs/2304.07010) - MCMC temelleri üzerine detaylı eğitim
- [Jang, Gu, Poole (2017): Categorical Reparameterization with Gumbel-Softmax](https://arxiv.org/abs/1611.01144) - orijinal Gumbel-Softmax makalesi
- [Holtzman et al. (2020): The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) - nucleus (top-p) sampling makalesi
- [Kingma & Welling (2014): Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) - reparameterization trick'i tanıtan VAE makalesi
- [Ho, Jain, Abbeel (2020): Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) - DDPM örneklemeyi görüntü üretimine bağlar
