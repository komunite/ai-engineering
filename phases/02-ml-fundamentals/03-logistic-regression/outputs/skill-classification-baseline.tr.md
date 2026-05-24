---
name: skill-classification-baseline
description: Karmaşık modellere geçmeden önce güçlü bir sınıflandırma baseline'ı kur
version: 1.0.0
phase: 2
lesson: 3
tags: [classification, logistic-regression, baseline, preprocessing]
---

# Sınıflandırma Baseline Rehberi

Karmaşık modeller denemeden önce lojistik regresyonla bir baseline kur. Saniyeler içinde eğitilir, olasılık üretir ve tamamen yorumlanabilir. Şaşırtıcı sayıda gerçek dünya problemi daha fazlasına asla ihtiyaç duymaz.

## Karar Kontrol Listesi

1. Karar sınırı muhtemelen doğrusal mı?
   - Evet: lojistik regresyon muhtemelen yeterli olacak
   - Hayır: yine de iyileşmeyi ölçmek için baseline olarak istiyorsun

2. Kaç özniteliğin var?
   - 50'nin altı: standart lojistik regresyon iyi çalışır
   - 50 ile 10.000 arası: L2 regularization ekle (Ridge)
   - 10.000 üstü (örn. TF-IDF metin öznitelikleri): L1 regularization (Lasso) ya da LinearSVC kullan

3. Veri seti dengesiz mi?
   - 5:1 altı oran: ayarlama yapmadan muhtemelen iyi
   - 5:1 ile 50:1 arası: sklearn'de `class_weight="balanced"` kullan
   - 50:1 üstü: class weighting'i uygun metrikle birleştir (precision, recall ya da F1)

4. Öznitelikler farklı ölçeklerde mi?
   - Lojistik regresyondan önce her zaman standardize et. Gradient tabanlı optimizasyon kullanır ve ölçeklenmemiş öznitelikler yakınsamayı yavaşlatır ya da karar sınırını bozar.

5. Eksik değerler var mı?
   - Fit etmeden önce impute et. Lojistik regresyon NaN'leri kaldıramaz.
   - Sayısal sütunlar için median imputation, kategorik için mode kullan.

## Lojistik regresyonun yeterli olduğu durumlar

- Çoğunlukla doğrusal öznitelik ilişkileriyle binary sınıflandırma
- Olasılık çıktısına ihtiyacın var (sadece sınıf etiketleri değil)
- Yorumlanabilirlik gerekli (standardizasyon sonrası katsayılar öznitelik önem yönünü ve göreceli büyüklüğü gösterir)
- Eğitim verisi küçük (yüzlerce ile birkaç bin örnek arası)
- Gerçek zamanlı servis için hızlı model gerekli (inference anında tek dot product)
- Düzenleyici ya da uyumluluk gereksinimleri açıklanabilirlik talep ediyor

## Ne zaman yükseltmeli

- Accuracy hedefin altında plato yapıyor ve feature engineering denedin
- Öznitelikler ile hedef arasındaki ilişki açıkça doğrusal değil (residual plot'ları kontrol et)
- Büyük tabular verin var (10k+ satır): gradient boosting (XGBoost ya da LightGBM) dene
- Öznitelikler polinom özniteliklerin yakalayamayacağı karmaşık etkileşimlere sahip
- Görüntü, metin ya da sıralı verin var: ham girdilerde lojistik regresyon çalışmaz

## Sınıflandırma baseline'ı için ön işleme adımları

1. **Train/test split** önce, herhangi bir ön işlemeden önce. Bu data leakage'ı önler.
2. **Eksik değerleri yönet**: sayısal için median impute, kategorik için mode impute.
3. **Kategorikleri kodla**: düşük kardinalite için one-hot (10 değerin altı), daha yüksek için target encoding. Target encoding'i sadece eğitim fold'larında fit et (leakage'ı önlemek için out-of-fold encoding kullan).
4. **Sayısalları ölçekle**: StandardScaler (sıfır ortalama, birim varyans). Train'de fit, ikisini de transform et.
5. **Lojistik regresyonu fit et** `C=1.0` ile (default regularization).
6. **Değerlendir**: confusion matrix, precision, recall, F1. Sadece accuracy değil.
7. **Threshold'u tune et**: default 0.5 nadiren optimal. 0.1 ile 0.9 arası tara ve precision/recall önceliğinle eşleşen threshold'u seç.

## Yaygın hatalar

- Dengesiz veride sadece accuracy değerlendirmek (çoğunluk sınıfını tahmin eden bir model yüksek skor alır ama işe yaramaz)
- Öznitelikleri ölçeklemeyi unutmak (ölçeklenmemiş özniteliklerle lojistik regresyon yavaş eğitilir ve daha kötü bir çözüme yakınsar)
- Karar threshold'unu tune etmek için test setini kullanmak (validation ya da çapraz doğrulama kullan)
- Baseline'ı atlayıp doğrudan XGBoost'a atlamak (yorumlanabilirliği kaybedersin ve referans noktan olmaz)
- Multicollinearity'yi kontrol etmemek (yüksek korelasyonlu öznitelikler katsayı varyansını şişirir)

## Hızlı referans

| Senaryo | Model | Regularization | Anahtar ayar |
|----------|-------|---------------|-------------|
| Az öznitelik, yorumlanabilir | LogisticRegression | L2 (default) | C=1.0 |
| Çok öznitelik, bazıları alakasız | LogisticRegression | L1 | penalty="l1", solver="saga" |
| Yüksek boyutlu seyrek (metin) | SGDClassifier | L1 ya da ElasticNet | loss="log_loss" |
| Dengesiz sınıflar | LogisticRegression | L2 | class_weight="balanced" |
| Olasılık gerekli | LogisticRegression | L2 | predict_proba() |
| Sadece sınıf etiketleri gerekli | LinearSVC | L2 | Büyük veri için LR'den daha hızlı |
