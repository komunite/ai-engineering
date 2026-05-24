---
name: skill-image-tensor-inspector
description: Herhangi bir görsel şeklindeki tensor ya da array'i inceleyip dtype, layout, range bilgisini ve raw, normalized ya da standardized görünüp görünmediğini raporla
version: 1.0.0
phase: 4
lesson: 1
tags: [computer-vision, debugging, preprocessing, tensors]
---

# Image Tensor Inspector

Bir bilgisayarlı görü pipeline'ının herhangi bir noktasında, elinde görsel şeklinde bir array varken tam olarak hangi durumda olduğunu bilmen gereken her an için teşhis skill'i.

## Ne zaman kullan

- Bir pretrained model çöp tahmin döndürüyor ve ön işlemeden şüpheleniyorsun.
- OpenCV ile torchvision arasında pipeline taşıyorsun ve kanal sırası belirsiz.
- Birden çok framework'ten katmanlar üst üste binmiş ve batch ekseni hep yanlış yerde çıkıyor.
- Loss'un `log(num_classes)`'de takıldığı bir eğitim döngüsünü ayıklıyorsun.

## Girdiler

- `x`: herhangi 2-D, 3-D ya da 4-D array benzeri (NumPy, PyTorch, JAX).
- Opsiyonel `expected`: kontrol edilecek değişmezlerin dict'i, örn. `{"layout": "CHW", "range": "standardized"}`.

## Adımlar

1. **Backend'i çöz** — `x`'in NumPy, Torch ya da JAX olduğunu tespit et. Orijinali değiştirmeden inceleme için NumPy'a çevir.

2. **Rank'ı sınıflandır**:
   - rank 2 -> tek kanallı görsel (H, W).
   - rank 3 -> son eksen 1, 3 ya da 4 ise ve diğer ikisinden kesinlikle küçükse `HWC`; aksi halde `CHW`.
   - rank 4 -> eksen 1 {1, 3, 4} içindeyse **ve** eksen 2 ya da eksen 3'ten biri 16'dan büyükse `NCHW` tercih et; aksi halde `NHWC` tercih et. Sadece eksen 1'e bakmak `(3, 4, 224, 3)` gibi küçük görsel NHWC batch'lerini yanlış sınıflandırır.
   - Belirsiz durumları (örn. `(1, 3, 3, 3)`) her zaman tahmin yerine `ambiguous` olarak işaretle; çağıranın `expected` sağlamasını iste.

3. **Dtype ve range'i sınıflandır**:
   - `uint8` ve [0, 255] aralığında -> `raw`.
   - `float*`, min >= 0 ve max <= 1.01 -> `normalized`.
   - `float*`, min < 0, |mean| < 0.5 ve 0.5 <= std <= 1.5 -> `standardized`.
   - Diğer her şey -> `unusual`, histogramı yazdır.

4. **Kanal başına istatistik** — kanal başına mean ve std raporla. Array standardized görünüyorsa ImageNet mean/std ile karşılaştır ve eşleşme güvenini göster.

5. **Şu blokla raporla**:

```
[inspector]
  backend:   numpy | torch | jax
  rank:      2 | 3 | 4
  layout:    HW | HWC | CHW | NHWC | NCHW
  dtype:     <dtype>
  shape:     <shape>
  range:     raw | normalized | standardized | unusual
  min/max:   <min> / <max>
  per-channel mean: [ ... ]
  per-channel std:  [ ... ]
  likely source:    camera | PIL | OpenCV | torchvision | random init
  likely target:    display | training | inference
```

6. **Sonraki aksiyonu öner** `likely target`'a göre:
   - `display` için: HWC'ye transpose et, clip et, uint8'e çevir.
   - `training` için: dataset istatistikleriyle standardize et, CHW'ye transpose et, batch ekseni ekle.
   - `inference` için: model card'daki tam değişmezleri eşleştir.

## Kurallar

- Girdiyi asla değiştirme. Sadece teşhis yazdır.
- `expected` sağlanmışsa, her uyuşmazlığı `[expected X got Y]` ile işaretle.
- Layout ya da kanal sırası belirsizse sessiz başarısızlık risklerini açıkça belirt.
- Tek seferde tek aksiyon öner, seçenek listesi değil.
