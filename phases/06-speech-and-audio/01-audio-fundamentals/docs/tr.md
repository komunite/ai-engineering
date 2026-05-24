# Ses Temelleri — Dalga Formları, Örnekleme, Fourier Dönüşümü

> Dalga formları ham sinyaldir. Spektrogramlar temsildir. Mel öznitelikleri ise ML dostu biçimdir. Modern her ASR ve TTS pipeline'ı bu merdiveni tırmanır ve ilk basamak örnekleme ile Fourier'i anlamaktır.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 1 · 06 (Vektörler ve Matrisler), Faz 1 · 14 (Olasılık Dağılımları)
**Süre:** ~45 dakika

## Sorun

Bir mikrofon basınç-zaman sinyali üretir. Senin sinir ağın tensor tüketir. İkisinin arasında, ihlal edildiğinde sessiz buglar üreten bir konvansiyon yığını vardır: model güzelce eğitilir ama WER ikiye katlanır, ya da TTS tıslamayla yayına çıkar, ya da bir ses klonlama sistemi konuşmacı yerine mikrofonu ezberler.

Konuşma sistemlerindeki her bug üç sorunun birine kadar izlenebilir:

1. Veri hangi örnekleme oranında kaydedildi ve model neyi bekliyor?
2. Sinyal aliased mı?
3. Ham örnekler üzerinde mi yoksa bir frekans temsili üzerinde mi çalışıyorsun?

Bunları doğru anla, Faz 6'nın geri kalanı çözülebilir hâle gelir. Yanlış anla, Whisper-Large-v4 bile çöp üretir.

## Kavram

![Dalga formu, örnekleme, DFT ve frekans bin'lerinin görselleştirmesi](../assets/audio-fundamentals.svg)

**Dalga formu (waveform).** `[-1.0, 1.0]` aralığında float'lardan oluşan tek boyutlu bir dizi. Örnek numarasıyla indekslenir. Saniyeye dönüştürmek için örnekleme oranına böl: `t = n / sr`. 16 kHz'de 10 saniyelik bir klip 160.000 float'luk bir dizidir.

**Örnekleme oranı (sr).** Saniyede kaç örnek alındığı. 2026'da yaygın oranlar:

| Oran | Kullanım |
|------|-----|
| 8 kHz | Telefon, eski VOIP. 4 kHz'deki Nyquist sessiz harfleri öldürür. ASR için kaçın. |
| 16 kHz | ASR standardı. Whisper, Parakeet, SeamlessM4T v2 hepsi 16 kHz tüketir. |
| 22.05 kHz | Eski modeller için TTS vocoder eğitimi. |
| 24 kHz | Modern TTS (Kokoro, F5-TTS, xTTS v2). |
| 44.1 kHz | CD ses, müzik. |
| 48 kHz | Film, profesyonel ses, yüksek-fidelity TTS (VALL-E 2, NaturalSpeech 3). |

**Nyquist-Shannon.** `sr` örnekleme oranı `sr/2`'ye kadar olan frekansları belirsizlik olmadan temsil edebilir. `sr/2` sınırı *Nyquist frekansı*dır. Nyquist'in üstündeki enerji *aliased* olur — daha düşük frekanslara katlanır — ve sinyali bozar. Downsample etmeden önce her zaman low-pass filtre uygula.

**Bit derinliği.** 16-bit PCM (signed int16, ±32.767 aralığı) evrensel değişim formatıdır. Müzik için 24-bit, dahili DSP için 32-bit float. `soundfile` gibi kütüphaneler int16 okur ama `[-1, 1]` aralığında float32 dizileri sunar.

**Fourier Dönüşümü.** Sonlu her sinyal, farklı frekanslardaki sinüzoidlerin toplamıdır. Discrete Fourier Transform (DFT), `N` örnek için `N` kompleks katsayı hesaplar — her frekans bin'i için bir tane. `bin k`, `k · sr / N` Hz frekansına eşlenir. Magnitüd o frekanstaki amplitüd, açı ise fazdır.

**FFT.** Fast Fourier Transform: `N` ikinin kuvveti olduğunda DFT için `O(N log N)` algoritmadır. Her ses kütüphanesi arka planda FFT kullanır. 16 kHz'de 1024-örneklik bir FFT, 0–8 kHz'i 15.6 Hz çözünürlükle kapsayan 512 kullanılabilir frekans bin'i verir.

**Framing + window.** Bütün bir klibi FFT'lemiyoruz. Onu örtüşen *frame*'lere (tipik olarak 25 ms, 10 ms hop ile) bölüyoruz, her frame'i kenar süreksizliklerini öldürmek için bir pencere fonksiyonuyla (Hann, Hamming) çarpıyoruz, sonra her frame'i FFT'liyoruz. Bu Short-Time Fourier Transform (STFT)'dir. Ders 02 buradan devralır.

## İnşa Et

### Adım 1: Bir klip oku ve dalga formunu çiz

`code/main.py` demoyu bağımlılıksız tutmak için sadece stdlib'in `wave` modülünü kullanır. Üretim için `soundfile` ya da `torchaudio.load` kullanacaksın (ikisi de `(waveform, sr)` tuple döndürür):

```python
import soundfile as sf
waveform, sr = sf.read("clip.wav", dtype="float32")  # shape (T,), sr=int
```

### Adım 2: İlk prensiplerden bir sinüs dalgası sentezle

```python
import math

def sine(freq_hz, sr, seconds, amp=0.5):
    n = int(sr * seconds)
    return [amp * math.sin(2 * math.pi * freq_hz * i / sr) for i in range(n)]
```

16 kHz'de 1 saniyelik bir 440 Hz sinüs (concert A) 16.000 float'tur. 16-bit PCM kodlamasıyla `wave.open(..., "wb")` kullanarak yaz.

### Adım 3: DFT'yi elle hesapla

```python
def dft(x):
    N = len(x)
    out = []
    for k in range(N):
        re = sum(x[n] * math.cos(-2 * math.pi * k * n / N) for n in range(N))
        im = sum(x[n] * math.sin(-2 * math.pi * k * n / N) for n in range(N))
        out.append((re, im))
    return out
```

`O(N²)` — doğruluğu teyit etmek için `N=256`'da iyidir, gerçek ses için işe yaramaz. Gerçek kod `numpy.fft.rfft` ya da `torch.fft.rfft` çağırır.

### Adım 4: Baskın frekansı bul

Magnitüd tepe indeksi `k_star`, `k_star * sr / N` frekansına eşlenir. Bunu 440 Hz sinüs üzerinde çalıştırmak `440 * N / sr` bin'inde bir tepe döndürmelidir.

### Adım 5: Aliasing'i göster

10 kHz'de bir 7 kHz sinüs örnekle (Nyquist = 5 kHz). 7 kHz ton Nyquist'in üstündedir ve `10 − 7 = 3 kHz`'e katlanır. FFT tepesi 3 kHz'de görünür. Bu klasik aliasing demosudur ve her DAC/ADC'nin neden brick-wall low-pass filtre ile geldiğinin nedenidir.

## Kullan

2026'da gerçekten yayına alacağın yığın:

| Görev | Kütüphane | Neden |
|------|---------|-----|
| WAV/FLAC/OGG oku/yaz | `soundfile` (libsndfile wrapper) | En hızlı, stabil, float32 döndürür. |
| Resample | `torchaudio.transforms.Resample` ya da `librosa.resample` | Doğru anti-aliasing dahili. |
| STFT / Mel | `torchaudio` ya da `librosa` | GPU dostu; PyTorch ekosistemi. |
| Real-time streaming | `sounddevice` ya da `pyaudio` | Cross-platform PortAudio binding'leri. |
| Bir dosyayı incele | `ffprobe` ya da `soxi` | CLI, hızlı, sr/kanal/codec raporlar. |

Karar kuralı: **başka hiçbir şeyi eşleştirmeden önce örnekleme oranını eşleştir**. Whisper 16 kHz mono float32 bekler. Ona 44.1 kHz stereo geçirirsen, model bug'ı gibi görünen çöp alırsın.

## Yayınla

`outputs/skill-audio-loader.md` olarak kaydet. Skill, ses girdisinin downstream modelin beklentileriyle eşleştiğini kontrol etmene ve eşleşmediğinde doğru şekilde resample etmene yardımcı olur.

## Alıştırmalar

1. **Kolay.** 16 kHz'de 1 saniyelik 220 Hz + 440 Hz + 880 Hz karışımı sentezle. DFT çalıştır. Beklenen bin'lerde üç tepe olduğunu doğrula.
2. **Orta.** Sesinin 48 kHz'de 3 saniyelik bir WAV'ını kaydet. `torchaudio.transforms.Resample` (anti-aliasing ile) kullanarak 16 kHz'e downsample et, sonra naif decimation ile (her üçüncü örnek) 16 kHz'e indir. İkisini de FFT'le. Aliasing nerede ortaya çıkıyor?
3. **Zor.** Sadece `math` ve Adım 3'teki DFT'yi kullanarak STFT'yi sıfırdan kur. Frame size 400, hop 160, Hann pencere. `matplotlib.pyplot.imshow` ile magnitüdleri çiz. Bu Ders 02'nin spektrogramıdır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Örnekleme oranı | Saniyede kaç örnek | ADC'nin sinyali ölçtüğü Hz cinsinden frekans. |
| Nyquist | Temsil edebileceğin maksimum frekans | `sr/2`; üstündeki enerji aşağı alias olur. |
| Bit derinliği | Her örneğin çözünürlüğü | `int16` = 65.536 seviye; `float32` = `[-1, 1]`'de 24-bit hassasiyet. |
| DFT | Diziler için Fourier dönüşümü | `N` örnek → `N` kompleks frekans katsayısı. |
| FFT | Hızlı DFT | `N` = ikinin kuvveti gerektiren `O(N log N)` algoritma. |
| Bin | Frekans kolonu | `k · sr / N` Hz; çözünürlük = `sr / N`. |
| STFT | Spektrogramın altındaki | Zaman üzerinde framed + windowed FFT. |
| Aliasing | Tuhaf frekans hayaletleri | Nyquist'in üstündeki enerjinin alt bin'lere yansıması. |

## İleri Okuma

- [Shannon (1949). Communication in the Presence of Noise](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf) — örnekleme teoreminin arkasındaki makale.
- [Smith — The Scientist and Engineer's Guide to Digital Signal Processing](https://www.dspguide.com/ch8.htm) — ücretsiz, kanonik DSP ders kitabı.
- [librosa docs — audio primer](https://librosa.org/doc/latest/tutorial.html) — kodla pratik adım adım rehber.
- [Heinrich Kuttruff — Room Acoustics (6th ed.)](https://www.routledge.com/Room-Acoustics/Kuttruff/p/book/9781482260434) — gerçek dünyadaki sesin neden temiz bir sinüzoid olmadığına dair referans.
- [Steve Eddins — FFT Interpretation notebook](https://blogs.mathworks.com/steve/2020/03/30/fft-spectrum-and-spectral-densities/) — frekans bin sezgisi 10 dakikada netleşir.
