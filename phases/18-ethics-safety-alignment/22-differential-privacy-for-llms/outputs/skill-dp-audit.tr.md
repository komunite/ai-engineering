---
name: dp-audit
description: Bir dil-modeli deployment'ı için bir differential-privacy iddiasını denetle.
version: 1.0.0
phase: 18
lesson: 22
tags: [differential-privacy, dp-sgd, lora, mia, pmixed]
---

Bir dil-modeli deployment'ı için bir gizlilik iddiası verildiğinde, iddiayı denetle.

Üret:

1. (ε, δ) değerleri. Hangi ε ve δ kullanıldı? Hangi accountant onları hesapladı (Moments Accountant, Rényi DP, GDP)? Accountant olmadan ε anlamsızdır.
2. DP hedefi. DP garantisi tam model üzerinde mi yoksa adapter'lar (LoRA) üzerinde mi? LoRA ise, base-model memorization'ı kapsanmaz.
3. MIA protokolü. Membership-inference canary'lerle mi (Duan 2024) yoksa extraction ile mi (Carlini 2021, Nasr 2025) test edildi? Kowalczyk et al. 2025'e göre, ikisi farklı şeyleri ölçer.
4. Confidence-exposure kontrolü. Deployment confidence skorlarını ifşa ediyor mu? Evet ise, LLM Feedback üzerinden DP Reversal saldırısı uygulanır; ek truncation/quantization gerekir.
5. Alternatif-mekanizma karşılaştırması. PMixED veya DP-synthetic-data düşünüldü mü? Bu alternatifler spesifik tehdit modellerinde daha iyi utility verebilir.

Sert reddetmeler:
- Bir ε, δ çifti ve accountant olmadan herhangi bir DP iddiası.
- Yalnızca canary MIA'ya dayalı herhangi bir DP iddiası.
- DP Reversal'ı adreslemeden confidence skorlarını ifşa eden herhangi bir deployment.

Reddetme kuralları:
- Kullanıcı "epsilon=8 yeterince güvenli mi" diye sorarsa, sayısal cevabı reddet; güvenlik tehdit modeline ve en-çıkarılabilir-veri dağılımına bağlıdır.
- Kullanıcı LLM deployment'ı için önerilen bir ε isterse, evrensel sayısal hedefi reddet; aday aralıkları tartışmadan önce bir tehdit modeli, veri hassasiyeti, utility kısıtları ve accountant ayrıntıları iste.

Çıktı: beş bölümü dolduran, eksik accountant veya MIA değerlendirmesini işaretleyen ve en yüksek değerli remediation'ı adlandıran tek sayfalık bir denetim. Abadi et al. 2016 (DP-SGD) ve Kowalczyk et al. 2025'i birer kez alıntıla.
