# Self-Hosted Serving Seçimi — llama.cpp, Ollama, TGI, vLLM, SGLang

> 2026'da self-hosted çıkarımda dört motor baskın. Donanım, ölçek ve ekosisteme göre seç. **llama.cpp** CPU'da en hızlı — en geniş model desteği, quantization ve threading üzerinde tam kontrol. **Ollama** dev-laptop tek-komut kurulum, llama.cpp'den ~%15-30 daha yavaş (Go + CGo + HTTP serileştirme), prod-benzeri yük altında 3x throughput farkı. **TGI 11 Aralık 2025'te bakım moduna girdi** — yalnız bug düzeltmeleri, vLLM'den ham throughput'ta ~%10 daha yavaş ama tarihsel olarak en iyi observability ve HF-ekosistem entegrasyonu. Bu bakım statüsü uzun-vadeli riskli bir bahis yapar — yeni projeler için SGLang ya da vLLM daha güvenli varsayılanlar. **vLLM** genel-amaçlı üretim varsayılanı — v0.15.1 (Şubat 2026) PyTorch 2.10, RTX Blackwell SM120, H200 optimizasyonu ekler. **SGLang** agentic multi-turn / prefix-ağırlıklı uzmanı — üretimde 400.000+ GPU (xAI, LinkedIn, Cursor, Oracle, GCP, Azure, AWS). Donanım kısıtları: yalnız-CPU → yalnız llama.cpp. AMD / NVIDIA-olmayan → yalnız vLLM (TRT-LLM NVIDIA-kilitli). 2026 pipeline deseni: dev = Ollama, staging = llama.cpp, prod = vLLM ya da SGLang. Baştan sona aynı GGUF/HF ağırlıkları.

**Tür:** Öğrenim
**Diller:** Python (stdlib, motor-karar ağacı yürüyücüsü)
**Ön koşullar:** Motorları kapsayan tüm Faz 17 dersleri (04, 06, 07, 09, 18)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Donanım (CPU / AMD / NVIDIA Hopper / Blackwell), ölçek (1 kullanıcı / 100 / 10.000) ve iş yükü (genel sohbet / agent / long-context) verildiğinde bir motor seç.
- 2026 TGI bakım-modu statüsünü (11 Aralık 2025) adlandır ve yeni projeleri neden vLLM ya da SGLang'e doğru saptırdığını söyle.
- Baştan sona aynı GGUF ya da HF ağırlıklarını kullanarak dev/staging/prod pipeline'ını tarif et.
- "Yalnız CPU"nun neden llama.cpp'yi zorladığını ve "AMD"nin neden TRT-LLM'i dışladığını açıkla.

## Sorun

Takımın yeni bir self-hosted LLM projesi başlatıyor. Bir mühendis Ollama der, bir diğeri vLLM, bir üçüncüsü "TGI kutudan çıkıp çalışmıyor mu?" Üçü de farklı bağlamlar için doğru. Hiçbiri her şey için doğru değil.

2026'da seçim ağacı önemli: önce donanım, ikincisi ölçek, üçüncüsü iş yükü. Ve spesifik bir 2025 olayı — TGI'nın 11 Aralık'ta bakım moduna girmesi — yeni projeler için varsayılanı değiştirir.

## Kavram

### Beş motor

| Motor | En iyi | Notlar |
|--------|----------|-------|
| **llama.cpp** | CPU / edge / minimum bağımlılık / en geniş model desteği | CPU'da en hızlı, tam kontrol |
| **Ollama** | Dev laptop'lar, tek kullanıcı, tek-komut kurulum | llama.cpp'den %15-30 daha yavaş; 3x prod throughput farkı |
| **TGI** | HF ekosistemi, regüle endüstriler | **Bakım modu 11 Ara 2025** |
| **vLLM** | Genel-amaçlı üretim, 100+ kullanıcı | Geniş üretim varsayılanı; v0.15.1 Şub 2026 |
| **SGLang** | Agentic multi-turn, prefix-ağırlıklı iş yükleri | Üretimde 400.000+ GPU |

### Önce-donanım kararı

**Yalnız CPU** → llama.cpp. Ollama da çalışır ama daha yavaş. Başka hiçbir motor CPU'da rekabetçi değil.

**AMD GPU** → vLLM (AMD ROCm desteği). SGLang da çalışır. TRT-LLM NVIDIA-kilitli, dolayısıyla dışta.

**NVIDIA Hopper (H100 / H200)** → vLLM ya da SGLang ya da TRT-LLM. Üçü de üst-tier.

**NVIDIA Blackwell (B200 / GB200)** → TRT-LLM throughput lideri (Faz 17 · 07). vLLM ve SGLang yakın takip eder.

**Apple Silicon (M-serisi)** → llama.cpp (Metal). Ollama bunu sarar.

### İkinci-ölçek kararı

**1 kullanıcı / yerel dev** → Ollama. Tek komut, saniyelerde ilk-token.

**10-100 kullanıcı / küçük takım** → tek-GPU vLLM.

**100-10k kullanıcı / üretim** → vLLM production-stack (Faz 17 · 18) ya da SGLang.

**10k+ kullanıcı / enterprise** → vLLM production-stack + disaggregated (Faz 17 · 17) + LMCache (Faz 17 · 18).

### Üçüncü-iş-yükü kararı

**Genel sohbet / Q&A** → vLLM geniş varsayılanda kazanır.

**Agentic multi-turn (tool'lar, planlama, bellek)** → SGLang'in RadixAttention'ı (Faz 17 · 06) domine eder.

**Ağır prefix yeniden kullanımlı RAG** → SGLang.

**Kod üretimi** → vLLM iyi; SGLang cache'te biraz daha iyi.

**Long context (128K+)** → vLLM + chunked prefill; SGLang + tier'lı KV.

### TGI bakım tuzağı

Hugging Face TGI 11 Aralık 2025'te bakım moduna girdi — bundan sonra yalnız bug düzeltmeleri. Tarihsel olarak: üst-tier observability, sınıfının en iyisi HF-ekosistem entegrasyonu (model card'lar, güvenlik araçları), ham throughput'ta vLLM'in biraz arkasında.

2026'da yeni projeler için: varsayılan olarak TGI'dan uzak. Mevcut TGI deployment'ları devam edebilir ama sonunda göç etmeli. SGLang ve vLLM daha güvenli varsayılanlar.

### Pipeline deseni

Dev (Ollama) → staging (llama.cpp) → prod (vLLM). Baştan sona aynı GGUF ya da HF ağırlıkları. Mühendisler laptop'larda hızlı iterasyon yapar; staging üretim quantization'ını yansıtır; prod serving hedefi.

### Ollama uyarısı

Ollama dev için harika. Paylaşılan üretim için harika değil: Go HTTP serileştirme overhead ekler, eşzamanlılık yönetimi vLLM'den daha basit, OpenTelemetry desteği gerilemiştir. Ollama'yı parladığı yerde — tek kullanıcı, tek komut — kullan ve paylaşılan için vLLM'e geç.

### Self-hosted vs managed ayrı bir karar

Faz 17 · 01 (yönetilen hyperscaler'lar), · 02 (çıkarım platformları) yönetileni kapsar. Bu ders zaten self-host etmeye karar verdiğini varsayar. Self-host nedenleri: veri ikametgâhı, custom fine-tune, ölçekte toplam maliyet sahipliği, hosted'ta mevcut olmayan alan modeli.

### Hatırlaman gereken sayılar

- TGI bakım modu: 11 Aralık 2025.
- vLLM v0.15.1: Şubat 2026; PyTorch 2.10; Blackwell SM120 desteği.
- SGLang üretim ayak izi: 400.000+ GPU.
- Ollama throughput farkı llama.cpp'ye karşı: %15-30 daha yavaş; prod yük altında 3x.

## Kullan

`code/main.py` bir karar-ağacı yürüyücüsü: donanım + ölçek + iş yükü verildiğinde, bir motor seçer ve nedenini açıklar.

## Yayınla

Bu ders `outputs/skill-engine-picker.md` üretir. Kısıtlar verildiğinde, bir motor seçer ve göç planını yazar.

## Alıştırmalar

1. `code/main.py`'ı donanım / ölçek / iş yükünle çalıştır. Output sezgine uyuyor mu?
2. Altyapın 12 H100 ve 8 MI300X AMD. Hangi motor? TRT-LLM neden masada değil?
3. Bir takım 2026'da "bildiğimiz şey bu" diye TGI kullanmak istiyor. Göç vakasını savun.
4. Ollama dev'den vLLM prod'a: quantization, konfigürasyon ve observability'de ne değişir?
5. P99 prefix uzunluğu 8K ve tenant'lar arası yüksek yeniden kullanımlı RAG ürünü. Bir motor seç ve Faz 17 · 11 + 18 ile yığ.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| llama.cpp | "CPU olan" | En geniş model desteği, CPU'da en hızlı |
| Ollama | "laptop olan" | Tek-komut kurulum, dev-sınıfı throughput |
| TGI | "HF'in serving'i" | Aralık 2025'ten beri bakım modu |
| vLLM | "varsayılan" | 2026 geniş üretim baseline'ı |
| SGLang | "agentic olan" | Prefix-ağırlıklı, RadixAttention |
| TRT-LLM | "NVIDIA-kilitli" | Blackwell throughput lideri, yalnız NVIDIA |
| GGUF | "llama.cpp formatı" | Paketlenmiş K-quant varyantları |
| Production-stack | "vLLM K8s" | Faz 17 · 18 referans deployment'ı |
| Pipeline deseni | "dev→stage→prod" | Aynı ağırlıklarda Ollama → llama.cpp → vLLM |

## İleri Okuma

- [AI Made Tools — vLLM vs Ollama vs llama.cpp vs TGI 2026](https://www.aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/)
- [Morph — llama.cpp vs Ollama 2026](https://www.morphllm.com/comparisons/llama-cpp-vs-ollama)
- [n1n.ai — Comprehensive LLM Inference Engine Comparison](https://explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13)
- [PremAI — 10 Best vLLM Alternatives 2026](https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/)
- [TGI maintenance announcement](https://github.com/huggingface/text-generation-inference) — release notes.
- [vLLM v0.15.1 release notes](https://github.com/vllm-project/vllm/releases)
