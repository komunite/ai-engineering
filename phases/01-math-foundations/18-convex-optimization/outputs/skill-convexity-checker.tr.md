---
name: skill-convexity-checker
description: Bir optimizasyon probleminin konveks olup olmadığını belirle ve doğru solver'ı seç
version: 1.0.0
phase: 1
lesson: 18
tags: [optimization, convexity, solvers]
---

# Konvekslik Kontrolcüsü

Bir optimizasyon probleminin konveks olup olmadığını nasıl doğrularsın ve cevabıyla ne yaparsın.

## Karar Kontrol Listesi

1. Amaç fonksiyonu konveks mi? (Hessian'ın pozitif yarı-tanımlı olduğunu kontrol et ya da kompozisyon kurallarını kullan.)
2. Tüm eşitsizlik kısıtları g_i(x) <= 0 formunda mı ve her g_i konveks mi?
3. Tüm eşitlik kısıtları afin (lineer) mi?
4. Üçü de evetse problem konvekstir. Yakınsama garantili bir konveks solver kullan.
5. Hayırsa, problem non-convex. SGD/Adam kullan ve lokal optimumları kabul et.

## Bir fonksiyonun konveksliğini nasıl test edersin

| Test | Hangi fonksiyona | Yöntem |
|---|---|---|
| İkinci türev >= 0 | Skaler fonksiyonlar f(x) | f''(x) hesapla. Her x için f''(x) >= 0 ise konveks. |
| Hessian PSD | Çok değişkenli fonksiyonlar f(x) | H(x) hesapla. Her yerde tüm eigenvalue'lar >= 0 ise konveks. |
| Tanım testi | Herhangi bir fonksiyon | Örneklenmiş x, y, t için f(tx + (1-t)y) <= t*f(x) + (1-t)*f(y) kontrol et. |
| Kompozisyon kuralları | Bileşik fonksiyonlar | Aşağıdaki kompozisyon tablosuna bak. |
| Bir doğruya kısıtlama | Çok değişkenli f | f konvekstir iff her x, v için g(t) = f(x + tv) t cinsinden konvekstir. |

## Kompozisyon kuralları (konveksliği koruyan)

| İşlem | Sonuç |
|---|---|
| f + g (ikisi de konveks) | Konveks |
| c * f (c > 0, f konveks) | Konveks |
| max(f, g) (ikisi de konveks) | Konveks |
| f(Ax + b), f konveks | Konveks |
| g(f(x)), g konveks azalmayan ve f konveks | Konveks |
| g(f(x)), g konveks artmayan ve f konkav | Konveks |
| Konveks fonksiyonların toplamı | Konveks |
| Konveks fonksiyonların noktasal supremum'u | Konveks |

## Yaygın ML amaçları: konveks mi, değil mi?

| Amaç | Konveks? | Neden |
|---|---|---|
| MSE: (1/n) sum(y - Xw)^2 | Evet | w cinsinden kuadratik, Hessian = (2/n) X^T X PSD |
| Logistic loss: sum(log(1 + exp(-y_i * w^T x_i))) | Evet | Konveks fonksiyonların toplamı (log-sum-exp ailesi) |
| Hinge loss: sum(max(0, 1 - y_i * w^T x_i)) | Evet | Konveks (lineer) fonksiyonların max'ı |
| L2 regularization: lambda * \|\|w\|\|^2 | Evet | Kuadratik, Hessian = 2*lambda*I |
| L1 regularization: lambda * \|\|w\|\|_1 | Evet | Mutlak değerlerin toplamı (konveks ama türevlenebilir değil) |
| Ridge regression: MSE + L2 | Evet | İki konveks fonksiyonun toplamı |
| LASSO: MSE + L1 | Evet | İki konveks fonksiyonun toplamı |
| Elastic net: MSE + L1 + L2 | Evet | Konveks fonksiyonların toplamı |
| SVM (primal): hinge + L2 | Evet | Konveks fonksiyonların toplamı |
| Softmax ile cross-entropy | Evet (logit'lerde) | Log-sum-exp konvekstir |
| Sinir ağı (herhangi bir loss) | Hayır | Lineer olmayan aktivasyonlar non-convex kompozisyon yaratır |
| k-means amacı | Hayır | Discrete atama adımı |
| Matris faktorizasyonu: \|\|X - UV^T\|\|^2 | Hayır | U ve V'de bilinear |
| GAN loss'u | Hayır | Minimax, generator'da non-convex |
| Contrastive loss (InfoNCE) | Hayır | Negatif sample'larla üstellerin oranının logu |

## Konveksliğe göre solver seçimi

| Problem tipi | Solver | Yakınsama garantisi |
|---|---|---|
| Konveks, smooth, kısıtsız | Gradient descent | Global minimuma O(1/k) |
| Konveks, smooth, kısıtsız | L-BFGS | Global minimuma superlinear |
| Konveks, smooth, kısıtsız | Newton yöntemi | Minimum yakınında kuadratik (Hessian işlenebilirse) |
| Konveks, smooth, kısıtlı | Interior point yöntemi | Polynomial zaman |
| Konveks, non-smooth (L1) | Proximal gradient / ISTA | Global minimuma O(1/k) |
| Konveks, non-smooth (L1) | ADMM | Esnek, kısıtları işler |
| Konveks, kuadratik | Conjugate gradient | n adımda tam çözüm |
| Non-convex, smooth | SGD / Adam | Lokal minimuma yakınsar |
| Non-convex, smooth | SGD + restart | Ortalamada daha iyi lokal minimum |
| Non-convex, smooth | Aşırı parametre + SGD | Düz minima, iyi genelleştirme |

## Yaygın hatalar

- Loss fonksiyonu konveks diye problemin konveks olduğunu varsaymak. Loss, optimize ettiğin parametrelerde konveks olmalı. Cross-entropy logit'lerde konvekstir, ama girdiden logit'lere kadar olan tam sinir ağı eşlemesi non-convex'tir.
- Non-convex problemde Newton yöntemi kullanmak. Hessian negatif eigenvalue'lara sahip olabilir, bu da Newton'un minimum yerine saddle point ya da maximum'a doğru hareket etmesine neden olur.
- L1 regularization'ın objective'i sıfırda non-differentiable yaptığını unutmak. Standart gradient descent iyi çalışmaz. Proximal gradient descent ya da subgradient yöntemleri kullan.
- A^T A oluşturarak condition number'ı karelemek. Least-squares çözmen gerekiyor ve A kötü şartlıysa, normal denklemler yerine QR ya da SVD kullan.
- Kontrol etmeden problemi non-convex ilan etmek. Birçok ML problemi (lineer modeller, SVM, logistic regression) konvekstir ve daha güçlü solver'lardan yararlanır.

## Hızlı test: problemim konveks mi?

```
1. Amacı yaz: f(w) minimize et, kısıtlara tabi
2. f(w)'deki her terim için:
   - PSD matrisli kuadratik mi? -> Konveks
   - Norm mu? -> Konveks
   - Log-sum-exp mi? -> Konveks
   - w'yi lineer olmayan biçimde içeriyor mu (sigmoid(w), w1*w2)? -> Muhtemelen non-convex
3. Tüm kısıtlar lineer ya da konveks eşitsizlikler mi?
4. TÜM terimler konveks ve kısıtlar konveks/lineer ise -> problem konvekstir
5. HERHANGİ bir terim non-convex ise -> problem non-convex'tir
```
