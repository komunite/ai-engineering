# Visual Autoregressive Modeling (VAR): Next-Scale Prediction

> Diffusion modelleri zamanda iteratif örnekler (denoising adımları). VAR ölçekte iteratif örnekler — önce 1x1 token tahmin eder, sonra 2x2, sonra 4x4, nihai çözünürlüğe kadar, her ölçek bir öncekine koşullanır. 2024 makalesi VAR'ın görsel üretimde GPT-stil ölçekleme yasalarına uyduğunu ve aynı compute bütçesinde DiT'yi geçtiğini gösterdi. Bu ders temel mekanizmayı inşa eder.

**Tür:** Yapım
**Diller:** Python (PyTorch ile)
**Ön koşullar:** Faz 7 Ders 03 (Multi-Head Attention), Faz 8 Ders 06 (DDPM)
**Süre:** ~90 dakika

## Sorun

Autoregressive üretim dil modellemede baskınlık kurdu çünkü öngörülebilir şekilde ölçeklenir: daha fazla compute, daha fazla parametre, daha düşük perplexity, daha iyi çıktılar. Görsel üretiminin 2024 öncesi iki ana AR girişimi vardı: PixelRNN/PixelCNN (piksel piksel) ve DALL-E 1 / Parti / MuseGAN (VQ-VAE kodları üzerinde token token).

İkisi de bir üretim-sırası probleminden muzdaripti. Pikseller ve token'lar 2D bir grid'de düzenli ama AR modeli onları 1D raster sırasında ziyaret etmek zorunda. Erken bir köşe pikseli görselin sonunda ne olacağı hakkında hiçbir fikre sahip değil. Üretim kalitesi GPT-on-text'ten daha kötü ölçekledi ve eşleşen compute'da diffusion modeli kalitesine asla ulaşamadı.

VAR üretim-sırası problemini neyin üretildiğini değiştirerek düzeltir. Görsel token'larını uzayda tek tek tahmin etmek yerine, VAR artan çözünürlüklerde bir görselin tamamını tahmin eder. Adım 1: bir 1x1 token tahmin et (genel görsel "özeti"). Adım 2: 2x2 bir token grid'i tahmin et (daha kaba feature'lar). Adım 3: 4x4 bir grid tahmin et. Adım K: nihai (H/8)x(W/8) grid'i tahmin et.

Her ölçek tüm önceki ölçeklere attend eder ("ölçek sırasında" causal) ve kendi ölçeği içinde paralel olarak. Sıra problemi kaybolur: k ölçeğindeki tüm görsel tek bir transformer pass'inde üretilir.

## Kavram

### VQ-VAE Multi-Scale Tokenizer

VAR'ın bir **multi-scale discrete tokenizer**'a ihtiyacı var. x görseli için, kademeli olarak daha yüksek çözünürlüklü token grid'leri dizisi üretir:

```
x -> encoder -> latent f
f -> 1x1'de tokenize et: (1, 1) şeklinde token grid'i z_1
f -> 2x2'de tokenize et: (2, 2) şeklinde token grid'i z_2
...
f -> (H/p)x(W/p)'de tokenize et: (H/p, W/p) şeklinde token grid'i z_K
```

Her z_k aynı codebook'u kullanır (tipik boyut 4096-16384). Her ölçekteki tokenization bağımsız değildir — her ölçekteki residual'ların toplamı f'i yeniden inşa edecek şekilde eğitilir:

```
f ≈ upsample(embed(z_1), target_size) + ... + upsample(embed(z_K), target_size)
```

Bu bir **residual VQ** varyantı. k ölçeği 1..k-1 ölçeklerinin kaçırdığını yakalar. Decoder tüm ölçek embedding'lerinin toplamını alır ve görseli üretir.

Multi-scale VQ tokenizer bir kez eğitilir (VQGAN gibi) sonra dondurulur. Tüm üretken işi üzerindeki autoregressive model yapar.

### Next-Scale Prediction

Üretken model tüm önceki ölçeklerden token'ları gören ve bir sonraki ölçekteki token'ları tahmin eden bir transformer.

Girdi dizisi yapısı:
```
[START, z_1 token'ları, z_2 token'ları, z_3 token'ları, ..., z_K token'ları]
```

Position embedding'leri hem ölçek indeksini hem de ölçek içindeki uzamsal konumu encode eder. Attention ölçek sırasında causal'dır: k ölçeğinde (i, j) konumundaki token, 1..k ölçeklerindeki tüm token'lara ve kullanılan ölçek-içi sırada daha önce gelen k ölçeğinin token'larına attend edebilir (VAR ölçek-içi causality olmadan sabit positional attention kullanır — bir ölçek içindeki tüm konumlar paralel olarak tahmin edilir).

Eğitim loss'u: her k ölçeğinde, tüm önceki-ölçek token'ları verildiğinde z_k token'larını tahmin et. Discrete VQ kodları üzerinde cross-entropy loss. "Dizinin" artık ölçek-yapılı olması dışında GPT ile aynı yapı.

### Üretim

Çıkarımda:
```
z_1 üret = p(z_1)'den örnekle                          # 1 token
z_2 üret = p(z_2 | z_1)'den örnekle                    # paralel 4 token
z_3 üret = p(z_3 | z_1, z_2)'den örnekle               # paralel 16 token
...
decode: f = embed-ve-upsample 1..K ölçeklerinin toplamı
image = VAE_decoder(f)
```

K = 10 ölçek için, üretim 10 transformer forward pass'i. Her pass tüm ölçeğini paralel üretir — ölçek içinde token başına autoregression yok. 256x256 bir görsel için bu kabaca 10 pass vs DiT'in 28-50'si.

### Next-Scale Neden Next-Token'ı Geçer

Üç yapısal zafer:
1. **Coarse-to-fine doğal görsel istatistiklerle hizalanır.** İnsan görsel algısı ve görsel dataset'leri ölçeğe bağlı düzenlilikler gösterir: düşük-frekanslı yapı kararlı ve öngörülebilir; yüksek-frekanslı detay düşük-frekanslı içeriğe koşulludur. Next-scale prediction bunu kullanır.
2. **Ölçek içinde paralel üretim.** GPT-stil token AR'ın aksine, VAR bir ölçekteki tüm token'ları tek adımda üretir. Etkili üretim uzunluğu lineer yerine log-ölçeklidir.
3. **Üretim sırası yanlılığı yok.** k ölçeğindeki token'lar k-1 ölçeğinin hepsini görür; erken token'ları geç bağlam mevcut olmadan commit etmeye zorlayan "solunda" ya da "üstünde" yanlılığı yok.

### Scaling Law

Tian et al. VAR'ın ImageNet'te FID için bir power-law ölçekleme eğrisi izlediğini gösterdi — tıpkı GPT'nin perplexity için yaptığı gibi. Parametreleri ya da compute'u ikiye katlamak güvenilir şekilde hatayı yarıya indirir. Bu, bu tür ölçekleme davranışını dil modelleri kadar temiz şekilde sergileyen ilk görsel-üretken modeldi. Sonuç olarak VAR-ölçek tahminleri mimari başına ampirik tahminler yerine compute'tan öngörülebilir hale gelir.

### Diffusion ile İlişki

VAR ve diffusion aynı veri-sıkıştırma hikayesini paylaşır: ikisi de üretim problemini daha kolay alt-problemler dizisine böler.

- Diffusion: kademeli olarak gürültü ekle, bir adımı geri almayı öğren.
- VAR: kademeli olarak çözünürlük ekle, bir sonraki ölçeği tahmin etmeyi öğren.

Problem boyunca farklı eksenler. İkisi de tractable koşullu dağılımlar verir. Ampirik olarak VAR çıkarımda daha hızlı (daha az pass, ölçek içinde tamamen paralel) ve sınıf-koşullu ImageNet'te DiT ile eşleşir ya da onu geçer. Metin-koşullu VAR (VARclip, HART) aktif bir araştırma yönü.

## İnşa Et

`code/main.py`'de şunları yapacaksın:
1. Sentetik "görsel" verisi (2D Gaussian halkaları) üzerinde minik bir **multi-scale VQ tokenizer** kur.
2. Token'ları next-scale-tahmin eden bir **VAR-stil transformer** eğit.
3. Transformer'ı 4 kez çağırarak (4 ölçek) ve decode ederek örnekle.
4. Ölçek-sıralı eğitimin üretimi ölçek içinde paralel yaptığını doğrula.

Bu bir oyuncak uygulama. Önemli olan ölçek-yapılı attention mask'i ve ölçek içinde paralel üretimi gerçekten çalışırken görmek.

## Yayınla

Bu ders `outputs/skill-var-tokenizer-designer.md` üretir — multi-scale tokenizer tasarlamak için bir skill: ölçek sayısı, ölçek oranları, codebook boyutu, residual paylaşımı, decoder mimarisi.

## Alıştırmalar

1. **Ölçek sayısı ablasyonu.** VAR'ı 4, 6, 8, 10 ölçekle eğit. Autoregressive pass sayısına karşı reconstruction kalitesini ölç. Daha fazla ölçek = daha ince residual'lar = daha iyi kalite ama daha fazla pass.

2. **Codebook boyutu.** 512, 4096, 16384 codebook boyutlarıyla tokenizer eğit. Daha büyük codebook'lar daha iyi reconstruction verir ama tahmin daha zor. Dirseği bul.

3. **Ölçek içinde paralel kontrolü.** Eğitilmiş bir VAR için, attention desenini açıkça ölç. k ölçeği içinde model ölçekler arası konumlara attend ediyor ama ölçek içinde etmiyor mu? Mask uygulamasını doğrula.

4. **VAR vs DiT ölçekleme.** Aynı ImageNet sınıf-koşullu görev için, eşleşen param bütçelerinde (örn. 33M, 130M, 458M) VAR ve DiT eğit. FID'yi compute'a karşı çiz. Her boyutta VAR DiT'in önüne çıkmalı — makalenin sonucunu küçük ölçekte çoğalt.

5. **Metin koşullaması.** VAR'ı bir metin embedding'i (CLIP pooled) ekstra koşullama girdisi olarak adaLN aracılığıyla almasına uzat. Bu HART reçetesi. Metin-hizalı örnekleme FID'sini ne kadar iyileştirir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| VAR | "Visual AutoRegressive" | VQ token grid'leri piramidi üzerinde next-scale prediction ile görsel üretimi |
| Next-scale prediction | "Daha kabayı tahmin et, sonra daha inceyi" | Model artan çözünürlük ölçeklerinde token'ları tahmin eder, tüm önceki ölçeklere koşullanır |
| Multi-scale VQ tokenizer | "Residual VQ" | Artan çözünürlükte K token grid'i üreten ve decoder tüm ölçekleri toplayan VQ-VAE |
| Ölçek k | "Piramit seviyesi k" | K çözünürlük seviyesinden biri, k=1'de 1x1'den k=K'de (H/p)x(W/p)'ye kadar |
| Ölçek içinde paralel | "Ölçek başına bir forward" | k ölçeğindeki tüm token'lar bir transformer pass'inde tahmin edilir, autoregressive değil |
| Ölçekler arası causal | "Ölçek-sıralı attention" | k ölçeğindeki token 1..k ölçeklerinin hepsine attend edebilir ama k+1..K ölçeklerine edemez |
| Residual VQ | "Additive tokenization" | Her ölçeğin token'ları daha düşük ölçeklerin bıraktığı residual'ı encode eder; decoder tüm ölçek embedding'lerini toplar |
| VAR ölçekleme yasası | "Image GPT ölçeklemesi" | FID compute'ta öngörülebilir bir power law izler, dil modellerinin perplexity'si gibi |
| HART | "Hibrit VAR + metin" | MaskGIT-stil iteratif decoding'i VAR'ın ölçek yapısıyla birleştiren metin-koşullu VAR varyantı |
| Ölçek position embedding | "(ölçek, satır, sütun) üçlüsü" | Positional encoding hem ölçek indeksini hem de ölçek içindeki uzamsal koordinatları taşır |

## İleri Okuma

- [Tian et al., 2024 — "Visual Autoregressive Modeling: Scalable Image Generation via Next-Scale Prediction"](https://arxiv.org/abs/2404.02905) — VAR makalesi, kanonik referans
- [Peebles and Xie, 2022 — "Scalable Diffusion Models with Transformers"](https://arxiv.org/abs/2212.09748) — DiT, diffusion karşılaştırma baseline'ı
- [Esser et al., 2021 — "Taming Transformers for High-Resolution Image Synthesis"](https://arxiv.org/abs/2012.09841) — VQGAN, VAR'ın multi-scale tokenizer'ının uzandığı tokenizer ailesi
- [van den Oord et al., 2017 — "Neural Discrete Representation Learning"](https://arxiv.org/abs/1711.00937) — VQ-VAE, discrete görsel tokenization temeli
- [Tang et al., 2024 — "HART: Efficient Visual Generation with Hybrid Autoregressive Transformer"](https://arxiv.org/abs/2410.10812) — metin-koşullu VAR
