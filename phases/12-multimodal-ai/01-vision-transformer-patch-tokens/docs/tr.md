# Vision Transformer'lar ve Patch-Token Primitive'i

> Multimodal bir şey yapmadan önce, görselin bir transformer'ın yiyebileceği token dizisine dönüşmesi gerek. 2020 ViT makalesi buna 16x16 piksellik patch'ler, bir lineer projeksiyon ve bir position embedding ile cevap verdi. Beş yıl sonra her 2026 frontier modeli (2576px native'de Claude Opus 4.7, Gemini 3.1 Pro, Qwen3.5-Omni) hâlâ böyle başlıyor — encoder ViT'ten DINOv2'ye, oradan SigLIP 2'ye değişti, register token'ları eklendi, positional scheme 2D-RoPE oldu, ama primitive yerinde kaldı. Bu ders patch-token pipeline'ını uçtan uca okuyor ve stdlib Python'da inşa ediyor, böylece Faz 12'nin geri kalanı için "görsel token'lar" hakkında somut bir zihinsel modelin olur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, patch tokenizer + geometri hesaplayıcı)
**Ön koşullar:** Faz 7 (Transformer'lar), Faz 4 (Bilgisayarlı Görü)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- HxWx3 bir görseli doğru positional encoding ile patch token dizisine dönüştür.
- Verili (patch boyutu, çözünürlük, hidden dim, depth) için bir ViT'in dizi uzunluğunu, parametre sayısını ve FLOPs'unu hesapla.
- ViT'i 2020 araştırmasından 2026 üretimine taşıyan üç yükseltmeyi söyle: self-supervised pretraining (DINO / MAE), register token'ları ve native-resolution packing.
- Aşağı akış görev için CLS pooling, mean pooling ve register token'ları arasından seç.

## Sorun

Transformer'lar vektör dizileri üzerinde çalışır. Metin zaten bir dizidir (byte'lar ya da token'lar). Görsel ise üç renk kanallı 2D bir piksel grid'i — dizi değil. Her pikseli flatten edersen, 224x224 RGB bir görsel 150,528 token olur ve bu uzunlukta self-attention başlamadan biter (dizi uzunluğunda kuadratik).

2020 öncesi yaklaşımlar öne bir CNN feature extractor cıvatalıyordu: ResNet 2048-boyutlu vektörlerden 7x7 bir feature map üretir, o 49 token'ı bir transformer'a beslersin. Çalışıyor ama CNN'in bias'larını (translation equivariance, yerel receptive field'lar) miras alıyor ve transformer'ın ölçek iştahını kaybediyor.

Dosovitskiy et al. (2020) küt soruyu sordu: peki ya CNN'i atlasak? Görseli sabit boyutlu patch'lere (mesela 16x16 piksel) ayır, her patch'i bir vektöre lineer projekte et, bir positional embedding ekle ve diziyi düz bir transformer'a besle. O zamanlar bu sapkınlıktı — convolution olmadan görü. Yeterli veriyle (JFT-300M, sonra LAION) ImageNet'te ResNet'i yendi ve gelişmeye devam etti.

2026'ya gelindiğinde ViT primitive'i sorgulanmaz temel. Her open-weights VLM'in vision tower'ı bir descendant (DINOv2, SigLIP 2, CLIP, EVA, InternViT). Soru artık "patch kullanmalı mıyız?" değil, "hangi patch boyutu, hangi çözünürlük programı, hangi pretraining objective'i, hangi positional encoding."

## Kavram

### Token olarak patch'ler

`(H, W, 3)` shape'inde bir `x` görseli ve `P` patch boyutu verildiğinde, görseli `(H/P) x (W/P)` üst üste binmeyen patch'ler grid'ine kesersin. Her patch `P x P x 3`'lük bir piksel küpüdür. Her küpü `3 P^2` bir vektöre flatten et. Her patch'i modelin `D` hidden boyutuna eşlemek için `(3 P^2, D)` shape'inde paylaşılan bir `W_E` lineer projeksiyonu uygula.

ViT-B/16 canonical config için:
- Çözünürlük 224, patch boyutu 16 → grid 14x14 → 196 patch token.
- Her patch `16 x 16 x 3 = 768` piksel değeri, `D = 768`'e projekte edilir.
- Öğrenilebilir bir `[CLS]` token'ı ekle → dizi uzunluğu 197.

Patch projeksiyonu matematiksel olarak kernel boyutu `P`, stride `P` ve `D` output kanallı 2D bir convolution'a özdeştir. Üretim kodu da onu öyle uyguluyor — `nn.Conv2d(3, D, kernel_size=P, stride=P)`. "Lineer projeksiyon" çerçeveleme kavramsal; kernel çerçeveleme verimli.

### Positional embedding'ler

Patch'lerin doğal bir sırası yok — transformer onları bir torba gibi görür. Erken ViT'ler öğrenilebilir bir 1D positional embedding ekledi (pozisyon başına bir 768-boyutlu vektör, 197 tane). Çalışıyor ama modeli eğitim çözünürlüğüne bağlıyor: çıkarımda grid'i değiştirirsen pozisyon tablosunu interpolate etmen gerekir.

Modern vision backbone'lar 2D-RoPE (Qwen2-VL'in M-RoPE'si, SigLIP 2'nin varsayılanı) ya da factorized 2D pozisyonlar kullanır. 2D-RoPE, query ve key vektörlerini patch'in (satır, sütun) indeksine göre döndürür, böylece model rotasyon açısından göreli 2D pozisyonu çıkarır. Pozisyon tablosu yok. Model çıkarımda keyfi grid boyutlarını halleder.

### CLS token, pooled output ve register token'ları

Görsel-seviye temsil nedir? Üç seçenek bir arada yaşar:

1. `[CLS]` token. Patch dizisine öğrenilebilir bir vektör başa ekle. Tüm transformer block'larından sonra, CLS token'ının hidden state'i görsel temsilidir. BERT'ten miras. Orijinal ViT ve CLIP tarafından kullanılır.
2. Mean pool. Patch token'larının output hidden state'lerinin ortalamasını al. SigLIP, DINOv2 ve modern VLM'lerin çoğu tarafından kullanılır.
3. Register token'ları. Darcet et al. (2023), açık bir sink token'ı olmadan eğitilen ViT'lerin self-attention'ı kaçıran yüksek-norm "artifact" patch'leri geliştirdiğini gözlemledi. 4–16 öğrenilebilir register token'ı eklemek bu yükü emer ve yoğun-tahmin kalitesini (segmentasyon, derinlik) artırır. DINOv2 ve SigLIP 2 ikisi de register'larla geliyor.

Seçim aşağı akış görevleri için önemli. Sınıflandırma için CLS iyi. Patch token'larını bir LLM'e besleyen VLM'ler için pooling'i tamamen atlarsın — her patch bir LLM input token'ı olur. Register'lar handoff'tan önce atılır (içerik değil, iskele).

### Pretraining: supervised, contrastive, masked, self-distilled

2020 ViT, JFT-300M üzerinde supervised classification ile pretrain edildi. Hızla şunlar tarafından geride bırakıldı:

- CLIP (2021): 400M çift üzerinde contrastive image-text. Ders 12.02.
- MAE (2021, He et al.): patch'lerin %75'ini maskele, pikselleri yeniden inşa et. Self-supervised, saf görseller üzerinde çalışır.
- DINO (2021) / DINOv2 (2023): öğrenci-öğretmen ile self-distillation, label yok, caption yok. 2023 DINOv2 ViT-g/14 en güçlü saf görsel backbone'u ve "dense feature" kullanım durumlarının varsayılanı.
- SigLIP / SigLIP 2 (2023, 2025): sigmoid loss ve native aspect ratio için NaFlex ile CLIP. 2026 open VLM'lerindeki (Qwen, Idefics2, LLaVA-OneVision) baskın vision tower.

Pretraining seçimin backbone'un ne için iyi olduğunu belirler: CLIP/SigLIP metin ile semantik eşleştirme için, DINOv2 yoğun görsel feature'lar için, MAE aşağı akış fine-tuning'in başlangıç noktası olarak.

### Scaling yasaları

ViT scaling (Zhai et al. 2022), bir ViT'in kalitesinin model boyutu, veri boyutu ve compute'ta öngörülebilir yasalara uyduğunu gösterdi. Sabit compute'ta:
- Daha büyük model + daha çok veri → daha iyi kalite.
- Patch boyutu dizi uzunluğu vs sadakat üzerinde bir kol. Patch 14 (DINOv2/SigLIP SO400m için tipik) görsel başına patch 16'dan daha çok token verir; OCR ve yoğun görevler için daha iyi, hız için daha kötü.
- Çözünürlük diğer büyük kol. 224'ten 384'e, 512'ye geçmek neredeyse her zaman yardımcı olur, FLOPs'ta kuadratik maliyetle.

ViT-g/14 (1B param, patch 14, çözünürlük 224 → 256 token) ve SigLIP SO400m/14 (400M param, patch 14) 2026 open VLM'leri için iki beygir encoder.

### Bir ViT için parametre sayısı

Tam hesaplama `code/main.py` içinde yaşar. 224'te ViT-B/16 için:

```
patch_embed = 3 * 16 * 16 * 768 + 768  =  591k
cls + pos    = 768 + 197 * 768          =  152k
block        = 4 * 768^2 (QKVO) + 2 * 4 * 768^2 (MLP) + 2 * 2*768 (LN)
             = 12 * 768^2 + 3k          =  7.1M
12 block     = 85M
final LN     = 1.5k
toplam       ≈ 86M
```

Checkpoint'i yüklemeden önce her ViT'i böyle göz kararı hesapla. Backbone boyutu herhangi bir aşağı akış VLM'inde VRAM zeminini belirler.

### 2026 üretim config'i

2026'da open VLM'lerin çoğunun ile geldiği encoder, native çözünürlükte (NaFlex) SigLIP 2 SO400m/14. Şuna sahip:
- 400M parametre.
- Patch boyutu 14, varsayılan çözünürlük 384 → görsel başına 729 patch token.
- Görsel-seviye görevler için mean pool; VQA için 729 patch'in hepsi LLM'e akar.
- 4 register token'ı, LLM handoff'undan önce atılır.
- Native aspect ratio için görsel-seviye scaling ile 2D-RoPE.

O config'teki her karar okuyabileceğin bir makaleye geri izlenir.

## Kullan

`code/main.py` bir patch tokenizer ve geometri hesaplayıcı. (görsel H, W, patch P, hidden D, depth L) alır ve şunları raporlar:

- Patch'leme sonrası grid shape ve dizi uzunluğu.
- Sentetik 8x8 piksellik oyuncak görsel için token dizisi (flatten + project yolundan yürür).
- Patch embed, position embed, transformer block'lar ve head'e göre kırılmış parametre sayısı.
- Hedef çözünürlükte forward pass başına FLOPs.
- ViT-B/16 @ 224, ViT-L/14 @ 336, DINOv2 ViT-g/14 @ 224, SigLIP SO400m/14 @ 384 arası karşılaştırma tablosu.

Çalıştır. Parametre sayılarını yayınlanmış sayılara eşle. Patch boyutu ve çözünürlükle oyna ki token-sayı maliyetini hissedesin.

## Yayınla

Bu ders `outputs/skill-patch-geometry-reader.md` üretir. Bir ViT config'i (patch boyutu, çözünürlük, hidden dim, depth) verildiğinde, gerekçelerle birlikte bir token sayısı, parametre sayısı ve VRAM tahmini üretir. Bir VLM için vision backbone seçtiğinde bu skill'i kullan — "token'lar patladı ve LLM context'im doldu" sürprizlerini engeller.

## Alıştırmalar

1. Native 1280x720 input'ta patch boyutu 14 ile Qwen2.5-VL için patch-token dizi uzunluğunu hesapla. CLS-only temsile göre nasıl?

2. 1080p bir frame (1920x1080) patch 14'te kaç token üretir? 5 dakikalık videoda 30 FPS'te toplam kaç görsel token? Hangi maliyet sana en çok tasarruf sağlar: pooling, frame örnekleme ya da token merging?

3. Patch token'lar üzerinde mean pooling'i saf Python'da uygula. DINOv2 çıktısının 196 token'ı üzerinde mean-pool'un, modelin `forward`'ı pooled embedding istendiğinde döndürdüğüne eşleştiğini doğrula.

4. "Vision Transformers Need Registers" (arXiv:2309.16588) Bölüm 3'ü oku. İki cümlede register'ların hangi artifact'ı emdiğini ve bunun aşağı akış yoğun tahmin için neden önemli olduğunu açıkla.

5. `code/main.py`'yi patch-n'-pack'i destekleyecek şekilde değiştir: farklı çözünürlüklerde görsel listesi verildiğinde tek paketlenmiş dizi ve block-diagonal attention mask üret. Ulaştığında Ders 12.06'ya karşı doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Patch | "16x16 piksellik kare" | Input görselin sabit boyutlu üst üste binmeyen bir bölgesi; tek bir token olur |
| Patch embedding | "Lineer projeksiyon" | Flatten edilmiş patch piksellerini D-boyutlu vektörlere eşleyen paylaşılan öğrenilmiş matris (ya da stride=P ile Conv2d) |
| CLS token | "Class token" | Son hidden state'i tüm görseli temsil eden başa eklenmiş öğrenilebilir vektör; 2026'da opsiyonel |
| Register token | "Sink token" | ViT'lerin pretraining sırasında geliştirdiği yüksek-norm attention artifact'larını emen ekstra öğrenilebilir token'lar |
| Position embedding | "Pozisyonel bilgi" | Diziyi sıra-farkındalıklı yapan pozisyon başına vektör ya da rotasyon; 2D-RoPE modern varsayılan |
| Grid | "Patch grid" | Verili çözünürlük ve patch boyutu için (H/P) x (W/P) 2D patch dizisi |
| NaFlex | "Native flexible resolution" | SigLIP 2 özelliği: tek model çoklu aspect ratio ve çözünürlüğü yeniden eğitim olmadan sunar |
| Backbone | "Vision tower" | Patch-token çıktıları VLM'de LLM'e beslenen pretrained görsel encoder |
| Pooling | "Görsel-seviye özet" | Patch token'larını tek bir vektöre çevirme stratejisi: CLS, mean, attention pool ya da register tabanlı |
| Patch 14 vs 16 | "Daha ince vs daha kaba grid" | Patch 14 görsel başına daha çok token üretir, OCR için daha iyi sadakat, daha yavaş; patch 16 klasik varsayılan |

## İleri Okuma

- [Dosovitskiy et al. — An Image is Worth 16x16 Words (arXiv:2010.11929)](https://arxiv.org/abs/2010.11929) — orijinal ViT.
- [He et al. — Masked Autoencoders Are Scalable Vision Learners (arXiv:2111.06377)](https://arxiv.org/abs/2111.06377) — MAE, self-supervised pretraining.
- [Oquab et al. — DINOv2 (arXiv:2304.07193)](https://arxiv.org/abs/2304.07193) — ölçekte self-distillation, label yok.
- [Darcet et al. — Vision Transformers Need Registers (arXiv:2309.16588)](https://arxiv.org/abs/2309.16588) — register token'ları ve artifact analizi.
- [Tschannen et al. — SigLIP 2 (arXiv:2502.14786)](https://arxiv.org/abs/2502.14786) — 2026 varsayılan vision tower.
- [Zhai et al. — Scaling Vision Transformers (arXiv:2106.04560)](https://arxiv.org/abs/2106.04560) — ampirik scaling yasaları.
