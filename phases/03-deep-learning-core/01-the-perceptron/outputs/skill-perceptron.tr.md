---
name: skill-perceptron
description: Perceptron pattern'ini anla ve ne zaman tek katmanlı, ne zaman çok katmanlı mimariyi kullanacağına karar ver
version: 1.0.0
phase: 3
lesson: 1
tags: [perceptron, neural-networks, classification, deep-learning]
---

# Perceptron Pattern'i

Bir perceptron girdilerin ağırlıklı toplamını ve bir bias'ı hesaplar, ardından bir step fonksiyonu uygulayarak ikili (binary) bir çıktı üretir. Sinir ağlarının temel birimidir.

```
output = step(w1*x1 + w2*x2 + ... + wn*xn + bias)
```

## Tek bir perceptron yeterli olduğunda

- Problem doğrusal ayrılabilir (linearly separable): tek bir düz çizgi (ya da hyperplane) iki sınıfı ayırabiliyor
- Mantık kapıları: AND, OR, NOT, NAND
- Basit eşik kararları: "skor X'in üstünde mi?"
- İki örtüşmeyen bölgeye kümelenen verilerde ikili sınıflandırıcılar

## Birden çok katmana ihtiyaç duyduğunda

- Problem doğrusal ayrılabilir değil: tek bir çizgi sınıfları ayıramıyor
- XOR ve parity problemleri
- "Bu ama şu değil" tarzı muhakeme gerektiren her görev (koşulların kombinasyonları)
- Gerçek dünya sınıflandırması: görüntü, metin, ses — neredeyse her zaman doğrusal değil

## Karar checklist'i

1. Verini çiz ya da incele. Sınıflar arasına tek bir düz sınır çizebiliyor musun?
   - Evet: tek perceptron işe yarar
   - Hayır: en az iki katmana ihtiyacın var
2. Problem daha basit doğrusal kararların AND/OR'una ayrıştırılabiliyor mu?
   - Bu ayrıştırma sana minimum network yapısını söyler
   - XOR = (A OR B) AND (NOT (A AND B)) = 2 katmanda 3 perceptron
3. İkiden fazla sınıflı problemler için her sınıf başına bir output node'una ihtiyacın var

## Eğitim kuralı

```
error = expected - predicted
weight_new = weight_old + learning_rate * error * input
bias_new = bias_old + learning_rate * error
```

Tahmin doğruysa hiçbir şey değişmez. Yanlışsa, ağırlıklar hatayı azaltacak şekilde kayar. Bu sadece tek katmanlı perceptron'lar için işler. Çok katmanlı ağlar backpropagation gerektirir.

## Sık yapılan hatalar

- Doğrusal olmayan pattern'leri tek perceptron'la öğrenmeye çalışmak (asla yakınsamaz)
- Learning rate'i çok yüksek (ağırlıklar salınır) ya da çok düşük (eğitim sonsuza kadar sürer) ayarlamak
- Bias terimini unutmak (onsuz karar sınırı orijinden geçmek zorundadır)
- Perceptron yakınsamasını (doğrusal ayrılabilir veri için garanti) genel sinir ağı yakınsamasıyla (garanti değil) karıştırmak
