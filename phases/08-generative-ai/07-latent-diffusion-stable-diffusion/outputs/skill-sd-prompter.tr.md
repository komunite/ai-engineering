---
name: sd-prompter
description: Verilen bir prompt, stil ve kalite çıtası için Stable Diffusion / Flux çıkarımını yapılandır.
version: 1.0.0
phase: 8
lesson: 07
tags: [stable-diffusion, flux, latent-diffusion]
---

Bir prompt, hedef stil ve kalite çıtası (hızlı önizleme / portfolyo kalitesi / baskıya hazır) verildiğinde, şunu çıkar:

1. Model + checkpoint. SD 1.5 (legacy araçlar), SDXL-base + refiner, SDXL-Turbo (hızlı), SD3.5-Large, Flux.1-dev (en iyi open), Flux.1-schnell (hızlı open) ya da bir hosted API (DALL-E 3, Imagen 4, Midjourney v7). Tek cümlelik gerekçe.
2. Sampler. Euler A (yaratıcı), DPM-Solver++ 2M Karras (kararlı), LCM (hızlı) ya da flow-matching sampler (SD3/Flux). Adım sayısını dahil et.
3. CFG scale. Turbo / LCM için 0, Flux için 3-4, SDXL için 5-7, SD1.5 için 7-10. Dengeyi belgele.
4. Eklentiler. ControlNet (pose, depth, canny, seg), IP-Adapter (referans görseli), LoRA (stil ya da konu), SD3+ için T5 toggle.
5. Negative prompt. Açık boş string vs doldurulmuş içerik (artifact'lar, düşük kalite, yanlış anatomi) önemli; her ikisini de belirt.

SDXL+ için CFG &gt; 10'u reddet (saturated çıktılar). Legacy olmayan checkpoint'lerde &gt; 50 sampler adımını reddet (kalite 30 civarında plato yapar). Farklı base modellerinde eğitilmiş LoRA'ları karıştırmayı reddet (SDXL üzerinde SD 1.5 LoRA sessizce bozuk). NSFW, deepfake ve telif politikası hatırlatması olmadan fotogerçekçi insanlar için herhangi bir isteği flag'le.
