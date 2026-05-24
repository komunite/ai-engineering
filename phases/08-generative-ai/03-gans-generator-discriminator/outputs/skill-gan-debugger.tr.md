---
name: gan-debugger
description: Loss eğrileri ve örnek grid'lerinden başarısız GAN eğitimini teşhis et; tek satırlık düzeltmeler reçete et.
version: 1.0.0
phase: 8
lesson: 03
tags: [gan, adversarial, debugging]
---

Başarısız bir GAN run'ı verildiğinde (D ve G loss eğrileri, örnek grid'i, veri seti boyutu, optimizer config'i), şunu çıkar:

1. Teşhis. Şu seçeneklerden tek bir kök neden: mode collapse, D çok güçlü, D çok zayıf, vanishing gradient, batch-norm sızıntısı, overfit D, learning-rate uyumsuzluğu, kötü init.
2. Kanıt. Loss eğrilerinde ya da örneklerde belirgin işarete işaret et (örn. "500. adımda D(fake) &lt; 0.05 = D çok güçlü").
3. Düzeltme. Tek bir somut değişiklik. Örnekler: `lr_D = lr_G / 2`, BN'i IN ile değiştir, D'ye spectral norm ekle, lambda=10 ile WGAN-GP'ye geç, batch size'ı 2'ye böl, D girdilerine 0.1 Gaussian noise ekle.
4. Yeniden çalıştırma protokolü. Denenecek seed'ler, yeniden değerlendirmeden önce adım sayısı, kabul kriteri (örn. "FID, 20k adımına kadar baseline'ın altına düşer").
5. Fallback. Düzeltme tek bir rerun'da oturmazsa sonra ne denenmeli. Genelde: mimariyi değiştir (StyleGAN, R3GAN) ya da veri seti çok çeşitliyse paradigma değiştir (diffusion, flow matching).

D zaten saturate olmuşken G learning rate'ini arttırmayı önermeyi reddet. Asıl başarısızlık D'de iken G'ye regularization eklemeyi reddet - önce D'yi düzelt. 100 adım içinde training collapse gösteren herhangi bir run'ı muhtemel kötü init ya da lr patlaması olarak flag'le, derin algoritmik sorun olarak değil.
