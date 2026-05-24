---
name: state-schema
description: Agent state ve task board için projeye özgü JSON Schema'lar, atomik write'larla bir Python StateManager ve şema bump'larının workbench'i bozamayacağı bir migration iskelesi üret.
version: 1.0.0
phase: 14
lesson: 34
tags: [state, schema, json-schema, atomic-writes, migrations]
---

Bir repo ve içinde çalışan agent ürünü verildiğinde, workbench için schema-first state dosyaları üret.

Üret:

1. Gerekli anahtarları, izin verilen status değerlerini, array-vs-null disiplinini ve bir `schema_version` integer'ını kapsayan `schemas/agent_state.schema.json`.
2. Görev id pattern'ini, izin verilen owner'ları, izin verilen status'leri ve acceptance array'lerini kapsayan `schemas/task_board.schema.json`.
3. `load`, `commit` ve `update`'i temp-and-rename atomik write'larla sunan `tools/state_manager.py`.
4. Sonraki şema bump'ı için `tools/migrate_state.py` iskelesi, dosya bilinmeyen bir versiyondan ise fail-loud yap.
5. `schema_version: 1` ile seed'lenmiş `agent_state.json` ve `task_board.json` ve taze bir backlog.

Sert ret durumları:

- `schema_version` alanı olmayan bir şema. Migration opsiyonel değildir.
- Bir array beklendiği yerde `null`'a izin vermek. `null`, data gibi maskelenen bir write-time bug'dır.
- Düz `open(path, "w")` kullanan bir writer. Yalnızca atomik write'lar; kısmi dosyalar source of truth'u bozar.
- State içinde token, ham chat transkript veya PII saklamak. State, repo-ilgili olgular içindir.

Reddetme kuralları:

- Repo'nun version control'ü yoksa, state dosyalarını göndermeyi reddet. Atomik write artı git diff durability hikayesidir.
- Proje `done` geçişini doğrulayacak en az bir acceptance komutuna sahip değilse, `status: done` enum değerini reddet. Acceptance kontrolü olmadan `done` eklemek tiyatrodur.
- Proje state'i lock stratejisi olmadan süreçler arası paylaşmak istiyorsa, göndermeden önce bu bulguyu yüzdür; atomik rename gerekli ama yeterli değildir.

Çıktı yapısı:

```
<repo>/
├── agent_state.json
├── task_board.json
├── schemas/
│   ├── agent_state.schema.json
│   └── task_board.schema.json
└── tools/
    ├── state_manager.py
    └── migrate_state.py
```

"Bundan sonra ne okumalı" notu ile bitir:

- Başlangıçta manager'ı çağıran initialization script için Lesson 35.
- Tamamlanmayı skorlamak için state okuyan verification gate için Lesson 38.
- Aynı şemayı tüketen handoff generator için Lesson 40.
