# Any-Resolution Görü: Patch-n'-Pack ve NaFlex

> Gerçek görseller 224x224 kareler değil. Bir fiş 9:16, bir chart 16:9, tıbbi tarama 4096x4096 olabilir, mobil ekran görüntüsü 9:19.5. 2024 öncesi VLM cevabı — her şeyi sabit kareye resize et — OCR, belge anlama ve yüksek çözünürlüklü sahne ayrıştırmayı çalıştıran sinyali çöpe attı. NaViT (Google, 2023) tek bir transformer batch'inde değişken çözünürlüklü patch'leri block-diagonal masking ile paketleyebileceğini gösterdi. Qwen2-VL'in M-RoPE'si (2024) mutlak positional tabloları tamamen düşürdü. LLaVA-NeXT'in AnyRes'i yüksek çözünürlüklü görselleri bir base + alt görsellere tile etti. SigLIP 2'nin NaFlex varyantı (2025) artık her aspect ratio'yu sunmak isteyen açık VLM'ler için varsayılan encoder. Bu ders patch-n'-pack'i uçtan uca uyguluyor.

**Tür:** Yapım
**Diller:** Python (stdlib, patch packer + block-diagonal mask)
**Ön koşullar:** Faz 12 · 01 (ViT patch'leri), Faz 12 · 05 (LLaVA)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Değişken çözünürlüklü bir görsel batch'inden patch'leri tek diziye paketle ve block-diagonal attention mask'ı inşa et.
- Verili bir görev için AnyRes tiling (LLaVA-NeXT), NaFlex (SigLIP 2) ve M-RoPE (Qwen2-VL) arasından seç.
- Resize etmeden OCR, chart'lar ve fotoğraf için token bütçelerini hesapla.
- Kare-resize'ın üç başarısızlık modunu söyle: ezilmiş metin, kırpılmış içerik, padding'de boşa giden token.

## Sorun

Transformer'lar bir dizi bekler. Bir batch aynı uzunlukta diziler yığını. Görsellerin 224x224 ise her seferinde 196 patch token alırsın, padding gerekmez, iş tamam. 224'te eğit, 224'te çıkarım yap, çözünürlüğü bir daha düşünme.

Dünya işbirliği yapmıyor. Belgeler dikey (8.5x11 inç, 2:3'lük). Chart ekran görüntüleri yatay (16:9). Fişler uzun ve ince (1:3). Tıbbi görüntüleme 2048x2048 ya da daha büyükte gönderiliyor. Mobil cihaz ekran görüntüleri 1170x2532 (0.46:1).

2024 öncesi üç seçenek ve her biri neden başarısız:

1. Sabit kareye (224x224 ya da 336x336) resize et. Ezilme metni ve yüzleri bozar. Aşağı ölçek chart etiketlerini ve OCR içeriğini yok eder. LLaVA-1.5'e kadar standart pratik.
2. Sabit aspect ratio'ya kırp. Görselin çoğunu çöpe atıyorsun ve kırpma konumunu seçmek kendi başına bir görü sorunu.
3. En uzun kenara padle. Distortion'ı düzeltir ama dikey görseller için token'ların %50+'sını padding'e harcar. Tüm o pad token'larında kuadratik attention maliyeti.

2024-2025 cevabı: transformer'ın patch'leri görselin native çözünürlüğünde yemesine izin ver ve heterojen bir batch'i boşa giden compute olmadan tek diziye nasıl paketleyeceğini çöz.

## Kavram

### NaViT ve patch-n'-pack

NaViT (Dehghani et al., 2023) bunun ölçekte çalıştığını gösteren makaleydi. Fikir mekanik:

1. Batch'teki her görsel için, seçilen patch boyutunda (mesela 14) native patch grid'ini hesapla.
2. Her görselin patch'lerini kendi değişken-uzunluklu dizisine flatten et.
3. Batch için tüm görsellerin patch'lerini tek uzun diziye birleştir.
4. Bir block-diagonal attention mask'ı inşa et, böylece görsel A'nın patch'leri yalnızca görsel A içinde attend etsin.
5. Patch başına pozisyon bilgisini taşı (2D RoPE ya da fractional position embedding'ler).

336x336 (576 token), 224x224 (256 token) ve 448x336 (768 token) üç görsellik bir batch, 1600x1600 block-diagonal mask ile tek 1600-token diziye dönüşür. Padding yok. Boşa giden compute yok. Transformer keyfi aspect ratio'ları halleder.

NaViT eğitim sırasında fractional patch dropping de tanıttı — batch boyunca rastgele patch'lerin %50'sini düşür — bu hem regularize eder hem eğitimi hızlandırır. SigLIP 2 bunu miras aldı.

### AnyRes (LLaVA-NeXT)

LLaVA-NeXT'in AnyRes'i pragmatik alternatif. Yüksek çözünürlüklü bir görsel ve sabit bir encoder (CLIP ya da SigLIP @ 336) verildiğinde, görseli tile et:

1. Görselin aspect ratio'suna en iyi uyan önceden tanımlı bir setten — (1x1), (1x2), (2x1), (1x3), (3x1), (2x2), vb. — bir grid yerleşimi seç.
2. Tam görseli grid'e tile et; her tile 336x336 crop olur.
3. Bir thumbnail da üret: tüm görsel global-context token olarak 336x336'ya resize edilmiş.
4. Her tile'ı donmuş 336-encoder'dan kodla. Tile token'larını + thumbnail token'larını birleştir.

2x2 grid artı thumbnail'da 672x672 görsel için: 4 * 576 + 576 = 2880 görsel token. Pahalı ama etkili — LLM hem yerel detayı hem global context'i görür.

AnyRes encoder'ın donmuş ve yalnızca bir çözünürlüğü desteklediğinde tercih yolu. Büyük görseller için token sayısını patlatır (4x4 grid'de 1344x1344 görsel 9216 + 576 ≈ 9800 token, 8k LLM context'in çoğunu doldurur).

### M-RoPE (Qwen2-VL)

Qwen2-VL Multimodal Rotary Position Embedding'i tanıttı. NaViT'in fractional pozisyonları ya da AnyRes'in tile-ve-thumbnail'ı yerine, her patch 3D bir pozisyon (temporal, height, width) taşır. Query/key rotasyonları keyfi H, W ve temporal uzunluğu halleder.

M-RoPE yeniden eğitim olmadan native dinamik çözünürlük gönderir. Çıkarımda herhangi bir HxW görsel besle, patch embedder H/14 x W/14 token üretir, her token kendi (t=0, r=satır, c=sütun) pozisyonunu alır, RoPE doğru frekanslarla attention'ı döndürür, tamam. Qwen2.5-VL ve Qwen3-VL bunu sürdürür. InternVL3'ün V2PE'si modalite başına değişken kodlamayla aynı fikir.

AnyRes'in aksine M-RoPE native çözünürlükte O(H x W / P^2) token — çoklayıcı tile yükü yok. NaViT'in aksine hâlâ forward başına tek görsel bekler. Çözünürlükler arası batching hâlâ üstte patch-n'-pack gerektiriyor.

### NaFlex (SigLIP 2)

NaFlex SigLIP 2 checkpoint'inin native-flex modu. Tek model çıkarımda çoklu dizi uzunluğunu (256, 729, 1024 token) sunar. İçeride eğitim sırasında NaViT tarzı patch-n'-pack ve patch başına mutlak fractional pozisyonlar kullanır. Satış noktası: tek checkpoint, görev bazında çıkarımda token bütçeni seç.

Semantik görev (sınıflandırma, retrieval) için 256 token. OCR ya da chart anlama için 1024 token. Yeniden eğitim yok.

### Packing mask

Block-diagonal mask, çoğu implementasyonun tökezlediği yer. `i=0..B-1` görsellerini `n_i` uzunluklarıyla kapsayan `N_total` uzunluğunda paketlenmiş bir dizi için, `(N_total, N_total)` shape'inde `M` mask'i her iki indeks aynı görselin block'una düşerse 1, yoksa 0'dır. Kümülatif uzunluk listesinden inşa edebilirsin:

```
offsets = [0, n_0, n_0+n_1, ..., N_total]
M[i, j] = 1 iff there exists b where offsets[b] <= i < offsets[b+1] and offsets[b] <= j < offsets[b+1]
```

PyTorch'ta bu `torch.block_diag` ya da explicit gather ile tek satır. FlashAttention'ın variable-length yolu (`cu_seqlens`) mask'i tamamen atlar ve kümülatif-uzunluk tensor'unu doğrudan kullanarak diziler içinde attend eder — tipik batch'ler için dense mask'ten ~10x daha hızlı.

### Token bütçeleri

Stratejini görev başına seç:

- OCR / belgeler: 1024-4096 token. 1024'te SigLIP 2 NaFlex ya da AnyRes 3x3 + thumbnail.
- Chart'lar ve UI: 384-448 native'de 729-1024 token. Max pixels cap'li Qwen2.5-VL dinamik çözünürlüğü.
- Doğal fotoğraflar: 256-576 token iyidir. Aşağı akış LLM yeterince görür. İçerik yoğunluğu yüksek olduğu yere token öde.
- Video: spatial pooling sonrası frame başına 64-128 token, 2-8 FPS. Ders 12.17 bunu kapsar.

2026 üretim kuralı: görev başına bir max-pixels cap seç, o cap'e kadar native aspect ratio'da kodla, batch'i paketle ve padding'i atla. Qwen2.5-VL `min_pixels` ve `max_pixels`'ı tam bunun için açıyor.

## Kullan

`code/main.py` integer piksel koordinatlarıyla heterojen bir görsel batch'i için patch-n'-pack uygular. Şunları yapar:

- (H, W) görsel boyutları listesi alır.
- Her görselin patch boyutu 14'te patch dizi uzunluğunu hesaplar.
- Onları toplam uzunluğu `sum(n_i)` olan tek diziye paketler.
- Block-diagonal attention mask'ı (netlik için dense) inşa eder.
- Paketlenmiş maliyeti kare-resize ve AnyRes tiling ile karşılaştırır.
- Karışık bir batch için (fiş, chart, ekran görüntüsü, fotoğraf) token bütçe tablosu yazdırır.

Çalıştır. Çıkan sayılar her 2026 açık VLM'in patch-n'-pack kullanmasının nedeni.

## Yayınla

Bu ders `outputs/skill-resolution-budget-planner.md` üretir. Karışık-aspect-ratio bir iş yükü (OCR, chart'lar, fotoğraflar, video frame'leri) ve toplam-token bütçesi verildiğinde, doğru stratejiyi (NaFlex, AnyRes, M-RoPE ya da fixed-square) seçer ve istek başına konfigürasyon yayar. Bir ürün için VLM boyutlandırırken bu skill'i kullan — latency bütçelerini öldüren sessiz 10x token patlamasını engeller.

## Alıştırmalar

1. Bir fiş 600x1500 (1:2.5). Patch boyutu 14'te kaç native-çözünürlüklü token? 336'ya kare-resize sonrası kaç? Pratikte hangisi daha çok OCR doğruluğu kaybeder?

2. 256, 576, 729, 1024 uzunluklu dört görsellik bir batch için block-diagonal mask'ı inşa et. Attention matrisinin 2585x2585 olduğunu ve tam olarak `256^2 + 576^2 + 729^2 + 1024^2` non-zero girdiye sahip olduğunu doğrula.

3. Patch 14'te 1792x896 görsel için karşılaştır: (a) 336'ya kare-resize sonra kodla, (b) AnyRes 2x1 + thumbnail, (c) native'de M-RoPE. Hangisi en az token kullanır? Hangisi en çok detayı korur?

4. Fractional patch dropping uygula: paketlenmiş bir dizi verildiğinde, token'ların %50'sini uniform rastgele düşür ve buna göre block-diagonal mask'ı güncelle. Mask'in seyreklik değişimini ölç.

5. Qwen2-VL makalesinin (arXiv:2409.12191) Bölüm 3.2'sini oku. `min_pixels` ve `max_pixels`'ın ne kontrol ettiğini ve her iki sınırın neden önemli olduğunu iki cümlede betimle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Patch-n'-pack | "NaViT tarzı packing" | Farklı görsellerden değişken-uzunluklu patch dizilerini tek batch boyutuna birleştir |
| Block-diagonal mask | "Packing mask" | Her görselin patch'lerini yalnızca kendisine attend etmeye sınırlayan attention mask'ı |
| AnyRes | "LLaVA-NeXT tiling" | Yüksek-çözünürlüklü görseli sabit-boyutlu tile grid'i artı global thumbnail'a böl; her tile'ı sabit encoder'la kodla |
| NaFlex | "SigLIP 2 native-flex" | Çıkarımda yeniden eğitim olmadan 256/729/1024-token bütçeleri sunan tek SigLIP 2 checkpoint |
| M-RoPE | "Multimodal RoPE" | Pozisyon tabloları olmadan keyfi H, W, T'yi halleden 3D rotary position encoding (zaman, satır, sütun) |
| cu_seqlens | "FlashAttention packing" | FlashAttention varlen yolunun dense block-diagonal mask yerine kullandığı kümülatif-uzunluk tensor'u |
| min_pixels / max_pixels | "Çözünürlük sınırları" | Çok küçük ya da çok büyük input'larda token sayısını sınırlayan Qwen2.5-VL istek başına ayarları |
| Görsel token bütçesi | "Görsel başına kaç token" | Görsel başına yayınlanan patch token'larının kabaca sayımı; LLM'in prompt bütçesini ve attention maliyetini belirler |

## İleri Okuma

- [Dehghani et al. — Patch n' Pack: NaViT (arXiv:2307.06304)](https://arxiv.org/abs/2307.06304)
- [Wang et al. — Qwen2-VL (arXiv:2409.12191)](https://arxiv.org/abs/2409.12191)
- [Laurençon et al. — What matters when building vision-language models? (Idefics2, arXiv:2405.02246)](https://arxiv.org/abs/2405.02246)
- [Tschannen et al. — SigLIP 2 (arXiv:2502.14786)](https://arxiv.org/abs/2502.14786)
- [Qwen Team — Qwen2.5-VL Technical Report (arXiv:2502.13923)](https://arxiv.org/abs/2502.13923)
