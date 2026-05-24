# Edge Inference — Apple Neural Engine, Qualcomm Hexagon, WebGPU/WebLLM, Jetson

> Çekirdek edge kısıtı bellek bant genişliği, compute değil. Mobil DRAM 50-90 GB/s'de; datacenter HBM3 2-3 TB/s aşar — 30-50x fark. Decode bellek-bağlı olduğundan fark belirleyici. 2026'da manzara dört yöne ayrılır. Apple M4/A18 Neural Engine unified bellek (CPU↔NPU kopyası yok) ile 38 TOPS tepe yapar. Qualcomm Snapdragon X Elite / 8 Gen 4 Hexagon 45 TOPS'a ulaşır. WebGPU + WebLLM M3 Max'te Llama 3.1 8B'i (Q4) ~41 tok/s'de çalıştırır (kabaca native'in %70-80'i); 17.6k GitHub yıldızı, OpenAI-uyumlu API, ~%70-75 mobil kapsama. NVIDIA Jetson Orin Nano Super (8GB) Llama 3.2 3B / Phi-3'e sığar; AGX Orin gpt-oss-20b'yi vLLM üzerinden ~40 tok/s'de çalıştırır; Jetson T4000 (JetPack 7.1) AGX Orin'in 2x'i. TensorRT Edge-LLM EAGLE-3, NVFP4, chunked prefill destekler — CES 2026'da Bosch, ThunderSoft, MediaTek tarafından gösterildi.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak bant-bağlı decode simülatörü)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 17 · 09 (Üretim Quantization)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Mobil LLM çıkarımının neden bellek-bant-genişliği-bağlı olduğunu ve compute'un ikincil olduğunu açıkla.
- Dört edge hedefini (Apple ANE, Qualcomm Hexagon, WebGPU/WebLLM, NVIDIA Jetson) say ve her birini bir kullanım senaryosuyla eşleştir.
- 2026 WebGPU kapsama farkını (Firefox Android yetişiyor) ve Safari iOS 26 inişini adlandır.
- Her hedef için bir quantization formatı seç (ANE için Core ML INT4 + FP16, Hexagon için QNN INT8/INT4, browser için WebGPU Q4, Jetson Thor için NVFP4).

## Sorun

Bir müşteri on-device bir chatbot istiyor: ses-öncelikli, varsayılan-olarak-özel, offline çalışır. Bir MacBook Pro M3 Max'te, Llama 3.1 8B Q4 ~55 tok/s'de çalışır — iyi. iPhone 16 Pro'da, aynı model 3 tok/s'de çalışır — iyi değil. Snapdragon 8 Gen 3'lü orta seviye bir Android'de, 7 tok/s. Chrome Android v121+ üzerinden WebGPU üzerinden tarayıcıda, cihaza bağlı olarak 4-8 tok/s.

Throughput varyansı bir porting sorunu değil. Bant genişliği farkı çarpı quantization formatı çarpı NPU'nun kullanıcı-alanından erişilebilir olup olmadığıdır. 2026'da edge çıkarım dört farklı çözümlü dört farklı sorundur.

## Kavram

### Bant genişliği gerçek tavan

Decode her token için ağırlıkların tüm kümesini okur. Q4'te bir 7B model 3.5 GB. 50 GB/s'de 3.5 GB okumak 70 ms alır — teorik tavan ~14 tok/s. 90 GB/s'de (üst-seviye mobil DRAM) tavan ~25 tok/s'ye taşınır. Bu sayının altında ne kadar compute olursa olsun yardımı olmaz.

3 TB/s'de datacenter HBM3 aynı 3.5 GB'ı 1.2 ms'de aşar — tavan 830 tok/s. Aynı model, aynı ağırlıklar. Farklı bellek alt-sistemi.

### Apple Neural Engine (M4 / A18)

- 38 TOPS'a kadar. Unified bellek (CPU ve ANE aynı havuzu paylaşır) — kopya overhead'i yok.
- Core ML + `.mlmodel` compile edilmiş modeller üzerinden, ya da PyTorch üzerinden Metal Performance Shaders (MPS) ile erişim.
- Llama.cpp Metal backend doğrudan ANE değil MPS kullanır; native ANE Core ML dönüşümü gerektirir.
- 2026'da iOS uygulamaları için en iyi pratik yol: INT4 ağırlıklar + FP16 aktivasyonlarla Core ML.

### Qualcomm Hexagon (Snapdragon X Elite / 8 Gen 4)

- 45 TOPS'a kadar. SoC içinde CPU ve GPU ile entegre ama ayrı bellek alanı.
- QNN (Qualcomm Neural Network) SDK ve AI Hub PyTorch/ONNX'ten dönüşüm sağlar.
- Chat template'leri, Llama 3.2, Phi-3 hepsi AI Hub'da first-class artifact olarak yayınlanır.

### Intel / AMD NPU'ları (Lunar Lake, Ryzen AI 300)

- 40-50 TOPS. Yazılım Apple/Qualcomm'un gerisinde; OpenVINO gelişiyor ama niche.
- Windows ARM copilot uygulamaları için en iyi; local-first için AMD/Intel desktop'larında yerel.

### WebGPU + WebLLM

- Modelleri WebGPU compute shader'ları üzerinden tarayıcıda çalıştır; kurulum yok.
- M3 Max'te Llama 3.1 8B Q4 ~41 tok/s — aynı backend üzerinden native'in kabaca %70-80'i.
- WebLLM'de 17.6k GitHub yıldızı; OpenAI-uyumlu JS API; Apache 2.0.
- 2026 kapsama: Chrome Android v121+, Safari iOS 26 GA, Firefox Android hâlâ yetişiyor. Genel ~%70-75 mobil kapsama.

### NVIDIA Jetson ailesi

- Orin Nano Super (8GB): Llama 3.2 3B, Phi-3'e iyi tok/s'de sığar.
- AGX Orin: gpt-oss-20b'yi vLLM üzerinden ~40 tok/s'de çalıştırır.
- Thor / T4000 (JetPack 7.1): AGX Orin performansının 2x'i, EAGLE-3 ve NVFP4 destekli.
- TensorRT Edge-LLM (2026) EAGLE-3 speculative decoding, NVFP4 ağırlıklar, chunked prefill destekler — datacenter optimizasyonları edge'e port edildi.

### Hedef başına quantization seçimi

| Hedef | Format | Notlar |
|--------|--------|-------|
| Apple ANE | INT4 ağırlıklar + FP16 aktivasyonlar | Core ML dönüşüm yolu |
| Qualcomm Hexagon | QNN INT8 / INT4 | AI Hub dönüştürücüleri |
| WebGPU / WebLLM | Q4 MLC (q4f16_1) | `mlc_llm convert_weight` + compile edilmiş `.wasm` kullan; GGUF desteklenmez |
| Jetson Orin Nano | Q4 GGUF ya da TRT-LLM INT4 | Bellek-bağlı |
| Jetson AGX / Thor | NVFP4 + FP8 KV | Edge-LLM yolu |

### Edge'de long-context tuzağı

Llama 3.1'in 128K context'i bir datacenter özelliği. 8 GB RAM'li bir telefonda, 4 GB model + 32K token için 2 GB KV cache + OS overhead = OOM. Edge deployment'lar agresif KV quantization (Q4 KV) kabul edilmedikçe context'i 4K-8K'da tutar.

### Killer app voice

Voice agent'lar gecikme-hassas (ilk token < 500 ms). Yerel çıkarım network gecikmesini tamamen elimine eder. Speech-to-text (Whisper Turbo varyantları edge'de çalışır) ile birleştir ve edge çıkarım üretim-kalite voice loop olur.

### Hatırlaman gereken sayılar

- Apple M4 / A18 ANE: 38 TOPS.
- Qualcomm Hexagon SD X Elite: 45 TOPS.
- WebLLM M3 Max: Llama 3.1 8B Q4'te ~41 tok/s.
- AGX Orin: gpt-oss-20b'de vLLM üzerinden ~40 tok/s.
- Datacenter-edge bant genişliği farkı: 30-50x.
- WebGPU mobil kapsama: ~%70-75 (Firefox Android geride).

## Kullan

`code/main.py` edge hedefleri arasında bant-bağlı matematiğe dayanan teorik decode throughput tavanlarını hesaplar. Gözlemlenen benchmark'larla karşılaştırır ve compute'un değil bant genişliğinin bottleneck olduğu yerleri vurgular.

## Yayınla

Bu ders `outputs/skill-edge-target-picker.md` üretir. Platform (iOS/Android/browser/Jetson), model ve gecikme/bellek bütçesi verildiğinde, bir quantization formatı ve dönüşüm pipeline'ı seçer.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Snapdragon 8 Gen 3'te (~77 GB/s bant genişliği) Q4'te 7B model için decode tavanını hesapla. Gözlemlenen 6-8 tok/s ile karşılaştır — runtime verimli mi?
2. Android'de WebGPU Chrome v121+ gerektirir. Eski tarayıcılar için bir fallback tasarla — aynı OpenAI-uyumlu API üzerinden sunucu-tarafı.
3. iOS uygulaman 4K-context streaming gerektiriyor. iPhone 16'da 4 GB aktif belleğin altında kalmana izin veren hangi model/format kombinasyonu?
4. Jetson AGX Orin gpt-oss-20b'yi 40 tok/s'de çalıştırır. Jetson Nano yalnız 3B'ye sığar. Ürünün ikisini de hedeflerse, çıkarım stack'ini nasıl birleştirirsin?
5. "2026'da WebLLM üretim-hazır mı" savın. Kapsamı, performansı ve Firefox Android farkını atıfla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| ANE | "Apple neural engine" | M-serisi ve A-serisinde on-device NPU; unified bellek |
| Hexagon | "Qualcomm NPU" | Snapdragon NPU; erişim için QNN SDK |
| WebGPU | "browser GPU" | W3C-standartlaşmış browser GPU API'sı; Chrome/Safari 2026 |
| WebLLM | "browser LLM runtime" | MLC-LLM projesi; Apache 2.0; OpenAI-uyumlu JS |
| Jetson | "NVIDIA edge" | Orin Nano / AGX / Thor / T4000 ailesi |
| TRT Edge-LLM | "edge TensorRT" | 2026 TensorRT-LLM edge port'u; EAGLE-3 + NVFP4 |
| Unified bellek | "paylaşılan havuz" | CPU ve NPU aynı RAM'i görür; kopya overhead'i yok |
| Bant-bağlı | "bellek-sınırlı" | Decode'un ağırlık okuyan byte/saniyeye kapısı |
| Core ML | "Apple dönüşümü" | ANE-native modeller için Apple framework'ü |
| QNN | "Qualcomm stack'i" | Qualcomm Neural Network SDK'i |

## İleri Okuma

- [On-Device LLMs State of the Union 2026](https://v-chandra.github.io/on-device-llms/) — manzara ve benchmark'lar.
- [NVIDIA Jetson Edge AI](https://developer.nvidia.com/blog/getting-started-with-edge-ai-on-nvidia-jetson-llms-vlms-and-foundation-models-for-robotics/) — Orin / AGX / Thor.
- [NVIDIA TensorRT Edge-LLM](https://developer.nvidia.com/blog/accelerating-llm-and-vlm-inference-for-automotive-and-robotics-with-nvidia-tensorrt-edge-llm/) — 2026 edge port duyurusu.
- [WebLLM (arXiv:2412.15803)](https://arxiv.org/html/2412.15803v2) — tasarım ve benchmark'lar.
- [Apple Core ML](https://developer.apple.com/documentation/coreml) — ANE-native dönüşüm.
- [Qualcomm AI Hub](https://aihub.qualcomm.com/) — Hexagon için önceden-dönüştürülmüş modeller.
