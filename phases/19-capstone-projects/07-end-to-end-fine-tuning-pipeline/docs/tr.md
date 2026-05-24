# Capstone 07 — Uçtan Uca Fine-Tuning Pipeline'ı (Data'dan SFT'den DPO'dan Serve'e)

> Kendi verinde eğitilmiş, kendi tercihlerinde DPO-aligned, quantize edilmiş, speculative-decoded ve ölçülebilir $/1M token'da sunulan bir 8B model. 2026 açık stack'i Axolotl v0.8, TRL 0.15, iterasyon için Unsloth, quantization için GPTQ/AWQ/GGUF, serving için EAGLE-3'lü vLLM 0.7. Capstone tüm pipeline'ı yeniden üretilebilir şekilde çalıştırmak — YAML in, sunulan endpoint out — ve 2026 Model Openness Framework altında bir model card yayınlamak.

**Tür:** Bitirme
**Diller:** Python (pipeline), YAML (config'ler), Bash (script'ler)
**Ön koşullar:** Faz 2 (ML), Faz 3 (DL), Faz 7 (transformer'lar), Faz 10 (LLM'ler sıfırdan), Faz 11 (LLM engineering), Faz 17 (infrastructure), Faz 18 (safety)
**Egzersize edilen fazlar:** P2 · P3 · P7 · P10 · P11 · P17 · P18
**Süre:** 35 saat

## Sorun

2026'da her ciddi yapay zeka ekibi elinde bir fine-tuning pipeline'ı tutar. Bir frontier base model yayınladıkları için değil, downstream adaptation — domain SFT, etiketli tercihlere karşı DPO, speculative decoding için distill edilmiş draft'lar, EAGLE-3 ile serving — ölçülebilir kazançların yaşadığı yer olduğu için. Axolotl v0.8 multi-GPU SFT config'lerini yönetir. TRL 0.15 DPO ve GRPO'yu yönetir. Unsloth sana hızlı tek-GPU iterasyonu sağlar. EAGLE-3'lü vLLM 0.7 decode throughput'unu kalite kaybı olmadan 2-3x iter. Tooling çalışıyor; zanaat YAML'larda, data hijyeninde ve eval disiplininde.

Bir 8B base'i (Llama 3.3, Qwen3 veya Gemma 3) task-spesifik veride önce SFT'den sonra DPO'dan geçireceksin, serving için quantize edeceksin ve lm-evaluation-harness, RewardBench-2, MT-Bench-v2 ve MMLU-Pro'ya karşı kazançları ölçeceksin. 2026 Model Openness Framework altında bir model card üreteceksin. Amaç yeniden üretilebilirlik — tek komut tüm pipeline'ı uçtan uca yeniden çalıştırır.

## Kavram

Pipeline'ın beş aşaması var. **Data**: dedup (MinHash / Datatrove), quality filter (Nemotron-CC tarzı sınıflandırıcı), PII scrub, public benchmark contamination'a karşı split-hygiene check. **SFT**: Axolotl YAML, 8xH100'de ZeRO-3, cosine schedule, packed sequences, 2-3 epoch. **DPO veya GRPO**: TRL config, 1 epoch, ya insan-etiketli ya da model-yargılı preference çiftleri, beta tuning. **Quantize**: deployment esnekliği için GPTQ + AWQ + GGUF. **Serve**: EAGLE-3 speculative head'lerle vLLM 0.7 (veya SpecForge ile SGLang), K8s deployment'ı, queue-wait'te HPA.

Ablation'lar teslimat: üç task-spesifik benchmark üzerinde sadece-SFT vs SFT+DPO vs SFT+GRPO. Serving metrik'leri: batch 1 / 8 / 32'de token/s, EAGLE-3 acceptance oranı, $/1M token. Safety eval: Llama Guard 4 pass oranı. Model card: bias değerlendirmeleri, yeniden üretilebilirlik seed'leri, data licensing.

## Mimari

```
ham data (HF dataset'leri + dahili)
    |
    v
Datatrove dedup + Nemotron-CC quality filter + PII scrub
    |
    v
split hijyen (MMLU-Pro contamination check)
    |
    v
Axolotl SFT config (YAML)  ---> 8xH100, ZeRO-3
    |
    v
TRL DPO / GRPO config       ---> 4xH100, 1 epoch
    |
    v
GPTQ + AWQ + GGUF quantize
    |
    v
vLLM 0.7 + EAGLE-3 speculative decoding
    |
    v
K8s deployment, queue-wait'te HPA
    |
    v
lm-eval-harness + RewardBench-2 + MT-Bench-v2 + MMLU-Pro
    |
    v
model card (2026 MOF) + safety eval (Llama Guard 4)
```

## Stack

- Data: dedup için Datatrove, quality için Nemotron-CC sınıflandırıcı, PII için Presidio
- Base: Llama 3.3 8B, Qwen3 14B veya Gemma 3 12B
- SFT: ZeRO-3, Flash Attention 3, packed sequence'lı Axolotl v0.8
- Preference tuning: DPO veya GRPO için TRL 0.15; tek-GPU iterasyonu için Unsloth
- Quantization: GPTQ (Marlin), AWQ, llama.cpp üzerinden GGUF
- Serving: EAGLE-3 speculative decoding'li vLLM 0.7 (veya SGLang 0.4 + SpecForge)
- Eval: lm-evaluation-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro
- Safety eval: Llama Guard 4, ShieldGemma-2
- Infrastructure: Kubernetes + NVIDIA device plugin, queue-wait metriğinde HPA
- Observability: training için W&B, inference için Langfuse

## İnşa Et

1. **Data pipeline.** Ham korpusta Datatrove dedup çalıştır. Nemotron-CC tarzı quality sınıflandırıcı uygula. Presidio PII scrub'lar. Açık seed'le train/val split'lerini yaz.

2. **Contamination check.** Her validation split için MMLU-Pro, MT-Bench-v2, RewardBench-2 test set'lerine karşı MinHash hesapla. Herhangi bir overlap'i reddet.

3. **Axolotl SFT.** ZeRO-3, FA3, sequence packing'li YAML. 8xH100'de 2-3 epoch. W&B'ye logla.

4. **TRL DPO / GRPO.** SFT checkpoint'ini al, preference çiftlerinde bir epoch DPO çalıştır (veya math/code'da doğrulanabilir reward ile GRPO). Beta sweep et.

5. **Quantize.** Üç quant üret: GPTQ-INT4-Marlin, AWQ-INT4, llama.cpp için GGUF-Q4_K_M. Boyutu ve nominal throughput'u kaydet.

6. **Speculative decoding ile sun.** Red Hat Speculators üzerinden eğitilmiş EAGLE-3 draft head'leri ile vLLM 0.7 config'i. Batch 1 / 8 / 32'de acceptance oranını ve tail latency'yi ölç. Aynı eval'de Anthropic / OpenAI'a karşı $/1M token raporla.

7. **Eval matrisi.** lm-eval-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro'yu base, sadece-SFT, SFT+DPO, SFT+GRPO üzerinde çalıştır. Bir tablo üret.

8. **Safety eval.** Dev set'te Llama Guard 4 pass oranı. ShieldGemma-2 output filtresi.

9. **Model card.** MOF 2026 template'i: data, training, eval, safety, license, YAML'lar ve commit SHA'larla yeniden üretilebilirlik bölümü.

## Kullan

```
$ ./pipeline.sh config/llama3.3-8b-domainX.yaml
[data]    300k dedup edildi, 12k filtrelendi, 280k kabul edildi (seed=7)
[SFT]     3 epoch, 8xH100, 6h12m, val loss 1.42 -> 1.03
[DPO]     1 epoch, beta=0.08, 4xH100, 1h40m
[quant]   GPTQ-INT4 4.6 GB, AWQ-INT4 4.8 GB, GGUF-Q4_K_M 5.1 GB
[serve]   vLLM 0.7, EAGLE-3 acceptance 0.74, p99 126ms @ bs=8
[eval]    MMLU-Pro +3.2, MT-Bench-v2 +0.41, RewardBench-2 +0.08
[card]    model-card.md 2026 MOF altında üretildi
```

## Yayınla

`outputs/skill-finetuning-pipeline.md` teslimat'ı açıklar. Tek bir komut data'yı SFT'den DPO'dan quant'tan serve'den eval'den geçirir ve bir model card + sunulan endpoint emit eder.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Base'e karşı eval delta'sı | Hedef task'larda ölçülen kazanç (MMLU-Pro, MT-Bench-v2, task-spesifik) |
| 20 | Pipeline yeniden üretilebilirliği | Tek komut identik seed'lerle uçtan uca yeniden çalıştırır |
| 20 | Data hijyeni | Dedup oranı, PII scrub kapsama, contamination check yeşil |
| 20 | Serving verimliliği | bs=1/8/32'de token/s, EAGLE-3 acceptance oranı, $/1M token |
| 15 | Model card + safety eval | 2026 MOF eksiksizliği + Llama Guard 4 pass oranı |
| **100** | | |

## Alıştırmalar

1. Aynı task-spesifik benchmark'ta sadece-SFT vs SFT+DPO vs SFT+GRPO çalıştır. Hangi preference method'unun kazandığını ve ne kadarla kazandığını raporla.

2. Llama 3.3 8B'yi Qwen3 14B ile değiştir. Eşleştirilmiş kalitede $/1M token'ı ölç.

3. EAGLE-3 acceptance oranını generic ShareGPT'ye karşı domain verisinde ölç. Delta'yı ve latency bütçeleri için ne anlama geldiğini raporla.

4. %1 contamination enjekte et (MMLU-Pro cevaplarını training verisine sızdır) ve eval'i yeniden çalıştır. MMLU-Pro doğruluğunun gerçekçi olmayan şekilde sıçradığını izle. Bunu yakalayan bir contamination-check CI gate'i inşa et.

5. Full fine-tune'a alternatif olarak LoRA SFT ekle. 10x daha az memory'de kalite gap'ini ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Axolotl | "SFT trainer'ı" | SFT, DPO ve distillation için birleşik YAML-sürücülü trainer |
| TRL | "Preference tuner" | LLM'ler üzerinde DPO, GRPO, PPO için Hugging Face kütüphanesi |
| GRPO | "Group-relative policy optimization" | Doğrulanabilir reward'larla DeepSeek R1'in RL tarifi |
| EAGLE-3 | "Speculative decoding draft'ı" | N token ileri tahmin eden draft head'leri; vLLM target model ile doğrular |
| MOF | "Model Openness Framework" | Model release'lerini data, kod, license'ta derecelendiren 2026 standardı |
| Contamination check | "Split hijyeni" | Test-set'in training'e sızıntısının MinHash-tabanlı tespiti |
| Acceptance oranı | "EAGLE / MTP metriği" | Target model tarafından kabul edilen draft'lanmış token'ların oranı |

## İleri Okuma

- [Axolotl dokümantasyonu](https://axolotl-ai-cloud.github.io/axolotl/) — referans SFT / DPO trainer'ı
- [TRL dokümantasyonu](https://huggingface.co/docs/trl) — DPO ve GRPO referans implementasyonları
- [Unsloth](https://github.com/unslothai/unsloth) — tek-GPU iterasyonu referansı
- [DeepSeek R1 makalesi (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948) — GRPO methodology'si
- [vLLM + EAGLE-3 dokümantasyonu](https://docs.vllm.ai) — referans serving stack'i
- [SGLang SpecForge](https://github.com/sgl-project/SpecForge) — alternatif speculative-decoding trainer'ı
- [Model Openness Framework 2026](https://isocpp.org/) — açık-release derecelendirme standardı
- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) — kanonik eval runner'ı
