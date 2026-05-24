# Text-to-Speech (TTS) — Tacotron'dan F5 ve Kokoro'ya

> ASR konuşmayı metne ters çevirir; TTS metni konuşmaya ters çevirir. 2026 yığını üç parçalı: metin → token'lar, token'lar → mel, mel → dalga formu. Her parçanın bir laptop'a sığan varsayılan bir modeli var.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar ve Mel), Faz 5 · 09 (Seq2Seq), Faz 7 · 05 (Full Transformer)
**Süre:** ~75 dakika

## Sorun

Bir string'in var: "Lütfen saat 6'da bitkileri sulamamı hatırlat." 3-saniyelik, doğal sesli, doğru prozodiye sahip (duraklamalar, vurgu), "bitkileri" kelimesini doğru ünlüyle telaffuz eden ve canlı bir ses asistanı için CPU'da 300 ms altında çalışan bir ses klibi gerekiyor. Ayrıca sesleri değiştirebilmen, code-switched girdiyi ("saat 6'da hatırlat, daijoubu?") ele alabilmen ve isimlerde kendini rezil etmemen gerekiyor.

Modern TTS pipeline'ları şöyle görünür:

1. **Text frontend.** Metni normalize et (tarihler, sayılar, e-postalar), fonemlere ya da subword token'lara çevir, prozodi özelliklerini tahmin et.
2. **Akustik model.** Metin → mel-spektrogram. Tacotron 2 (2017), FastSpeech 2 (2020), VITS (2021), F5-TTS (2024), Kokoro (2024).
3. **Vocoder.** Mel → dalga formu. WaveNet (2016), WaveRNN, HiFi-GAN (2020), BigVGAN (2022), 2024+ nöral codec vocoder'ları.

2026'da akustik + vocoder ayrımı end-to-end diffusion ve flow-matching modelleriyle bulanıklaşıyor. Ama üç-parça zihinsel modeli debugging için hâlâ geçerli.

## Kavram

![Tacotron, FastSpeech, VITS, F5/Kokoro yan yana](../assets/tts.svg)

**Tacotron 2 (2017).** Seq2seq: char-embedding → BiLSTM encoder → location-sensitive attention → autoregressive LSTM decoder mel frame'lerini yayar. Yavaş (AR), uzun metinde dengesiz. Hâlâ baseline olarak atıf alır.

**FastSpeech 2 (2020).** Non-autoregressive. Duration predictor her foneme kaç mel frame düşeceğini çıkarır. 1-pass, Tacotron'dan 10× hızlı. Biraz naturalness kaybeder (monotonik hizalama) ama her yerde yayınlanır.

**VITS (2021).** Encoder + flow-tabanlı duration + HiFi-GAN vocoder'ı varyasyonel çıkarımla end-to-end ortak eğitir. Yüksek kalite, tek model. 2022–2024 baskın open-source TTS. Varyantlar: YourTTS (multi-speaker zero-shot), XTTS v2 (2024, Coqui).

**F5-TTS (2024).** Flow matching üzerinde diffusion transformer. Doğal prozodi, 5 saniyelik referans ses ile zero-shot ses klonlama. 2026 open-source TTS leaderboard'larının zirvesinde. 335M param.

**Kokoro (2024).** Küçük (82M), CPU'da çalışabilir, real-time kullanım için sınıfının en iyisi İngilizce TTS. Closed-vocabulary İngilizce-only, apache-2.0.

**OpenAI TTS-1-HD, ElevenLabs v2.5, Google Chirp-3.** Ticari state of the art. ElevenLabs v2.5 emotion tag'leri ("[whispered]", "[laughing]") ve karakter sesleri 2026'da sesli kitap üretimini domine ediyor.

### Vocoder evrimi

| Dönem | Vocoder | Gecikme | Kalite |
|-----|---------|---------|---------|
| 2016 | WaveNet | sadece offline | yayınlandığında SOTA |
| 2018 | WaveRNN | ~realtime | iyi |
| 2020 | HiFi-GAN | 100× realtime | insan eşdeğeri |
| 2022 | BigVGAN | 50× realtime | konuşmacılar/dil'ler arası genelleşir |
| 2024 | SNAC, DAC (nöral codec'ler) | AR modellerle entegre | discrete token'lar, bit-verimli |

2026'ya gelindiğinde çoğu "TTS" modeli metinden dalga formuna end-to-end; mel-spektrogram dahili bir temsil.

### Değerlendirme

- **MOS (Mean Opinion Score).** 1–5 ölçek, crowd-sourced. Hâlâ altın standart; acı verici yavaş.
- **CMOS (Comparative MOS).** A-vs-B tercihi. Annotation başına daha sıkı güven aralıkları.
- **UTMOS, DNSMOS.** Reference-free nöral MOS tahmincileri. Leaderboard'lar için kullanılır.
- **ASR üzerinden CER (Character Error Rate).** TTS çıktısını Whisper'dan geçir, giriş metnine karşı CER hesapla. Anlaşılırlık için proxy.
- **SECS (Speaker Embedding Cosine Similarity).** Ses klonlama kalitesi.

LibriTTS test-clean üzerinde 2026 rakamları:

| Model | UTMOS | CER (Whisper üzerinden) | Boyut |
|-------|-------|-------------------|------|
| Ground truth | 4.08 | %1.2 | — |
| F5-TTS | 3.95 | %2.1 | 335M |
| XTTS v2 | 3.81 | %3.5 | 470M |
| VITS | 3.62 | %3.1 | 25M |
| Kokoro v0.19 | 3.87 | %1.8 | 82M |
| Parler-TTS Large | 3.76 | %2.8 | 2.3B |

## İnşa Et

### Adım 1: Girdiyi phonemize et

```python
from phonemizer import phonemize
ph = phonemize("Hello world", language="en-us", backend="espeak")
# 'həloʊ wɜːld'
```

Fonemler evrensel köprüdür. VITS seviyesinin altındaki kaliteye ham metin beslemekten kaçın.

### Adım 2: Kokoro çalıştır (2026 CPU varsayılanı)

```python
from kokoro import KPipeline
tts = KPipeline(lang_code="a")  # "a" = American English
audio, sr = tts("Please remind me to water the plants at 6 pm.", voice="af_bella")
# audio: float32 tensor, sr=24000
```

Offline çalışır, tek dosya, 82M param.

### Adım 3: Ses klonlamayla F5-TTS çalıştır

```python
from f5_tts.api import F5TTS
tts = F5TTS()
wav = tts.infer(
    ref_file="my_voice_5s.wav",
    ref_text="The quick brown fox jumps over the lazy dog.",
    gen_text="Please remind me to water the plants.",
)
```

5 saniyelik referans klip + transkriptini geç; F5 prozodi ve tını'yı klonlar.

### Adım 4: Sıfırdan HiFi-GAN vocoder

Tutorial script'e sığmayacak kadar büyük, ama şekli:

```python
class HiFiGAN(nn.Module):
    def __init__(self, mel_channels=80, upsample_rates=[8, 8, 2, 2]):
        super().__init__()
        # 4 upsample blok, mel-rate'ten audio-rate'e geçmek için toplam 256x
        ...
    def forward(self, mel):
        return self.blocks(mel)  # -> dalga formu
```

Eğitim: adversarial (kısa pencereler üzerinde discriminator) + mel-spektrogram reconstruction loss + feature-matching loss. Commoditized — `hifi-gan` repo ya da nvidia-NeMo'dan pretrained checkpoint kullan.

### Adım 5: Tam pipeline (pseudokod)

```python
text = "Please remind me at 6 pm."
phones = phonemize(text)
mel = acoustic_model(phones, speaker=alice)      # [T, 80]
wav = vocoder(mel)                                # [T * 256]
soundfile.write("out.wav", wav, 24000)
```

## Kullan

2026 yığını:

| Durum | Seç |
|-----------|------|
| Real-time İngilizce ses asistanı | Kokoro (CPU) ya da XTTS v2 (GPU) |
| 5 sn referanstan ses klonlama | F5-TTS |
| Ticari karakter sesleri | ElevenLabs v2.5 |
| Sesli kitap anlatımı | ElevenLabs v2.5 ya da XTTS v2 + fine-tune |
| Düşük-kaynaklı dil | 5–20 saatlik hedef-dil verisinde VITS eğit |
| Ekspresif / emotion tag'leri | ElevenLabs v2.5 ya da StyleTTS 2 fine-tune |

2026 itibarıyla open-source lider: **kalite için F5-TTS, verimlilik için Kokoro**. Tarihçi değilsen Tacotron'a uzanma.

## Tuzaklar

- **Metin normalizer yok.** "Dr. Smith" "Doctor" mu "Drive" mı okunur? "2026" "twenty twenty six" mı "two zero two six" mi? Phonemizer'dan ÖNCE normalize et.
- **OOV özel isimler.** "Ghumare" → "ghyu-mair"? Bilinmeyen token'lar için fallback grapheme-to-phoneme model yayınla.
- **Clipping.** Vocoder çıktısı nadiren clip olur, ama çıkarımda mel ölçekleme uyuşmazlığı ±1.0'ı aşabilir. Her zaman `np.clip(wav, -1, 1)`.
- **Örnekleme oranı uyuşmazlığı.** Kokoro 24 kHz çıkarır; downstream pipeline'ın 16 kHz bekliyor → resample et ya da aliasing al.

## Yayınla

`outputs/skill-tts-designer.md` olarak kaydet. Verilen bir ses, gecikme ve dil hedefi için TTS pipeline'ı tasarla.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Toy bir vocab'tan fonem sözlüğü inşa eder, fonem başına süreyi tahmin eder ve sahte bir "mel" programı yazdırır.
2. **Orta.** Kokoro'yu kur, aynı cümleyi `af_bella` ve `am_adam` sesleriyle sentezle. Ses sürelerini ve öznel kaliteyi karşılaştır.
3. **Zor.** Kendinin 5 saniyelik bir referans klibini kaydet. F5-TTS ile klonla. Referans ile klonlanan çıktı arası SECS raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Fonem | Ses birimi | Soyut ses sınıfı; İngilizcede 39 (ARPABet). |
| Duration predictor | Her fonemin ne kadar süreceği | Non-AR model çıktısı; fonem başına tam sayı frame. |
| Vocoder | Mel → dalga formu | Mel-spec'i ham örneklere eşleyen sinir ağı. |
| HiFi-GAN | Standart vocoder | GAN tabanlı; 2020–2024 baskın. |
| MOS | Öznel kalite | İnsan değerlendiricilerden 1–5 mean opinion score. |
| SECS | Ses-klon metriği | Hedef ve çıktı konuşmacı embedding'i arası kosinüs benzerliği. |
| F5-TTS | 2024 open-source SOTA | Flow-matching diffusion; zero-shot klonlama. |
| Kokoro | CPU İngilizce lideri | 82M-paramlı model, Apache 2.0. |

## İleri Okuma

- [Shen et al. (2017). Tacotron 2](https://arxiv.org/abs/1712.05884) — seq2seq baseline.
- [Kim, Kong, Son (2021). VITS](https://arxiv.org/abs/2106.06103) — end-to-end flow-tabanlı.
- [Chen et al. (2024). F5-TTS](https://arxiv.org/abs/2410.06885) — güncel open-source SOTA.
- [Kong, Kim, Bae (2020). HiFi-GAN](https://arxiv.org/abs/2010.05646) — 2026'da hâlâ yayınlanan vocoder.
- [Kokoro-82M on HuggingFace](https://huggingface.co/hexgrad/Kokoro-82M) — 2024 CPU dostu İngilizce TTS.
