# Voice Activity Detection ve Turn-Taking — Silero, Cobra ve Flush Hilesi

> Her ses ajanı iki karara bağlı yaşar ya da ölür: kullanıcı şu anda konuşuyor mu ve bitti mi? VAD ilkini cevaplar. Turn-detection (VAD + silence-hangover + semantik endpoint modeli) ikincisini. İkisini de yanlış anla, asistanın ya kullanıcıyı keser ya da hiç susmaz.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 11 (Real-Time Ses), Faz 6 · 12 (Ses Asistanı)
**Süre:** ~45 dakika

## Sorun

Ses ajanının her 20 ms chunk'ta verdiği üç farklı karar:

1. **Bu frame konuşma mı?** — VAD. İkili, frame başına.
2. **Kullanıcı yeni bir utterance başlattı mı?** — onset algılama.
3. **Kullanıcı bitirdi mi?** — end-pointing (turn-end).

Naif cevap (energy threshold) herhangi bir gürültüde başarısız olur — trafik, klavye, kalabalık gürültüsü. 2026 cevabı: Silero VAD (açık, deep-learned) + bir turn-detection modeli (semantik endpointing) + VAD-kalibre edilmiş bir silence hangover.

## Kavram

![VAD kaskadı: energy → Silero → turn-detektör → flush hilesi](../assets/vad-turn-taking.svg)

### Üç katmanlı VAD kaskadı

**Tier 1: energy gate.** En ucuz. RMS'yi -40 dBFS'te eşikle. Bariz sessizliği filtreler ama eşiğin üstündeki herhangi bir gürültüde ateşler.

**Tier 2: Silero VAD** (2020-2026, MIT). 1M parametre. 6000+ dil üzerinde eğitilmiş. Tek CPU thread'inde 30 ms chunk başına ~1 ms çalışır. %5 FPR'de %87.7 TPR. Open-source varsayılan.

**Tier 3: semantik turn detektörü.** LiveKit'in turn-detection modeli (2024-2026) ya da kendi küçük sınıflandırıcın. "Cümle ortasında duraklama"yı "konuşma bitti"den ayırır. Sadece sessizlik değil, linguistik bağlam (tonlama + son kelimeler) kullanır.

### Kritik parametreler ve varsayılanları

- **Eşik.** Silero olasılık çıkarır; konuşmayı &gt; 0.5'te (varsayılan) ya da &gt; 0.3'te (hassas) sınıflandır. Daha düşük eşik = daha az first-word clip, daha çok false positive.
- **Minimum konuşma süresi.** 250 ms'den kısa konuşmayı reddet — genellikle öksürük ya da sandalye gürültüsü.
- **Silence hangover (end-pointing).** VAD 0'a döndükten sonra turn'ün sonunu ilan etmeden önce 500-800 ms bekle. Çok kısa → kullanıcıyı kesersin. Çok uzun → hantal hisseder.
- **Pre-roll buffer.** VAD ateşlemeden önce 300-500 ms ses tut. "Hey"in kesilmesini engeller.

### Flush hilesi (Kyutai 2025)

Streaming STT modellerinin look-ahead gecikmesi vardır (Kyutai STT-1B için 500 ms, STT-2.6B için 2.5 sn). Normalde end-of-speech sonrası transkript için o kadar beklerdin. Flush hilesi: VAD end-of-speech ateşlediğinde, **STT'ye flush sinyali gönder**, anında çıktı zorlanır. STT ~4× realtime'da işlediği için 500 ms buffer ~125 ms'de biter.

End-to-end: 125 ms VAD + flush STT = konuşma gecikmesi.

### 2026 VAD karşılaştırması

| VAD | %5 FPR'de TPR | Gecikme | Lisans |
|-----|--------------|---------|---------|
| WebRTC VAD (Google, 2013) | %50.0 | 30 ms | BSD |
| Silero VAD (2020-2026) | %87.7 | ~1 ms | MIT |
| Cobra VAD (Picovoice) | %98.9 | ~1 ms | ticari |
| pyannote segmentation | %95 | ~10 ms | MIT-ish |

Silero doğru varsayılan. Cobra compliance / doğruluk yükseltmesi. Sadece-energy VAD'nin 2026 üretiminde yeri yok.

## İnşa Et

### Adım 1: Energy kapısı

```python
def energy_vad(chunk, threshold_dbfs=-40.0):
    rms = (sum(x * x for x in chunk) / len(chunk)) ** 0.5
    dbfs = 20.0 * math.log10(max(rms, 1e-10))
    return dbfs > threshold_dbfs
```

### Adım 2: Python'da Silero VAD

```python
from silero_vad import load_silero_vad, get_speech_timestamps

vad = load_silero_vad()
audio = torch.tensor(waveform_16k, dtype=torch.float32)
segments = get_speech_timestamps(
    audio, vad, sampling_rate=16000,
    threshold=0.5,
    min_speech_duration_ms=250,
    min_silence_duration_ms=500,
    speech_pad_ms=300,
)
for s in segments:
    print(f"{s['start']/16000:.2f}s - {s['end']/16000:.2f}s")
```

### Adım 3: Turn-end state machine

```python
class TurnDetector:
    def __init__(self, silence_hangover_ms=500, min_speech_ms=250):
        self.state = "idle"
        self.speech_ms = 0
        self.silence_ms = 0
        self.silence_hangover_ms = silence_hangover_ms
        self.min_speech_ms = min_speech_ms

    def update(self, is_speech, chunk_ms=20):
        if is_speech:
            self.speech_ms += chunk_ms
            self.silence_ms = 0
            if self.state == "idle" and self.speech_ms >= self.min_speech_ms:
                self.state = "speaking"
                return "START"
        else:
            self.silence_ms += chunk_ms
            if self.state == "speaking" and self.silence_ms >= self.silence_hangover_ms:
                self.state = "idle"
                self.speech_ms = 0
                return "END"
        return None
```

### Adım 4: Flush hilesi iskeleti

```python
def flush_on_end(stt_client, audio_buffer):
    stt_client.send_audio(audio_buffer)
    stt_client.send_flush()
    return stt_client.recv_transcript(timeout_ms=150)
```

STT (Kyutai, Deepgram, AssemblyAI) bunun çalışması için flush desteklemeli. Whisper streaming desteklemez — blok tabanlıdır ve her zaman chunk bekler.

## Kullan

| Durum | VAD seçimi |
|-----------|-----------|
| Açık, hızlı, genel | Silero VAD |
| Ticari çağrı merkezi | Cobra VAD |
| On-device (telefon) | Silero VAD ONNX |
| Araştırma / diarization | pyannote segmentation |
| Zero-dependency fallback | WebRTC VAD (legacy) |
| Turn-ending kalitesi gerekli | Silero + LiveKit turn-detector katmanlı |

Pratik kural: gerçekten başka seçeneğin yoksa hariç asla sadece-energy VAD yayınlama.

## Tuzaklar

- **Sabit eşik.** Sessizde çalışır, gürültülüde başarısız olur. Ya cihazda kalibre et ya da Silero'ya geç.
- **Çok-kısa silence hangover.** Ajan cümle ortasında keser. 500-800 ms konuşma konuşması için tatlı nokta.
- **Çok-uzun hangover.** Hantal hisseder. Hedef kullanıcılarla A/B test et.
- **Pre-roll buffer yok.** Kullanıcı sesinin ilk 200-300 ms'i kaybolur. Her zaman rolling pre-roll tut.
- **Semantik endpointing'i ihmal etmek.** "Hmm, düşüneyim..." uzun duraklamalar içerir. Kullanıcılar düşünce ortasında kesilmekten nefret eder. LiveKit'in turn-detector'ını ya da benzerini kullan.

## Yayınla

`outputs/skill-vad-tuner.md` olarak kaydet. Bir iş yükü için VAD modeli, eşik, hangover, pre-roll ve turn-detection stratejisi seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Konuşma + sessizlik + konuşma + öksürük dizisi simüle eder ve üç VAD katmanını test eder.
2. **Orta.** `silero-vad`'ı kur, 5-dakikalık bir kaydı işle, hem first-word clip'leri hem false trigger'ları minimize etmek için eşiği tune et. Precision/recall raporla.
3. **Zor.** Mini bir turn-detector kur: Silero VAD + son 10 kelimenin embedding'leri üzerinde 3-katmanlı MLP (sentence-transformers kullan). El-etiketli turn-end veri seti üzerinde eğit. Silero-only'yi %10 F1 yen.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| VAD | Ses detektörü | Frame başına ikili: bu konuşma mı? |
| Turn detection | End-pointing | VAD + silence-hangover + semantik endpoint. |
| Silence hangover | Konuşma-sonrası bekle | Turn end ilan etmeden önce beklenecek süre; 500-800 ms. |
| Pre-roll | Konuşma-öncesi buffer | VAD ateşlemeden önce 300-500 ms ses tut. |
| Flush hilesi | Kyutai hack'i | VAD → flush-STT → 500 ms yerine 125 ms gecikme. |
| Semantik endpoint | "Durmak mı istediler?" | Sadece sessizliğe değil kelimelere bakan ML sınıflandırıcı. |
| TPR @ FPR %5 | ROC noktası | Standart VAD benchmark'ı; Silero için %87.7, WebRTC %50. |

## İleri Okuma

- [Silero VAD](https://github.com/snakers4/silero-vad) — referans açık VAD.
- [Picovoice Cobra VAD](https://picovoice.ai/products/cobra/) — ticari doğruluk lideri.
- [Kyutai — Unmute + flush trick](https://kyutai.org/stt) — alt-200 ms mühendislik hilesi.
- [LiveKit — turn detection](https://docs.livekit.io/agents/logic/turns/) — üretimde semantik endpointing.
- [WebRTC VAD](https://webrtc.googlesource.com/src/) — legacy baseline.
- [pyannote segmentation](https://github.com/pyannote/pyannote-audio) — diarization-seviye segmentasyon.
