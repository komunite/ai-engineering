# Diffusion Modelleri — Sıfırdan DDPM

> Ho, Jain, Abbeel (2020) alana bıraktığı bir reçete verdi. Veriyi bin küçük adımda gürültüyle yok et. Gürültüyü tahmin etmek için tek bir sinir ağı eğit. Çıkarımda süreci tersine çevir. Bugün her ana akım görsel, video, 3D ve müzik modeli bu döngüde çalışıyor, muhtemelen üzerine flow matching ya da consistency numaralarıyla.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 · 02 (Backprop), Faz 8 · 02 (VAE)
**Süre:** ~75 dakika

## Sorun

`p_data(x)` için bir sampler istiyorsun. GAN'lar sık sık ıraksayan bir minimax oyunu oynar. VAE'ler Gaussian decoder'dan bulanık örnekler üretir. Aslında istediğin şu özelliklere sahip bir eğitim hedefi: (a) tek kararlı bir loss (saddle point yok, minimax yok), (b) `log p(x)` için bir alt sınır (likelihood'ların olsun) ve (c) SOTA kalitesinde örnekler.

Sohl-Dickstein et al. (2015) teorik bir cevap verdi: kademeli olarak Gaussian gürültü ekleyen bir Markov chain `q(x_t | x_{t-1})` tanımla ve denoise etmek için bir reverse chain `p_θ(x_{t-1} | x_t)` eğit. Ho, Jain, Abbeel (2020) loss'un tek satıra basitleştirilebileceğini gösterdi — gürültüyü tahmin et — ve matematiği temizledi. 2020'de bu bir merak konusuydu. 2021'de state-of-the-art örnekler üretti. 2022'de Stable Diffusion oldu. 2026'da alt zemin.

## Kavram

![DDPM: ileri gürültü, geri denoise](../assets/ddpm.svg)

**İleri süreç `q`.** `T` küçük adımda Gaussian gürültü ekle. Closed form — matematiğin tractable olmasının nedeni — kümülatif adımın da Gaussian olmasıdır:

```
q(x_t | x_0) = N( sqrt(α̅_t) · x_0,  (1 - α̅_t) · I )
```

burada `β_t` schedule'ı için `α̅_t = ∏_{s=1..t} (1 - β_s)`. `β_t`'yi 1e-4'ten 0.02'ye T=1000 adımda lineer seç ve `x_T` yaklaşık `N(0, I)` olur.

**Reverse süreç `p_θ`.** Eklenen gürültüyü tahmin eden bir sinir ağı `ε_θ(x_t, t)` öğren. `x_t` verildiğinde denoise et:

```
x_{t-1} = (1 / sqrt(α_t)) · ( x_t - (β_t / sqrt(1 - α̅_t)) · ε_θ(x_t, t) )  +  σ_t · z
```

burada `σ_t` ya `sqrt(β_t)` ya da öğrenilmiş bir varyans. İfade çirkin ama sadece cebir — posterior `q(x_{t-1} | x_t, x_0)` verildiğinde `x_{t-1}` için çözmek ve `x_0`'ı gürültü-tahminli tahminiyle yerine koymak.

**Eğitim loss'u.**

```
L_simple = E_{x_0, t, ε} [ || ε - ε_θ( sqrt(α̅_t) · x_0 + sqrt(1 - α̅_t) · ε,  t ) ||² ]
```

Veriden `x_0` örnekle, rastgele bir `t` seç, `ε ~ N(0, I)` örnekle, closed form ile tek atışta gürültülü `x_t`'yi hesapla ve gürültü üzerine regress et. Tek loss, minimax yok, KL yok, reparameterization numarası yok.

**Sampling.** `x_T ~ N(0, I)`'dan başla. Reverse adımı `t = T`'den `1`'e iterate et. Tamam.

## Neden çalışır

Üç sezgi:

1. **Denoising kolay; üretim zor.** `t=T`'de veri saf gürültü — ağın çözmesi gereken trivial bir problem var. `t=0`'da ağın birkaç pikseli temizlemesi gerek. Ara `t`'lerde problem zor ama ağ her gürültü seviyesinden aynı ağırlıklara akan birçok gradyana sahip.

2. **Kılık değiştirmiş score matching.** Vincent (2011) gürültüyü tahmin etmenin `∇_x log q(x_t | x_0)`'yi, yani *score*'u tahmin etmekle eşdeğer olduğunu kanıtladı. Reverse SDE yoğunluk gradyanı yukarı yürümek için bu score'u kullanır — yüksek olasılıklı bölgelere doğru rehberli rastgele yürüyüş.

3. **ELBO basit MSE'ye düşer.** Tam variational lower bound timestep başına bir KL terimine sahiptir. DDPM'in parameterization'ı ile bu KL terimleri belirli katsayılarla gürültü tahmininde MSE'ye basitleşir; Ho katsayıları attı ("simple" loss olarak adlandırdı) ve kalite *arttı*.

## İnşa Et

`code/main.py` 1-D bir DDPM uygular. Veri iki-modlu bir karışım. "Net" `(x_t, t)` alıp tahmini gürültü çıkaran minik bir MLP. Eğitim tek satırlık loss. Sampling reverse chain'i iterate eder.

### Adım 1: ileri schedule (closed form)

```python
betas = [1e-4 + (0.02 - 1e-4) * t / (T - 1) for t in range(T)]
alphas = [1 - b for b in betas]
alpha_bars = []
cum = 1.0
for a in alphas:
    cum *= a
    alpha_bars.append(cum)
```

### Adım 2: `x_t`'yi tek atışta örnekle

```python
def forward_sample(x0, t, alpha_bars, rng):
    a_bar = alpha_bars[t]
    eps = rng.gauss(0, 1)
    x_t = math.sqrt(a_bar) * x0 + math.sqrt(1 - a_bar) * eps
    return x_t, eps
```

### Adım 3: tek bir eğitim adımı

```python
def train_step(x0, model, alpha_bars, rng):
    t = rng.randrange(T)
    x_t, eps = forward_sample(x0, t, alpha_bars, rng)
    eps_hat = model_forward(model, x_t, t)
    loss = (eps - eps_hat) ** 2
    return loss, gradient_step(model, ...)
```

### Adım 4: reverse sampling

```python
def sample(model, alpha_bars, T, rng):
    x = rng.gauss(0, 1)
    for t in range(T - 1, -1, -1):
        eps_hat = model_forward(model, x, t)
        beta_t = 1 - alphas[t]
        x = (x - beta_t / math.sqrt(1 - alpha_bars[t]) * eps_hat) / math.sqrt(alphas[t])
        if t > 0:
            x += math.sqrt(beta_t) * rng.gauss(0, 1)
    return x
```

40 timestep ve 24-birim MLP'li 1-D bir problem için bu, iki-modlu karışımı ~200 epoch'ta öğrenir.

## Zaman koşullaması

Ağın hangi timestep'i denoise ettiğini bilmesi gerek. İki standart seçenek:

- **Sinusoidal embedding.** Transformer positional encoding gibi. `embed(t) = [sin(t/ω_0), cos(t/ω_0), sin(t/ω_1), ...]`. Bir MLP'den geçir, ağa broadcast et.
- **Film / group-norm koşullaması.** Her blokta kanal başına scale/bias'a projekte et (FiLM).

Oyuncak kodumuz sinusoidal → concat kullanır. Üretim U-Net'leri FiLM kullanır.

## Tuzaklar

- **Schedule çok önemli.** Linear `β` DDPM varsayılanı ama cosine schedule (Nichol & Dhariwal, 2021) aynı compute için daha iyi FID verir. Kalite plato çizerse schedule değiştir.
- **Timestep embedding kırılgan.** Ham `t`'yi float olarak geçmek oyuncak 1-D için çalışır ama görseller için başarısız olur; her zaman düzgün bir embedding kullan.
- **V-prediction vs ε-prediction.** Dar rejimler için (çok küçük ya da çok büyük t), `ε`'nın sinyal-gürültü oranı kötü. V-prediction (`v = α·ε - σ·x`) daha kararlı; SDXL, SD3 ve Flux kullanır.
- **Classifier-free guidance.** Çıkarımda hem koşullu hem koşulsuz `ε`'yı hesapla, sonra `ε_cfg = (1 + w) · ε_cond - w · ε_uncond` `w ≈ 3-7` ile. Ders 08'de işlenir.
- **1000 adım çok fazla.** Üretim DDIM (20-50 adım), DPM-Solver (10-20 adım) ya da distillation (1-4 adım) kullanır. Ders 12'ye bak.

## Kullan

| Rol | 2026'da tipik yığın |
|------|-----------------------|
| Görsel piksel-uzayı diffusion (küçük, oyuncak) | DDPM + U-Net |
| Görsel latent diffusion | VAE encoder + U-Net ya da DiT (Ders 07) |
| Video latent diffusion | Spatiotemporal DiT (Sora, Veo, WAN) |
| Ses latent diffusion | Encodec + diffusion transformer |
| Bilim (moleküller, proteinler, fizik) | Equivariant diffusion (EDM, RFdiffusion, AlphaFold3) |

Diffusion evrensel üretken omurga. Flow matching (Ders 13) aynı kalite için çıkarım hızında genellikle kazanan 2024-2026 rakibi.

## Yayınla

`outputs/skill-diffusion-trainer.md` olarak kaydet. Skill bir dataset + compute bütçesi alır ve şunu çıkarır: schedule (linear/cosine/sigmoid), prediction hedefi (ε/v/x), adım sayısı, guidance scale, sampler ailesi ve bir eval protokolü.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'de T'yi 40'tan 10'a değiştir. Örnek kalitesi (çıktıların görsel histogramı) nasıl bozulur? İki-modlu yapı hangi T'de çöker?
2. **(Orta)** ε-prediction'dan v-prediction'a geç. Reverse adımı yeniden türet. Nihai örnek kalitesini karşılaştır.
3. **(Zor)** Classifier-free guidance ekle. Bir sınıf etiketi `c ∈ {0, 1}` üzerinde koşulla, eğitim sırasında %10 oranında düşür ve sampling zamanında `ε = (1+w)·ε_cond - w·ε_uncond` kullan. Koşullu-mod-yakalama oranını `w = 0, 1, 3, 7`'de ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Forward süreç | "Gürültü ekleme" | Veriyi yok eden sabit Markov chain `q(x_t | x_{t-1})`. |
| Reverse süreç | "Denoising" | Veriyi yeniden inşa eden öğrenilmiş chain `p_θ(x_{t-1} | x_t)`. |
| β schedule | "Gürültü merdiveni" | Adım başına varyans; linear, cosine ya da sigmoid. |
| α̅ | "Alpha bar" | Kümülatif çarpım `∏(1 - β)`; `x_0`'dan closed-form `x_t` verir. |
| Simple loss | "Gürültüde MSE" | `||ε - ε_θ(x_t, t)||²`; tüm variational türetmeler buna çöker. |
| ε-prediction | "Gürültüyü tahmin et" | Çıktı eklenen gürültü; standart DDPM. |
| V-prediction | "Hızı tahmin et" | Çıktı `α·ε - σ·x`; t boyunca daha iyi koşullama. |
| DDPM | "Makale" | Ho et al. 2020; linear β, 1000 adım, U-Net. |
| DDIM | "Deterministik sampler" | Non-Markov sampler, 20-50 adım, aynı eğitim hedefi. |
| Classifier-free guidance | "CFG" | Koşullamayı güçlendirmek için koşullu ve koşulsuz gürültü tahminlerini karıştır. |

## Üretim notu: diffusion çıkarımı bir adım-sayısı problemidir

DDPM makalesi T=1000 reverse adım çalıştırır. Kimse bunu üretimde ship etmiyor. Her gerçek çıkarım yığını üç stratejiden birini seçer — ve her biri "latency nereden geliyor" üretim çerçevelemesine temiz şekilde karşılık gelir:

1. **Daha hızlı sampler, aynı model.** DDIM (20-50 adım), DPM-Solver++ (10-20), UniPC (8-16). Reverse döngüsünün drop-in değiştirilmesi; eğitilmiş `ε_θ` ağırlıkları el sürülmez. Latency'yi 20-50× keser.
2. **Distillation.** Bir öğrenciyi öğretmeni daha az adımda eşlemeye eğit: Progressive Distillation (2 → 1), Consistency Models (keyfi → 1-4), LCM, SDXL-Turbo, SD3-Turbo. Latency'yi başka 5-10× keser, yeniden eğitim gerektirir.
3. **Caching ve derleme.** `torch.compile(unet, mode="reduce-overhead")`, TensorRT-LLM'in diffusion backend'leri, `xformers`/SDPA attention, bf16 ağırlıklar. Adım başına latency'yi ~2× keser. (1) ve (2) ile yığılır.

Bir üretim diffusion sunucusu için bütçe konuşması, üretim literatürünün LLM'ler için tarif ettiğiyle aynıdır: latency `num_steps × step_cost + VAE_decode`, throughput `batch_size × (num_steps × step_cost)^-1`. TTFT küçük (bir adım); TPOT eşdeğeri tam yanıt süresi çünkü görsel üretimi kullanıcının perspektifinden "her şey bir anda".

## İleri Okuma

- [Sohl-Dickstein et al. (2015). Deep Unsupervised Learning using Nonequilibrium Thermodynamics](https://arxiv.org/abs/1503.03585) — diffusion makalesi, zamanının ötesinde.
- [Ho, Jain, Abbeel (2020). Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) — DDPM.
- [Song, Meng, Ermon (2021). Denoising Diffusion Implicit Models](https://arxiv.org/abs/2010.02502) — DDIM, daha az adım.
- [Nichol & Dhariwal (2021). Improved DDPM](https://arxiv.org/abs/2102.09672) — cosine schedule, öğrenilmiş varyans.
- [Dhariwal & Nichol (2021). Diffusion Models Beat GANs on Image Synthesis](https://arxiv.org/abs/2105.05233) — classifier guidance.
- [Ho & Salimans (2022). Classifier-Free Diffusion Guidance](https://arxiv.org/abs/2207.12598) — CFG.
- [Karras et al. (2022). Elucidating the Design Space of Diffusion-Based Generative Models (EDM)](https://arxiv.org/abs/2206.00364) — birleşik notasyon, en temiz reçete.
