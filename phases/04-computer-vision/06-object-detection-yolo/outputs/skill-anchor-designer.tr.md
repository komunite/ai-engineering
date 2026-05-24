---
name: skill-anchor-designer
description: Bir ground-truth box dataset'i verildiğinde (w, h) üzerinde k-means çalıştır ve FPN seviyesi başına anchor setleri ile coverage istatistiklerini döndür
version: 1.0.0
phase: 4
lesson: 6
tags: [computer-vision, detection, anchors, kmeans]
---

# Anchor Designer

Anchor'lar, anchor tabanlı bir detector'daki tek dataset'e en özgü hyperparameter'dır. Varsayılan COCO anchor'ları hücre kültürü görsellerinde, uydu tile'larında ya da küçük nesneli gözetimde yetersiz kalır. Bu skill, hedef veriye gerçekten uyan anchor'ları türetir.

## Ne zaman kullan

- Yeni bir dataset'te ilk eğitim turundan önce.
- Aksi halde sağlıklı bir modelde çok küçük ya da çok büyük nesnelerde recall zayıf olduğunda.
- Box boyutu dağılımının kaymış olabileceği büyük bir dataset genişlemesinden sonra.

## Girdiler

- `boxes`: ya `(cx, cy, w, h)` ya da `(x1, y1, x2, y2)` formatında shape (N, 4) numpy array; en az 1000 pozitif box önerilir.
- `num_anchors_per_level`: genellikle 3.
- `num_fpn_levels`: genellikle 3 (P3, P4, P5) ya da 4.
- `input_size`: eğitim çözünürlüğü HxW.
- Opsiyonel `strides`: seviye başına stride'lar; verilmezse `[8, 16, 32, 64]`'ün ilk `num_fpn_levels` girdisini al. Detector'ın FPN'i farklı stride'lara sahipse daha uzun ya da daha kısa bir array açıkça geç.

## Adımlar

1. **Box'ları normalize et**: `input_size`'da piksel birimlerinde `(w, h)` çiftlerine. w ya da h < 2 piksel olanları at.

2. **k-means çalıştır** `(w, h)` çiftleri üzerinde, `k = num_anchors_per_level * num_fpn_levels`. Mesafe fonksiyonu olarak Öklid değil, `1 - IoU(box, cluster)` kullan — `(w, h)` üzerinde Öklid ince uzun box'ları ve kare box'ları birlikte çöker. Tüm box'lar eşit katkıda bulunur (ağırlıksız); class-imbalanced bir dataset'in varsa ve daha büyük box recall'u istiyorsan, weight vector geçmek yerine girdi array'inde nadir sınıf box'larını tekrarla.

3. **Cluster'ları alana göre sırala**, artan. `num_anchors_per_level`'lık `num_fpn_levels` gruba böl. En küçük alanlar en yüksek çözünürlüklü seviyeye gider (en küçük stride).

4. **Seviye başına coverage istatistikleri** hesapla:
   - Her ground-truth box'ın o seviyedeki en iyi anchor'ına `median IoU`.
   - `recall@IoU=0.5` — en iyi anchor'ı IoU >= 0.5 olan box yüzdesi.
   - `area coverage` — alanı seviyenin `[anchor_min_area / 4, anchor_max_area * 4]`'üne düşen box oranı.

5. **Seviye başına anchor'ları raporla** ve `recall@IoU=0.5 < 0.9` olan seviyeleri işaretle; o seviyenin anchor'ları veriyle iyi eşleşmiyor ve yeniden ayarlanmalı ya da seviye başına anchor sayısı arttırılmalı.

## Rapor formatı

```
[anchor-designer]
  total boxes:         <N>
  clusters:            <k>
  distance metric:     1 - IoU

[level P3  stride=8]
  anchors (w, h):      [(A, B), (C, D), (E, F)]
  median IoU:          <X>
  recall@IoU=0.5:      <X>
  coverage:            <X>
  flag:                ok | retune

[level P4  stride=16]
  ...

[summary]
  overall recall@IoU=0.5: <X>
  smallest anchor:        <w x h>
  largest anchor:         <w x h>
  recommendation:         <one sentence if any level flagged>
```

## Kurallar

- Her zaman IoU tabanlı mesafe kullan; Öklid k-means görsel olarak makul ama ampirik olarak daha kötü anchor'lar üretir.
- Cluster'ları alana göre sırala, sonra artan sırada seviyelere ata.
- `num_anchors_per_level = 1` ise k-means'i tamamen atla: box'ları alana göre `num_fpn_levels` bin'e böl (örn. 3 seviye için tertile), ve her seviyenin anchor'ını bin başına median (w, h)'ye ayarla. Bu, küçük dataset'lerde `k = num_fpn_levels` ile k-means çalıştırmaktan daha sağlamdır.
- Negatif anchor boyutları asla çıkarma; 1'e clamp et.
- Dataset'in < 200 box'u varsa, kullanıcıyı anchor aramasının güvenilmez olduğu konusunda uyar ve varsayılan COCO anchor'ları + daha fazla eğitim verisi kullanmasını öner.
