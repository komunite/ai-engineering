# GAN'lar — Generator vs Discriminator

> Goodfellow'un 2014'teki numarası yoğunluğu tamamen atlamaktı. İki ağ. Biri sahteler üretir. Diğeri onları yakalar. Sahteler gerçekten ayırt edilemez hale gelene kadar dövüşürler. Çalışmamalı. Çoğu zaman çalışmıyor. Çalıştığında, örnekler dar alanlar için literatürdeki en keskin örnekler.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 · 02 (Backprop), Faz 3 · 08 (Optimizer'lar), Faz 8 · 02 (VAE)
**Süre:** ~75 dakika

## Sorun

VAE'ler bulanık örnekler üretir çünkü MSE decoder loss'u *ortalama* görsel için Bayes-optimaldir — ve birçok akla yatkın rakamın ortalaması bulanık bir rakamdır. *Akla yatkınlığı* ödüllendiren bir loss istiyorsun, herhangi bir hedefe piksel başına yakınlığı değil. Akla yatkınlığın closed-form'u yok. Onu öğrenmek zorundasın.

Goodfellow'un fikri: gerçek görselleri sahtelerden ayıran bir sınıflandırıcı `D(x)` eğit. `D`'yi kandıracak bir generator `G(z)` eğit. `G` için loss sinyali, `D`'nin şu anda bir şeyi gerçeğe benzettiği her şey. Bu sinyal `G` geliştikçe güncellenir, hareketli bir hedefi kovalar. Eğer iki ağ da yakınsarsa, `G` `log p(x)`'i hiç yazmadan veri dağılımını öğrenmiştir.

Bu, adversarial training. Matematik bir minimax oyunu:

```
min_G max_D  E_real[log D(x)] + E_fake[log(1 - D(G(z)))]
```

2026'da GAN'lar artık SOTA generator değil (diffusion ve flow matching o tacı yedi). Ama StyleGAN 2/3 hâlâ ship edilmiş en keskin yüz modelleri, GAN discriminator'ları diffusion eğitiminde *perceptual loss* olarak kullanılıyor ve adversarial training, gerçek zamanlı diffusion ship etmeni sağlayan hızlı 1-adımlık distillation'ları (SDXL-Turbo, SD3-Turbo, LCM) çalıştırıyor.

## Kavram

![GAN eğitimi: minimax'ta generator ve discriminator](../assets/gan.svg)

**Generator `G(z)`.** Bir gürültü vektörü `z ~ N(0, I)`'yi bir örnek `x̂`'ye eşler. Decoder şeklinde bir ağ (yoğun ya da transposed conv).

**Discriminator `D(x)`.** Bir örneği skaler bir olasılığa (ya da skora) eşler. Gerçek → 1, sahte → 0.

**Loss.** İki alternatif güncelleme:

- **`D`'yi eğit:** `loss_D = -[ log D(x) + log(1 - D(G(z))) ]`. Gerçek=1, sahte=0 üzerinde binary cross-entropy.
- **`G`'yi eğit:** `loss_G = -log D(G(z))`. Bu Goodfellow'un kullandığı *non-saturating* form (orijinal `log(1 - D(G(z)))` `D` emin olduğunda doyar ve gradyanları öldürür).

**Eğitim döngüsü.** Bir adım `D`, bir adım `G`. Tekrarla.

**Neden çalışır.** Eğer `G` `p_data`'yı mükemmel eşlerse, `D` şanstan daha iyi yapamaz ve her yerde 0.5 çıkarır; `G` artık gradyan almaz. Denge.

**Neden bozulur.** Mode collapse (`G`, `D`'nin sınıflandıramadığı tek bir mod bulur ve sonsuza kadar basar), vanishing gradient (`D` çok hızlı öğrenir ve `log D` doyar), eğitim kararsızlığı (learning rate, batch size, her şey).

## GAN'ları çalıştıran varyantlar

| Yıl | Yenilik | Düzeltme |
|------|------------|-----|
| 2015 | DCGAN | Conv/deconv, batch norm, LeakyReLU — ilk kararlı mimari. |
| 2017 | WGAN, WGAN-GP | BCE'yi Wasserstein uzaklığı + gradient penalty ile değiştir. Vanishing gradient'ı düzeltir. |
| 2017 | Spectral normalization | Discriminator'ı Lipschitz-bound et. 2026 discriminator'larında hâlâ kullanılıyor. |
| 2018 | Progressive GAN | Önce düşük çözünürlük eğit, katmanlar ekle. İlk megapiksel sonuçlar. |
| 2019 | StyleGAN / StyleGAN2 | Mapping network + adaptive instance norm. Sabit-alan fotorealizmde state of the art. |
| 2021 | StyleGAN3 | Alias-free, translation-equivariant — 2026'da hâlâ yüz altın standardı. |
| 2022 | StyleGAN-XL | Koşullu, sınıf-bilinçli, daha büyük ölçek. |
| 2024 | R3GAN | Daha güçlü regularization ile yeniden marka; numarasız 1024²'de çalışır. |

## İnşa Et

`code/main.py` 1-D veri üzerinde minik bir GAN eğitir: iki Gaussian'ın karışımı. Generator ve discriminator tek gizli katmanlı MLP'ler. Forward, backward ve minimax döngüsünü elle uyguluyoruz. Hedef, iki anahtar başarısızlık modunu (mode collapse + vanishing gradient) yaşanırken görmek.

### Adım 1: non-saturating loss

Vanilla Goodfellow loss'u `log(1 - D(G(z)))`, D, G'nin sahtesini yüksek güvenle sahte olarak sınıflandırdığında 0'a gider. O noktada G için gradyan temelde sıfırdır — G iyileşemez. Non-saturating form `-log D(G(z))` ters bir asimptota sahiptir: D emin olduğunda patlar ve G'ye güçlü bir sinyal verir.

```python
def g_loss(d_fake):
    # log D(G(z))'yi maksimize et  <=>  -log D(G(z))'yi minimize et
    return -sum(math.log(max(p, 1e-8)) for p in d_fake) / len(d_fake)
```

### Adım 2: generator adımı başına bir discriminator adımı

```python
for step in range(steps):
    # D'yi eğit
    real_batch = sample_real(batch_size)
    fake_batch = [G(z) for z in sample_noise(batch_size)]
    update_D(real_batch, fake_batch)

    # G'yi eğit
    fake_batch = [G(z) for z in sample_noise(batch_size)]  # taze sahteler
    update_G(fake_batch)
```

G için taze sahteler, aksi halde gradyanlar bayatlar.

### Adım 3: mode collapse'a dikkat et

```python
if step % 200 == 0:
    samples = [G(z) for z in sample_noise(500)]
    mode_a = sum(1 for s in samples if s < 0)
    mode_b = 500 - mode_a
    if min(mode_a, mode_b) < 50:
        print("  [!] mode collapse: one mode is starved")
```

Kanonik semptom: iki gerçek moddan biri artık üretilmiyor. Discriminator onu düzeltmeyi durdurur çünkü onu hiç sahte olarak görmez.

## Tuzaklar

- **Discriminator çok güçlü.** D'nin learning rate'ini 2-5x düşür ya da instance/katman gürültüsü ekle. D >%95 doğruluğa ulaşırsa G öldü.
- **Generator bir modu ezberliyor.** D girdilerine gürültü ekle, bir minibatch-discriminator katmanı kullan ya da WGAN-GP'ye geç.
- **Batch norm istatistik sızdırıyor.** Aynı BN katmanından akan gerçek batch + sahte batch istatistiklerini karıştırır. Onun yerine instance norm ya da spectral norm kullan.
- **Inception-score gaming.** FID ve IS düşük örnek sayılarında gürültülü. Eval'de ≥10k örnek kullan.
- **Tek-atış sampling koşullu görevlerde bir yalan.** Hâlâ kullanılabilir çıktılar için CFG ölçekleri, truncation numaraları ve yeniden örnekleme gerek.

## Kullan

2026 GAN yığını:

| Durum | Seç |
|-----------|------|
| Fotorealistik insan yüzleri, sabit poz | StyleGAN3 (en keskin, en küçük) |
| Anime / stilize yüzler | StyleGAN-XL ya da Stable Diffusion LoRA |
| Görsel-görsel çevirisi | Pix2Pix / CycleGAN (Faz 8 · 04) ya da ControlNet (Faz 8 · 08) |
| Hızlı 1-adımlık text-to-image | Diffusion'ın adversarial distillation'ı (SDXL-Turbo, SD3-Turbo) |
| Diffusion trainer içinde perceptual loss | Görsel crop'lar üzerinde küçük GAN discriminator |
| Çok-modlu, açık-uçlu herhangi bir şey | Yapma — diffusion ya da flow matching kullan |

GAN'lar keskin ama dar. Alanın açıldığında — fotoğraflar, keyfi metin prompt'ları, video — diffusion'a geç. Adversarial numara bir bileşen olarak yaşar (perceptual loss'lar, distillation), tek başına bir generator olarak değil.

## Yayınla

`outputs/skill-gan-debugger.md` olarak kaydet. Skill başarısız bir GAN koşusunu (loss eğrileri, örnek grid'i, dataset boyutu) alır ve sıralanmış olası nedenler listesi, tek satırlık düzeltmeler ve yeniden çalıştırma protokolü çıkarır.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi stok ayarlarla çalıştır. Sonra `D_LR = 5 * G_LR` ayarla ve yeniden çalıştır. G'nin loss'u sabite ne kadar hızlı çöker?
2. **(Orta)** Goodfellow BCE loss'unu WGAN loss'u ile değiştir: `loss_D = E[D(fake)] - E[D(real)]`, `loss_G = -E[D(fake)]` ve D'nin ağırlıklarını `[-0.01, 0.01]`'e clip et. Eğitim daha kararlı mı? Duvar-saati yakınsamayı karşılaştır.
3. **(Zor)** 1-D örneği 2-D veriye uzat (halka üzerinde 8 Gaussian karışımı). Generator'ın 1k, 5k, 10k adımda 8 moddan kaçını yakaladığını takip et. Minibatch discrimination uygula ve yeniden ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Generator | "G" | Gürültüden örneğe ağ, `G: z → x̂`. |
| Discriminator | "D" | Sınıflandırıcı `D: x → [0, 1]`, gerçek vs sahte. |
| Minimax | "Oyun" | Ortak bir hedefin `min_G max_D`'si. |
| Non-saturating loss | "Düzeltme" | G için `log(1 - D(G(z)))` yerine `-log D(G(z))` kullan. |
| Mode collapse | "G bir şeyi ezberledi" | Generator çeşitli veriye rağmen az sayıda farklı çıktı üretir. |
| WGAN | "Wasserstein" | BCE'yi Earth-Mover uzaklığı + gradient penalty ile değiştir; daha pürüzsüz gradyan. |
| Spectral norm | "Lipschitz numarası" | D'nin ağırlık normlarını eğimini bağlamak için kısıtla; eğitimi stabilize eder. |
| StyleGAN | "Çalışan" | Mapping network + AdaIN; yüzlerde sınıfının en iyisi, 2026'da hâlâ. |

## Üretim notu: tek-atış çıkarım GAN'ın kalıcı avantajıdır

GAN'lar artık açık-alan üretiminde örnek kalitesinde kazanmıyor ama çıkarım maliyetinde hâlâ kazanıyorlar. Üretim-çıkarım literatürü diliyle bir GAN'ın:

- **Prefill yok, decode aşaması yok.** Tek bir `G(z)` forward pass'i. TTFT ≈ toplam latency.
- **KV-cache baskısı yok.** Tek state ağırlıklar. Batch size cache değil, aktivasyon belleği tarafından sınırlanır.
- **Önemsiz sürekli batching.** Her istek aynı sabit FLOPs'u aldığından, sunucunun hedef doluluğunda statik bir batch genellikle optimaldir. In-flight scheduler gerek yok.

2026'da hızlı text-to-image için baskın teknik olarak GAN distillation'ın (SDXL-Turbo, SD3-Turbo, ADD, LCM) nedeni budur: bir diffusion tabanının dağılımını korurken 20-50 adımlık bir diffusion pipeline'ını 1-4 GAN tarzı forward pass'e çöker. Adversarial loss, yavaş generator'ları hızlılara dönüştürmek için eğitim zamanı bir düğme olarak hayatta kalır.

## İleri Okuma

- [Goodfellow et al. (2014). Generative Adversarial Nets](https://arxiv.org/abs/1406.2661) — orijinal GAN makalesi.
- [Radford et al. (2015). Unsupervised Representation Learning with DCGAN](https://arxiv.org/abs/1511.06434) — ilk kararlı mimari.
- [Arjovsky, Chintala, Bottou (2017). Wasserstein GAN](https://arxiv.org/abs/1701.07875) — WGAN.
- [Miyato et al. (2018). Spectral Normalization for GANs](https://arxiv.org/abs/1802.05957) — SN.
- [Karras et al. (2020). Analyzing and Improving the Image Quality of StyleGAN](https://arxiv.org/abs/1912.04958) — StyleGAN2.
- [Karras et al. (2021). Alias-Free Generative Adversarial Networks](https://arxiv.org/abs/2106.12423) — StyleGAN3.
- [Sauer et al. (2023). Adversarial Diffusion Distillation](https://arxiv.org/abs/2311.17042) — SDXL-Turbo.
