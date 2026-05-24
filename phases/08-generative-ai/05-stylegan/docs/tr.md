# StyleGAN

> Çoğu generator `z`'yi her katmana aynı anda karıştırır. StyleGAN onu ayırdı: önce `z`'yi bir ara `w`'ye eşle, sonra `w`'yi her çözünürlük seviyesinde AdaIN aracılığıyla *enjekte et*. O tek değişiklik latent uzayı çözdü ve fotorealistik yüzleri yedi yıldır çözülmüş bir problem haline getirdi.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 03 (GAN'lar), Faz 4 · 08 (Normalization), Faz 3 · 07 (CNN'ler)
**Süre:** ~45 dakika

## Sorun

Bir DCGAN, `z`'yi transposed convolution yığını üzerinden bir görsele eşler. Sorun: `z` her şeyi kontrol eder — poz, aydınlatma, kimlik, arka plan — hepsi birbirine geçmiş. `z`'nin bir ekseni boyunca hareket et, dördü de değişir. Modele "aynı kişi, farklı poz" diye soramazsın çünkü temsil bu şekilde faktörize değil.

Karras et al. (2019, NVIDIA) önerdi: `z`'yi conv katmanlarına doğrudan beslemeyi bırak. Ağ girdisi olarak sabit bir `4×4×512` tensor besle. `z ∈ Z → w ∈ W` eşlemesi yapan 8 katmanlı bir MLP öğren. `w`'yi her çözünürlükte *adaptive instance normalization* (AdaIN) aracılığıyla enjekte et: her conv feature map'i normalize et, sonra `w`'nin afin projeksiyonlarıyla ölçekle ve kaydır. Stokastik detay için (cilt gözenekleri, saç telleri) katman başına gürültü ekle.

Sonuç: `W`, "yüksek seviyeli stil" (poz, kimlik) vs "ince stil" (aydınlatma, renk) için kabaca dik eksenlere sahip. İki görsel arasında stilleri, düşük-çözünürlük seviyeleri için görsel A'nın `w`'sini ve yüksek için görsel B'nin `w`'sini kullanarak takas edebilirsin. Bu düzenlemeyi, alan-ötesi stilizasyonu ve tüm "StyleGAN-inversion" araştırma hattını açtı.

## Kavram

![StyleGAN: mapping network + AdaIN + katman başına gürültü](../assets/stylegan.svg)

**Mapping network.** `f: Z → W`, 8 katmanlı bir MLP. `Z = N(0, I)^512`. `W` Gaussian olmaya zorlanmaz — veriye uyarlı bir şekil öğrenir.

**Synthesis network.** Öğrenilmiş bir sabit `4×4×512`'den başlar. Her çözünürlük bloğu: `upsample → conv → AdaIN(w_i) → noise → conv → AdaIN(w_i) → noise`. Çözünürlükler ikiye katlanır: 4, 8, 16, 32, 64, 128, 256, 512, 1024.

**AdaIN.**

```
AdaIN(x, y) = y_scale · (x - mean(x)) / std(x) + y_bias
```

burada `y_scale` ve `y_bias` `w`'nin afin projeksiyonlarından gelir. Feature map başına normalize et, sonra yeniden stilize et. Buradaki "stil", feature map'in birinci ve ikinci dereceden istatistikleridir.

**Katman başına gürültü.** Her feature map'e eklenen tek kanallı Gaussian gürültü, öğrenilmiş kanal başına bir faktörle ölçeklenir. Global yapıyı etkilemeden stokastik detayı kontrol eder.

**Truncation trick.** Çıkarımda `z` örnekle, `w = mapping(z)` hesapla, sonra `w' = ŵ + ψ·(w - ŵ)` burada `ŵ` birçok örnek üzerindeki ortalama `w`. `ψ < 1` çeşitliliği kaliteyle takas eder. Hemen her StyleGAN demo'su `ψ ≈ 0.7` kullanır.

## StyleGAN 1 → 2 → 3

| Versiyon | Yıl | Yenilik |
|---------|------|------------|
| StyleGAN | 2019 | Mapping network + AdaIN + gürültü + progressive growing. |
| StyleGAN2 | 2020 | Weight demodulation AdaIN'i değiştirir (droplet artefaktlarını düzeltir); skip/residual mimari; path-length regularization. |
| StyleGAN3 | 2021 | Alias-free convolution + equivariant kernel'ler; piksel grid'ine yapışan texture'ı yok eder. |
| StyleGAN-XL | 2022 | Sınıf-koşullu, 1024², ImageNet. |
| R3GAN | 2024 | Daha güçlü reg ile yeniden marka; FFHQ-1024'te 20x daha az parametreyle diffusion'a olan farkı kapatır. |

2026'da StyleGAN3 şunlar için varsayılan olmaya devam eder: (a) yüksek FPS'te dar-alan fotorealizmi, (b) few-shot alan adaptasyonu (100 görselli yeni bir dataset üzerinde eğit, mapping'i dondur), (c) inversion-tabanlı düzenleme (gerçek bir fotoğrafı yeniden inşa eden `w`'yi bul, sonra o `w`'yi düzenle). Açık-alan text-to-image için araç o değil — diffusion.

## İnşa Et

`code/main.py` 1-D'de bir oyuncak "style-GAN lite" uygular: bir mapping MLP, öğrenilmiş sabit bir vektörü alan ve `w`'den türetilen scale/bias ile modüle eden bir synthesis fonksiyonu ve katman başına gürültü. `w`'yi afin-modülasyonla enjekte etmenin, `z`'yi generator'ın girdisine concatenate etmekle eşleştiğini ya da onu geçtiğini gösterir.

### Adım 1: mapping network

```python
def mapping(z, M):
    h = z
    for i in range(num_layers):
        h = leaky_relu(add(matmul(M[f"W{i}"], h), M[f"b{i}"]))
    return h
```

### Adım 2: adaptive instance normalization

```python
def adain(x, w_scale, w_bias):
    mu = mean(x)
    sd = std(x)
    x_norm = [(xi - mu) / (sd + 1e-8) for xi in x]
    return [w_scale * xi + w_bias for xi in x_norm]
```

Feature-map başına scale ve bias `w`'den lineer projeksiyon ile gelir.

### Adım 3: katman başına gürültü

```python
def add_noise(x, sigma, rng):
    return [xi + sigma * rng.gauss(0, 1) for xi in x]
```

Kanal başına sigma öğrenilebilir.

## Tuzaklar

- **Droplet artefaktları.** StyleGAN 1 feature map'lerde lekemsi bir droplet üretiyordu çünkü AdaIN ortalamayı sıfırlıyordu. StyleGAN 2'nin weight demodulation'ı bunu, aktivasyonlar yerine convolution ağırlıklarını ölçekleyerek düzeltir.
- **Texture sticking.** StyleGAN 1 ve 2'nin texture'ları nesne koordinatlarını değil piksel koordinatlarını takip ediyordu (interpolasyonda görünür). StyleGAN 3'ün alias-free convolution'ları bunu pencereli sinc filtreleriyle düzeltir.
- **Mode coverage.** Truncation `ψ < 0.7` temiz görünür ama dar bir koniden örnekler; çeşitlilik gerekiyorsa `ψ = 1.0` kullan.
- **Inversion kayıplıdır.** Gerçek bir fotoğrafı `W`'ye invert etmek genelde optimizasyon ya da bir encoder (e4e, ReStyle, HyperStyle) ile yapılır. Sonuçlar birçok iterasyonda kayar.

## Kullan

| Kullanım durumu | Yaklaşım |
|----------|----------|
| Fotorealistik insan yüzleri (anime, ürün, dar) | StyleGAN3 FFHQ / özel fine-tune |
| Bir fotoğraftan yüz düzenleme | e4e inversion + StyleSpace / InterFaceGAN yönleri |
| Face swap / reenactment | StyleGAN + encoder + harmanlama |
| Avatar pipeline'ları | Düşük-veri fine-tune için ADA'lı StyleGAN3 |
| Birkaç görselden alan adaptasyonu | Mapping network'ü dondur, synthesis'i fine-tune et |
| Çok-modlu ya da metin-koşullu üretim | Yapma — diffusion kullan |

Cevabın "bir kişinin yüzünün fotoğrafı" olduğu ürün-seviyesi demolarda, StyleGAN aynı kalite çıtasında çıkarım maliyetinde (tek forward pass, 4090'da <10ms) ve keskinlikte diffusion'ı yener.

## Yayınla

`outputs/skill-stylegan-inversion.md` olarak kaydet. Skill bir gerçek fotoğraf alır ve şunu çıkarır: inversion yöntemi (e4e / ReStyle / HyperStyle), beklenen latent loss, düzenleme bütçesi (artefaktlar önce `W`'de ne kadar hareket edebilirsin) ve bilinen-iyi düzenleme yönlerinin listesi (yaş, ifade, poz).

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi `adain_on=True` ve `adain_on=False` ile çalıştır. Sabit latent vs bozulmuş latent için çıktıların yayılımını karşılaştır.
2. **(Orta)** Mixing regularization uygula: bir eğitim batch'i için `w_a`, `w_b` hesapla ve synthesis'in ilk yarısına `w_a`, ikinci yarısına `w_b` uygula. Decoder disentangle edilmiş stilleri öğreniyor mu?
3. **(Zor)** Ön-eğitilmiş bir StyleGAN3 FFHQ modelini (ffhq-1024.pkl) al. Etiketli örnekler üzerinde SVM eğiterek "gülümseme"yi kontrol eden `w` yönünü bul; kimlik kaymadan ne kadar itebildiğini raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Mapping network | "MLP" | `f: Z → W`, 8 katman, latent geometriyi veri istatistiklerinden ayrıştırır. |
| W space | "Stil uzayı" | Mapping network'ün çıktısı; kabaca disentangle. |
| AdaIN | "Adaptive instance norm" | Feature map'i normalize et, sonra `w`-projeksiyonu ile scale + shift. |
| Truncation trick | "Psi" | `w = mean + ψ·(w - mean)`, ψ<1 çeşitliliği kaliteyle takas eder. |
| Path-length regularization | "PL reg" | `w` başına büyük görsel değişikliklerini cezalandırır; `W`'yi daha pürüzsüz yapar. |
| Weight demodulation | "StyleGAN2 düzeltmesi" | Aktivasyonlar yerine conv ağırlıklarını normalize et; droplet artefaktlarını öldürür. |
| Alias-free | "StyleGAN3'ün numarası" | Pencereli sinc filtreleri; piksel grid'ine yapışan texture'ı yok eder. |
| Inversion | "Gerçek görsel için w'yi bul" | `G(w) ≈ x` olacak şekilde `x → w` optimize et ya da encode et. |

## Üretim notu: StyleGAN neden 2026'da hâlâ ship ediliyor

4090'da StyleGAN3, 1024² bir FFHQ yüzünü 10 ms'nin altında üretir — `num_steps = 1`, VAE decode yok, cross-attention pass yok. Üretim terimleriyle bu, herhangi bir görsel generator'ı için zemin latency. Aynı çözünürlükte 50-adımlık SDXL + VAE-decode pipeline'ı ~3 saniye. Bu **300× fark**, ve dar-alan ürünleri için (avatar servisleri, ID belge pipeline'ları, stok yüz üretimi) TCO'da kazanır.

İki operasyonel sonuç:

- **Scheduler yok, batcher yok.** Hedef doluluğunda statik batch optimaldir. Sürekli batching (LLM ve diffusion için zorunlu) sıfır fayda sağlar çünkü her istek aynı FLOPs'u alır.
- **Truncation `ψ` güvenlik düğmesidir.** `ψ < 0.7` mapping network'ün aralığının dar bir konisinden örnekler. Sunum katmanının örnek varyansı üzerindeki tek manivelası budur. Tepe yükte düşük `ψ`, premium kullanıcılar için yüksek.

## İleri Okuma

- [Karras et al. (2019). A Style-Based Generator Architecture for GANs](https://arxiv.org/abs/1812.04948) — StyleGAN.
- [Karras et al. (2020). Analyzing and Improving the Image Quality of StyleGAN](https://arxiv.org/abs/1912.04958) — StyleGAN2.
- [Karras et al. (2021). Alias-Free Generative Adversarial Networks](https://arxiv.org/abs/2106.12423) — StyleGAN3.
- [Tov et al. (2021). Designing an Encoder for StyleGAN Image Manipulation](https://arxiv.org/abs/2102.02766) — e4e inversion.
- [Sauer et al. (2022). StyleGAN-XL: Scaling StyleGAN to Large Diverse Datasets](https://arxiv.org/abs/2202.00273) — StyleGAN-XL.
- [Huang et al. (2024). R3GAN: The GAN is dead; long live the GAN!](https://arxiv.org/abs/2501.05441) — modern minimal GAN reçetesi.
