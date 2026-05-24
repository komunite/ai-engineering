# Flow Matching ve Rectified Flow

> Diffusion modelleri gürültüden veriye eğri bir yol yürüdüğü için 20-50 sampling adımı alır. Flow matching (Lipman et al., 2023) ve rectified flow (Liu et al., 2022) düz yolları eğitti. Daha düz yollar daha az adım, daha az adım daha hızlı çıkarım demek. Stable Diffusion 3, Flux.1 ve AudioCraft 2 hepsi 2024'te flow matching'e geçti.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 06 (DDPM), Faz 1 · Kalkülüs
**Süre:** ~45 dakika

## Sorun

DDPM'nin reverse süreci `N(0, I)`'dan veri dağılımına 1000-adımlık stokastik bir yürüyüş. DDIM bunu 20-50 deterministik adıma çöktü. Daha az adım istiyorsun — ideal olarak tek. Engel, reverse süreci çözen ODE'nin stiff olması; yol eğridir.

Modeli, gürültüden veriye olan yolun *düz bir çizgi* olacağı şekilde eğitebilirsen, `t=1`'den `t=0`'a tek Euler adımı çalışırdı. Flow matching bunu doğrudan kurar: `x_1 ∼ N(0, I)`'dan `x_0 ∼ data`'ya düz-çizgi interpolasyon tanımla, bir vektör alanı `v_θ(x, t)`'yi zaman türevini eşlemek için eğit, çıkarımda entegre et.

Rectified flow (Liu 2022) daha ileri gider: yolları iteratif olarak, kademeli olarak lineere yaklaşan bir ODE üreten reflow prosedürüyle düzleştirir. İki reflow iterasyonundan sonra, 2-adımlık bir sampler 50-adımlık DDPM kalitesiyle eşleşir.

## Kavram

![Flow matching: gürültü ve veri arasında düz-çizgi interpolasyonu](../assets/flow-matching.svg)

### Düz-çizgi flow

Tanımla:

```
x_t = t · x_1 + (1 - t) · x_0,   t ∈ [0, 1]
```

burada `x_0 ~ data` ve `x_1 ~ N(0, I)`. Bu düz çizgi boyunca zaman türevi sabittir:

```
dx_t / dt = x_1 - x_0
```

Bir neural vektör alanı `v_θ(x_t, t)` tanımla ve onu bu türevi eşlemek için eğit:

```
L = E_{x_0, x_1, t} || v_θ(x_t, t) - (x_1 - x_0) ||²
```

Bu, **conditional flow matching** loss'u (Lipman 2023). Eğitim simülasyonsuz: ODE'yi hiç açmazsın. Sadece `(x_0, x_1, t)` örnekle ve regress et.

### Sampling

Çıkarımda, öğrenilmiş vektör alanını zamanda *geriye* entegre et:

```
x_{t-Δt} = x_t - Δt · v_θ(x_t, t)
```

`x_1 ~ N(0, I)`'da başla, `t=0`'a Euler-adımla in.

### Rectified flow (Liu 2022)

Düz-çizgi flow çalışır ama öğrenilen yollar *gerçekten düz değildir* — eğrilirler çünkü birçok `x_0` aynı `x_1`'e eşlenebilir. Rectified flow'un reflow adımı:

1. Rastgele eşleşmelerle flow modeli v_1 eğit.
2. v_1'i `x_1`'den iniş noktası `x_0`'a entegre ederek N çift `(x_1, x_0)` örnekle.
3. v_2'yi bu eşli örnekler üzerinde eğit. Çiftler artık "ODE-eşleştirilmiş" olduğundan, aralarındaki düz-çizgi interpolant'ı gerçekten daha düzdür.
4. Tekrarla.

Pratikte 2 reflow iterasyonu seni neredeyse-lineere getirir, 2-4 adımlık çıkarımı mümkün kılar. SDXL-Turbo, SD3-Turbo, LCM hepsi flow-matching'ten distillation'lı modeller.

### Neden 2024'te görsellerde kazandı

Üç neden:

1. **Simülasyonsuz eğitim** — eğitim sırasında ODE açma yok, uygulaması trivial.
2. **Daha iyi loss geometrisi** — düz yollar tutarlı sinyal-gürültü oranına sahip, DDPM ε-loss'u schedule'ın kenarlarında kötü SNR'ye sahip.
3. **Daha hızlı çıkarım** — SDXL-Turbo kalitesinde 4-8 adım; consistency distillation ile 1 adım.

## Flow matching vs DDPM — tam bağlantı

Gaussian-koşullu yollu flow matching, *belirli bir gürültü schedule'ıyla* diffusion'dır. `x_t = α(t) x_0 + σ(t) x_1` schedule'ını seç ve flow matching `v = α'·x_0 - σ'·x_1` ile Stratonovich-yeniden formüle edilmiş diffusion'ı geri kazanır. İkisi Gaussian yollar için cebirsel olarak eşdeğer.

Flow matching'in eklediği: hedefin *netliği* (düz bir hız), daha temiz bir loss ve Gaussian olmayan interpolant'larla deney yapma lisansı.

## İnşa Et

`code/main.py` iki-modlu bir Gaussian karışımında 1-D flow matching uygular. Vektör alanı `v_θ(x, t)` düz-çizgi hedefiyle eğitilmiş minik bir MLP. Çıkarımda 1, 2, 4 ve 20 Euler adımını entegre et ve örnek kalitesini karşılaştır.

### Adım 1: eğitim loss'u

```python
def train_step(x0, net, rng, lr):
    x1 = rng.gauss(0, 1)
    t = rng.random()
    x_t = t * x1 + (1 - t) * x0
    target = x1 - x0
    pred = net_forward(x_t, t)
    loss = (pred - target) ** 2
    # backprop + güncelle
```

### Adım 2: çok-adımlı çıkarım

```python
def sample(net, num_steps):
    x = rng.gauss(0, 1)
    for i in range(num_steps):
        t = 1.0 - i / num_steps
        dt = 1.0 / num_steps
        x -= dt * net_forward(x, t)
    return x
```

### Adım 3: adım sayılarını karşılaştır

4-adımlı sampler'ın zaten 20-adımlı kaliteyle eşleşmesini bekle — latency için büyük olay.

## Tuzaklar

- **Zaman parametrelemesi.** Flow matching `t=0` veride, `t=1` gürültüde olacak şekilde `t ∈ [0, 1]` kullanır. DDPM `t=0` veride, `t=T` gürültüde olacak şekilde `t ∈ [0, T]` kullanır. Aynı yön, farklı ölçek. Makaleler bunu sürekli yanlış yapar.
- **Schedule seçimi.** Rectified flow'un düz çizgisi "tek" flow-matching schedule'ı ama daha iyi ölçek kapsamı için cosine ya da logit-normal t-örnekleme (SD3 bunu yapar) kullanabilirsin.
- **Reflow maliyeti.** Reflow için eşli dataset üretmek örnek başına tam bir çıkarım pass'i. Sadece gerçekten 1-2 adımlık çıkarım gerektiğinde reflow yap.
- **Classifier-free guidance hâlâ uygulanır.** Lineer kombinasyonda ε'yı v ile değiştir: `v_cfg = (1+w) v_cond - w v_uncond`.

## Kullan

| Kullanım durumu | 2026 yığını |
|----------|-----------|
| Text-to-image, en iyi kalite | Flow matching: SD3, Flux.1-dev |
| Text-to-image, 1-4 adım | Distillation'lı flow matching: Flux.1-schnell, SD3-Turbo, SDXL-Turbo |
| Gerçek-zamanlı çıkarım | Flow-matched bir tabandan consistency distillation (LCM, PCM) |
| Ses üretimi | Flow matching: Stable Audio 2.5, AudioCraft 2 |
| Video üretimi | Diffusion'la karışmış flow matching (Sora, Veo, Stable Video) |
| Bilim / fizik (parçacık yörüngeleri, moleküller) | Flow matching + equivariant vektör alanı |

2025-2026'da bir makale "diffusion'dan daha hızlı" dediğinde, neredeyse her zaman flow matching + distillation.

## Yayınla

`outputs/skill-fm-tuner.md` olarak kaydet. Skill diffusion-stil bir model spec'i alır ve onu flow-matching eğitim config'ine dönüştürür: schedule seçimi, zaman örnekleme dağılımı (uniform / logit-normal), optimizer, reflow planı, hedef adım sayısı, eval protokolü.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi çalıştır ve gerçek veri dağılımına karşı 1-adımlık vs 20-adımlık MSE'yi karşılaştır.
2. **(Orta)** Uniform `t` örneklemesinden logit-normal'a geç (örneklemeyi orta-t'de yoğunlaştırır). Model kalitesi artar mı?
3. **(Zor)** Bir reflow iterasyonu uygula: ilk modeli entegre ederek eşli (x_0, x_1) üret, ikinci modeli çiftler üzerinde eğit ve 1-adımlık örnek kalitesini karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Flow matching | "Düz-çizgi diffusion" | `v_θ(x, t)`'yi bir interpolant boyunca `x_1 - x_0`'ı eşlemek için eğit. |
| Rectified flow | "Reflow" | Öğrenilen flow'ları düzleştiren iteratif prosedür. |
| Velocity field | "v_θ" | Modelin çıkışı — `x_t`'yi hareket ettirme yönü. |
| Düz-çizgi interpolant | "Yol" | `x_t = (1-t)·x_0 + t·x_1`; trivial hedef türevi. |
| Euler sampler | "1. derece ODE çözücüsü" | En basit entegrator; yollar düz olduğunda iyi çalışır. |
| Logit-normal t | "SD3 örneklemesi" | `t` örneklemesini gradyanların en güçlü olduğu orta değerlere yoğunlaştır. |
| Consistency distillation | "1-adımlık sampler" | Bir öğrenciyi herhangi bir `x_t`'yi doğrudan `x_0`'a eşlemeye eğit. |
| Hızla CFG | "v-CFG" | `v_cfg = (1+w) v_cond - w v_uncond`; aynı numara, yeni değişken. |

## Üretim notu: Flux.1-schnell en hızlı haliyle flow matching

Flow matching'in üretim zaferi Flux.1-schnell — Flux-dev-seviyesi kaliteyi korurken 1-4 çıkarım adımına distillation'lı flow-matched bir DiT. Niels'in "8GB makinede Flux çalıştır" notebook'u referans deployment reçetesi: T5 + CLIP encode, quantize MMDiT denoise (schnell için 4 adımda vs dev için 50), VAE decode. Maliyet muhasebesi:

| Varyant | Adımlar | L4'te 1024²'de latency | Toplam FLOPs (göreli) |
|---------|-------|------------------------|------------------------|
| Flux.1-dev (ham) | 50 | ~15 sn | 1.0× |
| Flux.1-schnell | 4 | ~1.2 sn | 0.08× (12× daha hızlı) |
| SDXL-base | 30 | ~4 sn | 0.25× |
| SDXL-Lightning 2-step | 2 | ~0.3 sn | 0.03× |

Üretim kuralı: **flow-matched taban + distillation = hızlı text-to-image için 2026 varsayılanı.** Her büyük satıcı bu kombo'yu ship ediyor: SD3-Turbo (SD3 + flow + distillation), Flux-schnell (Flux-dev + rectified-flow düzleştirme), CogView-4-Flash. Saf diffusion tabanları sadece eski checkpoint'ler için var.

## İleri Okuma

- [Liu, Gong, Liu (2022). Flow Straight and Fast: Learning to Generate and Transfer Data with Rectified Flow](https://arxiv.org/abs/2209.03003) — rectified flow.
- [Lipman et al. (2023). Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747) — flow matching.
- [Esser et al. (2024). Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206) — SD3, ölçekte rectified flow.
- [Albergo, Vanden-Eijnden (2023). Stochastic Interpolants](https://arxiv.org/abs/2303.08797) — FM + diffusion'ı kapsayan genel çerçeve.
- [Song et al. (2023). Consistency Models](https://arxiv.org/abs/2303.01469) — diffusion / flow'un 1-adımlık distillation'ı.
- [Sauer et al. (2023). Adversarial Diffusion Distillation (SDXL-Turbo)](https://arxiv.org/abs/2311.17042) — turbo varyantı.
- [Black Forest Labs (2024). Flux.1 modelleri](https://blackforestlabs.ai/announcing-black-forest-labs/) — üretimde flow matching.
