---
name: agents-sdk-scaffold
description: Bir triage agent, handoff'lar, input/output/tool guardrails, session store ve bir trace processor ile OpenAI Agents SDK uygulamasını iskelele.
version: 1.0.0
phase: 14
lesson: 16
tags: [openai, agents-sdk, handoffs, guardrails, tracing, session]
---

Bir ürün alanı ve uzman agent'ler listesi verildiğinde, bir OpenAI Agents SDK uygulamasını iskelele.

Üret:

1. Uzman başına `Agent` artı yalnızca handoff'ları olan (domain tool'ları yok) bir `triage` agent'i.
2. Tipli input schema, net açıklama (modele ne zaman kullanacağını söyler) ve execution sandbox ile domain tool başına `FunctionTool`.
3. Triage'dan her uzmana `Handoff`. Tool isimlerinin `transfer_to_<agent>` konvansiyonunu izlediğini doğrula.
4. PII, politika, scope için `InputGuardrail`. Guardrail LLM'i ana modele göre büyük olmadıkça varsayılan paralel mod — o zaman blocking kullan.
5. Uzunluk, PII, politika için `OutputGuardrail`. Güvenlik-kritik çıktılar için prod'ta her zaman blocking.
6. Network veya filesystem'a dokunan function tool'larda tool başına guardrail'ler.
7. `Session` store (SQLite varsayılan; prod için Redis).
8. OpenAI'nin trace UI'sının yanında span'leri backend'inize bağlayan `add_trace_processor`.

Sert ret durumları:

- Domain tool'ları olan triage agent'ler. Triage yalnızca handoff'lar; karıştırmak router'ın kararını sulandırır.
- Input/output'u değiştiren guardrail'ler. Guardrail'ler onaylar veya reddeder — yeniden yazmazlar.
- Sessiz handoff döngüleri. Bir hop sayacı talep et (varsayılan max 3).

Reddetme kuralları:

- Kullanıcı "guardrails yok, sadece hızlı git" isterse, ödeme yapan kullanıcılara veya PII'ye dokunan herhangi bir ürün için reddet.
- Ürünün yalnızca 2 uzmanı varsa, triage+handoff'lar yerine doğrudan classifier ile `Agents` üzerinden routing'i öner (Lesson 12) — daha az token maliyeti.
- Prod'ta tracing devre dışıysa, göndermeyi reddet. Multi-step başarısızlıklar trace olmadan hata ayıklanamaz.

Çıktı: `agents.py`, `tools.py`, `guardrails.py`, `app.py`, triage-agent gerekçesi, guardrail modları, trace processor ve session backend'i içeren `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 23 (OTel GenAI), Lesson 24 (observability backend'leri) veya Claude Agent SDK çevirisi için Lesson 17.
