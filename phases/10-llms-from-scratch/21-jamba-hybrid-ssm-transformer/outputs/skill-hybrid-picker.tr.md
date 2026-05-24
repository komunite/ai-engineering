---
name: hybrid-picker
description: Verilen bir iş yükü için saf Transformer, Jamba-stili hibrit ve saf SSM arasında seç.
version: 1.0.0
phase: 10
lesson: 21
tags: [jamba, mamba, ssm, hybrid, long-context, memory-budget, architecture]
---

Bir iş yükü spesifikasyonu (context length profili p50/p99, görev karışımı, GPU başına bellek bütçesi, hedef throughput, kalite-vs-hız önceliği) verildiğinde, saf Transformer (+MoE +MLA), Jamba-stili hibrit ve saf Mamba arasında öner.

Şunları üret:

1. Context-length kovası. Kısa (16k altı), orta (16k-64k), uzun (64k-256k) veya ultra-uzun (256k+). İlk-pass kararını yönlendirir.
2. Mimari önerisi. Saf Transformer, 1:7 hibrit, 1:3 hibrit, 1:15 hibrit veya saf Mamba arasından seç. Context kovası artı görevin in-context-recall taleplerini kullanarak gerekçelendir.
3. Bellek bütçesi kontrolü. Hedef context'te KV cache + SSM state'i hesapla. Ağırlıkları ve aktivasyon belleğini (tipik olarak ağırlıkların ve KV cache'in üzerine 10-20 GB) hesaba kattıktan sonra hedef accelerator'a sığdığını doğrula.
4. Kalite takası açıklaması. Seçilen sparsity seviyesinin kalite maliyetini belgele. 1:7 oranının altındaki hibridler in-context retrieval'da ölçülebilir miktarda bozulur; saf Mamba bazı state-tracking görevlerinde başarısız olur.
5. Inference stack uyumluluğu. Seçilen mimarinin hedef stack (vLLM, TensorRT-LLM, SGLang, llama.cpp) tarafından desteklendiğini doğrula. Hibridler saf Transformer'lardan daha ince tooling kapsamına sahiptir.

Sert redler:
- 16k altı context için Jamba-stili hibrit. Mimari yük haklı değil.
- Reasoning-yoğun veya multi-document cross-reference görevler için saf Mamba. State-tracking sınırları ısırır.
- 1:15 altı hibrit oranları. Bunun altında in-context recall güvenilmez.
- Belirtilen accelerator'da hesaplanan bellek bütçesine sığmayan herhangi bir öneri.

Reddetme kuralları:
- İş yükü gerçekten karışık kısa ve uzun context ise, hibrit önerisini reddet ve saf Transformer'ı (mümkünse MLA ile) öner — hibridler spesifik olarak uzun-context iş yüklerinde parlar.
- Accelerator tüketici sınıfıysa (24GB veya daha az), hibrit boyut modelleri reddet ve distilled küçük bir hibrit veya quantized saf Transformer öner.
- İş yükü latency-duyarlı batch-1 generation ise ve model yeniyse (mevcut deployment yolu yok), reddet ve daha basit yol olarak speculative decoding (Faz 10 · 15) ile iyi desteklenen saf Transformer öner.

Çıktı: context kovası, mimari seçimi, hedef context'te KV cache, kalite takası açıklaması ve inference stack uyumluluğunu listeleyen bir sayfalık öneri. İlk 10k üretim isteğinde öneriyi onaylayacak spesifik uzun-context değerlendirmesini (RULER, LongBench, needle-in-haystack) adlandıran "neyi izlemeli" paragrafıyla bitir.
