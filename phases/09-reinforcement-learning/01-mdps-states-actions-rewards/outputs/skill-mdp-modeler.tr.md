---
name: mdp-modeler
description: Bir görev tanımı verildiğinde, bir Markov Decision Process spesifikasyonu üret ve eğitim öncesi formülasyon risklerini işaretle.
version: 1.0.0
phase: 9
lesson: 1
tags: [rl, mdp, modeling]
---

Bir görev verildiğinde (kontrol / oyun / öneri / LLM fine-tuning), şu çıktıyı üret:

1. State. Tam feature vektörü ya da tensor spesifikasyonu. Markov özelliğini gerekçelendir.
2. Aksiyon. Ayrık küme ya da sürekli aralık. Boyutluluk.
3. Geçiş. Deterministik, bilinen modelle stokastik ya da yalnızca örnekleme tabanlı.
4. Ödül. Fonksiyon ve kaynak. Sparse vs şekillendirilmiş (shaped). Terminal vs adım başı.
5. İndirim faktörü. Değer ve horizon gerekçesi.

State Markov değilse ve frame-stacking ya da recurrent state açıkça belirtilmemişse hiçbir MDP'yi teslim etme. Hedef sonuç cinsinden tanımlanmamış hiçbir ödülü kabul etme. Sonsuz horizon görevinde `γ ≥ 1.0` varsa işaretle. Tipik adım ödülünün 100 katından büyük herhangi bir ödül aralığını olası bir gradient patlaması kaynağı olarak işaretle.
