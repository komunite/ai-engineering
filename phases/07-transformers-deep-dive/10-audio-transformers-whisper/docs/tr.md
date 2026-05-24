# Audio Transformer'lar — Whisper Mimarisi

> Ses, zamana karşı frekansın görüntüsüdür. Whisper mel spektrogramlar yiyen ve geri konuşan bir ViT'tir.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 7 · 05 (Tam Transformer), Faz 7 · 08 (Encoder-Decoder), Faz 7 · 09 (ViT)
**Süre:** ~45 dakika

## Sorun

Whisper'dan (OpenAI, Radford et al. 2022) önce, state-of-the-art automatic speech recognition (ASR) wav2vec 2.0 ve HuBERT demekti — self-supervised özellik çıkarıcılar artı fine-tune edilmiş bir head. Yüksek kalite, pahalı veri pipeline'ları, domain-kırılgan. Çok dilli konuşma tanıma dil ailesi başına ayrı modeller gerektiriyordu.

Whisper üç bahis koydu:

1. **Her şey üzerinde eğit.** 97 dilde internet'ten kazınmış 680.000 saat zayıf-etiketli ses. Temiz akademik corpus yok. Phoneme etiketi yok.
2. **Çoklu-görev tek model.** Transkripsiyon, çeviri, voice activity detection, dil ID'si ve task token'ları üzerinden timestamping üzerinde birlikte eğitilmiş tek bir decoder.
3. **Standart encoder-decoder transformer.** Encoder log-mel spektrogramları tüketir. Decoder autoregressive metin token'ları üretir. Vocoder yok, CTC yok, HMM yok.

Sonuç: Whisper large-v3 aksanlar, gürültü ve sıfır temiz etiketli veriye sahip diller arasında dayanıklıdır. 2026'da her açık-kaynak ses asistanı ve çoğu ticari olanlar için varsayılan konuşma front-end'idir.

## Kavram

![Whisper pipeline: ses → mel → encoder → decoder → metin](../assets/whisper.svg)

### Adım 1 — resample + window

16 kHz'de ses. 30 saniyeye clip/pad. Log-mel spektrogram hesapla: 80 mel bin, 10 ms stride → ~3.000 frame × 80 özellik. Bu, Whisper'ın gördüğü "input image"dir.

### Adım 2 — convolutional stem

Kernel 3 ve stride 2 olan iki Conv1D katmanı 3.000 frame'i 1.500'e düşürür. Çok parametre eklemeden sequence length'i yarıya indirir.

### Adım 3 — encoder

1.500 timestep üzerinde 24 katmanlı (large için) transformer encoder. Sinusoidal positional encoding, self-attention, GELU FFN. 1.500 × 1.280 hidden state üretir.

### Adım 4 — decoder

24 katmanlı transformer decoder. GPT-2'nin BPE vocabulary'sinin üst kümesi olan bir vocabulary'den birkaç ses-spesifik özel token ile autoregressive olarak token üretir.

### Adım 5 — task token'ları

Decoder prompt'u modele ne yapacağını söyleyen kontrol token'larıyla başlar:

```
<|startoftranscript|>  <|en|>  <|transcribe|>  <|0.00|>
```

veya

```
<|startoftranscript|>  <|fr|>  <|translate|>   <|0.00|>
```

Model bu konvansiyon üzerinde eğitildi. Görevi prefix ile kontrol edersin. Instruction-tuning'in 2026 eşdeğeri, ama konuşmaya uygulanmış.

### Adım 6 — çıktı

Log-prob eşiği olan beam search (genişlik 5). `<|notimestamps|>` token'ı yoksa ses'in her 0.02 saniyesinde timestamp'ler tahmin edilir.

### Whisper boyutları

| Model | Param | Katman | d_model | Head | VRAM (fp16) |
|-------|--------|--------|---------|-------|-------------|
| Tiny | 39M | 4 | 384 | 6 | ~1 GB |
| Base | 74M | 6 | 512 | 8 | ~1 GB |
| Small | 244M | 12 | 768 | 12 | ~2 GB |
| Medium | 769M | 24 | 1024 | 16 | ~5 GB |
| Large | 1550M | 32 | 1280 | 20 | ~10 GB |
| Large-v3 | 1550M | 32 | 1280 | 20 | ~10 GB |
| Large-v3-turbo | 809M | 32 | 1280 | 20 | ~6 GB (4 katmanlı decoder) |

Large-v3-turbo (2024) decoder'ı 32 katmandan 4'e kesti. <1 WER puan regresyonuyla 8× daha hızlı decoding. Bu decode hız kazancı, Whisper-turbo'nun 2026'da gerçek zamanlı sesli agent'lar için neden varsayılan olduğunun nedenidir.

### Whisper'ın yapmadığı

- Diarization yok (kim konuşuyor). Bunun için pyannote ile eşle.
- Doğal olarak gerçek zamanlı streaming yok — 30 saniyelik pencere sabittir. Modern wrapper'lar (`faster-whisper`, `WhisperX`) VAD + overlap üzerinden streaming bağlar.
- Harici chunking olmadan 30 s'nin ötesinde long-form context yok. Pratikte iyi çalışır çünkü insan konuşması transkripsiyon için nadiren uzun-mesafe context'e ihtiyaç duyar.

### 2026 manzarası

| Görev | Model | Notlar |
|------|-------|-------|
| İngilizce ASR | Whisper-turbo, Moonshine | Moonshine edge'de 4× daha hızlı |
| Çok dilli ASR | Whisper-large-v3 | 97 dil |
| Streaming ASR | faster-whisper + VAD | 150 ms latency hedeflerine ulaşılabilir |
| TTS | Piper, XTTS-v2, Kokoro | Encoder-decoder pattern, ama Whisper-biçimli |
| Ses + dil | AudioLM, SeamlessM4T | Tek transformer'da metin token'ları + ses token'ları |

## İnşa Et

`code/main.py`'a bak. Whisper'ı eğitmiyoruz — log-mel spektrogram pipeline'ı + task-token prompt formatter inşa ediyoruz. Production'da gerçekten dokunduğun parçalar bunlar.

### Adım 1: ses sentezle

16 kHz'de örneklenmiş 440 Hz'de 1 saniyelik sinüs dalgası üret. 16.000 sample.

### Adım 2: log-mel spektrogram (basitleştirilmiş)

Tam mel spektrogram FFT gerektirir. `librosa` gerektirmeden pipeline'ı gösteren basitleştirilmiş bir framing + frame başına enerji versiyonu yapıyoruz:

```python
def frame_signal(x, frame_size=400, hop=160):
    frames = []
    for start in range(0, len(x) - frame_size + 1, hop):
        frames.append(x[start:start + frame_size])
    return frames
```

Frame = 25 ms, hop = 10 ms. Whisper'ın window'lamasıyla eşleşir. Frame başına enerji pedagoji için mel bin'lerin yerine geçer.

### Adım 3: 30 s'ye pad

Whisper her zaman 30 saniyelik chunk'ları işler. Spektrogramı 3.000 frame'e pad et (veya clip et).

### Adım 4: prompt token'larını inşa et

```python
def whisper_prompt(lang="en", task="transcribe", timestamps=True):
    tokens = ["<|startoftranscript|>", f"<|{lang}|>", f"<|{task}|>"]
    if not timestamps:
        tokens.append("<|notimestamps|>")
    return tokens
```

Tüm task-control yüzeyi bu. 4 token'lık prefix.

## Kullan

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe("meeting.wav", language="en", task="transcribe")
print(result["text"])
print(result["segments"][0]["start"], result["segments"][0]["end"])
```

Daha hızlı, OpenAI-uyumlu:

```python
from faster_whisper import WhisperModel
model = WhisperModel("large-v3-turbo", compute_type="int8_float16")
segments, info = model.transcribe("meeting.wav", vad_filter=True)
for s in segments:
    print(f"{s.start:.2f} - {s.end:.2f}: {s.text}")
```

**2026'da Whisper ne zaman seçilir:**

- Tek modelle çok dilli ASR.
- Gürültülü, çeşitli sesin dayanıklı transkripsiyonu.
- Araştırma / prototip ASR — en hızlı başlangıç noktası.

**Başka bir şeyin seçileceği zaman:**

- Edge'de ultra-düşük latency streaming — Moonshine eşleşen kalitede Whisper'ı yener.
- <200 ms gerektiren gerçek zamanlı konuşma yapay zekası — özel streaming ASR.
- Konuşmacı diarization'ı — Whisper bunu yapmaz; pyannote bağla.

## Yayınla

`outputs/skill-asr-configurator.md`'ye bak. Skill, yeni bir konuşma uygulaması için bir ASR modeli, decoding parametreleri ve ön işleme pipeline'ı seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. 10 ms hop ile 16 kHz'de 1 saniyelik sinyal için frame sayısının ~100 frame olduğunu doğrula. 30 saniye için: ~3.000 frame.
2. **Orta.** `numpy.fft` kullanarak tam log-mel spektrogramı inşa et. 80 mel bin'in sayısal hata içinde `librosa.feature.melspectrogram(n_mels=80)` ile eşleştiğini doğrula.
3. **Zor.** Streaming çıkarımı implement et: ses'i 2 s overlap ile 10 s pencerelere chunk'la, her chunk'ta Whisper çalıştır, transkriptleri birleştir. 5 dakikalık podcast örneğinde tek-pass'a karşı word-error rate'i ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Mel spektrogram | "Ses görüntüsü" | 2D temsil: bir eksende frekans bin'leri, diğerinde zaman frame'leri; hücre başına log-ölçekli enerji. |
| Log-mel | "Whisper'ın gördüğü" | Log'tan geçirilmiş mel spektrogram; insanın yüksek sesi algılamasını yaklaşıklar. |
| Frame | "Bir zaman dilimi" | 25 ms'lik sample window'u; 10 ms stride'da örtüşen. |
| Task token | "Konuşma için prompt prefix" | Decoder prompt'unda `<|transcribe|>` / `<|translate|>` gibi özel token'lar. |
| Voice activity detection (VAD) | "Konuşmayı bul" | ASR'den önce sessizliği kaldıran gate; maliyeti büyük ölçüde kısar. |
| CTC | "Connectionist Temporal Classification" | Alignment'sız eğitim için klasik ASR loss'u; Whisper bunu KULLANMAZ. |
| Whisper-turbo | "Küçük decoder, tam encoder" | large-v3 encoder + 4 katmanlı decoder; 8× daha hızlı decoding. |
| Faster-whisper | "Production wrapper" | CTranslate2 yeniden implementasyonu; int8 quantization; OpenAI referansından 4× daha hızlı. |

## İleri Okuma

- [Radford et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper makalesi.
- [OpenAI Whisper repo](https://github.com/openai/whisper) — referans kod + model ağırlıkları. Conv1D stem + encoder + decoder'ı yukarıdan aşağıya ~400 satırda görmek için `whisper/model.py`'ı oku.
- [OpenAI Whisper — `whisper/decoding.py`](https://github.com/openai/whisper/blob/main/whisper/decoding.py) — Adım 5–6'da açıklanan beam-search + task-token mantığı burada; 500 satır, tamamen okunabilir.
- [Baevski et al. (2020). wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations](https://arxiv.org/abs/2006.11477) — habercisi; bazı ayarlarda hâlâ SOTA özellikler.
- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) — production wrapper, referanstan 4× daha hızlı.
- [Jia et al. (2024). Moonshine: Speech Recognition for Live Transcription and Voice Commands](https://arxiv.org/abs/2410.15608) — 2024 edge-dostu ASR, Whisper-biçimli ama daha küçük.
- [HuggingFace blog — "Fine-Tune Whisper For Multilingual ASR with 🤗 Transformers"](https://huggingface.co/blog/fine-tune-whisper) — mel spektrogram preprocessor ve token-timestamp işleme dahil kanonik fine-tuning tarifi.
- [HuggingFace `modeling_whisper.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/whisper/modeling_whisper.py) — dersin mimari diyagramını yansıtan tam implementasyon (encoder, decoder, cross-attention, generation).
