---
name: search-policy
description: Görev şekli, token bütçesi ve evaluator kalitesine göre bir arama stratejisi (ReAct, ToT, LATS, evolutionary) seç.
version: 1.0.0
phase: 14
lesson: 04
tags: [tree-of-thoughts, lats, mcts, search, value-function]
---

Bir görev şekli (tek-cevap / çok-cevap / açık-uçlu), bir token bütçesi ve mevcut bir evaluator (scalar test / heuristic / self-eval) verildiğinde, somut parametrelerle bir arama stratejisi önerisi üret.

Üret:

1. Karar. Şunlardan biri: linear ReAct, beam ToT (beam width k ile), BFS ToT (max derinlik ile), pruning ile DFS ToT, MCTS LATS (iterations ve UCT c ile), evolutionary search (yalnızca evaluator programatik ve kontrol edilebilirse).
2. Parametreler. Her strateji için somut sayısal varsayılanlar: beam width, derinlik sınırı, branching factor K, seviye başına rollout, UCT c (varsayılan 1.4), timeout.
3. Value function. Bir node'u tam olarak neyin skorlayacağını belirt. Seçenekler: unit-test geçme oranı, hedefe sayısal mesafe, format ile prompt verilmiş LLM skoru (sure/likely/impossible veya 1..10 veya vote) veya environment reward.
4. Token bütçesi tahmini. En kötü senaryo token = branching_factor ^ depth * avg_prompt_tokens. Sayıyı göster. Kullanıcının bütçesini aşıyorsa, daha ucuz bir strateji öner.
5. Failure mode'lar. Seçilen her strateji için, en üst iki failure mode'unu ve hafifletmelerini listele (örn. LATS + gürültülü evaluator -> CRITIC'e göre tool-grounded doğrulama ekle, Lesson 05).

Sert ret durumları:

- Evaluator güvenilmezken (yalnızca self-eval, ground truth yok) arama önermek. ReAct + CRITIC'e geri dön.
- Zorlayıcı bir sebep olmadan branching factor K'yi 5'in üzerine ayarlamak. K=3-5 paper varsayılanıdır; K=10 maliyeti patlatır.
- LATS'i chat tarzı görevlere uygulamak. Arama, programatik hedefi olmayan konuşma Q&A'ya yardım etmez.
- Makine-kontrol edilebilir fitness olmadan evolutionary search. AlphaEvolve yalnızca fitness programatik olduğunda ilginçtir (testleri çalıştır, hızı ölç, teoremi doğrula).

Reddetme kuralları:

- Token bütçesi tek-trajectory maliyetinin 5x'inden azsa, aramayı reddet ve ReAct + Reflexion (Lesson 03) öner.
- Duvar saati latency bütçesi 10 saniyeden azsa, LATS'i reddet ve ReAct öner.
- Görev saf bilgi geri alımı ise, aramayı reddet ve ReWOO (Lesson 02) öner.

Çıktı: bir öneri bloğu (seçilen strateji, parametreler, value function, bütçe tahmini) artı "bundan sonra ne okumalı" notu: evaluator güvenilirliği için Lesson 05 (CRITIC), evolutionary varyantlar için Lesson 11 (AlphaEvolve) veya benchmark düzeyinde doğrulama için Lesson 30 (eval-driven development).
