# Video Üretimi

> Görsel 2-D bir tensör. Video 3-D bir. Teori aynı; compute 10-100x daha zor. OpenAI'nın Sora'sı (Şub 2024) bunun mümkün olduğunu kanıtladı. 2026'ya gelindiğinde Veo 2, Kling 1.5, Runway Gen-3, Pika 2.0 ve WAN 2.2 metinden 1080p üretim videosu ship ediyor — ve açık ağırlık yığını (CogVideoX, HunyuanVideo, Mochi-1, WAN 2.2) 12 ay arkada.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 07 (Latent Diffusion), Faz 7 · 09 (ViT), Faz 8 · 06 (DDPM)
**Süre:** ~45 dakika

## Sorun

24fps'te 10 saniyelik 1080p bir video 240 kare × 1920×1080×3 piksel. Klip başına ~1.5 GB ham veri. Piksel-uzayı diffusion olanaksız. Şunlara ihtiyacın var:

1. **Spatiotemporal sıkıştırma.** Videoları kareler olarak değil, uzamsal-zamansal patch dizileri olarak encode eden bir VAE.
2. **Zamansal tutarlılık.** Kareler içerik, aydınlatma ve nesne kimliğini saniyeler boyunca paylaşmalı. Ağ hareketi modellemeli.
3. **Compute bütçesi.** Video eğitimi aynı model boyutu için görselden 10-100x daha pahalı.
4. **Koşullama.** Metin, görsel (ilk kare), ses ya da başka bir video. Çoğu üretim modeli dördünü de kabul eder.

Bunu çözen mimari spatiotemporal patch'lere uygulanan, devasa (prompt, caption, video) dataset'lerinde eğitilmiş **Diffusion Transformer (DiT)**. Ders 06 ile aynı diffusion loss'u.

## Kavram

![Video diffusion: patchify, DiT, decode](../assets/video-generation.svg)

### Patchify

Videoyu bir 3D VAE (öğrenilmiş spatiotemporal sıkıştırma) ile encode et. Latent şekli `[T_latent, H_latent, W_latent, C_latent]`. `[t_p, h_p, w_p]` boyutunda patch'lere böl. Sora tarzı modeller için `t_p = 1` (kare başına patch) ya da `t_p = 2` (her iki karede bir). 10 saniyelik 1080p bir video ~20,000-100,000 patch'e sıkışır.

### Spatiotemporal DiT

Bir transformer düz patch dizisini işler. Her patch'in 3D positional embedding'i (zaman + y + x) var. Attention genelde faktörize:

- **Spatial attention** her karenin patch'leri içinde.
- **Temporal attention** aynı uzamsal konumda kareler arasında.
- **Tam 3D attention** 16-100x daha pahalı; sadece düşük çözünürlükte ya da araştırmada kullanılır.

### Metin koşullaması

Büyük bir metin encoder'ı ile cross-attention (Sora için T5-XXL, CogVideoX-5B T5-XXL kullanır). Uzun prompt'lar önemli — Sora'nın eğitim seti klip başına ortalama 200 token'lık GPT-üretimi yoğun yeniden-caption'lara sahipti.

### Eğitim

Spatiotemporal latent'ler üzerinde standart diffusion loss'u (ε ya da v prediction). Veri: web videosu + ~100M küratörlü klip + sentetik metin caption'ları. Compute: küçük bir araştırma koşusu için bile 10,000+ GPU saati; Sora ölçeği 100,000+.

## 2026 üretim manzarası

| Model | Tarih | Maks süre | Maks çözünürlük | Açık ağırlık? | Dikkat çeken |
|-------|------|--------------|---------|---------------|---------|
| Sora (OpenAI) | 2024-02 | 60sn | 1080p | Hayır | Ölçekte dünya simülatörü özelliklerini gösteren ilk model |
| Sora Turbo | 2024-12 | 20sn | 1080p | Hayır | 5x daha hızlı çıkarımla üretim Sora'sı |
| Veo 2 (Google) | 2024-12 | 8sn | 4K | Hayır | 2025'te en yüksek kalite + fizik |
| Veo 3 | 2025 Q3 | 15sn | 4K | Hayır | Yerel ses ve daha güçlü kamera kontrolü |
| Kling 1.5 / 2.1 (Kuaishou) | 2024-2025 | 10sn | 1080p | Hayır | 2025 Q1'de en iyi insan hareketi |
| Runway Gen-3 Alpha | 2024-06 | 10sn | 768p | Hayır | Üzerinde profesyonel video araçları |
| Pika 2.0 | 2024-10 | 5sn | 1080p | Hayır | En güçlü karakter tutarlılığı |
| CogVideoX (THUDM) | 2024 | 10sn | 720p | Evet (2B, 5B) | İlk açık 5B ölçekli video |
| HunyuanVideo (Tencent) | 2024-12 | 5sn | 720p | Evet (13B) | 2024 sonu açık SOTA |
| Mochi-1 (Genmo) | 2024-10 | 5.4sn | 480p | Evet (10B) | En izin verici lisansa sahip |
| WAN 2.2 (Alibaba) | 2025-07 | 5sn | 720p | Evet | 2025 ortası en güçlü açık model |

Açık ağırlıklar görsel uzayına göre farkı daha hızlı kapatıyor: HunyuanVideo + WAN 2.2 LoRA'ları 2026 ortasına kadar çoğu açık kaynak workflow'unu zaten çalıştırıyor.

## İnşa Et

`code/main.py` temel spatiotemporal DiT fikrini simüle eder: küçük bir sentetik videoyu patch'le, patch başına bir position embedding ekle ve tüm diziyi patch'ler üzerinde transformer tarzı attention ile denoise et. Numpy yok; saf Python. Komşu-kare patch'leri bir denoiser'ı ve position embedding'leri paylaştığında zamansal tutarlılığın 1-D'de bile ortaya çıktığını gösteriyoruz.

### Adım 1: sentetik 1-D bir "videoyu" patch'le

```python
def make_video(T_frames=8, rng=None):
    # bir "video" pürüzsüz bir yörüngeyi takip eden 1-D değerler dizisi
    base = rng.gauss(0, 1)
    return [base + 0.3 * t + rng.gauss(0, 0.1) for t in range(T_frames)]
```

### Adım 2: kare başına position embedding

```python
def pos_embed(t, dim):
    return sinusoidal(t, dim)
```

### Adım 3: denoiser tüm diziyi görür

Her kareyi bağımsız denoise etmek yerine, minik ağımız tüm kare değerlerini + position embedding'lerini concatenate eder ve tüm kareler için gürültüyü ortak tahmin eder.

### Adım 4: zamansal tutarlılık testi

Eğitimden sonra bir video örnekle. Kare-kareye delta'yı ölç. Model zamansal yapı öğrendiyse, delta'lar her kareyi bağımsız örneklemekten daha küçük kalır.

## Tuzaklar

- **Bağımsız kare başına sampling = titreme.** Görsel diffusion'ı her karede ayrı ayrı çalıştırırsan çıktı titrer çünkü her karenin gürültüsü bağımsızdır. Video diffusion bunu kareleri attention ya da paylaşımlı gürültü aracılığıyla bağlayarak düzeltir.
- **Naif 3D attention = OOM.** 10 saniyelik 1080p bir latent üzerinde tam 3D attention yüz milyarlarca operasyon. Spatial + temporal'a faktörize et.
- **Veri caption'laması boyuttan daha önemli.** Sora'nın önceki çalışmalara göre ana yükseltmesi ~10x daha detaylı caption'larda (GPT-4 yeniden-etiketlenmiş klipler) eğitimdi. OpenAI'nın teknik raporu bunda açık.
- **İlk-kare koşullaması.** Çoğu üretim modeli ilk kare olarak bir görseli de kabul eder. Bu "image-to-video" modu; eğitim bu varyantı içerir.
- **Fizik kayması.** Uzun klipler (>10sn) ince tutarsızlıklar biriktirir. Kayan-pencere üretimi + keyframe anchor'lama yardımcı olur.

## Kullan

| Kullanım durumu | 2026 seçimi |
|----------|-----------|
| En yüksek kalitede text-to-video, hosted | Veo 3 ya da Sora |
| Kamera kontrollü sinematik | Motion brush'lu Runway Gen-3 |
| Klipler arası karakter tutarlılığı | Pika 2.0 ya da Kling 2.1 |
| Açık ağırlıklar, hızlı fine-tune | WAN 2.2 + LoRA |
| Image-to-video | WAN 2.2-I2V, Kling 2.1 I2V ya da Runway |
| Audio-to-video lip sync | Veo 3 (yerel ses) ya da özel lip-sync modeli |
| Video düzenleme | Runway Act-Two, Kling Motion Brush, Flux-Kontext (sabit kare) |

Kalite paritesinde video saniyesi başına maliyet 2024 ile 2026 arasında 20x düştü.

## Yayınla

`outputs/skill-video-brief.md` olarak kaydet. Skill bir video brief'i (süre, en boy oranı, stil, kamera planı, özne tutarlılığı, ses) alır ve şunu çıkarır: model + hosting, prompt iskelesi (kamera dili, özne tanımı, hareket tanımlayıcıları), seed + yeniden üretilebilirlik protokolü ve kare-seviyesi QA checklist.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'de (a) bağımsız kare başına sampling, (b) ortak dizi sampling için kare-kareye delta'yı karşılaştır. Delta'ların ortalamasını ve varyansını raporla.
2. **(Orta)** Bir ilk-kare koşulu ekle: 0. kareyi verilen bir değere sabitle ve geri kalanını örnekle. Sabitlenen değerin nasıl yayıldığını ölç.
3. **(Zor)** Yerel bir GPU'da CogVideoX-2B'yi çalıştırmak için HuggingFace diffusers kullan. 6 saniyelik bir klip için 720p'de 20 çıkarım adımını ölç. Darboğazı belirlemek için spatiotemporal attention'ı profil et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Video VAE | "3-D VAE" | `(T, H, W, C)` → spatiotemporal latent sıkıştıran encoder. |
| Patch'ler | "Token'lar" | Latent'in sabit boyutlu 3-D blokları; DiT'ye girdi. |
| Faktörize attention | "Spatial + temporal" | Önce uzay üzerinde attention, sonra zaman üzerinde; tam 3-D attention'ı atla. |
| Image-to-video (I2V) | "Bu fotoğrafı canlandır" | Model bir görsel + metin alır, ondan başlayan bir video çıkarır. |
| Keyframe koşullama | "Anchor kareleri" | Videonun yayını kontrol etmek için belirli kareleri sabitle. |
| Motion brush | "Yönlü ipucu" | Kullanıcının hareket vektörlerini görsele boyadığı UI girdisi. |
| Yeniden caption'lama | "Yoğun caption'lar" | Eğitim kliplerini detaylı prompt'larla yeniden etiketlemek için LLM kullanma. |
| Titreme | "Zamansal artefakt" | Kare-kareye tutarsızlık; bağlı denoising ile düzeltilir. |

## Üretim notu: video latent'leri bir bellek-bant genişliği problemidir

24 fps'te 10 saniyelik bir 1080p klip 240 kare × 1920 × 1080 × 3 ≈ 1.5 GB ham piksel. 4× bir video VAE sıkıştırması sonrasında (`2 × spatial × 2 × temporal`) latent istek başına ~100 MB. Bunu batch 1'de 30 adım boyunca bir spatiotemporal DiT'den geçir ve adım başına ~3 GB HBM'den taşıyorsun — darboğaz FLOP'lar değil, bellek bant genişliği.

Üç üretim düğmesi, hepsi üretim-çıkarım literatürü çıkarım bölümünden:

- **DiT boyunca TP.** Text-to-video modelleri rutin olarak ≥10B param. 4 H100 boyunca TP=4 standart; 405B sınıfı modeller için PP=2 × TP=2. Adım başına latency, all-reduce duvarına kadar TP ile kabaca lineer düşer.
- **Frame batching = sürekli batching.** Üretim zamanında video kavramsal olarak attention ile bağlı bir kare batch'i. Sürekli batching (in-flight scheduling) uygulanır: model mimarisi kayan-pencere üretimine izin veriyorsa, kare `t-1` döndürülürken kare `t+1`'i render etmeye başla.
- **Klip-seviyesi prefill cache.** Image-to-video için ilk-kare koşullaması bir LLM'in prompt prefill'ine analogdur: bir kez hesapla, zamansal decoder pass'leri arasında yeniden kullan. Bu etkili olarak video için bir KV-cache.

## İleri Okuma

- [Brooks et al. (2024). Video generation models as world simulators](https://openai.com/index/video-generation-models-as-world-simulators/) — Sora teknik raporu.
- [Yang et al. (2024). CogVideoX: Text-to-Video Diffusion Models with An Expert Transformer](https://arxiv.org/abs/2408.06072) — CogVideoX.
- [Kong et al. (2024). HunyuanVideo: A Systematic Framework for Large Video Generative Models](https://arxiv.org/abs/2412.03603) — HunyuanVideo.
- [Genmo (2024). Mochi-1 Technical Report](https://www.genmo.ai/blog/mochi) — Mochi-1.
- [Alibaba (2025). WAN 2.2](https://wanvideo.io/) — 2025 ortası açık SOTA.
- [Ho, Salimans, Gritsenko et al. (2022). Video Diffusion Models](https://arxiv.org/abs/2204.03458) — yapı taşı video diffusion makalesi.
- [Blattmann et al. (2023). Align your Latents (Video LDM)](https://arxiv.org/abs/2304.08818) — Stable Video Diffusion'ın atası.
