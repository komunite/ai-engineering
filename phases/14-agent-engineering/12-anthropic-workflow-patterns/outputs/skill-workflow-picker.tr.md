---
name: workflow-picker
description: Verilen bir görev için doğru pattern'i (prompt chain, router, parallel, orchestrator-workers, evaluator-optimizer veya tam agent) seç ve minimal implementasyonu üret.
version: 1.0.0
phase: 14
lesson: 12
tags: [anthropic, workflows, agents, patterns, minimal]
---

Bir görev tanımı verildiğinde, uyan minimal pattern'i seç ve en küçük doğru implementasyonu üret.

Karar ağacı:

1. Adımları sayabiliyor musun? -> **prompt chain** veya **routing**.
2. Çıktının bağımsız çalıştırmalar arasında aggregation gerektiriyor mu? -> **parallelization** (sectioning veya voting).
3. Üyeliği göreve göre değişen bir uzman havuzuna ihtiyacın var mı? -> **orchestrator-workers**.
4. Bir judge geçene kadar iteratif iyileştirme mi gerekiyor? -> **evaluator-optimizer** (Self-Refine şekli).
5. Yukarıdakilerin hiçbiri değil ya da adım sayısı ara sonuçlara mı bağlı? -> **agent döngüsü** (Lesson 01).

Üret:

- Workflow'lar için: LLM + tool çağrılarını compose eden saf fonksiyonlar. Framework yok.
- Agent'ler için: Lesson 01'den ReAct döngüsü artı görevin gerektirdiği tool registry'si.
- Karar gerekçesi, adım sayısı, beklenen token maliyeti ve gözlemlenebilir başarı kriteri içeren `README.md`.

Sert ret durumları:

- Görev 3 adımlık bir prompt chain iken bir framework'e (LangGraph, AutoGen, CrewAI) uzanmak. Aşırı mühendislik asıl problemi gizler.
- 3-worker'lı bir orchestrator-worker'ı "çoklu-agent" olarak tanımlamak. Worker'lar agent değildir; LLM çağrılarıdır. Netlik için "orchestrator-workers" kullan.
- Durdurma koşulu olmayan evaluator-optimizer. `max_iter` ve bir "fail-pass-through" fallback'i olmadan, döngü süresiz dönebilir.

Reddetme kuralları:

- Görev aslında bir router iken kullanıcı "çoklu-agent" isterse, reddet ve yeniden adlandır. Çoklu-agent etiketi, routing'in ihtiyaç duymadığı operasyonel maliyet (koordinasyon, hata ayıklama, eval'ler) taşır.
- Kullanıcı açık uçlu bir araştırma görevi için workflow ister, reddet ve tur bütçeli bir agent öner. Workflow'lar öngörülebilir trajectory'ler içindir.
- Kullanıcı 2 adımlık bir görev için agent ister, reddet ve prompt chaining öner. Agent'ler latency ve failure mode'lar ekler; yalnızca ihtiyacın olduğunda kullan.

Çıktı: pattern seçimi + minimal kod + README. "Bundan sonra ne okumalı" notu ile bitir: kalıcı state önemliyse Lesson 13 (LangGraph), handoff'lar ve guardrails için Lesson 16 (OpenAI Agents SDK) veya nihayetinde bir agent seçtinse Lesson 01.
