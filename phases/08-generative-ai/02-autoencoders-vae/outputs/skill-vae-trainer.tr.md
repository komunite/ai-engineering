---
name: vae-trainer
description: Verilen bir veri seti ve aşağı akış kullanımı için VAE mimarisi, latent boyutu, beta schedule ve değerlendirme planı belirt.
version: 1.0.0
phase: 8
lesson: 02
tags: [vae, latent, generative]
---

Bir veri seti profili (modalite, çözünürlük, veri seti boyutu) ve aşağı akış kullanımı (yalnızca reconstruction, sampling ya da bir latent-diffusion / token-AR modeli için input-encoder) verildiğinde, şunu çıkar:

1. Varyant. Plain VAE, beta-VAE, VQ-VAE, RVQ (residual) ya da NVAE. Modalite ve aşağı akış kullanımına bağlı tek cümlelik gerekçe.
2. Mimari. Encoder / decoder topolojisi (conv downsample faktörü, channel genişliği, hidden dim, attention bloklar). Uygunsa public referans ağırlıkları belirt (`sd-vae-ft-ema`, Encodec, DAC, WAN-VAE).
3. Latent dim. Spatial ve channel dim'leri. Örnek başına toplam bit. Ham veriye göre sıkıştırma oranı.
4. Beta schedule. Warmup rampı, final değer ve kullanılıyorsa free-bits eşiği.
5. Değerlendirme planı. Reconstruction MSE / SSIM / PSNR, dim başına KL, active-dim sayısı, posterior-collapse alarm eşiği, `q(z|x)` ile prior arasında Frechet distance.

Eğitim başlangıcında beta > 0.5 olan bir VAE'yi shipping reddet (posterior collapse). Plain Gaussian VAE'yi görseller için final generator olarak kullanmayı reddet - bulanık olur; bunun yerine diffusion veya flow-matching modeli için latent encoder olarak kullan. Codebook kullanımı %20 altında olan herhangi bir VQ-VAE'yi yanlış yapılandırılmış codebook reset politikası olarak flag'le.
