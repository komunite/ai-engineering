# Latent Diffusion ve Stable Diffusion

> 512×512 görseller üzerinde piksel-uzayı diffusion'ı bir hesaplama savaş suçudur. Rombach et al. (2022) bir görseli üretmek için 786k boyutun hepsine ihtiyacın olmadığını fark etti — semantik yapıyı yakalayacak kadarına ve geri kalan için ayrı bir decoder'a ihtiyacın var. Diffusion'ı bir VAE'nin latent uzayında çalıştır. O tek fikir Stable Diffusion.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 02 (VAE), Faz 8 · 06 (DDPM), Faz 7 · 09 (ViT)
**Süre:** ~75 dakika

## Sorun

512²'de piksel-uzayı diffusion'ı, U-Net'in `[B, 3, 512, 512]` şeklinde tensörler üzerinde çalışması demektir. Her sampling adımı 500M-param bir U-Net için ~100 GFLOPS. Elli adım görsel başına 5 TFLOPS. Bir milyar görsel üzerinde eğit ve compute faturası saçma.

O FLOPs'ların çoğu, kayıplı bir VAE'nin sıkıştırabileceği yüksek-frekanslı texture'ı — algısal olarak önemsiz detayları — ağdan geçirmeye gider. Rombach'ın fikri: bir VAE'yi bir kez eğit (*birinci aşama*), dondur ve diffusion'ı tamamen 4 kanallı 64×64 latent uzayında (*ikinci aşama*) çalıştır. Aynı U-Net. 1/16'sı kadar piksel. Karşılaştırılabilir kalite için ~64x daha az FLOPs.

Stable Diffusion reçetesi bu. SD 1.x / 2.x `64×64×4` latent'ler üzerinde 860M U-Net, SDXL `128×128×4` üzerinde 2.6B U-Net, SD3 U-Net'i flow matching'li bir Diffusion Transformer (DiT) ile değiştirdi. Flux.1-dev (Black Forest Labs, 2024) 12B-param DiT-MMDiT ship eder. Hepsi aynı iki-aşama alt zemininde çalışır.

## Kavram

![Latent diffusion: VAE sıkıştırması + latent uzayda diffusion](../assets/latent-diffusion.svg)

**İki aşama, ayrı eğitilir.**

1. **Aşama 1 — VAE.** Encoder `E(x) → z`, decoder `D(z) → x`. Hedef sıkıştırma: her uzamsal eksende 8× downsample + toplam latent boyutu piksel sayısının ~1/16'sı olacak şekilde kanalları ayarla. Loss = reconstruction (L1 + LPIPS perceptual) + KL (küçük ağırlık böylece `z` çok Gaussian olmaya zorlanmaz, çünkü `z`'den tam örneklemeye ihtiyacımız yok). Genelde decode edilen görseller keskin olsun diye adversarial loss ile eğitilir.

2. **Aşama 2 — `z` üzerinde diffusion.** `z = E(x_real)`'i veri olarak ele al. `z_t`'yi denoise etmek için bir U-Net (ya da DiT) eğit. Çıkarımda: `z_0`'ı diffusion ile örnekle, sonra `x = D(z_0)`.

**Metin koşullaması.** İki ek bileşen. Bir dondurulmuş metin encoder'ı (SD 1.x için CLIP-L, SD 2/XL için CLIP-L+OpenCLIP-G, SD3 ve Flux için T5-XXL). Bir cross-attention enjeksiyonu: her U-Net bloğu `[Q = görsel özellikleri, K = V = metin token'ları]` alır ve karıştırır. Metnin görseli etkileyebileceği tek yol token'lar.

**Loss fonksiyonu Ders 06 ile birebir aynı.** Gürültü üzerinde aynı DDPM / flow matching MSE. Sadece veri alanını değiştiriyorsun.

## Mimari varyantları

| Model | Yıl | Omurga | Latent şekli | Metin encoder | Parametre |
|-------|------|----------|--------------|--------------|--------|
| SD 1.5 | 2022 | U-Net | 64×64×4 | CLIP-L (77 token) | 860M |
| SD 2.1 | 2022 | U-Net | 64×64×4 | OpenCLIP-H | 865M |
| SDXL | 2023 | U-Net + refiner | 128×128×4 | CLIP-L + OpenCLIP-G | 2.6B + 6.6B |
| SDXL-Turbo | 2023 | Distillation'lı | 128×128×4 | aynı | 1-4 adım örnekleme |
| SD3 | 2024 | MMDiT (multimodal DiT) | 128×128×16 | T5-XXL + CLIP-L + CLIP-G | 2B / 8B |
| Flux.1-dev | 2024 | MMDiT | 128×128×16 | T5-XXL + CLIP-L | 12B |
| Flux.1-schnell | 2024 | MMDiT distilled | 128×128×16 | T5-XXL + CLIP-L | 12B, 1-4 adım |

Trend: U-Net'i DiT (latent patch'ler üzerinde transformer) ile değiştir, metin encoder'ı ölçeklendir (T5 prompt sadakatinde CLIP'i geçer), latent kanallarını arttır (4 → 16 daha fazla detay tavanı verir).

## İnşa Et

`code/main.py` Ders 06'daki DDPM'nin üstüne oyuncak bir 1-D "VAE" (gösterim için identity encoder + decoder; gerçek bir VAE bir conv ağı olurdu) bindirir ve classifier-free guidance ile sınıf koşullaması ekler. Aynı diffusion loss'unun ister ham 1-D değerleri ister encode edilmiş değerler üzerinde çalıştığını gösterir — anahtar içgörü.

### Adım 1: encoder/decoder

```python
def encode(x):    return x * 0.5          # daha küçük ölçeğe oyuncak "sıkıştırma"
def decode(z):    return z * 2.0
```

Gerçek bir VAE'nin eğitilmiş ağırlıkları var. Pedagoji için, bu lineer eşleme diffusion'ın orijinal veri uzayını umursamadan `z` üzerinde çalıştığını göstermek için yeterli.

### Adım 2: `z`-uzayında diffusion

Ders 06 ile aynı DDPM. Ağın gördüğü veri `z = E(x)`. `z_0`'ı örnekledikten sonra `D(z_0)` ile decode et.

### Adım 3: classifier-free guidance

Eğitim sırasında sınıf etiketini %10 oranında düşür (null token ile değiştir). Çıkarımda hem `ε_cond` hem `ε_uncond`'u hesapla, sonra:

```python
eps_cfg = (1 + w) * eps_cond - w * eps_uncond
```

`w = 0` = guidance yok (tam çeşitlilik), `w = 3` = varsayılan, `w = 7+` = doygun / aşırı keskin.

### Adım 4: metin koşullaması (kavram, kod değil)

Sınıf etiketini dondurulmuş bir metin encoder çıktısıyla değiştir. Metin embedding'ini U-Net'e cross-attention ile besle:

```python
h = h + CrossAttention(Q=h, K=text_embed, V=text_embed)
```

Bu, sınıf-koşullu bir diffusion modeliyle Stable Diffusion arasındaki tek önemli fark.

## Tuzaklar

- **VAE-ölçek uyumsuzluğu.** SD 1.x VAE'lerinin encoding'den sonra uygulanan bir ölçekleme sabiti (`scaling_factor ≈ 0.18215`) var. Bunu unutmak U-Net'i çılgınca yanlış varyansa sahip latent'lerde eğitir. Her checkpoint birini ship eder.
- **Metin encoder'ı sessizce yanlış.** SD3 >=128 token'lı T5-XXL gerektirir ve CLIP-only fallback kayıplıdır. Her zaman `use_t5=True` kontrol et yoksa prompt sadakati çöker.
- **Latent uzayları karıştırma.** SDXL, SD3, Flux farklı VAE'ler kullanır. SDXL latent'leri üzerinde eğitilmiş bir LoRA SD3'te çalışmaz. Hugging Face diffusers 0.30+ uyumsuz checkpoint'leri yüklemeyi reddeder.
- **CFG çok yüksek.** `w > 10` doygun, yağlı görseller üretir ve çeşitlilik pahasına prompt'a aşırı uyar. Tatlı nokta `w = 3-7`.
- **Negative prompt sızıntısı.** Boş negative prompt null token olur; dolu bir negative prompt `ε_uncond` olur. Bunlar aynı değil; bazı pipeline'lar sessizce null'a varsayılan.

## Kullan

2026'da üretim yığınları:

| Hedef | Önerilen omurga |
|--------|----------------------|
| Dar alan, eşli veri, sıfırdan model eğitimi | SDXL fine-tune (LoRA / tam) — en hızlı ship |
| Açık-alan text-to-image, açık ağırlıklar | Flux.1-dev (12B, Apache / ticari olmayan) ya da SD3.5-Large |
| En hızlı çıkarım, açık ağırlıklar | Flux.1-schnell (1-4 adım, Apache) ya da SDXL-Lightning |
| En iyi prompt sadakati, hosted | GPT-Image / DALL-E 3 (hâlâ), Midjourney v7, Imagen 4 |
| Düzenleme akışları | Flux.1-Kontext (Ara 2024) — yerel olarak görsel + metin kabul eder |
| Araştırma, baseline | SD 1.5 — antik ama iyi çalışılmış |

## Yayınla

`outputs/skill-sd-prompter.md` olarak kaydet. Skill bir metin prompt + hedef stil alır ve şunu çıkarır: model + checkpoint, CFG scale, sampler, negative prompt, çözünürlük, opsiyonel ControlNet/IP-Adapter kombo ve adım başına QA checklist.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi guidance `w ∈ {0, 1, 3, 7, 15}` ile çalıştır. Sınıf başına ortalama örneği kaydet. Hangi `w`'de sınıf ortalamaları gerçek veri ortalamalarını geçecek şekilde ıraksar?
2. **(Orta)** Oyuncak lineer encoder'ı reconstruction loss'lu bir tanh-MLP encoder/decoder çiftiyle değiştir. Yeni latent'ler üzerinde diffusion'ı yeniden eğit. Örnek kalitesi değişir mi?
3. **(Zor)** diffusers ile gerçek bir Stable Diffusion çıkarımı kur: `sdxl-base` yükle, CFG=7 ile 30 Euler adım çalıştır, süreyi ölç. Şimdi `sdxl-turbo`'ya 4 adım ve CFG=0 ile geç. Aynı konu, farklı kalite — neyin değiştiğini ve nedenini tarif et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Birinci aşama | "VAE" | Eğitilmiş encoder/decoder çifti; 512²'yi 64²'ye sıkıştırır. |
| İkinci aşama | "U-Net" | Latent uzay üzerinde diffusion modeli. |
| CFG | "Guidance scale" | `(1+w)·ε_cond - w·ε_uncond`; koşullama gücünü ayarlar. |
| Null token | "Boş prompt embed" | `ε_uncond` için kullanılan koşulsuz embed. |
| Cross-attention | "Metin nasıl girer" | Her U-Net bloğu metin token'larına K ve V olarak attend eder. |
| DiT | "Diffusion Transformer" | U-Net'i latent patch'ler üzerinde bir transformer ile değiştir; daha iyi ölçeklenir. |
| MMDiT | "Multi-modal DiT" | SD3'ün mimarisi: ortak attention'lı metin ve görsel akışları. |
| VAE scaling factor | "Sihirli sayı" | Latent'leri ~5.4'e böler böylece diffusion birim-varyans uzayında çalışır. |

## Üretim notu: 8GB tüketici GPU'da Flux-12B çalıştırma

Referans Flux entegrasyonu kanonik "tüketici GPU'm var, bunu ship edebilir miyim?" reçetesi. Numara üretim çıkarım literatürünün listelediği aynı üç-düğme reçetesinin bir diffusion DiT'ye uygulanması:

1. **Kademeli yükleme.** Flux'ın VRAM'de hiç birlikte var olmayan üç ağı vardır: T5-XXL metin encoder (fp32'de ~10 GB), CLIP-L (küçük), 12B MMDiT ve VAE. Önce prompt'u encode et, encoder'ları *sil*, DiT'yi yükle, denoise et, DiT'yi *sil*, VAE'yi yükle, decode et. Tüketici 8GB GPU'lar bir kerede sadece bir aşamaya sığar.
2. **bitsandbytes ile 4-bit quantization.** Hem T5 encoder hem DiT üzerinde `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)`. Belleği 8× keser, Aritra'nın benchmark'larına göre (notebook'a bağlı) text-to-image için kalite düşüşü algılanamaz.
3. **CPU offload.** `pipe.enable_model_cpu_offload()` her forward pass ilerledikçe modülleri CPU ile GPU arasında otomatik takas eder. %10-20 latency ekler ama pipeline'ın hiç çalışmasını sağlar.

Bellek muhasebesi: `10 GB T5 / 8 = 1.25 GB` quantize, `12 B param × 0.5 bayt = ~6 GB` quantize DiT, artı aktivasyonlar. Stas00'un terimleriyle bu, TP=1 çıkarımın aşırı ucu — model parallelism yok, maksimum quantization. Üretim için H100'lerde TP=2 ya da TP=4 çalıştırırdın; tek bir dev laptop için reçete bu.

## İleri Okuma

- [Rombach et al. (2022). High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion.
- [Podell et al. (2023). SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis](https://arxiv.org/abs/2307.01952) — SDXL.
- [Peebles & Xie (2023). Scalable Diffusion Models with Transformers (DiT)](https://arxiv.org/abs/2212.09748) — DiT.
- [Esser et al. (2024). Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206) — SD3, MMDiT.
- [Ho & Salimans (2022). Classifier-Free Diffusion Guidance](https://arxiv.org/abs/2207.12598) — CFG.
- [Labs (2024). Flux.1 — Black Forest Labs duyurusu](https://blackforestlabs.ai/announcing-black-forest-labs/) — Flux.1 ailesi.
- [Hugging Face Diffusers docs](https://huggingface.co/docs/diffusers/index) — yukarıdaki her checkpoint için referans uygulama.
