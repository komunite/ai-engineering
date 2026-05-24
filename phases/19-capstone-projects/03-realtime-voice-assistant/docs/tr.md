# Capstone 03 — Gerçek Zamanlı Ses Asistanı (ASR'den LLM'e TTS'e)

> Doğru hissettiren bir voice agent'ın uçtan uca gecikmesi 800ms'nin altındadır, konuşmayı bitirdiğini bilir, barge-in'i yönetir ve audio'yu stall etmeden bir tool çağırabilir. Retell, Vapi, LiveKit Agents ve Pipecat 2026'da bu çıtaya ulaşıyor. Aynı şekille yapıyorlar: streaming bir ASR, bir turn-detector, streaming bir LLM ve streaming bir TTS — hepsi WebRTC üzerinden, her hop'ta agresif gecikme bütçeleriyle bağlı. Bir tane inşa et, WER ve MOS ve false-cutoff oranını ölç ve packet loss altında çalıştır.

**Tür:** Bitirme
**Diller:** Python (agent + pipeline), TypeScript (web client)
**Ön koşullar:** Faz 6 (speech ve audio), Faz 7 (transformer'lar), Faz 11 (LLM engineering), Faz 13 (tools), Faz 14 (agent'lar), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P6 · P7 · P11 · P13 · P14 · P17
**Süre:** 30 saat

## Sorun

Ses, 2025-2026'nın en hızlı hareket eden yapay zeka UX kategorisi oldu. Teknik tavan her çeyrek düştü. OpenAI Realtime API, Gemini 2.5 Live, Cartesia Sonic-2, ElevenLabs Flash v3, LiveKit Agents 1.0 ve Pipecat 0.0.70 — hepsi sub-800ms first-audio-out'u erişim mesafesine getirdi. Çıta sadece gecikme değil. Etkileşim hissi: kullanıcıyı kesmemek, kesilmemek, cümle ortasında kesintiden iyileşmek, audio'yu stall etmeden konuşma ortasında bir tool çağırmak, jitter'lı mobil ağlarda hayatta kalmak.

Bunu üç REST çağrısını birbirine ekleyerek başaramazsın. Mimari uçtan uca pipeline'lı streaming'dir. Onu inşa et ve başarısızlık modları görünür hale gelir: telefon audio'su için tune edilmiş bir VAD'in arka plan TV'sinde tetiklenmesi, asla gelmeyen noktalama için bekleyen bir turn-detector, ilk çıkmadan önce 400ms buffer'layan bir TTS. Capstone, bunları yük altında tek tek düzeltmek ve bir latency-and-quality raporu yayınlamak.

## Kavram

Pipeline'ın beş streaming aşaması var: **audio in** (browser veya PSTN'den WebRTC), **ASR** (Deepgram Nova-3 veya faster-whisper'dan streaming partial transcript'ler), **turn detection** (VAD artı completion ipuçları için partial transcript'leri okuyan küçük bir turn-detector modeli), **LLM** (tur tamamlandı kabul edildiği anda token streaming), **TTS** (ilk LLM token'ından ~200ms içinde audio streaming out).

Üç cross-cutting concern. **Barge-in**: kullanıcı agent konuşurken konuşmaya başladığında, TTS iptal olur ve ASR hemen devralır. **Tool use**: konuşma ortasında function call'lar (weather, calendar) audio'yu stall etmeden side channel'da çalışmalı; gecikme 300ms'yi aşarsa agent bir acknowledgement token ("bir saniye...") pre-fill eder. **Backpressure**: packet loss altında, partial transcript'ler tutulur, VAD speech-gate eşiğini yükseltir ve agent acknowledge edilmemiş bir mesajın üstüne konuşmaktan kaçınır.

Ölçüm çıtası nicel. 15 dB SNR'da Hamming VAD benchmark'ında %8 altı WER. 100 ölçülen aramada p50 first-audio-out 800ms altında. False-cutoff oranı %3 altında. TTS'te MOS 4.2 üstü. Tek g5.xlarge'da 50 eşzamanlı arama. Bu sayılar teslimat.

## Mimari

```
browser / Twilio PSTN
        |
        v
   WebRTC / SIP edge
        |
        v
  LiveKit Agents 1.0  (veya Pipecat 0.0.70)
        |
   +----+--------------+--------------+-----------------+
   |                   |              |                 |
   v                   v              v                 v
  ASR              VAD v5         turn-detector     side-channel
(Deepgram         (Silero)          (LiveKit)        tool'ları
 Nova-3 /         speech-gate    partial'larda      (weather,
 Whisper-v3)      20ms başına     completion score   calendar)
   |                   |              |
   +--------+----------+--------------+
            v
        LLM (streaming)
     GPT-4o-realtime / Gemini 2.5 Flash /
     cascaded Claude Haiku 4.5
            |
            v
        TTS streaming
     Cartesia Sonic-2 / ElevenLabs Flash v3
            |
            v
     arayan'a geri audio
            |
            v
   OpenTelemetry voice traces -> Langfuse
```

## Stack

- Transport: LiveKit Agents 1.0 (WebRTC) artı Twilio PSTN gateway; alternatif framework olarak Pipecat 0.0.70
- ASR: Deepgram Nova-3 (streaming, sub-300ms ilk partial) veya self-hosted faster-whisper Whisper-v3-turbo
- VAD: Silero VAD v5 artı LiveKit turn-detector (partial transcript'leri okuyan küçük transformer)
- LLM: tight integration için OpenAI GPT-4o-realtime, Gemini 2.5 Flash Live veya cascaded Claude Haiku 4.5 (streaming completion'lar, ayrı audio path)
- TTS: Cartesia Sonic-2 (en düşük ilk-byte), ElevenLabs Flash v3 veya self-host için açık kaynak Orpheus
- Tool'lar: weather/calendar/booking için FastMCP side-channel; tool >300ms sürerse agent filler emit eder
- Observability: OpenTelemetry voice span'ları, audio replay'li Langfuse voice trace'leri
- Deployment: self-hosted Whisper + Orpheus için tek g5.xlarge (24GB VRAM); en düşük gecikme için hosted API'ler

## İnşa Et

1. **WebRTC oturumu.** Bir LiveKit room ve mikrofon audio'sunu stream eden bir web client ayağa kaldır. Sunucuda, room'a katılan bir agent worker bağla.

2. **ASR streaming.** 20ms PCM frame'leri Deepgram Nova-3'e (veya GPU'da faster-whisper'a) besle. Partial ve final transcript'lere subscribe ol. Partial başına gecikmeyi logla.

3. **VAD ve turn detector.** Frame stream'inde Silero VAD v5 çalıştır. Speech-end event'inde, LiveKit turn-detector'ı en son partial transcript'e karşı ateşle. Sadece VAD 500ms sessizlik söylediğinde ve turn-detector completion > 0.6 skor verdiğinde "tur tamamlandı" diye commit yap.

4. **LLM stream.** Tur tamamlandığında, çalışan konuşmayı artı final transcript'i ile LLM çağrısını başlat. Token'ları stream out. İlk token'da TTS'e handoff yap.

5. **TTS stream.** Cartesia Sonic-2 audio chunk'ları geri stream'ler. İlk chunk ilk LLM token'ından 200ms içinde sunucudan ayrılmalı. Chunk'ları LiveKit room'a emit et; client WebRTC jitter buffer üzerinden çalar.

6. **Barge-in.** TTS çalarken VAD yeni kullanıcı konuşması tespit ettiğinde, TTS stream'ini hemen iptal et, kalan LLM çıktısını düşür ve ASR'i yeniden silahlandır. Bir `tts_canceled` span yayınla.

7. **Tool side channel.** Weather ve calendar'ı function-calling tool'ları olarak kaydet. Invoke edildiğinde, çağrıyı eşzamanlı ateşle; 300ms içinde çözülmezse LLM'in filler olarak "bir saniye, kontrol edeyim" emit etmesini sağla; tool döndüğünde devam et.

8. **Eval harness.** 100 arama kaydet. WER (holdout transcript'e karşı), false-cutoff oranı (kullanıcı cümle ortasında iken iptal edilen TTS), first-audio-out p50, TTS MOS (insan veya NISQA) ve bir jitter-loss testi (paketlerin %3'ünü düşür) hesapla.

9. **Yük testi.** Sentetik arayan ile tek g5.xlarge'da 50 eşzamanlı arama sür. Sürdürülen first-audio-out p95'i ölç.

## Kullan

```
arayan: "yarın tokyo'da hava nasıl"
[asr  ] partial @280ms: "yarın"
[asr  ] partial @540ms: "yarın tokyo"
[turn ] completion score 0.82 @820ms; commit
[llm  ] ilk token @960ms
[tool ] weather.tokyo tomorrow -> 68/52 parçalı bulutlu @1140ms
[tts  ] ilk audio-out @1040ms: "Tokyo yarın parçalı bulutlu olacak..."
tur gecikmesi: 1040ms user-stop -> audio-out
```

## Yayınla

Teslimat `outputs/skill-voice-agent.md`. Bir domain (müşteri destek, scheduling veya kiosk) verildiğinde, ölçüm çıtasına tune edilmiş ASR/VAD/LLM/TTS pipeline'lı bir LiveKit agent'ı ayağa kaldırır. Rubrik:

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Uçtan uca gecikme | 100 kayıtlı arama boyunca 800ms altında p50 first-audio-out |
| 20 | Turn-taking kalitesi | Hamming VAD benchmark'ında %3 altı false-cutoff oranı |
| 20 | Tool-use doğruluğu | Audio'yu stall etmeden doğru veriyi döndüren konuşma-ortası tool çağrıları |
| 20 | Packet loss altında güvenilirlik | %3 packet drop enjekte edilmiş WER ve turn-taking kararlılığı |
| 15 | Eval harness eksiksizliği | Public config ile yeniden üretilebilir ölçümler |
| **100** | | |

## Alıştırmalar

1. Deepgram Nova-3'ü bir g5.xlarge üzerinde faster-whisper v3 turbo ile değiştir. Gecikme ve WER gap'ini ölç. CPU-vs-GPU kararlarının nerede önemli olduğunu belirle.

2. Bir interruption-arbitration politikası ekle: bir tool call sırasında kullanıcı barge-in yaptığında agent ne yapıyor? Üç politikayı karşılaştır (hard cancel, finish-tool-then-stop, queue next turn).

3. Adversarial bir turn-detector testi çalıştır: kullanıcıya cümle ortasında uzun duraksamalar ver. En düşük false-cutoff için, 900ms'yi geçmeden VAD silence eşiğini ve turn-detector score eşiğini tune et.

4. Aynı agent'ı Twilio üzerinden PSTN'de deploy et. PSTN first-audio-out'unu WebRTC'ye karşılaştır. Jitter-buffer ve codec farklarını açıkla.

5. İngilizce olmayan diller (Japonca, İspanyolca) için voice activity detection ekle. Silero VAD v5 false-trigger oranını dile özgü fine-tune'lara karşı ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Turn detection | "End of utterance" | VAD silence'ı ve bir partial transcript verildiğinde kullanıcının bitirdiğine karar veren sınıflandırıcı |
| Barge-in | "Interruption handling" | VAD yeni kullanıcı konuşması tespit ettiğinde playback ortasında TTS'i iptal etme |
| First-audio-out | "Latency" | Kullanıcı konuşmayı bırakmaktan sunucudan ilk audio paketinin ayrılmasına kadar geçen süre |
| VAD | "Speech gate" | Audio frame'leri speech vs sessizlik olarak sınıflandıran model; Silero VAD v5 2026 default'u |
| Jitter buffer | "Audio smoothing" | Ağ varyansını absorbe etmek için paketleri kısa süre tutan client-side buffer |
| Filler | "Acknowledgment token" | Tool yavaşken sessizlikten kaçınmak için agent'ın emit ettiği kısa ifade |
| MOS | "Mean opinion score" | Algısal speech kalite derecelendirmesi; NISQA otomatize proxy'dir |

## İleri Okuma

- [LiveKit Agents 1.0](https://github.com/livekit/agents) — referans WebRTC agent framework
- [Pipecat](https://github.com/pipecat-ai/pipecat) — alternatif Python-first streaming agent framework
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) — integrated speech model'lar için referans
- [Deepgram Nova-3 dokümantasyonu](https://developers.deepgram.com/docs) — streaming ASR referansı
- [Silero VAD v5](https://github.com/snakers4/silero-vad) — VAD referans modeli
- [Cartesia Sonic-2](https://docs.cartesia.ai) — düşük gecikmeli TTS referansı
- [Retell AI mimarisi](https://docs.retellai.com) — üretim voice agent mimarisi
- [Vapi.ai üretim stack'i](https://docs.vapi.ai) — alternatif üretim referansı
