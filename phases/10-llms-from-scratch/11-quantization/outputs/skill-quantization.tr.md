---
name: skill-quantization
description: Donanım, kalite ve latency kısıtlamalarına göre LLM'leri deploy ederken doğru quantization stratejisini seç
version: 1.0.0
phase: 10
lesson: 11
tags: [quantization, inference, deployment, optimization, fp8, int4, int8, gptq, awq, gguf]
---

# Quantization Karar Çerçevesi

Bir dil modelini deploy ederken, doğru sayı formatını, quantization yöntemini ve kalite doğrulama stratejisini seçmek için bu çerçeveyi kullan.

## Girdi Gereksinimleri

Şunu sağla:
- **Model** (ad, parametre sayısı, orijinal precision)
- **Hedef donanım** (GPU modeli/VRAM, CPU, Apple Silicon, edge cihazı)
- **Latency hedefi** (token/saniye, ilk token'a kadar geçen süre)
- **Kalite tabanı** (max kabul edilebilir perplexity artışı, benchmark delta)
- **Sunum deseni** (batch boyutu, max context length, eşzamanlı kullanıcı)

## Hızlı Seçim

| Durumun | Format | Yöntem | Beklenen Kalite Kaybı |
|---------------|--------|--------|----------------------|
| H100 GPU, maksimum throughput | FP8 E4M3 | Native H100 casting | < %0.1 |
| A100/A10, 2x throughput gerekli | INT8 | LLM.int8() veya SmoothQuant | < %0.5 |
| Tek 24GB GPU, 70B model | INT4 | AWQ veya GPTQ | %1-3 |
| MacBook / Apple Silicon | INT4 GGUF | llama.cpp ile Q4_K_M | %1-2 |
| Mobil / edge cihaz | INT4 veya INT3 | QAT + cihaza özgü | %2-5 |
| Maksimum sıkıştırma, biraz kayıp OK | INT2 | QuIP# veya AQLM | %5-15 |
| Eğitim (mixed precision) | BF16 + FP32 accum | Native framework desteği | %0 |

## Bileşene Göre Precision Seçimi

Tüm tensor'lar aynı muameleyi görmemeli.

| Bileşen | Güvenli Minimum | Önerilen | Kaçın |
|-----------|-------------|-------------|-------|
| FFN ağırlıkları | INT4 | INT4 (AWQ/GPTQ) | QAT olmadan INT2 |
| Attention ağırlıkları | INT4 | INT8 veya FP8 | INT2 |
| Embedding katmanı | INT8 | FP16 (orijinali koru) | INT4 |
| Output head | INT8 | FP16 (orijinali koru) | INT4 |
| KV cache | FP8 | FP8 veya INT8 | Uzun context'te INT4 |
| Attention logit'leri | FP16 | FP16 veya BF16 | INT8 |
| Aktivasyonlar (inference) | INT8 | FP8 veya INT8 | INT4 |

## Yöntem Karşılaştırması

### GPTQ
- **Ne zaman:** GPU inference, Hugging Face uyumlu model istiyorsun
- **Calibration verisi:** her biri 2048 token olan 128 örnek
- **Süre:** A100'de 70B için 30-60 dakika
- **Araçlar:** `auto-gptq`, `exllama`, `exllamav2`
- **Güç:** İyi test edilmiş, Hugging Face'te büyük model zoo
- **Zayıflık:** AWQ'dan uygulanması yavaş, bazı modellerde AWQ'dan biraz düşük kalite

### AWQ
- **Ne zaman:** GPU inference, bit başına en iyi kalite istiyorsun
- **Calibration verisi:** 128 örnek
- **Süre:** A100'de 70B için 15-30 dakika
- **Araçlar:** `autoawq`, `vLLM` (native destek)
- **Güç:** En iyi INT4 kalitesi, hızlı uygulama, vLLM entegrasyonu
- **Zayıflık:** GPTQ'dan küçük model zoo

### GGUF
- **Ne zaman:** CPU inference, Apple Silicon, llama.cpp ekosistemi
- **Varyantlar:** Q2_K, Q3_K_S/M/L, Q4_K_S/M, Q5_K_S/M, Q6_K, Q8_0, F16
- **Önerilen varsayılan:** Q4_K_M (en iyi kalite/boyut dengesi)
- **Araçlar:** `llama.cpp`, `ollama`, `LM Studio`
- **Güç:** Kendi içinde dosyalar, mixed precision, devasa ekosistem
- **Zayıflık:** GPU için optimal değil (CPU/Metal için tasarlandı)

### SmoothQuant
- **Ne zaman:** GPU'da INT8, hem weight hem activation quantization gerekli
- **Anahtar fikir:** Per-channel scaling ile quantization zorluğunu activation'lardan weight'lere taşı
- **Araçlar:** `smoothquant`, `TensorRT-LLM`
- **Güç:** 2x speedup için W8A8'i (hem weight hem activation INT8) etkinleştirir
- **Zayıflık:** Yalnızca INT8, INT4'e uzanmaz

## Kalite Doğrulama Protokolü

Quantize ettikten sonra, deploy etmeden önce doğrula:

1. **Perplexity testi.** WikiText-2 veya domain corpus'unda hesapla. Delta < 0.5 mükemmel, 0.5-1.0 iyi, > 2.0 problem.

2. **Benchmark sweep.** MMLU (genel), GSM8K (matematik), HumanEval (kod) çalıştır. Matematik ve kod precision kaybına en duyarlı.

3. **Çıktı karşılaştırması.** Hem orijinal hem quantized modelden 100 yanıt üret. Kazanma oranını hesaplamak için LLM-as-judge kullan. Hedef: quantized model > %90 promptta kazansın veya berabere kalsın.

4. **Latency ölçümü.** Batch boyutu 1 ve hedef batch boyutunda token/saniye ölç. Speedup'ın kalite maliyetini haklı çıkardığını doğrula.

5. **Uzun-context testi.** Uzun context (> 4K token) sunuyorsan, maksimum context length'te test et. KV cache quantization hataları dizi uzunluğuyla birikir.

## Bellek Bütçesi Hesaplayıcı

```
Weight bellek (GB) = parametre (B) * bit / 8 / 1.073741824
Token başına KV cache (MB) = 2 * num_layers * d_model * bit / 8 / 1048576
Context için KV cache (GB) = kv_per_token * max_context_length / 1024
Aktivasyon bellek (GB) ~ 1-4 GB (göreceli sabit, batch boyutuna bağlı)
Toplam = weight_memory + kv_cache + activation_memory + overhead (%10-20)
```

INT4'te Llama 3 70B, 32K context için örnek:
- Ağırlıklar: 70B * 4 / 8 / 1.07 = 32.6 GB
- KV cache (FP16): 2 * 80 * 8192 * 16 / 8 / 1e9 * 32768 = ~40 GB
- KV cache (FP8): ~20 GB
- FP8 KV ile toplam: ~55 GB (bir 80GB A100'e sığar)

## Yaygın Hatalar

| Hata | Neden Başarısız Olur | Düzeltme |
|---------|-------------|-----|
| Embedding katmanını INT4'e quantize etmek | İlk katman hataları tüm modele yayar | Embedding'leri FP16 veya INT8'de tut |
| INT4 için per-tensor scale kullanmak | Bir outlier row tüm row'lar için precision'ı bozar | Per-channel veya per-group scale kullan |
| GPTQ/AWQ'yu calibrate etmemek | Temsili veri olmadan scale faktörleri yanlış | Domain'inden 128 örnek kullan |
| Tüm katmanlar için aynı bit-width | İlk/son katmanlar daha duyarlı | Mixed precision: ilk/son için yüksek bit |
| Çok uzun context'te KV cache'i quantize etmek | Hatalar dizi uzunluğuyla kuadratik birikir | KV cache için INT4 değil FP8 kullan |
| Kalite doğrulamayı atlamak | Bazı modeller kötü quantize olur (özellikle sınırlarda) | Her zaman perplexity + task değerlendirmesi çalıştır |

## Deployment Reçeteleri

### Reçete 1: AWQ ile vLLM (GPU sunucusu)
```
pip install vllm autoawq
vllm serve model-awq --quantization awq --dtype half --max-model-len 8192
```

### Reçete 2: GGUF ile llama.cpp (MacBook)
```
./llama-server -m model.Q4_K_M.gguf -c 4096 -ngl 99
```

### Reçete 3: FP8 ile TensorRT-LLM (H100)
```
trtllm-build --model_dir model --output_dir engine --dtype float16 --use_fp8
```
