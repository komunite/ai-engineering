# 3D Üretimi

> 3D, 2D-to-3D kaldıracının en güçlü olduğu modalite. 2023 atılımı 3D Gaussian Splatting'di. 2024-2026 üretken itişi, tek bir prompt ya da fotoğraftan nesneler ve sahneler üretmek için multi-view diffusion + 3D yeniden inşayı üzerine katmanlar.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 4 (Görü), Faz 8 · 07 (Latent Diffusion)
**Süre:** ~45 dakika

## Sorun

3D içerik can sıkıcı:

- **Temsil.** Mesh'ler, point cloud'lar, voxel grid'leri, signed distance field (SDF), neural radiance field (NeRF), 3D Gaussian'lar. Her birinin trade-off'ları var.
- **Veri kıtlığı.** ImageNet'te 14M görsel var. En büyük temiz 3D dataset (Objaverse-XL, 2023) ~10M nesneye sahip, çoğu düşük kaliteli.
- **Bellek.** Bir 512³ voxel grid'i 128M voxel; faydalı bir sahne NeRF'i ray başına 1M örnek gerektirir. Üretim yeniden inşadan daha zor.
- **Süpervizyon.** Bir 2D görsel için piksellerin var. 3D için genelde bir avuç 2D görüntün var ve 3D'ye yükseltmen gerek.

2026 yığını iki problemi ayırır. Önce bir diffusion modeli ile *2D çoklu-görünüm görseller* üret. Sonra o görsellere bir *3D temsil* (genelde Gaussian splatting) fit et.

## Kavram

![3D üretimi: multi-view diffusion + 3D yeniden inşa](../assets/3d-generation.svg)

### Temsil: 3D Gaussian Splatting (Kerbl et al., 2023)

Bir sahneyi ~1M 3D Gaussian bulutu olarak temsil et. Her birinin 59 parametresi var: konum (3), kovaryans (6, ya da quaternion 4 + scale 3), opaklık (1), spherical-harmonics renk (derece 3'te 48, derece 0'da 3).

Rendering = projeksiyon + alpha-compositing. Hızlı (4090'da 1080p'de ~100 fps). Türevlenebilir. Ground-truth fotoğraflara karşı gradient descent ile fit edilir. Bir sahne tüketici GPU'da 5-30 dakikada fit olur.

Üzerine iki 2023-2024 yeniliği:
- **Üretken Gaussian splat'lar.** LGM, LRM, InstantMesh gibi modeller bir ya da birkaç görselden doğrudan bir Gaussian bulutu tahmin eder.
- **4D Gaussian Splatting.** Dinamik sahneler için kare başına offset'li Gaussian'lar.

### Multi-view diffusion

Bir metin prompt ya da tek görselden aynı nesnenin birden çok tutarlı görünümünü üretmek için ön-eğitilmiş bir görsel diffusion modelini fine-tune et. Zero123 (Liu et al., 2023), MVDream (Shi et al., 2023), SV3D (Stability, 2024), CAT3D (Google, 2024). Genelde nesnenin etrafında 4-16 görünüm çıkarır, Gaussian splatting ya da NeRF ile 3D'ye yükseltilir.

### Text-to-3D pipeline'ları

| Model | Girdi | Çıktı | Süre |
|-------|-------|--------|------|
| DreamFusion (2022) | metin | SDS ile NeRF | varlık başına ~1 saat |
| Magic3D | metin | mesh + texture | ~40 dk |
| Shap-E (OpenAI, 2023) | metin | implicit 3D | ~1 dk |
| SJC / ProlificDreamer | metin | NeRF / mesh | ~30 dk |
| LRM (Meta, 2023) | görsel | triplane | ~5 sn |
| InstantMesh (2024) | görsel | mesh | ~10 sn |
| SV3D (Stability, 2024) | görsel | yeni görünümler | ~2 dk |
| CAT3D (Google, 2024) | 1-64 görsel | 3D NeRF | ~1 dk |
| TripoSR (2024) | görsel | mesh | ~1 sn |
| Meshy 4 (2025) | metin + görsel | PBR mesh | ~30 sn |
| Rodin Gen-1.5 (2025) | metin + görsel | PBR mesh | ~60 sn |
| Tencent Hunyuan3D 2.0 (2025) | görsel | mesh | ~30 sn |

2025-2026 yönü: oyun motorlarına uygun PBR materyalli doğrudan text-to-mesh modeller. Multi-view diffusion ara adımı genel nesneler için hâlâ en iyi performans veren reçete.

### NeRF (bağlam için)

Neural Radiance Field (Mildenhall et al., 2020). Minik bir MLP `(x, y, z, görüntüleme yönü)` alır ve `(renk, yoğunluk)` çıkarır. Işınlar boyunca entegre ederek render et. Yeni-görünüm sentezinde kaliteyle mesh-tabanlı yöntemleri geçer ama render etmesi 100-1000x daha yavaş. Çoğu gerçek-zamanlı kullanım için Gaussian splatting'e yenildi ama araştırmada hâlâ baskın.

## İnşa Et

`code/main.py` oyuncak bir 2D "Gaussian splatting" fit uygular: sentetik bir hedef görseli (pürüzsüz bir gradient) 2D Gaussian splat'larının toplamı olarak temsil et. Hedefe eşleşmek için gradient descent ile konumları, renkleri ve kovaryansları optimize et. İki temel operasyonu görürsün: forward render (splat + alpha-composite) ve gradient descent ile fit.

### Adım 1: 2D Gaussian splat

```python
def gaussian_at(x, y, gaussian):
    px, py = gaussian["pos"]
    sigma = gaussian["sigma"]
    d2 = (x - px) ** 2 + (y - py) ** 2
    return math.exp(-d2 / (2 * sigma * sigma))
```

### Adım 2: splat'ları toplayarak render et

```python
def render(image_size, gaussians):
    img = [[0.0] * image_size for _ in range(image_size)]
    for g in gaussians:
        for y in range(image_size):
            for x in range(image_size):
                img[y][x] += g["color"] * gaussian_at(x, y, g)
    return img
```

Gerçek 3D Gaussian splatting Gaussian'ları derinliğe göre sıralar ve sırayla alpha-composite eder. Bizim 2D oyuncağımız sadece toplar.

### Adım 3: gradient descent ile fit

```python
for step in range(steps):
    pred = render(size, gaussians)
    loss = mse(pred, target)
    gradients = compute_grads(pred, target, gaussians)
    update(gaussians, gradients, lr)
```

## Tuzaklar

- **Görünüm tutarsızlığı.** 4 görünümü bağımsız üretirsen ve nesne yapısı konusunda anlaşmazlarsa, 3D fit bulanık olur. Çözüm: paylaşımlı attention'lı multi-view diffusion.
- **Arka taraf halüsinasyonu.** Tek görsel → 3D, görünmeyen tarafı icat etmek zorunda. Kalite çılgınca değişir.
- **Gaussian splat patlaması.** Kısıtsız eğitim 10M splat'a büyür ve overfit olur. Densification + pruning sezgileri (3D-GS orijinal makalesinden) zorunlu.
- **Topoloji sorunları.** Implicit field'lardan (SDF) gelen mesh'lerin genelde delikleri ya da kendileriyle kesişimleri var. Ship etmeden önce bir remesher çalıştır (örn. blender'ın voxel remesh'i).
- **Eğitim verisinin lisansı.** Objaverse'in karışık lisansları var; ticari kullanım modele göre değişir.

## Kullan

| Görev | 2026 seçimi |
|------|-----------|
| Fotoğraflardan sahne yeniden inşası | Gaussian splatting (3DGS, Gsplat, Scaniverse) |
| Oyunlar için text-to-3D nesne | Meshy 4 ya da Rodin Gen-1.5 (PBR çıktı) |
| Image-to-3D | Hunyuan3D 2.0, TripoSR, InstantMesh |
| Birkaç görselden yeni-görünüm sentezi | CAT3D, SV3D |
| Dinamik sahne yeniden inşası | 4D Gaussian Splatting |
| Avatar / giyimli insan | Gaussian Avatar, HUGS |
| Araştırma / SOTA | Geçen hafta ne çıktıysa |

Bir oyun ya da e-ticaret pipeline'ında üretim 3D ship etmek için: Meshy 4 ya da Rodin Gen-1.5 doğrudan Unity / Unreal'a giden PBR mesh'ler çıkarır.

## Yayınla

`outputs/skill-3d-pipeline.md` olarak kaydet. Skill bir 3D brief'i (girdi: metin / bir görsel / birkaç görsel; çıktı: mesh / splat / NeRF; kullanım: render / oyun / VR) alır ve şunu çıkarır: pipeline (multi-view diffusion + fit ya da doğrudan mesh modeli), baz model, iterasyon bütçesi, topoloji son-işleme, gereken materyal kanalları.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi 4, 16, 64 Gaussian ile çalıştır. Hedefe karşı nihai MSE'yi raporla.
2. **(Orta)** Renkli Gaussian'lara (RGB) uzat. Yeniden inşanın hedef renk desenini eşlediğini doğrula.
3. **(Zor)** gsplat ya da Nerfstudio kullanarak 50 fotoğraflık bir çekimden gerçek bir nesneyi yeniden inşa et. Fit süresini ve held-out görünümlerde nihai SSIM'i raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| 3D Gaussian Splatting | "3DGS" | 3D Gaussian bulutu olarak sahne; türevlenebilir alpha-composite render. |
| NeRF | "Neural radiance field" | 3D noktada renk + yoğunluk çıkaran MLP; ışın entegrasyonuyla render. |
| Triplane | "Üç 2-D düzlem" | 3D'yi üç 2-D eksen-hizalı feature grid'e faktörize et; hacimselden daha ucuz. |
| SDS | "Score distillation sampling" | 2D-diffusion score'unu pseudo-gradient olarak kullanarak 3D model eğit. |
| Multi-view diffusion | "Aynı anda birçok görünüm" | Tutarlı kamera görünümleri batch'i çıkaran diffusion modeli. |
| PBR | "Fiziksel-tabanlı rendering" | Albedo, roughness, metallic, normal kanallı materyal. |
| Densification | "Splat'ları büyüt" | 3DGS eğitim sezgisi: yüksek-gradient bölgelerde splat'ları böl / klonla. |

## Üretim notu: 3D'nin henüz paylaşılan bir alt zemini yok

Görsel (latent diffusion + DiT) ve video (spatiotemporal DiT) aksine, 3D'nin 2026'da tek baskın bir runtime'ı yok. Üretim karar ağacı temsile göre dallanır:

- **NeRF / triplane.** Çıkarım ray-marching + örnek başına bir MLP forward'ı. 512² render milyonlarca MLP forward'ı gerektirir. Ray örneklerini agresif batch'le; SDPA/xformers uygulanır.
- **Multi-view diffusion + LRM yeniden inşası.** İki aşamalı pipeline. Aşama 1 (multi-view DiT) Ders 07'deki gibi bir diffusion sunucusu. Aşama 2 (LRM transformer) görünümler üzerinde tek-atış forward pass. Genel latency profili "diffusion + tek-atış" — aşama başına servis primitif'lerini buna göre seç.
- **SDS / DreamFusion.** Varlık başına optimizasyon, çıkarım değil. Build job'ları, istek handler'ları değil.

Çoğu 2026 ürünü için doğru cevap "istek üzerine multi-view diffusion modelini çalıştır, asenkron olarak 3DGS'ye yeniden inşa et, gerçek-zamanlı görüntüleme için 3DGS'yi sun". Bu, iş yükünü bir GPU-çıkarım sunucusu (hızlı) ile bir offline optimizer (yavaş) arasında temiz şekilde böler.

## İleri Okuma

- [Mildenhall et al. (2020). NeRF: Representing Scenes as Neural Radiance Fields](https://arxiv.org/abs/2003.08934) — NeRF.
- [Kerbl et al. (2023). 3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://arxiv.org/abs/2308.04079) — 3DGS.
- [Poole et al. (2022). DreamFusion: Text-to-3D using 2D Diffusion](https://arxiv.org/abs/2209.14988) — SDS.
- [Liu et al. (2023). Zero-1-to-3: Zero-shot One Image to 3D Object](https://arxiv.org/abs/2303.11328) — Zero123.
- [Shi et al. (2023). MVDream](https://arxiv.org/abs/2308.16512) — multi-view diffusion.
- [Hong et al. (2023). LRM: Large Reconstruction Model for Single Image to 3D](https://arxiv.org/abs/2311.04400) — LRM.
- [Gao et al. (2024). CAT3D: Create Anything in 3D with Multi-View Diffusion Models](https://arxiv.org/abs/2405.10314) — CAT3D.
- [Stability AI (2024). Stable Video 3D (SV3D)](https://stability.ai/research/sv3d) — SV3D.
