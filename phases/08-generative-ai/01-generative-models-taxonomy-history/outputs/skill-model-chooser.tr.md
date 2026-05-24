---
name: generative-model-chooser
description: Verilen bir görev ve bütçe için üretken model ailesi, backbone ve hosted alternatif seç.
version: 1.0.0
phase: 8
lesson: 01
tags: [generative, taxonomy]
---

Bir görev tanımı verildiğinde (modalite, alan, latency bütçesi, compute bütçesi, condition sinyali), şunu çıkar:

1. Aile. Explicit-tractable, explicit-approximate (VAE / diffusion), implicit (GAN), score / flow matching ya da token-AR. Modalite + latency'e bağlı tek cümlelik gerekçe.
2. Backbone + açık referans. Kullanıcının bugün fine-tune edebileceği bir pretrained open-weights model (örn. Stable Diffusion 3, Flux.1-dev, AudioCraft 2, StyleGAN3, 3D Gaussian Splatting).
3. Hosted alternatifler. Kalite / maliyet / latency dengesine göre sıralanmış üç production API (fal.ai, Replicate, Stability, Runway, Veo, Kling, ElevenLabs vb.).
4. Failure mode. Seçilen aile için bilinen patoloji (mode collapse, exposure bias, sampler drift, tokenizer artifact'ları, CLIP-score gaming).
5. Bütçe. Tek bir A100'de kabaca eğitim saati, örnek başına çıkarım maliyeti, VRAM tabanı.

Görev likelihood scoring gerektiriyorsa GAN önermeyi reddet. Yüksek çözünürlüklü gerçek-zamanlı kullanım için autoregressive-over-pixels önermeyi reddet. Listelenen açık backbone alanı zaten kapsıyorsa "sıfırdan eğit" tavsiyesini flag'le.
