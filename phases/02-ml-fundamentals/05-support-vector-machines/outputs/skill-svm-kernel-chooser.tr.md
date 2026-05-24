---
name: skill-svm-kernel-chooser
description: Problemin için doğru SVM kernel'ını seç ve C ile gamma'yı tune et
version: 1.0.0
phase: 2
lesson: 5
tags: [svm, kernel, classification, hyperparameter-tuning]
---

# SVM Kernel Seçim Rehberi

SVM'ler iki seçimle tanımlanır: kernel (karar sınırının şeklini belirler) ve regularization parametreleri (margin genişliği ile sınıflandırma hataları arasındaki dengeyi kontrol eder). Bunları doğru yapmak, işe yaramaz bir model ile güçlü bir model arasındaki farktır.

## Karar Kontrol Listesi

1. Veri doğrusal olarak ayrılabilir mi (ya da yakın)?
   - Evet: linear kernel kullan. Daha hızlı ve daha yorumlanabilir.
   - Hayır: adım 2'ye geç.

2. Öznitelik vs örnek sayısı nedir?
   - Öznitelik >> örnek (örn. TF-IDF ile metin): linear kernel kullan. Yüksek boyutlu veri çoğu zaman doğrusal olarak ayrılabilir. RBF kazanç sağlamadan karmaşıklık ekler.
   - Örnek >> öznitelik (örn. 10-50 öznitelikli tabular veri): RBF kernel default seçim.

3. Karar sınırının pürüzsüz olması bekleniyor mu?
   - Pürüzsüz, sürekli sınır: RBF kernel
   - Polinom şekilli sınır: polynomial kernel (derece 2 ya da 3 ile başla)
   - Domain bilgisi spesifik etkileşim terimleri öneriyor: eşleşen dereceli polynomial kernel

4. Veri seti ne kadar büyük?
   - 10.000'in altı örnek: herhangi bir kernel çalışır, RBF güvenli default
   - 10.000 ile 100.000 arası: linear kernel ya da LinearSVC (primal formülasyon, epoch başına O(n))
   - 100.000 üstü: kernel SVM kullanma. Linear SVM, gradient boosting ya da sinir ağlarına geç.

5. Öznitelikleri ölçekledin mi?
   - SVM'ler öznitelik ölçeklemesi gerektirir. Fit etmeden önce her zaman standardize et (sıfır ortalama, birim varyans). Ölçeklenmemiş öznitelikler margin geometrisini bozar.

## Kernel seçim akış şeması

```
Başla
  |
  v
Öznitelik > 1000 ya da öznitelik >> örnek?
  Evet --> Linear kernel (hız için LinearSVC)
  Hayır --> Veri seti < 10k örnek?
            Evet --> Önce RBF dene (en iyi genel amaçlı kernel)
            Hayır --> Linear kernel (kernel SVM'ler O(n^2) ile O(n^3))
```

RBF iyi çalışmazsa, polinom derece 2-3 dene. O da başarısız olursa, problem SVM'lere uygun olmayabilir.

## C'yi tune etmek (regularization)

C yanlış sınıflandırmaların cezasını kontrol eder. Regularization gücüyle ters ilişkilidir.

| C değeri | Etki | Ne zaman kullanılır |
|---------|--------|-------------|
| 0.001 - 0.01 | Geniş margin, çok ihlal izinli | Gürültülü veri, generalization isteniyor |
| 0.1 - 1.0 | Dengeli | İyi başlangıç aralığı |
| 10 - 1000 | Dar margin, az ihlal | Temiz veri, yüksek accuracy gerekli |

Tuning stratejisi:
- C=1.0 ile başla
- Log ölçeğinde ara: [0.001, 0.01, 0.1, 1, 10, 100, 1000]
- En iyi değeri seçmek için çapraz doğrulama kullan
- En iyi C aralığının kenarındaysa, aralığı o yönde uzat

## Gamma'yı tune etmek (RBF kernel)

Gamma tek bir eğitim noktasının etkisinin ne kadar uzağa ulaştığını kontrol eder. Gaussian'ın genişliğini tanımlar.

| gamma değeri | Etki | Ne zaman kullanılır |
|-------------|--------|-------------|
| Küçük (0.001) | Her nokta geniş bir alanı etkiler. Pürüzsüz, basit sınır | Underfitting ya da az öznitelik |
| Orta (auto: 1/n_features) | sklearn default. Makul başlangıç noktası | Genel kullanım |
| Büyük (10+) | Her nokta sadece yakındaki noktaları etkiler. Karmaşık, dalgalı sınır | Overfitting riski |

Tuning stratejisi:
- gamma="scale" ile başla (1 / (n_features * X.var()), sklearn default)
- Log ölçeğinde ara: [0.001, 0.01, 0.1, 1, 10]
- Düşük gamma + yüksek C overfit eğilimindedir
- Yüksek gamma + düşük C underfit eğilimindedir

## Birlikte C ve gamma tuning

C ve gamma etkileşimli çalışır. Onları her zaman bağımsız değil, birlikte tune et.

Önerilen yaklaşım:
1. Kaba grid search: C [0.01, 0.1, 1, 10, 100], gamma [0.001, 0.01, 0.1, 1, 10] (25 kombinasyon)
2. En iyi bölgeyi bul
3. En iyi bölge etrafında ince grid search (örn. C [5, 10, 20, 50], gamma [0.05, 0.1, 0.2])
4. Boyunca 5-fold çapraz doğrulama kullan

## Yaygın hatalar

- Yüksek boyutlu seyrek veride RBF kernel kullanmak (linear daha iyi ve 100 kat daha hızlı)
- Öznitelikleri ölçeklemeyi unutmak (en yaygın SVM hatası)
- Gürültülü veride C'yi çok yüksek ayarlamak (sınırı öğrenmek yerine gürültüyü ezberler)
- 50k örnek üstü veri setlerinde kernel SVM kullanmak (eğitim süresi engelleyici)
- C ve gamma'yı birlikte tune etmemek (birbirini telafi ederler)
- Polinom derecesini default 5+ yapmak (agresif overfit eder, önce 2 ya da 3 dene)

## Hızlı referans

| Kernel | Ne zaman kullanılır | Anahtar parametreler | Eğitim karmaşıklığı |
|--------|------------|----------------|-------------------|
| Linear | Metin/TF-IDF, çok öznitelik, büyük veri | Sadece C | Epoch başına O(n) |
| RBF | Genel amaçlı, 10k altı örnek | C, gamma | O(n^2) ile O(n^3) |
| Polynomial | Bilinen polinom ilişkiler | C, degree, coef0 | O(n^2) ile O(n^3) |
| Sigmoid | Nadiren işe yarar (iki katmanlı sinir ağına eşdeğer) | C, gamma, coef0 | O(n^2) ile O(n^3) |
