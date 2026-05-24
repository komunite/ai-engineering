---
name: topology-picker
description: Belirli bir görev için çoklu-agent debate topolojisi (star / chain / tree / graph), agent N'i, heterojenlik profili ve round üst sınırı seç.
version: 1.0.0
phase: 16
lesson: 15
tags: [multi-agent, debate, topology, voting, self-consistency]
---

Bir görev tanımı verildiğinde, çoklu-agent topolojisi ve boyutlandırma öner.

Üret:

1. **Görev parmak izi.** Araştırma (uzun-ufuk, açık-uçlu), hızlı-olgu (kapalı-form yanıt), aşamalı-iyileştirme (sahnelendirilmiş pipeline) ya da görüş (ground truth yok). Birini seç; ikisi arasında geziyorsa, baskın şekli seç.
2. **Topoloji.** Star, chain, tree ya da graph. Parmak izinden gerekçelendir:
   - araştırma → graph (any-to-any eleştiri)
   - hızlı-olgu → star (hub aggregator)
   - aşamalı-iyileştirme → chain (ya da divide-and-conquer ise tree)
   - görüş → yukarıdakilerin hiçbiri; tek agent + insan kararı öner
3. **Agent N'i.** 3 en ucuz işe yarar ensemble'dır; 5 ortak sweet spot'tur; 7+ özel uzmanlıktır. Graph topolojide 5'in üzerinde, koordinasyon vergisi uyar.
4. **Heterojenlik profili.** Monoculture önemliyse (araştırma, reasoning) en az bir agent farklı bir base model ailesinden gelmelidir. N=5'te 3 farklı base model tercih et.
5. **Round üst sınırı.** 1 round = oy. 2 round = bir iyileştirme. 3 round = uyumun baskın olmasından önceki maksimum. Asla sınırsız değil.
6. **Aggregation.** Plurality (ucuz), confidence-ağırlıklı (Ders 14'ten CP-WBFT), geometric median (DecentLLMs) ya da judge-puanlı. Maliyet kısıtları plurality'yi dayatmadıkça varsayılan olarak confidence-ağırlıklı.
7. **Eskalasyon.** Eşik-altı konsensüs → nereye eskalasyon? İnsan, farklı base modellerle başka bir ensemble ya da abstention?

Sert ret durumları:

- Graph topolojide 10+ agent önerisi. Koordinasyon vergisi baskın olur; önce ölç.
- Açık araştırma soruları için star topoloji. Star, any-to-any eleştirinin yararını kaybeder.
- Aynı base modeli N kez çalıştırıp buna çoklu-agent diyen öneriler. Bu kılık değiştirmiş self-consistency'dir; doğru etiketle.
- Sınırsız round'lar. Uyumu ödüllendirir; debate ne kadar uzun çalışırsa, agent'lar mantıktan çok baskıdan dolayı o kadar anlaşır.

Reddetme kuralları:

- Görevin ground truth'u yoksa (görüş, sentez, yaratıcı), oylamanın tavsiye niteliğinde olduğunu belirt. Tek agent + insan kararı öner.
- Kullanıcının birden fazla base modele erişimi yoksa, monoculture tavanını işaretle ve fallback olarak sıcaklık varyasyonlu self-consistency öner.
- Görev basitse (tek olgu araması, < 100 token reasoning), N=5 self-consistency'li tek agent öner.

Çıktı: bir sayfalık brief. Tek cümlelik öneriyle başla ("Graph topoloji, 3 farklı base modelden N=5 agent, 2 round, confidence-ağırlıklı aggregation, eşik-altında insana eskalasyon."), ardından yukarıdaki yedi bölüm. Bütçe tahminiyle bitir: sorgu başına beklenen token ve saniye cinsinden beklenen latency.
