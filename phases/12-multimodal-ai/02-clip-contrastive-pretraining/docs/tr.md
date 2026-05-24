# CLIP ve Contrastive Vision-Language Pretraining

> OpenAI'nin CLIP'i (2021) sonraki beş yılı besleyecek kadar büyük tek bir fikri kanıtladı: yalnızca gürültülü web görsel-caption çiftleri ve bir contrastive loss kullanarak bir image encoder ile bir text encoder'ı aynı vektör uzayında hizala. Sıfır supervised label. 400M çift. Ortaya çıkan embedding uzayı zero-shot sınıflandırma, image-text retrieval yapar ve her 2026 VLM'ine vision tower olarak takılır. SigLIP 2 (2025) softmax'i sigmoid ile değiştirdi ve daha düşük maliyetle CLIP'i geçti. Bu ders matematiği InfoNCE'den sigmoid pairwise loss'a yürüyor ve eğitim adımını stdlib Python'da inşa ediyor.

**Tür:** Yapım
**Diller:** Python (stdlib, InfoNCE + sigmoid loss implementasyonları)
**Ön koşullar:** Faz 12 · 01 (ViT patch'leri), Faz 7 (Transformer'lar)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Mutual information'dan InfoNCE loss'unu türet ve sayısal olarak kararlı vektörleştirilmiş bir versiyonu uygula.
- Sigmoid pairwise loss'un (SigLIP) softmax'in talep ettiği all-gather yükü olmadan batch 32768+'a neden ölçeklendiğini açıkla.
- Metin şablonları (`a photo of a {class}`) inşa edip cosine similarity üzerinde argmax alarak zero-shot ImageNet sınıflandırması çalıştır.
- CLIP / SigLIP pretraining'in sana verdiği dört kolu söyle: batch boyutu, temperature, prompt template, veri kalitesi.

## Sorun

CLIP-öncesi görü supervised'di. Etiketli dataset'ler topla (ImageNet: 1.2M görsel, 1000 sınıf), bir CNN eğit, gönder. Etiketler pahalı, etiketler etiketleyicilerin üzerinde anlaşabildiklerine bias yapıyor ve etiketler fine-tuning olmadan yeni görevlere transfer olmuyor.

Image-caption web'inde bir milyar artı gevşekçe etiketlenmiş çift bedava var. Bir golden retriever fotoğrafının "parktaki köpeğim Max" alt text'i bir gözetim sinyali taşır — metin görseli betimler. Soru: bunu kullanışlı eğitime çevirebilir misin?

CLIP'in cevabı: image-caption çiftlerini bir eşleştirme görevi olarak ele al. N görsel ve N caption'lık bir batch verildiğinde, her görseli N-1 distractor'a karşı kendi caption'ı ile eşleştirmeyi öğren. Gözetim "bu ikisi birbirine ait; bu N-1 değil." Sınıf etiketi yok. İnsan annotation'ı yok. Sadece contrastive loss.

Ortaya çıkan embedding uzayı CLIP'in eğitildiğinden fazlasını yapar. ImageNet zero-shot çalışır çünkü "a photo of a cat" hiç açıkça kedi etiketlenmemiş kedi resimlerinin yanına embed olur. Bu, her 2026 VLM'ini doğuran bahis.

## Kavram

### Dual encoder

CLIP iki kuleli:

- Image encoder `f`: ViT ya da ResNet, görsel başına D-boyutlu vektör verir.
- Text encoder `g`: küçük transformer, caption başına D-boyutlu vektör verir.

İki kule de çıktılarını birim uzunluğa normalize eder. Similarity `cos(f(x), g(y)) = f(x)^T g(y)`'dir çünkü ikisi de birim norm.

N (görsel, caption) çiftli batch için, `(N, N)` shape'inde `S` similarity matrisini inşa et:

```
S[i, j] = cos(f(x_i), g(y_j)) / tau
```

burada `tau` öğrenilen bir temperature (CLIP 0.07'ye initialize ediyor; log-uzayda öğreniliyor).

### InfoNCE loss

CLIP satırlar ve sütunlar üzerinde simetrik cross-entropy kullanır:

```
loss_i2t = CE(S, labels=identity)     # her görselin pozitifi kendi caption'ı
loss_t2i = CE(S^T, labels=identity)   # her caption'ın pozitifi kendi görseli
loss = (loss_i2t + loss_t2i) / 2
```

Bu InfoNCE. CE'deki softmax, her görseli batch'teki diğer her caption'dan daha çok kendi caption'ı ile eşleşmeye zorlar. "Negatif'ler" diğer tüm batch öğeleri. Daha büyük batch = daha çok negatif = daha güçlü sinyal. CLIP batch 32k'da eğitti; ölçek önemli.

### Temperature

`tau` softmax'in keskinliğini kontrol eder. Düşük tau → keskin dağılım, hard negative mining etkisi. Yüksek tau → yumuşak, tüm örnekler katkıda bulunur. CLIP collapse'ı engellemek için kırpılmış log(1/tau)'yu öğrenir. SigLIP 2 başlangıç tau'yu sabitler ve onun yerine öğrenilen bir bias kullanır.

### Sigmoid neden daha iyi ölçekler (SigLIP)

Softmax tüm similarity matrisinin senkronda olmasına ihtiyaç duyar. Dağıtık eğitimde her embedding'i her replica'ya all-gather etmen, sonra softmax yapman gerekir. Bu iletişim için world size'da kuadratiktir.

SigLIP softmax'i element-wise sigmoid ile değiştirir: her `(i, j)` çifti için loss "bunlar eşleşen çift mi?" ikili sınıflandırması. Pozitif sınıf etiketleri diyagonal, geri kalan her şey negatif. Loss:

```
L = -1/N sum over (i, j) [ y_ij log sigmoid(S[i,j]) + (1-y_ij) log sigmoid(-S[i,j]) ]
```

`y_ij = 1` eğer `i == j`, değilse 0. Her çiftin loss'u bağımsız. All-gather gerekmiyor. Her GPU kendi yerel bloğunu hesaplar ve toplar. SigLIP 2 batch 32k-512k'ya ucuza ölçeklenir, oysa CLIP orantılı olarak daha çok iletişime ihtiyaç duyardı.

### Zero-shot sınıflandırma

N sınıf adı verildiğinde, her sınıf için bir metin şablonu inşa et:

```
"a photo of a {class}"
```

Her şablonu text encoder ile embed et. Görselini image encoder ile embed et. Argmax cosine similarity = tahmin edilen sınıf. Hedef sınıflar üzerinde eğitim yok.

Prompt şablonları önemli. CLIP'in orijinal makalesi sınıf başına 80 şablon (düz, sanatsal, fotoğraf, tablo, vs.) kullandı ve embedding'leri ortaladı. +3 ImageNet puanı. Modern kullanım tipik olarak bir ya da iki şablon seçer.

### Linear probe ve fine-tuning

Zero-shot bir baseline. Bir linear probe (hedef sınıfların için donmuş CLIP feature'ları üstüne bir lineer katman eğit) in-domain görevlerde zero-shot'u yener. Tam fine-tuning in-domain'de linear probe'u yener ama zero-shot transfer'e zarar verebilir. Üç rejim, üç trade-off.

### SigLIP 2: NaFlex ve dense feature'lar

SigLIP 2 (2025) şunları ekler:
- NaFlex: tek model değişken aspect ratio ve çözünürlükleri halleder.
- Segmentasyon ve derinlik tahmini için daha iyi dense feature'lar, VLM'lerde donmuş backbone olarak kullanımı hedefler.
- Çok dilli: CLIP yalnızca İngilizce iken 100+ dilde eğitildi.
- 1B param ölçeği, CLIP 400M'de tepe yapmışken.

2026 open VLM'lerinde SigLIP 2 SO400m/14 varsayılan vision tower. Spesifik LAION-2B eğitim dağılımı sorgu kalıbınla eşleşen saf image-text retrieval için CLIP varsayılan olmaya devam ediyor.

### ALIGN, BASIC, OpenCLIP, EVA-CLIP

ALIGN (Google, 2021): CLIP ile aynı fikir, 1.8B çift ölçek, %90 gürültülü. Gürültülü verinin ölçeklendiğini kanıtladı. OpenCLIP (LAION): LAION-400M / 2B üzerinde CLIP'in açık reprodüksiyonu, birden çok ölçek, başvurulan open checkpoint. EVA-CLIP: masked image modeling'den initialize olur; VLM'ler için güçlü backbone. BASIC: Google'ın CLIP+ALIGN hibriti. Hepsi aynı aile, farklı veri ve tuning.

### Zero-shot tavanı

CLIP sınıfı modeller %76 ImageNet zero-shot civarında sınırlanır (CLIP-G, OpenCLIP-G). Ötesi ya çok daha büyük veri (SigLIP 2 %80+ alır) ya da mimari değişiklik (supervised head'ler, daha çok parametre) gerektirir. Benchmark doyuyor; gerçek değer aşağı akış VLM'lerinin tükettiği embedding uzayı.

## Kullan

`code/main.py` şunları uygular:

1. Bir oyuncak dual encoder (hash tabanlı görsel feature'lar, metin karakter feature'ları) böylece numpy olmadan InfoNCE shape'ini görebilirsin.
2. Saf Python'da InfoNCE loss (log-sum-exp ile sayısal kararlılık).
3. Karşılaştırma için sigmoid pairwise loss.
4. Bir zero-shot sınıflandırma rutini: bir metin prompt setine karşı cosine similarity hesapla, tahmin için argmax.

Çalıştır ve loss eğrisini izle. Mutlak sayılar oyuncak; shape gerçek bir CLIP trainer'ın yaydığıyla eşleşir.

## Yayınla

Bu ders `outputs/skill-clip-zero-shot.md` üretir. Bir görsel seti (path ile) ve hedef sınıflar listesi verildiğinde, CLIP şablonu ile metin prompt'ları inşa eder, belirtilen bir checkpoint (örn. `openai/clip-vit-large-patch14`) ile iki tarafı da embed eder ve similarity skorları ile top-1 / top-5 tahminleri döndürür. Skill, prompt listesinde olmayan sınıflar hakkında iddia yapmayı reddeder.

## Alıştırmalar

1. 4 çiftlik bir batch için InfoNCE'yi elle uygula. 4x4 similarity matrisini inşa et, softmax çalıştır, diyagonali çıkar, cross-entropy hesapla. Python implementasyonunu bu el hesabına karşı doğrula.

2. SigLIP temperature'a ek olarak bir bias parametresi `b` kullanır: `S'[i,j] = S[i,j]/tau + b`. Batch satır başına büyük sınıf dengesizliği olduğunda (pozitiften çok daha çok negatif) `b` ne rol oynar? SigLIP Bölüm 3'ü (arXiv:2303.15343) oku.

3. Kediler vs köpekler için zero-shot sınıflandırıcı inşa et. İki prompt şablonu dene: `a photo of a {class}` ve `a picture of a {class}`. 100 test görseli üzerinde doğruluğu ölç. Şablonların ensemble'ı tek olanı yener mi?

4. 512-GPU çalıştırması için batch 32k'da softmax InfoNCE vs sigmoid pairwise'in iletişim maliyetini hesapla. Hangisi O(N), hangisi O(N^2) ölçeklenir? SigLIP Bölüm 4'ü kaynak göster.

5. OpenCLIP scaling-laws makalesini (arXiv:2212.07143, Cherti et al.) oku. Figürlerden veri ölçekleme için sonuçlarını yeniden üret: sabit model boyutunda, ImageNet zero-shot doğruluğu ile eğitim veri boyutu arasındaki log-lineer ilişki nedir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| InfoNCE | "Contrastive loss" | Bir batch'in similarity matrisi üzerinde cross-entropy; her öğenin pozitifi eşli öğesi, negatifler diğer her şey |
| Sigmoid loss | "SigLIP loss" | Çift başına ikili cross-entropy; softmax yok, all-gather yok, dağıtık eğitimde ucuza ölçekler |
| Temperature | "tau" | Softmax/sigmoid öncesi logit'leri ölçekleyen scalar; dağılımın keskinliğini kontrol eder |
| Zero-shot | "no-finetune sınıflandırma" | Sınıf embedding'leri inşa etmek için metin prompt'ları kullan ve cosine similarity ile sınıflandır; hedef sınıflarda eğitim yok |
| Prompt template | "a photo of a ..." | Sınıf adı etrafındaki metin iskelesi; zero-shot doğruluğunu 1-5 puan etkiler |
| Dual encoder | "Two-tower" | Bir image encoder + bir text encoder, paylaşılan D-boyutlu uzayda çıktılar |
| Hard negative | "Zor distractor" | Pozitife yeterince benzer bir negatif, model onları ayırmak için çalışmak zorunda |
| Linear probe | "Donmuş + bir katman" | Donmuş feature'lar üstüne yalnızca bir lineer sınıflandırıcı eğit; feature kalitesini ölçer |
| NaFlex | "Native flexible resolution" | SigLIP 2'nin görselleri resize olmadan herhangi bir aspect ratio ve çözünürlükte alabilme yeteneği |
| Temperature scaling | "log-parametrelendirilmiş tau" | CLIP `log(1/tau)`'yu parametrelendiriyor ki gradyanlar davransın; sıfıra yakın tau'ya collapse'ı engellemek için kırpıyor |

## İleri Okuma

- [Radford et al. — Learning Transferable Visual Models From Natural Language Supervision (arXiv:2103.00020)](https://arxiv.org/abs/2103.00020) — CLIP makalesi.
- [Zhai et al. — Sigmoid Loss for Language Image Pre-Training (arXiv:2303.15343)](https://arxiv.org/abs/2303.15343) — SigLIP.
- [Tschannen et al. — SigLIP 2 (arXiv:2502.14786)](https://arxiv.org/abs/2502.14786) — çok dilli + NaFlex.
- [Jia et al. — ALIGN (arXiv:2102.05918)](https://arxiv.org/abs/2102.05918) — gürültülü web verisi ile ölçek.
- [Cherti et al. — Reproducible scaling laws for contrastive language-image learning (arXiv:2212.07143)](https://arxiv.org/abs/2212.07143) — OpenCLIP scaling yasaları.
