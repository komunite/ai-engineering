---
name: runtime-picker
description: Verilen bir stack, latency bütçesi ve operasyonel şekil için production agent runtime'ı (Agno, Mastra, LangGraph, provider SDK) seç.
version: 1.0.0
phase: 14
lesson: 18
tags: [agno, mastra, langgraph, runtime, selection]
---

Bir stack, latency bütçesi, gerekli primitiv'ler ve operasyonel şekil verildiğinde, bir runtime seç.

Karar:

1. Python + FastAPI + saniyede binlerce kısa ömürlü agent -> **Agno**.
2. TypeScript + Next.js/Vercel + birleşik çoklu-provider -> **Mastra**.
3. Durable state, açık grafik, başarısızlıkta-resume -> **LangGraph** (Lesson 13).
4. Claude-öncelikli ürün, Claude Code harness şeklini istiyor -> **Claude Agent SDK** (Lesson 17).
5. OpenAI-öncelikli ürün, handoff'lar + guardrails + tracing istiyor -> **OpenAI Agents SDK** (Lesson 16).
6. Multi-agent takım, actor-model eşzamanlılığı, fault isolation -> **AutoGen v0.4** / **Microsoft Agent Framework** (Lesson 14).
7. Rol-tabanlı işbirliği veya event-driven deterministik workflow'lar -> **CrewAI** Crew veya Flow (Lesson 15).
8. Yukarıdakilerin hiçbiri değil -> doğrudan API çağrıları + Lesson 01'den stdlib döngüsü.

Üret:

- Kısa bir karar belgesi: stack, latency hedefi, gerekli primitiv'ler, gözlenen trade-off'lar.
- Seçilen runtime'da minimal bir iskele.
- Bugün başka bir runtime kullanılıyorsa bir migration planı.

Sert ret durumları:

- İş yükü istek başına bir yavaş çağrı olduğunda yalnızca "performans" üzerinden Agno veya Mastra seçmek. Performans nadiren darboğazdır.
- Bir Python monorepo'sunda gerekçe olmadan TypeScript runtime seçmek. Karışık dilli agent kodu operasyonel bir vergidir.
- Stateless kısa görevler için LangGraph seçmek. Checkpointer, basit bir workflow'un (Lesson 12) kaçındığı bir overhead ekler.

Reddetme kuralları:

- Kullanıcı "karşılaştırmak için beş runtime hepsi" isterse, reddet. Kendi iş yükünüzde benchmark yapın; framework vendor benchmark'ları yön gösterir.
- Kullanıcı Mastra'nın `ee/` özelliklerini self-host etmek isterse, reddet ve lisans şartlarına yönlendir.
- Ürün uzun süreli async iş gerektiriyorsa (saatlerden günlere), self-hosted'ı reddet ve Claude Managed Agents'a veya queue-tabanlı bir mimariye yönlendir (Lesson 29).

Çıktı: karar belgesi + iskele + README. "Bundan sonra ne okumalı" notu ile bitir: framework'ün üzerindeki operasyonel katman için Lesson 24 (observability) ve Lesson 29 (production runtime'ları).
