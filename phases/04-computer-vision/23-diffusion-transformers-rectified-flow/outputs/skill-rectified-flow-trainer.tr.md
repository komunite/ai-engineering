---
name: skill-rectified-flow-trainer
description: AdaLN DiT ve Euler sampling ile tam bir rectified-flow eğitim döngüsü yaz
version: 1.0.0
phase: 4
lesson: 23
tags: [diffusion, rectified-flow, DiT, training]
---

# Rectified Flow Trainer

Herhangi bir görsel tensor dataset'inde rectified flow ile küçük bir DiT'i başarıyla eğitebilecek temiz, minimal bir eğitim döngüsü üret.

## Ne zaman kullan

- SD3 / FLUX eğitim objektifini küçük ölçekte yeniden üretirken.
- Aynı veride rectified flow vs DDPM benchmark'ı yaparken.
- Standart olmayan bir domain (medikal, uydu) için custom bir rectified flow modeli inşa ederken.

## Girdiler

- `model`: `(x, t)` alan ve tahmin edilen velocity döndüren bir `nn.Module`.
- `dataset`: modelin domain'indeki temiz görsellerin bir iterable'ı.
- `optimizer`: AdamW, `lr=1e-4`, `weight_decay=0.01`, `betas=(0.9, 0.99)`.
- `scheduler`: warmup'lı cosine, varsayılan 1000 warmup adımı.

## Eğitim adımı

```python
def rectified_flow_train_step(model, x0, optimizer, device):
    model.train()
    x0 = x0.to(device)
    n = x0.size(0)
    t = torch.rand(n, device=device)                     # [0, 1]'de uniform
    epsilon = torch.randn_like(x0)
    x_t = (1 - t[:, None, None, None]) * x0 + t[:, None, None, None] * epsilon
    target_v = epsilon - x0                              # velocity hedefi
    pred_v = model(x_t, t)
    loss = F.mse_loss(pred_v, target_v)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()
```

## Sampling (Euler)

```python
@torch.no_grad()
def sample(model, shape, steps=20, device="cpu"):
    model.eval()
    x = torch.randn(shape, device=device)
    dt = 1.0 / steps
    t = torch.ones(shape[0], device=device)
    for _ in range(steps):
        v = model(x, t)
        x = x - dt * v
        t = t - dt
    return x
```

## İpuçları

- `torch.rand` uniform `t` kullan; logit-normal ya da SD3 tarzı `t`'nin ağırlıklı örneklemesi biraz yardımcı olur ama başlamak için gerekli değil.
- Model ağırlıklarının EMA'sı standart uygulama; `ema_model`'i 0.9999 decay ile sürdür.
- Conditional modeller için classifier-free guidance: eğitim sırasında %10 olasılıkla conditioning'i boş/null embedding ile değiştir; çıkarımda `v_uncond + w * (v_cond - v_uncond)`'u `w` 3-5 civarında karıştır.
- LDM tarzı eğitim için (FLUX, SD3), tüm döngü bir VAE latent uzayında çalışır; yukarıdaki temiz `x0` aslında `VAE.encode(image)`'dir.
- 32x32 toy dataset'te tipik yakınsama: 2000-5000 adım. Gerçek latent SD3 eğitiminde: yüz binlerce.

## Rapor

```
[rectified flow training]
  steps:        <int>
  final loss:   <float>
  ema decay:    <float>
  vae?:         yes | no
  cfg dropout:  <fraction>

[sampling]
  default steps: 20
  schnell / turbo target: 4
  full quality reference: 50+ (sadece karşılaştırma için)
```

## Kurallar

- RGB `uint8` veride image-space velocity hedefi ile rectified flow'u asla eğitme; önce zero mean, unit variance'a normalize et.
- Timestep-bucket başına eğitim loss'unu her zaman logla; erken timestep'ler (0 yakını) geç olanlardan (1 yakını) daha yüksek loss'a sahipse velocity parametrization muhtemelen yanlış bağlı.
- Aynı eğitim döngüsünde rectified flow velocity hedefi ile DDPM noise hedefini karıştırma; birini seç.
- Ampere+ GPU'larda bfloat16 eğitim kullan; float16 velocity büyüklüğü nedeniyle rectified flow'da bazen NaN grad üretir.
