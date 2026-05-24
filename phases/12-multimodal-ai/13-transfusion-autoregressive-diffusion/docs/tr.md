# Transfusion: Tek Transformer'da Autoregressive Metin + Diffusion Görsel

> Chameleon ve Emu3 her şeyi ayrık token'lara yatırdı. Çalışıyorlar, ama quantization bottleneck'i görünür — görsel kalitesi sürekli-uzay diffusion modellerinin altında plato yapıyor. Transfusion (Meta, Zhou et al., Ağustos 2024) tersi bahsi yapar: görselleri sürekli tut, VQ-VAE'yi tamamen düşür ve tek bir transformer'ı iki loss ile eğit. Metin token'ları next-token-prediction alır. Görsel patch'leri bir flow-matching / diffusion loss alır. İki objective aynı ağırlıkları optimize eder. Stable Diffusion 3'ün altında yatan mimari (MMDiT) yakın bir kuzen. Bu ders Transfusion tezini okur, oyuncak iki-loss bir trainer inşa eder ve tek bir transformer'ın iki işi yapmasına izin veren attention mask'ı izler.

**Tür:** Yapım
**Diller:** Python (stdlib, MNIST-ölçekli oyuncakta iki-loss trainer)
**Ön koşullar:** Faz 12 · 11 (Chameleon), Faz 8 (Generative AI)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Tek backbone üzerinde iki loss çalıştıran (metin token'larında NTP, görsel patch'lerinde diffusion MSE) bir transformer ekle.
- Görsel patch'leri boyunca bidirectional attention artı metin token'ları üzerinde causal attention'ın neden doğru mask seçimi olduğunu açıkla.
- Transfusion tarzı (sürekli görseller, diffusion loss) ile Chameleon tarzı (ayrık görseller, NTP) compute, kalite ve kod karmaşıklığında karşılaştır.
- MMDiT'in katkısını söyle: her block'ta modalite-spesifik ağırlıklar, residual stream'de joint attention.

## Sorun

Ayrık vs sürekli görsel token'lar tartışması LLM'lerden eski. Sürekli temsiller (ham pikseller, VAE latent'leri) detayı korur. Ayrık token'lar (VQ indeksleri) transformer'ın native sözcüğüne sığar ama quantization adımında detayı kaybeder.

Chameleon / Emu3 ayrık gitti: tek loss, tek mimari, ama görsel sadakati tokenizer kalitesi tarafından sınırlandı.

Diffusion modelleri sürekli gitti: olağanüstü görsel kalitesi, ama LLM'den ayrı bir model, karmaşık gürültü-program mühendisliği ve metin üretimiyle temiz entegrasyon yok.

Transfusion soruyor: ikisine birden sahip olabilir miyiz? Görselleri sürekli tut, hâlâ tek model eğit, tek gradient adımına dikilmiş iki loss kullan.

## Kavram

### İki-loss mimari

Tek bir decoder-only transformer şunları içeren bir diziyi işler:

- Metin token'ları (ayrık, BPE vocab'tan).
- Görsel patch'leri (sürekli, lineer embedding üzerinden hidden dim'e projekte edilmiş 16x16 piksel block'ları — ViT encoder'ın input'u ile aynı).
- Sürekli patch'lerin nerede yaşadığını işaretleyen `<image>` ve `</image>` etiketleri.

Forward pass bir kere çalışır. Loss token başına iki head'den birini seçer:

- Metin token'ları için: vocab-logits head'inde standart cross-entropy.
- Görsel patch'leri için: sürekli patch'lerde diffusion loss — her patch'e eklenen gürültüyü tahmin et.

Gradient paylaşılan transformer gövdesinden akar. İki loss da paylaşılan ağırlıkları eş zamanlı iyileştirir.

### Attention mask: causal metin + bidirectional görsel

Metin token'ları causal olmalı — bir metin token'ının gelecek metne attend etmesine izin veremezsin, yoksa teacher forcing kırılır. Ama görsel patch'leri bir snapshot temsil ediyor; aynı görsel block içinde birbirlerine bidirectional attend etmeliler.

Mask:

```
M[i, j] = 1 if:
  (i is text and j is text and j <= i)   # metin için causal
  OR (i is image and j is image and same_image_block(i, j))   # görsel içinde bidirectional
  OR (i is text and j is image and j < i_image_end)   # metin önceki görsellere attend eder
  OR (i is image and j is text and j < i_image_start)   # görsel önceki metne attend eder
```

Eğitim ve çıkarımda block-triangular mask olarak uygulanır.

### Transformer içinde diffusion loss

Diffusion loss standart: bir görsel patch'ine gürültü ekle, modelden gürültüyü (ya da denkliğiyle temiz patch'i) tahmin etmesini iste. Transfusion versiyonu flow matching kullanır — gürültüden temize velocity field'ı tahmin et.

Eğitim sırasında:
1. Her görsel patch x0 için rastgele timestep t örnekle.
2. Gürültü ε örnekle, xt = (1-t) * x0 + t * ε hesapla (flow matching için lineer interpolation).
3. Transformer v_theta(xt, t) tahmin eder; loss = MSE(v_theta(xt, t), ε - x0).
4. Aynı diziden metin NTP loss'ları ile birlikte backprop.

Çıkarımda üretim:
- Metin token'ları: standart autoregressive sampling.
- Görsel patch'leri: önceki metin token'larına koşullu diffusion sampling döngüsü (tipik 10-30 adım).

### MMDiT: Stable Diffusion 3'ün varyantı

Stable Diffusion 3 (Esser et al., Mart 2024) Transfusion ile aynı zaman civarında MMDiT (Multimodal Diffusion Transformer) gönderdi. Mimariler kardeş.

MMDiT'in anahtar farkları:

- Block başına modalite-spesifik ağırlıklar. Her transformer block metin token'ları vs görsel patch'leri için ayrı Q, K, V ve MLP ağırlıklarına sahip. Attention joint (cross-modality); geri kalan her şey modalite-spesifik.
- Rectified flow eğitimi. Bilinen sampling ve DDPM'den daha basit matematiğe sahip belirli bir flow-matching varyantı.
- Ölçek. MMDiT SD3 için backbone (2B ve 8B param varyantları). Transfusion makalesi 7B'ye ölçekler.

İkisi aynı çekirdek fikre yakınsar: tek transformer metinde NTP ve sürekli görsel temsillerinde diffusion çalıştırır.

### Bu Chameleon-tarzını neden yener

Görsel üretiminde sürekli-diffusion ile ayrık-NTP arasındaki kalite farkı ölçülebilir. Transfusion makalesi raporluyor:

- 7B param'da, aynı boyutta Chameleon-tarzı modeli FID'de 3-5 puan yener.
- Tokenizer eğitimi gerekmez — görsel encoder daha basit (hidden'a Linear projeksiyon, ViT'in input katmanıyla aynı).
- Çıkarım autoregressive görsel token'larının aksine görsel patch denoising'i paralelleştirebilir.

Dezavantaj: Transfusion dual-loss bir model, eğitim dinamiklerini zorlaştırıyor. Loss ağırlıklarının tune edilmesi gerekiyor. NTP ve diffusion arasında program uyumsuzluğu bir head'in baskın olmasına neden olabilir.

### Aşağıda ne oturur

Janus-Pro (Ders 12.15) anlama ve üretim için vision encoder'ı ayırarak Transfusion fikrini rafine eder — biri için SigLIP, diğeri için VQ — transformer gövdesini paylaşırken. Show-o (Ders 12.14) diffusion'ı discrete-diffusion (masked prediction) ile değiştirir. Birleştirilmiş-üretim ailesi Transfusion'dan sonra hızla dallanıyor.

Görsel yayan 2026 üretim VLM'leri — Gemini 3 Pro, GPT-5, Claude Opus 4.7'nin görsel üretim yolu — neredeyse kesinlikle bu ailenin bir descendant'ını kullanıyor. Detaylar proprietary.

## Kullan

`code/main.py` ufak bir MNIST-benzeri sorun üzerinde oyuncak bir Transfusion inşa eder:

- Metin caption'ları bir rakam (0-9) betimleyen kısa integer dizileri.
- Görseller 4x4 byte grid'leri.
- Paylaşılan-ağırlık lineer projeksiyonlar çifti transformer yerine geçer; metinde NTP loss, gürültülü patch'lerde MSE loss.
- Eğitim döngüsü iki loss'u sırayla yapar, attention mask explicit.
- Üretim tek forward pass'te bir metin caption ve 4x4 görsel üretir.

Transformer oyuncak. İki-loss tesisat, attention mask inşası ve çıkarım döngüsü gerçek artifact'lar.

## Yayınla

Bu ders `outputs/skill-two-loss-trainer-designer.md` üretir. Yeni bir multimodal eğitim görevi (metin + görsel, metin + ses, metin + video) verildiğinde, iki-loss programını (loss ağırlıkları, mask shape, paylaşılan vs modalite-spesifik block'lar) tasarlar ve implementasyon risklerini işaretler.

## Alıştırmalar

1. Bir Transfusion tarzı model %70 metin token ve %30 görsel patch eğitir. Görsel diffusion loss büyüklük olarak metin NTP loss'unun ~10 katı. Hangi loss ağırlıkları onları dengeler?

2. Bir dizi için block-triangular mask'ı uygula: `[T, T, <image>, P, P, P, P, </image>, T]`. Her girişi 0 ya da 1 işaretle.

3. MMDiT modalite-spesifik QKV ağırlıklarına sahip. Bu Transfusion'ın tamamen-paylaşılan transformer'ına göre ne parametre sayısı ek yükü ekler? 7B param'da buna değer mi?

4. Üretim: bir metin prompt verildiğinde, model 50 token için NTP çalıştırır, sonra `<image>`'a çarpar, sonra 20 denoise adımı üzerinde 256 patch'te diffusion çalıştırır. Toplam kaç forward pass?

5. SD3 makalesi Bölüm 3'ü oku. Rectified flow'u ve DDPM'den daha az çıkarım adımında neden yakınsadığını betimle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| İki-loss eğitim | "NTP + diffusion" | Tek transformer aynı gradient adımında metin token'larında cross-entropy ve sürekli görsel patch'lerinde MSE'yi optimize eder |
| Flow matching | "Rectified flow" | Gürültüden temiz veriye velocity field tahmin eden diffusion varyantı; DDPM'den daha basit matematik |
| MMDiT | "Multimodal DiT" | Stable Diffusion 3'ün mimarisi: joint attention, modalite-spesifik MLP'ler ve norm'lar |
| Block-triangular mask | "Causal metin + bidirectional görsel" | Metin boyunca causal ama görsel bölgeleri içinde bidirectional olan attention mask |
| Sürekli görsel temsili | "VQ yok" | Görsel patch'leri integer codebook indeksleri olarak değil, real-valued vektörler olarak |
| Velocity tahmini | "v-parametrelendirme" | Network çıktısı gürültünün kendisi değil, gürültü ve veri arasındaki velocity field'ı |

## İleri Okuma

- [Zhou et al. — Transfusion (arXiv:2408.11039)](https://arxiv.org/abs/2408.11039)
- [Esser et al. — Stable Diffusion 3 / MMDiT (arXiv:2403.03206)](https://arxiv.org/abs/2403.03206)
- [Peebles & Xie — DiT (arXiv:2212.09748)](https://arxiv.org/abs/2212.09748)
- [Zhao et al. — MonoFormer (arXiv:2409.16280)](https://arxiv.org/abs/2409.16280)
- [Xie et al. — Show-o (arXiv:2408.12528)](https://arxiv.org/abs/2408.12528)
