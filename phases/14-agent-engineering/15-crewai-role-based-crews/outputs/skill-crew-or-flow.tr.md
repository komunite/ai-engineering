---
name: crew-or-flow
description: Verilen bir görev için CrewAI Crew veya Flow seç ve minimal implementasyonu iskelele.
version: 1.0.0
phase: 14
lesson: 15
tags: [crewai, crews, flows, multi-agent, role-based]
---

Bir görev tanımı verildiğinde, Crew (otonom) veya Flow (deterministik) seç, sonra iskelele.

Karar:

1. Görevin SLA, compliance veya deterministik replay gereksinimleri var mı? -> Flow.
2. Görev keşif amaçlı mı (araştırma, ilk taslak, beyin fırtınası)? -> Crew.
3. Görevin LLM-seçimli sıralama ile 4+ uzmanı var mı? -> Hierarchical Crew.
4. Görevin sabit bir sırada <=3 uzmanı mı var? -> Sequential Crew veya Flow — Flow'u tercih et.

Crew'lar için üret:

1. Agent tanımları: role, goal, backstory (sıkı, <=200 kelime), tools.
2. Task tanımları: description, expected_output, agent.
3. Doğru Process (Sequential | Hierarchical) ile Crew.
4. Crew'u örnek input'larla çalıştıran ve expected_output'ların üretildiğini kontrol eden bir test koşumu.

Flow'lar için üret:

1. `@start` giriş fonksiyonu.
2. Bir DAG oluşturan `@listen(topic)` adımları.
3. Açık event topic'leri; sihirli broadcast yok.
4. Bir replay koşumu: bir kickoff payload verildiğinde, deterministik olarak yeniden çalıştır.

Sert ret durumları:

- Backstory olmadan Crew'lar. Backstory'ler load-bearing'dir.
- Açık topic isimleri olmadan Flow'lar. "Implicit chaining" denetim amacını boşa çıkarır.
- 2 uzmanlı Hierarchical Crew'lar. Manager overhead'i maliyetini kazanmıyor.

Reddetme kuralları:

- Kullanıcı prod-only compliance görevinde Crew isterse, reddet ve Flow'a taşı.
- Kullanıcı açık uçlu araştırma görevinde Flow isterse, reddet ve Crew'a taşı.
- Backstory 200 kelimeyi aşıyorsa, reddet ve kısaltma talep et. Context bütçesi sınırlı.

Çıktı: `agents.py`, `tasks.py`, `crew.py` veya `flow.py`, artı karar gerekçesi içeren `README.md`. "Bundan sonra ne okumalı" notu ile bitir: observability için Lesson 24 (Langfuse/AgentOps) veya Flow durable resume semantikleri gerektiriyorsa Lesson 13.
