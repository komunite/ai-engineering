---
name: edge-target-picker
description: Cihaz, model ve latency bütçesi verildiğinde bir edge inference hedefi (Apple ANE, Qualcomm Hexagon, WebGPU/WebLLM, NVIDIA Jetson) ve eşleşen quantization formatı seç.
version: 1.0.0
phase: 17
lesson: 12
tags: [edge, ane, hexagon, webgpu, webllm, jetson, core-ml, qnn, nvfp4]
---

Deployment platformu (iOS, Android, browser, robotik/otomotiv/edge server), model ve latency/bellek bütçesi verildiğinde, bir edge hedef önerisi üret.

Üret:

1. Hedef. Spesifik NPU/GPU'yu adlandır (ANE, Hexagon, WebGPU, Jetson Orin Nano / AGX / Thor). Platform ve 2026 runtime kapsamıyla gerekçelendir.
2. Bant genişliği tavanı. Teorik decode tavanını hesapla: bandwidth_GB_s / model_size_GB. Kullanıcının tok/s gereksinimiyle karşılaştır. Tavan gereksinimin altındaysa, reddet veya daha küçük model / daha sıkı quantization öner.
3. Quantization formatı. Q4 GGUF (browser/edge CPU), Core ML INT4 + FP16 (ANE), QNN INT8/INT4 (Hexagon) veya NVFP4 + FP8 KV (Jetson Thor / Edge-LLM) seç.
4. Dönüştürme pipeline'ı. Tam dönüştürücüyü adlandır (Core ML converter, Qualcomm AI Hub, WebLLM için MLC-LLM, TensorRT-LLM Edge compiler).
5. Context bütçesi. Cihaz RAM'inde ağırlıkların yanına sığacak max context'i belirt. Uzun-context kullanım durumları için KV quantization belirt (Q4 KV) veya reddet.
6. Fallback. Cihaz yetersiz olduğunda veya WebGPU mevcut değilse (Firefox Android, eski tarayıcılar), aynı OpenAI-uyumlu arayüzle sunucu tarafı API fallback'ini belirt.

Hard rejects:
- Bant genişliği tavanının üstünde tok/s vaat etmek. Reddet — fizik.
- 2026'da Core ML olmayan bir runtime üzerinden ANE'yi doğrudan hedeflemek. ANE'yi yalnızca Core ML native olarak açar.
- WebGPU'nun her tarayıcıda olduğunu varsaymak. 2026 mobil kapsamı ~%70-75; her zaman fallback'i belirt.

Reddetme kuralları:
- Model >6 GB ve hedef bir telefon (4-8 GB RAM) ise, reddet — önce daha küçük bir model veya agresif quantization öner.
- İstek iPhone üzerinde 7B modelde 128K context ise, reddet — cihaz RAM'i Q4 KV artı sliding-window attention olmadan sığdıramaz.
- Deployment Android üzerinde WebGPU ile uzun-context streaming gerektiriyorsa ve kullanıcı Firefox desteği istiyorsa, reddet ve Chrome veya sunucu fallback'i iste.

Çıktı: hedef, tavan, quantization, dönüştürücü, context bütçesi, fallback adlandıran tek sayfalık plan. Tek bir metrikle bitir: hedef filodaki en kötü durum cihazda gözlenen tok/s.
