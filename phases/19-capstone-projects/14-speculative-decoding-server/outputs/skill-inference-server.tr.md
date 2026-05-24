---
name: inference-server
description: EAGLE-3 veya P-EAGLE draft'lar, K8s autoscaling ve tam throughput/latency/cost raporuyla speculative-decoding inference server gönder.
version: 1.0.0
phase: 19
lesson: 14
tags: [capstone, inference, vllm, sglang, eagle-3, p-eagle, speculative-decoding, quantization, hpa]
---

İki açık target model (Llama 3.3 70B ve Qwen3-Coder-30B MoE veya GPT-OSS-120B) verildiğinde, speculative decoding, kuantizasyon ve Kubernetes autoscaling ile bir production serving stack gönder. Ölçülen speedup ve tail-latency sayılarını yayınla.

Build planı:

1. Target modelleri FP8 Marlin kuantizasyon ile vLLM 0.7 (veya SGLang 0.4) altında deploy et.
2. Red Hat Speculators'tan hizalı bir EAGLE-3 draft yükle (veya SpecForge ile eğit).
3. Baseline sayılar: speculation olmadan batch 1/8/32'de tokens/s ve p50/p99 latency.
4. EAGLE-3'ü etkinleştir. Aynı benchmark'ı yeniden çalıştır. Speedup, acceptance oranı ve p99 tail-latency delta'sını raporla.
5. P-EAGLE parallel speculation'ı etkinleştir; daha derin ağaçların yardım ettiği vs zarar verdiği inflection noktayı raporla.
6. Benchmark'ları distribution'lar arasında çalıştır: ShareGPT, HumanEval, domain verisi. Acceptance-rate drift'ini yayınla.
7. İkinci target model (MoE) üzerinde tekrarla; draft acceptance'ında routing-noise hassasiyetini tespit et.
8. `queue_wait_ms` izleyen HPA ile Kubernetes'e deploy et. Yük üçe katlandığında scale-out gösterimi yap.
9. Eşleşen eval'lerde Anthropic Claude Sonnet 4.7 ve OpenAI GPT-5.4'e karşı $/1M token karşılaştır.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Baseline'a karşı ölçülen speedup | Her iki modelde eşleşen kalitede 2.5x+ throughput |
| 20 | Gerçekçi trafik üzerinde acceptance oranı | Distribution başına acceptance-rate raporu |
| 20 | P99 tail-latency disiplini | Speculation ile ve olmadan batch 1/8/32'de p99 |
| 20 | Ops | K8s deploy, queue-wait üzerinde HPA, smooth rollout, drain-first upgrade |
| 15 | Yazım ve metodoloji | Metriklerin net türetilmesi, eşleşen baseline'lar |

Sert ret durumları:

- Tail latency olmadan steady-state throughput raporlamak.
- Queue-wait yerine CPU üzerinde HPA. GPU saturation altında thrash yapar.
- Draft-target version hizalamasını görmezden gelmek. Drifted draft'lar speculation olmamaktan daha pahalıdır.
- Hosted API'lerin prompt-caching indirimlerini atlayan maliyet karşılaştırmaları.

Reddetme kuralları:

- Rollout drain olmadan serve etmeyi reddet. Request'ler uçuştayken in-place upgrade diskalifiyedir.
- Distribution'lar arasında aggregate edilmiş acceptance oranı raporlamayı reddet. Distribution başına zorunlu.
- Eşleşen non-speculative sayı olmadan bs=32'de speculative-decoding kazanımı iddia etmeyi reddet.

Çıktı: vLLM / SGLang config'leri, EAGLE-3 draft download script'i, K8s deployment manifest'leri, queue-wait üzerinde HPA config'i, ShareGPT / HumanEval / domain verisi için benchmark harness'i, $/1M token karşılaştırma tablosu ve speculative decoding'in tanıttığı üç tail-latency regression'ı ile her birini düzelten mitigation'ı (batch gating, ngram fallback, kuantizasyon tweak'i) adlandıran bir yazımı içeren bir repo.
