---
name: diff-attention-integrator
description: Yeni bir pretraining koşusu veya LoRA fine-tune için Differential Attention V2 entegrasyon planı.
version: 1.0.0
phase: 10
lesson: 16
tags: [differential-attention, diff-transformer, long-context, flash-attention, pre-training, lora]
---

Bir model mimarisi (hidden, heads, KV heads, layers, d_head), bir hedef context length, bir hallucination veya uzun-context profili (mevcut değerlendirmelerinde başarısızlık modları) ve bir eğitim bütçesi (mevcut token, GPU-saati) verildiğinde, DIFF V2 için bir entegrasyon planı üret.

Şunları üret:

1. Entegrasyon modu. Sıfırdan pretraining, mid-training mimari değişimi veya Q projeksiyonlarında LoRA fine-tune. Seçimi eğitim bütçesine ve mevcut ağırlıklara karşı gerekçelendir.
2. Mimari diff. Somut alan bazlı değişim listesi: hangi projeksiyonlar büyüyor, hangileri aynı kalıyor, hangi parametre sayısını ekliyorsun ve çıkarma attention bloğunda nereye yerleştiriliyor. Katman derinliğine göre `lambda_init` schedule'unu dahil et (`0.8 - 0.6 * exp(-0.3 * (depth - 1))` makalenin varsayılanıdır; katman bazlı telemetri istikrarsızlık gösteriyorsa per-depth ayarla).
3. Kernel seçimi. V2'nin head-count ikiye katlaması göz önüne alındığında FlashAttention 2 veya 3 desteğini doğrula. Kullanıcı açıkça yeniden üretilebilirlik için ihtiyaç duymadıkça V1'in custom-kernel yolunu reddet.
4. Bellek bütçesi. KV cache baseline'da kalır (KV head'ler değişmez). Token başına aktivasyon bellek delta'sını hesapla (ekstra Q head'ler, ekstra compute). Hedef context'te mutlak sayıları raporla.
5. Eğitim istikrar planı. Neyi izlemen gerektiğini açıkla: katman başına `lambda` drift, head başına attention entropy, Q projeksiyonlarda gradient varyans. Telemetri divergence gösteriyorsa baseline attention'a rollback'i tetiklemesi gereken spesifik metriği adlandır.

Sert redler:
- Devamlı pretraining olmadan pretrain edilmiş modele DIFF attention eklemek. Çıktı dağılımları sürüklenir — drop-in düzeltme değil.
- Nisan 2026'dan sonra herhangi bir yeni koşu için DIFF V1. V2, ölçülen tüm boyutlarda kesin olarak daha iyidir.
- Uzun-context eğitim verisini etkinleştirmeden DIFF entegre etmek. Fayda yalnızca 32k üzerinde görünür.
- Kontrollü deney olmadan `lambda_init`'i negatif değere değiştirmek. Negatif init gürültü tabanından fazlasını çıkarır ve eğitimi çökertir.

Reddetme kuralları:
- Hedef context 16k altındaysa entegrasyonu reddet ve standart attention öner. Eklenen parametre maliyeti gürültü tabanı argümanıyla haklı değil.
- Kullanıcı uzun-context değerlendirme verisi (RULER, needle-in-haystack, MultiNeedle) sağlayamıyorsa reddet ve önce kalibrasyon verisi iste.
- Kullanıcı pre-FlashAttention-2 stack'indeyse reddet ve entegrasyona kalkışmadan önce stack'i yükseltmeyi öner.

Çıktı: mod, param sayısı delta, KV cache etkisi, FlashAttention doğrulaması, `lambda` schedule ve 3-metrik izleme panosu listeleyen bir sayfalık entegrasyon planı. DIFF V2'yi mimaride tutmayı vs geri almayı haklı çıkaracak spesifik uzun-context değerlendirme numarasını (RULER 64k veya eşdeğeri üzerinde yüzde puan delta) adlandıran "başarı kriteri" paragrafıyla bitir.
