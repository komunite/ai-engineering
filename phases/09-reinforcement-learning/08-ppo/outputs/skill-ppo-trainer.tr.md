---
name: ppo-trainer
description: Belirli bir environment için PPO eğitim konfigürasyonu ve teşhis planı üret.
version: 1.0.0
phase: 9
lesson: 8
tags: [rl, ppo, policy-gradient]
---

Bir environment ve eğitim bütçesi verildiğinde şu çıktıyı üret:

1. Rollout boyutu. `N` env × `T` adım.
2. Update zamanlaması. `K` epoch, minibatch boyutu, LR zamanlaması.
3. Surrogate parametreleri. `ε` (clip), `c_v`, `c_e`, advantage normalizasyonu açık.
4. Advantage. Açık `γ` ve `λ` ile GAE(`λ`).
5. Teşhis planı. Alert'lerle birlikte KL, clip fraction, explained variance eşikleri.

`K > 30` ya da `ε > 0.3` (güvensiz trust region) kabul etme. Advantage normalizasyonu ya da KL/clip izlemesi olmadan hiçbir PPO koşusunu kabul etme. 0.4'ün üzerinde sürekli kalan clip fraction'ı drift olarak işaretle.
