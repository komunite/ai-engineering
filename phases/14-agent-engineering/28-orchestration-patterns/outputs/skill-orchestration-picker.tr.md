---
name: orchestration-picker
description: Verilen bir problem için bir orchestration topolojisi (supervisor, swarm, hierarchical, debate veya yok) seç ve minimal olarak implemente et.
version: 1.0.0
phase: 14
lesson: 28
tags: [orchestration, supervisor, swarm, hierarchical, debate]
---

Bir ürün alanı ve bir görev sınıfı verildiğinde, minimal topolojiyi seç.

Karar:

1. 1 agent + workflow pattern'leri (Lesson 12) yeterli mi? -> topolojiyi hiç kullanma.
2. Farklı sorumluluklarla 2-4 uzman mı? -> **supervisor-worker**.
3. Latency-kritik ve uzmanlar temiz şekilde devredebiliyor mu? -> **swarm**.
4. 10+ uzman, supervisor context bütçesi başarısız oluyor mu? -> **hierarchical**.
5. Doğruluk maliyetten daha önemli, çoklu-öneri + eleştiri yardımcı oluyor mu? -> **debate** (Lesson 25).

Üret:

1. Seçilen topoloji iskelesi.
2. Swarm'da hop counter; hierarchical'da nesting derinlik sınırı; debate'te round cap.
3. Handoff başına veya adım başına observability kancaları (OTel GenAI span'leri, Lesson 23).
4. "Neden bu, şu değil" README bölümü.

Sert ret durumları:

- Sırayla 3 LLM çağrısı yapmaya "çoklu-agent" demek. Bu bir prompt chain'dir.
- Hop counter olmadan swarm. Sekme kesindir.
- Branch başına 1 uzmana inen hierarchical. Düzleştir.

Reddetme kuralları:

- Kullanıcı tek bir ReAct döngüsünün halledebileceği bir görev için çoklu-agent isterse, reddet ve Lesson 01'i öner.
- Kullanıcı 2 adımlı görev için supervisor isterse, reddet ve prompt chaining (Lesson 12) öner.
- Alanın compliance / denetim gereksinimleri varsa, swarm'ı reddet ve supervisor veya hierarchical öner.

Çıktı: topoloji iskelesi + karar gerekçeli README. "Bundan sonra ne okumalı" notu ile bitir: supervisor implementasyonu için Lesson 13 (LangGraph), handoff-as-tools için Lesson 16 (OpenAI Agents SDK) veya debate ayrıntıları için Lesson 25.
