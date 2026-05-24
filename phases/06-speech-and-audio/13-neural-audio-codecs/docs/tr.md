# Nöral Ses Codec'leri — EnCodec, SNAC, Mimi, DAC ve Semantik-Akustik Ayrımı

> 2026 ses üretimi neredeyse tamamen token. EnCodec, SNAC, Mimi ve DAC sürekli dalga formlarını bir transformer'ın tahmin edebileceği discrete dizilere çevirir. Semantik vs akustik token ayrımı — birinci codebook semantik olarak, geri kalanı akustik olarak — ses için Transformer'dan beri en önemli mimari değişimdir.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar), Faz 10 · 11 (Quantization), Faz 5 · 19 (Subword Tokenization)
**Süre:** ~60 dakika

## Sorun

Dil modelleri discrete token üzerinde çalışır. Ses sürekli. Konuşma / müzik için LLM-tarzı bir model istiyorsan — MusicGen, Moshi, Sesame CSM, VibeVoice, Orpheus — önce bir **nöral ses codec'ine** ihtiyacın var: sesi küçük bir token sözlüğüne discretize eden öğrenilmiş encoder ve dalga formunu yeniden oluşturan eşleşen decoder.

İki aile ortaya çıktı:

1. **Reconstruction-first codec'ler** — EnCodec, DAC. Algısal ses kalitesini optimize eder. Token'lar "akustik" — konuşmacı kimliği, tını, arka plan gürültüsü dahil her şeyi yakalar.
2. **Semantic-first codec'ler** — Mimi (Kyutai), SpeechTokenizer. Birinci codebook'u linguistik / fonetik içeriği encode etmeye zorlar (genellikle WavLM'den distill ederek). Sonraki codebook'lar akustik ayrıntı.

2024-2026 içgörüsü: **saf reconstruction codec'i metinden üretmeye çalıştığında sana bulanık konuşma verir.** Codec token'ları üzerindeki LLM, aynı codebook'ta hem dil yapısını HEM de akustik yapıyı öğrenmek zorunda kalır ki bu ölçeklenmez. Onları ayırmak — semantik codebook 0, akustik codebook'lar 1-N — Moshi ve Sesame CSM'i çalıştıran şeydir.

## Kavram

![Dört codec manzarası: EnCodec, DAC, SNAC (multi-scale), Mimi (semantic+acoustic)](../assets/codec-comparison.svg)

### Temel hile: Residual Vector Quantization (RVQ)

İyi kalite için milyonlarca koda ihtiyaç duyacak tek büyük bir codebook yerine, tüm modern ses codec'leri **RVQ** kullanır: küçük codebook'lardan oluşan bir kaskat. Birinci codebook encoder çıktısını quantize eder; ikinci residual'ı quantize eder; vs. Her codebook 1024 kod. 8 codebook = etkin sözlük 1024^8 = 10^24.

Çıkarım zamanında, decoder yeniden oluşturmak için frame başına seçilen tüm kodları toplar.

### 2026'da önemli olan dört codec

**EnCodec (Meta, 2022).** Baseline. Dalga formu üzerinde encoder-decoder, RVQ bottleneck. 24 kHz, 32 codebook mümkün, varsayılan 4 codebook @ 1.5 kbps. `1D conv + transformer + 1D conv` mimarisi kullanır. MusicGen tarafından kullanılır.

**DAC (Descript, 2023).** L2-normalize edilmiş codebook'larla RVQ, periyodik aktivasyon fonksiyonları, iyileştirilmiş loss'lar. Herhangi bir açık codec'in en yüksek reconstruction fidelity'si — 12 codebook ile bazen orijinal konuşmadan ayırt edilemez. 44.1 kHz full-band.

**SNAC (Hubert Siuzdak, 2024).** Multi-scale RVQ — kaba codebook'lar ince olanlardan daha düşük frame rate'te çalışır. Sesi hiyerarşik olarak etkin modelliyor: ~12 Hz'de bir kaba "taslak" artı 50 Hz'de ayrıntı. Hiyerarşik yapı LM tabanlı üretime iyi haritalandığı için Orpheus-3B tarafından kullanılır.

**Mimi (Kyutai, 2024).** 2026 oyun değiştiricisi. 12.5 Hz frame rate (son derece düşük), 8 codebook @ 4.4 kbps. Codebook 0, **WavLM'den distill edilmiş** — WavLM'in konuşma-içerik özniteliklerini tahmin etmek için eğitilmiş. Codebook'lar 1-7 akustik residual. Bu ayrım Moshi'yi (Ders 15) ve Sesame CSM'i çalıştırır.

### Dil modellemesi için frame rate'ler önemlidir

Daha düşük frame rate = daha kısa dizi = daha hızlı LM.

| Codec | Frame rate | 1 sn = N frame | Şuna iyi |
|-------|-----------|----------------|---------|
| EnCodec-24k | 75 Hz | 75 | müzik, genel ses |
| DAC-44.1k | 86 Hz | 86 | high-fidelity müzik |
| SNAC-24k (kaba) | ~12 Hz | 12 | AR-LM verimli |
| Mimi | 12.5 Hz | 12.5 | streaming konuşma |

12.5 Hz'de 10 saniyelik bir utterance sadece 125 codec frame — bir transformer bunları kolayca tahmin edebilir.

### Semantik vs akustik token'lar

```
frame_t → [semantic_token_t, acoustic_token_0_t, acoustic_token_1_t, ..., acoustic_token_6_t]
```

- **Semantik token (Mimi'de codebook 0).** Ne söylendiğini encode eder — fonemler, kelimeler, içerik. Yardımcı tahmin loss'u üzerinden WavLM'den distill edilir.
- **Akustik token'lar (codebook'lar 1-7).** Tını, konuşmacı kimliği, prozodi, arka plan gürültüsü, ince ayrıntıyı encode eder.

Bir AR LM önce semantik token'ı tahmin eder (metne koşullu), sonra akustik token'ları tahmin eder (semantik + konuşmacı referansına koşullu). Bu faktörizasyon, modern TTS'in sesleri zero-shot-klonlayabilmesinin nedeni: semantik model içeriği ele alır; akustik model tını'yı ele alır.

### 2026 reconstruction kalitesi (saniyede bit, daha düşük bitrate daha iyi)

| Codec | Bitrate | PESQ | ViSQOL |
|-------|---------|------|--------|
| Opus-20kbps | 20 kbps | 4.0 | 4.3 |
| EnCodec-6kbps | 6 kbps | 3.2 | 3.8 |
| DAC-6kbps | 6 kbps | 3.5 | 4.0 |
| SNAC-3kbps | 3 kbps | 3.3 | 3.8 |
| Mimi-4.4kbps | 4.4 kbps | 3.1 | 3.7 |

Opus gibi geleneksel codec'ler bit başına algısal kalitede hâlâ kazanır. Nöral codec'ler **discrete token'larda** (Opus üretmez) ve **üretken-model kalitesinde** (LM'in bu token'larla yapabileceği şey) kazanır.

## İnşa Et

### Adım 1: EnCodec ile encode et

```python
from encodec import EncodecModel
import torch

model = EncodecModel.encodec_model_24khz()
model.set_target_bandwidth(6.0)  # kbps

wav = torch.randn(1, 1, 24000)
with torch.no_grad():
    encoded = model.encode(wav)
codes, scale = encoded[0]
# codes: (1, n_codebooks, n_frames), dtype=int64
```

6 kbps'de `n_codebooks=8`. Her kod 0-1023 (10-bit).

### Adım 2: Decode et ve reconstruction ölç

```python
with torch.no_grad():
    wav_recon = model.decode([(codes, scale)])

from torchaudio.functional import compute_deltas
import torch.nn.functional as F

mse = F.mse_loss(wav_recon[:, :, :wav.shape[-1]], wav).item()
```

### Adım 3: Semantik-akustik ayrımı (Mimi-tarzı)

```python
from moshi.models import loaders
mimi = loaders.get_mimi()

with torch.no_grad():
    codes = mimi.encode(wav)  # shape (1, 8, frames@12.5Hz)

semantic = codes[:, 0]
acoustic = codes[:, 1:]
```

Semantik codebook 0 WavLM-hizalı. Bir text-to-semantic transformer eğitebilirsin — doğrudan-sese gitmekten çok daha küçük sözlük. Sonra ayrı bir akustik-to-waveform decoder konuşmacı referansına koşullanır.

### Adım 4: Codec token'ları üzerinde AR LM neden çalışır

Mimi'nin 12.5 Hz × 8 codebook'unda 10 sn konuşma klibi için:

```
N_tokens = 10 * 12.5 * 8 = 1000 token
```

1000 token bir transformer için önemsiz bir bağlam. 256M-paramlı bir transformer modern GPU'da milisaniyeler içinde 10 saniyelik konuşma üretebilir.

## Kullan

Problem → codec haritası:

| Görev | Codec |
|------|-------|
| Genel müzik üretimi | EnCodec-24k |
| En yüksek fidelity reconstruction | DAC-44.1k |
| Konuşma üzerinde AR LM (TTS) | SNAC ya da Mimi |
| Streaming full-duplex konuşma | Mimi (12.5 Hz) |
| Metinle ses-efekt kütüphanesi | EnCodec + T5 koşulu |
| İnce-ayrıntılı ses düzenleme | DAC + inpainting |

Pratik kural: **üretken model kuruyorsan Mimi ya da SNAC ile başla. Sıkıştırma pipeline'ı kuruyorsan Opus kullan.**

## Tuzaklar

- **Çok fazla codebook.** Codebook eklemek fidelity'i lineer artırır ama LM dizi uzunluğunu da lineer artırır. 8-12'de dur.
- **Frame-rate uyuşmazlığı.** LM'i 12.5 Hz Mimi'de eğitip sonra 50 Hz EnCodec'te fine-tune etmek sessizce başarısız olur.
- **Tüm codebook'ların eşit olduğunu varsaymak.** Mimi'de codebook 0 içeriği taşır; onu kaybetmek anlaşılırlığı yok eder. Codebook 7'yi kaybetmek zar zor fark edilir.
- **Reconstruction kalitesini tek metrik olarak kullanmak.** Bir codec harika reconstruction'a sahip olabilir ama semantik yapısı kötüyse LM tabanlı üretim için işe yaramaz olabilir.

## Yayınla

`outputs/skill-codec-picker.md` olarak kaydet. Verilen üretken ya da sıkıştırma görevi için codec seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Toy bir skaler + residual quantizer implement eder ve codebook ekledikçe reconstruction hatasını ölçer.
2. **Orta.** `encodec`'i kur ve held-out konuşma klibinde 1, 4, 8, 32 codebook'u karşılaştır. PESQ ya da MSE'yi bitrate'e karşı çiz.
3. **Zor.** Mimi yükle. Bir klibi encode et. Codebook 0'ı rastgele tam sayılarla değiştir; decode et. Sonra codebook 7'yi benzer şekilde değiştir. İki bozulmayı karşılaştır — codebook 0 bozulması anlaşılırlığı yok etmeli; codebook 7 bozulması neredeyse hiçbir şey değiştirmemeli.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| RVQ | Residual quantization | Küçük codebook'ların kaskadı; her biri öncekinin residual'ını quantize eder. |
| Frame rate | Codec hızı | Saniyede kaç token-frame. Daha düşük = daha hızlı LM. |
| Semantik codebook | Codebook 0 (Mimi) | SSL özniteliklerinden distill edilmiş codebook; içeriği encode eder. |
| Akustik codebook'lar | Diğer her şey | Tını, prozodi, gürültü, ince ayrıntı. |
| PESQ / ViSQOL | Algısal kalite | MOS ile korele objektif metrikler. |
| EnCodec | Meta codec'i | RVQ baseline'ı; MusicGen tarafından kullanılır. |
| Mimi | Kyutai codec'i | 12.5 Hz frame rate; semantik-akustik ayrım; Moshi'yi çalıştırır. |

## İleri Okuma

- [Défossez et al. (2023). EnCodec](https://arxiv.org/abs/2210.13438) — RVQ baseline'ı.
- [Kumar et al. (2023). Descript Audio Codec (DAC)](https://arxiv.org/abs/2306.06546) — en yüksek fidelity açık.
- [Siuzdak (2024). SNAC](https://arxiv.org/abs/2410.14411) — multi-scale RVQ.
- [Kyutai (2024). Mimi codec](https://kyutai.org/codec-explainer) — semantik-akustik ayrım, WavLM distillation.
- [Borsos et al. (2023). AudioLM](https://arxiv.org/abs/2209.03143) — iki-aşamalı semantik/akustik paradigma.
- [Zeghidour et al. (2021). SoundStream](https://arxiv.org/abs/2107.03312) — orijinal streamable RVQ codec'i.
