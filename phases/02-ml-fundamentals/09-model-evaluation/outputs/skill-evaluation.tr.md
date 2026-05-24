---
name: skill-evaluation
description: Sınıflandırma ve regresyon modelleri için değerlendirme stratejisi kontrol listesi
version: 1.0.0
phase: 2
lesson: 9
tags: [evaluation, metrics, cross-validation, model-selection]
---

# Model Değerlendirme Stratejisi

Herhangi bir ML modelini doğru değerlendirmek için kontrol listesi. En yaygın değerlendirme hatalarından kaçınmak için bu sırayı takip et.

## Adım 1: Veriyi doğru böl

- Herhangi bir ön işlemeden (ölçekleme, imputation, encoding) önce böl
- Sınıflandırma görevleri için stratified split kullan
- En sona yalnızca bir kez dokunacağın bir test set ayır
- Küçük veri setlerinde tek split yerine 5-fold ya da 10-fold çapraz doğrulama kullan
- Zaman serisi için zamana dayalı split kullan (asla karıştırma)

## Adım 2: Doğru metriği seç

### Sınıflandırma

| Durum | Bu metriği kullan | Neden |
|-----------|----------------|-----|
| Dengeli sınıflar, basit karşılaştırma | Accuracy | Yorumlaması kolay, sınıflar eşitken anlamlı |
| False positive maliyetli (spam filtresi, fraud uyarıları) | Precision | İşaretlenenlerin kaçının gerçekten pozitif olduğunu ölçer |
| False negative maliyetli (kanser taraması, güvenlik) | Recall | Gerçek pozitiflerin kaçını yakaladığını ölçer |
| Precision ve recall arasında denge gerekli | F1 Score | Harmonik ortalama, aşırı dengesizliği cezalandırır |
| Threshold'lar arasında model karşılaştırması | AUC-ROC | Threshold'dan bağımsız sıralama kalitesi |
| Dengesiz veri | F1, AUC-ROC ya da PR-AUC | Dengesiz sınıflarda accuracy yanıltıcı |

### Regresyon

| Durum | Bu metriği kullan | Neden |
|-----------|----------------|-----|
| Standart regresyon, outlier kabul edilebilir | RMSE | Hedefle aynı birim, büyük hataları cezalandırır |
| Outlier'a dayanıklı değerlendirme | MAE | Tüm hatalara eşit muamele, outlier domine etmez |
| Farklı ölçeklerdeki modelleri karşılaştırma | R-squared | 0-1 normalize ölçek (açıklanan varyans oranı) |
| Business dolar miktarı gerektiriyor | MAE ya da RMSE | Hata büyüklüğü olarak doğrudan yorumlanabilir |

## Adım 3: Baseline'lar belirle

Modelini değerlendirmeden önce, baseline performansını hesapla:
- Sınıflandırma: çoğunluk sınıfı tahmincisi (her zaman en yaygın sınıfı tahmin et)
- Regresyon: her zaman eğitim hedefinin ortalamasını tahmin et
- Bu baseline'ları yenemeyen herhangi bir model öğrenmiyor demektir

## Adım 4: Çapraz doğrulama yap

- İstikrarlı tahminler için K-fold (K=5 ya da K=10) kullan
- Sınıflandırma için stratified K-fold kullan
- Fold'lar arası ortalama ve standart sapma raporla
- mean=0.85, std=0.02 olan bir model, mean=0.87, std=0.10 olandan daha güvenilirdir

## Adım 5: Modelleri istatistiksel olarak karşılaştır

- Anlamlılığı kontrol etmeden en yüksek ortalama skorlu modeli seçme
- Çapraz doğrulama fold'ları arasında paired t-test kullan
- |t| < 2.78 ise (K=5, df=4, p<0.05) fark şans eseri olabilir
- Performans farkları anlamlı değilse daha basit modeli düşün

## Adım 6: Yaygın hataları kontrol et

- Data leakage: herhangi bir test verisi bilgisi eğitime sızdı mı? (bölmeden önce ölçekleme, hedef türevli öznitelikler)
- Class imbalance: accuracy zayıf azınlık sınıf performansını saklıyor mu?
- Overfitting: eğitim ve doğrulama performansı arasındaki fark büyük mü?
- Çok fazla değerlendirme: test setine birden fazla kez baktın mı?

## Adım 7: Nihai performansı raporla

- Train + validation birleşimi üzerinde eğit
- Ayrılan test setinde tam olarak bir kez değerlendir
- Mümkünse güven aralıklarıyla birlikte seçilen metriği raporla
- Baseline karşılaştırmasını belirt (random/mean'den ne kadar daha iyi)
