---
name: deepseek-v3-reader
description: Bir DeepSeek ailesi config'ini oku ve bileşen bazlı bir mimari analiz üret.
version: 1.0.0
phase: 10
lesson: 20
tags: [deepseek-v3, deepseek-r1, mla, moe, mtp, dualpipe, architecture]
---

Bir DeepSeek ailesi model (V3, R1 veya herhangi bir türevi) ve onun config'i (hidden_size, layers, num_experts, kv_lora_rank, vb.) verildiğinde, modeli bileşene göre parçalayan ve hangi DeepSeek'e özgü innovasyonları kullandığını tespit eden bir mimari analiz üret.

Şunları üret:

1. Alan bazlı config okuma. Her alan için, eşleştiği bileşeni ve katkıda bulunduğu parametre sayısını adlandır. Format: `field_name: value → interpretation → parameter contribution`.
2. Parametre dökümü. Toplam parametreler, aktif parametreler, aktif oran. Embedding, katman başına attention, katman başına MLP (dense vs expert), router, MTP modülü, LM head, RMSNorm toplam olarak böl.
3. Hedef context'te KV cache. BF16 ve FP8 değerlerini raporla. Aynı context ve hidden size'da Llama-3 tarzı GQA(8/128) baseline ile karşılaştırma dahil et.
4. İnnovasyon kontrol listesi. MLA, MTP, aux-loss-free routing, DualPipe'tan her biri için, modelin onu kullanıp kullanmadığını ve config/makalede bunun nerede görünür olduğunu tespit et.
5. Akıl sağlığı kontrolü. Modelin inference bellek bütçesini (ağırlıklar + KV cache + aktivasyonlar) spesifik bir deployment hedefinde (H100 80GB, H200 141GB, MI300X 192GB, tek node vs multi-node) hesapla. Sığıp sığmadığını ve hangi quantization'ın gerekeceğini raporla.

Sert redler:
- DeepSeek-V3'ü GPT-sınıfı dense modellerle karıştıran herhangi bir analiz. Mimari maddeten farklı.
- Context length belirtmeden MLA'nın GQA'dan hızlı olduğunu iddia etmek. Kısa context'te (4k altı) karşılaştırılabilirler; MLA uzun context'te kazanır.
- MTP'yi speculative decoding'in yerine geçen bir şey olarak yorumlamak. O bir pretraining hedefi olup aynı zamanda draft görevi de görür.

Reddetme kuralları:
- Sağlanan config `kv_lora_rank`, `num_experts` veya `first_k_dense_layers` eksikse, reddet — bu bir DeepSeek ailesi modeli değil.
- Kullanıcı tam yayımlanmış parametre sayısı eşleşmesi (en yakın 100M'e) isterse, reddet ve yayımlanmış numaranın basitleştirilmiş bir hesaplayıcının tam olarak yeniden üretmediği implementasyona özgü yapısal parametreler içerdiğini açıkla. Onları makalenin Bölüm 2 ek'ine yönlendir.
- Hedef deployment hedefi bir tüketici GPU (24GB veya daha az) ise, reddet ve bunun yerine quantize edilmiş distilled bir DeepSeek-ailesi türevi öner.

Çıktı: alanları, parametre dökümünü, KV cache'i, innovasyon kontrol listesini ve deployment uyumunu listeleyen bir sayfalık mimari analiz. Analizin yüzeye çıkardığı soruya bağlı olarak NSA (Faz 10 · 17), V2 makalesinden MLA ablation'ları veya V3 teknik raporunun Bölüm 2 ek'inden birini adlandıran "sıradaki okuma" paragrafıyla bitir.
