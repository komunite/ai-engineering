---
name: vit-configurator
description: Yeni bir görüntü görevi için ViT varyantı, patch boyutu ve pretraining kaynağı seç.
version: 1.0.0
phase: 7
lesson: 9
tags: [transformers, vit, vision]
---

Bir görüntü görevi (sınıflandırma / segmentasyon / tespit / retrieval), görüntü çözünürlüğü, veri seti boyutu (etiketli + etiketsiz) ve deployment hedefi verildiğinde şunları çıkarırsın:

1. Backbone. Şunlardan biri: DINOv2 ViT-L/14 (retrieval/sınıflandırma için default), SAM 3 encoder (segmentasyon), SigLIP (görüntü-dil), ConvNeXt (gecikme-kritik). Tek cümlelik gerekçe.
2. Patch boyutu. 224'te standart sınıflandırma için 16, DINOv2 için 14, yüksek çözünürlükte dense prediction için 8. Sequence length `(H/P)^2 + 1` ve attention maliyeti `O(N^2)`'i işaretle.
3. Pretraining kaynağı. Checkpoint adı. Küçük etiketli setler için (<10k): DINOv2 özellikleri dondurulmuş + linear probe. >100k için: son block'ları fine-tune et. Nedenini belirt.
4. Eğitim tarifi. Optimizer (AdamW), lr, augmentation'lar (RandAug, MixUp, Random Erasing), label smoothing (tipik 0.1), EMA.
5. Risk notu. Veri rejimi riski (tam fine-tune için çok az veri), çözünürlük uyumsuzluğu (pretrain 224 → deploy 1024 konum interpolasyonu olmadan), register-token yokluğu (DINOv2 özelliklerine zarar verebilir).

1M'den az görüntüyle sıfırdan bir ViT eğitmeyi önermeyi reddet — CNN baseline'ları kazanır. Sequence length > 4096 veren patch boyutu önermeyi reddet, Flash Attention + hiyerarşik varyantların (Swin) açık tartışması olmadan. Positional embedding'leri interpole etmeden girdi çözünürlüğünü değiştiren herhangi bir deployment'ı işaretle.
