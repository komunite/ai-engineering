---
name: handoff-generator
description: Workbench artifact'larından session sonu handoff paketleri üret; yedi kanonik alana bağlı hem insan-okunabilir Markdown hem de makine-okunabilir JSON üretir.
version: 1.0.0
phase: 14
lesson: 40
tags: [handoff, generator, session-end, packet, next-action]
---

Bir workbench (state, verdict, review, feedback log, diff) verildiğinde, agent runtime'a bağlı bir session-sonu handoff generator üret.

Üret:

1. `generate_handoff(snapshot) -> (markdown, payload)` sunan `tools/generate_handoff.py`.
2. `outputs/handoff/<session_id>/handoff.md` ve `handoff.json`.
3. Yedi gerekli alanı ve feedback tail formatını kapsayan `handoff.schema.json`.
4. Generator'ı çalıştıran ve herhangi bir alan eksikse session'ı kapatmayı reddeden session-sonu hook script'i.
5. Yedi alanı, kaynaklarını ve trimming politikasını listeleyen `docs/handoff.md`.

Sert ret durumları:

- `next_action`'sız bir handoff. Handoff gibi maskelenen status raporları sonraki session'ı zehirler.
- Özeti el yazısıyla yazan bir generator. Agent'in işi workbench'i üretilebilir bir state'te bırakmaktır.
- JSON'dan ayrılan bir markdown paketi. JSON kaynaktır; markdown JSON'un render'ıdır.
- 30 girdiden uzun bir feedback tail. Tam log version control'de; paket küçük kalmalı.

Reddetme kuralları:

- Verification raporu eksikse, paketi üretmeyi reddet. Verdict'siz handoff bir dilektir.
- Review raporu eksikse ve bir insan reviewer beklendiyse, reddet ve önce review pas'ını talep et.
- Diff özeti boş ama session 5 dakikadan uzun çalıştıysa, üretmeden önce anomaliyi yüzdür; gerçek no-op'tan ziyade takılmış bir session'dan şüphe duy.

Çıktı yapısı:

```
<repo>/
├── outputs/handoff/<session_id>/
│   ├── handoff.md
│   └── handoff.json
├── tools/generate_handoff.py
├── handoff.schema.json
└── docs/handoff.md
```

"Bundan sonra ne okumalı" notu ile bitir:

- Real-style sample app'ta uçtan uca egzersiz için Lesson 41.
- Generator'ı capstone workbench pack'ine paketlemek için Lesson 42.
- Session-end'i queue, event ve cron tetikleyicilerine bağlamak için Lesson 29 (Production Runtimes).
