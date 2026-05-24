---
name: dp-solver
description: Küçük bir tabular MDP'yi policy iteration ya da value iteration ile tam olarak çöz. Yakınsama davranışını raporla.
version: 1.0.0
phase: 9
lesson: 2
tags: [rl, dynamic-programming, bellman]
---

Modeli bilinen bir MDP verildiğinde şu çıktıyı üret:

1. Seçim. Policy iteration vs value iteration. |S|, |A|, γ'ya bağlanan gerekçe.
2. Başlatma. V_0, başlangıç policy'si. Yakınsama hassasiyeti.
3. Durdurma. Sup-norm toleransı ε. Beklenen sweep sayısı.
4. Doğrulama. V*(s_0) tam olarak hesaplanmış. Greedy policy çıkarılmış.
5. Kullanım. Bu baseline'ın örnekleme tabanlı yöntemleri hata ayıklamak/değerlendirmek için nasıl kullanılacağı.

10⁷'den büyük state uzaylarında DP çalıştırma. Sup-norm kontrolü yapılmadan yakınsama iddiasında bulunma. Sonsuz horizon görevinde `γ ≥ 1` varsa garanti ihlali olarak işaretle.
