---
name: marl-picker
description: Belirli bir çoklu-agent görev için MARL algoritması (MADDPG, QMIX, MAPPO, IQL ya da uzantıları) seç. Cooperative vs competitive, action-space türü, heterojenlik, reward yapısı ve ölçeği dikkate al.
version: 1.0.0
phase: 16
lesson: 20
tags: [multi-agent, MARL, MADDPG, QMIX, MAPPO, CTDE]
---

Bir çoklu-agent görev tanımı verildiğinde, MARL algoritmasını seç.

Üret:

1. **Görev taksonomisi.** Tamamen kooperatif (paylaşılan reward), tamamen kompetitif (sıfır-toplamlı), karışık, general-sum. Agent sayısı. Homojen vs heterojen.
2. **Observability.** Tam (her agent global state'i görür), kısmi (her biri yalnızca kendi gözlemini görür) ya da communication-enabled.
3. **Action space.** Kesikli (Atari benzeri, SMAC) ya da sürekli (particle world, MuJoCo). Algoritma seçimini etkiler.
4. **Reward yapısı.** Yoğun (per-step shaped) vs sparse (yalnızca terminal). Yoğun MAPPO'yu pratik yapar; sparse credit assignment yardımına ihtiyaç duyar (QMIX'in value decomposition'ı).
5. **Algoritma önerisi.** Yu et al. 2022 başına MAPPO'yu baseline olarak başlat. Şuraya geç:
   - QMIX, kooperatif + homojen + güçlü sparse-reward credit assignment gerektiğinde
   - MADDPG, karışık (kooperatif + kompetitif) + sürekli action'lar olduğunda
   - Uzantılar (QTRAN, QPLEX, FACMAC), monotonluk kısıtı çok kısıtlayıcı olduğunda
6. **Eğitim altyapısı.** Şunlara sahip misin: yeterli etkileşim verisi, compute bütçesi, reward shaping uzmanlığı, kararlılık bütçesi (deney başına 5-10 seed)? Yoksa, LLM agent'lar için prompt-seviyesi politikalar öner.
7. **Deployment sözleşmesi.** CTDE: deploy zamanında her agent yalnızca yerel gözlem görür. Runtime kodunun buna uyması için sözleşmeyi açıkça yaz.

Sert ret durumları:

- İlk run için MAPPO-dışı baseline seçmek. MAPPO 2026 baseline'ıdır; oradan başla.
- Karışık kooperatif-kompetitif görevler için QMIX kullanmak. Value decomposition monoton aggregation varsayar.
- Etkileşim verisi veya reward sinyali olmayan LLM-agent sistemleri için MARL eğitimi önermek. Veri olana kadar prompt-seviyesi politikalar daha iyi performans gösterecek.
- Agent başına gözlemleri ve eylemleri loglamadan eğitim. Hata ayıklama imkansız.

Reddetme kuralları:

- Görevde ~1000'den az etkileşim verisi epizodu varsa, prompt-seviyesi politikalar veya supervised fine-tune öner.
- Görev non-Markovian ise (memory gerektirir) ama öneri recurrent critic'leri içermiyorsa, boşluğu işaretle.
- Görev general-sum kompetitif ise (birden fazla equilibrium), MARL tek başına seçmez; mekanizma tasarımı veya equilibrium seçimi öner.

Çıktı: bir sayfalık brief. Tek cümlelik öneriyle başla ("Merkezi value fonksiyonlu MAPPO baseline; agent başına kesikli actor; deploy'da CTDE; deney başına 5 seed."), ardından yukarıdaki yedi bölüm. Eğitim-deployment pipeline'ı ile bitir: veri toplama, eğitim, değerlendirme, rollout.
