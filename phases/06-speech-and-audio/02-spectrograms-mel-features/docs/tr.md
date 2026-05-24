# Spektrogramlar, Mel Ölçeği ve Ses Öznitelikleri

> Sinir ağları ham dalga formlarını iyi tüketmez. Spektrogram tüketirler. Mel spektrogramı daha da iyi tüketirler. 2026'da her ASR, TTS ve ses sınıflandırıcı bu tek önişlem seçimine bağlı yaşar ya da ölür.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 01 (Ses Temelleri)
**Süre:** ~45 dakika

## Sorun

16 kHz'de 10 saniyelik bir klip al. Bu 160.000 float demek, hepsi `[-1, 1]` aralığında, "köpek havlaması" ya da "kedi kelimesi" etiketiyle neredeyse hiç korele değil. Ham dalga formu bilgiyi içerir ama modelin kolayca çıkaramayacağı bir biçimde. 100 ms arayla söylenmiş iki özdeş fonem tamamen farklı ham örneklere sahiptir.

Bir spektrogram bunu çözer. İnsan algısının önemsediği yapıyı (~10–25 ms zaman pencerelerinde hangi frekansların enerjik olduğu) korurken, algının görmezden geldiği zamansal detayı (mikro-saniye jitter) sıkıştırır.

Mel spektrogramlar daha da ileri gider. İnsanlar pitch'i logaritmik algılar: 100 Hz vs 200 Hz, 1000 Hz vs 2000 Hz ile "aynı uzaklıkta" duyulur. Mel ölçeği frekans eksenini buna uyacak şekilde büker. Mel-ölçekli spektrogram, 2010'dan 2026'ya kadar konuşma ML'inde en önemli tek özniteliktir.

## Kavram

![Dalga formundan STFT'ye, mel spektrograma, MFCC merdivenine](../assets/mel-features.svg)

**STFT (Short-Time Fourier Transform).** Dalga formunu örtüşen frame'lere böl (tipik: 25 ms pencere, 10 ms hop = 16 kHz'de 400 örnek / 160 örnek). Her frame'i bir pencere fonksiyonuyla çarp (varsayılan Hann; Hamming biraz farklı bir trade-off). Her frame'i FFT'le. Magnitüd spektrumlarını `(n_frames, n_freq_bins)` şeklinde bir matriste yığ. İşte spektrogramın.

**Log-magnitude.** Ham magnitüdler 5-6 büyüklük mertebesine yayılır. Dinamik aralığı sıkıştırmak için `log(|X| + 1e-6)` ya da `20 * log10(|X|)` al. Her üretim pipeline'ı ham magnitüd değil, log-magnitude kullanır.

**Mel ölçeği.** Hz cinsinden frekans `f`, mel `m`'e `m = 2595 * log10(1 + f / 700)` ile eşlenir. Eşleme 1 kHz altında kabaca lineer, üstünde kabaca logaritmiktir. 0–8 kHz'i kapsayan 80 mel bin standart ASR girdisidir.

**Mel filterbank.** Mel ölçeği üzerinde eşit aralıklı üçgen filtrelerden oluşan bir küme. Her filtre komşu FFT bin'lerinin ağırlıklı toplamıdır. STFT magnitüdünü filterbank matrisiyle çarpmak, mel-spektrogramı tek matmul'da verir.

**Log-mel-spektrogram.** `log(mel_spec + 1e-10)`. Whisper'ın girdisi. Parakeet'in girdisi. SeamlessM4T'nin girdisi. 2026'nın evrensel ses frontend'i.

**MFCC'ler.** Log-mel-spektrogramı al, bir DCT (tip II) uygula, ilk 13 katsayıyı tut. Öznitelikleri korelasyonsuzlaştırır ve daha da sıkıştırır. CNN'ler/Transformer'lar ham log-mel üzerinde 2015 civarında yetişene kadar baskın öznitelikti. Hâlâ konuşmacı tanımada kullanılır (x-vector'lar, ECAPA).

**Çözünürlük takası.** Daha büyük FFT = daha iyi frekans çözünürlüğü ama daha kötü zaman çözünürlüğü. 25 ms / 10 ms audio-ML varsayılanıdır; müzik için 50 ms / 12.5 ms; geçici (transient) algılama için (davul vuruşları, patlamalı sesler) 5 ms / 2 ms.

## İnşa Et

### Adım 1: Dalga formunu frame'le

```python
def frame(signal, frame_len, hop):
    n = 1 + (len(signal) - frame_len) // hop
    return [signal[i * hop : i * hop + frame_len] for i in range(n)]
```

16 kHz'de 10 saniyelik bir klip `frame_len=400, hop=160` ile 998 frame üretir.

### Adım 2: Hann pencere

```python
import math

def hann(N):
    return [0.5 * (1 - math.cos(2 * math.pi * n / (N - 1))) for n in range(N)]
```

FFT'den önce eleman bazında çarp. Sıfır olmayan uç noktalarda kesmeden kaynaklanan spektral sızıntıyı kaldırır.

### Adım 3: STFT magnitüdü

```python
def stft_magnitude(signal, frame_len=400, hop=160):
    win = hann(frame_len)
    frames = frame(signal, frame_len, hop)
    return [magnitudes(dft([w * s for w, s in zip(win, f)])) for f in frames]
```

Üretim `torch.stft` ya da `librosa.stft` kullanır (FFT destekli, vektörize). Buradaki döngü pedagojiktir; `code/main.py`'de kısa klipler üzerinde çalışır.

### Adım 4: Mel filterbank

```python
def hz_to_mel(f):
    return 2595.0 * math.log10(1.0 + f / 700.0)

def mel_to_hz(m):
    return 700.0 * (10 ** (m / 2595.0) - 1)

def mel_filterbank(n_mels, n_fft, sr, fmin=0, fmax=None):
    fmax = fmax or sr / 2
    mels = [hz_to_mel(fmin) + (hz_to_mel(fmax) - hz_to_mel(fmin)) * i / (n_mels + 1)
            for i in range(n_mels + 2)]
    hzs = [mel_to_hz(m) for m in mels]
    bins = [int(h * n_fft / sr) for h in hzs]
    fb = [[0.0] * (n_fft // 2 + 1) for _ in range(n_mels)]
    for m in range(n_mels):
        for k in range(bins[m], bins[m + 1]):
            fb[m][k] = (k - bins[m]) / max(1, bins[m + 1] - bins[m])
        for k in range(bins[m + 1], bins[m + 2]):
            fb[m][k] = (bins[m + 2] - k) / max(1, bins[m + 2] - bins[m + 1])
    return fb
```

`n_fft=400` ile 0–8 kHz'i kapsayan 80 mel `(80, 201)` bir matris verir. `(n_frames, 201)` STFT magnitüdünü transpoza ile çarp, `(n_frames, 80)` mel-spektrogram elde et.

### Adım 5: Log-mel

```python
def log_mel(mel_spec, eps=1e-10):
    return [[math.log(max(v, eps)) for v in frame] for frame in mel_spec]
```

Yaygın alternatifler: `librosa.power_to_db` (referansa normalize edilmiş dB), `10 * log10(power + eps)`. Whisper daha karmaşık bir clip + normalize rutini kullanır (Whisper'ın `log_mel_spectrogram`'ına bak).

### Adım 6: MFCC'ler

```python
def dct_ii(x, n_coeffs):
    N = len(x)
    return [
        sum(x[n] * math.cos(math.pi * k * (2 * n + 1) / (2 * N)) for n in range(N))
        for k in range(n_coeffs)
    ]
```

Her log-mel frame'ine DCT uygula, ilk 13 katsayıyı tut. İşte MFCC matrisin. Birinci katsayı genellikle düşürülür (toplam enerjiyi kodlar).

## Kullan

2026 yığını:

| Görev | Öznitelikler |
|------|----------|
| ASR (Whisper, Parakeet, SeamlessM4T) | 80 log-mel, 10 ms hop, 25 ms pencere |
| TTS akustik model (VITS, F5-TTS, Kokoro) | 80 mel, ince zamansal kontrol için 5–12 ms hop |
| Ses sınıflandırma (AST, PANNs, BEATs) | 128 log-mel, 10 ms hop |
| Konuşmacı embedding (ECAPA-TDNN, WavLM) | 80 log-mel ya da ham-dalga formu SSL |
| Müzik (MusicGen, Stable Audio 2) | EnCodec discrete token'lar (mel değil) |
| Keyword spotting | Tiny cihazlar için 40 MFCC |

Pratik kural: **müzikle çalışmıyorsan, 80 log-mel ile başla.** Sapmayı ispat yükü senin omuzlarında.

## 2026'da Hâlâ Yayına Çıkan Tuzaklar

- **Mel sayısı uyuşmazlığı.** 80 mel ile eğitim, 128 mel ile çıkarım. Sessiz hata. Her iki uçta öznitelik şeklini logla.
- **Yukarı akış örnekleme oranı uyuşmazlığı.** 22.05 kHz'de hesaplanan mel'ler 16 kHz'den farklı görünür. Öznitelikleştirme *öncesi* SR'yi düzelt.
- **dB vs log.** Whisper dB-mel değil log-mel bekler. Bazı HF pipeline'ları otomatik algılar; senin custom kodun algılamaz.
- **Normalization drift.** Eğitim sırasında per-utterance normalizasyon, çıkarımda global normalizasyon. WER'i ikiye katlayan üretim bug'ı.
- **Padding'den sızıntı.** Bir klibin sonunu sıfır-padding'le doldurmak takip eden frame'lerde düz spektrum üretir. Simetrik pad et ya da replicate.

## Yayınla

`outputs/skill-feature-extractor.md` olarak kaydet. Skill verilen bir model hedefi için öznitelik tipi, mel sayısı, frame/hop ve normalizasyon seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Bir chirp (200 → 4000 Hz arasında frekans taraması) sentezler ve frame başına argmax mel bin'ini yazdırır. Çiz (opsiyonel) ve taramayla eşleştiğini doğrula.
2. **Orta.** `n_mels` `{40, 80, 128}` ve `frame_len` `{200, 400, 800}` değerleriyle yeniden çalıştır. Zaman ekseninde keskin-tepe bant genişliğini ölç. Hangi kombinasyon chirp'i en iyi çözüyor?
3. **Zor.** `power_to_db`'yi uygula ve AudioMNIST üzerinde tiny bir CNN sınıflandırıcının ASR doğruluğunu (a) ham log-mel, (b) `ref=max` ile dB-mel, (c) MFCC-13 + delta + delta-delta kullanarak karşılaştır. Top-1 doğruluğunu raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Frame | Bir dilim | Bir FFT'ye beslenen 25 ms'lik dalga formu parçası. |
| Hop | Stride | Ardışık frame'ler arası örnek; 10 ms ASR varsayılanı. |
| Pencere | Hann/Hamming şeyi | Frame kenarlarını sıfıra koniklendiren noktasal çarpan. |
| STFT | Spektrogram üreteci | Framed + windowed FFT; zaman × frekans matrisi verir. |
| Mel | Bükülmüş frekans | Log-algı ölçeği; `m = 2595·log10(1 + f/700)`. |
| Filterbank | Matris | STFT'yi mel bin'lerine projekte eden üçgen filtreler. |
| Log-mel | Whisper'ın girdisi | `log(mel_spec + eps)`; 2026'da standartlaşmış. |
| MFCC | Eski-okul öznitelik | Log-mel'in DCT'si; 13 katsayı, korelasyonsuz. |

## İleri Okuma

- [Davis, Mermelstein (1980). Comparison of parametric representations for monosyllabic word recognition](https://ieeexplore.ieee.org/document/1163420) — MFCC makalesi.
- [Stevens, Volkmann, Newman (1937). A Scale for the Measurement of the Psychological Magnitude Pitch](https://pubs.aip.org/asa/jasa/article-abstract/8/3/185/735757/) — orijinal mel ölçeği.
- [OpenAI — Whisper source, log_mel_spectrogram](https://github.com/openai/whisper/blob/main/whisper/audio.py) — referans uygulamayı oku.
- [librosa feature extraction docs](https://librosa.org/doc/main/feature.html) — `mfcc`, `melspectrogram` ve hop/pencere için referans.
- [NVIDIA NeMo — audio preprocessing](https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/main/asr/asr_all.html#featurizers) — Parakeet + Canary modelleri için üretim ölçeğinde pipeline.
