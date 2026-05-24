---
name: skill-mot-evaluator
description: Ground-truth track'lere karşı MOTA / IDF1 / HOTA için tam bir değerlendirme harness'ı yaz
version: 1.0.0
phase: 4
lesson: 27
tags: [mot, evaluation, tracking, metrics]
---

# MOT Evaluator

Tracker'ının çıktısını standart MOTA/IDF1/HOTA pipeline'ına sar ki literatüre karşı adil karşılaştırabilesin.

## Ne zaman kullan

- MOT17 / MOT20 / DanceTrack / SportsMOT üzerinde yeni bir tracker'ı benchmark ederken.
- Kendi footage'inde ByteTrack'i BoT-SORT'a SAM 2'ye karşılaştırırken.
- Bir paper ya da PR açıklaması için tekrarlanabilir bir sayı üretirken.

## Girdiler

- `predictions`: frame başına `(track_id, x, y, w, h, confidence)` tuple listesi.
- `ground_truth`: frame başına `(gt_id, x, y, w, h)` tuple listesi.
- `iou_threshold`: MOTA için tipik 0.5; HOTA bir sweep kullanır.
- `evaluator`: `py-motmetrics` (MOTA, IDF1) ya da `TrackEval` (HOTA).

## Çıktı formatı kontratı

Hem `py-motmetrics` hem `TrackEval` belirli bir disk üzerinde format bekler:

```
# predictions.txt
<frame>,<track_id>,<x>,<y>,<w>,<h>,<confidence>,-1,-1,-1

# ground_truth.txt
<frame>,<gt_id>,<x>,<y>,<w>,<h>,1,-1,-1,-1
```

Frame'ler 1-indexed, box'lar (x1, y1, x2, y2) değil (x, y, w, h). Çoğu entegrasyon bug'ı dönüşümde yaşar.

## Adımlar

1. Tracker'ının çıktısını MOT Challenge text formatına çevir.
2. İki dosyada `py-motmetrics.io.loadtxt` çalıştır.
3. `mm.metrics.create().compute()` ile MOTA + IDF1 hesapla.
4. HOTA için, aynı dosyalarla ve `Metrics: HOTA` ile `TrackEval` çağır.
5. Dashboard'lar için sonuçları JSON olarak kaydet.

## Implementation taslağı

```python
import motmetrics as mm

def evaluate_mota_idf1(pred_path, gt_path):
    gt = mm.io.loadtxt(gt_path, fmt="mot15-2D")
    pred = mm.io.loadtxt(pred_path, fmt="mot15-2D")
    acc = mm.utils.compare_to_groundtruth(gt, pred, dist="iou", distth=0.5)
    metrics = mm.metrics.create().compute(
        acc, metrics=["num_frames", "mota", "motp", "idf1", "idp", "idr", "num_switches"]
    )
    return metrics


def write_mot_txt(predictions, path):
    with open(path, "w") as f:
        for frame_idx, detections in enumerate(predictions, start=1):
            for tid, x, y, w, h, conf in detections:
                f.write(f"{frame_idx},{tid},{x:.2f},{y:.2f},{w:.2f},{h:.2f},{conf:.3f},-1,-1,-1\n")
```

## Rapor

```
[mot evaluation]
  frames:     <int>
  gt tracks:  <int>
  pred tracks: <int>

[metrics]
  MOTA:       <float>
  MOTP:       <float>
  IDF1:       <float>
  IDP/IDR:    <float/float>
  ID switches: <int>
  HOTA:       <float>  (TrackEval'dan)
```

## Kurallar

- Çıktı text dosyasında her zaman 1-indexed frame kullan; MOT tooling bunu bekler.
- Yazmadan önce (x1, y1, x2, y2)'yi (x, y, w, h)'a çevir.
- Modern karşılaştırmalar için tek başına MOTA raporlama; IDF1 ve HOTA dahil et.
- MOT17'de private vs public detection'lara dikkat et — ayrı değerlendirilirler ve karıştırmak skorları şişirir.
- Sekans başına skorları logla; toplam tek zor sekans üzerindeki başarısızlıkları gizler.
