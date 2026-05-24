---
name: engine-picker
description: Hardware, ölçek ve iş yükü verildiğinde bir self-hosted LLM engine'i (llama.cpp, Ollama, TGI, vLLM, SGLang) seç. Migrasyon tetikleyicisi olarak 2026 TGI maintenance mode'unu adlandır.
version: 1.0.0
phase: 17
lesson: 28
tags: [self-hosted, vllm, sglang, llama-cpp, ollama, tgi, trt-llm, engine-selection]
---

Hardware (CPU / Apple Silicon / AMD / NVIDIA Hopper / NVIDIA Blackwell), ölçek (tek-kullanıcı / küçük takım / üretim / enterprise) ve iş yükü (genel sohbet / agentic / RAG / uzun-context / kod) verildiğinde, bir engine önerisi üret.

Üret:

1. Engine. Spesifik engine'i adlandır. Hardware-öncelikli, ölçek-ikinci, iş yükü-üçüncü ağacını referans göster.
2. Alternatifler neden değil. Her alternatif engine için, neden seçim olmadığını belirt (TGI maintenance mode, AMD TRT-LLM'yi hariç tutar, Ollama yalnızca dev'dir).
3. Pipeline. Üretim ise, pipeline pattern'ini adlandır (dev Ollama → staging llama.cpp → prod vLLM/SGLang) ve ağırlık formatının (GGUF veya HF) akıp aktığını doğrula.
4. Üretim stacking. Üretim ölçeğinde, kompozisyon için Phase 17 · 18 (production-stack), · 17 (disaggregated), · 11 (cache-aware router)'a yönlendir.
5. TGI migrasyonu. Mevcut TGI ise, migrasyon planı ve zaman çizelgesini belirt — acil değil ama 6 ay içinde başlamalı.
6. Hardware tuzağı. İki hard kısıtı belirt: yalnızca CPU → llama.cpp; AMD → TRT-LLM yok.

Hard rejects:
- 2026'da yeni projeleri varsayılan olarak TGI'ye almak. Reddet — maintenance mode.
- >1 eşzamanlı kullanıcıda paylaşılan üretim için Ollama. Reddet — throughput boşluğu.
- NVIDIA-only doğrulamadan TRT-LLM önermek. Reddet — AMD / NVIDIA dışı hard bloktur.

Reddetme kuralları:
- Hardware karma ise (bazıları AMD, bazıları NVIDIA), cluster başına engine kararları iste; tek bir engine'i zorla.
- İş yükü üretim ölçeğinde "bilinmeyen/genel" ise, varsayılan olarak vLLM ve 3 ay trafik verisinden sonra yeniden değerlendirme planla.
- Takım "Blackwell mevcudiyeti olmadan GPU başına en hızlı" istiyor ve yalnızca Hopper'da ısrar ediyorsa, doğrula — TRT-LLM veya vLLM her ikisi de kabul edilebilir.

Çıktı: engine, reddedilen alternatifler, pipeline, üretim stacking, TGI migrasyon tutumu içeren tek sayfalık öneri. Tek çeyreklik gözden geçirmeyle bitir: iş yükü şekli önemli ölçüde değiştiğinde engine seçimini yeniden değerlendir.
