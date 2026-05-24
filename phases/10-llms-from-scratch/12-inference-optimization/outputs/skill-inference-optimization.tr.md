---
name: skill-inference-optimization
description: LLM inference servisinde throughput, latency ve maliyeti teşhis et ve optimize et
version: 1.0.0
phase: 10
lesson: 12
tags: [inference, kv-cache, batching, speculative-decoding, vllm, optimization]
---

# LLM Inference Optimizasyon Deseni

İki faz: prefill (compute-bound, paralel) ve decode (memory-bound, sıralı).
Her optimizasyon bir veya her ikisini hedefler.

```
Request -> Prefill (prompt'u işle) -> Decode (token üret) -> Response
              |                            |
         Compute-bound               Memory-bound
         Optimize: fusion,           Optimize: batching,
         prefix caching              quantization, speculation
```

## Karar çerçevesi

### Adım 1: Darboğazını tespit et

İş yükün için ops:byte oranını ölç:

| ops:byte | Bound | Neyi optimize etmeli |
|----------|-------|-----------------|
| < 50 | Bellek | KV cache'i quantize et, batch boyutunu artır |
| 50-200 | Geçişli | Her ikisi önemli, batching ile başla |
| > 200 | Compute | Kernel fusion, tensor parallelism, FP8 |

### Adım 2: Motorunu seç

- **Varsayılan**: vLLM (en geniş model desteği, PagedAttention, OpenAI uyumlu API)
- **Multi-turn / structured output**: SGLang (RadixAttention prefix caching, constrained decoding)
- **Max NVIDIA throughput**: TensorRT-LLM (kernel fusion, H100'de FP8)

### Adım 3: Optimizasyonları sırayla uygula

1. **KV cache** -- her zaman açık, dezavantaj yok
2. **Continuous batching** -- her zaman açık, dezavantaj yok (vLLM/SGLang bunu varsayılan yapar)
3. **Prefix caching** -- paylaşılan system prompt'ların varsa etkinleştir (çoğu chatbot vardır)
4. **Quantization** -- INT8/FP8 KV cache belleği 2-4x azaltır, minimal kalite kaybı
5. **Speculative decoding** -- latency throughput'tan önemliyse ekle
6. **Tensor parallelism** -- model tek GPU'ya sığmadığında GPU'lara böl

## KV cache bellek formülü

```
per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_param
total = per_token * sequence_length * num_concurrent_users
```

Yaygın modeller için hızlı referans (BF16):

| Model | Token başına | 100 kullanıcı @ 4K |
|-------|-----------|----------------|
| Llama 3 8B | 32 KB | 12.5 GB |
| Llama 3 70B | 320 KB | 125 GB |
| Llama 3 405B | 504 KB | 197 GB |

## Speculative decoding kontrol listesi

- Draft model hedeften 5-10x daha küçük olmalı (örn. 70B için 8B draft)
- Anlamlı speedup için kabul oranı > %70
- Öngörülebilir metinde en iyi (kod, structured output, doğal dil)
- Yaratıcı/sampling-yoğun görevlerde en kötü (düşük temperature yardımcı olur)
- Çoğu iş yükünde EAGLE > draft-target > n-gram

## Yaygın hatalar

- Batch=1'de decode çalıştırmak (memory-bound, GPU compute'ta %95 boşta)
- Bitişik KV cache blokları tahsis etmek (PagedAttention kullan, neredeyse sıfır israfa eriş)
- İsteklerin %80'i aynı system prompt'u paylaşırken prefix caching'i görmezden gelmek
- Model ağırlıkları için GPU belleğini fazla tahsis edip KV cache'e hiçbir şey bırakmamak
- Latency'yi ölçmeden throughput ölçmek (10s TTFT'de yüksek throughput işe yaramaz)
- Yüksek temperature ile speculative decoding kullanmak (kabul oranı %50'nin altına düşer)

## İzleme kontrol listesi

- Time to first token (TTFT): prefill latency, etkileşimli kullanım için hedef < 500ms
- Inter-token latency (ITL): decode hızı, streaming için hedef < 50ms
- Throughput (token/saniye): eşzamanlı kullanıcılar boyunca toplam
- KV cache kullanımı: tahsis edilen cache'in kullanılan yüzdesi
- Batch kullanımı: iterasyon başına dolu batch slot yüzdesi
- Kuyruk derinliği: batch slot bekleyen istek
