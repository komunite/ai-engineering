---
name: skill-pipeline-budget-planner
description: Hedef latency ve throughput verildiğinde her pipeline aşamasına zaman bütçesi ata ve hangi aşamanın bütçeyi ilk kaçıracağını işaretle
version: 1.0.0
phase: 4
lesson: 16
tags: [vision, pipeline, performance, deployment]
---

# Pipeline Budget Planner

Bir latency/throughput hedefini her ekip üyesinin hangi sayıya doğru mühendislik yaptığını bildiği bir aşama-aşama bütçeye çevir.

## Ne zaman kullan

- Yeni bir bilgisayarlı görü servisi inşa etmeden önce, her aşama için beklenti belirlemek için.
- İlk benchmark'tan sonra, hangi aşamanın bütçesinden en uzakta olduğunu görmek için.
- SLA değiştiğinde ve bütçelerin yeniden müzakere edilmesi gerektiğinde.

## Girdiler

- `p95_latency_target_ms`: request başına bütçe.
- `target_qps`: replica başına throughput.
- `stages`: `{ name: str, current_ms: float }` listesi.

## Tahsis kuralları

Mevcut ölçüm yoksa yedi standart aşama için varsayılan tahsis:

| Aşama | Pay |
|-------|-------|
| decode + preprocess | 15% |
| detector forward | 55% |
| postprocess detections (NMS, clamp) | 5% |
| sınıflandırıcı için crop + resize | 5% |
| classifier forward | 15% |
| schema validation | <1% |
| response serialization | 4% |

GPU-bound pipeline'larda (cloud), detector payı sık sık %70'e çıkar. CPU'da, preprocessing ve classifier batching daha çok yer.

## Rapor

```
[budget plan]
  p95 target:  <ms>
  throughput:  <qps per replica>

| stage               | target_ms | current_ms | headroom | gate |
|---------------------|-----------|------------|----------|------|
| decode+preprocess   | ...       | ...        | ...      | ok|X |
| detector            | ...       | ...        | ...      | ok|X |
| ...                 | ...       | ...        | ...      |      |

[bottleneck]
  stage:  <name>
  miss:   <ms over budget>
  lever:  <specific action>

[levers]
  decode+preprocess:   Pillow-SIMD, libjpeg-turbo, NVJPEG ile GPU'da decode
  detector:            daha küçük backbone, daha düşük input resolution, INT8, TensorRT
  postprocess:         GPU-side NMS (torchvision.ops), fused mask'lar
  crop+resize:         grid_sample ile GPU crop, batched interpolate
  classifier:          daha küçük backbone, INT8, sıcak cache, batch
  schema:              hot path'te validation atla, sadece sınırlarda validate et
  response:            orjson, stream protobuf
```

## Kurallar

- Schema validation'ı production path'ten düşürmeyi asla önerme; bunun yerine sınıra taşımayı öner.
- Preprocessing bütçesini kaçırıyorsa, modeli değiştirmeden önce her zaman Pillow-SIMD ya da NVJPEG dene.
- Detector kaçışı hedefin %30'undan fazlaysa, mevcut olanı optimize etmek yerine modeli değiştir.
- current_ms > 1.1 * target_ms olduğunda gate'i `X` olarak işaretle; bütçenin %10'u içindeyse `ok` işaretle.
