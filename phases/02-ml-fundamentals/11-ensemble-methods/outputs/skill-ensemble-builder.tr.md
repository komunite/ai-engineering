---
name: skill-ensemble-builder
description: Doğru ensemble yöntemini seç ve problemin için yapılandır
version: 1.0.0
phase: 2
lesson: 11
tags: [ensemble, bagging, boosting, random-forest, xgboost, stacking]
---

# Ensemble Yöntem Seçim Rehberi

Ensemble'lar, herhangi bir tek modelden daha iyi tahminler üretmek için birden fazla modeli birleştirir. Soru her zaman şudur: ne tür bir ensemble ve ne zaman?

## Karar Kontrol Listesi

1. Mevcut modelinin temel sorunu nedir?
   - High variance (overfitting): bagging kullan (Random Forest)
   - High bias (underfitting): boosting kullan (Gradient Boosting, XGBoost)
   - Her ikisi ya da maksimum accuracy istiyorsun: stacking kullan

2. Ne kadar verin var?
   - 1.000 satır altı: Random Forest (sağlam, yanlış yapılandırması zor)
   - 1.000 ile 100.000 arası: XGBoost ya da LightGBM (tabular için genel olarak en iyisi)
   - 100.000 üstü: LightGBM (en hızlı gradient boosting, büyük veriyi iyi yönetir)

3. Tuning'e ne kadar zaman ayırabilirsin?
   - Minimal: default'larla Random Forest (neredeyse her zaman çalışır)
   - Orta: learning_rate=0.1 ile XGBoost, early stopping ile n_estimators tune et
   - Maksimum: LightGBM ya da XGBoost ile Bayesian hyperparameter search

4. Yorumlanabilirlik gerekli mi?
   - Evet: tek karar ağacı ya da feature importance'lı küçük Random Forest
   - Kısmen: SHAP değerleriyle gradient boosting
   - Hayır: stacking ya da deep ensemble'lar

5. Veri çok outlier'lı gürültülü mü?
   - Evet: Random Forest (bagging gürültüye sağlam)
   - Hayır: gradient boosting (temiz veride accuracy'yi daha ileri itebilir)

## Hangi yöntemi ne zaman kullanmalı

**Random Forest (Bagging)**: güvenli ilk seçim. Bootstrap örneklerinde çok sayıda ağacı eğitir ve ortalama alır. Bias'ı artırmadan varyansı azaltır. Orta veri setlerinde overfit etmesi neredeyse imkansız. Minimal tuning gerekir: n_estimators=100-500 ayarla ve default'ları bırak.

**AdaBoost**: örnek ağırlık güncellemeli sıralı boosting. Basit base learner'larla (decision stump) iyi çalışır. Yanlış sınıflandırılmış noktaları yukarı ağırlıklandırdığı için outlier ve gürültülü etiketlere duyarlıdır. Pratikte büyük ölçüde gradient boosting tarafından değiştirilmiştir.

**Gradient Boosting**: her yeni ağacı ensemble'ın o ana kadarki residual'larına fit eder. Bias'ı azaltır. Tabular veri için en güçlü yöntem. Tuning gerektirir: learning_rate, n_estimators, max_depth, min_child_weight, subsample.

**XGBoost**: regularization, ikinci dereceden optimizasyon ve sistem seviyesi hız iyileştirmeleri ile gradient boosting. Eksik değerleri yerel olarak halleder. Kaggle yarışmaları ve tabular ML production için default.

**LightGBM**: leaf-wise büyüme ile gradient boosting (level-wise yerine). Büyük veri setlerinde XGBoost'tan daha hızlı. Histogram tabanlı split kullanır. 50k satır üzeri veri setleri için en iyisi.

**CatBoost**: yerel kategorik öznitelik yönetimi ile gradient boosting. One-hot encode etmek gerekmez. Çok kategorik özniteliğin olduğu durumlarda iyi.

**Stacking**: birden fazla çeşitli base modelin tahminleri üzerinde bir meta-learner eğitir. Mutlak en iyi accuracy gerektiğinde ve compute fazlasıyla varsa kullan. Leakage'dan kaçınmak için base model tahminlerini her zaman çapraz doğrulama ile üret.

**Voting**: en basit ensemble. Hard voting (çoğunluk sınıfı) ya da soft voting (olasılık ortalaması). Meta-learner olmadan 2-3 çeşitli modeli hızlı birleştirme yolu.

## Yaygın hatalar

- Early stopping olmadan gradient boosting kullanmak (çok fazla tur çalışırsa overfit eder)
- learning_rate'i çok yüksek ayarlamak (0.3 üstü genellikle istikrarsızlığa neden olur)
- Gradient boosting için max_depth'i tune etmemek (sınırsız ya da çok derin ağaçların default'ı overfit eder)
- Hepsi aynı tip modellerle stacking (diversity stacking'in amacıdır)
- Gürültülü veride AdaBoost kullanmak (outlier'lar her turda daha yüksek ağırlık alır)
- Random Forest'ın underfitting'i düzelteceğini beklemek (varyansı azaltır, bias'ı değil)

## Yönteme göre tuning öncelikleri

**Random Forest:**
1. n_estimators: 100-500 (daha fazlası nadiren kötü, sadece daha yavaş)
2. max_depth: None (ağaçlar tamamen büyüsün) ya da hız için 10-20'de sınırla
3. max_features: sınıflandırma için "sqrt", regresyon için "log2" ya da n/3

**XGBoost / LightGBM:**
1. learning_rate: 0.01-0.3 (daha fazla ağaç için compute'un varsa düşük daha iyi)
2. n_estimators: tahmin etmek yerine validation set üzerinde early stopping kullan
3. max_depth: 3-8 (6 ile başla)
4. min_child_weight / min_data_in_leaf: 1-20 (yüksek overfitting'i önler)
5. subsample: 0.7-1.0
6. colsample_bytree: 0.7-1.0
7. reg_alpha (L1) ve reg_lambda (L2): 0-10

## Hızlı referans

| Yöntem | Neyi azaltır | Hız | Tuning eforu | En iyi |
|--------|---------|-------|--------------|----------|
| Random Forest | Variance | Hızlı | Düşük | Gürültülü veri, hızlı baseline |
| AdaBoost | Bias | Hızlı | Düşük | Basit base learner'lar, temiz veri |
| Gradient Boosting | Bias | Orta | Yüksek | Tabular veri, yarışmalar |
| XGBoost | İkisi de | Hızlı | Yüksek | Production tabular ML |
| LightGBM | İkisi de | En hızlı | Yüksek | Büyük veri setleri (50k+ satır) |
| CatBoost | İkisi de | Orta | Orta | Çok kategorik öznitelik |
| Stacking | İkisi de | Yavaş | Yüksek | Maksimum accuracy, çeşitli modeller |
| Voting | Variance | Hızlı | Yok | 2-3 modelin hızlı kombinasyonu |
