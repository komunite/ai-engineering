---
name: attention-shapes
description: Attention implementasyonlarındaki shape bug'larını hata ayıkla
phase: 5
lesson: 10
---

Bozuk bir attention implementasyonu verildiğinde shape uyumsuzluğunu tespit edersin. Çıkar:

1. Hangi matrisin shape'i yanlış. Tensor'u adlandır.
2. `(d_s, d_h, d_attn, T_enc, T_dec, batch_size)` kullanılarak çıkarılan doğru shape'i ne olmalı.
3. Tek satırlık fix. Transpose, reshape ya da projection.
4. Regresyonu yakalamak için bir test. Tipik olarak `output.shape == (batch, T_dec, d_h)` ve `weights.shape == (batch, T_dec, T_enc)` ve `weights.sum(dim=-1)` değerinin 1'e yakın olduğunu assert et.

Sessizce broadcast eden fix'leri önermeyi reddet. Broadcast-gizleyen bug'lar sonradan sessiz doğruluk kaybı olarak ortaya çıkar.

Bahdanau karışıklığında, decoder girdisinin `s_{t-1}` (step-öncesi state) olduğunu vurgula. Luong için `s_t` (step-sonrası state). Dot-product attention'da ilk seferde en sık görülen hata query/key boyut uyumsuzluğudur — bunu açıkça işaretle.
