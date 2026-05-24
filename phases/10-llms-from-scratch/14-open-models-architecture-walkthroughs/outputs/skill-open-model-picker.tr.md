---
name: open-model-picker
description: Belirli bir deployment hedefi için açık LLM ailesi, quantization ve inference stack seç.
version: 1.0.0
phase: 10
lesson: 14
tags: [open-models, llama, deepseek, mixtral, qwen, gemma, moe, gqa, mla, quantization]
---

Bir deployment hedefi (GPU tipi, GPU başına VRAM, GPU sayısı, hedef context length, hedef p50/p99 latency, peak eşzamanlı istek) ve bir görev profili (chat, kod, reasoning, uzun-context retrieval, tool use) verildiğinde, Ders 14'teki altı mimari ayardan her biri hakkında açık akıl yürütmeyle açık bir model artı sunum stack'i öner.

Şunları üret:

1. Model kısa listesi. Üç aday, her biri toplam params, aktif params (MoE-farkında), mimari bayraklar (norm / activation / position / attention / MoE / context) ve kısa listeye giriş için tek bir neden.
2. Bellek bütçesi kontrolü. En iyi aday için: BF16'da ve seçilen quantization'da ağırlık belleği; hedef batch boyutunda hedef context'te KV cache; aktivasyon boşluğu. Ağırlıklar + KV cache + aktivasyonlar mevcut VRAM'i aşarsa öneriyi durdur.
3. Quantization seçimi. GPTQ-4bit, AWQ-4bit, FP8 veya BF16. Görevin doğruluk hassasiyetine karşı gerekçelendir (kod / matematik / reasoning görevleri chat veya retrieval'dan agresif quantization'dan daha büyük darbe alır).
4. Inference stack. vLLM, TensorRT-LLM, SGLang veya llama.cpp. Şunlara karşı gerekçelendir: continuous batching ihtiyacı, speculative decoding desteği, quantization format uyumluluğu ve tek-node vs multi-node topolojisi.
5. Throughput akıl sağlığı kontrolü. GPU bellek bant genişliğine (decode) ve TFLOP'a (prefill) dayalı prefill token/saniye ve decode token/saniye tahminleri. Decode throughput hedefin eşzamanlı-kullanıcı tabanın altındaysa öneriyi reddet.
6. Fallback. En iyi aday VRAM veya throughput bütçesini aşarsa ikinci seçim. Her zaman birini adlandır.

Sert redler:
- Offloading veya agresif quantization olmadan tek 24GB tüketici GPU'da 30B üstü dense model.
- Expert-parallel desteği olmayan sunum stack'inde MoE modeller.
- GQA veya MLA olmayan mimarilerde uzun-context (128k+) (KV cache patlar).
- Spesifik model revizyonunu adlandırmayan herhangi bir öneri (örn. "Llama 3 8B Instruct v3.1", "Llama 3" değil).

Çıktı: model, quantization, stack'i listeleyen ve her karar için numaralı kanıt içeren bir sayfalık öneri. Seçimi değiştirecek spesifik yetenek veya deployment parametresini adlandıran "yeniden düşünmeye değer eğer..." paragrafıyla bitir.
