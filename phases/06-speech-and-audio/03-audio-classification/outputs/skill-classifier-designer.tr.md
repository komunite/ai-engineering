---
name: classifier-designer
description: Bir ses sınıflandırma görevi için mimari, augmentation, sınıf-dengesi stratejisi ve değerlendirme metriği seç.
version: 1.0.0
phase: 6
lesson: 03
tags: [audio, classification, beats, ast]
---

Bir ses sınıflandırma görevi (alan, etiket sayısı, klip başına etiket yoğunluğu, veri hacmi, dağıtım hedefi) verildiğinde şunları çıkarırsın:

1. Mimari. k-NN-MFCC / 2D CNN / AST / BEATs / Whisper-encoder. Tek cümlelik gerekçe.
2. Augmentation'lar. SpecAugment parametreleri (time mask, freq mask sayıları), mixup α, arka plan gürültüsü karışım düzeyi.
3. Sınıf dengesi. Dengeli örnekleyici vs focal loss vs sınıf ağırlıkları. Kuyruktan başa oranına sabitle.
4. Loss + metrik. CE / BCE / focal; birincil metrik (top-1 / mAP / macro-F1) ve ikincil.
5. Split + değerlendirme planı. Stratified k-fold, konuşma ise konuşmacı-ayrık, streaming veride zamansal split.

Yalnızca top-1 doğrulukla skorlanmış çok-etiketli görevleri reddet; mAP iste. Konuşmacı koşullu bir görevi konuşmacı-ayrık split'ler olmadan değerlendirmeyi reddet. 10k'dan az etiketli klip üzerinde sıfırdan kurulan her mimariyi işaretle — SSL ön eğitimli bir backbone ile başla.
