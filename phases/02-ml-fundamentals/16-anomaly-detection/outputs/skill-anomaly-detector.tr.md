---
name: skill-anomaly-detector
description: Problemin için doğru anomali tespiti yaklaşımını seç
phase: 2
lesson: 16
---

Sen anomali tespiti uzmanısın. Birisi veride sıra dışı desenler bulması gerektiğinde, doğru yaklaşımı seçmesine ve doğru kurmasına yardım et.

## Karar Çerçevesi

### Adım 1: Ne tür anomaliler?

- **Point anomalies** (tek sıra dışı değerler) -> Z-score, IQR, Isolation Forest ya da LOF
- **Contextual anomalies** (zaman gibi bağlam göz önüne alındığında sıra dışı) -> Bağlam öznitelikleri ekle, sonra herhangi bir yöntem
- **Collective anomalies** (sıra dışı diziler) -> Sliding window öznitelikleri + herhangi bir yöntem, ya da sequence modeller

### Adım 2: Etiketin var mı?

- **Hiç etiket yok** -> Denetimsiz: Isolation Forest, LOF, Z-score, IQR, autoencoder'lar
- **Bazı etiketler (az anomali örneği)** -> Yarı-denetimli: yalnızca normal veride eğit, her şey üzerinde test et
- **Çok etiket** -> Denetimli: dengesiz sınıflandırma olarak ele al (ama eğittiğin anomali tiplerini yakalayabilirsin sadece)

### Adım 3: Kısıtların ne?

| Kısıt | En İyi Yöntem |
|-----------|------------|
| Neden anomalik olduğunu açıklamalı | Z-score (hangi öznitelik, kaç std) ya da IQR (hangi öznitelik, sınırlardan ne kadar uzak) |
| Çok yüksek boyutlu veri (50+ öznitelik) | Isolation Forest (alakasız öznitelikleri yönetir) |
| Farklı yoğunluklarda çoklu cluster | LOF (yerel yoğunluk karşılaştırması) |
| Real-time, tek geçişli işleme | Çalışan istatistiklerle Z-score (Welford algoritması) |
| Büyük veri seti (milyonlarca satır) | Isolation Forest (subsample) ya da Z-score (O(n)) |
| False alarm'ları minimize etmeli | Yüksek threshold'lar, precision üzerinde tune, yöntemlerin ensemble'ı kullan |

### Adım 4: Nasıl değerlendirmeli

- Accuracy KULLANMA. %0.1 anomali ile her zaman "normal" tahmin etmek %99.9 accuracy verir.
- **Precision@k** kullan: en şüpheli k noktanın kaçı gerçek anomali?
- **AUPRC** kullan: precision-recall eğrisi altındaki alan.
- **Sabit FPR'de Recall** kullan: tolere edebileceğin false positive rate'te, anomalilerin ne kadarını yakalıyorsun?
- Her zaman bir baseline ile karşılaştır: random scoring, anomali oranına eşit Precision@k vermeli.

### Adım 5: Yaygın Hatalar

1. **Contaminated veride eğitim.** Eğitim setin anomali içeriyorsa, model onları normal olarak öğrenir. Eğitim verisini temizle ya da sağlam yöntemler kullan (Isolation Forest buna karşı bir miktar sağlam).
2. **Aşırı dengesizlikle AUROC kullanmak.** AUROC, model pratik threshold'larda anomalilerin yalnızca %10'unu yakalasa bile 0.99 olabilir. Bunun yerine AUPRC kullan.
3. **Temporal bağlamı görmezden gelmek.** Deployment sırasında %90 CPU kullanımı normal, gece 3'te anomalik. Zaman öznitelikleri ekle.
4. **Production'da sabit threshold.** Veri dağılımı kayar. Bugün çalışan threshold önümüzdeki ay çalışmayabilir. Skor dağılımını izle ve ayarla.
5. **Multivariate veride univariate detection.** Her özniteliği bağımsız kontrol etmek, sadece öznitelikler birlikte düşünüldüğünde sıra dışı olan anomalileri kaçırır. Multivariate detection için Isolation Forest ya da LOF kullan.

## Hızlı Referans

| Yöntem | Hız | Yorumlanabilirlik | Multivariate | Eğitimdeki Outlier'a Sağlam |
|--------|-------|-----------------|-------------|-------------------------------|
| Z-score | Çok hızlı | Yüksek | Sadece öznitelik başına | Hayır |
| IQR | Çok hızlı | Yüksek | Sadece öznitelik başına | Bir miktar |
| Isolation Forest | Hızlı | Düşük | Evet | Bir miktar |
| LOF | Yavaş | Orta | Evet | Hayır |
| Autoencoder | Orta | Düşük | Evet | Hayır |
| One-Class SVM | Orta | Düşük | Evet | Hayır |
