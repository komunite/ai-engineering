# Olasılık ve Dağılımlar

> Olasılık, yapay zekanın belirsizliği ifade etmek için kullandığı dildir.

**Tür:** Öğrenim
**Dil:** Python
**Ön koşullar:** Faz 1, Ders 01-04
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Bernoulli, kategorik, Poisson, uniform ve normal dağılımlar için PMF ve PDF'leri sıfırdan implemente et
- Beklenen değer, varyans hesapla ve Gauss'ların neden hakim olduğunu açıklamak için Merkezi Limit Teoremi'ni kullan
- Sayısal kararlılık hilesiyle (max logit'i çıkararak) softmax ve log-softmax fonksiyonları inşa et
- Logit'lerden cross-entropy loss hesapla ve onu negatif log-likelihood'a bağla

## Sorun

Bir sınıflandırıcı `[0.03, 0.91, 0.06]` çıktısı veriyor. Bir dil modeli 50.000 aday arasından sonraki kelimeyi seçer. Bir diffusion modeli öğrenilen dağılımlardan örnekleyerek görüntüler üretir. Bunların hepsi iş başındaki olasılıktır.

Bir modelin yaptığı her tahmin bir olasılık dağılımıdır. Her loss fonksiyonu, tahmin edilen dağılımın gerçek olandan ne kadar uzak olduğunu ölçer. Her eğitim adımı bir dağılımı diğerine benzemesi için parametreleri ayarlar. Olasılık olmadan tek bir ML makalesi okuyamazsın, tek bir modeli debug edemezsin veya eğitim loss'unun neden NaN olduğunu anlayamazsın.

## Kavram

### Olaylar, Örneklem Uzayları ve Olasılık

Örneklem uzayı S, tüm olası sonuçların kümesidir. Bir olay, örneklem uzayının bir alt kümesidir. Olasılık, olayları 0 ile 1 arasındaki sayılara eşler.

```
Yazı-tura:
  S = {Y, T}
  P(Y) = 0.5,  P(T) = 0.5

Tek zar atışı:
  S = {1, 2, 3, 4, 5, 6}
  P(çift) = P({2, 4, 6}) = 3/6 = 0.5
```

Üç aksiyom tüm olasılığı tanımlar:
1. Herhangi bir A olayı için P(A) >= 0
2. P(S) = 1 (her zaman bir şey olur)
3. A ve B aynı anda olamadığında P(A veya B) = P(A) + P(B)

Geri kalan her şey (Bayes teoremi, beklenen değerler, dağılımlar) bu üç kuraldan çıkar.

### Koşullu Olasılık ve Bağımsızlık

P(A|B), B olduğu varsayıldığında A'nın olasılığıdır.

```
P(A|B) = P(A ve B) / P(B)

Örnek: iskambil destesi
  P(Papaz | Resimli kart) = P(Papaz ve Resimli) / P(Resimli)
                          = (4/52) / (12/52)
                          = 4/12 = 1/3
```

İki olay, birini bilmek diğeri hakkında hiçbir şey söylemediğinde bağımsızdır:

```
Bağımsız:    P(A|B) = P(A)
Eşdeğer:     P(A ve B) = P(A) * P(B)
```

Yazı-tura atışları bağımsızdır. İade etmeden kart çekmek değildir.

### Probability Mass Function vs Probability Density Function

Kesikli rastgele değişkenlerin bir probability mass function'ı (PMF) vardır. Her sonucun doğrudan okuyabileceğin belirli bir olasılığı vardır.

```
PMF: P(X = k)

Adil zar:
  P(X = 1) = 1/6
  P(X = 2) = 1/6
  ...
  P(X = 6) = 1/6

  Tüm olasılıkların toplamı = 1
```

Sürekli rastgele değişkenlerin bir probability density function'ı (PDF) vardır. Tek bir noktadaki yoğunluk bir olasılık değildir. Olasılık, yoğunluğun bir aralık üzerinden integralinden gelir.

```
PDF: f(x)

P(a <= X <= b) = a'dan b'ye f(x)'in integrali

f(x) 1'den büyük olabilir (yoğunluk, olasılık değil)
-inf'ten +inf'e f(x) dx'in integrali = 1
```

Bu ayrım ML'de önemli. Sınıflandırma çıktıları PMF'lerdir (kesikli seçimler). VAE latent uzayları PDF'leri kullanır (sürekli).

### Yaygın Dağılımlar

**Bernoulli:** bir deneme, iki sonuç. İkili sınıflandırmayı modeller.

```
P(X = 1) = p
P(X = 0) = 1 - p
Ortalama = p,  Varyans = p(1-p)
```

**Kategorik:** bir deneme, k sonuç. Çok sınıflı sınıflandırmayı (softmax çıktısı) modeller.

```
P(X = i) = p_i,  p_i'lerin toplamı = 1
Örnek: P(kedi) = 0.7,  P(köpek) = 0.2,  P(kuş) = 0.1
```

**Uniform:** tüm sonuçlar eşit olası. Rastgele initialization için kullanılır.

```
Kesikli: k in {1, ..., n} için P(X = k) = 1/n
Sürekli: x in [a, b] için f(x) = 1/(b-a)
```

**Normal (Gauss):** çan eğrisi. Ortalama (mu) ve varyans (sigma^2) ile parametrize edilir.

```
f(x) = (1 / sqrt(2*pi*sigma^2)) * exp(-(x - mu)^2 / (2*sigma^2))

Standart normal: mu = 0, sigma = 1
  Verinin %68'i 1 sigma içinde
  %95'i 2 sigma içinde
  %99.7'si 3 sigma içinde
```

**Poisson:** sabit bir aralıkta nadir olayların sayıları. Olay oranlarını modeller.

```
P(X = k) = (lambda^k * e^(-lambda)) / k!
Ortalama = lambda,  Varyans = lambda
```

### Beklenen Değer ve Varyans

Beklenen değer ağırlıklı ortalama sonuçtur.

```
Kesikli:   E[X] = x_i * P(X = x_i)'lerin toplamı
Sürekli:   E[X] = x * f(x) dx'in integrali
```

Varyans ortalama etrafındaki yayılımı ölçer.

```
Var(X) = E[(X - E[X])^2] = E[X^2] - (E[X])^2
Standart sapma = sqrt(Var(X))
```

ML'de beklenen değer loss fonksiyonu olarak görünür (veri dağılımı üzerinde ortalama loss). Varyans sana model kararlılığı hakkında bilgi verir. Gradyanlardaki yüksek varyans gürültülü eğitim demektir.

### Birleşik (Joint) ve Marjinal Dağılımlar

Bir birleşik dağılım P(X, Y) iki rastgele değişkeni birlikte tanımlar.

Birleşik PMF örneği (X = hava durumu, Y = şemsiye):

| | Y=0 (şemsiyesiz) | Y=1 (şemsiyeli) | Marjinal P(X) |
|---|---|---|---|
| X=0 (güneş) | 0.40 | 0.10 | P(X=0) = 0.50 |
| X=1 (yağmur) | 0.05 | 0.45 | P(X=1) = 0.50 |
| **Marjinal P(Y)** | P(Y=0) = 0.45 | P(Y=1) = 0.55 | 1.00 |

Marjinal dağılım diğer değişkeni toplama ile dışarı alır:

```
P(X = x) = tüm y'ler üzerinden P(X = x, Y = y)'nin toplamı
```

Yukarıdaki tablodaki satır ve sütun toplamları marjinal'lerdir.

### Normal Dağılım Neden Her Yerde Görünür

Merkezi Limit Teoremi: birçok bağımsız rastgele değişkenin toplamı (veya ortalaması), orijinal dağılımdan bağımsız olarak normal dağılıma yakınsar.

```
1 zar at:  uniform dağılım (düz)
2 zarın ortalaması:  üçgensel (tepeli)
30 zarın ortalaması: neredeyse mükemmel çan eğrisi

Bu HERHANGİ bir başlangıç dağılımı için çalışır.
```

Bu yüzden:
- Ölçüm hataları yaklaşık normaldir (birçok küçük bağımsız kaynak)
- Sinir ağlarındaki weight initialization'ları normal dağılım kullanır
- SGD'deki gradient gürültüsü yaklaşık normaldir (birçok örnek gradyanın toplamı)
- Normal dağılım, verilen bir ortalama ve varyans için maksimum entropi dağılımıdır

### Log Olasılıkları

Ham olasılıklar sayısal problemlere yol açar. Birçok küçük olasılığı birbiriyle çarpmak hızla underflow ile sıfıra düşer.

```
P(cümle) = P(kelime1) * P(kelime2) * ... * P(kelime_n)
         = 0.01 * 0.003 * 0.02 * ...
         -> 0.0 (~30 terim sonra underflow)
```

Log olasılıkları bunu düzeltir. Çarpmalar toplamalara dönüşür.

```
log P(cümle) = log P(kelime1) + log P(kelime2) + ... + log P(kelime_n)
             = -4.6 + -5.8 + -3.9 + ...
             -> sonlu sayı (underflow yok)
```

Kurallar:
- log(a * b) = log(a) + log(b)
- Log olasılıkları her zaman <= 0'dır (çünkü 0 < P <= 1)
- Daha negatif = daha az olası
- Cross-entropy loss, doğru sınıfın negatif log olasılığıdır

### Olasılık Dağılımı Olarak Softmax

Sinir ağları ham skorlar (logit'ler) çıktısı verir. Softmax onları geçerli bir olasılık dağılımına çevirir.

```
softmax(z_i) = exp(z_i) / tüm j'ler için exp(z_j)'nin toplamı

Özellikler:
  - Tüm çıktılar (0, 1) aralığındadır
  - Tüm çıktılar 1'e toplanır
  - Girdilerin göreli sıralamasını korur
  - exp() logit'ler arasındaki farkları büyütür
```

Softmax hilesi: overflow'u önlemek için üstel almadan önce max logit'i çıkar.

```
z = [100, 101, 102]
exp(102) = overflow

z_shifted = z - max(z) = [-2, -1, 0]
exp(0) = 1  (güvenli)

Aynı sonuç, overflow yok.
```

Log-softmax sayısal kararlılık için softmax ve log'u birleştirir. PyTorch bunu cross-entropy loss için içeride kullanır.

### Örnekleme (Sampling)

Örnekleme, bir dağılımdan rastgele değerler çekmek demektir. ML'de:
- Dropout rastgele olarak hangi nöronların sıfırlanacağını örnekler
- Veri çoğaltması rastgele dönüşümleri örnekler
- Dil modelleri tahmin edilen dağılımdan sonraki token'ı örnekler
- Diffusion modelleri gürültüyü örnekler ve aşamalı olarak temizler

Keyfi dağılımlardan örnekleme, inverse transform sampling, rejection sampling veya reparameterization trick (VAE'lerde kullanılır) gibi teknikler gerektirir.

## İnşa Et

### Adım 1: Olasılık temelleri

```python
import math
import random

def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def combinations(n, k):
    return factorial(n) // (factorial(k) * factorial(n - k))

def conditional_probability(p_a_and_b, p_b):
    return p_a_and_b / p_b

p_king_given_face = conditional_probability(4/52, 12/52)
print(f"P(Papaz | Resimli kart) = {p_king_given_face:.4f}")
```

### Adım 2: Sıfırdan PMF ve PDF

```python
def bernoulli_pmf(k, p):
    return p if k == 1 else (1 - p)

def categorical_pmf(k, probs):
    return probs[k]

def poisson_pmf(k, lam):
    return (lam ** k) * math.exp(-lam) / factorial(k)

def uniform_pdf(x, a, b):
    if a <= x <= b:
        return 1.0 / (b - a)
    return 0.0

def normal_pdf(x, mu, sigma):
    coeff = 1.0 / (sigma * math.sqrt(2 * math.pi))
    exponent = -0.5 * ((x - mu) / sigma) ** 2
    return coeff * math.exp(exponent)
```

### Adım 3: Beklenen değer ve varyans

```python
def expected_value(values, probabilities):
    return sum(v * p for v, p in zip(values, probabilities))

def variance(values, probabilities):
    mu = expected_value(values, probabilities)
    return sum(p * (v - mu) ** 2 for v, p in zip(values, probabilities))

die_values = [1, 2, 3, 4, 5, 6]
die_probs = [1/6] * 6
mu = expected_value(die_values, die_probs)
var = variance(die_values, die_probs)
print(f"Zar: E[X] = {mu:.4f}, Var(X) = {var:.4f}, SD = {var**0.5:.4f}")
```

### Adım 4: Dağılımlardan örnekleme

```python
def sample_bernoulli(p, n=1):
    return [1 if random.random() < p else 0 for _ in range(n)]

def sample_categorical(probs, n=1):
    cumulative = []
    total = 0
    for p in probs:
        total += p
        cumulative.append(total)
    samples = []
    for _ in range(n):
        r = random.random()
        for i, c in enumerate(cumulative):
            if r <= c:
                samples.append(i)
                break
    return samples

def sample_normal_box_muller(mu, sigma, n=1):
    samples = []
    for _ in range(n):
        u1 = random.random()
        u2 = random.random()
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        samples.append(mu + sigma * z)
    return samples
```

### Adım 5: Softmax ve log olasılıkları

```python
def softmax(logits):
    max_logit = max(logits)
    shifted = [z - max_logit for z in logits]
    exps = [math.exp(z) for z in shifted]
    total = sum(exps)
    return [e / total for e in exps]

def log_softmax(logits):
    max_logit = max(logits)
    shifted = [z - max_logit for z in logits]
    log_sum_exp = max_logit + math.log(sum(math.exp(z) for z in shifted))
    return [z - log_sum_exp for z in logits]

def cross_entropy_loss(logits, target_index):
    log_probs = log_softmax(logits)
    return -log_probs[target_index]
```

### Adım 6: Merkezi Limit Teoremi gösterimi

```python
def demonstrate_clt(dist_fn, n_samples, n_averages):
    averages = []
    for _ in range(n_averages):
        samples = [dist_fn() for _ in range(n_samples)]
        averages.append(sum(samples) / len(samples))
    return averages
```

### Adım 7: Görselleştirme

```python
import matplotlib.pyplot as plt

xs = [mu + sigma * (i - 500) / 100 for i in range(1001)]
ys = [normal_pdf(x, mu, sigma) for x, mu, sigma in ...]
plt.plot(xs, ys)
```

Tüm görselleştirmeleri içeren tam implementasyonlar `code/probability.py`'de.

## Kullan

NumPy ve SciPy ile yukarıdaki her şey tek satırlık:

```python
import numpy as np
from scipy import stats

normal = stats.norm(loc=0, scale=1)
samples = normal.rvs(size=10000)
print(f"Ortalama: {np.mean(samples):.4f}, Std: {np.std(samples):.4f}")
print(f"P(X < 1.96) = {normal.cdf(1.96):.4f}")

logits = np.array([2.0, 1.0, 0.1])
from scipy.special import softmax, log_softmax
probs = softmax(logits)
log_probs = log_softmax(logits)
print(f"Softmax: {probs}")
print(f"Log-softmax: {log_probs}")
```

Bunları sıfırdan inşa ettin. Artık kütüphane çağrılarının ne yaptığını biliyorsun.

## Alıştırmalar

1. Exponential dağılım için inverse transform sampling implemente et. 10.000 değer örnekleyerek ve histogramı gerçek PDF ile karşılaştırarak doğrula.

2. İki hileli zar için bir birleşik dağılım tablosu kur. Marjinal dağılımları hesapla ve zarların bağımsız olup olmadığını kontrol et.

3. Doğru sınıf indeks 3 olduğunda `[2.0, 0.5, -1.0, 3.0, 0.1]` logit'leri çıkaran 5 sınıflı bir sınıflandırıcı için cross-entropy loss hesapla. Sonra cevabını PyTorch'un `nn.CrossEntropyLoss`'u ile doğrula.

4. Log olasılıklarının bir listesini alıp en olası diziyi, toplam log olasılığını ve eşdeğer ham olasılığı döndüren bir fonksiyon yaz. Her kelimenin olasılığının 0.01 olduğu 50 kelimelik bir cümleyle test et.

## Anahtar Terimler

| Terim | İnsanlar ne der | Aslında ne demek |
|------|----------------|----------------------|
| Örneklem uzayı | "Tüm olasılıklar" | Bir deneyin her olası sonucunun S kümesi |
| PMF | "Olasılık fonksiyonu" | Her kesikli sonucun tam olasılığını veren, 1'e toplanan fonksiyon |
| PDF | "Olasılık eğrisi" | Sürekli değişkenler için yoğunluk fonksiyonu. Olasılık almak için bir aralık üzerinde integre et |
| Koşullu olasılık | "Bir şey verildiğinde olasılık" | P(A\|B) = P(A ve B) / P(B). Bayesçi düşüncenin ve Bayes teoreminin temeli |
| Bağımsızlık | "Birbirini etkilemiyorlar" | P(A ve B) = P(A) * P(B). Bir olayı bilmek diğeri hakkında hiçbir şey söylemez |
| Beklenen değer | "Ortalama" | Tüm sonuçların olasılıkla ağırlıklandırılmış toplamı. Loss fonksiyonu bir beklenen değerdir |
| Varyans | "Ne kadar yayılmış" | Ortalamadan beklenen kare sapma. Yüksek varyans = gürültülü, kararsız tahminler |
| Normal dağılım | "Çan eğrisi" | f(x) = (1/sqrt(2*pi*sigma^2)) * exp(-(x-mu)^2/(2*sigma^2)). CLT nedeniyle her yerde görünür |
| Merkezi Limit Teoremi | "Ortalamalar normal olur" | Birçok bağımsız örneğin ortalaması, kaynaktan bağımsız olarak normal dağılıma yakınsar |
| Birleşik dağılım | "İki değişken birlikte" | P(X, Y) X ve Y sonuçlarının her kombinasyonunun olasılığını tanımlar |
| Marjinal dağılım | "Diğer değişkeni topla" | P(X) = y üzerinden P(X, Y) toplamı. Birleşikten bir değişkenin dağılımını geri kazanır |
| Log olasılığı | "Log uzayında çalış" | Uzun dizilerde sayısal underflow'u önlemek için P yerine log(P) kullanmak |
| Softmax | "Skorları olasılıklara çevir" | softmax(z_i) = exp(z_i) / sum(exp(z_j)). Reel değerli logit'leri geçerli bir olasılık dağılımına eşler |
| Cross-entropy | "Loss fonksiyonu" | -sum(p_true * log(p_predicted)). İki dağılımın ne kadar farklı olduğunu ölçer. Daha düşük daha iyi |
| Logit'ler | "Ham model çıktıları" | Softmax öncesi normalize edilmemiş skorlar. Lojistik fonksiyondan adlandırılmıştır |
| Örnekleme | "Rastgele değerler çekme" | Bir olasılık dağılımına göre değer üretme. Modellerin çıktı üretme şekli |

## İleri Okuma

- [3Blue1Brown: But what is the Central Limit Theorem?](https://www.youtube.com/watch?v=zeJD6dqJ5lo) - ortalamaların neden normal olduğuna dair görsel kanıt
- [Stanford CS229 Probability Review](https://cs229.stanford.edu/section/cs229-prob.pdf) - burada işlenen her şeyi ve daha fazlasını kapsayan özlü referans
- [The Log-Sum-Exp Trick](https://gregorygundersen.com/blog/2020/02/09/log-sum-exp/) - sayısal kararlılığın neden önemli olduğu ve nasıl elde edildiği
