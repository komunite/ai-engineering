---
name: skill-clustering-guide
description: Veri şekli, gürültü ve kısıtlara göre doğru clustering algoritmasını seç
version: 1.0.0
phase: 2
lesson: 7
tags: [clustering, k-means, dbscan, hierarchical, gmm, unsupervised]
---

# Clustering Algoritma Seçim Rehberi

Clustering için tek bir en iyi algoritma yoktur. Doğru seçim; cluster şekline, cluster sayısını bilip bilmediğine, veride ne kadar gürültü olduğuna ve veri setinin büyüklüğüne bağlıdır.

## Karar Kontrol Listesi

1. Cluster sayısını biliyor musun?
   - Evet: K-Means ya da GMM
   - Hayır: DBSCAN (cluster'ları otomatik bulur) ya da hierarchical (dendrogramı farklı seviyelerde kes)

2. Cluster'lar ne şekilde?
   - Yaklaşık küresel (blob benzeri): K-Means
   - Farklı boyutlarda eliptik: GMM
   - Keyfi şekiller (hilal, halka, zincir): DBSCAN
   - İç içe ya da hiyerarşik: hierarchical clustering

3. Veri gürültü ya da outlier içeriyor mu?
   - Evet: DBSCAN (gürültü noktalarını açıkça etiketler) ya da GMM (düşük olasılıklı noktalar outlier'dır)
   - Hayır: K-Means iyi

4. Soft atama (olasılıklar) gerekli mi?
   - Evet: GMM her cluster için P(cluster | veri noktası) verir
   - Hayır: K-Means ya da DBSCAN hard atama verir

5. Veri seti ne kadar büyük?
   - 10.000 altı: herhangi bir algoritma çalışır
   - 10.000 - 1.000.000: K-Means (hızlı), Mini-Batch K-Means (daha hızlı)
   - 1.000.000 üstü: Mini-Batch K-Means ya da BIRCH. Hierarchical çok yavaş.

## Hangi yaklaşımı ne zaman kullanmalı

**K-Means**: default başlangıç noktası. Hızlı (O(n * k * iterations)), basit ve birçok problem için yeterli. K'yi seçmek için elbow yöntemi ya da silhouette skoru kullan. Sınırlamalar: küresel cluster'lar varsayar, başlangıç değerine duyarlıdır (K-Means++ kullan ya da birden çok kez çalıştır), değişen cluster boyutlarını iyi kaldıramaz.

**DBSCAN**: keyfi şekilli cluster'ları keşfetmek ve outlier'ları otomatik tespit etmek için en iyisi. İki parametre: eps (komşuluk yarıçapı) ve min_samples (minimum yoğunluk). K belirtmeyi gerektirmez. Sınırlamalar: cluster yoğunlukları çok farklı olduğunda zorlanır, eps tuning zor olabilir. eps tahmini için k-distance plot kullan: her noktanın k. en yakın komşusuna olan mesafesini hesapla, sırala ve elbow ara.

**Hierarchical (Agglomerative)**: bir birleştirme ağacı oluşturur. Cluster yapısını birden çok detay seviyesinde keşfetmek istediğinde faydalı (dendrogramı farklı yüksekliklerde kes). Kompakt cluster'lar için Ward's linkage en iyi çalışır. Single linkage uzun cluster'ları bulur ama gürültüye duyarlıdır. Sınırlamalar: O(n^2) bellek ve O(n^3) zaman, bu yüzden büyük veri setlerinde pratik değil.

**GMM (Gaussian Mixture Models)**: olasılıksal atamalarla soft clustering. Her cluster'ı kendi ortalaması ve covariance'ı olan bir Gaussian dağılımı olarak modeller. Cluster'lar eliptik ya da örtüşüyorsa K-Means'ten daha iyi. Bileşen sayısını seçmek için BIC (Bayesian Information Criterion) kullan. Sınırlamalar: Gaussian dağılımları varsayar, dışbükey olmayan şekillerde başarısız olabilir, başlangıca duyarlıdır.

## Cluster kalitesini değerlendirme (etiket yok)

| Metrik | Neyi ölçer | Aralık | Ne zaman kullanılır |
|--------|-----------------|-------|----------|
| Silhouette skoru | Cohesion vs separation | -1 ile 1 (yüksek daha iyi) | K değerlerini ya da algoritmaları karşılaştırma |
| Inertia (cluster içi SS) | Cluster'ların sıkılığı | 0 ile inf (düşük daha iyi) | K-Means için elbow yöntemi |
| BIC / AIC | Karmaşıklık cezalı model fit | Düşük daha iyi | GMM bileşen sayısını seçme |
| Calinski-Harabasz indeksi | Arası/içi varyans oranı | Yüksek daha iyi | Hızlı karşılaştırma |
| Davies-Bouldin indeksi | Cluster'lar arası ortalama benzerlik | Düşük daha iyi | Örtüşen cluster'ları cezalandırır |

## Yaygın hatalar

- Öznitelikleri ölçeklemeden K-Means çalıştırmak (büyük ölçekli öznitelikler mesafe hesabını domine eder)
- Veri yüksek boyutluyken K'yi 2D'de göz kararı seçmek (silhouette skorlarını kullan)
- Küresel olmayan cluster'larda K-Means kullanmak (hilal ya da halka şeklindeki veri DBSCAN gerektirir)
- DBSCAN eps'i çok büyük (her şey tek cluster) ya da çok küçük (her şey gürültü) ayarlamak
- Cluster etiketlerini ground truth olarak ele almak (clustering keşfedicidir; domain bilgisiyle doğrula)
- 20.000'den fazla noktalı veri setlerinde hierarchical clustering çalıştırmak (bellek ve zaman patlar)

## Hızlı referans

| Algoritma | Cluster şekli | K bulur | Gürültüyü kaldırır | Soft atama | Ölçeklenebilirlik |
|-----------|--------------|---------|---------------|-----------------|-------------|
| K-Means | Küresel | Hayır (K'yi sen verirsin) | Hayır | Hayır | Milyonlar |
| Mini-Batch K-Means | Küresel | Hayır | Hayır | Hayır | On milyonlar |
| DBSCAN | Keyfi | Evet | Evet | Hayır | Yüz binler |
| Hierarchical | Herhangi (linkage'a bağlı) | Esnek (dendrogramı kes) | Linkage'a bağlı | Hayır | 20k altı |
| GMM | Eliptik | Hayır (K'yi sen verirsin) | Kısmen (düşük olasılık) | Evet | 100k altı |
| HDBSCAN | Keyfi | Evet | Evet | Kısmen | Yüz binler |
