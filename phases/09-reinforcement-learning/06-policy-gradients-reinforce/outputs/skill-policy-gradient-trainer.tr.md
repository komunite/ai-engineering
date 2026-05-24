---
name: policy-gradient-trainer
description: Belirli bir görev için REINFORCE / actor-critic / PPO eğitim konfigürasyonu üret ve varyans sorunlarını teşhis et.
version: 1.0.0
phase: 9
lesson: 6
tags: [rl, policy-gradient, reinforce]
---

Bir environment (ayrık / sürekli aksiyonlar, horizon, ödül istatistikleri) verildiğinde şu çıktıyı üret:

1. Policy head. Softmax (ayrık) ya da Gaussian (sürekli), parametre sayılarıyla.
2. Baseline. Yok (vanilla), running mean, öğrenilmiş `V̂(s)` ya da A2C critic.
3. Varyans kontrolleri. Varsayılan açık reward-to-go, dönüş normalizasyonu, gradient clip değeri.
4. Entropy bonus. Katsayı β ve decay zamanlaması.
5. Batch boyutu. Update başına episode sayısı; on-policy veri tazeliği kontratı.

500 adımdan uzun horizon'larda baseline'sız REINFORCE'u kabul etme. Sürekli aksiyon kontrolünü softmax head ile kabul etme. `β = 0` ve gözlemlenen policy entropy < 0.1 olan herhangi bir koşuyu entropy-collapsed olarak işaretle.
