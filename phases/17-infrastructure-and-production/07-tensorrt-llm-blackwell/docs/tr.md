# Blackwell'de FP8 ve NVFP4 ile TensorRT-LLM

> TensorRT-LLM yalnız-NVIDIA ama Blackwell'de kazanır. Dynamo orkestrasyonu ile GB200 NVL72'de, SemiAnalysis InferenceX 2026 Q1-Q2'de 120B modelde milyon token başına $0.012 ölçtü; H100 + vLLM'de $0.09/M'e karşı — 7x ekonomik fark. Stack bileşik üç floating-point rejimi: FP8 KV cache ve attention kernel'leri için kritik kalır çünkü ihtiyaç duydukları dinamik aralığa sahip; NVFP4 (4-bit microscaling) ağırlıkları ve aktivasyonları halleder; multi-token prediction (MTP) ve disaggregated prefill/decode üstüne 2-3x daha ekler. Day-0 model desteği FP4 ağırlıkları post-training dönüşüm olmadan doğrudan yükler. 2026 mühendislik takımları için püf nokta: TRT-LLM kapalı bir NVIDIA stack'i, dolayısıyla benimsemek taşınabilirliği throughput ile takas eder. Taahhüt etmeden önce model ve donanım karışımının üzerinde matematiği çalıştır.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak FP8/NVFP4 bellek ve maliyet hesaplayıcısı)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 10 · 13 (Quantization)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Ağırlıklar NVFP4'te olsa bile KV cache ve attention için FP8'in neden kritik kaldığını açıkla.
- Bir frontier modelin BF16, FP8 ve NVFP4 altında HBM ayak izini hesapla ve tasarrufların nereden geldiği üzerine akıl yürüt.
- TRT-LLM'in sömürdüğü Blackwell-spesifik özellikleri adlandır (day-0 FP4, MTP, disaggregated serving, all-to-all primitive'ler).
- TRT-LLM'in NVIDIA-lock'unun Hopper'da vLLM'e karşı 7x maliyet farkına ne zaman değdiğine karar ver.

## Sorun

2026'da çıkarım ekonomisinin frontier'ı "dolar başına token sayısı". Cevap dört yığılmış seçime bağlı: donanım jenerasyonu (Hopper H100/H200 vs Blackwell B200/GB200), hassasiyet (BF16 → FP8 → NVFP4), serving motoru (vLLM vs SGLang vs TRT-LLM) ve orkestrasyon (düz vs disaggregated vs Dynamo).

Hopper'da vLLM ile, 120B'lik bir MoE milyon token başına ~$0.09'da çalışır. Blackwell'de TRT-LLM + Dynamo ile, aynı model ~$0.012'de çalışır — 7x daha ucuz. O farkın bir kısmı donanım (Blackwell Hopper'a karşı GPU başına LLM throughput'unda 11-15x). Bir kısmı stack: FP4 ağırlıklar, MTP draft, disaggregated prefill/decode ve MoE expert iletişimi için NVLink 5 all-to-all.

Bunu NVIDIA stack'inin dışında çoğaltamazsın. Tradeoff bu — ekonomi için taşınabilirlik. Hangi stack seçimlerinin farkın hangi payını verdiğini anlamak bu dersin amacı.

## Kavram

### KV cache için FP8 neden hâlâ taban

2026'da yaygın bir hata: NVFP4'ün her yere uygulandığını varsaymak. Uygulanmaz. KV cache FP8 (8-bit floating point) gerektirir çünkü geniş bir dinamik aralık kapsayan attention key ve value'larını saklar. KV'yi FP4'e quantize etmek felaket doğruluk kaybına neden olur — dağılımın kuyruğu düşer ve attention skorları çöker. FP8'in exponent bit'leri KV cache'e ihtiyaç duyduğu aralığı verir.

NVFP4 (2025-2026) ağırlıklar ve aktivasyonlara uygulanır. Microscaling: her ağırlık block'unun kendi scale faktörü var, böylece küçük block'lar per-tensor scale kaybı olmadan farklı dinamik aralıkları kapsayabilir. Aktivasyonlar için, FP4 dayanır çünkü aktivasyonlar bir katman içinde küçük-aralıktır.

Tipik Blackwell config'i:

- Ağırlıklar: NVFP4 (4-bit microscaling).
- Aktivasyonlar: NVFP4.
- KV cache: FP8.
- Attention accumulator: FP32 (softmax stabilitesi).

### TRT-LLM'in kullandığı Blackwell-spesifik primitive'ler

- **Day-0 FP4 ağırlıkları**: model sağlayıcılar FP4 ağırlıkları doğrudan yayınlar; TRT-LLM post-training dönüşüm olmadan yükler. FP4 için AWQ / GPTQ adımı yok.
- **Multi-token prediction (MTP)**: EAGLE ile aynı fikir (Faz 17 · 05) ama TRT-LLM build'ine entegre.
- **Disaggregated serving**: ayrı GPU pool'larda prefill ve decode, KV cache NVLink ya da InfiniBand üzerinden transfer edilir. Dynamo ile aynı fikir (Faz 17 · 20).
- **All-to-all iletişim primitive'leri**: NVLink 5 MoE expert iletişim gecikmesini Hopper'a karşı 3x kısalttı. TRT-LLM'in MoE kernel'leri bunun için tunlu.
- **NVFP4 + MXFP8 microscaling**: Blackwell Tensor Core'larda donanım-hızlandırılmış scale-faktör işleme.

### Ezberlemen gereken sayılar

- HGX B200, TRT-LLM üzerinden GPT-OSS-120B'de $0.02/M token.
- GB200 NVL72, Dynamo (TRT-LLM'i orkestre eden) üzerinden $0.012/M token.
- Karşılaştırılabilir iş yükünde H100 + vLLM ≈ $0.09/M token.
- 2026'da TRT-LLM güncellemelerinin üç ayında 2.8x throughput kazancı.
- Blackwell'in Hopper'a karşı GPU başına LLM throughput'u 11-15x.
- MLPerf Inference v6.0 (Nisan 2026): Blackwell sunulan her görevde baskın.

### FP4 kalitede gerçekte ne maliyetler

NVFP4 agresif. Reasoning-ağırlıklı iş yüklerinde (chain-of-thought, matematik, uzun context'li kod üretimi), FP4 ağırlıkları görünür şekilde bozulur. Block başına kalibrasyon mitige eder ama elimine etmez. Reasoning model'ler yayınlayan takımlar genelde uzlaşma olarak FP8 ağırlıkları + FP4 aktivasyonları kullanır, ya da boyunca FP8 ile H200'de kalır.

Kural: NVFP4 ağırlıklarına taahhüt etmeden önce her zaman eval set'inde görev kalitesini doğrula.

### Bu neden bir NVIDIA-lock kararı

TRT-LLM C++ + CUDA + kapalı-kaynak kernel'ler. Modellerin belirli bir GPU SKU için compile edilmesi gerek. AMD yok, Intel yok, ARM yok. Altyapı stratejin multi-vendor ise, TRT-LLM TRT-LLM-servis edilen katman için başlangıç değil — karma donanımda vLLM'den hâlâ servis edebilirsin. Yalnız-NVIDIA isen, 7x fark lock'u öder.

### 2026 pratik tarifi

Yıllık $100M+ çıkarım faturası için, Hopper + vLLM'de çalışmak masada 7-10x bırakır. Maliyet-baskın iş yüklerini Blackwell + TRT-LLM + Dynamo'ya taşı. Model iterasyon hızı için deney katmanını H100 + vLLM'de tut. Üretimden önce her NVFP4-dönüştürülmüş modelde kaliteyi doğrula.

### Disaggregation bonusu

TRT-LLM'in disaggregated serving'i (ayrı prefill ve decode pool'lar) Faz 17 · 20'de derinlemesine ele alınır. Blackwell'de, çarpan üst üste yığılır: FP4 ağırlıkları × MTP speedup × disaggregated yerleşim × cache-aware routing. 7x sayısı bu tam stack'i varsayar.

## Kullan

`code/main.py` üç stack arasında bir model için HBM ayak izini, decode throughput'unu (bellek-bağlı rejim) ve $/M-token'ı hesaplar: H100 + BF16 + vLLM, H100 + FP8 + vLLM, B200 + NVFP4/FP8 + TRT-LLM. Çalıştır ve bileşik etkiyi ve her değişikliğin farkın hangi payını sunduğunu gör.

## Yayınla

Bu ders `outputs/skill-trtllm-blackwell-advisor.md` üretir. Bir iş yükü, model boyutu ve yıllık token hacmi verildiğinde, Blackwell + TRT-LLM stack'inin NVIDIA-lock'a değip değmediğine karar verir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. %30 aktif parametreli bir 120B MoE'de, H100 BF16, H100 FP8 ve B200 NVFP4/FP8'de bellek-bant-genişliği-sınırlı decode throughput'unu hesapla. En büyük sıçrama nereden geliyor?
2. Bir müşteri yılda $2M H100 + vLLM'e harcıyor. 7x ekonomik fark verildiğinde, 12 ayda TRT-LLM'e bir migrasyonu amortize etmek için satın almaları gereken break-even Blackwell GPU sayısı kaç?
3. NVFP4 ağırlık dönüşümünden sonra MATH'ta 3 puan doğruluk düşüşü görüyorsun. İki kurtarma yolu adlandır: biri kalite-öncelikli (FP8 ağırlıkları tut), biri maliyet-öncelikli (alan-içi veriyle kalibre et).
4. MLPerf v6.0 çıkarım sonuçlarını oku. Hangi görevde en küçük Blackwell-üstü-Hopper farkı var ve neden?
5. 128k context'te NVFP4 ağırlıklar + FP8 KV cache'te 405B modelin için gereken HBM'i hesapla. Tek bir GB200 NVL72 node'una sığar mı?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| FP8 | "sekiz-bit float" | 8-bit floating point; dinamik aralık nedeniyle KV cache ve attention için kullanılır |
| NVFP4 | "dört-bit micro" | NVIDIA'nın 4-bit microscaling FP formatı; Blackwell'de ağırlıklar ve aktivasyonlar |
| MXFP8 | "MX sekiz" | Microscaling FP8 varyantı; Blackwell Tensor Core'larda donanım-hızlandırılmış |
| Day-0 FP4 | "FP4 ağırlıkları yayınla" | Model sağlayıcılar ağırlıkları zaten FP4'te yayınlar; post-train dönüşüm adımı yok |
| MTP | "multi-token prediction" | TRT-LLM'in entegre speculative-decoding draft'ı (Faz 17 · 05) |
| Disaggregated serving | "prefill/decode böl" | Ayrı GPU pool'larında prefill ve decode; KV NVLink/IB üzerinden transfer edilir |
| All-to-all | "MoE expert iletişimi" | Token'ları expert GPU'lara yönlendiren iletişim deseni; NVLink 5 3x kısaltır |
| InferenceX | "SemiAnalysis çıkarım benchmark'ı" | 2026 endüstri-kabul edilmiş token-başına-maliyet benchmark'ı |

## İleri Okuma

- [NVIDIA — Blackwell Ultra MLPerf Inference v6.0](https://developer.nvidia.com/blog/nvidia-blackwell-ultra-sets-new-inference-records-in-mlperf-debut/) — Nisan 2026 MLPerf sonuçları.
- [NVIDIA — MoE Inference on Blackwell](https://developer.nvidia.com/blog/delivering-massive-performance-leaps-for-mixture-of-experts-inference-on-nvidia-blackwell/) — NVLink 5 all-to-all ve MoE kernel'ler.
- [TensorRT-LLM Overview](https://nvidia.github.io/TensorRT-LLM/overview.html) — resmi motor dokümantasyonu.
- [NVIDIA — Introducing Dynamo](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/) — TRT-LLM üzerinde disaggregated orkestrasyon.
- [MLPerf Inference](https://mlcommons.org/benchmarks/inference-datacenter/) — Blackwell sayılarını yayınlayan benchmark suite.
