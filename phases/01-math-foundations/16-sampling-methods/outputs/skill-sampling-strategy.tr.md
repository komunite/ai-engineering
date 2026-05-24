---
name: skill-sampling-strategy
description: Üretim, tahmin ya da çıkarım için doğru sampling yöntemini seç
version: 1.0.0
phase: 1
lesson: 16
tags: [sampling, mcmc, generation]
---

# Sampling Stratejisi Seçimi

Metin üretimi, Bayesçi çıkarım, Monte Carlo tahmini ve eğitim için doğru sampling yöntemini nasıl seçersin.

## Karar Kontrol Listesi

1. Çıktı mı üretiyorsun (metin, görüntü) yoksa bir nicelik mi tahmin ediyorsun (integral, beklenen değer)?
2. Hedef dağılımdan doğrudan sample alabiliyor musun yoksa sadece yoğunluğunu mu değerlendirebiliyorsun?
3. Hedef dağılım kesikli mi yoksa sürekli mi?
4. Örneklem uzayının boyutu nedir? Düşük (< 5), orta (5-100) ya da yüksek (> 100)?
5. Tam (exact) sample mı yoksa yaklaşık mı gerek?
6. Sampling operasyonu üzerinden gradient gerekli mi?

## Hangi yöntemi ne zaman kullanmalı

| Yöntem | Ne zaman kullanılır | Karmaşıklık | Exact? |
|---|---|---|---|
| Doğrudan sampling | CDF var ya da bir kütüphane fonksiyonu kullanabiliyorsun | Sample başına O(1) | Evet |
| Inverse CDF | Kapalı form CDF tersi bilinir (exponential, Cauchy) | Sample başına O(1) | Evet |
| Box-Muller | Kütüphane olmadan normal sample gerekli | Sample başına O(1) | Evet |
| Rejection sampling | Hedef PDF'i değerlendirebiliyorsun, düşük boyut (1-3) | Sample başına O(1/kabul) | Evet |
| Importance sampling | Bireysel sample değil, beklenen değer lazım | n sample için O(n) | Yaklaşık |
| Stratified sampling | Monte Carlo tahmini, düşük varyans isteniyor | n sample için O(n) | Yaklaşık |
| Metropolis-Hastings | Yüksek boyutlu, normalize edilmemiş yoğunluğu değerlendirebiliyorsun | Adım başına O(1) + burn-in | Asimptotik |
| Gibbs sampling | Her şartlı dağılımdan sample alabiliyorsun | Tam tarama başına O(d) | Asimptotik |
| HMC/NUTS | Yüksek boyutlu sürekli, pürüzsüz yoğunluk | Adım başına O(L * d) | Asimptotik |
| Temperature sampling | LLM metin üretimi, yaratıcılık kontrolü | Vocab boyutu V için O(V) | N/A |
| Top-k sampling | LLM üretim, olası olmayan token'ları çıkar | O(V log k) | N/A |
| Top-p (nucleus) | LLM üretim, adaptif aday seti | O(V log V) | N/A |
| Reparameterization | Gaussian sampling üzerinden gradient (VAE) | O(d) | Evet |
| Gumbel-Softmax | Kategorik sampling üzerinden gradient | k sınıf için O(k) | Yaklaşık |

## LLM üretim ayarları

| Kullanım | Temperature | Top-p | Top-k | Notlar |
|---|---|---|---|---|
| Gerçek bilgi Q&A | 0.0 (greedy) | -- | -- | Deterministik, rastgelelik yok |
| Kod üretimi | 0.2-0.5 | 0.9 | -- | Düşük yaratıcılık, yüksek tutarlılık |
| Genel sohbet | 0.7 | 0.9 | -- | Dengeli |
| Yaratıcı yazım | 0.9-1.2 | 0.95 | -- | Daha yüksek çeşitlilik |
| Beyin fırtınası | 1.0-1.5 | 0.95 | -- | Maksimum çeşitlilik, tutarlılık kaybedebilir |

Temperature ve top-p birleştirilebilir. Önce temperature uygula (logit'leri ölçekle), sonra top-p filtresi uygula.

## MCMC yöntem seçimi

| Özellik | Metropolis-Hastings | Gibbs | HMC/NUTS |
|---|---|---|---|
| Boyut | Herhangi | Herhangi (en iyi < 100) | Yüksek (100+) |
| Şartlılar gerekli | Hayır | Evet | Hayır |
| Gradient gerekli | Hayır | Hayır | Evet |
| Kabul oranı | ~%23'e ayarla | Her zaman %100 | ~%65'e ayarla |
| Korelasyon | Yüksek (random walk) | Orta | Düşük |
| Burn-in | Uzun | Orta | Kısa |
| Şuna iyi gelir | Keşif, basit modeller | Eşlenik modeller, Bayes ağları | Sürekli posterior'lar, derin olasılıksal modeller |

## Yaygın hatalar

- Yüksek boyutlarda rejection sampling kullanmak. Kabul oranı boyutla üstel düşer. 5 boyutun üstünde MCMC'ye geç.
- MCMC proposal varyansını çok yüksek ya da çok düşük ayarlamak. Çok yüksek: çoğu proposal reddedilir, chain takılır. Çok düşük: tüm proposal'lar kabul edilir, chain yavaş hareket eder. Random walk MH için ~%23 kabul hedefle.
- Burn-in'i unutmak. MCMC'nin ilk N sample'ı başlangıç noktası tarafından sapmaya uğramıştır. En az 1000 adım at (karmaşık dağılımlarda daha fazla).
- Hedeften çok farklı bir proposal ile importance sampling kullanmak. Birkaç sample devasa ağırlıklar alır ve tahmini güvenilmez kılar. Effective sample size'ı izle: ESS = (sum w_i)^2 / sum(w_i^2).
- Deterministik çıktı gerektiren görevlerde temperature > 0 kullanmak (örn. sınıflandırma, yapılandırılmış çıkarım). Greedy (T=0) ya da beam search kullan.
- Top-p'yi temperature ile birleştirmemek. Temperature tek başına uzun kuyruktaki çöp token'ları temizlemez. Top-p temizler.
- Standart sampling operasyonundan backprop yapmak. Sürekli (Gaussian) için reparameterization trick, kesikli (categorical) için Gumbel-Softmax kullan.

## Hızlı referans: varyans azaltma teknikleri

| Teknik | Nasıl çalışır | Varyans azaltma |
|---|---|---|
| Stratified sampling | Uzayı strata'lara böl, her birinden sample al | Her zaman <= standart MC |
| Antithetic variates | Hem U hem 1-U kullan | Monotonik fonksiyonlarda çalışır |
| Control variates | Ortalaması bilinen bir değişkeni çıkar | Korelasyon ile orantılı |
| Importance sampling | Daha iyi bir proposal'dan sample'ları yeniden ağırlıkla | Proposal kalitesine bağlı |
| Latin hypercube | Her boyutu bağımsız olarak strata'la | Yüksek boyutta stratified'tan iyi |
