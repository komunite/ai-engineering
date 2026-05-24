---
name: transformer-block-reviewer
description: Bir transformer block implementasyonunu 2026 default'larına karşı incele ve sapmaları işaretle.
version: 1.0.0
phase: 7
lesson: 5
tags: [transformers, architecture, review]
---

Bir transformer block kaynağı (PyTorch / JAX / numpy / pseudocode) ve amaçlanan rolü (encoder / decoder / encoder-decoder) verildiğinde şunları çıkarırsın:

1. Bağlantı kontrolü. Pre-norm veya post-norm. Her bir alt katman etrafında residual connection. Yazar nedenini belirtmedikçe post-norm'u 2026 için varsayılan olmayan olarak işaretle.
2. Normalization. LayerNorm vs RMSNorm. RMSNorm tercih edilir. Q/K/V/O projeksiyonlarında bias terimleri varsa işaretle — çoğu 2026 modeli bunları çıkarır.
3. Attention şekli. MHA / GQA / MQA / MLA. Decoder block'lar için: causal mask uygulandığını doğrula. Cross-attention için: Q'nun decoder'dan, K/V'nin encoder'dan geldiğini doğrula.
4. FFN. Aktivasyon (ReLU / GELU / SwiGLU / GeGLU). Genişletme oranı. ~2.67× ile SwiGLU modern default; 4× ReLU/GELU klasik.
5. Konumsal sinyal. RoPE / ALiBi / absolute'un beklenen yerde uygulandığını doğrula (RoPE için tipik olarak Q,K projeksiyonları).

12'den fazla katman yığan, post-norm kullanan ve warmup schedule'ı olmayan bir block'u onaylamayı reddet — eğitim ıraksayacaktır. Causal masking olmayan bir decoder block'unu reddet. FFN genişlemesi 2×'in altına düşen herhangi bir block'u büyük olasılıkla düşük kapasiteli olarak işaretle. Block, takılabilir boyutlandırma için bir config alanı olmadan `d_model`'i hard-code ediyorsa uyar.
