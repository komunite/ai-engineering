# Ses Üretimi

> Ses 16-48 kHz'de 1-D bir sinyal. Beş saniyelik bir klip 80-240k örnek. Hiçbir transformer doğrudan bu diziye attend etmez. 2026'da her üretim ses modeli için çözüm aynı: bir neural codec (Encodec, SoundStream, DAC) sesi 50-75 Hz'de discrete token'lara sıkıştırır ve bir transformer ya da diffusion modeli token'ları üretir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Ses Özellikleri), Faz 6 · 04 (ASR), Faz 8 · 06 (DDPM)
**Süre:** ~45 dakika

## Sorun

Üç ses üretim görevi:

1. **Text-to-speech.** Metin verildiğinde, konuşma üret. Temiz konuşma dar bantlıdır ve güçlü fonetik yapıya sahiptir — token üzerinde transformer ile iyi çözülür. VALL-E (Microsoft), NaturalSpeech 3, ElevenLabs, OpenAI TTS.
2. **Müzik üretimi.** Bir prompt (metin, melodi, akor ilerleyişi, tür) verildiğinde müzik üret. Çok daha geniş dağılım. MusicGen (Meta), Stable Audio 2.5, Suno v4, Udio, Riffusion.
3. **Ses efektleri / sound design.** Bir prompt verildiğinde ambient ses ya da Foley üret. AudioGen, AudioLDM 2, Stable Audio Open.

Üçü de aynı alt zeminde çalışır: neural audio codec + token-AR ya da diffusion generator.

## Kavram

![Ses üretimi: codec token'ları + transformer ya da diffusion](../assets/audio-generation.svg)

### Neural audio codec'leri

Encodec (Meta, 2022), SoundStream (Google, 2021), Descript Audio Codec (DAC, 2023). Bir konvolüsyonel encoder waveform'u zaman adımı başına bir vektöre sıkıştırır; residual vector quantization (RVQ) her vektörü K codebook indeksinin bir kademesine dönüştürür. Decoder tersine çevirir. 75 Hz'de 8 RVQ codebook kullanan 2 kbps'te 24 kHz ses = 600 token/saniye.

```
waveform (16000 örnek/saniye)
    └─ encoder conv ─┐
                     ├─ RVQ katman 1 → 75 Hz'de indeksler
                     ├─ RVQ katman 2 → 75 Hz'de indeksler
                     ├─ ...
                     └─ RVQ katman 8
```

### Üzerine iki üretken paradigma

**Token-autoregressive.** RVQ token'larını bir diziye düzleştir, decoder-only bir transformer çalıştır. MusicGen K codebook stream'ini stream başına offset'lerle paralel yaymak için "delayed parallel" kullanır. VALL-E metin promptu + 3 saniyelik ses örneğinden konuşma token'ları üretir.

**Latent diffusion.** Codec token'larını sürekli latent'ler olarak paketle ya da onları kategorik diffusion ile modelle. Stable Audio 2.5 sürekli ses latent'leri üzerinde flow matching kullanır. AudioLDM 2 text-to-mel-to-audio diffusion kullanır.

2024-2026 trendi: flow matching müzikte kazanıyor (daha hızlı çıkarım, daha temiz örnekler), token-AR doğal olarak causal olduğu ve iyi stream ettiği için konuşmaya hâlâ hakim.

## Üretim manzarası

| Sistem | Görev | Omurga | Latency |
|--------|------|----------|---------|
| ElevenLabs V3 | TTS | Token-AR + neural vocoder | ~300ms ilk token |
| OpenAI GPT-4o audio | Tam-dubleks konuşma | Uçtan-uca multimodal AR | ~200ms |
| NaturalSpeech 3 | TTS | Latent flow matching | Streaming değil |
| Stable Audio 2.5 | Müzik / SFX | Ses latent'leri üzerinde DiT + flow matching | 1 dakikalık klip için ~10sn |
| Suno v4 | Tam şarkılar | Açıklanmamış; token-AR şüpheli | Şarkı başına ~30sn |
| Udio v1.5 | Tam şarkılar | Açıklanmamış | Şarkı başına ~30sn |
| MusicGen 3.3B | Müzik | Encodec 32kHz üzerinde token-AR | Gerçek zamanlı |
| AudioCraft 2 | Müzik + SFX | Flow matching | 5sn klip için ~5sn |
| Riffusion v2 | Müzik | Spektrogram diffusion | ~10sn |

## İnşa Et

`code/main.py` temel fikri simüle eder: iki farklı "stilden" üretilmiş sentetik "ses token'ı" dizileri üzerinde minik bir next-token transformer eğit (stil A için alternatif düşük ve yüksek token'lar, stil B için monotonik rampa). Stil üzerinde koşulla ve örnekle.

### Adım 1: sentetik ses token'ları

```python
def make_tokens(style, length, vocab_size, rng):
    if style == 0:  # "konuşma-benzeri": alternatif
        return [i % vocab_size for i in range(length)]
    # "müzik-benzeri": rampa
    return [(i * 3) % vocab_size for i in range(length)]
```

### Adım 2: minik bir token tahmincisi eğit

Stil üzerinde koşullanmış bir bigram-tarzı tahminci. Önemli olan desen: codec token'ları → cross-entropy eğitim → autoregressive sampling.

### Adım 3: koşullu örnekle

Stil token'ı ve bir başlangıç token'ı verildiğinde, sonraki token'ı tahmin edilen dağılımdan örnekle. 20-40 token boyunca devam et.

## Tuzaklar

- **Codec kalitesi çıkış kalitesini sınırlar.** Codec bir sesi sadık şekilde temsil edemiyorsa, hiçbir generator kalitesi yardımcı olmaz. DAC mevcut açık en iyisi.
- **RVQ hata birikimi.** Her RVQ katmanı öncekinin residual'ını modeller. 1. katmandaki hatalar yayılır. Üst katmanlarda sıcaklık 0 ile örnekleme yardımcı olur.
- **Müzikal yapı.** 30 saniyelik token'lar 75 Hz'de 20k+ token. Transformer'lar için zor. MusicGen kayan pencere + prompt devam kullanır; Stable Audio daha kısa klipler + crossfading kullanır.
- **Sınırlarda artefaktlar.** Üretilen klipler arasında crossfade dikkatli overlap-add gerektirir.
- **Temiz veri iştahı.** Müzik generator'ları on binlerce saatlik lisanslı müzik gerektirir. Suno / Udio RIAA davası (2024) bunu yüzeye çıkardı.
- **Voice cloning etiği.** 3 saniyelik bir örnek artı bir metin promptu, VALL-E / XTTS / ElevenLabs'ın bir sesi klonlamasına yeter. Her üretim modeli suistimal tespiti + opt-out listeleri gerektirir.

## Kullan

| Görev | 2026 yığını |
|------|------------|
| Ticari TTS | ElevenLabs, OpenAI TTS ya da Azure Neural |
| Voice cloning (rıza onaylı) | XTTS v2 (açık) ya da ElevenLabs Pro |
| Arka plan müziği, hızlı | Stable Audio 2.5 API, Suno ya da Udio |
| Sözlü müzik | Suno v4 ya da Udio v1.5 |
| Ses efektleri / Foley | AudioCraft 2, ElevenLabs SFX ya da Stable Audio Open |
| Gerçek zamanlı ses agent'ı | GPT-4o realtime ya da Gemini Live |
| Açık ağırlık müzik araştırması | MusicGen 3.3B, Stable Audio Open 1.0, AudioLDM 2 |
| Dublaj / çeviri | HeyGen, ElevenLabs Dubbing |

## Yayınla

`outputs/skill-audio-brief.md` olarak kaydet. Skill bir ses brief'i (görev, süre, stil, ses, lisans) alır ve şunu çıkarır: model + hosting, prompt formatı (tür tag'leri, stil tanımlayıcıları, yapısal işaretçiler), codec + generator + vocoder zinciri, seed protokolü ve eval planı (MOS / CLAP score / TTS için CER / kullanıcı A/B).

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi çalıştır ve stili açıkça ayarla. Üretilen dizilerin stilin desenini eşlediğini doğrula.
2. **(Orta)** Delayed parallel decoding ekle: 1 adım offset kalması gereken 2 token stream'ini simüle et. Ortak bir tahminci eğit.
3. **(Zor)** MusicGen-small'u yerel çalıştırmak için HuggingFace transformers kullan. Üç farklı promptla 10 saniyelik klip üret; stil sadakati için A/B yap.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Codec | "Neural sıkıştırma" | Ses için encoder / decoder; tipik çıktı 50-75 Hz token'lar. |
| RVQ | "Residual VQ" | K quantizer'lı kademe; her biri öncekinin residual'ını modeller. |
| Token | "Bir codec sembolü" | Bir codebook'a discrete indeks; 1024 ya da 2048 tipik. |
| Delayed parallel | "Offset codebook'lar" | Dizi uzunluğunu azaltmak için K token stream'ini kademeli offset'lerle yay. |
| Flow matching | "Sesin 2024 zaferi" | Diffusion'a daha düz-yol alternatifi; daha hızlı örnekleme. |
| Voice prompt | "3 saniyelik örnek" | Klonlanan sesi yönlendiren konuşmacı embedding'i ya da token prefix'i. |
| Mel spectrogram | "Görsel" | Log-büyüklük algısal spektrogram; birçok TTS sistemi tarafından kullanılır. |
| Vocoder | "Mel'den dalgaya" | Mel spektrogramlarını sese geri çeviren neural bileşen. |

## Üretim notu: ses bir streaming problemidir

Ses, kullanıcıların *üretildikçe* gelmesini beklediği tek çıkış modalitesi — hepsi birden değil. Üretim terimleriyle bu TPOT'un (Time Per Output Token) önemli olduğu anlamına gelir çünkü kullanıcının dinleme hızı hedef throughput'tur — okuma hızı değil. Encodec'te ~75 token/saniyede tokenize edilmiş 16kHz ses için, sunucu oynatmayı pürüzsüz tutmak için kullanıcı başına ≥75 token/sn üretmeli.

İki mimari sonuç:

- **Flow-matching ses modelleri trivial olarak stream edemez.** Stable Audio 2.5 ve AudioCraft 2 sabit klip uzunluğunu tek pass'te render eder. Stream etmek için klibi parçalayıp sınırları overlap'lersin — kayan-pencere diffusion'ı düşün — bir codec AR modeline göre 100-300ms latency yükü ekler.

Ürün "canlı sesli sohbet" ya da "gerçek zamanlı müzik devamı" ise, codec AR yolunu seç. "Submit'te 30 saniyelik klip render et" ise, flow-matching kalite ve toplam latency'de kazanır.

## İleri Okuma

- [Défossez et al. (2022). Encodec: High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438) — codec standardı.
- [Zeghidour et al. (2021). SoundStream](https://arxiv.org/abs/2107.03312) — yaygın kullanılan ilk neural ses codec'i.
- [Kumar et al. (2023). High-Fidelity Audio Compression with Improved RVQGAN (DAC)](https://arxiv.org/abs/2306.06546) — DAC.
- [Wang et al. (2023). Neural Codec Language Models are Zero-Shot Text to Speech Synthesizers (VALL-E)](https://arxiv.org/abs/2301.02111) — VALL-E.
- [Copet et al. (2023). Simple and Controllable Music Generation (MusicGen)](https://arxiv.org/abs/2306.05284) — MusicGen.
- [Liu et al. (2023). AudioLDM 2: Learning Holistic Audio Generation with Self-supervised Pretraining](https://arxiv.org/abs/2308.05734) — AudioLDM 2.
- [Stability AI (2024). Stable Audio 2.5](https://stability.ai/news/introducing-stable-audio-2-5) — flow matching'li 2025 text-to-music.
