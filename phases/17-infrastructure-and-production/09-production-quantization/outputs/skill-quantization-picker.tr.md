---
name: quantization-picker
description: Hardware, engine, iş yükü ve kalite toleransı verildiğinde 2026 quantization formatı seç ve bir kalibrasyon + doğrulama planı üret.
version: 1.0.0
phase: 17
lesson: 09
tags: [quantization, awq, gptq, gguf, fp8, nvfp4, calibration]
---

Hardware (CPU / H100 / H200 / B200 / GB200, sayıyla), engine (llama.cpp / vLLM / TRT-LLM / SGLang), model (boyut + görev tipi — rutin sohbet / reasoning / kod / multi-LoRA) ve kalite toleransı (HumanEval / MATH / MMLU üzerinde N-puanlık düşüşü emebilir) verildiğinde, bir quantization formatı seç ve bir doğrulama planı üret.

Üret:

1. Format önerisi. Şunlardan biri: GGUF Q4_K_M, GGUF Q5_K_M, GPTQ-Int4 + Marlin, AWQ-Int4 + Marlin, FP8, NVFP4 + FP8 KV veya stacked bir kombinasyon. Karar ağacıyla gerekçelendir: CPU → GGUF; reasoning → FP8; vLLM üzerinde multi-LoRA → GPTQ; rutin GPU sohbet → AWQ; doğrulanmış Blackwell → NVFP4.
2. Bellek bütçesi. Ağırlıklar + KV cache (raporlanan eşzamanlılık × context'te) + aktivasyonları raporla. Hedef GPU'ya sığdığını doğrula veya çoklu-GPU gereksinimini belirt.
3. Kalibrasyon planı. Dataset kaynağı (AWQ/GPTQ için domain-eşleşmiş; son çare olarak genel C4/WikiText). Örnek sayısı (domain için 500-2000). Doğrulama seti (kalibrasyon havuzundan tutulan %10).
4. Doğrulama planı. Göreve eşleşmiş eval seti: kod için HumanEval, reasoning için MATH/MMLU, sohbet için MT-Bench. Baseline BF16 vs quantized. Düşüş ≤ kalite toleransıysa ship et.
5. KV cache kararı. Ağırlık quantization'dan ayrı. Reasoning için FP8 KV öner; attention doğruluğu marjinalse BF16 KV; INT8 KV yalnızca doğrulamadan sonra.
6. Rollback yolu. Disk'te BF16/FP8 ağırlıkları tut; üretim kalitesi bozulursa geri dön flag'i.

Hard rejects:
- Reasoning-yoğun iş yüklerinde eval-seti doğrulaması olmadan NVFP4 ağırlık önermek.
- Domain modeller için genel web verisinde kalibrasyon yapmak. Her zaman in-domain kullan.
- HBM bütçesinde KV cache'i unutmak. Her zaman kalemlendir.
- Kernel'leri adlandırmadan throughput sayıları iddia etmek (Marlin-AWQ vs plain AWQ 10x'tir).

Reddetme kuralları:
- İş yükü doğası gereği kalite-marjinalse (açık uçlu yaratıcı üretim, edge-case reasoning), agresif INT4'ü reddet. FP8 veya BF16'da kal.
- Engine llama.cpp ise, GGUF dışında herhangi bir formatı reddet. Formatın engine ile eşleşmesi olmazsa olmazdır.
- Kullanıcı 1.000 örneklik eval çalıştıramıyorsa, reddet. Üretimde kör quantization yok.

Çıktı: seçilen format, HBM bütçesi, kalibrasyon planı, doğrulama planı, KV cache kararı ve rollback yolunu listeleyen tek sayfalık quantization seçimi. Ana riske göre eval-seti delta'sı, peak eşzamanlılıkta KV cache baskısı veya gerçek batch boyutunda throughput'tan birini adlandıran "sırada neyi ölç" paragrafıyla bitir.
