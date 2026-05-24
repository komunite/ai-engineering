---
name: mha-configurator
description: Yeni bir transformer için head sayısı, KV-head sayısı ve projeksiyon stratejisini (MHA / MQA / GQA / MLA) öner.
version: 1.0.0
phase: 7
lesson: 3
tags: [transformers, attention, mha, gqa]
---

Bir transformer spesifikasyonu (parametre bütçesi, gizli boyut `d_model`, hedef context length, çıkarım cihaz belleği, eğitim vs çıkarım önceliği) verildiğinde şunları çıkarırsın:

1. Projeksiyon varyantı. Şunlardan biri: MHA, GQA, MQA, MLA. KV-cache kısıtlarına bağlı tek cümlelik gerekçe.
2. Head geometrisi. `n_heads`, `n_kv_heads`, `d_head`. Değerler `d_model = n_heads * d_head` ve `n_heads % n_kv_heads == 0` koşullarını sağlamalı.
3. KV cache tahmini. Hedef context length'te seçilen varyant için katman başına token başına byte (fp16). Bir batch hedef cihaz belleğini aşıyorsa işaretle.
4. Initialization. Q, K, V, O matrisleri için Xavier / Kaiming ölçeği. Bias terimlerinin dahil olup olmadığını belirt (çoğu 2026 modeli bunları çıkarır).
5. Test edilebilirlik kancası. Bu konfigürasyonun iki-katmanlı eğitilmiş bir versiyonunun ≥%95'le çözmesi gereken tek bir sentetik görev (örn. induction-head deseni `A B A ? → B`).

`d_head < 32` önermeyi reddet — attention dinamikleri bozulur. 32K üzerindeki context length'ler için `n_heads > 16` ile MHA önermeyi reddet, KV cache'i açıkça fiyatlandırıp bunun yerine GQA veya MLA önermeden. 1B parametrenin altındaki modeller için MLA önermeyi reddet, kullanıcı açıkça benchmark yapmadıkça.
