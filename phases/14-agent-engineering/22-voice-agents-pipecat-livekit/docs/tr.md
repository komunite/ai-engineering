# Ses Agent'ları: Pipecat ve LiveKit

> Ses agent'ları 2026'da birinci-sınıf bir üretim kategorisi. Pipecat sana Python frame-tabanlı bir pipeline veriyor (VAD → STT → LLM → TTS → transport). LiveKit Agents AI modellerini WebRTC üzerinden kullanıcılara köprülüyor. Üretim latency hedefleri premium stack'ler için uçtan-uca 450–600ms'de iniyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 12 (Workflow Desenleri)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Pipecat'in frame-tabanlı pipeline'ını açıkla: DOWNSTREAM (source→sink) ve UPSTREAM (kontrol).
- Kanonik ses pipeline aşamalarını ve Pipecat'in hangi transport'ları desteklediğini adlandır.
- LiveKit Agents'in iki ses agent class'ını (MultimodalAgent, VoicePipelineAgent) ve her birinin ne zaman uyduğunu açıkla.
- 2026 üretim latency beklentilerini ve mimari seçimleri nasıl yönlendirdiklerini özetle.

## Sorun

Ses agent'ları TTS bolted-on bir text döngüsü değil. Latency bütçeleri acımasız (~600ms), kısmi ses varsayılan, turn detection bir model ve transport'lar telephony SIP'ten WebRTC'ye uzanıyor. Ya frame-tabanlı bir pipeline (Pipecat) kurarsın ya da bir platforma yaslanırsın (LiveKit).

## Kavram

### Pipecat (pipecat-ai/pipecat)

- Python frame-tabanlı pipeline framework'ü.
- `Frame` → `FrameProcessor` chain.
- İki akış yönü:
  - **DOWNSTREAM** — source → sink (ses in, TTS out).
  - **UPSTREAM** — feedback ve kontrol (cancellation, metrics, barge-in).
- `PipelineTask` event'lerle (`on_pipeline_started`, `on_pipeline_finished`, `on_idle_timeout`) ve metrics/tracing/RTVI için observer'larla lifecycle'ı yönetir.

Tipik pipeline:

```
VAD (Silero) → STT → LLM (context user/assistant alternates eder) → TTS → transport
```

Transport'lar: Daily, LiveKit, SmallWebRTCTransport, FastAPI WebSocket, WhatsApp.

Pipecat Flows yapılandırılmış konuşmalar (state machine'ler) ekler. Pipecat Cloud yönetilen runtime.

### LiveKit Agents (livekit/agents)

- AI modellerini WebRTC üzerinden kullanıcılara köprüler.
- Anahtar kavramlar: `Agent`, `AgentSession`, `entrypoint`, `AgentServer`.
- İki ses agent class:
  - **MultimodalAgent** — OpenAI Realtime ya da eşdeğer üzerinden doğrudan ses.
  - **VoicePipelineAgent** — STT → LLM → TTS cascade; text-seviyesi kontrol verir.
- Bir transformer model üzerinden semantik turn detection.
- Native MCP entegrasyonu.
- SIP üzerinden telephony.
- LiveKit Inference üzerinden API key'siz 50+ model; plugin'ler üzerinden 200+ daha.

### Ticari platformlar

Vapi (~450–600ms optimize edilmiş premium stack'te) ve Retell (180 test çağrı genelinde ~600ms uçtan-uca) bunların üstüne inşa eder. WebRTC ekibi olmadan yönetilen bir ses stack'i istediğinde platform seç.

### Bu desen nerede ters gider

- **Barge-in işleme yok.** Kullanıcı kesintiye uğratır; agent konuşmaya devam eder. Pipecat'te UPSTREAM cancel frame'leri, LiveKit'te eşdeğeri gerektirir.
- **STT güveni göz ardı edildi.** Düşük-güven transkriptler LLM'e doğruluk gibi beslenir. Güven üzerinde kapı koy ya da onay iste.
- **TTS cümle-ortasında cutoff.** Pipeline bir utterance ortasında iptal edince, TTS'in bilmesi ya da sesi kesmesi gerek.
- **Latency bütçesi göz ardı edildi.** Her bileşen 50–200ms ekler. Yayınlamadan önce zincirini topla.

### Tipik 2026 latency'leri

- VAD: 20–60ms
- STT partial: 100–250ms
- LLM first token: 150–400ms
- TTS first audio: 100–200ms
- Transport RTT: 30–80ms

Uçtan-uca 450–600ms premium. 800–1200ms yaygın. > 1500ms'lik herhangi bir şey bozuk hissettirir.

## İnşa Et

`code/main.py` şunlara sahip frame-tabanlı oyuncak bir pipeline:

- `Frame` tipleri (audio, transcript, text, tts_audio, control).
- `process(frame)` ile `Processor` arayüzü.
- Scripted processor'lar olarak beş-aşamalı pipeline (VAD → STT → LLM → TTS → transport).
- Barge-in'i göstermek için bir UPSTREAM cancel frame.

Çalıştır:

```
python3 code/main.py
```

Trace normal akışı ve TTS'i utterance ortasında durduran bir barge-in cancel'ı gösterir.

## Kullan

- **Pipecat** tam kontrol için — custom processor'lar, Python-first, plug'lanabilir sağlayıcılar.
- **LiveKit Agents** WebRTC-first deployment'lar ve telephony için.
- **Vapi / Retell** WebRTC ekibi olmadan hosted ses agent'ları için.
- **OpenAI Realtime / Gemini Live** doğrudan ses-in/ses-out için (MultimodalAgent).

## Yayınla

`outputs/skill-voice-pipeline.md` VAD + STT + LLM + TTS + transport artı barge-in işleme ile Pipecat-şekilli bir ses pipeline'ını iskeler.

## Alıştırmalar

1. Oyuncak pipeline'ına bir metrics observer ekle: saniye başına aşama başına frame say. Latency nerede birikiyor?
2. Confidence-gated STT uygula: eşiğin altında, "tekrar eder misin?" iste.
3. Semantik turn detection ekle: basit kural — transkript "?" ile bitiyorsa, turun sonu.
4. Pipecat'in transport dokümanlarını oku. Stdlib transport'unu SmallWebRTCTransport config (stub) ile değiştir.
5. Aynı sorguda bir OpenAI Realtime'ı vs STT+LLM+TTS cascade'i ölç. Text-seviyesi kontrol ne latency maliyeti taşır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Frame | "Event" | Pipeline'da tipli veri birimi (audio, transcript, text, control) |
| Processor | "Pipeline aşaması" | process(frame)'li handler |
| DOWNSTREAM | "İleri akış" | Source'tan sink'e: ses in, konuşma out |
| UPSTREAM | "Feedback akışı" | Kontrol: cancel, metrics, barge-in |
| VAD | "Voice activity detection" | Kullanıcının konuştuğunu tespit eder |
| Semantik turn detection | "Akıllı end-of-turn" | Kullanıcının bittiğine model-tabanlı karar |
| MultimodalAgent | "Doğrudan ses agent" | Ses in, ses out; ortada text yok |
| VoicePipelineAgent | "Cascade agent" | STT + LLM + TTS; text-seviyesi kontrol |

## İleri Okuma

- [Pipecat docs](https://docs.pipecat.ai/getting-started/introduction) — frame-tabanlı pipeline, processor'lar, transport'lar
- [LiveKit Agents docs](https://docs.livekit.io/agents/) — WebRTC + ses primitif'leri
- [Vapi](https://vapi.ai/) — yönetilen ses platformu
- [Retell AI](https://www.retellai.com/) — yönetilen ses, latency-benchmark'lı
