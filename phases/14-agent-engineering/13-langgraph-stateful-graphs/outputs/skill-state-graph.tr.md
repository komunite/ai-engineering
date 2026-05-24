---
name: state-graph
description: Tipli state, koşullu edge'ler, node başına checkpointing ve durable resume ile LangGraph-şekilli state machine kur.
version: 1.0.0
phase: 14
lesson: 13
tags: [langgraph, state-machine, durable, checkpointing, human-in-the-loop]
---

Bir hedef runtime, bir state şekli, node fonksiyonları kümesi ve bir checkpointer backend'i verildiğinde, stateful bir agent grafiği üret.

Üret:

1. Tipli bir `State` (dict veya Pydantic). Her alanı belgele. Node'lar state okur; güncellemeleri döndürürler.
2. `add_node`, `add_edge`, `add_conditional_edges`, `set_entry` artı `START`/`END` sentinel'leri içeren bir `StateGraph`.
3. `save(session_id, node, state)` ve `load_latest(session_id)` içeren bir `Checkpointer` arayüzü. Varsayılan olarak SQLite; Postgres/Redis/custom'a izin ver.
4. Grafikte adım adım ilerleyen, her node'dan sonra state'i serialize eden, human-in-the-loop için `PausedAtNode` yakalayan ve opsiyonel `state_override` ile `resume_from` destekleyen bir `Runner`.
5. Üç topoloji helper'ı: supervisor (merkezi router), swarm (paylaşımlı-tool handoff'ları), hierarchical (subgraph'lar).

Sert ret durumları:

- Açık random-seed veya duvar saati yakalaması olmadan non-deterministik node'lar. Resume, node çıktısının verilen input state'te yeniden üretilebilir olduğunu varsayar.
- Yalnızca "summary" state'i kaydeden bir checkpointer. Tam state'i serialize et yoksa resume bozulur.
- Her edge'in koşullu olduğu grafikler. Ara sıra dallanan lineer zincirleri tercih et.

Reddetme kuralları:

- Kullanıcı persistence olmadan bir state graph isterse, reddet. Tüm amaç durable resume'dur; resume gerekmiyorsa, Lesson 12'deki workflow pattern'leri kullan.
- Kullanıcı "yalnızca başarıda checkpoint" isterse, reddet. Başarısızlıkların da state'e ihtiyacı var — hata ayıklama oradan başlar.
- Grafik ~30 node'dan fazlaysa, flat layout'u reddet ve iç içe subgraph'lar talep et. Flat 30-node grafikler gözden geçirilemez.

Çıktı: `state.py`, `graph.py`, `checkpointer.py`, `runner.py`, state şemasını, checkpointer seçimini ve resume semantiklerini açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: actor-model alternatifi için Lesson 14, handoff/guardrails katmanı için Lesson 16 veya grafik adımlarında OTel span'leri için Lesson 23.
