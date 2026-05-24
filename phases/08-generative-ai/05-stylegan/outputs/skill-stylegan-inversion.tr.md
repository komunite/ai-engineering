---
name: stylegan-inversion
description: Gerçek bir fotoğraf üzerinde pretrained StyleGAN için inversion ve düzenleme pipeline'ı seç.
version: 1.0.0
phase: 8
lesson: 05
tags: [stylegan, inversion, editing]
---

Gerçek bir fotoğraf + pretrained StyleGAN checkpoint (FFHQ-1024, StyleGAN-XL, custom fine-tune) ve hedef düzenleme (yaş, gülümseme, poz, saç, kimlik koruma) verildiğinde, şunu çıkar:

1. Inversion yöntemi. e4e (hızlı, düşük fidelity), ReStyle (iteratif encoder), HyperStyle (hypernet), PTI (pivotal tuning) ya da doğrudan W-optimizasyonu. Fidelity vs hıza bağlı tek cümlelik gerekçe.
2. Hedef uzay. W, W+ ya da StyleSpace. Dengeler: W = en disentangled ama en düşük fidelity, W+ = katman başına w, StyleSpace = channel düzeyinde.
3. Düzenleme yönü. İsimlendirilmiş yön kaynağı: InterFaceGAN (SVM-tabanlı), StyleSpace channel'ları, GANSpace PCA ya da öğrenilmiş bir classifier.
4. Fidelity bütçesi. Identity drift'ten önce LPIPS eşiği; geri alma heuristiği.
5. Değerlendirme. ID benzerliği (ArcFace cosine), orijinale LPIPS, düzenleme gücü (hedef attribute classifier skoru).

Doğrudan Z'de düzenleme yapan herhangi bir pipeline'ı reddet (entangled). Identity kontrolleri olmadan büyük düzenlemeleri (W'de &gt;1.5 sigma) reddet. Open-domain düzenleme gereken istekleri flag'le (örn. "onu çizgi film yap") - bunlar StyleGAN değil, diffusion + IP-Adapter gerektirir.
