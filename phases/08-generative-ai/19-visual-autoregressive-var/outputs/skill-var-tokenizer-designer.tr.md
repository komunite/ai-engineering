---
name: var-tokenizer-designer
description: Next-scale visual autoregressive görsel üretimi için multi-scale residual VQ tokenizer tasarla.
version: 1.0.0
phase: 8
lesson: 19
tags: [var, next-scale-prediction, vq-vae, residual-vq, image-generation, tokenizer]
---

Görsel hedefi (çözünürlük, channel'lar, renkli vs grayscale, veri seti boyutu, aşağı akış LM compute bütçesi, hedef FID) verildiğinde, şunu çıkar:

1. Scale schedule. 1x1'den (H/p) x (W/p)'ye kadar K çözünürlük seviyesini listele. 256x256 için varsayılan 10 ölçek, 512x512 için 14. K'yı LM'nin etkin sequence length'i (ölçek alanlarının toplamı) ve ölçek başına parallel-within-scale bütçesine karşı gerekçelendir.
2. Codebook. Tüm ölçekler boyunca tek paylaşımlı codebook boyutu V (tipik 4096 / 8192 / 16384). V'yi veri seti boyutu ve decoder kapasitesinden seç. Calibration batch'inde codebook kullanımının %50'nin üzerinde kaldığını doğrula yoksa V'yi küçült.
3. Residual paylaşımı. Ölçeklerin 1..K birlikte summed upsampled embedding'ler aracılığıyla latent'i yeniden inşa ettiğini doğrula (residual VQ). Patch size p'yi ve VAE backbone'unu belirt (VQGAN-tarzı discriminator açık / kapalı, perceptual loss ağırlığı).
4. Decoder. Summed latent'i piksellere geri eşleyen VAE decoder. VQGAN decoder, VAR-paper decoder ya da daha hafif MAGVIT-tarzı decoder'dan seç. FID hedefine ve decoder VRAM'ine karşı gerekçelendir.
5. Position embedding. Ölçek başına learned embedding ve ölçek içinde 2D sin-cos ile (scale_index, row, col) üçlüsünü doğrula. Flat 1D position'ları reddet; LM, doğru conditional'ı uygulamak için ölçek etiketine ihtiyaç duyar.

VAR için non-residual multi-scale tokenizer'ı reddet. Summed residual'lar olmadan next-scale conditional ill-defined hale gelir ve LM, paper'ın kanıtladığından farklı bir objective optimize eder. V daha küçük ölçeğin pixel count'una göre kalibre edilmediği ve codebook collapse hafifletilmediği sürece ölçek başına ayrı codebook'ları reddet. K x average-scale-area, LM'nin max sequence length'ini text conditioning için headroom'dan eksiltince aştığında next-scale prediction'ı tamamen reddet.

Örnek girdi: "ImageNet class-conditional 256x256, veri seti 1.2M, LM bütçesi 1.5B params, hedef FID 5.0 altında."

Örnek çıktı:
- Scale schedule: K=10, boyutlar 1, 2, 3, 4, 5, 6, 8, 10, 13, 16. Toplam token 671.
- Codebook: paylaşımlı, V=4096. 256'da ImageNet'te %70-80 kullanım beklenir.
- Residual paylaşımı: doğrulandı; p=16, perceptual + adversarial loss'lar ile VQGAN backbone, residual sum f'yi yeniden inşa eder.
- Decoder: VQGAN decoder, 4 upsampling bloğu, ekstra refiner yok.
- Position embedding: (scale, row, col) üçlüsü, learned scale token + ölçek içinde 2D sin-cos.
