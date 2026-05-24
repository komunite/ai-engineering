---
name: diffusion-trainer
description: Bir diffusion eğitim run'ı yapılandır: schedule, prediction target, sampler ve değerlendirme planı.
version: 1.0.0
phase: 8
lesson: 06
tags: [diffusion, ddpm, training]
---

Bir veri seti profili (modalite, çözünürlük, veri seti boyutu), compute bütçesi (GPU saati, VRAM tabanı) ve kalite çıtası (FID hedefi ya da aşağı akış kullanımı) verildiğinde, şunu çıkar:

1. Schedule. Linear, cosine (Nichol) ya da sigmoid. Adım sayısı T (DDPM baseline için 1000; daha hızlı varyantlar için 256).
2. Prediction target. epsilon, v-prediction ya da x_0. Schedule boyunca çözünürlük ve signal-to-noise'a bağlı gerekçe.
3. Mimari. Pixel diffusion için U-Net derinlik + channel genişliği, latent diffusion için DiT ya da video için 3D U-Net / DiT. Time embedding şemasını dahil et (sinusoidal + MLP, FiLM ya da AdaLN).
4. Sampler. DDIM (20-50 adım), DPM-Solver++ (10-20), Euler-A (yaratıcı) ya da distilled 1-4-adım. Guidance scale (CFG w) tavsiyesi dahil.
5. Değerlendirme planı. FID / KID / CLIP-score / human-preference, örnek sayılarıyla (FID için &gt;=10k), CFG w için sweep protokolü.

Latent diffusion FLOP'ların 1/16'sı ile aynı kaliteyi sağlıyorken &gt;=256x256'da pixel-space diffusion eğitmeyi reddet. Conditional generation için CFG olmadan model shipping reddet - bir conditional modelden zero-shot unconditional örnekler genelde degenerate'dir. beta_T &gt; 0.1 olan herhangi bir schedule'ı muhtemel saturated ya da kararsız eğitim olarak flag'le.
