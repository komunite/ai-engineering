---
name: rlhf-architect
description: Bir dil modeli için RM, KL ve veri stratejisi dahil bir RLHF / DPO / GRPO alignment pipeline'ı tasarla.
version: 1.0.0
phase: 9
lesson: 9
tags: [rl, rlhf, alignment, llm]
---

Bir base LM, hedef davranış (alignment / akıl yürütme / refusal / agent) ve bir preference ya da verifier bütçesi verildiğinde şu çıktıyı üret:

1. Aşama. SFT? RM? DPO? GRPO? Gerekçesiyle.
2. Preference ya da verifier kaynağı. İnsanlar, AI feedback, kural tabanlı, unit-test-pass ya da reward distillation.
3. KL stratejisi. Sabit β, adaptif β ya da DPO (örtük KL).
4. Teşhisler. Ortalama KL, ödül kararlılığı, over-optimization koruması (holdout insan değerlendirmesi).
5. Güvenlik kapısı. Red-team kümesi, refusal oranı, helpfulness RM'den ayrı safety RM.

KL monitörü olmadan RLHF-PPO teslim etme. Hedef policy'den daha küçük bir RM kullanma. Yalnızca uzunluğa dayalı ödülleri kabul etme. Kör bir insan değerlendirme setini ayırmayan herhangi bir pipeline'ı over-optimization koruması eksik olarak işaretle.
