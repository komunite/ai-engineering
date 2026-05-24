---
name: td-agent
description: Tabular ya da küçük feature'lı bir RL görevi için Q-learning, SARSA, Expected SARSA arasından seçim yap.
version: 1.0.0
phase: 9
lesson: 4
tags: [rl, td-learning, q-learning, sarsa]
---

Tabular ya da küçük feature'lı bir environment verildiğinde şu çıktıyı üret:

1. Algoritma. Q-learning / SARSA / Expected SARSA / n-step varyantı. On-policy vs off-policy ve varyansa bağlanan tek cümlelik gerekçe.
2. Hyperparametreler. α, γ, ε, decay zamanlaması.
3. Başlatma. Q_0 değeri (iyimser vs sıfır) ve gerekçe.
4. Yakınsama teşhisi. Hedef öğrenme eğrisi, DP mümkünse `|Q - Q*|` kontrolü.
5. Deployment uyarısı. Inference'ta exploration nasıl davranacak? SARSA'nın muhafazakarlığı gerekli mi?

10⁶'dan büyük state uzaylarında tabular TD uygulama. Max-bias uyarısı olmadan Q-learning agent'ı teslim etme. ε'nin baştan sona 1.0'da tutulduğu (exploitation aşaması olmayan) hiçbir agent'ı işaretle.
