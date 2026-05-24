# Vision Transformer'lar (ViT)

> Görüntü bir patch grid'idir. Cümle bir token grid'idir. Aynı transformer ikisini de yer.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 05 (Tam Transformer), Faz 4 · 03 (CNN'ler), Faz 4 · 14 (Vision Transformer'lara Giriş)
**Süre:** ~45 dakika

## Sorun

2020'den önce, computer vision convolution demekti. ImageNet, COCO ve detection benchmark'larındaki her SOTA bir CNN backbone kullanıyordu. Transformer'lar dil içindi.

Dosovitskiy et al. (2020) — "An Image is Worth 16x16 Words" — convolution'ları tamamen düşürebileceğini gösterdi. Bir görüntüyü sabit boyutlu patch'lere dilimle, her patch'i lineer olarak bir embedding'e projeksiyona uğrat, diziyi vanilla transformer encoder'a besle. Yeterli ölçekte (ImageNet-21k pretraining veya daha büyük), ViT ResNet tabanlı modelleri eşleştirir veya yener.

ViT, 2026'da daha geniş bir pattern'in başlangıcıydı: bir mimari, birçok modalite. Whisper ses'i tokenize eder. ViT görüntüyü tokenize eder. Robotik için action token'ları. Video için piksel token'ları. Transformer umursamaz — ona bir dizi besle ve öğrensin.

2026'ya gelindiğinde, ViT ve torunları (DeiT, Swin, DINOv2, ViT-22B, SAM 3) vision'ın çoğuna sahip. CNN'ler hâlâ edge cihazlarda ve latency hassasiyetli görevlerde kazanıyor. Geri kalan her şeyin yığında bir yerde bir ViT'i var.

## Kavram

![Görüntü → patch'ler → token'lar → transformer](../assets/vit.svg)

### Adım 1 — patchify

`H × W × C` görüntüyü `N × (P·P·C)` düz patch dizisine böl. Tipik kurulum: `224 × 224` görüntü, `16 × 16` patch → her biri 768 değer olan 196 patch.

```
görüntü (224, 224, 3) → 16x16x3 patch'lerin 14 × 14 grid'i → her biri 768 uzunluğunda 196 vektör
```

Patch boyutu manivela. Daha küçük patch'ler = daha çok token, daha iyi çözünürlük, quadratic attention maliyeti. Daha büyük patch'ler = daha kaba, daha ucuz.

### Adım 2 — lineer embedding

Tek bir öğrenilmiş matris her düz patch'i `d_model`'a projeksiyona uğratır. Kernel boyutu `P` ve stride `P` olan bir convolution'a eşdeğer. PyTorch'ta bu literal olarak `nn.Conv2d(C, d_model, kernel_size=P, stride=P)` — 2 satırlık bir implementasyon.

### Adım 3 — `[CLS]` token öne ekle, positional embedding ekle

- Öğrenilebilir bir `[CLS]` token öne ekle. Son hidden state'i sınıflandırma için kullanılan görüntü temsilidir.
- Öğrenilebilir positional embedding'ler (ViT-orijinal) veya sinusoidal 2D (sonraki varyantlar) ekle.
- 2024+ RoPE pozisyon için 2D'ye uzandı, bazen açık embedding'ler olmadan.

### Adım 4 — standart transformer encoder

`LayerNorm → Self-Attention → + → LayerNorm → MLP → +` blokları L tane yığ. BERT'le aynı. Vision'a özgü katman yok. Makalenin pedagojik can alıcı noktası budur.

### Adım 5 — head

Sınıflandırma için: `[CLS]` hidden state al → linear → softmax. DINOv2 veya SAM için, `[CLS]`'i at, patch embedding'leri doğrudan kullan.

### Önemli olan varyantlar

| Model | Yıl | Değişiklik |
|-------|------|--------|
| ViT | 2020 | Orijinal. Sabit patch boyutu, tam global attention. |
| DeiT | 2021 | Distillation; yalnız ImageNet-1k'da eğitilebilir. |
| Swin | 2021 | Shifted window'lı hiyerarşik. Sub-quadratic maliyeti düzeltti. |
| DINOv2 | 2023 | Self-supervised (etiket yok). En iyi genel vision özellikleri. |
| ViT-22B | 2023 | 22B parametre; scaling laws uygulanır. |
| SigLIP | 2023 | ViT + dil çifti, sigmoid contrastive loss. |
| SAM 3 | 2025 | Segment anything; ViT-Large + promptlanabilir mask decoder. |

### Neden bir süre aldı

ViT, CNN'leri eşleştirmek için *çok fazla* veri ister çünkü CNN'in inductive bias'ları yok (translation invariance, yerellik). >100M etiketli görüntü veya güçlü self-supervised pretraining olmadan, CNN'ler eşleşen compute'ta hâlâ kazanır. DeiT bunu 2021'de distillation numaralarıyla düzeltti; DINOv2 bunu 2023'te self-supervision ile kalıcı olarak düzeltti.

## İnşa Et

`code/main.py`'a bak. Saf-stdlib patchify + lineer embedding + sağlık kontrolleri. Eğitim yok — herhangi bir gerçekçi ölçekte ViT PyTorch ve saatlerce GPU zamanı ister.

### Adım 1: sahte görüntü

24 × 24 RGB görüntü, `(R, G, B)` tuple satırlarının listesi olarak. 6×6 patch kullanıyoruz → 16 patch, her biri 108-d embedding vektörü.

### Adım 2: patchify

```python
def patchify(image, P):
    H = len(image)
    W = len(image[0])
    patches = []
    for i in range(0, H, P):
        for j in range(0, W, P):
            patch = []
            for di in range(P):
                for dj in range(P):
                    patch.extend(image[i + di][j + dj])
            patches.append(patch)
    return patches
```

Raster sıra: grid boyunca row-major. Her ViT bu sıralamayı kullanır.

### Adım 3: lineer embed

Her düz patch'i rastgele bir `(patch_flat_size, d_model)` matrisle çarp. `[CLS]` öne eklendikten sonra çıktı şeklinin `(N_patches + 1, d_model)` olduğunu doğrula.

### Adım 4: gerçekçi bir ViT için parametreleri say

ViT-Base için param sayısını yazdır: 12 katman, 12 head, d=768, patch=16. ResNet-50 ile karşılaştır (~25M). ViT-Base ~86M'ye iner. ViT-Large ~307M. ViT-Huge ~632M.

## Kullan

```python
from transformers import ViTImageProcessor, ViTModel
import torch
from PIL import Image

processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
model = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")

img = Image.open("cat.jpg")
inputs = processor(img, return_tensors="pt")
out = model(**inputs).last_hidden_state   # (1, 197, 768): [CLS] + 196 patch
cls_emb = out[:, 0]                       # görüntü temsili
```

**DINOv2 embedding'leri görüntü özellikleri için 2026 varsayılanıdır.** Backbone'u dondur, küçük bir head eğit. Sınıflandırma, retrieval, detection, captioning için çalışır. Meta'nın DINOv2 checkpoint'leri her metin-dışı vision görevinde CLIP'i geçer.

**Patch-size seçimi.** Küçük modeller 16×16 (ViT-B/16) kullanır. Yoğun tahmin (segmentation) 8×8 veya 14×14 (SAM, DINOv2) kullanır. Çok büyük modeller 14×14 kullanır.

## Yayınla

`outputs/skill-vit-configurator.md`'ye bak. Skill, veri seti boyutu, çözünürlük ve compute bütçesi verilen yeni bir vision görevi için bir ViT varyantı ve patch boyutu seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. Patch sayısının `(H/P) * (W/P)`'ye eşit olduğunu ve düz patch boyutunun `P*P*C`'ye eşit olduğunu doğrula.
2. **Orta.** 2D sinusoidal positional embedding'leri implement et — her patch'in `row`'u ve `col`'u için iki bağımsız sinusoidal kod, birleştirilmiş. Onları küçük bir PyTorch ViT'e besle ve CIFAR-10'da öğrenilebilir positional embedding'lere karşı doğruluğu karşılaştır.
3. **Zor.** 3 katmanlı bir ViT kur (PyTorch), 4×4 patch'lerle 1.000 MNIST görüntüsünde eğit. Test doğruluğunu ölç. Şimdi aynı 1.000 görüntüde DINOv2 pretraining ekle (basitleştirilmiş: encoder'ı mask'lenmiş patch'lerden patch embedding'lerini tahmin etmek için eğit). Doğruluk artar mı?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Patch | "Vision-transformer token'ı" | Görüntünün `P × P × C` bölgesi için piksel değerlerinden oluşan düz vektör. |
| Patchify | "Doğra + düzleştir" | Görüntüyü örtüşmeyen patch'lere dilimle, her birini vektöre düzleştir. |
| `[CLS]` token | "Görüntü özeti" | Öne eklenmiş öğrenilebilir token; son embedding'i görüntü temsilidir. |
| Inductive bias | "Modelin varsaydığı" | ViT'in CNN'lerden daha az öncesi vardır; farkı kapatmak için daha çok veri ister. |
| DINOv2 | "Self-supervised ViT" | Görüntü augmentation + momentum teacher kullanarak etiketler olmadan eğitildi. 2026'da en iyi genel görüntü özellikleri. |
| SigLIP | "CLIP'in halefi" | Sigmoid contrastive loss ile eğitilmiş ViT + metin encoder; eşleşen compute'ta CLIP'ten daha iyi. |
| Swin | "Window'lu ViT" | Local attention + shifted window'lu hiyerarşik ViT; sub-quadratic. |
| Register token'ları | "2023 numarası" | Attention sink'leri emen birkaç ekstra öğrenilebilir token; DINOv2 özelliklerini iyileştirir. |

## İleri Okuma

- [Dosovitskiy et al. (2020). An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929) — ViT makalesi.
- [Touvron et al. (2021). Training data-efficient image transformers & distillation through attention](https://arxiv.org/abs/2012.12877) — DeiT.
- [Liu et al. (2021). Swin Transformer: Hierarchical Vision Transformer using Shifted Windows](https://arxiv.org/abs/2103.14030) — Swin.
- [Oquab et al. (2023). DINOv2: Learning Robust Visual Features without Supervision](https://arxiv.org/abs/2304.07193) — DINOv2.
- [Darcet et al. (2023). Vision Transformers Need Registers](https://arxiv.org/abs/2309.16588) — DINOv2 için register-token düzeltmesi.
