---
name: finetuning-pipeline
description: Ablation, kuantizasyon ve 2026 Model Openness Framework model card'ı ile tekrarlanabilir data-to-SFT-to-DPO-to-serve fine-tuning pipeline'ı çalıştır.
version: 1.0.0
phase: 19
lesson: 07
tags: [capstone, fine-tuning, axolotl, trl, dpo, grpo, vllm, eagle-3, mof]
---

Bir base model (Llama 3.3 8B, Qwen3 14B veya Gemma 3 12B) ve task-specific bir dataset verildiğinde, sunulan bir endpoint ve tekrarlanabilir bir model card üreten tek komutluk bir pipeline kur.

Build planı:

1. Data aşaması: Datatrove dedup, Nemotron-CC tarzı kalite filtresi, Presidio PII scrub, seed'li train/val split'leri.
2. Contamination check: MMLU-Pro, MT-Bench-v2, RewardBench-2'ye karşı MinHashLSH. Örtüşmede reddet.
3. SFT: ZeRO-3, Flash Attention 3, paketlenmiş sequence'lar ile Axolotl v0.8, 8xH100 üzerinde 2-3 epoch.
4. Preference tuning: TRL 0.15 DPO (veya doğrulanabilir reward'larla GRPO) 1 epoch için, beta sweep'i.
5. Quantize: GPTQ-INT4-Marlin + AWQ-INT4 + GGUF-Q4_K_M.
6. Serve: vLLM 0.7 ile EAGLE-3 speculative decoding (Red Hat Speculators veya SGLang SpecForge üzerinden draft head'leri). Queue-wait üzerinde HPA ile K8s deployment.
7. Eval: base/SFT-only/SFT+DPO/SFT+GRPO arasında lm-evaluation-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro.
8. Safety: Llama Guard 4 geçiş oranı, ShieldGemma-2 output filter.
9. Data, training, eval, safety, reproducibility bölümleriyle 2026 Model Openness Framework altında model card.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Base'e karşı eval delta'sı | MMLU-Pro, MT-Bench-v2, task-specific benchmark'larda ölçülen kazanım |
| 20 | Pipeline reproducibility'si | Aynı seed'lerle tek komutluk rerun eşleşen hash'ler verir |
| 20 | Data hijyeni | Dedup oranı, PII scrub kapsamı, contamination check yeşil |
| 20 | Serving verimliliği | Batch 1/8/32'de tokens/s, EAGLE-3 acceptance, $/1M token |
| 15 | Model card + safety eval | 2026 MOF tamlığı + Llama Guard 4 geçiş oranı |

Sert ret durumları:

- MinHash contamination check'ini atlayan pipeline'lar. MMLU-Pro'yu eğitime sızdırmak klasik eval-cheating failure mode'dur.
- Seed veya YAML eklenmeden yapılan eğitim çalıştırmaları. Reproducibility sert gereksinimdir.
- EAGLE-3 veya eşdeğer speculative decoding konfigürasyonu olmadan serving. Baseline tokens/s 2026 bar'ı değildir.
- Eksik safety eval. Her fine-tune Llama Guard 4 geçiş oranıyla gönderilir.

Reddetme kuralları:

- lm-eval-harness commit SHA'sını eklemeden benchmark skoru iddia eden model card yayınlamayı reddet.
- Lisansı türev modelleri yasaklayan veriler üzerinde fine-tune yapmayı reddet. MOF data licensing'i derecelendirir.
- Eval matrisinde kalite kaybını ölçmeden kuantize edilmiş modeli göndermeyi reddet.

Çıktı: pipeline orkestratörü, Llama 3.3 8B + bir alternatif base için YAML'lar, SFT ve DPO W&B run log'ları, kuantize artifact'ler, sunulan endpoint, üç benchmark'lı eval matrisi, safety eval, 2026 MOF model card'ı ve yakalayıp düzelttiğin en büyük üç data-hijyeni sorunu üzerine bir yazımı içeren bir repo.
