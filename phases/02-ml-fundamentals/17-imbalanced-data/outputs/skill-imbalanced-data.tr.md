---
name: skill-imbalanced-data
description: Dengesiz sınıflandırma problemlerini yönetmek için karar kontrol listesi
version: 1.0.0
phase: 2
lesson: 17
tags: [imbalanced-data, smote, class-weights, threshold-tuning, evaluation]
---

# Dengesiz Veri Stratejisi

Dengesiz sınıflandırmayı yönetmek için bir karar kontrol listesi. Problemine doğru yaklaşımı seçmek için bu sırayı takip et.

## Adım 1: Dengesizliği ölç

- Sınıf başına örnek sayısı say
- Dengesizlik oranını hesapla (çoğunluk / azınlık)
- Hafif: oran < 3:1 (örn. 70/30)
- Orta: oran 3:1 ile 20:1 arası (örn. 95/5)
- Şiddetli: oran > 20:1 (örn. 99/1)

## Adım 2: Doğru metriği seç

Dengesiz veri setlerinde accuracy yerine precision/recall/F1 tercih et. Problemine göre seç:

| Durum | Birincil Metrik | İkincil Metrik |
|-----------|---------------|-----------------|
| Pozitifleri kaçırmak çok maliyetli (fraud, hastalık) | Recall | F2 score |
| False alarm maliyetli (spam filtresi, öneriler) | Precision | F0.5 score |
| Her ikisi de yaklaşık olarak önemli | F1 score | MCC |
| Tek bir sıralama metriği gerekli | AUPRC | AUC-ROC |
| Veri setleri arası karşılaştırma gerekli | MCC | AUPRC |

## Adım 3: Bir rebalancing stratejisi seç

### Dengesizlik şiddetine göre

| Dengesizlik | Önce Dene | Sonra Dene | Kaçın |
|-----------|-----------|------------|-------|
| Hafif (< 3:1) | Class weights | Threshold tuning | Oversampling (gereksiz) |
| Orta (3:1 ile 20:1) | SMOTE + class weights | Üstüne threshold tuning | Undersampling (çok veri kaybı) |
| Şiddetli (> 20:1) | SMOTE + class weights + threshold | Balanced bagging ile ensemble | Tek başına undersampling |

### Veri seti büyüklüğüne göre

| Veri Seti Büyüklüğü | Tercih Edilen Strateji | Neden |
|-------------|-------------------|--------|
| < 1.000 örnek | Oversampling ya da SMOTE | Çoğunluk verisini kaybetmeyi göze alamazsın |
| 1.000 - 10.000 | SMOTE + threshold tuning | k-NN için yeterli azınlık örneği |
| > 10.000 | Class weights ya da undersampling | Hızlı, yeterli azınlık verisi |

## Adım 4: Tekniği uygula

### Class weights (her zaman önce dene)
- sklearn'de: `class_weight='balanced'`
- Veri değişikliği gerekmez
- Loss tabanlı herhangi bir modelle çalışır
- Beklentide oversampling'e eşdeğer

### SMOTE
- Yalnızca eğitim verisine uygula (asla test/validation'a)
- k=5 komşu kullan (default)
- En iyi sonuç için class weights ile birleştir
- Sınır yakınındaki gürültülü sentetik noktalara dikkat et

### Threshold tuning
- Modeli eğit, validation set üzerinde tahmin edilen olasılıkları al
- Threshold'ları 0.05'ten 0.95'e tara
- Seçilen metriği maksimize eden threshold'u seç
- Her zaman validation verisinde tune et, asla test verisinde değil

## Adım 5: Doğru şekilde doğrula

- Stratified cross-validation kullan (her fold'da sınıf oranlarını korur)
- Metrikleri orijinal (resample edilmemiş) test setinde raporla
- SMOTE'u asla bölmeden önce uygulama -- yalnızca eğitim fold'larında
- "Her zaman çoğunluğu tahmin et" baseline'ı ile karşılaştır

## Adım 6: Kaçınılması gereken yaygın hatalar

- SMOTE'u train/test split öncesi tüm veri setine uygulamak (data leakage)
- Değerlendirme metriği olarak accuracy kullanmak
- Class weights'ı önce denememek (en basit yaklaşım, çoğu zaman yeterli)
- Oversample edip sonra çapraz doğrulamak (sentetik noktalar fold'lar arasında sızar)
- Threshold tuning'i görmezden gelmek (yeniden eğitim gerektirmeyen bedava performans)
- Küçük veri setlerinde random undersampling kullanmak (çok veri atar)

## Hızlı Karar Ağacı

1. Dengesizlik oranı < 3:1 mi? -> Yalnızca class weights dene
2. Veri seti > 10.000 örnek mi? -> Class weights + threshold tuning
3. Veri seti < 1.000 örnek mi? -> SMOTE + class weights
4. Aksi halde -> SMOTE + class weights + threshold tuning
5. Hâlâ yeterli değil mi? -> Balanced bagging ensemble
