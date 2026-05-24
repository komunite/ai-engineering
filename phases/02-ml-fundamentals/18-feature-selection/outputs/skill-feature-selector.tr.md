---
name: skill-feature-selector
description: Doğru öznitelik seçim yöntemini seçmek için hızlı referans karar ağacı
version: 1.0.0
phase: 2
lesson: 18
tags: [feature-selection, mutual-information, rfe, lasso, tree-importance]
---

# Öznitelik Seçim Stratejisi

Doğru öznitelik seçim yöntemini seçmek ve uygulamak için hızlı referans.

## Adım 1: Temizlikle başla

Herhangi bir yöntemi uygulamadan önce, açıkça işe yaramaz öznitelikleri kaldır:

- **Sabit öznitelikler**: varyans = 0. Onları kaldır.
- **Sabite yakın öznitelikler**: varyans < 0.01 (ya da eşiğin). Onları kaldır.
- **Duplike öznitelikler**: aynı sütunlar. Birini tut, kalanını at.
- **ID sütunları**: satır başına benzersiz, genelleştirilebilir bilgi taşımaz. Onları kaldır.

Bu saniyeler sürer ve dağınık gerçek dünya veri setlerinde özniteliklerin %10-30'unu eleyebilir.

## Adım 2: Durumuna göre bir yöntem seç

### Hızlı Karar Ağacı

1. **< 50 öznitelik?** Mutual information sıralamasıyla başla. Top K'yı tut.
2. **50 - 500 öznitelik?** Önce variance threshold kullan, sonra doğrusal model kullanıyorsan L1 (Lasso), ağaç kullanıyorsan tree importance.
3. **> 500 öznitelik?** Yöntemleri zincirle: variance threshold -> mutual information filtresi (top %50) -> hayatta kalanlarda RFE.
4. **Yorumlanabilirlik gerekli?** L1 regularization sana kesin sıfır/sıfır olmayan verir. Tree importance sıralı skorlar verir.
5. **Doğrusal olmayan ilişkileri yakalaman gerekiyor mu?** Mutual information ya da tree tabanlı önem. L1'den kaçın (yalnızca doğrusal).
6. **Öznitelik etkileşimleri gerekli mi?** RFE ya da tree tabanlı önem. Filter yöntemleri etkileşimleri kaçırır.

### Yöntem Referansı

| Yöntem | Ne Zaman Kullanılır | Ne Zaman Kaçınılır |
|--------|------------|---------------|
| Variance threshold | Her zaman, ilk adım olarak | Asla atlama |
| Mutual information | Hızlı sıralama, doğrusal olmayan ilişkiler | Öznitelik etkileşim tespiti gerektiğinde |
| RFE | Kapsamlı seçim, orta öznitelik sayısı | Çok pahalı modeller, > 1000 öznitelik |
| L1 / Lasso | Doğrusal modeller, hızlı embedded seçim | Doğrusal olmayan problemler, yüksek korelasyonlu öznitelikler |
| Tree importance | Doğrusal olmayan ilişkiler, öznitelik etkileşimleri | Yüksek kardinaliteli özniteliklere karşı önyargılı |
| Permutation importance | Model-agnostic doğrulama, son kontrol | İlk eleme için çok yavaş |

## Adım 3: Seçimini doğrula

- Seçili özniteliklerle model performansını tüm özniteliklerle karşılaştır
- Tek train/test split değil, çapraz doğrulama kullan
- Performans %1-2'den fazla düşerse, faydalı öznitelikleri kaldırmış olabilirsin
- Performans iyileşirse, gürültüyü başarıyla kaldırdın

## Adım 4: Yaygın tuzakları yönet

### Korelasyonlu öznitelikler
- L1 keyfi olarak korelasyonlu bir gruptan birini seçer ve diğerlerini sıfırlar
- Önce korelasyon matrisini hesapla ve hangi korelasyonlu öznitelikleri tutacağına karar ver
- Tree importance, önemi korelasyonlu öznitelikler arasında yayar

### Data leakage
- Öznitelik seçimini yalnızca eğitim verisinde fit et
- Aynı seçimi test verisine uygula
- Çapraz doğrulamada, öznitelik seçimi her fold içinde yapılmalı

### Öznitelik seçimine overfitting
- Çok iterasyonla RFE eğitim setine overfit edebilir
- Seçim için kullanılan veride değil, ayrılmış veride doğrula
- Daha sağlam sonuçlar için stability selection kullan (subsample'larda tekrar)

## Adım 5: Production kontrol listesi

- [ ] Variance threshold ilk filtre olarak uygulandı
- [ ] Öznitelik seçimi yalnızca eğitim verisinde fit edildi
- [ ] Seçilen öznitelikler belgelendi (isimler, kullanılan yöntem, skorlar)
- [ ] Performans karşılaştırıldı: seçili öznitelikler vs tüm öznitelikler
- [ ] Çapraz doğrulama yapıldı, tek split değil
- [ ] Öznitelik seçimi eğitim pipeline'ına entegre edildi (manuel değil)
- [ ] Feature drift için monitoring kuruldu (seçili öznitelikler eskiyebilir)
