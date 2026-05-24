---
name: audio-brief
description: Bir ses brief'ini TTS, müzik ve SFX boyunca model + prompt + değerlendirme planına çevir.
version: 1.0.0
phase: 8
lesson: 11
tags: [audio, tts, music, sfx, codec]
---

Bir ses brief'i (görev: TTS / müzik / SFX / voice clone, süre, stil, ses ya da tür, lisans kısıtlamaları, gerçek-zamanlı ya da offline, kalite çıtası) verildiğinde, şunu çıkar:

1. Model + hosting. ElevenLabs V3, OpenAI TTS, XTTS v2, Suno v4, Udio, Stable Audio 2.5, MusicGen 3.3B, AudioCraft 2 ya da GPT-4o realtime. Tek cümlelik gerekçe.
2. Prompt formatı. TTS: metin + ses prompt'u (3-10 s örnek ya da ses ID) + duygu / tempo etiketleri. Müzik: tür + enstrümantasyon + mood + BPM + yapısal işaretler. SFX: onomatopoeia + kaynak + süre ipucu.
3. Codec + generator + vocoder zinciri. Spesifik codec'i adlandır (Encodec 32 kHz, DAC 44 kHz, custom) ve generator seçimi (token-AR vs flow-matching).
4. Seed + tekrar üretilebilirlik. Seed pin, version pin, prompt hash.
5. Değerlendirme. TTS için MOS (mean opinion score) ya da A/B, müzik için CLAP skoru, TTS transkripsiyon için CER, SFX için kullanıcı dinleme testi.
6. Guardrail'lar. Voice-clone onayı + watermark (PerTh / SynthID-audio), müzik çıktısı üzerinde telif taraması, training-data policy kontrolü.

Sahibinden doğrulanmış onay olmadan herhangi bir sesi clone etmeyi reddet (Cassette-dönemi "3 saniyelik prompt" onay değildir). Lisanssız referans materyali ile müzik shipping reddet. Streaming token-AR modeli kullanmayan &lt; 200 ms gerçek-zamanlı hedefi flag'le - diffusion tabanlı ses 2026'da sub-300 ms TTFB'yi karşılayamaz.
