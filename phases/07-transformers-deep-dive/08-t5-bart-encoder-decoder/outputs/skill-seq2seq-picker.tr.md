---
name: seq2seq-picker
description: Yeni bir sequence-to-sequence görev için encoder-decoder vs decoder-only seçimi yap.
version: 1.0.0
phase: 7
lesson: 8
tags: [transformers, t5, bart, seq2seq]
---

Bir seq2seq görev (çeviri / özetleme / speech-to-text / yapılandırılmış ekstraksiyon / yeniden yazım), girdi ve çıktı uzunluk dağılımları ve kalite vs gecikme öncelikleri verildiğinde şunları çıkarırsın:

1. Mimari. Şunlardan biri: encoder-decoder (T5 / BART / Whisper-tarzı), decoder-only instruction-tuned, encoder-only + prompt şablonu. Tek cümlelik gerekçe.
2. Pretraining hedefi. Span corruption (T5), denoising (BART), next-token (decoder-only) veya "pretraining'i atla, mevcut checkpoint'i fine-tune et." Checkpoint'i adlandır.
3. Girdi formatlama. Görev prefix string'i (T5 stili) vs sistem prompt'u (decoder-only) vs ham token'lar (BART). BOS/EOS işleme dahil.
4. Decoding stratejisi. Beam search genişliği ve uzunluk cezası (çeviri/özet), veya nucleus/min-p (sohbet-benzeri görevler). Görev için hangisi olduğunu belirt.
5. Değerlendirme. Göreve uygun metrik: BLEU / ROUGE / WER / F1 / exact match. Test split boyutunu dahil et.

Üretici çıktılar için encoder-only önermeyi reddet. Girdi zaten bir konuşma olduğunda encoder-decoder önermeyi reddet — decoder-only konuşma belleğine doğal olarak uyar. Whisper'ı yenilecek baseline olarak belirtmeden speech-to-text için decoder-only seçimini işaretle.
