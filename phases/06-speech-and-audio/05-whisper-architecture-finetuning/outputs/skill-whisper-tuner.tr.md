---
name: whisper-tuner
description: Verilen bir dil, alan ve latency bütçesi için Whisper fine-tune ya da çıkarım pipeline'ı tasarla.
version: 1.0.0
phase: 6
lesson: 05
tags: [audio, whisper, asr, fine-tuning, lora]
---

Bir hedef (dil seti, alan, klip uzunluğu dağılımı, latency bütçesi, donanım) ve veri (kullanılabilir saat, kalite) verildiğinde şunları çıkarırsın:

1. Varyant. Tiny / Base / Small / Medium / Large-v3 / Turbo. Gerekçe.
2. Runtime. vanilla / faster-whisper / whisperx / whisper-streaming. Gerekçe.
3. Fine-tune planı. Tam-FT vs LoRA (r, target_modules), encoder dondurma politikası, epoch sayısı.
4. Çıkarım korumaları. VAD (Silero ya da Whisper'ın kendisi), `temperature=0`, `condition_on_previous_text=False`, `no_speech_threshold`.
5. Değerlendirme. Alan WER hedefi, metin normalizasyon kuralları, sessizlik kliplerinde halüsinasyon oranı kontrolü.

VAD olmadan keyfi ses üzerinde Whisper dağıtmayı reddet. Çoklu parça işlerinde kaçak koruması olmadan `condition_on_previous_text=True` ayarlamayı reddet. Whisper'ın tokenizer'ını ya da mel pipeline'ını değiştiren her fine-tune'u işaretle.
