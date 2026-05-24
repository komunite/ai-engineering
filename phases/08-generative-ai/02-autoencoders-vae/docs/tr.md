# Autoencoder'lar ve Variational Autoencoder'lar (VAE)

> Düz bir autoencoder sıkıştırır sonra yeniden inşa eder. Ezberler. Üretmez. Tek bir numara ekle — kodun Gaussian görünmesini zorla — ve bir sampler elde edersin. O tek numara, `z = μ + σ·ε`'nın reparameterization'ı, 2026'da kullandığın her latent-diffusion ve flow-matching görsel modelinin girdisinde bir VAE olmasının nedenidir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 · 02 (Backprop), Faz 3 · 07 (CNN'ler), Faz 8 · 01 (Taksonomi)
**Süre:** ~75 dakika

## Sorun

784 piksellik bir MNIST rakamını 16 sayılık bir koda sıkıştır, sonra yeniden inşa et. Düz bir autoencoder reconstruction MSE'yi parlatır ama kod uzayı yumru yumru bir dağınıklıktır. Kod uzayında rastgele bir nokta seç, decode et, gürültü alırsın. Sampler'ı yok. Şık giyinmiş bir sıkıştırma modelidir.

Aslında istediğin: (a) kod uzayı örnekleyebileceğin temiz, pürüzsüz bir dağılım olsun — örneğin izotropik bir Gaussian `N(0, I)`, (b) herhangi bir örneğin decode'u akla yatkın bir rakam üretsin, ve (c) encoder ile decoder hâlâ iyi sıkıştırsın. Üç hedef, tek mimari, tek loss.

Kingma'nın 2013 VAE'si bunu encoder'ı bir *dağılım* `q(z|x) = N(μ(x), σ(x)²)` çıkarmaya eğiterek, bu dağılımı bir KL cezasıyla `N(0, I)` prior'una çekerek ve decode etmeden önce `z`'yi `q(z|x)`'ten örnekleyerek çözer. Çıkarım zamanında, encoder'ı at, `z ~ N(0, I)` örnekle, decode et. KL cezası, kod uzayını yapılı olmaya zorlayan şeydir.

2026'da VAE'ler ham görsel kalitede diffusion'a yenildiğinden tek başına nadiren ship edilir — ama her latent-diffusion modelinin (SD 1/2/XL/3, Flux, AudioCraft) tercih ettiği encoder'dır. VAE'yi öğren, kullandığın her görsel pipeline'ının görünmez ilk katmanını öğrenmiş olursun.

## Kavram

![Autoencoder vs VAE: reparameterization trick](../assets/vae.svg)

**Autoencoder.** `z = encoder(x)`, `x̂ = decoder(z)`, loss = `||x - x̂||²`. Kod uzayı yapısız.

**VAE encoder.** İki vektör çıkarır: `μ(x)` ve `log σ²(x)`. Bunlar `q(z|x) = N(μ, diag(σ²))` tanımlar.

**Reparameterization trick.** `q(z|x)`'ten örnekleme türevlenebilir değildir. Örneği `z = μ + σ·ε` olarak yeniden yaz, burada `ε ~ N(0, I)`. Şimdi `z`, `(μ, σ)`'nın deterministik bir fonksiyonu artı parametre olmayan bir gürültü — gradyanlar `μ` ve `σ` üzerinden akar.

**Loss.** Evidence Lower BOund (ELBO), iki terim:

```
loss = reconstruction + β · KL[q(z|x) || N(0, I)]
     = ||x - x̂||²  + β · Σ_i ( σ_i² + μ_i² - log σ_i² - 1 ) / 2
```

Reconstruction `x̂`'yi `x`'e doğru iter. KL `q(z|x)`'i prior'a doğru iter. Trade-off yaparlar. Küçük β (<1) = daha keskin örnekler, kod uzayı daha az Gaussian. Büyük β (>1) = daha temiz kod uzayı, daha bulanık örnekler. β-VAE (Higgins 2017) bu düğmeyi meşhur etti ve disentanglement araştırmasını başlattı.

**Sampling.** Çıkarımda: `z ~ N(0, I)` çek, decoder'dan ileri geçir. Tek forward pass — diffusion gibi iteratif örnekleme yok.

## İnşa Et

`code/main.py` numpy ya da torch olmadan minik bir VAE uygular. Girdi, 8-D'de 2 bileşenli Gaussian karışımından çekilmiş 8 boyutlu sentetik veri. Encoder ve decoder tek gizli katmanlı MLP'ler. tanh aktivasyonu, forward pass, loss ve elle yazılmış bir backward pass uyguluyoruz. Üretim değil — pedagoji.

### Adım 1: encoder forward

```python
def encode(x, enc):
    h = tanh(add(matmul(enc["W1"], x), enc["b1"]))
    mu = add(matmul(enc["W_mu"], h), enc["b_mu"])
    log_sigma2 = add(matmul(enc["W_sig"], h), enc["b_sig"])
    return mu, log_sigma2
```

`σ` yerine `log σ²` — böylece ağ çıkışı kısıtsız olur (σ'nın softplus'ı tuzaktır — gradyanlar σ ≈ 0'da ölür).

### Adım 2: reparameterize ve decode

```python
def reparameterize(mu, log_sigma2, rng):
    eps = [rng.gauss(0, 1) for _ in mu]
    sigma = [math.exp(0.5 * lv) for lv in log_sigma2]
    return [m + s * e for m, s, e in zip(mu, sigma, eps)]

def decode(z, dec):
    h = tanh(add(matmul(dec["W1"], z), dec["b1"]))
    return add(matmul(dec["W_out"], h), dec["b_out"])
```

### Adım 3: ELBO

```python
def elbo(x, x_hat, mu, log_sigma2, beta=1.0):
    recon = sum((a - b) ** 2 for a, b in zip(x, x_hat))
    kl = 0.5 * sum(math.exp(lv) + m * m - lv - 1 for m, lv in zip(mu, log_sigma2))
    return recon + beta * kl, recon, kl
```

Her iki dağılım da Gaussian olduğu için tam closed-form KL. Sayısal entegre etme. 2026'da hâlâ monte-carlo KL tahminleriyle kod gönderen insanlar var — sebepsiz 3x daha yavaş.

### Adım 4: üret

```python
def sample(dec, z_dim, rng):
    z = [rng.gauss(0, 1) for _ in range(z_dim)]
    return decode(z, dec)
```

Üretken model bu. Beş satır.

## Tuzaklar

- **Posterior collapse.** KL terimi `q(z|x) → N(0, I)`'yi öyle agresif zorlar ki `z`, `x` hakkında bilgi taşımaz. Çözüm: β-annealing (β=0'dan başla, 1'e tırman), free bit'ler, ya da pasif boyutlarda KL'yi atla.
- **Bulanık örnekler.** Gaussian decoder likelihood'u MSE reconstruction'ı ima eder; bu L2 için Bayes-optimaldir (ortalama) — akla yatkın rakamlar kümesinin ortalaması bulanık bir rakamdır. Çözüm: discrete decoder (VQ-VAE, NVAE) ya da VAE'yi sadece encoder olarak kullan ve latent'lerin üzerine diffusion bindir (Stable Diffusion bunu yapar).
- **β çok büyük, çok erken.** Bkz. posterior collapse. β≈0.01'den başla ve tırman.
- **Latent boyutu çok küçük.** 16-D MNIST için işe yarar, 256-D ImageNet 256² için, 2048-D ImageNet 1024² için. Stable Diffusion'ın VAE'si 512×512×3 → 64×64×4'e sıkıştırır (uzamsal alanda 32x downsample, kanallarda 32x).

## Kullan

2026 VAE yığını:

| Durum | Seç |
|-----------|------|
| Diffusion için görsel-latent encoder | Stable Diffusion VAE (`sd-vae-ft-ema`) ya da Flux VAE |
| Ses-latent encoder | Encodec (Meta), SoundStream ya da DAC (Descript) |
| Video latent'leri | Sora'nın spatiotemporal patch'leri, Latte VAE, WAN VAE |
| Disentangle edilmiş temsil öğrenme | β-VAE, FactorVAE, TCVAE |
| Discrete latent'ler (transformer modelleme için) | VQ-VAE, RVQ (ResidualVQ) |
| Üretim için sürekli latent'ler | Düz VAE, sonra o latent uzayda bir flow/diffusion modelini koşulla |

Bir latent-diffusion modeli, encoder ile decoder arasında diffusion modeli yaşayan bir VAE'dir. VAE kaba sıkıştırma yapar, diffusion modeli ağır işi taşır. Aynı desen video (VAE + video-diffusion DiT) ve ses (Encodec + MusicGen transformer) için.

## Yayınla

`outputs/skill-vae-trainer.md` olarak kaydet.

Skill şunu alır: dataset profili + latent-boyut hedefi + downstream kullanım (reconstruction, sampling ya da latent-diffusion girdisi) ve şunu çıkarır: mimari seçim (plain/β/VQ/RVQ), β schedule, latent boyutu, decoder likelihood'u (Gaussian vs kategorik) ve değerlendirme planı (recon MSE, boyut başına KL, `q(z|x)` ile `N(0, I)` arasında Fréchet uzaklığı).

## Alıştırmalar

1. **(Kolay)** `code/main.py`'deki `β`'yı `0.01`, `0.1`, `1.0`, `5.0` olarak değiştir. Nihai reconstruction MSE ve KL'yi kaydet. Hangi β sentetik verin için Pareto-en iyi?
2. **(Orta)** Gaussian decoder likelihood'unu Bernoulli likelihood (cross-entropy loss) ile değiştir. Aynı sentetik verinin binarize edilmiş versiyonunda örnek kalitesini karşılaştır.
3. **(Zor)** `code/main.py`'yi mini bir VQ-VAE'ye uzat: sürekli `z`'yi K=32 girişli bir codebook'ta en yakın komşu lookup ile değiştir. Reconstruction MSE'yi karşılaştır ve kaç codebook girişinin kullanıldığını raporla (codebook collapse gerçek).

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Autoencoder | Encode-decode ağı | `x → z → x̂`, MSE öğren. Üretken değil. |
| VAE | Sampler'lı AE | Encoder bir dağılım çıkarır, KL cezası kod uzayını şekillendirir. |
| ELBO | Evidence lower bound | `log p(x) ≥ recon - KL[q(z|x) \|\| p(z)]`; `q = p(z|x)` olduğunda dar. |
| Reparameterization | `z = μ + σ·ε` | Stokastik düğümü deterministik + saf gürültü olarak yeniden yazar. Sampling üzerinden backprop'u mümkün kılar. |
| Prior | `p(z)` | Latent için hedef dağılım, tipik olarak `N(0, I)`. |
| Posterior collapse | "KL terimi kazanıyor" | Encoder `x`'i yok sayar, prior'u çıkarır; decoder halüsinasyon yapmak zorunda. |
| β-VAE | Ayarlanabilir KL ağırlığı | `loss = recon + β·KL`. Daha yüksek β = daha disentangle ama daha bulanık. |
| VQ-VAE | Discrete latent | Sürekli `z`'yi en yakın codebook vektörüyle değiştir; transformer modellemeyi mümkün kılar. |

## Üretim notu: VAE bir diffusion sunucusundaki en sıcak yoldur

Bir Stable Diffusion / Flux / SD3 pipeline'ında VAE istek başına iki kez çağrılır — bir kez encode (img2img / inpainting yapılıyorsa) ve bir kez decode. 1024²'de decoder pass'i, `128×128×16` latent'leri `1024×1024×3`'e geri upsample ettiği için sık sık tüm pipeline'daki tek en büyük aktivasyon-bellek tepesidir. İki pratik sonuç:

- **Decode'u dilimle ya da tile'la.** `diffusers` `pipe.vae.enable_slicing()` ve `pipe.vae.enable_tiling()` sunar. Tiling, `O(H·W)` yerine `O(tile²)` bellek için küçük bir dikiş artefaktı takas eder. Tüketici GPU'larda 1024²+ için zorunlu.
- **bf16 decoder, son resize için fp32 numerics.** SD 1.x VAE fp32'de yayınlandı ve 1024²+'da fp16'ya cast edildiğinde *sessizce NaN üretir*. SDXL `madebyollin/sdxl-vae-fp16-fix`'i ship eder — her zaman fp16-fix varyantını tercih et ya da bf16 kullan.

## İleri Okuma

- [Kingma & Welling (2013). Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) — VAE makalesi.
- [Higgins et al. (2017). β-VAE: Learning Basic Visual Concepts with a Constrained Variational Framework](https://openreview.net/forum?id=Sy2fzU9gl) — disentangle β-VAE.
- [van den Oord et al. (2017). Neural Discrete Representation Learning](https://arxiv.org/abs/1711.00937) — VQ-VAE.
- [Vahdat & Kautz (2021). NVAE: A Deep Hierarchical Variational Autoencoder](https://arxiv.org/abs/2007.03898) — state-of-the-art görsel VAE.
- [Rombach et al. (2022). High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion; encoder olarak VAE.
- [Défossez et al. (2022). High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438) — Encodec, ses VAE standardı.
