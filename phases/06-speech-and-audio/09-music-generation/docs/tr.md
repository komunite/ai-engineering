# Müzik Üretimi — MusicGen, Stable Audio, Suno ve Lisanslama Depremi

> 2026 müzik üretimi: Suno v5 ve Udio v4 ticariyi domine ediyor; MusicGen, Stable Audio Open ve ACE-Step open-source'a liderlik ediyor. Teknik problem büyük ölçüde çözülmüş durumda. Hukuki problem (Warner Music $500M anlaşma, UMG anlaşması) 2025-2026'da alanı yeniden şekillendirdi.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar), Faz 4 · 10 (Diffusion Modelleri)
**Süre:** ~75 dakika

## Sorun

Metin → 30 saniyeden 4 dakikaya kadar bir müzik klibi; sözler, vokaller ve yapı dahil. Üç alt-problem:

1. **Enstrümantal üretim.** "Sıcak tuşlarla lo-fi hip-hop davulları" gibi metin → ses. MusicGen, Stable Audio, AudioLDM.
2. **Şarkı üretimi (vokaller + sözlerle).** "Yağmurlu Texas geceleri hakkında country şarkısı" → tam şarkı. Suno, Udio, YuE, ACE-Step.
3. **Koşullu / kontrol edilebilir.** Mevcut klibi uzat, bir bridge'i yeniden üret, türü değiştir, stem-ayır ya da inpaint et. Udio'nun inpainting + stem ayırma'sı 2026'da eşleşilmesi gereken özellik.

## Kavram

![Müzik üretimi: token-LM vs diffusion, 2026 model haritası](../assets/music-generation.svg)

### Neural-codec token'ları üzerinde Token LM

Meta'nın **MusicGen**'i (2023, MIT) ve birçok türevi: metin/melodi embedding'lerine koşullan, EnCodec token'larını (32 kHz, 4 codebook) otoregresif tahmin et, EnCodec ile decode et. 300M - 3.3B param. Güçlü baseline; 30 saniyeden sonra zorlanır.

**ACE-Step** (open-source, 4B XL Nisan 2026'da yayınlandı) bunu tam-şarkı, söz-koşullu üretim için genişletir. Açık topluluğun Suno'ya en yakın şeyi.

### Mel'ler ya da latent'lar üzerinde diffusion

**Stable Audio (2023)** ve **Stable Audio Open (2024)**: sıkıştırılmış ses üzerinde latent diffusion. Loop'larda, ses tasarımında, ambient dokularda parlar. Yapılandırılmış tam şarkılarda iyi değil.

**AudioLDM / AudioLDM2**: T2I-tarzı latent diffusion üzerinden text-to-audio, müzik, ses efektleri, konuşmaya genelleştirilmiş.

### Hibrit (üretim) — Suno, Udio, Lyria

Kapalı ağırlıklar. Muhtemelen AR codec LM + diffusion-tabanlı vocoder, özelleşmiş vocal / drum / melody head'leri ile. Suno v5 (2026) ELO 1293 kalite lideri. Udio v4 inpainting + stem ayırma (bas, davul, vokal ayrı indirme) ekler.

### Değerlendirme

- **FAD (Fréchet Audio Distance).** VGGish ya da PANNs öznitelikleri kullanılarak üretilmiş vs gerçek ses dağılımı arasında embedding seviyesi mesafe. Daha düşük daha iyi. MusicGen small: MusicCaps'te 4.5 FAD; SOTA ~3.0.
- **Müzikalite (öznel).** İnsan tercihi. Suno v5 ELO 1293 liderdir.
- **Metin-ses hizalama.** Prompt ile çıktı arası CLAP skoru.
- **Müzikalite artefaktları.** Off-beat geçişler, vokal-cümle drift'i, 30 sn sonrası yapı kaybı.

## 2026 model haritası

| Model | Param | Uzunluk | Vokal | Lisans |
|-------|--------|--------|--------|---------|
| MusicGen-large | 3.3B | 30 sn | yok | MIT |
| Stable Audio Open | 1.2B | 47 sn | yok | Stability non-commercial |
| ACE-Step XL (Nis 2026) | 4B | &gt; 2 dk | var | Apache-2.0 |
| YuE | 7B | &gt; 2 dk | var, çok dilli | Apache-2.0 |
| Suno v5 (kapalı) | ? | 4 dk | var, ELO 1293 | ticari |
| Udio v4 (kapalı) | ? | 4 dk | var + stem | ticari |
| Google Lyria 3 (kapalı) | ? | real-time | var | ticari |
| MiniMax Music 2.5 | ? | 4 dk | var | ticari API |

## Hukuki manzara (2025-2026)

- **Warner Music vs Suno anlaşması.** $500M. WMG artık Suno'da AI benzerlik, müzik hakları ve kullanıcı-üretimi parçalar üzerinde gözetime sahip. Udio'da benzer UMG anlaşması.
- **AB AI Act** + **California SB 942**: AI tarafından üretilmiş müzik açıklanmalı.
- **MIT altındaki Riffusion / MusicGen** compliance yükü taşımaz ama ticari vokal de yok.

Güvenle-yayınlanabilir kalıplar:

1. Sadece enstrümantal üret (MusicGen, Stable Audio Open, MIT/CC0 çıktılar).
2. Per-generation lisanslı ticari API'lar kullan (Suno, Udio, ElevenLabs Music).
3. Sahip olunan ya da lisanslı katalog üzerinde eğit (çoğu kurum buraya iner).
4. Üretimleri watermark + metadata ile etiketle.

## İnşa Et

### Adım 1: MusicGen ile üret

```python
from audiocraft.models import MusicGen
import torchaudio

model = MusicGen.get_pretrained("facebook/musicgen-small")
model.set_generation_params(duration=10)
wav = model.generate(["upbeat synthwave with driving drums, 128 BPM"])
torchaudio.save("out.wav", wav[0].cpu(), 32000)
```

Üç boyut: `small` (300M, hızlı), `medium` (1.5B), `large` (3.3B). "Fikir oturuyor mu" için small yeterli.

### Adım 2: Melodi koşullaması

```python
melody, sr = torchaudio.load("humming.wav")
wav = model.generate_with_chroma(
    ["jazz piano cover"],
    melody.squeeze(),
    sr,
)
```

MusicGen-melody bir chromagram alır ve tını'yı değiştirirken melodiyi korur. "Bu melodiyi yaylı dörtlü olarak ver" için kullanışlı.

### Adım 3: FAD değerlendirme

```python
from frechet_audio_distance import FrechetAudioDistance
fad = FrechetAudioDistance()

fad.get_fad_score("generated_folder/", "reference_folder/")
```

VGGish-embedding mesafesi hesaplar. Tür seviyesi regresyon testleri için kullanışlı; insan dinleyicilerin yerini tutmaz.

### Adım 4: LLM-müzik workflow'una ekleme

Ders 7-8'deki fikirlerle birleştir:

```python
prompt = "Write a 30-second jazz loop. Describe the drums, bass, and piano voicing."
description = llm.complete(prompt)
music = musicgen.generate([description], duration=30)
```

## Kullan

| Hedef | Yığın |
|------|-------|
| Enstrümantal ses tasarımı | Stable Audio Open |
| Oyun / adaptif müzik | Google Lyria RealTime (kapalı) |
| Vokalli tam şarkı (ticari) | Açık lisansla Suno v5 ya da Udio v4 |
| Vokalli tam şarkı (açık) | ACE-Step XL ya da YuE |
| Kısa reklam jingle'ı | Mırıldanılmış referansa melodi-koşullu MusicGen |
| Müzik-video arka planı | MusicGen + Stable Video Diffusion |

## 2026'da Hâlâ Yayına Çıkan Tuzaklar

- **Telif aklama prompt'ları.** "Taylor Swift tarzında şarkı" — ticari Suno/Udio artık bunları filtreliyor, açık modeller filtrelemiyor. Kendi filtre listeni ekle.
- **30 sn sonrası tekrar / drift.** AR modeller loop yapar. Birden çok üretimi crossfade yap ya da yapısal tutarlılık için ACE-Step kullan.
- **Tempo drift'i.** Modeller BPM'den sapar. Prompt'ta BPM tag'leri kullan ve librosa'nın `beat_track`'i ile post-filter uygula.
- **Vokal anlaşılırlığı.** Suno mükemmel; açık modeller kelimelerde sıklıkla bulanıktır. Sözler önemliyse ticari API kullan ya da fine-tune et.
- **Mono çıktı.** Açık modeller mono ya da sahte-stereo üretir. Düzgün stereo reconstruction ile yükselt (ezst, Cartesia'nın stereo diffusion'ı).

## Yayınla

`outputs/skill-music-designer.md` olarak kaydet. Müzik-gen deployment'ı için model, lisans stratejisi, uzunluk / yapı planı ve disclosure metadata'sı seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. ASCII sembol olarak bir "üretken" akor ilerlemesi + davul kalıbı üretir — müzik-gen karikatürü. İstersen herhangi bir MIDI renderer üzerinden çal.
2. **Orta.** `audiocraft`'ı kur, MusicGen-small ile 4 tür prompt'unda 10 saniyelik klipler üret, referans tür setine karşı FAD ölç.
3. **Zor.** ACE-Step (ya da MusicGen-melody) kullanarak aynı melodinin farklı tını prompt'larıyla üç varyasyonunu üret. Hizalamayı doğrulamak için prompt'a CLAP benzerliği hesapla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| FAD | Ses FID'i | Gerçek vs üretilmişin embedding dağılımları arası Fréchet mesafesi. |
| Chromagram | Pitch olarak melodi | 12-boyutlu frame başına vektör; melodi koşullamasına girdi. |
| Stem'ler | Enstrüman parçaları | WAV olarak ayrılmış bas / davul / vokal / melodi. |
| Inpainting | Bir bölümü yeniden üretme | Bir zaman penceresini maskele; model sadece onu yeniden üretir. |
| CLAP | Metin-ses CLIP'i | Karşıtsal ses-metin embedding'i; metin-ses hizalamayı değerlendirir. |
| EnCodec | Müzik codec'i | MusicGen tarafından kullanılan Meta'nın nöral codec'i; 32 kHz, 4 codebook. |

## İleri Okuma

- [Copet et al. (2023). MusicGen](https://arxiv.org/abs/2306.05284) — açık autoregressive benchmark.
- [Evans et al. (2024). Stable Audio Open](https://arxiv.org/abs/2407.14358) — ses-tasarımı varsayılanı.
- [ACE-Step](https://github.com/ace-step/ACE-Step) — açık 4B tam-şarkı üreteci, Nisan 2026.
- [Suno v5 platform docs](https://suno.com) — ticari kalite lideri.
- [AudioLDM2](https://arxiv.org/abs/2308.05734) — müzik + ses efektleri için latent diffusion.
- [WMG-Suno settlement coverage](https://www.musicbusinessworldwide.com/suno-warner-music-settlement/) — Kas 2025 emsali.
