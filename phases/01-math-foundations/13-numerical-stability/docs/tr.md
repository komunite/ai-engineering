# Sayısal Kararlılık

> Floating point sızdıran bir soyutlamadır. Eğitim sırasında seni ısırır ve geldiğini göremezsin.

**Tür:** Yapım
**Dil:** Python
**Ön koşullar:** Faz 1, Ders 01-04
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Max-subtraction trick'i kullanarak sayısal olarak kararlı softmax ve log-sum-exp implemente et
- Floating-point hesaplamalarında overflow, underflow ve catastrophic cancellation'ı tanımla
- Merkezi sonlu farklar kullanarak analitik gradyanları sayısal gradyanlara karşı doğrula
- bfloat16'nın neden eğitim için float16'ya tercih edildiğini ve loss scaling'in gradyan underflow'unu nasıl önlediğini açıkla

## Sorun

Modelin üç saat eğitilir, sonra loss NaN olur. Bir print ifadesi eklersin. Logit'ler 9.000. adımda iyi. 9.001. adımda `inf`. 9.002. adımda her gradyan `nan` ve eğitim ölmüş.

Veya: modelin tamamlanana kadar eğitilir ama doğruluk makalenin iddia ettiğinden %2 daha kötü. Her şeyi kontrol edersin. Mimari eşleşiyor. Hiperparametreler eşleşiyor. Veri eşleşiyor. Sorun, makalenin float32 kullanması ve senin doğru ölçekleme olmadan float16 kullanmandır. Otuz iki bit birikmiş yuvarlama hatası doğruluğunu sessizce yedi.

Veya: sıfırdan cross-entropy loss implemente edersin. Küçük logit'lerde çalışır. Logit'ler 100'ü aştığında `inf` döner. Softmax overflow yaptı çünkü `exp(100)` float32'nin temsil edebileceğinden daha büyük. Her ML framework'ü bunu iki satırlık bir trick ile halleder. Trick'in var olduğunu bilmiyordun.

Sayısal kararlılık teorik bir endişe değildir. Başarılı bir eğitim çalıştırması ile sessizce başarısız olan bir çalıştırma arasındaki farktır. Debug edeceğin her ciddi ML bug'ı sonunda floating point'e iner.

## Kavram

### IEEE 754: Bilgisayarlar Reel Sayıları Nasıl Saklar

Bilgisayarlar reel sayıları IEEE 754 standardını takip eden floating point değerleri olarak saklar. Bir float'ın üç parçası vardır: bir işaret bit'i, bir üs (exponent) ve bir mantis (significand).

```
Float32 layout (toplam 32 bit):
[1 işaret] [8 üs] [23 mantis]

Değer = (-1)^işaret * 2^(üs - 127) * 1.mantis
```

Mantis hassasiyeti belirler (kaç anlamlı basamak). Üs aralığı belirler (sayı ne kadar büyük veya küçük olabilir).

```
Format     Bit    Üs        Mantis    Ondalık basamak  Aralık (yaklaşık)
float64    64     11        52        ~15-16          +/- 1.8e308
float32    32     8         23        ~7-8            +/- 3.4e38
float16    16     5         10        ~3-4            +/- 65.504
bfloat16   16     8         7         ~2-3            +/- 3.4e38
```

float32 sana yaklaşık 7 ondalık basamak hassasiyet verir. Bu, 1.0000001 ve 1.0000002'yi ayırt edebileceği, ama 1.00000001 ve 1.00000002'yi ayırt edemeyeceği anlamına gelir. 7 basamaktan sonra her şey yuvarlama gürültüsüdür.

float16 sana yaklaşık 3 basamak verir. Temsil edebileceği en büyük sayı 65.504'tür. Logit'lerin, gradyanların ve aktivasyonların rutin olarak bunu aştığı ML için endişe verici şekilde küçüktür.

bfloat16, Google'ın float16'nın aralık problemine cevabıdır. float32 ile aynı 8 bit üse sahiptir (aynı aralık, 3.4e38'e kadar) ama yalnızca 7 mantis bit'i (float16'dan daha az hassasiyet). Sinir ağlarını eğitmek için aralık hassasiyetten daha önemlidir, dolayısıyla bfloat16 genelde kazanır.

### Neden 0.1 + 0.2 != 0.3

0.1 sayısı ikili floating point'te tam olarak temsil edilemez. Taban 2'de, tekrarlanan bir kesirdir:

```
İkili olarak 0.1 = 0.0001100110011001100110011... (sonsuza kadar tekrarlanan)
```

Float32 bunu 23 bit mantise kısaltır. Saklanan değer yaklaşık 0.100000001490116'dır. Benzer şekilde, 0.2 yaklaşık 0.200000002980232 olarak saklanır. Toplamları 0.3 değil 0.300000004470348'dir.

```
Python'da:
>>> 0.1 + 0.2
0.30000000000000004

>>> 0.1 + 0.2 == 0.3
False
```

Bu ML için önemlidir çünkü:

1. `if loss < threshold` gibi loss karşılaştırmaları yanlış cevaplar verebilir
2. Çok sayıda küçük değer biriktirmek (binlerce adım üzerinde gradyan güncellemeleri) gerçek toplamdan uzaklaşır
3. Float'ları `==` ile karşılaştırırsan checksum ve tekrarlanabilirlik testleri başarısız olur

Çözüm: float'ları asla `==` ile karşılaştırma. `abs(a - b) < epsilon` veya `math.isclose()` kullan.

### Catastrophic Cancellation

Neredeyse eşit iki floating point sayısını çıkardığında, anlamlı basamaklar iptal olur ve sana yuvarlama gürültüsünün baş basamaklara terfi ettiği bir sonuç kalır.

```
a = 1.0000001    (float32'de 1.00000011920929 olarak saklanır)
b = 1.0000000    (float32'de 1.00000000000000 olarak saklanır)

Gerçek fark:  0.0000001
Hesaplanan:   0.00000011920929

Göreli hata: %19.2
```

Tek bir çıkarmadan %19'luk göreli hata. ML'de bu şu durumlarda olur:

- Büyük ortalamalı veride varyans hesaplama: E[x] büyükken `E[x^2] - E[x]^2`
- Neredeyse eşit log-olasılıkları çıkarma
- Çok küçük epsilon ile sonlu fark gradyanları hesaplama

Çözüm: büyük, neredeyse eşit sayıları çıkarmaktan kaçınmak için formülleri yeniden düzenle. Varyans için Welford algoritmasını kullan veya önce veriyi merkezle. Log olasılıkları için, baştan sona log uzayında çalış.

### Overflow ve Underflow

Overflow, bir sonuç temsil edilemeyecek kadar büyük olduğunda olur. Underflow, çok küçük olduğunda olur (temsil edilebilir en küçük pozitif sayıdan sıfıra daha yakın).

```
Float32 sınırları:
  Maksimum:  3.4028235e+38
  Minimum pozitif (normal): 1.175e-38
  Minimum pozitif (denorm): 1.401e-45
  Overflow:  > 3.4e38 olan herhangi bir şey inf olur
  Underflow: < 1.4e-45 olan herhangi bir şey 0.0 olur
```

`exp()` fonksiyonu ML'deki birincil overflow kaynağıdır:

```
exp(88.7)  = 3.40e+38   (float32'ye zar zor sığar)
exp(89.0)  = inf         (overflow)
exp(-87.3) = 1.18e-38   (underflow'un hemen üstünde)
exp(-104)  = 0.0         (sıfıra underflow)
```

`log()` fonksiyonu diğer yöne çarpar:

```
log(0.0)   = -inf
log(-1.0)  = nan
log(1e-45) = -103.3      (iyi)
log(1e-46) = -inf        (girdi 0'a underflow oldu, sonra log(0) = -inf)
```

ML'de `exp()` softmax, sigmoid ve olasılık hesaplamalarında görünür. `log()` cross-entropy, log-likelihood'larda ve KL diverjansında görünür. `log(exp(x))` kombinasyonu doğru trick'ler olmadan bir mayın tarlasıdır.

### Log-Sum-Exp Trick'i

`log(sum(exp(x_i)))`'i doğrudan hesaplamak sayısal olarak tehlikelidir. Herhangi bir `x_i` büyükse, `exp(x_i)` overflow yapar. Tüm `x_i`'ler çok negatifse, her `exp(x_i)` sıfıra underflow yapar ve `log(0)` `-inf`'tir.

Trick: üstel almadan önce maksimum değeri çıkar.

```
log(sum(exp(x_i))) = max(x) + log(sum(exp(x_i - max(x))))
```

Bu neden çalışır: `max(x)` çıkarıldıktan sonra, en büyük üs `exp(0) = 1`'dir. Overflow mümkün değildir. Toplamdaki en az bir terim 1'dir, dolayısıyla toplam en az 1'dir ve `log(1) = 0`'dır. `-inf`'e underflow mümkün değildir.

Kanıt:

```
log(sum(exp(x_i)))
= log(sum(exp(x_i - c + c)))                    (c ekle ve çıkar)
= log(sum(exp(x_i - c) * exp(c)))               (exp(a+b) = exp(a)*exp(b))
= log(exp(c) * sum(exp(x_i - c)))               (exp(c)'yi dışarı çarpan olarak çıkar)
= c + log(sum(exp(x_i - c)))                    (log(a*b) = log(a) + log(b))
```

`c = max(x)` ayarla, overflow elenir.

Bu trick ML'de her yerde görünür:
- Softmax normalizasyonu
- Cross-entropy loss hesaplaması
- Sıralı modellerde log-olasılık toplamı
- Gauss karışımı
- Variational inference

### Softmax Neden Max-Subtraction Trick'ine İhtiyaç Duyar

Softmax logit'leri olasılıklara çevirir:

```
softmax(x_i) = exp(x_i) / sum(exp(x_j))
```

Trick olmadan, [100, 101, 102] logit'leri overflow'a sebep olur:

```
exp(100) = 2.69e43
exp(101) = 7.31e43
exp(102) = 1.99e44
toplam   = 2.99e44

Bunlar float32'yi (maks ~3.4e38) overflow yapıyor mu? Hayır, 2.69e43 < 3.4e38? Aslında:
exp(88.7) zaten float32 sınırında.
exp(100) float32'de inf'tir.
```

Trick ile, max(x) = 102'yi çıkar:

```
exp(100 - 102) = exp(-2) = 0.135
exp(101 - 102) = exp(-1) = 0.368
exp(102 - 102) = exp(0)  = 1.000
toplam = 1.503

softmax = [0.090, 0.245, 0.665]
```

Olasılıklar aynıdır. Hesaplama güvenlidir. Bu bir optimizasyon değildir. Doğruluk için bir gerekliliktir.

### NaN ve Inf: Tespit ve Önleme

`nan` (Not a Number) ve `inf` (sonsuz) hesaplama boyunca viral olarak yayılır. Gradient güncellemesindeki tek bir `nan` weight'i `nan` yapar, bu da sonraki her çıktıyı `nan` yapar. Eğitim bir adımda ölür.

`inf` nasıl ortaya çıkar:
- Büyük bir pozitif sayının `exp()`'i
- Sıfıra bölme: `1.0 / 0.0`
- Birikimlerde `float32` overflow

`nan` nasıl ortaya çıkar:
- `0.0 / 0.0`
- `inf - inf`
- `inf * 0`
- Negatif bir sayının `sqrt()`'i
- Negatif bir sayının `log()`'u
- Mevcut bir `nan`'i içeren herhangi bir aritmetik

Tespit:

```python
import math

math.isnan(x)       # x nan ise True
math.isinf(x)       # x +inf veya -inf ise True
math.isfinite(x)    # x ne nan ne de inf ise True
```

Önleme stratejileri:

1. `exp()` girdilerini clamp et: `exp(clamp(x, -80, 80))`
2. Paydalara epsilon ekle: `x / (y + 1e-8)`
3. `log()` içine epsilon ekle: `log(x + 1e-8)`
4. Kararlı implementasyonlar kullan (log-sum-exp, kararlı softmax)
5. Weight patlamasını önlemek için gradient clipping
6. Debug sırasında her forward pass sonrası `nan`/`inf` kontrolü yap

### Sayısal Gradient Checking

Analitik gradyanların (backpropagation'dan) bug'ları olabilir. Sayısal gradient checking, gradyanları sonlu farklarla hesaplayarak onları doğrular.

Merkezi fark formülü:

```
df/dx ~= (f(x + h) - f(x - h)) / (2h)
```

Bu O(h^2) doğruluktadır, sadece O(h) olan forward fark `(f(x+h) - f(x)) / h`'tan çok daha iyidir.

h seçimi: çok büyükse yaklaşım yanlıştır. Çok küçükse catastrophic cancellation cevabı yok eder. `h = 1e-5` ile `1e-7` arası tipiktir.

Kontrol: analitik ve sayısal gradyanlar arasındaki göreli farkı hesapla.

```
relative_error = |grad_analytical - grad_numerical| / max(|grad_analytical|, |grad_numerical|, 1e-8)
```

Pratik kurallar:
- relative_error < 1e-7: mükemmel, gradyan doğru
- relative_error < 1e-5: kabul edilebilir, muhtemelen doğru
- relative_error > 1e-3: bir şeyler yanlış
- relative_error > 1: gradyan tamamen yanlış

Yeni bir katman veya loss fonksiyonu implemente ederken her zaman gradyanları kontrol et. PyTorch bunun için `torch.autograd.gradcheck()` sağlar.

### Mixed Precision Training

Modern GPU'ların float16 matris çarpımlarını float32'den 2-8 kat daha hızlı hesaplayan özel donanım (Tensor Core'lar) vardır. Mixed precision training bunu sömürür:

```
1. Weight'lerin float32 master kopyasını tut
2. float16'da forward pass (hızlı)
3. float32'de loss hesapla (overflow'u önler)
4. float16'da backward pass (hızlı)
5. Gradyanları float32'ye ölçekle
6. float32 master weight'leri güncelle
```

Saf float16 eğitiminin sorunu: gradyanlar genelde çok küçüktür (1e-8 veya daha küçük). Float16 ~6e-8'in altında her şeyi sıfıra underflow yapar. Modelin öğrenmeyi durdurur çünkü tüm gradyan güncellemeleri sıfırdır.

Çözüm loss scaling'dir:

```
1. Loss'u büyük bir ölçek faktörüyle çarp (örn. 1024)
2. Backward pass (loss * 1024)'ün gradyanlarını hesaplar
3. Tüm gradyanlar 1024 kat daha büyük (float16 underflow'unun üstüne itildi)
4. Weight'leri güncellemeden önce gradyanları 1024'e böl
5. Net etki: aynı güncelleme, ama underflow yok
```

Dinamik loss scaling, ölçek faktörünü otomatik olarak ayarlar. Büyük bir değerle başla (65536). Gradyanlar `inf`'e overflow yaparsa, onu yarıya indir. N adım overflow olmadan geçerse, ikiye katla.

### bfloat16 vs float16: Eğitim için Neden bfloat16 Kazanır

```
float16:   [1 işaret] [5 üs]   [10 mantis]
bfloat16:  [1 işaret] [8 üs]   [7 mantis]
```

float16'nın daha fazla hassasiyeti vardır (10 mantis bit'i vs 7) ama sınırlı aralık (maks ~65.504). bfloat16'nın daha az hassasiyeti ama float32 ile aynı aralığı vardır (maks ~3.4e38).

Sinir ağı eğitimi için:

- Aktivasyonlar ve logit'ler eğitim spike'larında düzenli olarak 65.504'ü aşar. float16 overflow yapar; bfloat16 halleder.
- Loss scaling float16 ile gereklidir ama bfloat16 ile genelde gereksizdir çünkü aralığı gradyan büyüklük spektrumunu kapsar.
- bfloat16, float32'nin basit bir kısaltmasıdır: mantisin alt 16 bit'ini at. Dönüşüm önemsizdir ve üste'de kayıpsızdır.

float16 değerlerin sınırlı olduğu ve hassasiyetin daha önemli olduğu inference için tercih edilir. bfloat16, aralığın daha önemli olduğu eğitim için tercih edilir. Bu yüzden TPU'lar ve modern NVIDIA GPU'ları (A100, H100) yerel bfloat16 desteğine sahiptir.

### Gradient Clipping

Patlayan gradyanlar, gradyanlar birçok katman boyunca üstel olarak büyüdüğünde olur (RNN'lerde, derin ağlarda ve transformer'larda yaygındır). Tek bir büyük gradyan tüm weight'leri tek adımda bozabilir.

İki tür clipping:

**Değere göre clip:** her gradyan elemanını bağımsız olarak clamp et.

```
grad = clamp(grad, -max_val, max_val)
```

Basit ama gradyan vektörünün yönünü değiştirebilir.

**Norm'a göre clip:** norm'u bir eşiği aşmayacak şekilde tüm gradyan vektörünü ölçekle.

```
if ||grad|| > max_norm:
    grad = grad * (max_norm / ||grad||)
```

Gradyanın yönünü korur. `torch.nn.utils.clip_grad_norm_()`'in yaptığı budur. Standart seçimdir.

Tipik değerler: transformer'lar için `max_norm=1.0`, RL için `max_norm=0.5`, daha basit ağlar için `max_norm=5.0`.

Gradient clipping bir hack değildir. Bir güvenlik mekanizmasıdır. Onsuz, tek bir aykırı batch haftalarca süren eğitimi mahvedecek kadar büyük bir gradyan üretebilir.

### Sayısal Stabilizer Olarak Normalizasyon Katmanları

Batch normalization, layer normalization ve RMS normalization genellikle eğitimin yakınsamasına yardımcı olan regularizer'lar olarak sunulur. Bunlar aynı zamanda sayısal stabilizer'lardır.

Normalizasyon olmadan aktivasyonlar katmanlar boyunca üstel olarak büyüyebilir veya küçülebilir:

```
Katman 1: [0, 1] aralığında değerler
Katman 5: [0, 100] aralığında değerler
Katman 10: [0, 10.000] aralığında değerler
Katman 50: [0, inf] aralığında değerler
```

Normalizasyon her katmanda aktivasyonları yeniden merkezler ve ölçekler:

```
LayerNorm(x) = (x - mean(x)) / (std(x) + epsilon) * gamma + beta
```

`epsilon` (tipik olarak 1e-5) tüm aktivasyonlar aynı olduğunda sıfıra bölmeyi önler. Öğrenilen parametreler `gamma` ve `beta` ağın ihtiyaç duyduğu herhangi bir ölçeği geri yüklemesine izin verir.

Bu, değerleri ağ boyunca sayısal olarak güvenli bir aralıkta tutar, hem forward pass'te overflow'u hem de backward pass'te gradient patlamasını önler.

### Yaygın ML Sayısal Bug'ları

**Bug: Birkaç epoch sonra loss NaN.**
Sebep: logit'ler çok büyüdü, softmax overflow yaptı. Veya learning rate çok yüksek ve weight'ler diverge etti.
Çözüm: kararlı softmax kullan (max çıkarma), learning rate'i azalt, gradient clipping ekle.

**Bug: Loss log(num_classes)'ta takıldı.**
Sebep: model çıktıları neredeyse uniform olasılıklar. Genelde gradyanların yok olduğu veya modelin hiç öğrenmediği anlamına gelir.
Çözüm: veri label'larının doğru olduğunu kontrol et, loss fonksiyonunu doğrula, ölü ReLU'ları kontrol et.

**Bug: Validation doğruluğu beklenenden %1-3 daha düşük.**
Sebep: uygun loss scaling olmadan mixed precision. Gradient underflow küçük güncellemeleri sessizce sıfırlar.
Çözüm: dinamik loss scaling'i etkinleştir veya bfloat16'ya geç.

**Bug: Bazı katmanlar için gradient norm'ları 0.0.**
Sebep: ölü ReLU nöronları (tüm girdiler negatif) veya float16 underflow.
Çözüm: LeakyReLU veya GELU kullan, gradient scaling kullan, weight initialization'ı kontrol et.

**Bug: Model bir GPU'da çalışıyor ama başka bir GPU'da farklı sonuçlar veriyor.**
Sebep: deterministik olmayan floating point birikim sırası. GPU paralel reduction'ları farklı donanımda farklı sıralarda toplar ve floating point toplama birleşimli değildir.
Çözüm: küçük farkları (1e-6) kabul et veya `torch.use_deterministic_algorithms(True)` ayarla ve hız cezasını kabul et.

**Bug: Loss hesaplamasında `exp()` `inf` döndürüyor.**
Sebep: ham logit'ler max-subtraction trick'i olmadan `exp()`'e geçirildi.
Çözüm: içeride log-sum-exp uygulayan `torch.nn.functional.log_softmax()` kullan.

**Bug: float32'den float16'ya geçtikten sonra eğitim diverge ediyor.**
Sebep: float16, 6e-8'in altındaki gradient büyüklüklerini veya 65.504'ün üstündeki aktivasyonları temsil edemez.
Çözüm: loss scaling (AMP) ile mixed precision kullan veya yerine bfloat16 kullan.

## İnşa Et

### Adım 1: Floating point hassasiyet sınırlarını göster

```python
print("=== Floating Point Hassasiyeti ===")
print(f"0.1 + 0.2 = {0.1 + 0.2}")
print(f"0.1 + 0.2 == 0.3? {0.1 + 0.2 == 0.3}")
print(f"Fark: {(0.1 + 0.2) - 0.3:.2e}")
```

### Adım 2: Naif vs kararlı softmax implemente et

```python
import math

def softmax_naive(logits):
    exps = [math.exp(z) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]

def softmax_stable(logits):
    max_logit = max(logits)
    exps = [math.exp(z - max_logit) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]

safe_logits = [2.0, 1.0, 0.1]
print(f"Naif:    {softmax_naive(safe_logits)}")
print(f"Kararlı: {softmax_stable(safe_logits)}")

dangerous_logits = [100.0, 101.0, 102.0]
print(f"Kararlı: {softmax_stable(dangerous_logits)}")
# softmax_naive(dangerous_logits) [nan, nan, nan] döndürür
```

### Adım 3: Kararlı log-sum-exp implemente et

```python
def logsumexp_naive(values):
    return math.log(sum(math.exp(v) for v in values))

def logsumexp_stable(values):
    c = max(values)
    return c + math.log(sum(math.exp(v - c) for v in values))

safe = [1.0, 2.0, 3.0]
print(f"Naif:    {logsumexp_naive(safe):.6f}")
print(f"Kararlı: {logsumexp_stable(safe):.6f}")

large = [500.0, 501.0, 502.0]
print(f"Kararlı: {logsumexp_stable(large):.6f}")
# logsumexp_naive(large) inf döndürür
```

### Adım 4: Kararlı cross-entropy implemente et

```python
def cross_entropy_naive(true_class, logits):
    probs = softmax_naive(logits)
    return -math.log(probs[true_class])

def cross_entropy_stable(true_class, logits):
    max_logit = max(logits)
    shifted = [z - max_logit for z in logits]
    log_sum_exp = math.log(sum(math.exp(s) for s in shifted))
    log_prob = shifted[true_class] - log_sum_exp
    return -log_prob

logits = [2.0, 5.0, 1.0]
true_class = 1
print(f"Naif:    {cross_entropy_naive(true_class, logits):.6f}")
print(f"Kararlı: {cross_entropy_stable(true_class, logits):.6f}")
```

### Adım 5: Gradient checking

```python
def numerical_gradient(f, x, h=1e-5):
    grad = []
    for i in range(len(x)):
        x_plus = x[:]
        x_minus = x[:]
        x_plus[i] += h
        x_minus[i] -= h
        grad.append((f(x_plus) - f(x_minus)) / (2 * h))
    return grad

def check_gradient(analytical, numerical, tolerance=1e-5):
    for i, (a, n) in enumerate(zip(analytical, numerical)):
        denom = max(abs(a), abs(n), 1e-8)
        rel_error = abs(a - n) / denom
        status = "OK" if rel_error < tolerance else "FAIL"
        print(f"  param {i}: analitik={a:.8f} sayısal={n:.8f} "
              f"rel_error={rel_error:.2e} [{status}]")

def f(params):
    x, y = params
    return x**2 + 3*x*y + y**3

def f_grad(params):
    x, y = params
    return [2*x + 3*y, 3*x + 3*y**2]

point = [2.0, 1.0]
analytical = f_grad(point)
numerical = numerical_gradient(f, point)
check_gradient(analytical, numerical)
```

## Kullan

### Mixed precision simülasyonu

```python
import struct

def float32_to_float16_round(x):
    packed = struct.pack('f', x)
    f32 = struct.unpack('f', packed)[0]
    packed16 = struct.pack('e', f32)
    return struct.unpack('e', packed16)[0]

def simulate_bfloat16(x):
    packed = struct.pack('f', x)
    as_int = int.from_bytes(packed, 'little')
    truncated = as_int & 0xFFFF0000
    repacked = truncated.to_bytes(4, 'little')
    return struct.unpack('f', repacked)[0]
```

### Gradient clipping

```python
def clip_by_norm(gradients, max_norm):
    total_norm = math.sqrt(sum(g**2 for g in gradients))
    if total_norm > max_norm:
        scale = max_norm / total_norm
        return [g * scale for g in gradients]
    return gradients

grads = [10.0, 20.0, 30.0]
clipped = clip_by_norm(grads, max_norm=5.0)
print(f"Orijinal norm: {math.sqrt(sum(g**2 for g in grads)):.2f}")
print(f"Kırpılmış norm:  {math.sqrt(sum(g**2 for g in clipped)):.2f}")
print(f"Yön korundu: {[c/clipped[0] for c in clipped]} == {[g/grads[0] for g in grads]}")
```

### NaN/Inf tespiti

```python
def check_tensor(name, values):
    has_nan = any(math.isnan(v) for v in values)
    has_inf = any(math.isinf(v) for v in values)
    if has_nan or has_inf:
        print(f"UYARI {name}: nan={has_nan} inf={has_inf}")
        return False
    return True

check_tensor("iyi", [1.0, 2.0, 3.0])
check_tensor("kötü",  [1.0, float('nan'), 3.0])
check_tensor("çirkin", [1.0, float('inf'), 3.0])
```

Gösterilen tüm uç durumlarla birlikte tam implementasyonlar için `code/numerical.py`'a bak.

## Yayınla

Bu ders şunları üretir:
- Kararlı softmax, log-sum-exp, cross-entropy, gradient checking ve mixed precision simülasyonu içeren `code/numerical.py`
- Eğitimde NaN/Inf ve sayısal sorunları teşhis etmek için `outputs/prompt-numerical-debugger.md`

Bu kararlı implementasyonlar Faz 3'te eğitim döngüsünü inşa ederken ve Faz 4'te attention mekanizmalarını implemente ederken tekrar görünür.

## Alıştırmalar

1. **Catastrophic cancellation.** [1000000.0, 1000001.0, 1000002.0]'nin varyansını float32'de naif formül `E[x^2] - E[x]^2` kullanarak hesapla. Sonra Welford'un online algoritmasını kullanarak hesapla. Hataları gerçek varyansa (0.6667) karşı karşılaştır.

2. **Hassasiyet avı.** `1.0 + x == 1.0` olacak şekilde Python'da en küçük pozitif float32 değeri `x`'i bul. Bu makine epsilon'udur. `numpy.finfo(numpy.float32).eps` ile eşleştiğini doğrula.

3. **Log-sum-exp uç durumları.** `logsumexp_stable` fonksiyonunu şu durumlarla test et: (a) tüm değerler eşit, (b) bir değer geri kalanından çok daha büyük, (c) tüm değerler çok negatif (-1000). Naif versiyonun başarısız olduğu yerlerde doğru sonuçlar verdiğini doğrula.

4. **Bir sinir ağı katmanını gradient checking.** Tek bir lineer katman `y = Wx + b` ve onun analitik backward pass'ini implemente et. 3x2 bir weight matrisi için doğruluğu doğrulamak için `numerical_gradient` kullan.

5. **Loss scaling deneyi.** float16 ile eğitim simüle et: [1e-9, 1e-3] aralığında rastgele gradyanlar oluştur, float16'ya çevir ve hangi kesrinin sıfır olduğunu ölç. Sonra loss scaling uygula (1024 ile çarp), float16'ya çevir, geri ölçekle ve sıfır kesrini tekrar ölç.

## Anahtar Terimler

| Terim | İnsanlar ne der | Aslında ne demek |
|------|----------------|----------------------|
| IEEE 754 | "Float standardı" | İkili floating point formatlarını, yuvarlama kurallarını ve özel değerleri (inf, nan) tanımlayan uluslararası standart. Her modern CPU ve GPU bunu uygular. |
| Makine epsilon | "Hassasiyet sınırı" | Belirli bir float formatında 1.0 + e != 1.0 olacak şekilde en küçük e değeri. float32 için yaklaşık 1.19e-7'dir. |
| Catastrophic cancellation | "Çıkarmadan hassasiyet kaybı" | Neredeyse eşit floating point sayıları çıkarırken, anlamlı basamaklar iptal olur ve yuvarlama gürültüsü sonuca hakim olur. |
| Overflow | "Sayı çok büyük" | Bir sonuç temsil edilebilir maksimum değeri aşar ve inf olur. exp(89) float32'yi overflow yapar. |
| Underflow | "Sayı çok küçük" | Bir sonuç temsil edilebilir en küçük pozitif sayıdan sıfıra daha yakındır ve 0.0 olur. exp(-104) float32'yi underflow yapar. |
| Log-sum-exp trick'i | "Önce max'ı çıkar" | Overflow ve underflow'u önlemek için exp(max(x))'i dışarı çarpan olarak çıkararak log(sum(exp(x)))'i hesaplama. Softmax, cross-entropy ve log-olasılık matematiğinde kullanılır. |
| Kararlı softmax | "Patlayan softmax değil" | Üstel almadan önce max(logit'ler)'i çıkarmak. Sayısal olarak aynı sonuç, overflow mümkün değil. |
| Gradient checking | "Backprop'unu doğrula" | İmplementasyon bug'larını yakalamak için backpropagation'dan gelen analitik gradyanları sonlu farklardan gelen sayısal gradyanlara karşı karşılaştırma. |
| Mixed precision | "Float16 forward, float32 backward" | Hız-kritik işlemler için daha düşük hassasiyetli float'lar ve sayısal olarak duyarlı işlemler için daha yüksek hassasiyetli float'lar kullanmak. Tipik hızlanma 2-3x. |
| Loss scaling | "Gradient underflow'u önle" | Gradyanların float16'nın temsil edilebilir aralığında kalması için backprop'tan önce loss'u büyük bir sabitle çarpmak, sonra weight güncellemelerinden önce aynı sabite bölmek. |
| bfloat16 | "Brain floating point" | Google'ın 8 üs bit'i (float32 ile aynı aralık) ve 7 mantis bit'i (float16'dan daha az hassasiyet) olan 16 bit formatı. Eğitim için tercih edilir. |
| Gradient clipping | "Gradient norm'unu sınırla" | Gradient vektörünü norm'u bir eşiği aşmayacak şekilde ölçekleme. Patlayan gradyanların weight'leri mahvetmesini önler. |
| NaN | "Not a Number" | Tanımsız işlemlerden (0/0, inf-inf, sqrt(-1)) özel float değeri. Sonraki tüm aritmetik boyunca yayılır. |
| Inf | "Sonsuz" | Overflow veya sıfıra bölmeden özel float değeri. NaN üretmek için birleşebilir (inf - inf, inf * 0). |
| Sayısal gradyan | "Brute force türev" | f(x+h) ve f(x-h)'yi değerlendirip 2h'a bölerek bir türevi yaklaşıklamak. Yavaş ama doğrulama için güvenilir. |

## İleri Okuma

- [What Every Computer Scientist Should Know About Floating-Point Arithmetic (Goldberg 1991)](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) -- kesin referans, yoğun ama tam
- [Mixed Precision Training (Micikevicius et al., 2018)](https://arxiv.org/abs/1710.03740) -- float16 eğitimi için loss scaling'i tanıtan NVIDIA makalesi
- [AMP: Automatic Mixed Precision (PyTorch docs)](https://pytorch.org/docs/stable/amp.html) -- PyTorch'ta mixed precision için pratik rehber
- [bfloat16 format (Google Cloud TPU docs)](https://cloud.google.com/tpu/docs/bfloat16) -- Google'ın TPU'lar için bu formatı neden seçtiği
- [Kahan Summation (Wikipedia)](https://en.wikipedia.org/wiki/Kahan_summation_algorithm) -- floating point toplamalarda yuvarlama hatasını azaltmak için algoritma
