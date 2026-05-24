---
name: voice-agent
description: 800ms altı first-audio-out, barge-in işleme ve konuşma ortasında tool kullanımıyla gerçek zamanlı bir voice agent kur.
version: 1.0.0
phase: 19
lesson: 03
tags: [capstone, voice, webrtc, livekit, pipecat, asr, tts, streaming]
---

Bir domain (müşteri desteği, randevu, perakende asistanı) verildiğinde, barge-in, tool çağrıları ve paket kaybını işlerken uçtan uca first-audio-out'u 800ms altında tutan bir WebRTC voice agent deploy et.

Build planı:

1. Mikrofon ses akışı yapan web client'lı bir LiveKit Agents 1.0 odası ayağa kaldır. Telefon kapsaması için Twilio PSTN gateway ekle.
2. Streaming ASR çalıştır (Deepgram Nova-3 hosted ya da g5.xlarge üzerinde faster-whisper Whisper-v3-turbo). Partial ve final transkriptlere abone ol.
3. 20ms frame'lerde Silero VAD v5 çalıştır. Konuşma bitince LiveKit turn-detector ile en son partial'ı skorla; yalnızca VAD silence >= 500ms VE completion score >= 0.6 olduğunda turn-complete'e commit ol.
4. LLM'i (GPT-4o-realtime, Gemini 2.5 Flash Live veya cascaded Claude Haiku 4.5) stream et. İlk token'ı TTS'e 200ms içinde teslim et.
5. TTS'i (Cartesia Sonic-2 veya ElevenLabs Flash v3) stream et. İlk audio chunk, ilk LLM token'ından sonra 200ms içinde sunucudan çıkmalı.
6. Barge-in: VAD SPEAKING veya THINKING sırasında yeni kullanıcı konuşması tespit ederse, TTS'i iptal et, kalan LLM çıktısını düşür, ASR'ı yeniden hazırla. `tts_canceled` span yayınla.
7. Tool side-channel: function call'ları eşzamanlı çalıştır; latency > 300ms olursa audio stream durmasın diye bir onay filler'ı yay.
8. 100 çağrı kaydet. Held-out transkriptlere karşı WER, Hamming VAD benchmark üzerinde false-cutoff oranı, first-audio-out p50, NISQA MOS ve %3 paket kaybı altındaki davranışı ölç.
9. Tek bir g5.xlarge üzerinde sentetik çağrı yapanla 50 eşzamanlı çağrıyı load-test et; sürdürülen first-audio-out p95 değerini raporla.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Uçtan uca latency | 100 kayıtlı çağrıda 800ms altı p50 first-audio-out |
| 20 | Turn-taking kalitesi | Hamming VAD benchmark üzerinde %3 altı false-cutoff oranı |
| 20 | Tool kullanımı doğruluğu | Konuşma ortasındaki tool çağrıları audio'yu durdurmadan doğru veri döner |
| 20 | Paket kaybı altında güvenilirlik | %3 paket kaybı enjekte edilmiş WER ve turn-taking kararlılığı |
| 15 | Eval harness tamlığı | Kamuya açık config ile tekrarlanabilir ölçümler |

Sert ret durumları:

- Streaming olmayan pipeline'lar (batch ASR, batch TTS) latency hedefini tutturamaz.
- TTS buffer'ı anında iptal etmeyen herhangi bir barge-in politikası. Gecikmeli iptal en kötü kullanıcı deneyimi gerilemelerini üretir.
- LLM stream'ini senkronize bloke eden tool çağrıları. Side channel'da çalışmalı.

Reddetme kuralları:

- VAD ya da turn-detector olmadan deploy etmeyi reddet. Sabit-timeout'lu turn-taking kabul edilemez cutoff oranı üretir.
- MOS'un human-rated mı yoksa NISQA-proxied mi olduğunu belgelemeden raporlamayı reddet.
- En az 100 kayıtlı çağrı olmadan ve call trace'leri yayınlamadan "p50 latency under X" raporlamayı reddet.

Çıktı: LiveKit agent worker'ı, PSTN gateway config'ini, 100 çağrılık eval harness'ini, kamuya açık bir Langfuse voice dashboard'ı, hosted bir rakiple (Retell, Vapi veya doğrudan OpenAI Realtime API) yan yana karşılaştırmayı ve gözlemlediğin en büyük üç turn-taking arızası ile her birini düzelten detector tuning'ini içeren bir yazımı içeren bir repo.
