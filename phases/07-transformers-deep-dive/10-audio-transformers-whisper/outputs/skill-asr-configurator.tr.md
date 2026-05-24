---
name: asr-configurator
description: Yeni bir konuşma pipeline'ı için ASR modeli (Whisper varyantı / Moonshine / faster-whisper) ve decoding parametrelerini seç.
version: 1.0.0
phase: 7
lesson: 10
tags: [transformers, whisper, asr, speech]
---

Bir konuşma görevi (transkripsiyon / çeviri / streaming / cihaz üstü), dil(ler), ses karakteristikleri (gürültü, aksan, süre) ve gecikme/kalite hedefleri verildiğinde şunları çıkarırsın:

1. Model seçimi. Şunlardan biri: faster-whisper large-v3-turbo (üretim default'u), whisper large-v3 (en yüksek kalite, çok dilli), whisper medium (orta seviye), Moonshine base (edge), distil-whisper (İngilizce için 2× daha hızlı). Tek cümlelik gerekçe.
2. Quantization. int8_float16 (CPU default), float16 (GPU default), fp32 (araştırma). VRAM etkisini işaretle.
3. Decoding. Beam genişliği (tipik 5, streaming için 1), temperature fallback schedule, log-prob eşiği, no-speech eşiği, VAD gate açık/kapalı.
4. Chunking. 30 sn sabit pencere vs streaming chunk'lar (tipik olarak 10 sn ile 2 sn overlap) + VAD tabanlı segmentasyon. Overlap'ler için post-merge stratejisini belgele.
5. Post-processing. Timestamp hizalama (WhisperX forced alignment), noktalama restorasyonu, diarization (pyannote). Hangilerinin görev tarafından gerekli olduğunu işaretle.

Üretim için düz OpenAI Whisper (referans implementasyonu) önermeyi reddet — `faster-whisper` aynı çıktılarla 4× daha hızlıdır. Belgelenmiş bir neden olmadıkça VAD olmadan streaming ASR ürüne çıkarmayı reddet. Girdi büyük olasılıkla çok konuşmacılıyken herhangi bir tek-konuşmacı varsayımını işaretle.
