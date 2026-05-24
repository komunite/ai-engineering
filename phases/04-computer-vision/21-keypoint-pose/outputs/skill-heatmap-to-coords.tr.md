---
name: skill-heatmap-to-coords
description: Her production poz modelince kullanılan sub-pixel heatmap-to-coordinate rutinini yaz
version: 1.0.0
phase: 4
lesson: 21
tags: [keypoint, pose, subpixel, inference]
---

# Heatmap to Coords

Ham keypoint heatmap'lerini sub-pixel hassas koordinatlara çevir. Her poz pipeline'ında en ucuz accuracy yükseltmesi.

## Ne zaman kullan

- Heatmap tabanlı bir keypoint modelini deploy ederken.
- Poz metriklerini benchmark ederken — OKS sub-pixel accuracy'ye son derece hassas.
- Poz kodunu bir framework'ten diğerine taşırken.

## Girdiler

- `heatmaps`: `(N, K, H, W)` tensor, modelden keypoint başına heatmap'ler.
- `confidence_threshold`: peak'i bu değerin altında olan keypoint'leri at.

## Adımlar

1. Her heatmap'in **argmax**'ını al ve integer peak konumunu bul.
2. **First-difference offset** — komşu piksellerden sub-pixel offset tahmin et. `0.25` katsayısı `sigma >= 1` olan Gaussian heatmap'ler için kalibre edilmiş bir sezgiseldir; ilkeli sub-pixel kurtarımı için tam quadratic fit (DARK) ya da Gaussian fit kullan.

```
dx = 0.25 * sign(heatmap[y, x+1] - heatmap[y, x-1])
dy = 0.25 * sign(heatmap[y+1, x] - heatmap[y-1, x])
```

DARK / quadratic varyantı için, lokal quadratic kullanarak yaklaş:

```
dx = -0.5 * (heatmap[y, x+1] - heatmap[y, x-1])
        / (heatmap[y, x+1] - 2 * heatmap[y, x] + heatmap[y, x-1] + eps)
```

Quadratic fit zirve heatmap'lerde daha doğru; sign tabanlı offset heatmap'ler gürültülü olduğunda daha güvenli varsayılan.

3. Integer peak'e **offset ekle**.
4. **Confidence** — keypoint başına peak değerini döndür; istemciler düşük güvenli tahminleri maskelemek için kullanır.
5. **Sınır durumu** — peak bir eksenin ilk ya da son pikseline düştüğünde, komşulardan biri clamp'lenir; offset sıfıra çöker, bu en güvenli fallback'tir.

## Çıktı şablonu

```python
import torch

def heatmap_to_coords_subpixel(heatmaps, threshold=0.2):
    N, K, H, W = heatmaps.shape
    flat = heatmaps.reshape(N, K, -1)
    conf, idx = flat.max(dim=-1)
    ys = (idx // W).float()
    xs = (idx % W).float()

    ys_int = ys.long()
    xs_int = xs.long()

    x_minus = (xs_int - 1).clamp(min=0)
    x_plus = (xs_int + 1).clamp(max=W - 1)
    y_minus = (ys_int - 1).clamp(min=0)
    y_plus = (ys_int + 1).clamp(max=H - 1)

    batch_idx = torch.arange(N).view(-1, 1).expand(-1, K)
    kp_idx = torch.arange(K).view(1, -1).expand(N, -1)

    dx_raw = (heatmaps[batch_idx, kp_idx, ys_int, x_plus]
              - heatmaps[batch_idx, kp_idx, ys_int, x_minus])
    dy_raw = (heatmaps[batch_idx, kp_idx, y_plus, xs_int]
              - heatmaps[batch_idx, kp_idx, y_minus, xs_int])
    dx = 0.25 * torch.sign(dx_raw)
    dy = 0.25 * torch.sign(dy_raw)

    at_left = xs_int == 0
    at_right = xs_int == (W - 1)
    at_top = ys_int == 0
    at_bottom = ys_int == (H - 1)
    dx = torch.where(at_left | at_right, torch.zeros_like(dx), dx)
    dy = torch.where(at_top | at_bottom, torch.zeros_like(dy), dy)

    refined_x = xs + dx
    refined_y = ys + dy
    coords = torch.stack([refined_x, refined_y], dim=-1)
    mask = conf >= threshold
    return coords, conf, mask
```

## Rapor

```
[subpixel decode]
  keypoints:   K
  threshold:   <float>
  valid_rate:  fraction of keypoints above threshold
```

## Kurallar

- Komşu indekslerini her zaman geçerli aralığa clamp et; kenardaki keypoint'lerin sıfır-fark offset'i olur ama çökme olmaz.
- İstemcilerin düşük güvenli noktaları maskeleyebilmesi için confidence'ı koordinatlarla birlikte döndür.
- Sub-pixel rafinaj sadece heatmap zirve etrafında düz olduğunda yardımcı olur — eğitimin sigma >= 1 olan bir Gaussian hedef kullandığını kontrol et.
- Çok küçük heatmap çözünürlükleri için (< 48x48), koordinat çıkarmadan önce heatmap'i tam görsel boyutuna upsample etmeyi düşün; sub-pixel offset stride ile ölçeklenir.
