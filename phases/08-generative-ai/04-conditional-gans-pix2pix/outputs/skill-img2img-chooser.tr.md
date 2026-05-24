---
name: img2img-chooser
description: Eşli vs eşsiz veri, alan spesifikliği ve latency bütçesi verildiğinde bir image-to-image yaklaşımı seç.
version: 1.0.0
phase: 8
lesson: 04
tags: [pix2pix, img2img, conditional]
---

Bir görev tanımı verildiğinde (kaynak alan, hedef alan, veri kullanılabilirliği - eşli/eşsiz/N örnek, latency bütçesi, kalite çıtası), şunu çıkar:

1. Yaklaşım. Pix2Pix (eşli, dar), Pix2PixHD (eşli, yüksek çözünürlüklü), CycleGAN (eşsiz), SPADE (seg-to-image) ya da SD3 / Flux.1 üzerinde ControlNet varyantı (genel, open-domain).
2. Eğitim veri spec'i. Minimum çift sayısı, çözünürlük, augmentation'lar, lisans değerlendirmeleri.
3. Mimari. G (U-Net derinliği, channel genişliği), D (PatchGAN receptive field, spectral norm), loss ağırlıkları (adv, L1, VGG-perceptual).
4. Çıkarım latency'si. Tek bir consumer GPU'da (RTX 4090, M3 Max) hedef ms/görsel, çözünürlük dengesi.
5. Değerlendirme. Tutulan eşli veriye karşı LPIPS, 5k örnek üzerinde FID, göreve özgü metrikler (seg görevleri için mIoU, super-resolution için PSNR), insan tercihi.

Veri eşsiz iken Pix2Pix önermeyi reddet - yerine CycleGAN ya da ControlNet reçete et. 500'den az çift ile eşli model eğitmeyi augmentation / pretraining tavsiyesi olmadan reddet. "Keyfi text prompt" diyen herhangi bir isteği flag'le - bunlar eşli GAN değil, diffusion + ControlNet gerektirir.
