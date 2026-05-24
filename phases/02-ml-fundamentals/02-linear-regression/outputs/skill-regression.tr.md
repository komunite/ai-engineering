---
name: skill-regression
description: Veri karakteristikleri ve problem kısıtlarına göre doğru regresyon yaklaşımını seç
version: 1.0.0
phase: 2
lesson: 2
tags: [regression, linear-regression, polynomial-regression, ridge, regularization]
---

# Regresyon Strateji Rehberi

Regresyon sürekli değerleri tahmin eder. Doğru yaklaşım; öznitelikler ile hedef arasındaki ilişkiye, öznitelik sayısına ve overfitting riskine bağlıdır.

## Karar Kontrol Listesi

1. Öznitelikler ile hedef arasındaki ilişki yaklaşık olarak doğrusal mı?
   - Evet: sıradan doğrusal regresyonla başla
   - Hayır: polinom öznitelikler ya da doğrusal olmayan bir model dene

2. Örneklere göre kaç özniteliğin var?
   - Az öznitelik, çok örnek: sıradan doğrusal regresyon iyi çalışır
   - Çok öznitelik, az örnek: regularization kullan (Ridge ya da Lasso)
   - Örnekten daha fazla öznitelik: öznitelik seçimi için Lasso (L1), ya da tüm ağırlıkları küçültmek için Ridge (L2)

3. Yorumlanabilirlik gerekli mi?
   - Evet: az öznitelikli doğrusal regresyon, ya da otomatik öznitelik seçimi için Lasso
   - Hayır: polinom öznitelikler, ya da ağaç tabanlı modellere veya sinir ağlarına geç

4. Veri setin küçük mü (10.000 satırın altı)?
   - Hız için normal denklemi (kapalı form çözüm) kullan
   - Güvenilir değerlendirme için çapraz doğrulama şart

5. Veri setin büyük mü (milyonlarca satır)?
   - Stochastic gradient descent (SGD) ya da mini-batch gradient descent kullan
   - Normal denklem O(n^3) matris tersi nedeniyle çok yavaş

## Hangi yaklaşımı ne zaman kullanmalı

**Sıradan Doğrusal Regresyon**: herhangi bir regresyon görevi için baseline. Buradan başla. R-squared kabul edilebilirse ve model basitse, burada dur.

**Polinom Regresyon**: dağılım grafiği bir doğru değil, eğri gösteriyor. Derece 2 ile başla. Sadece doğrulama performansıyla gerekçelendirilirse artır. Derece > 5 neredeyse her zaman overfit eder.

**Ridge Regression (L2)**: çok sayıda korelasyonlu öznitelik. Tüm ağırlıklar sıfıra doğru küçülür ama hiçbiri tam olarak sıfır olmaz. Tüm özniteliklerin katkıda bulunduğuna inandığında iyi.

**Lasso Regression (L1)**: çok öznitelik ve yalnızca birkaçının önemli olduğundan şüphelendiğin durumlar. Lasso, alakasız öznitelik ağırlıklarını tam olarak sıfıra çekerek otomatik öznitelik seçimi yapar.

**Elastic Net**: L1 ve L2 cezalarını birleştirir. Çok sayıda korelasyonlu özniteliğin olduğu ve bir miktar öznitelik seçimi istediğin durumlarda kullan.

## Yaygın hatalar

- Gradient descent öncesi öznitelik ölçeklemeyi atlamak (yakınsama aşırı yavaşlar)
- Hiperparametreleri tune etmek için test set performansını kullanmak (validation set ya da çapraz doğrulama kullan)
- Doğrulama hatasını kontrol etmeden yüksek dereceli polinom fit etmek (training R^2 derece ile her zaman artar)
- Residual plot'ları görmezden gelmek (residual'lar bir desen gösteriyorsa R^2 yanıltıcı olabilir)
- R^2'yi tek metrik olarak ele almak (residual dağılımı, MAE ve domain'e özgü eşikleri kontrol et)

## Hızlı referans

| Yöntem | Ne zaman kullanılır | Regularization | Öznitelik seçimi |
|--------|------------|---------------|-------------------|
| OLS | Baseline, az öznitelik | Yok | Manuel |
| Ridge | Çok öznitelik, hepsi ilgili | L2 (shrink) | Hayır |
| Lasso | Çok öznitelik, az ilgili | L1 (zero out) | Otomatik |
| Elastic Net | Çok korelasyonlu öznitelik | L1 + L2 | Kısmi |
| Polinom | Doğrusal olmayan ilişki | Üstüne Ridge/Lasso ekle | Manuel derece seçimi |
