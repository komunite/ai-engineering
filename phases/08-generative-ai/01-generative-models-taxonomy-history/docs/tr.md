# Üretken Modeller — Taksonomi ve Tarih

> Her görsel modeli, metin modeli, video modeli ve 3D modeli beş gruptan birine girer. Yanlış grubu seçersen haftalarca matematikle boğuşursun. Doğrusunu seçersen alanın son on iki yıllık ilerlemesi kafanda temiz şekilde dizilir.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 2 (ML Temelleri), Faz 3 (Deep Learning Çekirdeği), Faz 7 · 14 (Transformer'lar)
**Süre:** ~45 dakika

## Sorun

Bir üretken model tek bir iş yapar: bilinmeyen bir `p_data(x)` dağılımından çekilmiş eğitim örnekleri verildiğinde, aynı dağılımdan geliyormuş gibi görünen yeni örnekler üretir. Yüzler, cümleler, MIDI dosyaları, protein yapıları — gözünü kısarsan hepsi aynı problem.

İşin can sıkıcı yanı şu: `p_data` milyonlarca boyutlu bir uzayda yaşıyor (512x512 RGB bir görsel ~786k boyut), örnekler o uzayın içindeki ince bir manifold üzerinde oturuyor ve elinde belki 10M örnek var. Yoğunluğu kaba kuvvetle bulmak umutsuz. Her üretken model, zor bir problemi biraz daha az zor bir problemle takas eden bir uzlaşmadır.

Son on iki yılda beş aile hayatta kaldı. Her ailenin hangi uzlaşmayı yaptığını bilmek, hangi görevlerde kazandığını ve hangilerinde çöktüğünü sana söyler.

## Kavram

![Üretken modellerin beş ailesi — neyi modellediğine göre taksonomi](../assets/taxonomy.svg)

**1. Açık yoğunluk, tractable.** `log p(x)`'i gerçekten değerlendirebileceğin bir toplam olarak yaz. Autoregressive modeller (PixelCNN, WaveNet, GPT) `p(x) = ∏ p(x_i | x_<i)` şeklinde faktörize eder. Normalizing flow'lar (RealNVP, Glow) `p(x)`'i basit bir tabanın tersinir bir dönüşümü olarak kurar. Artı: tam likelihood, temiz eğitim loss'u. Eksi: autoregressive çıkarım sıralıdır (uzun diziler için yavaş), flow'lar tersinir mimariler gerektirir (mimari açıdan kısıtlayıcı).

**2. Açık yoğunluk, yaklaşık.** `log p(x)`'i alttan sınırla (ELBO) ve sınırı optimize et. VAE'ler (Kingma 2013) varyasyonel posterior'lu bir encoder-decoder kullanır. Diffusion modelleri (DDPM, Ho 2020) ağırlıklı bir ELBO'yu örtük olarak optimize eden bir denoiser eğitir. Diffusion, 2026'da görsel, video ve 3D'nin baskın omurgasıdır.

**3. Örtük yoğunluk.** Yoğunluğu tamamen atla; örnek üreten bir generator `G(z)` ve gerçeği sahteden ayıran bir discriminator `D(x)` öğren. GAN'lar (Goodfellow 2014). Çıkarımda hızlı (tek forward pass) ama eğitimde namıyla kararsız. StyleGAN 1/2/3, sabit-alanlı fotorealizmde (yüzler, yatak odaları) 2026'da bile state of the art kalır.

**4. Score-tabanlı / sürekli-zaman.** Log-yoğunluğun gradyanını `∇_x log p(x)` (score) doğrudan öğren. Song & Ermon (2019) score matching'in diffusion'ı bir SDE'ye genellediğini gösterdi. Flow matching (Lipman 2023) 2024-2026 modası: simülasyonsuz eğitim, daha düz yollar, DDPM'den 4-10x daha hızlı örnekleme. Stable Diffusion 3, Flux, AudioCraft 2 hepsi flow matching kullanır.

**5. Discrete kodlar üzerinde token-tabanlı autoregressive.** Yüksek boyutlu veriyi bir VQ-VAE ya da residual quantizer ile kısa bir discrete token dizisine sıkıştır, sonra bir Transformer ile token dizisini modelle. Parti, MuseNet, AudioLM, VALL-E, Sora'nın patch tokenizer'ı hepsi bunu kullanır. Bu, 1. kova artı öğrenilmiş bir tokenizer.

## Kısa bir tarih

| Yıl | Model | Neden önemliydi |
|------|-------|-----------------|
| 2013 | VAE (Kingma) | Kullanılabilir eğitim loss'u olan ilk deep üretken model. |
| 2014 | GAN (Goodfellow) | Örtük yoğunluk, likelihood yok — şaşırtıcı derecede keskin örnekler. |
| 2015 | DRAW, PixelCNN | Sıralı görsel üretimi. |
| 2017 | Glow, RealNVP | Tersinir flow'lar; derinlikle tam likelihood. |
| 2017 | Progressive GAN | İlk megapiksel yüzler. |
| 2019 | StyleGAN / StyleGAN2 | O tek alanda hâlâ yenilmesi zor fotorealistik yüzler. |
| 2020 | DDPM (Ho) | Diffusion pratik hale geliyor. |
| 2021 | CLIP, DALL-E 1, VQGAN | Text-to-image ana akıma giriyor. |
| 2022 | Imagen, Stable Diffusion 1, DALL-E 2 | Latent diffusion + metin koşullaması = commodity. |
| 2022 | ControlNet, LoRA | Ön-eğitilmiş diffusion üzerinde ince kontrol. |
| 2023 | SDXL, Midjourney v5, Flow matching | Ölçek + daha iyi eğitim dinamikleri. |
| 2024 | Sora, Stable Diffusion 3, Flux.1 | Video diffusion; flow matching kazanır. |
| 2025 | Veo 2, Kling 1.5, Runway Gen-3, Nano Banana | Üretim kalitesinde video. |
| 2026 | Consistency + Rectified Flow | Diffusion omurgalarından tek-adım örnekleme. |

## Beş-soru triyajı

Yeni bir üretken model makalesi düştüğünde, yöntem bölümünü okumadan önce şu beş soruyu yanıtla.

1. **Ne modelleniyor?** Pikseller, latent'ler, discrete token'lar, 3D Gaussian'lar, mesh'ler, dalga formları?
2. **Yoğunluk açık mı örtük mü?** `log p(x)`'i yazıyorlar mı?
3. **Örnekleme: tek atışta mı iteratif mi?** İteratif, daha yavaş çıkarım demek; tek-atış genellikle adversarial ya da distillation'lı demek.
4. **Koşullama: koşulsuz, sınıf, metin, görsel, poz?** Bu loss'u ve mimari iskeleyi belirler.
5. **Değerlendirme: FID, CLIP score, IS, insan tercihi, görev doğruluğu?** Her birinin bilinen başarısızlık modları var (bkz. Ders 14).

Bu faz boyunca her ders için bu beşi yeniden yanıtlayacaksın. Sonunda refleks haline gelecek.

## İnşa Et

Bu dersin kodu hafif bir görselleştirme: 1-D bir Gaussian karışımını örneklerden üç oyuncak yaklaşımla (kernel yoğunluk, discrete histogram ve en yakın-örnek "GAN-vari" generator) fit et, böylece açık vs örtük yoğunluk farkını tek ekrana sığacak bir problemde görebilirsin.

`code/main.py`'yi çalıştır. İki-modlu bir Gaussian karışımından 2000 örnek çeker, sonra şunu yazdırır:

```
explicit density (histogram): p(x in [-0.5, 0.5]) ≈ 0.38
approximate density (KDE):     p(x in [-0.5, 0.5]) ≈ 0.41
implicit (nearest-sample gen): 20 new samples printed, no p(x)
```

Dikkat: ilk ikisi sana "bu nokta ne kadar olası?" sorusunu sordurur. Üçüncüsü soramaz. Bu, gelecekteki her ders için önemli olacak *açık vs örtük* ayrımıdır.

## Kullan

2026'da hangi aile, hangi görev için?

| Görev | En iyi aile | Neden |
|------|-------------|-----|
| Fotorealistik yüzler, dar alan | StyleGAN 2/3 | Hâlâ en keskin, en hızlı çıkarım. |
| Genel text-to-image | Latent diffusion + flow matching | SD3, Flux.1, DALL-E 3. |
| Hızlı text-to-image | Rectified flow + distillation | SDXL-Turbo, SD3-Turbo, LCM. |
| Text-to-video | Diffusion Transformer + flow matching | Sora, Veo 2, Kling. |
| Konuşma + müzik | Token-tabanlı AR (AudioLM, VALL-E, MusicGen) ya da flow matching (AudioCraft 2) | Discrete token'lar ucuza ölçeklenir. |
| 3D sahneler | Gaussian Splatting fit, diffusion prior | Yeniden inşa için 3D-GS, yeni-görünüm için diffusion. |
| Yoğunluk tahmini (örnekleme yok) | Flow'lar | Tam `log p(x)`'i olan tek aile. |
| Simülasyon / fizik | Flow matching, score SDE | Düz-çizgi yollar, pürüzsüz vektör alanları. |

## Yayınla

`outputs/skill-model-chooser.md` olarak kaydet.

Skill bir görev tanımı alır ve şunları çıkarır: (1) hangi aileyi kullanacağın, (2) sıralanmış üç açık ve üç hosted seçenek listesi, (3) dikkat etmen gereken muhtemel başarısızlık modu, ve (4) compute/zaman bütçesi.

## Alıştırmalar

1. **(Kolay)** Şu beş ürün için aileyi ve omurgayı belirle: ChatGPT image, Midjourney v7, Sora, Runway Gen-3, ElevenLabs. Kanıt halka açık teknik raporlardan olmalı.
2. **(Orta)** Yarın okuyacağın makale diffusion'dan 100x daha hızlı örnekleme iddia ediyor. Hızlanmanın koşullama ve yüksek çözünürlükte hayatta kalıp kalmadığını kontrol etmek için üç soru yaz.
3. **(Zor)** Önemsediğin bir alanı al (örn. protein yapısı, CAD, moleküller, yörüngeler). O alandaki mevcut SOTA modeli için beş-soru triyajını yanıtla ve daha iyi bir modelin neyi değiştireceğini taslakla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Üretken model | "Yeni şeyler üretiyor" | `p_data(x)` için bir sampler öğrenir, isteğe bağlı olarak `log p(x)`'i açar. |
| Açık yoğunluk | "Değerlendirilebilir" | Model closed-form ya da tractable bir `log p(x)` sağlar. |
| Örtük yoğunluk | "GAN tarzı" | Sadece sampler — verilen bir noktanın `p(x)`'ini değerlendirmenin yolu yok. |
| ELBO | "Evidence lower bound" | `log p(x)` için tractable bir alt sınır; VAE'ler ve diffusion bunu optimize eder. |
| Score | "Log-yoğunluğun gradyanı" | `∇_x log p(x)`; diffusion ve SDE modelleri bu alanı öğrenir. |
| Manifold hipotezi | "Veri bir yüzeyde yaşıyor" | Yüksek boyutlu veri düşük boyutlu bir manifold üzerinde yoğunlaşır; boyut indirgemenin neden çalıştığı. |
| Autoregressive | "Sonraki parçayı tahmin et" | Eklem dağılımı koşulluların çarpımı olarak faktörize et. |
| Latent | "Sıkıştırılmış kod" | Bir decoder'ın girdiyi yeniden inşa edebileceği düşük boyutlu temsil. |

## Üretim notu: beş aile, beş çıkarım şekli

Her aile farklı bir çıkarım-sunucusu maliyet eğrisine karşılık gelir. Üretim-çıkarım literatürü LLM çıkarımını prefill + decode olarak çerçeveler; aynı ayrıştırma burada da geçerli:

- **Autoregressive (kova 1 ve 5).** Sıralı decode latency'ye hakim; KV-cache, sürekli batching ve speculative decoding doğrudan uygulanır.
- **VAE / diffusion / flow-matching (kova 2 ve 4).** LLM anlamında bir decode yok. Maliyet = `num_steps × step_cost` ve `step_cost`, tam latent çözünürlüğünde bir transformer ya da U-Net forward'ı. Üretim kontrolleri adım sayısı (DDIM / DPM-Solver / distillation), batch size ve hassasiyet (bf16 / fp8 / int4).
- **GAN (kova 3).** Tek forward pass. Schedule yok, KV-cache yok. TTFT ≈ toplam latency. StyleGAN'ın dar alan UX'inde hâlâ kazanmasının nedeni budur.

Bir makale özetinde "diffusion'dan daha hızlı" gördüğünde, bunu "daha az adım × aynı adım maliyeti" ya da "aynı adım × daha ucuz adım maliyeti" olarak çevir. Geri kalan her şey pazarlama.

## İleri Okuma

- [Goodfellow et al. (2014). Generative Adversarial Nets](https://arxiv.org/abs/1406.2661) — GAN makalesi.
- [Kingma & Welling (2013). Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) — VAE makalesi.
- [Ho, Jain, Abbeel (2020). Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) — DDPM makalesi.
- [Song et al. (2021). Score-Based Generative Modeling through SDEs](https://arxiv.org/abs/2011.13456) — SDE olarak diffusion.
- [Lipman et al. (2023). Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747) — flow matching makalesi.
- [Esser et al. (2024). Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206) — Stable Diffusion 3.
