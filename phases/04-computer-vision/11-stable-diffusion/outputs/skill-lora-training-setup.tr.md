---
name: skill-lora-training-setup
description: Caption, rank, batch size ve learning rate dahil custom bir dataset için tam bir LoRA eğitim config'i yaz
version: 1.0.0
phase: 4
lesson: 11
tags: [computer-vision, stable-diffusion, lora, fine-tuning]
---

# LoRA Training Setup

Fine-tune niyetinin açıklamasını `diffusers` ya da `kohya_ss`'e geçirmeye hazır somut bir eğitim config'ine çevir.

## Ne zaman kullan

- Bir özne (kişi, nesne, karakter), bir stil (sanatçı, marka) ya da bir konsept (poz, ışık) için LoRA eğitirken.
- Mevcut bir LoRA'yı daha fazla veriyle genişletirken.
- Çıktısı eğitim görselleri için underfit ya da overfit olan bir LoRA turunu ayıklarken.

## Girdiler

- `purpose`: subject | style | concept
- `num_images`: mevcut eğitim görseli sayısı
- `base_model`: SD 1.5 | SDXL | SD3 | FLUX
- `gpu_vram_gb`: 8 | 12 | 16 | 24 | 48+
- `caption_source`: manual | BLIP2-generated | dataset-native

## Rank seçici

| Purpose | Rank | Alpha |
|---------|------|-------|
| Subject | 8-16 | rank |
| Style | 16-32 | rank * 2 |
| Concept | 32-64 | rank |

Daha yüksek rank = daha çok kapasite, küçük dataset'lerde daha çok overfitting riski. Alpha LoRA'nın etki gücünü ölçekler; `alpha == rank` güvenli varsayılan. Stiller belgelenmiş istisnadır: `alpha == rank * 2` daha güçlü bir stil itişi verir ama stili çok sert pişirme riski pahasına — sadece subject fidelity hedef değilse kullan.

## Eğitim adım hedefi

- 5-20 görselle `subject`: 500-1500 adım.
- 30-100 görselle `style`: 1500-4000 adım.
- 100+ görselle `concept`: 4000-10000 adım.

Aşırıya kaçma — eğitim görsellerini ezberlemiş bir LoRA genelleştiremez.

## Learning rate

- Text encoder LoRA: SD 1.5 için `1e-4`, SDXL için `5e-5`.
- U-Net LoRA: SD 1.5 için `1e-4`, SDXL için `1e-4`.
- FLUX / SD3: transformer için `5e-5`, text encoder'lar genellikle dondurulur.
- `num_images < 15` (subject) ya da 3000 adımdan uzun eğittiğinde LR'yi yarıya indir; küçük dataset'ler ve uzun turlar daha nazik güncellemeden faydalanır.

## Scheduler

- `cosine_with_warmup` (varsayılan): ilk %5-10 adımda warmup, sonra cosine decay. `steps >= 1000` olduğunda kullan; decay kuyruğu daha keskin final örnekler verir.
- `constant`: sadece çok kısa turlar için (`steps < 500`) ya da yeniden anneal etmeden mevcut öğrenilmiş feature'ları korumak istediğin bir önceki LoRA'yı sürdürürken kullan.

## Caption formatı

- Subject: her caption'a benzersiz bir trigger token ("myperson") önekle. Trigger token'ı nadir tut ki mevcut konseptleri ezmesin. Gerçek kelimelerden ve yaygın isimlerden kaçın.
- Style: her caption'ın sonuna benzersiz bir stil etiketi ekle ("...in mystyle style"). Etiketin kendisini nadir bir trigger token olarak ele al — zaten gerçek bir konsepte eşlenen `impressionism` değil, `mystyle`.
- Concept: konsepti her caption'da açıkla; trigger token yok. Konseptin kendisi (örn. "low-angle shot") çapa.

## Çıktı config

```yaml
model:
  base: <base_model HF id>
  precision: fp16 | bf16

lora:
  rank: <int>
  alpha: <int>
  targets: unet.cross_attention  # and/or unet.to_q, to_k, to_v, to_out

training:
  steps:          <int>
  batch_size:     <int, tuned to gpu_vram_gb>
  grad_accum:     <int, usually 1 on >=16 GB, 4 on <=12 GB>
  learning_rate:  <float>
  optimizer:      AdamW8bit | AdamW
  scheduler:      cosine_with_warmup | constant
  warmup_steps:   <int>
  save_every:     <int>

data:
  images_dir:     <path>
  caption_source: <manual | BLIP2 | native>
  trigger_token:   <string if purpose==subject>
  resolution:      <512 for SD 1.5, 1024 for SDXL>
  aspect_ratio_bucketing: true
  augmentation:
    flip:          true
    color_jitter:  false

validation:
  prompts:
    - "<trigger> ...test prompt..."
    - "<trigger> in a different scene"
  every_steps: 250
```

## Rapor

```
[lora setup]
  purpose:   <subject|style|concept>
  base:      <model>
  rank:      <int>
  steps:     <int>
  batch:     <int>   grad_accum: <int>
  lr:        <float>
  vram est.: <float> GB
```

## Kurallar

- Asla `rank > 64` önerme; bunun üstünde LoRA bir mini fine-tune olur ve "adapter" doğasını kaybeder.
- `num_images < 5` için güçlü uyar — 1-3 görselde identity LoRA'lar her seferinde overfit eder.
- `gpu_vram_gb < 12` için AdamW8bit ve gradient checkpointing zorunlu.
- `base_model == FLUX` ve `gpu_vram_gb < 24` ise, `schnell` varyantına yönlendir ve eğitimin daha yavaş olduğunu not düş.
- Validation prompt'ları asla atlama; örnek grid'i olmayan bir LoRA'yı değerlendirmek imkansız.
