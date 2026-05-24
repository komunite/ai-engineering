---
name: mc-evaluator
description: Bir policy'yi Monte Carlo rollout'larıyla değerlendir ve mümkünse DP karşılaştırmasıyla birlikte bir yakınsama raporu üret.
version: 1.0.0
phase: 9
lesson: 3
tags: [rl, monte-carlo, evaluation]
---

Bir environment (episodik, reset+step API'sine sahip) ve bir policy verildiğinde şu çıktıyı üret:

1. Yöntem. First-visit vs every-visit MC. Gerekçe.
2. Episode bütçesi. Hedef sayı, varyans teşhisi, beklenen standard error.
3. Exploration planı. ε zamanlaması (gerekirse) ya da exploring starts.
4. Altın standart karşılaştırma. Tabular ise DP-optimal V*; aksi halde bir Q-learning / PPO baseline'ından bir alt/üst sınır.
5. Sonlandırma kontrolü. Maksimum adım sınırı, timeout'lar, sonlanmayan trajectory'lerin işlenmesi.

Sonlu horizon sınırı olmadan episodik olmayan görevlerde MC çalıştırma. Tabular görevlerde state başına 100'den az episode'dan V^π tahminleri raporlama. Sıfır varyanslı aksiyona sahip herhangi bir policy'yi exploration riski olarak işaretle.
