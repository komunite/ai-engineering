# Çıkarım Metrikleri — TTFT, TPOT, ITL, Goodput, P99

> Dört metrik bir çıkarım deployment'ının çalışıp çalışmadığına karar verir. TTFT prefill artı queue artı network'tür. TPOT (eşdeğer ITL) bellek-bağlı decode'un token başına maliyetidir. End-to-end gecikme TTFT artı TPOT çarpı output uzunluğudur. Throughput filo genelinde toplanmış saniye başına token'dır. Ama ürün için önemli olan goodput'tur — aynı anda her SLO'yu karşılayan isteklerin fraksiyonu. Düşük goodput'ta yüksek throughput, kullanıcılara zamanında ulaşmayan token'ları işliyorsun demektir. 2026'da TRT-LLM'de Llama-3.1-8B-Instruct için referans sayılar: ortalama TTFT 162 ms, ortalama TPOT 7.33 ms, ortalama E2E 1.093 ms. Her zaman P50, P90, P99'u raporla — asla yalnız ortalama değil. Ve ölçüm tuzağına dikkat: GenAI-Perf ITL hesaplamasında TTFT'yi hariç tutar, LLMPerf dahil eder; iki araç aynı çalıştırmada TPOT konusunda anlaşamaz.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak percentile hesaplayıcı ve goodput raporlayıcı)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- TTFT, TPOT, ITL, E2E, throughput ve goodput'u kesin olarak tanımla ve her birinin ölçtüğü bileşeni adlandır.
- LLM serving için ortalamanın neden yanlış istatistik olduğunu ve P50/P90/P99'u nasıl okuyacağını açıkla.
- Bir SLO çoklu-kısıt (örn. TTFT<500 ms VE TPOT<15 ms VE E2E<2 s) inşa et ve buna karşı goodput'u hesapla.
- Aynı çalıştırma için TPOT konusunda anlaşmayan iki benchmark aracı adlandır ve nedenini açıkla.

## Sorun

"Throughput'umuz saniyede 15.000 token." Yani? İsteklerin %40'ı end-to-end'de 2 saniyeyi geçtiyse, kullanıcılar oturumu bıraktı. Tek başına throughput sana ürünün çalışıp çalışmadığını söylemez.

Çıkarımın birden fazla gecikme ekseni var ve her biri farklı şekilde başarısız olur. Prefill compute-bağlı ve prompt uzunluğuyla ölçeklenir. Decode bellek-bağlı ve batch boyutuyla ölçeklenir. Queue gecikmesi operasyonel bir sorun. Network fiziksel-mesafe sorunu. Her biri için ayrı metriklere ihtiyacın var, percentile'lara ihtiyacın var ve "kullanıcı beklediğini aldı mı" diyen tek bir kompozite ihtiyacın var — bu goodput.

## Kavram

### TTFT — ilk token'a süre

`TTFT = queue_time + network_request + prefill_time`

Prompt'lar uzun olduğunda prefill domine eder. H100'de Llama-3.3-70B FP8'de, 32k prompt ~800 ms saf prefill alır. Queue zamanı yük altında scheduler davranışı. Network request TLS dahil tel zamanı. TTFT kullanıcının bir şeyin stream geri gelmeden önce gördüğü gecikme.

### TPOT / ITL — inter-token gecikme

Bir miktar için birçok isim. `TPOT` (time per output token), `ITL` (inter-token latency), `token başına decode gecikmesi` — hepsi aynı. İlkten sonra ardışık stream edilen token'lar arasındaki zaman.

`TPOT = (decode_forward_time + scheduler_overhead) / tokens_produced`

Chunked prefill'li aynı Llama-3.3-70B H100 stack'inde, TPOT ortalama ~7 ms. Chunked prefill olmadan, komşu bir sequence'teki uzun bir prefill sırasında, TPOT 50 ms'ye sıçrayabilir. Ortalamayı değil P99'u izle.

### E2E gecikme

`E2E = TTFT + TPOT * output_tokens + network_response`

Uzun output'lar (>500 token) için, E2E TPOT-baskındır. Uzun prompt'lu kısa output'lar için, E2E TTFT-baskındır. Output-uzunluğuna-koşullu E2E raporla.

### Throughput

`throughput = total_output_tokens / elapsed_time`

Toplam metrik. Sana filo verimliliğini söyler. Bireysel-istek sağlığını söylemez.

### Goodput — gerçekte umursadığın metrik

`goodput = (TTFT <= a) VE (TPOT <= b) VE (E2E <= c)'yi karşılayan isteklerin fraksiyonu`

SLO çoklu-kısıt. Bir istek yalnız her kısıt tutuyorsa "iyi"dir. Goodput pay. %60 goodput'ta yüksek throughput başarısızlık. %99 goodput'ta daha düşük throughput hedef.

2026'da goodput MLPerf Inference v6.0 sunumlarında ve AI platform sağlayıcılarındaki dahili SLA takibinde kullanılan metrik.

### Neden ortalama yanlış istatistik

LLM gecikme dağılımları sağa-çarpık. Bir uzun-prefill komşusuyla bir decode batch'i ~7 ms TPOT'ta 500 token ve ~60 ms TPOT'ta 20 token yayınlayabilir. Ortalama TPOT 9 ms. P99 TPOT 65 ms. Kullanıcılar P99'a düzenli olarak çarpar — bu yüzden ayrılırlar.

Her zaman üçlüyü (P50, P90, P99) raporla. Kullanıcı deneyimi için, optimize ettiğin P99'dur.

### Referans sayılar — Llama-3.1-8B-Instruct TRT-LLM, 2026

- ortalama TTFT: 162 ms
- ortalama TPOT: 7.33 ms
- ortalama E2E: 1.093 ms
- P99 TPOT: chunked-prefill konfigürasyonuna bağlı olarak 10-25 ms değişir.

Bunlar yayınlanmış NVIDIA referans noktaları. Model boyutuyla (70B 3-5x gösterir), donanımla (H100 vs B200 ~3x) ve yükle değişirler.

### Ölçüm tuzağı

2026'nın en çok kullanılan iki benchmark aracı aynı çalıştırma için TPOT konusunda anlaşamaz:

- **NVIDIA GenAI-Perf**: ITL hesaplamasından TTFT'yi hariç tutar. ITL token 2'den başlar.
- **LLMPerf**: TTFT'yi dahil eder. ITL token 1'den başlar.

TTFT 500 ms ve toplam 700 ms decode'da 100 output token olan bir istek için, GenAI-Perf `ITL = 700/99 = 7.07 ms` raporlar, LLMPerf `ITL = 1200/100 = 12.00 ms` raporlar. Araç seçimi sayıyı değiştirir.

Her zaman hangi aracı söyle. Her zaman tanımı yayınla.

### Bir SLO inşa etmek

2026'da 70B sohbet modeli için makul bir tüketici SLO'su:

- TTFT P99 <= 800 ms.
- TPOT P99 <= 25 ms.
- <300-token output'lar için E2E P99 <= 3 s.
- Goodput hedefi >= %99.

Enterprise SLO'lar TTFT'yi sıkılaştırır (200-400 ms) ve E2E'yi gevşetir. Mesele onları yazmak, üçünü de ölçmek ve goodput'u tek bir kompozit olarak takip etmek.

### Nasıl ölçülür

- Gerçek trafiği ya da gerçekçi sentetik (`--mean-input-tokens 800 --stddev-input-tokens 300 --mean-output-tokens 150` ile LLMPerf) çalıştır.
- Benchmark çalıştırması için tepe eşzamanlılığın 2x'ini hedefle.
- 30-50 iterasyon çalıştır, birleştirilmiş örnekten percentile al.
- Araç adı, araç sürümü, model, donanım, eşzamanlılık, prompt dağılımı ile yayınla.

## Kullan

`code/main.py` bir oyuncak goodput hesaplayıcısı. Bir sentetik gecikme dağılımı üret, bir SLO uygula ve goodput'u hesapla. Aynı trace'te GenAI-Perf vs LLMPerf TPOT farkını da gösterir.

## Yayınla

Bu ders `outputs/skill-slo-goodput-gate.md` üretir. Bir iş yükü ve SLO verildiğinde, throughput yerine goodput üzerinde deploy'ları gate'leyen CI/CD-hazır bir benchmark tarifi üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. %1 kuyruk sıçramalı bir dağılım üret. P99 TPOT'u 30 ms'den 15 ms'ye sıkılaştırdığında goodput nasıl değişir?
2. Bir vendor "Llama 3.3 70B H100'de 15.000 tok/s" diyor. Güvenmeden önce sorulacak üç soru adlandır.
3. Chunked prefill P99 TPOT'u neden korur ama ortalama TPOT'u korumaz?
4. Bir voice asistanı için tüketici SLO'su inşa et (ilk token okunmaz, duyulur). Hangi metrik en kullanıcı-görünür?
5. LLMPerf README'sini ve GenAI-Perf dokümanlarını oku. Araçların anlaşmadığı üç başka metriği tanımla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| TTFT | "ilk token'a süre" | Queue + network + prefill; uzun prompt'larda prefill ile domine olur |
| TPOT | "output token başına süre" | İlkten sonra token başına bellek-bağlı decode maliyeti |
| ITL | "inter-token latency" | Çoğu araçta TPOT ile aynı (hepsi değil — GenAI-Perf'e bak) |
| E2E | "end to end" | TTFT + TPOT * output_len; üstünde yanıt-tarafı network |
| Throughput | "tok/s" | Filo verimliliği; gecikme percentile'ları olmadan işe yaramaz |
| Goodput | "SLO-karşılanan oran" | Aynı anda her SLO kısıtını karşılayan isteklerin fraksiyonu |
| P99 | "kuyruk" | 100'de 1 en kötü-durum gecikme; kullanıcı deneyimi metriği |
| SLO çoklu-kısıt | "joint" | Üç gecikme sınırının VE'si; herhangi biri ihlal edilirse istek başarısız |
| GenAI-Perf vs LLMPerf | "araç tuzağı" | Araçlar ITL'in TTFT'yi içerip içermediği konusunda anlaşamaz |

## İleri Okuma

- [NVIDIA NIM — LLM Benchmarking Metrics](https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html) — TTFT, ITL, TPOT'un kanonik tanımı.
- [Anyscale — LLM Serving Benchmarking Metrics](https://docs.anyscale.com/llm/serving/benchmarking/metrics) — alternatif tanımlar ve ölçüm tarifi.
- [BentoML — LLM Inference Metrics](https://bentoml.com/llm/inference-optimization/llm-inference-metrics) — gerçek deployment'larda uygulanan ölçüm.
- [LLMPerf](https://github.com/ray-project/llmperf) — Ray-tabanlı open-source benchmark.
- [GenAI-Perf](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/client/src/c++/perf_analyzer/genai-perf/README.html) — NVIDIA'nın benchmark aracı.
- [MLPerf Inference](https://mlcommons.org/benchmarks/inference-datacenter/) — endüstri-kabul edilmiş goodput-tabanlı benchmark.
