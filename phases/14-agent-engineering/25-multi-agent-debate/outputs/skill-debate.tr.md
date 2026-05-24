---
name: debate
description: N tartışmacı, R round, yapılandırılabilir topoloji (full mesh, star, ring) ve bir convergence kuralı ile multi-agent debate iskelele.
version: 1.0.0
phase: 14
lesson: 25
tags: [debate, multi-agent, society-of-minds, sparse-topology]
---

Bir soru sınıfı ve doğruluk hedefi verildiğinde, bir debate protokolünü iskelele.

Üret:

1. Homojenleşmeyi önlemek için farklı prompt'lar (ve ideal olarak farklı modeller) içeren `Debater`.
2. Round runner: full mesh, star veya ring topolojisi.
3. Convergence kuralı: majority-vote, güvene göre ağırlıklı veya fallback'li supermajority.
4. Round 1 zorunlu anlaşmazlık: her tartışmacı mümkünse farklı bir öneri döndürür.
5. Maliyet muhasebesi: toplam critique operasyonu + soru başına token maliyeti.

Sert ret durumları:

- Tüm tartışmacıların aynı prompt VE aynı modelle olması. Garanti groupthink.
- Maliyet kontrolü olmadan N >= 6 ile full mesh. Debate ops O(N*R) ölçeklenir.
- Convergence kuralı yok. Tartışmacı 0'ın round-R cevabını döndürmek convergence değildir.

Reddetme kuralları:

- Ürün latency-hassas ise (<1s bütçesi), debate'i reddet. Yerine Self-Refine (Lesson 05) veya parallel voting (Lesson 12) kullan.
- Soru sınıfı basit factual lookup ise (başkent, tarih, tanım), debate'i reddet. Lookup + CRITIC (Lesson 05) daha ucuz.
- Tartışmacılar eval setindeki herhangi bir soruda round 1'den sonra anlaşmazlığa düşmüyorsa, protokolü reddet. Model/prompt çeşitliliğine ihtiyacın var.

Çıktı: `debater.py`, `topology.py`, `convergence.py`, `runner.py`, N/R seçimini, topoloji gerekçesini ve eval setinde maliyet-vs-doğruluk ölçümlerini açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: görev daha basitse Lesson 12 (workflow pattern'leri) veya debate'i daha büyük bir sisteme gömmek için Lesson 28 (orchestration pattern'leri).
