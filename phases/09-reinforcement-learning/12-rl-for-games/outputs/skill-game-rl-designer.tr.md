---
name: game-rl-designer
description: Belirli bir alan için oyun-RL ya da akıl yürütme-RL eğitim pipeline'ı (AlphaZero / MuZero / GRPO) tasarla.
version: 1.0.0
phase: 9
lesson: 12
tags: [rl, alphazero, muzero, grpo, self-play]
---

Bir hedef (tam bilgili oyun / eksik bilgili / Atari / LLM akıl yürütme / kombinatoryel) verildiğinde şu çıktıyı üret:

1. Environment uyumu. Kurallar biliniyor mu? Markov mı? Stokastik mi? Multi-agent mı? AlphaZero vs MuZero vs GRPO seçimini bilgilendirir.
2. Arama stratejisi. MCTS (öğrenilmiş prior'lu PUCT), Gumbel-sampled, best-of-N ya da yok.
3. Self-play planı. Simetrik self-play / league / offline veri / verifier üretimi.
4. Hedef sinyal. Oyun sonucu / verifier ödülü / preference / öğrenilmiş model. Sağlamlık planı dahil.
5. Teşhisler. Baseline'a karşı kazanma oranı, ELO eğrisi, verifier pass oranı, referansa KL.

Eksik bilgili oyunlarda AlphaZero'yu kabul etme (CFR'a yönlendir). Güvenilir bir verifier olmadan GRPO'yu kabul etme. Sabit baseline rakip kümesi olmayan herhangi bir oyun-RL pipeline'ını kabul etme (self-play ELO aksi halde kalibre değildir).
