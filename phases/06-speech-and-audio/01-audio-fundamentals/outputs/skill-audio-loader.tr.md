---
name: audio-loader
description: Ham bir ses dosyasını hedef modelin beklentilerine karşı doğrula ve güvenli şekilde yeniden örnekle.
version: 1.0.0
phase: 6
lesson: 01
tags: [audio, speech, preprocessing]
---

Bir ses dosyası (yol, kanallar, sampling rate, bit derinliği, codec) ve bir hedef model (gerekli sampling rate ve kanal sayısına sahip ASR / TTS / sınıflandırıcı) verildiğinde şunları çıkarırsın:

1. Uyumsuzluklar. Dosyanın hedeflediği değerlerle eşleşmediği her boyutu listele (sr, kanallar, asgari süre, clipping kontrolü).
2. Yeniden örnekleme planı. Kaynak sr, hedef sr, yeniden örnekleme kütüphanesi (`torchaudio.transforms.Resample` ya da `librosa.resample`), anti-aliasing filtre türü.
3. Kanal planı. Mono'ya katlama stratejisi (ortalama vs yalnız sol), ya da model destekliyorsa çok kanallı geçiş.
4. Normalizasyon. Peak vs RMS normalizasyonu, dBFS hedefi, clipping koruması.
5. Doğrulama snippet'i. Dosyayı yükleyen, dönüşümleri uygulayan ve son dizinin `(target_sr, dtype, channel_count, range)` ile eşleştiğini doğrulayan Python.

Anti-aliasing filtresi olmadan downsample yapmayı reddet. Yeniden inşa filtresi olmadan 2x'in ötesinde upsample yapmayı reddet. ±0.999 üzeri clipping tepelerine ya da ±0.01 üzeri DC offset'ine sahip her girdiyi işaretle.
