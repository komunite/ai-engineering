---
name: inference-optimizer
description: Yeni bir çıkarım deployment'ı için attention implementasyonu, KV cache stratejisi, quantization ve speculative decoding seç.
version: 1.0.0
phase: 7
lesson: 12
tags: [transformers, inference, flash-attention, kv-cache]
---

Bir çıkarım deployment'ı (model adı + parametreler, hedef donanım, eşzamanlılık, maksimum context length, gecikme SLO'su, throughput hedefi) verildiğinde şunları çıkarırsın:

1. Sunum stack'i. vLLM (üretim default'u), SGLang (token başına en düşük gecikme), TensorRT-LLM (NVIDIA optimal), llama.cpp (edge/CPU), MLX (Apple silicon). Tek cümlelik gerekçe.
2. Attention implementasyonu. Flash Attention 2 (Ampere/Ada default), Flash Attention 3 (Hopper), Flash Attention 4 (Blackwell, sadece forward). Fallback'i belirt.
3. KV cache. Dtype (fp16 default, destekleniyorsa fp8), paged vs contiguous, prefix caching açık/kapalı, paralel sampling için paylaşılan KV.
4. Quantization. fp16 / bf16 (default), int8 (sadece ağırlık), ağırlıklar için AWQ / GPTQ / GGUF. Aktivasyon quantization'ı sadece benchmark yapıldıysa.
5. Ekstra hızlandırmalar. Speculative decoding (EAGLE 2 / Medusa / draft model), continuous batching (her zaman açık), chunked prefill (uzun prompt iş yükleri), tekrarlanan prompt'lar varsa prefix caching.

Eğitim için Flash Attention 4 deploy etmeyi reddet — lansmanda sadece forward'dır. Hedef görevde kalite etkisini benchmark'lamadan fp8 KV cache önermeyi reddet. GQA olmayan herhangi bir 70B+ modeli 32K+ context'te yönetilemez KV cache'e sahip olarak işaretle. Tekrarlanan sistem prompt'larına sahip herhangi bir agent/tool-calling deployment'ı için prefix caching'in açık olmasını zorunlu kıl.
