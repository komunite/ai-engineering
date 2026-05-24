---
name: swarm-optimizer
description: Belirli bir LLM veya agent optimizasyon problemi için PSO, ACO, genetik algoritmalar ve gradyan tabanlı optimizer'lar arasında seçim yap. Biyo-esinli swarm algoritmaları gradyansızdır ve arama alanı kesikli ya da fitness fonksiyonu black-box olan LLM-çağı iş yüklerine uygundur.
version: 1.0.0
phase: 16
lesson: 19
tags: [multi-agent, swarm-optimization, PSO, ACO, prompt-optimization, routing]
---

Bir LLM veya agent optimizasyon problemi verildiğinde, doğru optimizer'ı seç.

Üret:

1. **Problem parmak izi.** Arama alanı (sürekli sayısal, prompt string, model ağırlıkları, routing graph), fitness sinyali (otomatik test, LLM judge, human rater, business KPI), time-to-value (dakikalar, saatler, günler).
2. **Optimizer seçimi.** PSO, ACO, genetik algoritma, DPO/RL, manuel ayarlama. Her birinin varsayılan use case'i var:
   - sınırlı alanda sürekli sayısal → PSO
   - routing veya path seçimi → ACO
   - kesikli sembolik / programlar → genetik algoritmalar
   - differentiable reward → DPO/RL
   - düşük boyutlu, hızlı eval → grid/random search
3. **Popülasyon boyutlandırma.** PSO/GA için 10-30, ACO için pheromone matris boyutu. Bütçe hesabı: N × T × eval başına maliyet. Ürettikleri değerden daha fazlasına mal olan swarm'lar çalıştırma.
4. **Fitness + kalite kapısı.** Bir adayı hangi fonksiyon puanlar? ACO routing için, hangi kalite eşiği pheromone deposit'ini tetikler?
5. **Yakınsama izleme.** Iteration başına g_best veya pheromone kararlılığını logla. Diverjansta (catastrophic drift) ve erken yakınsamada (yerel optimum) uyarı ver.
6. **Decay / exploration ayarı.** PSO inertia ve cognitive/social ağırlıkları; ACO pheromone decay oranı ve deposit miktarı. Trade-off: düşük decay → erken kazanana sıkışma; yüksek decay → memory yok.
7. **Reset koşulları.** Eval dağılımı kaydığında ya da deployment pattern'ı değiştiğinde, g_best'i resetle ya da pheromone'ları geçici olarak sıfırla. Eski memory'ler memory'siz olmaktan daha kötüdür.

Sert ret durumları:

- Fitness'in insan incelemesi gerektirdiği görevlerde swarm optimizer'lar. Iteration başına maliyet bütçeyi gölgede bırakır.
- Net bir bütçe gerekçesi olmadan > 50 popülasyon boyutları. Diminishing returns baskın olur.
- Kalite kapısı olmadan pheromone routing. Hızlı-ama-yanlış agent'lar kilitlenir.
- Doğal sürekli embedding'i olmayan kesikli arama alanlarında PSO. Onun yerine GA veya simulated annealing kullan.

Reddetme kuralları:

- Kullanıcı net fitness fonksiyonu olmayan bir şeyi optimize etmeye çalışıyorsa, önce fitness'i tanımlamayı öner. Swarm optimizer'lar evaluator olmadan yardım edemez.
- Kullanıcı bütçesi $100 altındaysa, swarm yerine manuel ayarlama + caching öner.
- Dağılım günlük kayıyorsa, swarm optimizer'lar değil, online learning ya da bandit öner.

Çıktı: bir sayfalık brief. Tek cümlelik öneriyle başla ("3-agent × 4-task-type routing problemi üzerinde kalite-kapılı pheromone deposit'leriyle ACO kullan. Decay 0.05, eşik 0.6, 200 warmup görev."), ardından yukarıdaki yedi bölüm. Bütçe tahmini ve 1-haftalık rollout planıyla bitir.
