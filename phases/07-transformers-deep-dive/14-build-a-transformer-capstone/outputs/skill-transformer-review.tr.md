---
name: transformer-review
description: Sıfırdan-transformer implementasyonunu 13 Faz 7 dersine karşı incele.
version: 1.0.0
phase: 7
lesson: 14
tags: [transformers, review, capstone]
---

Bir sıfırdan-transformer kod tabanı (PyTorch / JAX) verildiğinde, 2026 default'larına karşı incele ve eksik veya hatalı parçaları işaretle:

1. Attention. Causal mask mevcut. `sqrt(d_head)` ile ölçeklendirme. Multi-head split çalışıyor. Mevcutsa Flash Attention kullanılmış. d_model ≥ 1024 ise GQA belirtilmiş.
2. Positional encoding. RoPE (2026 tercihli) veya learned absolute (küçük modeller için kabul edilebilir). Sinusoidal'i tarihsel olarak işaretle.
3. Block bağlantısı. Pre-norm (post-norm değil). RMSNorm (LayerNorm değil). SwiGLU FFN (ReLU/GELU değil). Her alt katman etrafında residual'lar. Linear katmanlarda bias'lar çıkarılmış (modern default).
4. Eğitim. AdamW (veya 2026+ için Muon), linear warmup ile cosine LR schedule, 1.0'da gradient clipping, bf16 autocast. Token embedding ve lm_head arasında weight tying.
5. Loss. Her konumda shift-by-one cross-entropy. Varsa padding'i maskele. Sabit bir aralıkta eğitim ve doğrulama loss'unu logla.

Şunlardan herhangi birine sahip bir kod tabanını onaylamayı reddet: açık neden olmadan post-norm, 2026 üretim kodunda gerekçesiz LayerNorm, decoder self-attention'da eksik causal mask, küçük bir LM'de tied olmayan embedding'ler. İşaretle: doğrulama split'i yok, gradient clipping yok, warmup olmadan LR > 1e-3 veya fallback olmadan positional embedding aralığını aşan bir block_size. `python code/main.py` çalıştırıp uçtan uca son doğrulama loss'unun nano konfigürasyonunda tinyshakespeare üzerinde 2.5'in altına indiğini kontrol etmeyi öner.
