---
name: sd-toolkit-composer
description: Verilen girdiler için bir SD / Flux base üzerine ControlNet, LoRA ve IP-Adapter kompoze et.
version: 1.0.0
phase: 8
lesson: 08
tags: [controlnet, lora, ip-adapter, diffusion]
---

Bir görev (hedef görsel), girdiler (prompt, referans görseli, pose / depth / scribble / seg, konu kimliği) ve base model (SDXL, SD3.5, Flux.1-dev) verildiğinde, şunu çıkar:

1. ControlNet yığını. Hangi ControlNet'ler (canny / openpose / depth / scribble / seg / lineart / tile), hangi ağırlıkta, hangi sırayla. Ağırlıkların toplamının maks &lt;= 1.5.
2. LoRA yığını. İsimlendirilmiş LoRA'lar, rank, alpha. alpha &gt; 1.5 ise ya da birden fazla LoRA aynı kavramı hedefliyorsa uyar.
3. IP-Adapter. Yok, plain ya da FaceID varyantı; tipik 0.4-0.8 ağırlık.
4. Text prompt + negative prompt. Anahtar kelime sırası, token bütçesi, negative scaffolding.
5. Sampler + CFG + seed. Euler A / DPM-Solver++ / LCM; CFG scale base'e bağlı. Tekrar üretilebilir seed protokolü.
6. QA checklist. ControlNet drift, LoRA aşırı doygunluk, IP-Adapter identity sızıntısı, anatomi sorunları için görsel kontrol.

SDXL base üzerinde SD 1.5 LoRA yığmayı reddet (dimension uyumsuzluğu). 3+ ControlNet'i her biri 1.0 ağırlıkta çalıştırmayı reddet (feature çakışması). Kullanıcının SDXL ya da Flux için GPU bütçesi olduğunda herhangi bir SD 1.5 önerisini flag'le. &lt; 10 görsel üzerinde LoRA kimlik eğitimini muhtemel overfit olarak flag'le.
