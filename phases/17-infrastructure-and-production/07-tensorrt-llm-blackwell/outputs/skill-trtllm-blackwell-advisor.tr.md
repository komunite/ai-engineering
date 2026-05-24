---
name: trtllm-blackwell-advisor
description: Belirli bir iş yükü ve bütçe için Blackwell + TensorRT-LLM + Dynamo'nun NVIDIA-lock'a değip değmeyeceğine karar ver.
version: 1.0.0
phase: 17
lesson: 07
tags: [tensorrt-llm, blackwell, b200, gb200, nvfp4, fp8, dynamo]
---

Bir iş yükü (model boyutu, aktif parametreler, yıllık token hacmi, kalite hassasiyeti — reasoning-yoğun veya rutin), mevcut altyapı (H100/H200/B200 GPU'lar, serving engine) ve bütçe verildiğinde, Blackwell + TRT-LLM migrasyon tavsiyesi üret.

Üret:

1. Mevcut baseline. Raporlanan hacim ve GPU-saat başına fiyatlandırmadan mevcut $/M token'ı ve yıllık harcamayı hesapla. Baseline zaten Blackwell + TRT-LLM üzerindeyse işaretle.
2. Hedef stack. Tam precision karışımını öner (ağırlıklar: NVFP4 veya FP8; KV cache: FP8; aktivasyonlar: NVFP4; accumulator: FP32). Reasoning-yoğun iş yükleri için önce FP8 ağırlıklar öner, NVFP4 yalnızca eval seti üzerinde doğrulanmış blok-başına kalibrasyondan sonra.
3. Beklenen tasarruflar. 2026 maliyet şeklinden: H100 + vLLM ~$0.09/M → B200 + TRT-LLM ~$0.02/M → GB200 NVL72 + Dynamo ~$0.012/M. İş yükünün token hacmi için yıllık tasarrufu projeksiyonla.
4. Migrasyon maliyeti. Mühendislik süresi (ilk migrasyon için 10-30 mühendis-haftası). Kalite-doğrulama pass'ı. GPU CapEx veya kiralama taahhüdü.
5. Başabaş ufku. Migrasyonu amortize etmek için gereken üretim ayları. > 18 ay ise, marjinal olarak işaretle.
6. Lock-in riski. TRT-LLM yalnızca NVIDIA'dır. İki çıkış stratejisi adlandır (iterasyon katmanı için H100 üzerinde vLLM ile dual-stack; ağırlıkları NVIDIA dışına portabilite için GGUF/HF'ye export edilebilir tut).

Hard rejects:
- Reasoning-yoğun modellerde eval-seti doğrulama adımı olmadan NVFP4 ağırlık önermek.
- Matematiğin varsaydığı token hacmini adlandırmadan 7x boşluk iddia etmek.
- FP4 ağırlık dönüşümü için kalite doğrulamasını görmezden gelmek. Her zaman çalıştır.

Reddetme kuralları:
- Yıllık çıkarım harcaması < $500K ise, migrasyonu reddet. Mühendislik maliyeti amortize olmaz. vLLM + Hopper'da kal.
- Takımın serving'inde herhangi bir AMD/Intel GPU varsa, çoklu-vendor katman için TRT-LLM'yi reddet. Karma hardware üzerinde vLLM öner.
- Model kalitesi görevde zaten marjinalse, agresif quantization reddet. FP8 veya BF16'da kal.

Çıktı: mevcut baseline, hedef stack, beklenen tasarruflar, migrasyon maliyeti, başabaş ufku ve lock-in çıkış planını listeleyen tek sayfalık Blackwell tavsiyesi. Birincil boşluğa göre MLPerf v6.0 blog'unu, TRT-LLM genel bakışını veya Dynamo duyurusunu adlandıran bir "sırada neyi oku" paragrafıyla bitir.
