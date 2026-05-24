# LLM API'larını Load Testing — k6 ve Locust Neden Yalan Söyler

> Geleneksel load tester'lar streaming yanıtlar, değişken output uzunlukları, token-seviyesi metrikler ya da GPU saturation için tasarlanmadı. İki tuzak çoğu takımı ısırır. GIL tuzağı: Locust'un token-seviyesi ölçümü tokenization'ı Python GIL altında çalıştırır, ki bu ağır eşzamanlılık altında istek üretimiyle yarışır; tokenization birikimi sonra raporlanan inter-token gecikmesini şişirir — client'ın bottleneck, sunucu değil. Prompt-tekdüzelik tuzağı: bir loop testindeki özdeş prompt'lar token dağılımındaki tek bir noktayı test eder; gerçek trafiğin değişken uzunluğu ve çeşitli prefix eşleşmeleri var. LLMPerf bunu `--mean-input-tokens` + `--stddev-input-tokens` ile düzeltir. 2026'da araç eşlemesi: token-seviyesi doğruluk için LLM-özelleşmiş (GenAI-Perf, LLMPerf, LLM-Locust, guidellm); **k6 v2026.1.0** + **k6 Operator 1.0 GA (Eylül 2025)** — streaming-aware, TestRun/PrivateLoadZone CRD'leri üzerinden Kubernetes-native dağıtık, CI/CD gate'leri için en iyi; Go constant-rate saturation için Vegeta; Locust 2.43.3 yalnızca streaming için LLM-Locust eklentisiyle. Load desenleri: steady-state, ramp, spike (autoscaling testi), soak (memory leak'ler).

**Tür:** Yapım
**Diller:** Python (stdlib, oyuncak gerçekçi-prompt üretici + gecikme toplayıcı)
**Ön koşullar:** Faz 17 · 08 (Çıkarım Metrikleri), Faz 17 · 03 (GPU Autoscaling)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Genel load tester'ları LLM API'lar için yalan söyleten iki anti-pattern'i (GIL tuzağı, prompt-tekdüzelik tuzağı) açıkla.
- Verilen amaç için bir araç seç: LLMPerf (benchmark run), k6 + streaming eklentisi (CI gate), guidellm (büyük ölçekli sentetik), GenAI-Perf (NVIDIA referansı).
- Dört load deseni (steady, ramp, spike, soak) tasarla ve her birinin yakaladığı başarısızlık modunu adlandır.
- Sabit uzunluk yerine input token'larının ortalama + stddev'i kullanarak gerçekçi bir prompt dağılımı inşa et.

## Sorun

LLM endpoint'ini 500 eşzamanlı kullanıcıda k6-test ettin. Dayandı. Yayınladın. Üretimde 200 gerçek kullanıcıda servis çöktü — P99 TTFT patladı, GPU'lar sabitlendi.

İki şey oldu. Birincisi, k6 500 özdeş prompt gönderdi — istek-coalescing ve prefix caching'in 500 eşzamanlı decode hallediyorsun gibi göstermesini sağladı, gerçekte bir tane hallediyordun. İkincisi, k6 streaming yanıtlardaki inter-token gecikmesini gözün deneyimlediği şekilde takip etmez; tek bir HTTP bağlantısı görür, değişen aralıklarda gelen 500 token değil.

LLM'ler için load testing kendi disiplinidir.

## Kavram

### GIL tuzağı (Locust)

Locust Python kullanır ve tokenization'ı client-side'da GIL altında çalıştırır. Yüksek eşzamanlılıkta tokenizer istek üretiminin arkasında queue'lanır. Raporlanan inter-token gecikme client-tarafı tokenization birikimini içerir. Sunucu yavaş sanıyorsun; test koşumu yavaş.

Çözüm: LLM-Locust eklentisi tokenization'ı ayrı process'lere taşır ya da compile edilmiş-dil koşumu (k6, tokenizers.rs kullanan LLMPerf) kullan.

### Prompt-tekdüzelik tuzağı

Bilinen tüm load tester'lar tek bir prompt configure etmene izin verir. 10.000 iterasyonluk bir loop testinde tam olarak aynı prompt her seferinde gönderilir. Sunucu her seferinde aynı prefix görür — prefix cache hit'leri %100'e yaklaşır, throughput harika görünür.

Çözüm: bir prompt dağılımından örnekle. LLMPerf `--mean-input-tokens 500 --stddev-input-tokens 150` kullanır — çeşitli uzunluklar, çeşitli içerikler.

### Dört load deseni

1. **Steady-state** — 30-60 dakika sabit RPS. Yakalar: baseline performans regresyon'ları.
2. **Ramp** — 15 dakika boyunca RPS'i 0'dan hedefe lineer artır. Yakalar: kapasite kırılım noktası, warm-up anomalileri.
3. **Spike** — 2 dakikalığına ani 3-10x RPS sonra geri. Yakalar: autoscaling gecikmesi, queue saturation, cold-start etkisi.
4. **Soak** — 4-8 saat steady-state. Yakalar: memory leak'ler, connection-pool kayması, observability taşması.

### 2026 araç eşlemesi

**LLMPerf** (Anyscale) — Python ama Rust-destekli tokenization. Ortalama/stddev prompt'lar. Streaming-aware. Performans run'ları için en iyi varsayılan.

**NVIDIA GenAI-Perf** — NVIDIA'nın referansı. Triton client kullanır; kapsamlı metrik kapsama. ITL'i TTFT'yi hariç tuttuğunu unutma; LLMPerf'inki içerir. İki araç aynı sunucu için farklı TPOT üretir.

**LLM-Locust** (TrueFoundry) — GIL tuzağını düzelten Locust eklentisi. Tanıdık Locust DSL + streaming metrikleri.

**guidellm** — büyük ölçekli sentetik benchmarking.

**k6 v2026.1.0** + **k6 Operator 1.0 GA (Eylül 2025)**:
- k6 kendisi (Go, compile edilmiş, GIL yok) streaming-aware metrikler ekledi.
- k6 Operator Kubernetes-native dağıtık testing için TestRun / PrivateLoadZone CRD'leri kullanır.
- CI/CD gate'leri ve SLA testing için en iyi.

**Vegeta** — Go, k6'dan daha basit. Constant-rate HTTP saturation. LLM-aware değil ama gateway / rate-limit testing için iyi.

**Locust 2.43.3 stock** — LLM için GIL tuzağı var. Yalnız LLM-Locust eklentisiyle.

### CI'da SLA gate'i

PR üzerinde k6 çalıştır:

- Baseline RPS'te her biri 30-50 iterasyon.
- Gate: P50/P95 TTFT, 5xx < %5, eşiğin altında TPOT.
- İhlalde build'i kır.

### Gerçekçi prompt dağılımı

Gerçek trafik örneklerinden (varsa) ya da yayınlanmış dağılımlardan (örn. sohbet için ShareGPT prompt'ları, kod için HumanEval) inşa et. Ortalama + stddev'i LLMPerf'e besle. Tek-prompt-loop'undan ne pahasına olursa olsun kaçın.

### Hatırlaman gereken sayılar

- k6 Operator 1.0 GA: Eylül 2025.
- k6 v2026.1.0: streaming-aware metrikler.
- Tipik LLMPerf run: eşzamanlılık X'te 100-1000 istek.
- Tipik CI gate'i: PR başına 30-50 iterasyon.
- Dört desen: steady, ramp, spike, soak.

## Kullan

`code/main.py` gerçekçi prompt dağılımıyla bir load test simüle eder, etkin TPOT ölçer ve uniform-prompt tuzağını gösterir.

## Yayınla

Bu ders `outputs/skill-load-test-plan.md` üretir. İş yükü ve SLA verildiğinde, aracı seçer ve dört load desenini tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Uniform vs gerçekçi dağılımı karşılaştır — fark nerede?
2. CI gate'i için k6 script'i yaz: 100 eşzamanlıda TTFT P95 < 800 ms, runtime 5 dakika.
3. Soak test'in saat başına 50 MB bellek büyümesi gösteriyor. Üç sebep adlandır ve aralarında seçim yapacak enstrümantasyonu söyle.
4. 10 RPS'ten 100 RPS'e spike test. Karpenter + vLLM production-stack yerindeyse (Faz 17 · 03 + 18) beklenen toparlanma zamanı ne?
5. GenAI-Perf TPOT=6ms raporluyor; LLMPerf aynı sunucuda TPOT=11ms raporluyor. Açıkla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| LLMPerf | "LLM koşumu" | Anyscale benchmark aracı, streaming-aware |
| GenAI-Perf | "NVIDIA aracı" | NVIDIA referans koşumu |
| LLM-Locust | "LLM'ler için Locust" | GIL tuzağını düzelten Locust eklentisi |
| guidellm | "sentetik benchmark" | Büyük ölçekli sentetik araç |
| k6 Operator | "K8s k6" | CRD-tabanlı dağıtık k6 |
| GIL tuzağı | "Python client overhead'i" | Tokenization birikimi raporlanan gecikmeyi şişirir |
| Prompt-tekdüzelik tuzağı | "tek-prompt yalanı" | Aynı prompt'la loop cache'i hit eder, throughput'u şişirir |
| Steady-state | "sabit yük" | N dakika düz RPS |
| Ramp | "lineer yukarı" | Süre boyunca 0'dan hedefe |
| Spike | "burst test" | Ani çarpan sonra geri |
| Soak | "uzun test" | Leak tespiti için saatler |

## İleri Okuma

- [TianPan — Load Testing LLM Applications](https://tianpan.co/blog/2026-03-19-load-testing-llm-applications)
- [PremAI — Load Testing LLMs 2026](https://blog.premai.io/load-testing-llms-tools-metrics-realistic-traffic-simulation-2026/)
- [NVIDIA NIM — Introduction to LLM Inference Benchmarking](https://docs.nvidia.com/nim/large-language-models/1.0.0/benchmarking.html)
- [TrueFoundry — LLM-Locust](https://www.truefoundry.com/blog/llm-locust-a-tool-for-benchmarking-llm-performance)
- [LLMPerf](https://github.com/ray-project/llmperf)
- [k6 Operator](https://github.com/grafana/k6-operator)
