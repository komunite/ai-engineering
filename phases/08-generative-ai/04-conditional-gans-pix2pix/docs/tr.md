# Conditional GAN'lar ve Pix2Pix

> 2014-2017'nin ilk büyük kilidi açma anı, bir GAN'ın ne yaptığını kontrol etmekti. Bir etiket ekle ya da bir görsel ya da bir cümle. Pix2Pix bunun görsel versiyonunu yaptı ve dar görsel-görsel görevlerinde hâlâ her genel text-to-image modelini geçer.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 03 (GAN'lar), Faz 4 · 06 (U-Net), Faz 3 · 07 (CNN'ler)
**Süre:** ~75 dakika

## Sorun

Koşulsuz bir GAN keyfi yüzler örnekler. Demo için faydalı, üretimde işe yaramaz. İstediğin: *bir eskizi fotoğrafa eşle*, *bir haritayı hava fotoğrafına eşle*, *gündüz sahnesini geceye eşle*, *gri tonlamalı bir görseli renklendir*. Bunların hepsinde girdi olarak bir `x` görseli alırsın ve bazı semantik karşılıklı bir `y` çıkarmalısın. `x` başına birçok akla yatkın `y` vardır. Mean-squared error onları lapaya düzleştirir. Adversarial loss düzleştirmez, çünkü "gerçek görünüyor" keskindir.

Conditional GAN (Mirza & Osindero, 2014) hem `G`'ye hem `D`'ye girdi olarak bir koşul `c` ekler. Pix2Pix (Isola et al., 2017) bunu özelleştirdi: koşul tam bir girdi görseli, generator bir U-Net, discriminator *patch-tabanlı* bir sınıflandırıcı (PatchGAN) ve loss adversarial + L1. Bu reçete, 2026'da bile dar görsel-görsel alanlarda sıfırdan text-to-image modellerini geçer çünkü *eşli veri* üzerinde eğitilmiştir — tam ihtiyacın olan sinyale sahipsin.

## Kavram

![Pix2Pix: U-Net generator, PatchGAN discriminator](../assets/pix2pix.svg)

**Koşullu G.** `G(x, z) → y`. Pix2Pix'te `z`, G içindeki dropout'tur (girdi gürültüsü yok — Isola açık gürültünün yok sayıldığını buldu).

**Koşullu D.** `D(x, y) → [0, 1]`. Girdi *çift* (koşul, çıktı). Anahtar fark bu: D, `y`'nin sadece gerçek görünüp görünmediğine değil, `x` ile tutarlı olup olmadığına karar vermek zorunda.

**U-Net generator.** Bottleneck boyunca skip connection'lı encoder-decoder. Girdi ve çıktının düşük seviyeli yapıyı (kenarlar, siluet) paylaştığı görevler için kritik. Skip'ler olmadan yüksek-frekanslı detay kaybolur.

**PatchGAN discriminator.** Tek bir gerçek/sahte skoru çıkarmak yerine, D her hücresi ~70×70 piksellik bir receptive field'a karar veren bir `N×N` grid çıkarır. Ortalanır. Bu bir Markov random field varsayımıdır: gerçekçilik yereldir. Eğitmesi çok daha hızlı, daha az parametre, daha keskin çıktı.

**Loss.**

```
loss_G = -log D(x, G(x)) + λ · ||y - G(x)||_1
loss_D = -log D(x, y) - log (1 - D(x, G(x)))
```

L1 terimi eğitimi stabilize eder ve G'yi bilinen hedefe iter. L1, L2'den daha keskin kenarlar verir (medyanlar, ortalama değil). `λ = 100` Pix2Pix varsayılanıydı.

## CycleGAN — eşli verin olmadığında

Pix2Pix eşli `(x, y)` veri ister. CycleGAN (Zhu et al., 2017) bu gereksinimi ekstra bir loss pahasına atar: *cycle consistency* loss'u. İki generator `G: X → Y` ve `F: Y → X`. Onları `F(G(x)) ≈ x` ve `G(F(y)) ≈ y` olacak şekilde eğit. Bu eşli örnek olmadan atları zebralara, yazı kışa çevirmeni sağlar.

2026'da eşsiz görsel-görsel çoğunlukla CycleGAN yerine diffusion (ControlNet, IP-Adapter) ile yapılır ama cycle-consistency fikri hemen her eşsiz alan adaptasyonu makalesinde yaşar.

## İnşa Et

`code/main.py` 1-D veri üzerinde minik bir conditional GAN uygular. Koşul `c` bir sınıf etiketi (0 ya da 1). Görev: verilen sınıf için koşullu dağılımdan bir örnek üret.

### Adım 1: koşulu hem G hem D girdilerine ekle

```python
def G(z, c, params):
    return mlp(concat([z, one_hot(c)]), params)

def D(x, c, params):
    return mlp(concat([x, one_hot(c)]), params)
```

One-hot encoding en basit yol. Daha büyük modeller öğrenilmiş embedding, FiLM modülasyonu ya da cross-attention kullanır.

### Adım 2: koşullu eğitim

```python
for step in range(steps):
    x, c = sample_real_conditional()
    noise = sample_noise()
    update_D(x_real=x, x_fake=G(noise, c), c=c)
    update_G(noise, c)
```

Generator marjinal dağılımı değil, *verilen koşul için* gerçek dağılımı eşlemeli.

### Adım 3: sınıf başına çıktıyı doğrula

```python
for c in [0, 1]:
    samples = [G(noise, c) for noise in batch]
    mean_c = mean(samples)
    assert_near(mean_c, real_mean_for_class_c)
```

## Tuzaklar

- **Koşul yok sayıldı.** G marjinalize etmeyi öğrenir, D ceza vermez çünkü koşul sinyali zayıf. Çözüm: D'yi daha agresif koşulla (erken katman, sadece geç değil), projection discriminator kullan (Miyato & Koyama 2018).
- **L1 ağırlığı çok düşük.** G sadık olmayan, keyfi gerçek-görünüşlü çıktılara sürüklenir. Pix2Pix tarzı görevler için λ≈100 ile başla.
- **L1 ağırlığı çok yüksek.** G bulanık çıktı üretir çünkü L1 hâlâ bir L_p norm. Eğitim stabilize olduğunda aşağı anneal et.
- **D'de ground-truth sızıntısı.** Sadece `y`'yi değil, `(x, y)`'yi D girdisi olarak concatenate et. Bu olmadan D tutarlılığı kontrol edemez.
- **Sınıf başına mode collapse.** Her sınıf bağımsız çökebilir. Sınıf-koşullu çeşitlilik kontrolleri çalıştır.

## Kullan

2026'da görsel-görsel görevlerinin durumu:

| Görev | En iyi yaklaşım |
|------|---------------|
| Eskiz → fotoğraf, aynı alan, eşli veri | Pix2Pix / Pix2PixHD (hâlâ hızlı, hâlâ keskin) |
| Eskiz → fotoğraf, eşsiz | Scribble koşullama modeliyle ControlNet |
| Semantic seg → fotoğraf | SPADE / GauGAN2 ya da SD + ControlNet-Seg |
| Stil transferi | IP-Adapter ya da LoRA ile diffusion; GAN yöntemleri eski |
| Derinlik → fotoğraf | Stable Diffusion üzerinde ControlNet-Depth |
| Süper çözünürlük | Real-ESRGAN (GAN), ESRGAN-Plus ya da SD-Upscale (diffusion) |
| Renklendirme | ColTran, diffusion-tabanlı renklendiriciler ya da Pix2Pix-color |
| Gündüz → gece, mevsimler, hava | CycleGAN ya da ControlNet-tabanlı |

Pix2Pix şu durumlarda doğru araç olmaya devam eder: (a) binlerce eşli örneğin var, (b) görev dar ve tekrarlanabilir, ve (c) hızlı çıkarım gerek. Genel açık-alan görevlerinde diffusion kazanır.

## Yayınla

`outputs/skill-img2img-chooser.md` olarak kaydet. Skill bir görev tanımı, veri durumu (eşli vs eşsiz, N örnek) ve latency/kalite bütçesi alır, sonra şunu çıkarır: yaklaşım (Pix2Pix, CycleGAN, ControlNet varyantı, SDXL + IP-Adapter), eğitim verisi gereksinimleri, çıkarım maliyeti ve eval protokolü (LPIPS, FID, göreve özgü).

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi üçüncü bir sınıf eklemek için değiştir. G'nin hâlâ her sınıfın gürültüsünü doğru moda eşlediğini doğrula.
2. **(Orta)** 1-D ayarında L1'i perceptual-stil bir loss ile değiştir (örn. feature extractor olarak davranan donmuş küçük bir D). Koşullu dağılımın keskinliğini değiştirir mi?
3. **(Zor)** 1-D ayarında bir CycleGAN taslakla: iki dağılım, iki generator, cycle loss. Eşli veri olmadan ikisi arasında eşleme öğrendiğini göster.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Conditional GAN | "Etiketli GAN" | G(z, c), D(x, c). İki ağ da koşulu görür. |
| Pix2Pix | "Görsel-görsel GAN'ı" | U-Net G ve PatchGAN D + L1 loss ile eşli cGAN. |
| U-Net | "Skip'li encoder-decoder" | Simetrik conv ağı; skip'ler yüksek-freq'i korur. |
| PatchGAN | "Yerel-gerçekçilik sınıflandırıcısı" | D global skor yerine patch başına skor çıkarır. |
| CycleGAN | "Eşsiz görsel çevirisi" | İki G + cycle-consistency loss; eşli veri yok. |
| SPADE | "GauGAN" | Ara aktivasyonları semantik haritayla normalize eder; segmentation-to-image. |
| FiLM | "Feature-wise linear modulation" | Koşuldan feature başına afin dönüşüm; ucuz koşullama. |

## Üretim notu: latency-bağlı bir baseline olarak Pix2Pix

Eşli verin ve dar bir görevin (eskiz → render, semantic harita → fotoğraf, gündüz → gece) olduğunda, Pix2Pix'in tek-atış çıkarımı latency'de diffusion'ı bir büyüklük mertebesi geçer. Üretim karşılaştırması genelde:

| Yol | Adımlar | Tek L4'te 512²'de tipik latency |
|------|-------|----------------------------------------|
| Pix2Pix (U-Net forward) | 1 | ~30 ms |
| SD-Inpaint ya da SD-Img2Img | 20 | ~1.2 s |
| SDXL-Turbo Img2Img | 1-4 | ~0.15-0.35 s |
| ControlNet + SDXL base | 20-30 | ~3-5 s |

Pix2Pix statik batch'lerde throughput'ta kazanır (her istek aynı FLOPs). Diffusion kalite ve genelleştirmede kazanır. Modern oyun genelde dar görev için Pix2Pix tarzı distillation'lı bir model ve tail girdiler için bir diffusion fallback ship etmek.

## İleri Okuma

- [Mirza & Osindero (2014). Conditional Generative Adversarial Nets](https://arxiv.org/abs/1411.1784) — cGAN makalesi.
- [Isola et al. (2017). Image-to-Image Translation with Conditional Adversarial Networks](https://arxiv.org/abs/1611.07004) — Pix2Pix.
- [Zhu et al. (2017). Unpaired Image-to-Image Translation using Cycle-Consistent Adversarial Networks](https://arxiv.org/abs/1703.10593) — CycleGAN.
- [Wang et al. (2018). High-Resolution Image Synthesis with Conditional GANs](https://arxiv.org/abs/1711.11585) — Pix2PixHD.
- [Park et al. (2019). Semantic Image Synthesis with Spatially-Adaptive Normalization](https://arxiv.org/abs/1903.07291) — SPADE / GauGAN.
- [Miyato & Koyama (2018). cGANs with Projection Discriminator](https://arxiv.org/abs/1802.05637) — projection D.
