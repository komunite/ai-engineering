---
name: actor-critic-trainer
description: Belirli bir environment için A2C / A3C / GAE konfigürasyonu üret; advantage tahmini ve loss ağırlıklarını belirt.
version: 1.0.0
phase: 9
lesson: 7
tags: [rl, actor-critic, gae]
---

Bir environment ve compute bütçesi verildiğinde şu çıktıyı üret:

1. Paralellik. A2C (GPU batched) vs A3C (CPU async) ve worker sayısı.
2. Rollout uzunluğu T. Update başına env başına adım sayısı.
3. Advantage tahmincisi. n-step ya da GAE(λ); λ'yı belirt.
4. Loss ağırlıkları. `c_v` (value), `c_e` (entropy), gradient clip.
5. Learning rate'ler. Actor ve critic (ayrı kullanılıyorsa).

Horizon'u 1000'den büyük environment'larda tek worker'lı A2C'yi kabul etme (çok on-policy, çok yavaş). Advantage normalizasyonu olmadan teslim etme. `c_e = 0` ve gözlemlenen entropy < 0.1 olan herhangi bir koşuyu entropy-collapsed olarak işaretle.
