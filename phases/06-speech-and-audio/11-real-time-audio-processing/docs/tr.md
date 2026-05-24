# Real-Time Ses İşleme

> Batch pipeline'lar bir dosyayı işler. Real-time pipeline'lar sonraki 20 milisaniyeyi, sonrakilerin gelmesinden önce işler. Her konuşan AI, broadcast stüdyosu ve telefon botu bu latency bütçesine bağlı yaşar ya da ölür.

**Tür:** Yapım
**Diller:** Python, Rust
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar), Faz 6 · 04 (ASR), Faz 6 · 07 (TTS)
**Süre:** ~75 dakika

## Sorun

Canlı hissettiren bir ses asistanı istiyorsun. İnsan konuşma sırasına geçiş gecikmesi ~230 ms (sessizlikten cevaba). 500 ms üstü robotik hissettirir; 1500 ms üstü bozuk. 2026'da tam **duy → anla → cevapla → konuş** döngüsü için bütçe:

| Aşama | Bütçe |
|-------|--------|
| Mic → buffer | 20 ms |
| VAD | 10 ms |
| ASR (streaming) | 150 ms |
| LLM (ilk token) | 100 ms |
| TTS (ilk chunk) | 100 ms |
| Render → hoparlör | 20 ms |
| **Toplam** | **~400 ms** |

Moshi (Kyutai, 2024) full-duplex 200 ms kaydetti. GPT-4o-realtime (2024) ~320 ms kaydediyor. 2022'deki cascaded pipeline'lar 2500 ms ile yayınlanıyordu. 10× iyileşme üç teknikten geldi: (1) her yerde streaming, (2) partial sonuçlarla asenkron pipelining, (3) kesilebilir üretim.

## Kavram

![Ring buffer, VAD kapısı, kesinti ile streaming ses pipeline'ı](../assets/real-time.svg)

**Frame / chunk / pencere.** Real-time ses sabit-boyutlu bloklar olarak akar. Yaygın seçim: 20 ms (16 kHz'de 320 örnek). Tüm downstream bu kadansa ayak uydurmak zorundadır.

**Ring buffer.** Sabit-boyutlu dairesel buffer. Producer thread yeni frame'leri yazar, consumer thread okur. Hot path'te allocation engeller. Boyut ≈ maksimum-latency × örnekleme-oranı; 2-saniyelik 16 kHz ring = 32.000 örnek.

**VAD (Voice Activity Detection).** Kimse konuşmadığında downstream işi kapatır. Silero VAD 4.0 (2024) CPU'da 30 ms frame başına <1 ms çalışır. `webrtcvad` eski alternatif.

**Streaming ASR.** Ses geldikçe partial transkript yayan modeller. NeMo'daki streaming modda Parakeet-CTC-0.6B (2024) 320 ms gecikmede %2–5 WER yapar. Whisper-Streaming (Macháček et al., 2023), Whisper'ı ~2 sn gecikmeyle near-streaming için chunk'lar.

**Kesinti.** Asistan konuşurken kullanıcı konuştuğunda (a) barge-in'i algılaman, (b) TTS'i durdurman, (c) kalan LLM çıktısını atman gerek. Hepsi 100 ms içinde, yoksa kullanıcı sağır asistan algılar.

**WebRTC Opus transport.** 20 ms frame, 48 kHz, 8–128 kbps adaptif bitrate. Tarayıcı ve mobil için standart. LiveKit, Daily.co, Pion 2026'da ses uygulamaları kurmak için yığınlar.

**Jitter buffer.** Network paketleri sırasız / geç gelir. Jitter buffer yeniden sıralar ve yumuşatır; çok küçük → duyulabilir boşluklar, çok büyük → gecikme. Tipik 60–80 ms.

### Yaygın tuzaklar

- **Thread contention.** Python'un GIL'i + ağır modeller ses thread'ini aç bırakabilir. C-callback ses kütüphanesi (sounddevice, PortAudio) kullan ve Python'u hot path'in dışında tut.
- **Sample-rate dönüşüm gecikmesi.** Pipeline içinde resampling 5–20 ms ekler. Ya önceden resample et ya da zero-latency resampler kullan (PolyPhase, `soxr_hq`).
- **TTS priming.** Kokoro gibi hızlı TTS'in bile ilk istekte 100–200 ms warm-up'ı var. Modeli cache'le + ilk gerçek tur'dan önce dummy run ile ısıt.
- **Echo cancellation.** AEC olmadan TTS çıktısı mike yeniden girer ve bot'un kendi sesine ASR'ı tetikler. WebRTC AEC3 open-source varsayılan.

## İnşa Et

### Adım 1: Ring buffer

```python
import collections

class RingBuffer:
    def __init__(self, capacity):
        self.buf = collections.deque(maxlen=capacity)
    def write(self, frame):
        self.buf.extend(frame)
    def read(self, n):
        return [self.buf.popleft() for _ in range(min(n, len(self.buf)))]
    def level(self):
        return len(self.buf)
```

Kapasite maks buffering gecikmesini belirler. 16 kHz'de 32.000 örnek = 2 sn.

### Adım 2: VAD kapısı

```python
def simple_energy_vad(frame, threshold=0.01):
    return sum(x * x for x in frame) / len(frame) > threshold ** 2
```

Üretimde Silero VAD ile değiştir:

```python
import torch
vad, _ = torch.hub.load("snakers4/silero-vad", "silero_vad")
is_speech = vad(torch.tensor(frame), 16000).item() > 0.5
```

### Adım 3: Streaming ASR

```python
# NeMo üzerinden Parakeet-CTC-0.6B streaming
from nemo.collections.asr.models import EncDecCTCModelBPE
asr = EncDecCTCModelBPE.from_pretrained("nvidia/parakeet-ctc-0.6b")
# chunk_ms=320 ms, look_ahead_ms=80 ms
for chunk in audio_stream():
    partial_text = asr.transcribe_streaming(chunk)
    print(partial_text, end="\r")
```

### Adım 4: Kesinti handler'ı

```python
class Dialog:
    def __init__(self):
        self.tts_task = None

    def on_user_speech(self, frame):
        if self.tts_task and not self.tts_task.done():
            self.tts_task.cancel()   # barge-in
        # sonra streaming ASR'a besle

    def on_final_user_utterance(self, text):
        self.tts_task = asyncio.create_task(self.reply(text))

    async def reply(self, text):
        async for tts_chunk in llm_then_tts(text):
            speaker.write(tts_chunk)
```

Async I/O ve cancellable TTS streaming'e bağlı. Ses track'inde WebRTC peerconnection.stop() kanonik yoldur.

## Kullan

2026 yığını:

| Katman | Seç |
|-------|------|
| Transport | LiveKit (WebRTC) ya da Pion (Go) |
| VAD | Silero VAD 4.0 |
| Streaming ASR | Parakeet-CTC-0.6B ya da Whisper-Streaming |
| LLM ilk-token | Groq, Cerebras, vLLM-streaming |
| Streaming TTS | Kokoro ya da ElevenLabs Turbo v2.5 |
| Echo cancel | WebRTC AEC3 |
| End-to-end nativ | OpenAI Realtime API ya da Moshi |

## Tuzaklar

- **Güvende olmak için 500 ms buffer'lamak.** Buffer'ın *ta kendisi* latency tabanın. Küçült.
- **Thread'leri pin etmemek.** UI'dan-düşük-öncelikli thread'de ses callback'i = yük altında glitch.
- **Çok küçük TTS chunk'ları.** 200 ms altı chunk'lar vocoder artefaktlarını duyulabilir yapar. 320 ms chunk'lar tatlı nokta.
- **Jitter buffer yok.** Gerçek network'ler jitter'lıdır; yumuşatma olmadan pop alırsın.
- **Tek-sefer hata işleme.** Ses pipeline'ları crash-proof olmak zorunda. Bir exception session'ı öldürür.

## Yayınla

`outputs/skill-realtime-designer.md` olarak kaydet. Aşama başına somut latency bütçeleriyle real-time ses pipeline'ı tasarla.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Ring buffer + energy VAD simüle eder; sahte 10-saniyelik akış için aşama gecikmelerini yazdırır.
2. **Orta.** `sounddevice` kullanarak mikrofonunu 20 ms frame'lerde işleyen ve her frame'de VAD durumunu yazdıran bir passthrough döngüsü kur.
3. **Zor.** `aiortc` ile tam duplex echo testi kur: tarayıcı → WebRTC → Python → WebRTC → tarayıcı. 1 kHz pulse ile glass-to-glass gecikmeyi ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Ring buffer | Dairesel queue | Ses frame'leri için sabit-boyutlu, lock-free (ya da SPSC-kilitli) FIFO. |
| VAD | Sessizlik kapısı | Konuşma vs konuşma değil işaretleyen model ya da heuristic. |
| Streaming ASR | Real-time STT | Ses geldikçe partial metin yayar; sınırlı lookahead. |
| Jitter buffer | Network yumuşatıcısı | Sırasız paketleri yeniden sıralayan queue; tipik 60–80 ms. |
| AEC | Echo cancellation | Hoparlör-to-mic feedback yolunu çıkarır. |
| Barge-in | Kullanıcı kesintisi | TTS ortasında sistem kullanıcı konuşmasını algılar; playback iptal etmek zorunda. |
| Full duplex | Eş zamanlı iki yönlü | Kullanıcı ve bot aynı anda konuşabilir; Moshi full duplex. |

## İleri Okuma

- [Macháček et al. (2023). Whisper-Streaming](https://arxiv.org/abs/2307.14743) — chunked near-streaming Whisper.
- [Kyutai (2024). Moshi](https://kyutai.org/Moshi.pdf) — full-duplex 200 ms gecikme.
- [LiveKit Agents framework (2024)](https://docs.livekit.io/agents/) — üretim ses agent orkestrasyonu.
- [Silero VAD repo](https://github.com/snakers4/silero-vad) — alt-1 ms VAD, Apache 2.0.
- [WebRTC AEC3 paper](https://webrtc.googlesource.com/src/+/main/modules/audio_processing/aec3/) — open source altında echo cancellation.
