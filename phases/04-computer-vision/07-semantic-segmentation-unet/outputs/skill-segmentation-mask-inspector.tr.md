---
name: skill-segmentation-mask-inspector
description: Sınıf dağılımını, tahmin edilen mask istatistiklerini ve en çok az tahmin edilen ya da sınırı bulanık sınıfları raporla
version: 1.0.0
phase: 4
lesson: 7
tags: [computer-vision, segmentation, debugging, evaluation]
---

# Segmentation Mask Inspector

"Loss düştü" ile "mask'ler gerçekten doğru görünüyor" arasındaki uçurum için teşhis.

## Ne zaman kullan

- Bir eğitim turundan hemen sonra, mIoU iyi görünüyor ama görsel inceleme aksini söylüyorsa.
- Deployment öncesi: tahminlerin sınıf dengesini ground truth'a karşı kontrol etmek için.
- Sınıf başına IoU büyük nesnelerde yüksek ama küçüklerde düşükse.
- Piksel sayısı küçük olduğu için IoU'da görünmeyen sınır artefaktlarını ayıklarken.

## Girdiler

- `preds`: tahmin edilen class ID'lerin (N, H, W) tensor'u.
- `targets`: ground-truth class ID'lerin (N, H, W) tensor'u.
- `num_classes`: tam sayı.
- Opsiyonel `class_names`: C string listesi.

## Adımlar

1. **Sınıf piksel histogramları.** `preds` ve `targets` için sınıf başına piksel yüzdesini hesapla. `|pred% - gt%| / max(gt%, 1e-6) > 0.30` (göreceli sapma %30 üstü) olan herhangi bir sınıfı işaretle. Ground truth'ta olmayan sınıflar için (`gt% == 0`), 0.3 üstündeki herhangi tahmin payını doğrudan işaretle.

2. **Sınıf başına IoU** ve **sınıf başına boundary F1**. Boundary F1, her mask'i 3 piksel dilate edip, kesiştirip puanlayarak hesaplanır. IoU > 0.7 ama boundary F1 < 0.5 olan sınıflar kenarları bulanıklaştırıyor.

3. **Küçük nesne recall'u.** Her ground-truth bağlı bileşeni boyut bucket'larına ayır (tiny < 100 px, small < 1000 px, medium < 10000 px, large >= 10000 px). Sınıf başına bucket başına recall raporla. Küçük nesne recall'u 0.3'ün altında ve büyük nesne recall'u 0.9'un üstündeyse, bu bir çözünürlük / receptive field problemine işaret eder.

4. **Karışıklık çiftleri.** Her sınıf için, en sık karıştığı sınıfı bul (ground-truth mask'i içinde en yaygın yanlış tahmin edilen sınıf). En üst 3 çifti raporla.

5. **Doygunluk kontrolü (sadece `preds` değil `probs` ya da `logits` gerekli).** Çağıran ham piksel başına olasılık dağılımı `probs: (N, C, H, W)` geçirirse, sınıf başına `probs.max(dim=1) > 0.99` olan piksellerin oranını hesapla. Yüksek doygunluk (sınıfın piksellerinin >0.9'u) overconfidence'ı önerir — label smoothing ya da kalibrasyon adayı. Sadece argmax'lanmış `preds` mevcutsa, bu adımı atla ve raporda not düş.

## Rapor formatı

```
[mask-inspector]
  classes: C

[class distribution]
  name       gt %    pred %   delta
  ...

[metrics]
  class       IoU     bF1    recall_tiny  recall_small  recall_medium  recall_large
  ...

[confusion pairs]
  class A confused with class B: <N> pixels (most common)
  class B confused with class A: <N> pixels
  ...

[verdict]
  most impactful issue: <one sentence>
```

## Kurallar

- Sınıf satırlarını azalan gt piksel payına göre sırala ki en sık sınıflar önce gelsin.
- IoU < 0.4 ya da boundary F1 < 0.3 olan sınıfları `critical` olarak işaretle.
- Küçük nesne recall'u baskın başarısızlıksa, şunları öner: daha yüksek çözünürlüklü eğitim, son encoder stage'inde daha küçük stride ya da feature pyramid decoder.
- Boundary F1 baskın başarısızlıksa, şunları öner: sınır farkında loss (Lovasz ya da BoundaryLoss), yatay flip ile TTA ve stride'sız decoder.
- Sınıf indeksini asla tek tanımlayıcı olarak çıkarma; `class_names` sağlanmışsa, her satırda kullan.
