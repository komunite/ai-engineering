# Ses Anti-Spoofing ve Ses Watermarking — ASVspoof 5, AudioSeal, WaveVerify

> Ses klonlama savunmalardan daha hızlı yayına çıktı. 2026 üretim ses sistemlerinin iki şeye ihtiyacı var: gerçek vs sahte konuşmayı sınıflandıran bir detektör (AASIST, RawNet2) ve sıkıştırma ile düzenlemeyi atlatan bir watermark (AudioSeal). İkisini de yayınla ya da ses klonlamayı yayınlama.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 06 (Konuşmacı Tanıma), Faz 6 · 08 (Ses Klonlama)
**Süre:** ~75 dakika

## Sorun

Üç ilgili savunma:

1. **Anti-spoofing / deepfake algılama.** Verilen bir ses klibi, sentetik mi gerçek mi? ASVspoof benchmark'ları (ASVspoof 2019 → 2021 → 5) altın standart.
2. **Ses watermarking.** Bir detektörün sonradan çıkarabileceği algılanamaz bir sinyali üretilmiş sese göm. AudioSeal (Meta) ve WavMark açık seçenekler.
3. **Doğrulanmış kaynak.** Ses dosyalarının + metadata'nın kriptografik imzalanması. C2PA / Content Authenticity Initiative.

Algılama işbirliği yapmayan saldırganları ele alır. Watermarking compliance'ı ele alır — AI tarafından üretilmiş ses bu şekilde tanımlanabilir olmalı. İkisi de 2026'da zorunlu.

## Kavram

![Anti-spoofing vs watermarking vs provenance — üç savunma katmanı](../assets/spoofing-watermark.svg)

### ASVspoof 5 — 2024-2025 benchmark'ı

Önceki sürümlerden en büyük değişim:

- **Crowdsourced veri** (stüdyo temiz değil) — gerçekçi koşullar.
- **~2000 konuşmacı** (önceden ~100).
- **32 saldırı algoritması.** TTS + ses dönüştürme + adversarial perturbasyon.
- **İki track.** Countermeasure (CM) standalone algılama; biyometrik sistemler için Spoofing-robust ASV (SASV).

ASVspoof 5'te state-of-the-art: ~%7.23 EER. Daha eski ASVspoof 2019 LA'da: %0.42 EER. Gerçek dünya deployment'ında: in-the-wild kliplerde %5-10 EER bekle.

### AASIST ve RawNet2 — algılama model aileleri

**AASIST** (2021, 2026'ya kadar güncellendi). Spektral öznitelikler üzerinde graph-attention. ASVspoof 5 countermeasure görevinde mevcut SOTA.

**RawNet2.** Ham dalga formu üzerinde convolutional front-end + TDNN backbone. Daha basit baseline; fine-tuning ile hâlâ rekabetçi.

**NeXt-TDNN + SSL özniteliklerini.** 2025 varyantı: ECAPA-tarzı + WavLM öznitelikleri + focal loss. ASVspoof 2019 LA'da %0.42 EER'e ulaşıyor.

### AudioSeal — 2024 watermark varsayılanı

Meta'nın **AudioSeal**'ı (Oca 2024, v0.2 Ara 2024). Kritik tasarım:

- **Localized.** Watermark'ı 16 kHz örnek çözünürlüğünde (1/16000 sn) frame başına algılar.
- **Generator + detektör ortak eğitilmiş.** Generator algılanamaz sinyali gömmeyi öğrenir; detektör onu augmentation'lar arasından bulmayı öğrenir.
- **Robust.** MP3 / AAC sıkıştırması, EQ, ±%10 speed-shift, +10 dB SNR gürültü karışımını atlatır.
- **Hızlı.** Detektör 485× realtime çalışır; WavMark'tan 1000× hızlı.
- **Kapasite.** 16-bit payload (model ID, üretim timestamp, kullanıcı ID encode edebilir) her utterance'a embeddable.

### WavMark

AudioSeal öncesi açık baseline. Invertible nöral ağ, saniyede 32 bit. Problemler:

- Senkronizasyon brute-force yavaş.
- Gaussian gürültü ya da MP3 sıkıştırması ile kaldırılabilir.
- Real-time dostu değil.

### WaveVerify (Tem 2025)

AudioSeal'ın zayıflıklarını ele alır — özellikle temporal manipülasyonları (tersleme, hız). FiLM tabanlı generator + Mixture-of-Experts detektör kullanır. Standart saldırılarda AudioSeal ile rekabetçi; temporal düzenlemeleri ele alır.

### Saldırganların istismar ettiği boşluk

AudioMarkBench'ten: "pitch shift altında, tüm watermark'lar 0.6'nın altında Bit Recovery Accuracy gösterir, neredeyse tamamen kaldırma anlamına gelir." **Pitch-shift evrensel saldırıdır.** Hiçbir 2026 watermark'ı agresif pitch modifikasyonuna tam robust değil. Bu yüzden watermarking yanında algılama (AASIST) gerek.

### C2PA / Content Authenticity Initiative

ML tekniği değil — bir manifest formatı. Ses dosyaları oluşturma aracı, yazar, tarih hakkında kriptografik imzalanmış metadata taşır. Audobox / Seamless onu kullanır. Provenance için iyi; kötü aktör yeniden encode edip metadata'yı çıkarırsa hiçbir şey yapmaz.

## İnşa Et

### Adım 1: Basit spektral-öznitelik detektörü (toy)

```python
def spectral_rolloff(spec, percentile=0.85):
    cum = 0
    total = sum(spec)
    if total == 0:
        return 0
    threshold = total * percentile
    for k, v in enumerate(spec):
        cum += v
        if cum >= threshold:
            return k
    return len(spec) - 1

def is_suspicious(audio):
    spec = magnitude_spectrum(audio)
    rolloff = spectral_rolloff(spec)
    return rolloff / len(spec) > 0.92
```

Sentetik konuşma genellikle alışılmadık derecede düz yüksek-frekans enerjisine sahiptir. Üretim detektörleri bunu değil, AASIST kullanır. Ama sezgi geçerli.

### Adım 2: AudioSeal embed + detect

```python
from audioseal import AudioSeal
import torch

generator = AudioSeal.load_generator("audioseal_wm_16bits")
detector = AudioSeal.load_detector("audioseal_detector_16bits")

audio = load_wav("generated.wav", sr=16000)[None, None, :]
payload = torch.tensor([[1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0]])
watermark = generator.get_watermark(audio, sample_rate=16000, message=payload)
watermarked = audio + watermark

result, decoded_payload = detector.detect_watermark(watermarked, sample_rate=16000)
# result: [0, 1] aralığında float — watermark varlığı olasılığı
# decoded_payload: 16 bit; embed edilmiş payload ile eşle
```

### Adım 3: Değerlendirme — EER

```python
def eer(real_scores, fake_scores):
    thresholds = sorted(set(real_scores + fake_scores))
    best = (1.0, 0.0)
    for t in thresholds:
        far = sum(1 for s in fake_scores if s >= t) / len(fake_scores)
        frr = sum(1 for s in real_scores if s < t) / len(real_scores)
        if abs(far - frr) < best[0]:
            best = (abs(far - frr), (far + frr) / 2)
    return best[1]
```

### Adım 4: Üretim entegrasyonu

```python
def safe_tts(text, voice, clone_reference=None):
    if clone_reference is not None:
        verify_consent(user_id, clone_reference)
    audio = tts_model.synthesize(text, voice)
    audio_with_wm = audioseal_embed(audio, payload=build_payload(user_id, model_id))
    manifest = c2pa_sign(audio_with_wm, user_id, timestamp=now())
    return audio_with_wm, manifest
```

Her üretim şunları yayınlar: (1) watermark, (2) imzalı manifest, (3) retention-policy-compliant audit log.

## Kullan

| Kullanım | Savunma |
|----------|---------|
| TTS / ses klonlama yayını | Her çıktıda AudioSeal embed (pazarlık edilemez) |
| Biyometrik ses unlock | AASIST + ECAPA ensemble; liveness challenge |
| Çağrı merkezi dolandırıcılık algılama | Gelen aramaların %20 örneğinde AASIST |
| Podcast otantikliği | Yüklemede C2PA imzalama, AI üretimliyse AudioSeal |
| Araştırma / detektör eğitimi | ASVspoof 5 train/dev/eval set'leri |

## Tuzaklar

- **Detektör hiç çalışmadan watermark.** Anlamsız. Detektörü CI'ında yayınla.
- **Kalibrasyonsuz algılama.** ASVspoof LA üzerinde eğitilmiş AASIST overfit yapar; gerçek dünya doğruluğu düşer. Domain'inde kalibre et.
- **Pitch-shift boşluğu.** Agresif pitch shift çoğu watermark'ı kaldırır. Algılama fallback'i bulundur.
- **Metadata strip-and-rehost.** C2PA yeniden encode ile önemsizce atlanabilir. Her zaman kriptografik + algısal (watermark) savunmayı birlikte ekle.
- **Algılama olarak liveness.** Kullanıcıdan rastgele bir cümle söylemesini iste. Replay saldırılarını önler ama real-time klonlamayı önlemez.

## Yayınla

`outputs/skill-spoof-defender.md` olarak kaydet. Ses-gen deployment'ı için algılama modeli, watermark, provenance manifest ve operasyonel playbook seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Sentetik ses üzerinde toy detektör + toy watermark embed/detect.
2. **Orta.** `audioseal`'ı kur, bir TTS çıktısına 16-bit payload göm, yeniden decode et. Sesi gürültüyle bozma ve Bit Recovery Accuracy ölç.
3. **Zor.** ASVspoof 2019 LA üzerinde RawNet2 ya da AASIST fine-tune et. EER ölç. F5-TTS-üretilmiş kliplerin held-out set'inde test et — OOD algılamanın nasıl bozulduğunu gör.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| ASVspoof | Benchmark | İki yılda bir challenge; 2024 = ASVspoof 5. |
| CM (countermeasure) | Detektör | Sınıflandırıcı: gerçek konuşma vs sentetik / dönüştürülmüş. |
| SASV | Konuşmacı verif + CM | Entegre biyometrik + spoof algılama. |
| AudioSeal | Meta watermark'ı | Localized, 16-bit payload, WavMark'tan 485× hızlı. |
| Bit Recovery Accuracy | Watermark hayatta kalması | Saldırı sonrası kurtarılan payload bit oranı. |
| C2PA | Provenance manifest'i | Oluşturma / yazarlık hakkında kriptografik metadata. |
| AASIST | Detektör ailesi | Graph-attention tabanlı anti-spoofing SOTA. |

## İleri Okuma

- [Todisco et al. (2024). ASVspoof 5](https://dl.acm.org/doi/10.1016/j.csl.2025.101825) — güncel benchmark.
- [Defossez et al. (2024). AudioSeal](https://arxiv.org/abs/2401.17264) — watermark varsayılanı.
- [Chen et al. (2025). WaveVerify](https://arxiv.org/abs/2507.21150) — temporal saldırılar için MoE detektör.
- [Jung et al. (2022). AASIST](https://arxiv.org/abs/2110.01200) — SOTA algılama backbone'u.
- [AudioMarkBench (2024)](https://proceedings.neurips.cc/paper_files/paper/2024/file/5d9b7775296a641a1913ab6b4425d5e8-Paper-Datasets_and_Benchmarks_Track.pdf) — robustluk değerlendirme.
- [C2PA specification](https://c2pa.org/specifications/specifications/) — provenance manifest formatı.
