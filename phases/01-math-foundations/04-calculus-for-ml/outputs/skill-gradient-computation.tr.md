---
name: skill-gradient-computation
description: Yaygın ML loss fonksiyonlarının gradientlerini hesapla ve doğru türev yaklaşımını seç
version: 1.0.0
phase: 1
lesson: 4
tags: [calculus, gradients, backpropagation]
---

# ML için Gradient Hesaplama

Sinir ağlarında kullanılan loss fonksiyonları, aktivasyon fonksiyonları ve katman operasyonlarının gradientlerini hesaplamak için pratik referans.

## Karar Kontrol Listesi

1. Fonksiyon basit primitive'lerden mi oluşuyor (üs, exp, log, trig)? Analitik türevleri ve zincir kuralını kullan.
2. Fonksiyon özel ya da kara kutu bir operasyon mu? Sayısal türev kullan: `(f(x+h) - f(x-h)) / (2h)` ve h = 1e-7.
3. Fonksiyon PyTorch/JAX'taki tensor operasyonlarından mı oluşuyor? Autograd halletsin. Sayısal kontrolle doğrula.
4. Skaler bir loss'un ağırlık matrisine göre gradientini mi istiyorsun? Zincir kuralını computation graph üzerinden node-node uygula.
5. Türevlenemez bir operasyon var mı (argmax, yuvarlama, sampling)? Straight-through estimator ya da reparametrizasyon trick'i kullan.

## Hangi yaklaşımı ne zaman kullanmalı

| Yaklaşım | Ne zaman kullanılır | Maliyet |
|---|---|---|
| Analitik (elle türev) | Basit fonksiyonlar, autograd çıktısını doğrulamak | Runtime'da bedava |
| Sayısal (sonlu farklar) | Debug, gradient kontrolü, kara kutu fonksiyonlar | n parametre için 2n forward pass |
| Otomatik türev (autograd) | Herhangi bir türevlenebilir computation graph (default) | Bir backward pass |
| Sembolik (SymPy, Mathematica) | Makaleler için kapalı form gradient türetmek | Sadece compile time |

## Hızlı referans: yaygın türevler

| Fonksiyon | f(x) | f'(x) | ML bağlamı |
|---|---|---|---|
| MSE loss | (1/n) sum(y_hat - y)^2 | (2/n)(y_hat - y) | Regresyon |
| Cross-entropy (binary) | -(y log(p) + (1-y) log(1-p)) | p - y (sigmoid sonrası) | Binary sınıflandırma |
| Cross-entropy (multi) | -log(p_true_class) | p - one_hot(y) (softmax sonrası) | Çok sınıflı sınıflandırma |
| Sigmoid | 1 / (1 + e^(-x)) | sigma(x) * (1 - sigma(x)) | Output gate'ler, binary çıktı |
| Tanh | (e^x - e^(-x)) / (e^x + e^(-x)) | 1 - tanh(x)^2 | Hidden aktivasyonlar (eski) |
| ReLU | max(0, x) | x > 0 ise 1, x < 0 ise 0 | Default hidden aktivasyon |
| Leaky ReLU | max(0.01x, x) | x > 0 ise 1, x < 0 ise 0.01 | Ölü nöronlardan kaçınma |
| GELU | x * Phi(x) | Phi(x) + x * phi(x) | Transformer'lar |
| Softmax_i | e^(x_i) / sum(e^(x_j)) | i=j için s_i(1 - s_i), i!=j için -s_i*s_j | Output layer (Jacobian) |
| Log-softmax | x_i - log(sum(e^(x_j))) | i. girdi için 1 - softmax(x_i) | Sayısal olarak kararlı CE |
| Linear layer | y = Wx + b | dL/dW = dL/dy * x^T, dL/db = dL/dy | Her katman |
| L2 regularization | lambda * sum(w^2) | 2 * lambda * w | Weight decay |
| L1 regularization | lambda * sum(\|w\|) | lambda * sign(w) | Seyreklik (sparsity) |

## Yaygın hatalar

- Batch ortalamalı loss'larda (MSE, cross-entropy) 1/n faktörünü unutmak. Gradient batch size ile ölçeklenir.
- Softmax gradientini vektör olarak hesaplamak, halbuki o aslında bir Jacobian matristir. Cross-entropy + softmax birlikteyse gradient (p - y)'ye sadeleşir ve tam Jacobian'dan kaçınılır.
- Zincir kuralını yanlış sırada uygulamak. Loss'tan geriye doğru çalış: dL/dW = dL/dy * dy/dW.
- Sayısal türevde çok büyük (h = 0.1) ya da çok küçük (h = 1e-15) h kullanmak. float64 için h = 1e-7'de kal.
- ReLU'nun tam x = 0'da tanımsız gradienti olduğunu unutmak. Pratikte 0 ya da 0.5'e ayarla.

## Gradient kontrol tarifi

```
Her w parametresi için:
  numeric_grad = (loss(w + h) - loss(w - h)) / (2h)
  auto_grad = backward pass değeri
  relative_error = |numeric - auto| / max(|numeric|, |auto|, 1e-8)
  assert relative_error < 1e-5
```

1e-3 üzerindeki relatif hata bir şeyin yanlış olduğu anlamına gelir. 1e-5 ile 1e-3 arası, araştır.
