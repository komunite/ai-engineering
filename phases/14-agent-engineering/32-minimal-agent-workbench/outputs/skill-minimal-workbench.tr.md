---
name: minimal-workbench
description: Herhangi bir repo için üç dosyalık minimum viable agent workbench'i kur — kısa AGENTS.md router, durable agent_state.json ve projenin mevcut backlog'una bağlı bir JSON task_board.json.
version: 1.0.0
phase: 14
lesson: 32
tags: [workbench, agents-md, state, task-board, scaffold]
---

Bir repo yolu ve kısa bir backlog verildiğinde, minimum viable agent workbench'i iskelele.

Üret:

1. 80 satırdan uzun olmayan `AGENTS.md`. Şunlara yönlendirmeli: state dosyası, task board, derin kurallar belgesi (boş olsa bile) ve verification komutu. Bu dosyada düzyazı tutorial yok.
2. Şu anahtarlarla `agent_state.json`: `active_task_id`, `touched_files`, `assumptions`, `blockers`, `next_action`. Tüm opsiyonel alanlar varsayılan olarak boş array veya boş string, asla array'ler için `null` değil.
3. Görev JSON array'i olarak `task_board.json`. Her görev `id`, `goal`, `owner` (`builder` | `reviewer` | `human`), `acceptance` (string listesi) ve `status` (`todo` | `in_progress` | `done` | `blocked`) içerir.
4. Yüzey başına tek bir H2 ile `docs/agent-rules.md` placeholder, böylece sonraki dersler doldurabilir.

Sert ret durumları:

- 80 satır üzerinde veya 10 satır altında `AGENTS.md`. Çok uzun ve agent atlar; çok kısa ve hiç routing taşımaz.
- Repo yerine sohbet geçmişine atıfta bulunan bir state dosyası. Repo, system of record'dur.
- `acceptance`'sız bir task board. Kabul kriteri olmayan görevler "iyi görünüyor" rubber stamp'lere dönüşür.
- `owner`'ı `agent` veya `model` olan görevler. Owner'lar rollerdir, varlıklar değil.

Reddetme kuralları:

- Repo'nun verification komutu yoksa, biri sağlanana veya stub'lanana kadar `AGENTS.md` yazmayı reddet. Eksik bir gate'i işaret eden router, hiç router'dan daha kötüdür.
- Backlog 12'den fazla açık göreve sahipse, reddet ve kullanıcıdan bölmesini iste. Ekran üzerindeki board'lar planlama tiyatrosuna kayar.
- Proje izlenen dosyalarda secret'larla geliyorsa, state dosyasını yazmayı reddet ve secret sızıntısını önce bir bloklayıcı bulgu olarak yüzdür.

Çıktı yapısı:

```
<repo>/
├── AGENTS.md
├── agent_state.json
├── task_board.json
└── docs/
    └── agent-rules.md
```

"Bundan sonra ne okumalı" notu ile bitir:

- Kuralların placeholder'ını executable kısıtlara çevirmek için Lesson 33.
- Durable state şeması için Lesson 34.
- Görev başına scope kontratı için Lesson 36.
