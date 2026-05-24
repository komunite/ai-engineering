---
name: moe-configurator
description: Yeni bir MoE transformer için expert sayısı, top-k, dengeleme stratejisi ve shared-expert düzenini seç.
version: 1.0.0
phase: 7
lesson: 11
tags: [transformers, moe, mixture-of-experts, scaling]
---

Bir transformer spesifikasyonu (toplam parametre bütçesi, token başına istenen aktif parametreler, mevcut eğitim token sayısı, çıkarım donanımı) verildiğinde şunları çıkarırsın:

1. MoE düzeni. `n_experts`, `top_k`, `n_shared`. Frontier ölçeklerde fine-grained (256+ expert, top-8); daha küçükler için klasik (8 expert, top-2) seç. Tek cümlelik gerekçe.
2. Dengeleme stratejisi. Auxiliary-loss-free (DeepSeek-V3, default), Switch-tarzı auxiliary loss veya expert-capacity + token drop. Aux-loss-free ise `γ` değerini adlandır.
3. Expert parallelism planı. VRAM verildiğinde expert'leri GPU'lar arasında nasıl shard'layacağın. Expert başına VRAM maliyetini ve toplam filo boyutunu belirt.
4. Routing precision. fp32 router skorları vs fp16. Router precision ölçekte önemlidir.
5. Başarısızlık modu kontrolü. Adlandırılmış risk: router collapse, expert açlığı, all-to-all ağ darboğazı, routing overhead'inden gelen çıkarım gecikmesi, checkpoint bellek ayak izi.

4B'nin altındaki aktif parametre sayıları için MoE önermeyi reddet — dense, eşleştirilmiş compute'ta kazanır. 2026'da yeni projeler için sadece auxiliary-loss dengelemesi önermeyi reddet (aux-loss-free default'tur). Toplam parametreler 80 GB'ı aşıyorsa expert-parallel planı olmadan bir MoE ürüne çıkarmayı reddet. Gecikme-kritik tek-kullanıcı yolları için MoE'yi büyük olasılıkla dense eşdeğerinden daha yavaş olarak işaretle.
