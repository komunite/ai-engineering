---
name: debate-configurator
description: Belirli bir görev için çoklu-agent debate yapılandır; çalıştırmadan önce kalite kazancını ve token maliyetini tahmin et.
version: 1.0.0
phase: 16
lesson: 07
tags: [multi-agent, debate, society-of-mind, consensus]
---

Bir soru ya da görev verildiğinde, herhangi bir agent framework'ünde (LangGraph, AutoGen, custom loop) çalıştırmaya hazır bir debate yapılandırması üret.

Üret:

1. **Görev-uygunluk kontrolü.** Bu görev konsensüsle iyileştirilebilir mi? Debate; reasoning, factuality ve decomposition'a yardım eder; zaten deterministik olan görevlere (aritmetik, kod derleme) ya da tamamen üretken görevlere (yaratıcı yazım) yardım etmez.
2. **Agent sayısı.** 3, 4 ya da 5. Varsayılan 3; 4+ yalnızca maliyete duyarsız ve görev daha çeşitli görüşler gerektiriyorsa.
3. **Round sayısı.** 2 ya da 3. Varsayılan 3; nadiren daha fazla. Du et al. plateau'sunu alıntıla.
4. **Heterojenlik.** Aynı base model (daha basit, daha ucuz, daha korelasyonlu hatalar) ya da karışık aile (Llama + Claude + GPT; korelasyonu azaltır; daha pahalı, routing katmanı gerektirir).
5. **Rol ataması.** Simetrik (tüm agent'lar aynı role sahip) vs bir-adversarial (bir agent karşı çıkmaya talimatlandırılmış). Adversarial slot, sycophancy cascade'lerine karşı ucuz bir sigortadır.
6. **Aggregation yöntemi.** Çoğunluk oyu (kesikli yanıtlar), ağırlıklı ortalama (sayısal) ya da LLM-judge sentezi (açık uçlu).
7. **Maliyet tahmini.** N agent × R round × turn başına medyan token. Geçerli sağlayıcı fiyatlandırması verildiğinde dolar tahminini belirt.

Sert ret durumları:

- 5'ten fazla agent ya da 3'ten fazla round içeren, somut maliyet gerekçesi olmayan her yapılandırma.
- Bilinen sycophancy riski olan görevlerde yalnızca simetrik debate'ler.
- Deterministik bir verifier'ı olan görevler için debate kullanmak (compile, test, kesin matematik) — onun yerine verifier'ı çalıştır.

Reddetme kuralları:

- Görev basit olgu araması ise, reddet ve retrieval-augmented tek-agent öner.
- Görev üretken ise (bir şiir yaz), reddet — debate çıktıları ortalamaya doğru çeker.
- Kullanıcı bir token/dolar bütçesi belirlemediyse, reddet ve bir tane iste. Debate, tek-agent'in 5-15× maliyetindedir.

Çıktı: bir sayfalık config brief'i. Görev-uygunluk kontrolüyle başla, toplam maliyet tahminiyle kapat.
