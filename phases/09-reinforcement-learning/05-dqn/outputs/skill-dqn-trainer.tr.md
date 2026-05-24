---
name: dqn-trainer
description: Ayrık aksiyonlu bir RL görevi için DQN eğitim konfigürasyonu üret (replay buffer, target sync, ε zamanlaması, reward clipping).
version: 1.0.0
phase: 9
lesson: 5
tags: [rl, dqn, deep-rl]
---

Ayrık aksiyonlu bir environment (gözlem shape'i, aksiyon sayısı, horizon, ödül ölçeği) verildiğinde şu çıktıyı üret:

1. Ağ. Mimari (MLP / CNN / Transformer), feature boyutu, derinlik.
2. Replay buffer. Kapasite, minibatch boyutu, warmup boyutu.
3. Target network. Sync stratejisi (her C adımda hard sync ya da soft τ).
4. Exploration. ε başlangıç / bitiş / zamanlama uzunluğu.
5. Loss. Huber vs MSE, gradient clip değeri, reward clipping kuralı.
6. Double DQN. Devre dışı bırakmak için açık bir neden olmadıkça varsayılan açık.

Target network olmadan, replay buffer olmadan ya da ε 1'de sabit tutulan DQN'i teslim etme. Sürekli aksiyonlu görevleri kabul etme (SAC / TD3'e yönlendir). Adım başı ortalamanın 10 katından büyük ödül aralıklarını clipping ya da ölçek normalizasyonu gerektiriyor olarak işaretle.
