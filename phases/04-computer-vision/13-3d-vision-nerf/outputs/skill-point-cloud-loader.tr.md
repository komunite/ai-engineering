---
name: skill-point-cloud-loader
description: Doğru normalization, centring ve point sampling ile .ply / .pcd / .xyz dosyaları için bir PyTorch Dataset yaz
version: 1.0.0
phase: 4
lesson: 13
tags: [3d-vision, point-cloud, data-loading, pytorch]
---

# Point Cloud Loader

Bir 3D scan dosya klasörünü eğitime hazır bir PyTorch `Dataset`'e çevir.

## Ne zaman kullan

- Yeni bir point cloud sınıflandırma / segmentasyon projesine başlarken.
- `.ply`, `.pcd` ve `.xyz` formatları arası geçerken.
- Hatasız eğitilen ama kötü yakınsayan bir modeli ayıklarken; sık sık data loader normalization yanlıştır.

## Girdiler

- `data_root`: point cloud dosyaları klasörü ve etiketler için opsiyonel CSV.
- `file_format`: ply | pcd | xyz | npy.
- `num_points`: sabit sampling boyutu, tipik olarak 1024 ya da 2048.
- `augmentation`: none | rotate | jitter | mixup.

## Normalization politikası

Her production point cloud pipeline'ı sırayla uygular:

1. Cloud'u **merkeze al**: centroid'i çıkar.
2. Birim küreye **ölçekle**: merkezden max mesafeye böl.
3. `num_points` point **örnekle**. Cloud daha çoksa, sadık şekil temsili için **farthest point sampling** (FPS) ya da hız için random sampling kullan. Daha azsa, point'leri tekrarla.
4. Point sırasını **karıştır** (sıra zaten model için önemli olmamalı, ama karıştırmak kazara sıra bağımlılıklarını kırar).

## Çıktı şablonu

```python
import numpy as np
import torch
from torch.utils.data import Dataset

try:
    import open3d as o3d
    HAS_O3D = True
except ImportError:
    HAS_O3D = False

def _read_ply(path):
    if HAS_O3D:
        pc = o3d.io.read_point_cloud(path)
        return np.asarray(pc.points, dtype=np.float32)
    # Fallback: minimal ascii-ply reader
    ...

def _fps(points, k):
    idx = np.zeros(k, dtype=np.int64)
    dist = np.full(len(points), np.inf)
    seed = np.random.randint(len(points))
    idx[0] = seed
    for i in range(1, k):
        dist = np.minimum(dist, ((points - points[idx[i-1]]) ** 2).sum(axis=1))
        idx[i] = int(np.argmax(dist))
    return idx

def normalise(points):
    centre = points.mean(axis=0)
    points = points - centre
    scale = np.max(np.linalg.norm(points, axis=1))
    return points / max(scale, 1e-8)

class PointCloudDataset(Dataset):
    def __init__(self, files, labels, num_points=1024, augment=False):
        self.files = files
        self.labels = labels
        self.num_points = num_points
        self.augment = augment

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        pts = _read_ply(self.files[i])
        pts = normalise(pts)
        if len(pts) >= self.num_points:
            idx = _fps(pts, self.num_points)
            pts = pts[idx]
        else:
            reps = int(np.ceil(self.num_points / len(pts)))
            pts = np.tile(pts, (reps, 1))[:self.num_points]
        # Tiling deterministik sırada point tekrarladığında özellikle
        # önemli olan kazara bağımlılıkları kırmak için point sırasını karıştır.
        np.random.shuffle(pts)
        if self.augment:
            theta = np.random.uniform(0, 2 * np.pi)
            R = np.array([[np.cos(theta), 0, np.sin(theta)],
                          [0, 1, 0],
                          [-np.sin(theta), 0, np.cos(theta)]], dtype=np.float32)
            pts = pts @ R
            pts = pts + np.random.normal(0, 0.02, pts.shape).astype(np.float32)
        pts = np.ascontiguousarray(pts, dtype=np.float32)
        return torch.from_numpy(pts).transpose(0, 1), int(self.labels[i])
```

## Rapor

```
[dataset]
  files:          <N>
  format:         <ply|pcd|xyz|npy>
  points_per_sample: <int>
  normalise:      centre + unit sphere
  sampling:       FPS | random
  augmentation:   <list>
```

## Kurallar

- Ölçekten önce her zaman merkeze al; sırayı değiştirmek "birim küre"nin anlamını değiştirir.
- Şekil görevleri için random sampling yerine FPS tercih et; her noktanın zaten önemli olduğu segmentasyon için random iyi.
- Değerlendirme sırasında asla augment etme; sadece eğitim sırasında.
- Point cloud dosyaları renk ya da normal'leri ekstra kanal olarak içeriyorsa, Dataset'i sadece xyz değil `(3 + C, num_points)` tensor döndürecek şekilde genişlet.
