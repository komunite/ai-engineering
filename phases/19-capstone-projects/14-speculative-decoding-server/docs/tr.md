# Capstone 14 — Speculative-Decoding Inference Sunucusu

> vLLM 0.7'deki EAGLE-3 gerçek trafikte 2.5-3x throughput yayınlıyor. P-EAGLE (AWS 2026) paralel speculation'ı daha da ileri itti. SGLang'ın SpecForge'u ölçekte draft head'leri eğitti. Red Hat'in Speculators hub'ı yaygın açık modeller için aligned draft'lar yayınladı. TensorRT-LLM speculative decoding'i NVIDIA'da first-class hale getirdi. 2026 üretim serving stack'i EAGLE-ailesi draft'larla vLLM veya SGLang, FP8 veya INT4 quantization ve queue-wait'te HPA. Bu capstone, iki açık modeli baseline throughput'unun 2.5x+'ında full bir tail-latency raporuyla sunmak.

**Tür:** Bitirme
**Diller:** Python (serving), C++ / CUDA (kernel incelemesi), YAML (config'ler)
**Ön koşullar:** Faz 3 (deep learning), Faz 7 (transformer'lar), Faz 10 (LLM'ler sıfırdan), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P3 · P7 · P10 · P17
**Süre:** 30 saat

## Sorun

Speculative decoding 2026'da bir commodity haline geldi. EAGLE-3 draft head'leri target model'in hidden state'leri üzerinde eğitilir ve N token ileri tahmin eder; target model tek geçişte doğrular. %60-80 acceptance oranları 2-3x uçtan uca throughput'a çevrilir. vLLM 0.7 bunu nativ entegre eder. SGLang + SpecForge sana training pipeline'ını verir. Red Hat'in Speculators'ı Llama 3.3 70B, Qwen3-Coder-30B MoE, GPT-OSS-120B için aligned draft'lar yayınlar.

Zanaat serving operasyonlarında, modelde değil. Acceptance oranı trafik dağılımı ile drift eder (ShareGPT vs code vs domain verisi). Reject altında tail latency speculation'sızdan daha kötü — birden çok batch size'da p99 raporlamalısın, sadece steady-state token/sec değil. Anthropic / OpenAI API'ye karşı 1M token başına maliyet credibility kaldıracı.

## Kavram

Speculative decoding'in iki katmanı var. Bir **draft** modeli (EAGLE-3 head, ngram veya daha küçük target-aligned model) adım başına k aday token önerir. **Target** modeli k'nın hepsini tek geçişte doğrular; kabul edilen prefix greedy path'i değiştirir. Acceptance oranı draft-target hizalamasına ve input dağılımına bağlı.

EAGLE-3 çoğu trafikte ngram draft'ları yener. P-EAGLE daha derin draft ağaçları için paralel speculation çalıştırır. Trade-off: reject'te P99 latency daha yüksek çünkü verify geçişi daha büyük. Serving config bunu yüzeylemek için batch-size-bucket'lanmış latency raporlamalı.

Deployment Kubernetes. vLLM 0.7 GPU başına veya tensor-parallel shard başına bir replica çalıştırır. HPA CPU yerine queue-wait'te autoscale eder. FP8 (Marlin) ve INT4 (AWQ) quant'lar GPU memory'sini bir H100 / H200 envelope içinde tutar. Uçtan uca rapor throughput, acceptance oranı, batch 1/8/32'de p50/p99 ve $/1M token.

## Mimari

```
istek ingress
    |
    v
vLLM sunucusu (0.7) veya SGLang (0.4)
    |
    +-- draft: EAGLE-3 head'leri | P-EAGLE paralel | ngram fallback
    +-- target: Llama 3.3 70B | Qwen3-Coder-30B | GPT-OSS-120B
    |     quantized FP8-Marlin veya INT4-AWQ
    |
    v
verify geçişi: k draft token'ı target boyunca batch'le
    |
    v (prefix kabul; reject edilen suffix için resample)
    v
client'a token stream geri
    |
    v
Prometheus metrik'leri: throughput, acceptance oranı, queue wait, latency p50/p99
    |
    v
queue-wait metriğinde HPA
```

## Stack

- Serving: vLLM 0.7 veya SGLang 0.4
- Speculative method'ları: EAGLE-3 draft head'leri, P-EAGLE paralel speculation, ngram fallback
- Draft training: SpecForge (SGLang) veya Red Hat Speculators
- Target modeller: Llama 3.3 70B, Qwen3-Coder-30B MoE, GPT-OSS-120B
- Quantization: FP8 (Marlin), INT4 AWQ
- Deployment: Kubernetes + NVIDIA device plugin; queue-wait metriğinde HPA
- Eval: domain-spread acceptance ölçümü için ShareGPT, MT-Bench-v2, GSM8K, HumanEval
- Referans: vendor baseline'ı için TensorRT-LLM speculative decoding

## İnşa Et

1. **Target model hazırlama.** Llama 3.3 70B'yi seç. Marlin üzerinden FP8'e quantize et. 1xH100'de (veya 2x tensor-parallel) vLLM 0.7 altında deploy et.

2. **Draft kaynağı.** Red Hat Speculators'tan aligned bir EAGLE-3 draft head çek (veya SpecForge üzerinden bir tane eğit). vLLM'in speculative-decoding config'ine yükle.

3. **Baseline sayılar.** Speculation'dan önce: batch 1/8/32'de token/s, p50/p99 latency, GPU utilization. Yayınla.

4. **EAGLE-3 enable et.** Config'i flip et; aynı benchmark'ı yeniden çalıştır. Hızlanma, acceptance oranı, p99 tail-latency delta raporla.

5. **P-EAGLE.** Paralel speculation enable et; serial EAGLE-3'e karşı daha derin draft ağacını ölç. P-EAGLE'ın yardım ettiği vs zarar verdiği inflection noktasını raporla.

6. **Domain trafiği.** Aynı sunucudan ShareGPT vs HumanEval vs domain-spesifik trafik çalıştır. Dağılım başına acceptance oranını ölç. Draft'ların ne zaman drift ettiğini belirle.

7. **İkinci target modeli.** Aynı pipeline'ı Qwen3-Coder-30B MoE üzerinde çalıştır. Draft daha zor (MoE routing noise'i). Raporla.

8. **K8s HPA.** `queue_wait_ms` izleyen HPA'lı K8s altında deploy et. Yük üç katına çıktığında scale-out göster.

9. **Maliyet karşılaştırması.** Aynı eval'de Anthropic Claude Sonnet 4.7 ve OpenAI GPT-5.4'e karşı $/1M token hesapla. Yayınla.

## Kullan

```
$ curl https://infer.example.com/v1/chat/completions -d '{"messages":[...]}'
[serve]     vLLM 0.7, Llama 3.3 70B FP8, EAGLE-3 aktif
[decode]    bs=8, accepted_tokens_per_step=3.2, acceptance_rate=0.76
[latency]   ilk-token 42ms, full-response 980ms (620 token)
[cost]      sürdürülen throughput'ta 1M output token başına $0.34
```

## Yayınla

`outputs/skill-inference-server.md` teslimat'ı açıklar. Speculative decoding'li ölçülmüş bir serving stack'i, full bir benchmark raporu ve bir K8s deployment'ı.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Baseline'a karşı ölçülen hızlanma | İki modelde eşleştirilmiş kalitede 2.5x+ throughput |
| 20 | Gerçekçi trafikte acceptance oranı | Per-dağılım acceptance-rate raporu |
| 20 | P99 tail-latency disiplini | Speculation'lı ve speculation'sız batch 1/8/32'de p99 |
| 20 | Ops | K8s deploy, queue-wait'te HPA, rollout pürüzsüz |
| 15 | Yazım ve methodology | Neyin değiştiğinin ve nedeninin net açıklaması |
| **100** | | |

## Alıştırmalar

1. Draft target'ten bir versiyon geri olduğunda acceptance-oranı degradation'ı ölç (örn. Llama 3.3 -> 3.4 drift). Bir monitoring alert inşa et.

2. ngram-fallback implement et: EAGLE-3 acceptance'ı bir eşiğin altına düşerse ngram draft'larına geç. Güvenilirlik iyileşmesini raporla.

3. Kontrollü bir MoE deneyi çalıştır: routing noise enjekte edilmiş vs edilmemiş aynı Qwen3-Coder-30B. Draft acceptance duyarlılığını ölç.

4. H200'e (141 GB) extend et. Replica başına model-boyut headroom'unu ve un-quantized Llama 3.3 70B sunup sunamayacağını raporla.

5. Aynı H100 hardware'de TensorRT-LLM speculative decoding benchmark'la. vLLM'e karşı nerede kazandığını raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Draft model | "Speculator" | Target'ın doğrulayacağı N token öneren küçük model |
| EAGLE-3 | "2026 draft mimarisi" | Target hidden state'lerinde eğitilmiş draft head'i; ~%75 acceptance |
| P-EAGLE | "Paralel speculation" | Tek target geçişinde doğrulanan draft branch ağacı |
| Acceptance oranı | "Hit rate" | Resample olmadan kabul edilen draft'lanmış token'ların oranı |
| Quantization | "FP8 / INT4" | GPU memory'sine daha çok model sığdırmak için düşük-precision ağırlıklar |
| Queue wait | "HPA metriği" | Bir isteğin inference başlamadan önce pending queue'da beklediği süre |
| Speculators hub | "Aligned draft'lar" | Yaygın açık modeller için Red Hat Neural Magic EAGLE draft'ları hub'ı |

## İleri Okuma

- [vLLM EAGLE ve P-EAGLE dokümantasyonu](https://docs.vllm.ai) — referans serving stack'i
- [P-EAGLE (AWS 2026)](https://aws.amazon.com/blogs/machine-learning/p-eagle-faster-llm-inference-with-parallel-speculative-decoding-in-vllm/) — paralel speculative decoding makalesi + entegrasyon
- [SGLang SpecForge](https://github.com/sgl-project/SpecForge) — draft-head training pipeline'ı
- [Red Hat Speculators](https://github.com/neuralmagic/speculators) — aligned draft hub'ı
- [TensorRT-LLM speculative decoding](https://nvidia.github.io/TensorRT-LLM/) — vendor alternatifi
- [Fireworks.ai serving mimarisi](https://fireworks.ai/blog) — ticari referans
- [EAGLE-3 makalesi (arXiv:2503.01840)](https://arxiv.org/abs/2503.01840) — method makalesi
- [vLLM repository'si](https://github.com/vllm-project/vllm) — kod ve benchmark'lar
