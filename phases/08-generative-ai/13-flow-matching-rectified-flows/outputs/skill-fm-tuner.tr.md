---
name: fm-tuner
description: Bir diffusion eğitim planını flow-matching / rectified-flow config'ine dönüştür.
version: 1.0.0
phase: 8
lesson: 13
tags: [flow-matching, rectified-flow, diffusion]
---

Bir diffusion-tarzı eğitim planı (veri, compute, schedule, hedef adım sayısı, kalite çıtası) verildiğinde, flow-matching karşılığını çıkar:

1. Schedule + interpolant. Linear (rectified flow), optimal transport (Lipman OT-CFM), variance-preserving ya da cosine. Tek cümlelik gerekçe.
2. Time sampling. Uniform, logit-normal (SD3) ya da mode-weighted. 1000 Hz'de uniform sampling uçlarda kapasiteyi israf ederse uyar.
3. Target. Velocity v = x_1 - x_0 (rectified flow) ya da alpha'(t)x_1 + sigma'(t)x_0 (CFM). Hangisi olduğunu belirt.
4. Optimizer + lr warmup. Transformer ölçeğinde kararlılık için beta2 = 0.95 ile AdamW dahil.
5. Reflow planı. 0, 1 ya da 2 reflow iterasyonu çalıştırılıp çalıştırılmayacağı; iterasyon başına bütçe ~ curated bir subset üzerinde tam yeniden çıkarım.
6. Adım sayıları. Eğitim adım sayısı hedefi, beklenen çıkarım adımları (20, 4, 2, 1), guidance scale aralığı.
7. Değerlendirme. Diffusion baseline'a karşı FID / CLIP-score, kalite vs adım sayısı plot'u.

v_1 yakınsamadan reflow yapmayı reddet (kötü bir model üzerinde reflow yalnızca kötü yönü pekiştirir). Üstünde consistency distillation olmadan 1-adım çıkarım önermeyi reddet. &gt; 20 adım çıkarım hedefleyen herhangi bir flow-matching modelini flag'le - bu kadar çok adım gerekiyorsa, reformülasyonu boşa harcadın.
