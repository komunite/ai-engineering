---
name: skill-dcgan-scaffold
description: z_dim, image_size ve num_channels'tan başlayarak eğitim döngüsü ve örnek kaydedici dahil tam bir DCGAN scaffold'u yaz
version: 1.0.0
phase: 4
lesson: 9
tags: [computer-vision, gan, dcgan, scaffolding]
---

# DCGAN Scaffold

Üç parametre verildiğinde, hedef görsel çözünürlüğüne göre doğru boyutlandırılmış bir mimariyle çalıştırılabilir bir DCGAN proje iskeleti çıkar.

## Ne zaman kullan

- Küçük bir dataset üzerinde yeni bir generative deneye başlarken.
- Çalışan minimal bir örnekle DCGAN temellerini öğretirken.
- Conditional GAN'ler prototipleştirilirken (etiket enjeksiyonu aynı scaffold'da olur).

## Girdiler

- `image_size`: 32, 64, 128'den biri (iki kuvveti olmalı).
- `num_channels`: 1 (grayscale) ya da 3 (RGB).
- `z_dim`: tipik olarak 64 ya da 128.
- `with_spectral_norm`: yes | no; varsayılan yes.

## Mimari boyutlandırma

G'deki transposed conv blok sayısı ve D'deki strided conv blok sayısı `image_size`'a bağlıdır:

| image_size | G blocks | D blocks |
|------------|----------|----------|
| 32         | 4        | 4        |
| 64         | 5        | 5        |
| 128        | 6        | 6        |

Her ek blok spatial boyutu iki katına çıkarır (G) ya da yarıya indirir (D). Feature sayısı 32'den başlar ve `feat_base * 2^block_index` ile ölçeklenir.

## Çıktı dosyaları

- `model.py` — Generator + Discriminator class'ları
- `train.py` — eğitim döngüsü, loss, optimizer kurulumu
- `sample.py` — örnek grid kaydedicisi
- `config.json` — hyperparameter'lar
- `README.md` — 10 satırlık quickstart

## Rapor

```
[scaffold]
  image_size:       <int>
  num_channels:     <int>
  z_dim:            <int>
  spectral_norm:    yes | no

[arch]
  G blocks:         <N>, channels: [list]
  D blocks:         <N>, channels: [list]
  G params (est):   <N>
  D params (est):   <N>

[training defaults]
  optimizer:   Adam(lr=2e-4, betas=(0.5, 0.999))
  batch_size:  64
  epochs:      50
  sample_every: 1 epoch

[files written]
  - model.py
  - train.py
  - sample.py
  - config.json
  - README.md
```

## Kurallar

- G çıktısında her zaman `nn.Tanh()` kullan ve eğitim sırasında veriyi [-1, 1]'e ölçekle.
- D'de her zaman `LeakyReLU(0.2)` kullan.
- `with_spectral_norm == yes` ise, D'deki her conv'u `spectral_norm()` ile sar ve D'den BatchNorm'u kaldır. G'de BatchNorm'u tut.
- image_size > 128 için scaffold çıkarma — DCGAN bunun üstünde kararsızlaşır; kullanıcıyı StyleGAN ya da bir diffusion model'e yönlendir.
