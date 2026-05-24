---
name: marl-architect
description: Belirli bir görev için doğru multi-agent RL rejimini (IPPO, CTDE, self-play, league) seç.
version: 1.0.0
phase: 9
lesson: 10
tags: [rl, multi-agent, marl, self-play]
---

`n` agent'lı bir görev verildiğinde şu çıktıyı üret:

1. Rejim sınıflandırması. Kooperatif / adversaryal / general-sum. Gerekçelendir.
2. Algoritma. IPPO / MAPPO / QMIX / self-play / league. Coupling sıkılığına ve ödül yapısına bağlanan gerekçe.
3. Bilgi erişimi. Centralized training (critic'e hangi global bilgi gidiyor)? Decentralized execution?
4. Credit assignment. Counterfactual baseline, value decomposition ya da reward shaping.
5. Exploration planı. Agent başına entropy, population-based training ya da league.

Sıkı bağlı kooperatif görevlerde bağımsız Q-learning'i kabul etme. Cycle riski olan general-sum'da self-play önerme. Sabit-rakipli değerlendirme olmadan herhangi bir MARL pipeline'ını işaretle (cherry-picked self-play sayıları yaygındır).
