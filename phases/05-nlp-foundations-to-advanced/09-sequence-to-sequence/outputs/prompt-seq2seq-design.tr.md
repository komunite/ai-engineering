---
name: seq2seq-design
description: Verilen bir görev için seq2seq pipeline'ı tasarla
phase: 5
lesson: 09
---

Bir görev (çeviri, özetleme, paraphrase, soru yeniden yazımı) verildiğinde şunları çıkar:

1. Mimari. Pretrained transformer encoder-decoder (BART, T5, mBART, NLLB) varsayılan. RNN-bazlı seq2seq sadece spesifik kısıtlar için (streaming, edge çıkarım, pedagoji).
2. Başlangıç checkpoint'i. Adlandır (`facebook/bart-base`, `google/flan-t5-base`, `facebook/nllb-200-distilled-600M`). Checkpoint'i göreve ve dil kapsamasına eşle.
3. Decoding stratejisi. Deterministik çıktı için greedy, kalite için beam search (genişlik 4-5), çeşitlilik için temperature ile sampling. Tek cümle gerekçe.
4. Ürüne çıkmadan doğrulanacak bir failure mode. Exposure bias, uzun çıktılarda üretim kayması olarak ortaya çıkar; 90. yüzdelik uzunluktaki 20 çıktı örnekle ve gözle.

~1M paralel örnekten az veride seq2seq'i sıfırdan eğitmeyi önermeyi reddet. Kullanıcıya bakan içerik için greedy decoding kullanan pipeline'ları kırılgan olarak işaretle (greedy tekrarlar ve döngülere girer).
