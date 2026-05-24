---
name: nsa-integrator
description: Uzun-context pretraining koşusunda Native Sparse Attention için entegrasyon planı.
version: 1.0.0
phase: 10
lesson: 17
tags: [nsa, sparse-attention, long-context, pre-training, kernel-aligned, deepseek]
---

Bir uzun-context pretraining koşu spesifikasyonu (hedef context, base mimari, mevcut eğitim token'ı, GPU topolojisi, deployment hedefi) verildiğinde, bir NSA entegrasyon planı üret.

Şunları üret:

1. Compression block boyutu `l`. 32, 64 veya 128 seç. Hedef context'e karşı gerekçelendir: 16k-32k için `l = 32`, 64k-128k için `l = 64`, 256k+ için `l = 128`. Büyük `l` daha az sıkıştırılmış key ama daha kaba routing sinyali demek.
2. Top-k seçim sayısı. 8 ile 32 arası seç. Makalenin varsayılanı 16. Hedef görev karışımına karşı gerekçelendir: reasoning-yoğun görevler (matematik, kod) daha yüksek `k`'den faydalanır çünkü seçim precision'ı daha önemli. Retrieval-yoğun görevler daha düşük `k`'de çalışır.
3. Sliding window `W`. 256, 512 veya 1024 seç. Varsayılan 512. Yoğun yapılandırılmış içerik (kod) için local context yeterliyse daha kısa; nesir için daha uzun.
4. Gate MLP. Genişlik ve initializasyon belirt. Varsayılan: `hidden`'dan 3'e linear katman, `sigmoid` veya `softplus` activation ile. Gate ağırlıkları bir branch'ı tercih etmeye çökerse uyar — bu `l`, `k` veya `W`'nin kötü ayarlandığını gösterir.
5. Kernel seçimi. Hedef accelerator için Triton veya CUDA kernel mevcudiyetini doğrula. Inference'ta dense attention'a fallback'i reddet (NSA'nın bütün amacı decode compute tasarrufu). Yalnızca forward kernel varsa backward yoksa, pretraining'i reddet ve mevcut dense checkpoint'ler üzerinde devamlı eğitim öner.

Sert redler:
- Devamlı pretraining olmadan dense attention ile pretrain edilmiş bir modelde NSA. Inference'ta bolt-on yapılamaz.
- 16k altı hedef context. Üç-branch yükü baskındır.
- NSA kernel desteği olmayan stack'lerde inference-only deployment'lar. Bunun yerine MLA veya sliding-window attention öner.

Reddetme kuralları:
- Uzun-context değerlendirme verisi (RULER, LongBench, needle-in-haystack) mevcut değilse, reddet ve önce kalibrasyon verisi iste.
- Eğitim verisi context dağılımı kısa dizilerce baskınsa, reddet ve NSA entegre etmeden önce veri yeniden ağırlıklandırma öner.
- Accelerator A100'den eskiyse reddet — NSA'nın kernel avantajları H100/H200/MI300 bellek hiyerarşilerini varsayar.

Çıktı: `l`, `k`, `W`, gate config, kernel yolu ve hedef context'te beklenen compute tasarruflarını listeleyen bir sayfalık entegrasyon planı. NSA'yı tutmayı haklı çıkaran spesifik RULER veya LongBench numarasını (eşleşen dense-attention baseline'a karşı yüzde puan) belirten "başarı kriteri" paragrafıyla bitir. Mimari MLA veya dense GQA'ya geri alınmalıysa altındaki metrik eşiğini olan bir rollback tetikleyici dahil et.
