---
name: skill-mask-rcnn-head-swapper
description: Custom num_classes için bir torchvision Mask R-CNN'de box ve mask head'lerini değiştirmek için tam kodu üret
version: 1.0.0
phase: 4
lesson: 8
tags: [computer-vision, mask-rcnn, fine-tuning, torchvision]
---

# Mask R-CNN Head Swapper

Spesifik olarak Mask R-CNN için head-swap boilerplate üretir. Aşağıdaki şablon `model.roi_heads.box_predictor` ve `model.roi_heads.mask_predictor`'a dayanır; bunlar sadece `maskrcnn_resnet50_fpn` ve `maskrcnn_resnet50_fpn_v2`'de bulunur. Faster R-CNN'in box predictor'ı var ama mask predictor'ı yok; RetinaNet `RetinaNetHead` kullanır ve hiç `roi_heads`'i yoktur — ikisi de farklı skill gerektirir.

## Ne zaman kullan

- Custom bir sınıf seti üzerinde `maskrcnn_resnet50_fpn` ya da `maskrcnn_resnet50_fpn_v2`'yi fine-tune ederken.
- COCO'da eğitilmiş bir Mask R-CNN checkpoint'ini COCO olmayan bir sınıf sayısına taşırken.
- `cls_score.out_features` ya da `mask_predictor` uyumsuzluğuyla çöken bir Mask R-CNN eğitim turunu ayıklarken.

## Kapsam dışı

- `fasterrcnn_*` — mask_predictor yok. Sadece `box_predictor`'ı değiştir; ayrı bir Faster R-CNN head-swap tarifi kullan.
- `retinanet_*` — `roi_heads` yok; classifier + regression head'leri `model.head.classification_head` ve `model.head.regression_head` altında yaşar. RetinaNet'e özel skill kullan.
- `keypointrcnn_*` — `mask_predictor` yerine `keypoint_predictor` kullanır.

## Girdiler

- `model_name`: torchvision detection model constructor'ı, örn. `maskrcnn_resnet50_fpn_v2`.
- `num_classes`: background dahil. 4 nesne sınıfı dataset'i `num_classes=5` demek.
- `freeze`: `backbone`, `backbone_fpn`, `none`'dan biri.

## Adımlar

1. Model constructor'ını ve iki predictor class'ını (`FastRCNNPredictor`, `MaskRCNNPredictor`) import et.
2. Default ağırlıklı pretrained modeli yükle.
3. `model.roi_heads.box_predictor`'ı yeni bir `FastRCNNPredictor(in_features, num_classes)` ile değiştir.
4. `model.roi_heads.mask_predictor`'ı yeni bir `MaskRCNNPredictor(in_features_mask, hidden_layer=256, num_classes)` ile değiştir.
5. İstenen freeze politikasını uygula.
6. Modül başına trainable params listeleyen bir teyit bloğu yazdır.

## Çıktı kod şablonu

```python
from torchvision.models.detection import {MODEL_NAME}, {MODEL_WEIGHTS}
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

def build_model(num_classes={NUM_CLASSES}):
    model = {MODEL_NAME}(weights={MODEL_WEIGHTS}.DEFAULT)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask, 256, num_classes)

    {FREEZE_BLOCK}

    return model
```

Burada `{FREEZE_BLOCK}`:

- `none` -> boş
- `backbone` ->
  ```python
  for p in model.backbone.parameters():
      p.requires_grad = False
  ```
- `backbone_fpn` ->
  ```python
  for p in model.backbone.parameters():
      p.requires_grad = False
  # FPN parametreleri backbone.fpn içinde yaşar
  ```

## Rapor

```
[head-swap]
  model:         <MODEL_NAME>
  num_classes:   <N>  (includes background)
  freeze policy: <choice>
  trainable:     <N>
  total:         <N>
```

## Kurallar

- Background dahil olmadan asla `num_classes` önerme; kullanıcıya her zaman hatırlat.
- Mümkünse torchvision detection modellerinin `_v2` varyantlarını kullan; eski olanlardan daha iyi pretrained ağırlıkları var.
- Modeli bu skill içinde instantiate etme — kod bloğunu üret ve kullanıcı çalıştırsın.
- Kullanıcı 10,000+ görsellik bir dataset'te `freeze backbone` isterse, backbone'u da fine-tune etmeyi düşünmesini öner.
