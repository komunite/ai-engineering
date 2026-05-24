---
name: skill-depth-to-pointcloud
description: Doğru intrinsics handle'ı ile derinlik haritalarından point cloud inşa et ve .ply'ye export et
version: 1.0.0
phase: 4
lesson: 26
tags: [depth, point-cloud, 3d, intrinsics]
---

# Depth to Point Cloud

Bir derinlik haritası artı bir renk görselini görselleştirme ya da daha fazla 3D çalışma için export edilebilir dokumalı bir point cloud'a çevir.

## Ne zaman kullan

- Derinlik tahminlerini gerçek bir 3D sahne olarak görselleştirirken.
- Tek görselden seyrek 3D rekonstrüksiyonu bootstrap ederken.
- SfM başarısız olduğunda 3DGS eğitimi için girdi üretirken.
- Tahmin edilen derinliği LiDAR ground truth'a karşı karşılaştırırken.

## Girdiler

- `depth`: çıktıda istediğin aynı birimlerde derinliklerin `(H, W)` numpy array'i (metre önerilir).
- `rgb`: renklerin `(H, W, 3)` numpy array'i (uint8 ya da float32 [0, 1]).
- `intrinsics`: piksel birimlerinde `(fx, fy, cx, cy)`.
- Opsiyonel `depth_scale`: tahmin edilen derinlik birimlerini metreye çevirmek için çarpan.

## Pipeline

1. **Validate** — derinlik dahil etmeyi planladığın her yerde pozitif ve sonlu olmalı. Geçersiz pikselleri maskele.
2. **Lift** — piksel başına `X = (u - cx) * d / fx`, `Y = (v - cy) * d / fy`, `Z = d`.
3. **RGB ile eşle** — her 3D point eşleşen pikselden `(r, g, b)` üçlüsü alır.
4. **Export** — PLY (taşınabilir), `.xyz` (hafif), `.pcd` (Open3D-native), `.las`/`.laz` (geospatial).

## Implementation şablonu

```python
import numpy as np

def depth_to_point_cloud(depth, intrinsics, depth_scale=1.0, min_depth=0.1, max_depth=100.0):
    H, W = depth.shape
    fx, fy, cx, cy = intrinsics
    v, u = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    z = depth.astype(np.float32) * depth_scale
    valid = (z > min_depth) & (z < max_depth) & np.isfinite(z)
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    points = np.stack([x, y, z], axis=-1)
    return points, valid


def write_ply(path, points, colors=None, valid_mask=None):
    p = points.reshape(-1, 3)
    if valid_mask is not None:
        p = p[valid_mask.flatten()]
    lines = [
        "ply",
        "format ascii 1.0",
        f"element vertex {p.shape[0]}",
        "property float x", "property float y", "property float z",
    ]
    if colors is not None:
        c = colors.reshape(-1, 3).astype(np.uint8)
        if valid_mask is not None:
            c = c[valid_mask.flatten()]
        lines += ["property uchar red", "property uchar green", "property uchar blue"]
    lines.append("end_header")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
        if colors is not None:
            for pt, col in zip(p, c):
                f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f} {col[0]} {col[1]} {col[2]}\n")
        else:
            for pt in p:
                f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}\n")
```

## Rapor

```
[export]
  input depth shape:  (H, W)
  valid points:       <N> of <H*W>
  output format:      ply | xyz | pcd | las
  coordinate system:  camera (+X right, +Y down, +Z forward)
  scale:              metres | millimetres | normalised
```

## Kurallar

- Geçersiz derinliği (sıfır, NaN, inf, doymuş) her zaman maskele; onları dahil etmek orijinde bir çöp point bulutu üretir.
- Relative-depth modelden tahmin için, metric olarak export ETME; konvansiyonu bildirmek için çıktı dosya adına `relative_` öneki koy.
- Kamera koordinat konvansiyonunu tutarlı tut (OpenCV: +X sağ, +Y aşağı, +Z ileri). Aşağı akış araç OpenGL (+Y yukarı) bekliyorsa işaretleri değiştir.
- Dense sahneler için (> 1M point), bir subsample parametresi sun; > 500 MB PLY dosyaları her yerde yüklemek zor.
- "Makul" çıktı üretmek için derinliği asla sessizce clip etme; uyarılı eşiklerle açıkça clip et ki kullanıcılar neyin atıldığını bilsin.
