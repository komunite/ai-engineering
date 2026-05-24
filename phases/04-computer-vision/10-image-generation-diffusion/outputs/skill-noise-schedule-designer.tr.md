---
name: skill-noise-schedule-designer
description: T ve hedef bozulma seviyesi verildiğinde linear, cosine ya da sigmoid beta schedule artı SNR plot üret
version: 1.0.0
phase: 4
lesson: 10
tags: [computer-vision, diffusion, noise-schedule, training]
---

# Noise Schedule Designer

Bir beta schedule, her diffusion adımında ne kadar sinyalin korunduğunu kontrol eder. Kötü schedule'lar her aşağı akış kararında eğitim verimliliğini ve örnek kalitesini sınırlar.

## Ne zaman kullan

- Yeni bir diffusion eğitim turuna başlarken ve T ile beta seçerken.
- Bulanık örnekler üreten (schedule çok agresif) ya da yapı öğrenemeyen (schedule çok yumuşak) bir diffusion modeli ayıklarken.
- Farklı schedule'lar raporlayan paper'lardaki tasarımları karşılaştırırken.

## Girdiler

- `T`: timestep sayısı, tipik olarak 100-1000.
- `type`: linear | cosine | sigmoid.
- `target_alpha_bar_final`: t=T'de tutulacak sinyal oranı, varsayılan 0.001 (%99.9 bozulmuş).
- Opsiyonel `image_resolution` — daha büyük görseller daha yavaş bozan schedule'lardan (cosine ya da shifted) faydalanır.

## Schedule formülleri

### Linear
```
beta_t = beta_start + (beta_end - beta_start) * (t - 1) / (T - 1)
```
Varsayılanlar: beta_start=1e-4, beta_end=0.02 (DDPM paper).

### Cosine (Nichol & Dhariwal, 2021)
```
alpha_bar_t = cos^2((t/T + s) / (1 + s) * pi/2)
beta_t = 1 - alpha_bar_t / alpha_bar_{t-1}
```
s = 0.008. Sinyali daha uzun tutar; düşük step sayısında daha iyi.

### Sigmoid
```
alpha_bar_t = 1 / (1 + exp(k * (t/T - 0.5)))
```
k = 6 - 12. İyi orta yol; bazı SDXL varyantlarınca kullanılır.

## Adımlar

1. Formüle göre betaları hesapla.
2. `alphas`, `alphas_cumprod`, `sqrt_alphas_cumprod`, `sqrt_one_minus_alphas_cumprod`'u önceden hesapla.
3. SNR_t = alpha_bar_t / (1 - alpha_bar_t) hesapla; zamana göre SNR özeti üret.
4. `alphas_cumprod[T-1]`'in `target_alpha_bar_final`'in %10'u içinde olduğunu doğrula; aksi halde beta_end (linear), s (cosine) ya da k (sigmoid)'yi ayarla ve tekrar dene.
5. Üç checkpoint raporla:
   - `t=T*0.25` — erken bozulma
   - `t=T*0.5` — orta
   - `t=T*0.75` — son yakını

## Rapor

```
[schedule]
  type:   <name>
  T:      <int>
  beta_start: <float>   beta_end: <float>

[signal retention]
  t=0.25T:  alpha_bar=<X>  SNR=<X>
  t=0.5T:   alpha_bar=<X>  SNR=<X>
  t=0.75T:  alpha_bar=<X>  SNR=<X>
  t=T:      alpha_bar=<X>  SNR=<X>

[warnings]
  - <if alpha_bar collapses before 0.75T>
  - <if beta_end produces NaN in log-SNR>
```

## Kurallar

- Herhangi `alpha_bar_t <= 0` olan schedule çıkarma; 1e-5 altındaki değerleri clamp et ve uyar.
- Düşük step sayılı sampling (< 30 adım) için varsayılan öneri cosine.
- `quality_target == research` için varsayılan linear — DDPM baseline'ları linear schedule ile raporlanır.
- `image_resolution > 256` ise, yüksek çözünürlüklerde daha çok sinyal tutmak için schedule'ı shift etmeyi (Chen, 2023) öner.
