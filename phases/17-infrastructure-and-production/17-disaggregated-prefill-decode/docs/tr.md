# Disaggregated Prefill/Decode — NVIDIA Dynamo ve llm-d

> Prefill compute-bağlı; decode bellek-bağlı. İkisini aynı GPU'da çalıştırmak bir kaynağı israf eder. Disaggregation onları ayrı pool'lara böler ve aralarında NIXL (RDMA/InfiniBand ya da TCP fallback) üzerinden KV cache transfer eder. NVIDIA Dynamo (GTC 2025 duyuru, 1.0 GA) vLLM/SGLang/TRT-LLM'in üzerinde oturur — Planner Profiler + SLA Planner SLO'ları karşılamak için prefill:decode oranlarını otomatik-rate-eşler. NVIDIA throughput kazançlarını bu civarda yayınlar — developer.nvidia.com (2025-06) GB200 NVL72 + Dynamo'da DeepSeek-R1 MoE için orta-gecikme rejiminde ~6x iyileştirme gösterir, ve Dynamo ürün sayfası (developer.nvidia.com, tarihsiz) GB300 NVL72 + Dynamo vs Hopper'da 50x'e varan MoE throughput'unu reklamlar. "30x" rakamı tam-stack Blackwell + Dynamo + DeepSeek-R1 raporlarındaki topluluk toplamı; tam olarak 30x diyen tek bir birincil kaynak bulamadık, dolayısıyla bunu yönsel bir iddia olarak ele al. llm-d (Red Hat + AWS) Kubernetes-native: prefill / decode / router bağımsız Service'ler olarak, rol başına HPA ile. llm-d 0.5 hierarchical KV offloading, cache-aware LoRA routing, UCCL networking, scale-to-zero ekliyor. Ekonomik: birden fazla müşteri açıklamasından dahili rollup $2M-sınıfı çıkarım harcamasında (yani yılda $600-800K) sabit SLA'de colocated serving'den Dynamo'lu disaggregated'a geçince %30-40 tasarruf öneriyor; spesifik $2M→$600-800K rakamı tek bir yayınlanmış vaka çalışması değil, dahili bir bileşik — referans alıntı değil, büyüklük-mertebesi çıpa olarak kullan. Kısa prompt'lar (<512 token, kısa output) transfer maliyetini gerekçelendirmez.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak disaggregated-vs-colocated simülatörü)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 17 · 08 (Çıkarım Metrikleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Prefill ve decode'un neden farklı optimal GPU tahsislerine sahip olduğunu açıkla ve colocation altındaki israfı sayısallaştır.
- Disaggregated mimariyi diyagramla: prefill pool'u, decode pool'u, NIXL üzerinden KV transferi, router.
- Disaggregation'ın ne zaman ödemediği koşulu adlandır (kısa prompt'lar, kısa output'lar).
- NVIDIA Dynamo'yu (stack-üstü) llm-d'den (Kubernetes-native) ayır ve her birini bir operasyonel bağlama eşle.

## Sorun

Llama 3.3 70B'yi 8 H100'de çalıştırıyorsun. Karma iş yükü altında (uzun prompt'lar + kısa output'lar), GPU'lar decode sırasında boşta çünkü compute'un çoğu prefill'e harcandı. Farklı bir iş yükü altında (kısa prompt'lar + uzun output'lar), tersi olur. Colocated prefill + decode demek ikisini de aşırı sağlıyorsun demek.

Bütçe etkisi: GPU zamanının %20-40'ı yanlış kaynakta israf ediliyor. Bellek-bağlı decode çalıştırmak için H100 compute satın alıyorsun ya da compute-bağlı prefill çalıştırmak için H100 HBM bant genişliği satın alıyorsun. İkisi de pahalı israf.

Disaggregation prefill ve decode'u her birinin bottleneck'i için boyutlandırılmış ayrı pool'lara böler. KV cache prefill pool'undan decode pool'una yüksek-bant-genişliği interconnect üzerinden transfer edilir.

## Kavram

### Bottleneck'ler neden farklı

**Prefill** — transformer'ı tam input prompt üzerinden tek bir forward'da çalıştır. Matrix çarpımları domine eder; compute-bağlı. H100 FP8 ~2000 TFLOPS kullanışlı throughput verir. Batch verimliliği iyi — bir forward birçok token'ı işler.

**Decode** — her iterasyonda tam ağırlıkları okuyarak seferde bir token üret. Bellek-bant-genişliği-bağlı. HBM3 ~3 TB/s verir. Batch verimliliği yalnız yüksek eşzamanlılıkta iyi — ağırlık okuması batch boyunca amortize edilir.

Onları colocate etmek: ikisi için de optimize edilmiş GPU'lar satın alırsın. H100 ikisinde de iyi ama her iki halde de aynı maliyetler. Ölçekte, prefill pool'unu H100 / compute-ağırlıklı; decode pool'unu H200 / bellek-ağırlıklı, ya da agresif quantization'la istersin.

### Mimari

```
            ┌──────────────┐
   İstek → │    Router    │ ───────────────────────┐
            └──────┬───────┘                        │
                   │                                │
                   ▼ (yalnız prompt)                │
            ┌──────────────┐    KV cache    ┌───────▼──────┐
            │ Prefill pool │ ─── NIXL ────► │ Decode pool  │
            │  (compute)   │                │  (bellek)    │
            └──────────────┘                └──────┬───────┘
                                                   │ token'lar
                                                   ▼
                                                 Client
```

NIXL NVIDIA'nın inter-node transport'u. Mevcutsa RDMA/InfiniBand kullanır, aksi takdirde TCP fallback. Transfer gecikmesi gerçek — tipik olarak 70B FP8'de 4K-token'lık bir prompt'un KV cache'i için 20-80 ms. Kısa prompt'ların disaggregation'ı gerekçelendirmemesinin nedeni bu: transfer vergisi tasarrufları aşar.

### Dynamo vs llm-d

**NVIDIA Dynamo** (GTC 2025 duyuru, 1.0 GA):
- vLLM, SGLang, TRT-LLM üzerinde bir orkestratör olarak oturur.
- Planner Profiler iş yükünü ölçer, SLA Planner prefill:decode oranlarını otomatik-configure eder.
- Rust çekirdek, Python genişletilebilirlik.
- Throughput kazançları: NVIDIA orta-gecikme rejiminde GB200 NVL72 + Dynamo'da DeepSeek-R1 MoE için 6x raporlar (developer.nvidia.com, 2025-06); tam Blackwell + Dynamo + DeepSeek-R1 stack'lerinde "30x'e kadar" topluluk raporları tek bir birincil kaynaktan yoksundur ve yönsel olarak ele alınmalıdır.
- GB300 NVL72 + Dynamo: Dynamo ürün sayfasına göre Hopper'a karşı 50x'e varan MoE throughput'u (developer.nvidia.com, tarihsiz).

**llm-d** (Red Hat + AWS, Kubernetes-native):
- Prefill / decode / router bağımsız Kubernetes Service'ler olarak.
- Queue derinliği (prefill) / KV utilization (decode) sinyalleriyle rol başına HPA.
- `topologyConstraint packDomain: rack` yüksek-bant-genişliği KV transferi için prefill+decode kliklerini aynı rack'te paketler.
- llm-d 0.5 (2026): hierarchical KV offloading, cache-aware LoRA routing, UCCL networking, scale-to-zero.

Yönetilen bir stack-üstü orkestratör istiyorsan Dynamo kullan. Kubernetes-native primitive'ler istiyorsan ve CNCF ekosistemine bağlıysan llm-d kullan.

### Ekonomik

Dahili bileşik (tek bir yayınlanmış vaka çalışması değil — büyüklük-mertebesi çıpa):

- Colocated serving'de yıllık $2M çıkarım harcaması.
- Dynamo'lu disaggregated'a geçti.
- Aynı istek hacmi, aynı P99 gecikme SLA'i.
- Raporlanan tasarruf: $600K-$800K/yıl (%30-40 azaltma).
- Yeni donanım yok.

Bu rakamı tek bir alıntılanabilir vaka çalışmasından değil, birden fazla müşteri açıklamasından sentezliyoruz; en yakın yayınlanmış veri noktası Baseten'in Dynamo KV routing ile 2x daha hızlı TTFT / %61 daha yüksek throughput'u (baseten.co, 2025-10) ve %40-60 KV hit oranında VAST + CoreWeave'in %60-130 daha fazla token/$ projeksiyonu (vastdata.com, 2025-12). Tasarruflar her pool'u right-sizing'den geliyor; prefill-ağırlıklı iş yükleri (8K+ prefix'li RAG) dengeli olanlardan daha fazla yararlanır.

### Ne zaman disaggregate ETMEMELİ

- < 512 token'lık prompt'lar ve < 200 token'lık output'lar: transfer vergisi kazancı domine eder.
- Küçük cluster (< 4 GPU): yeterli pool çeşitliliği yok.
- Takım iki GPU pool'unu rol başına ölçeklemeyle çalıştıramaz: Dynamo yardım eder ama önemsiz değil.
- RDMA fabric yok: TCP transfer vergisi daha ağır.

### Router Faz 17 · 11 ile entegre olur

Disaggregated router'lar KV-cache-aware'dir (Faz 17 · 11). Bir istek prefix'ini tutan decode pool'una iner — eşleşme yoksa, prefill → decode akar. Hit oranı ve disaggregation üst üste yığılır — cache-aware router yeni bir prefill'in gerekip gerekmediğini belirler.

### Blackwell'de MoE gerçek sayıların olduğu yer

GB300 NVL72 + Dynamo Hopper baseline'ına karşı 50x MoE throughput'u gösterir. MoE expert routing prefill'de compute-ağırlıklı ama decode'da bellek-ağırlıklı (expert cache'leri), dolayısıyla disaggregation çift kazanç. 2026 frontier model serving MoE-baskın (DeepSeek-V3, gelecek GPT-5 varyantları).

### Hatırlaman gereken sayılar

Benchmark sayıları kayar — NVIDIA ve çıkarım stack'i her çeyrek güncellenmiş sonuçlar yayınlar. Alıntılamadan önce yeniden kontrol et.

- GB200 NVL72 + Dynamo'da DeepSeek-R1: orta-gecikme rejiminde baseline'a karşı ~6x throughput (developer.nvidia.com, 2025-06); tam Blackwell + Dynamo stack'lerinde "30x'e kadar" topluluk iddiaları tek bir birincil kaynak olmayan yönsel toplamlar.
- GB300 NVL72 + Dynamo: Hopper'a karşı 50x'e varan MoE throughput'u (developer.nvidia.com, tarihsiz).
- Tasarruf çıpası (dahili bileşik, tek bir vaka çalışması değil): sabit SLA'de yıllık $2M harcamadan yılda $600-800K.
- Disaggregation eşiği: >512 token'lık prompt'lar + >200 token'lık output'lar.
- NIXL üzerinden KV transferi: 70B FP8'de 4K-prompt'lık KV için 20-80 ms.

## Kullan

`code/main.py` colocated vs disaggregated serving simüle eder. Throughput'u, istek başına maliyeti ve prompt-uzunluğu crossover'ını raporlar.

## Yayınla

Bu ders `outputs/skill-disaggregation-decider.md` üretir. İş yükü ve cluster verildiğinde, disaggregate edip etmemeye karar verir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Disaggregation hangi prompt uzunluğunda colocation'ı yener?
2. P99 prefix uzunluğu 8K, output 300 olan bir RAG servisi için prefill pool'unu ve decode pool'unu tasarla.
3. Dynamo vs llm-d: Python runtime tercihi olmayan saf-Kubernetes bir mağaza için birini seç.
4. KV transfer maliyetini hesapla: 70B FP8'de 4K prefill = ~500 MB KV. RDMA 100 GB/s'de, transfer = 5 ms. TCP 10 GB/s'de = 50 ms. SLA'in için hangisi önemli?
5. MoE expert routing KV erişim desenlerini değiştirir. Token başına farklı expert'leri etkinleştiren MoE ile disaggregation nasıl davranır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Disaggregated serving | "prefill/decode böl" | Her faz için ayrı GPU pool'ları |
| NIXL | "NVIDIA transport'u" | Dynamo'nun inter-node KV transferi (RDMA/TCP) |
| NVIDIA Dynamo | "orkestratör" | vLLM/SGLang/TRT-LLM için stack-üstü koordinatör |
| llm-d | "Kubernetes native" | Red Hat + AWS K8s disaggregated stack'i |
| Planner Profiler | "Dynamo auto-config" | İş yükünü ölçer, pool oranlarını configure eder |
| SLA Planner | "Dynamo politikası" | SLO'ları karşılamak için prefill:decode'u otomatik-rate-eşler |
| `packDomain: rack` | "llm-d topology" | Hızlı KV için prefill+decode'u aynı rack'te paketle |
| UCCL | "unified collective" | Scale-to-zero için llm-d 0.5 networking katmanı |
| MoE expert routing | "token başına expert" | DeepSeek-V3 deseni; disaggregation yardım eder |

## İleri Okuma

- [NVIDIA — Introducing Dynamo](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/)
- [NVIDIA — Disaggregated LLM Inference on Kubernetes](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/)
- [TensorRT-LLM Disaggregated Serving blog](https://nvidia.github.io/TensorRT-LLM/blogs/tech_blog/blog5_Disaggregated_Serving_in_TensorRT-LLM.html)
- [llm-d GitHub](https://github.com/llm-d/llm-d)
- [llm-d 0.5 release notes](https://github.com/llm-d/llm-d/releases)
