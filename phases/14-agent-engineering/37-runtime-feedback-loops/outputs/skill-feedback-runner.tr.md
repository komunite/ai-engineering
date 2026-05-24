---
name: feedback-runner
description: Shell komutlarını deterministik stdout/stderr/exit/duration yakalama ile sar, komut başına JSONL kaydı kalıcı kıl ve feedback eksikse agent döngüsünün ilerlemesini reddet.
version: 1.0.0
phase: 14
lesson: 37
tags: [feedback, subprocess, runner, jsonl, loop-control]
---

Bir agent döngüsü içinde shell komutları çalıştıran bir proje verildiğinde, bir feedback runner ve yazdığı JSONL'ı üret.

Üret:

1. `run_with_feedback(command: list[str], agent_note: str, timeout_s: float) -> FeedbackRecord` sunan `tools/run_with_feedback.py`.
2. Workbench altında satır başına bir kayıt olan `feedback_record.jsonl` konumu.
3. Aktif görev için en son N kaydı döndüren `tools/feedback_loader.py`.
4. Agent döngüsünün başarı iddiasından önce çağırdığı bir `loop_can_advance(record) -> bool` helper'ı.
5. Şunları kapsayan testler: başarı yolu, sıfır olmayan exit, timeout, eksik binary, deterministik head/tail kısaltma.

Sert ret durumları:

- Runner'da herhangi bir yerde `shell=True`. Yalnızca argv.
- Duvar saatine veya rastgele örneklemeye bağlı kısaltma. Aynı input aynı kaydı üretmeli.
- `duration_ms`'siz kayıtlar. Yavaş probe'lar takılmış bir workbench'in ilk işaretidir.
- Sınırsız liste döndüren bir loader. Son N'de sınırla veya sayfala.

Reddetme kuralları:

- Proje stdout aracılığıyla secret aktarıyorsa, runner'ı redaksiyon adımı olmadan göndermeyi reddet. Yakalanacak satırları yüzdür.
- Projenin süresiz takılabilecek komutları varsa, varsayılan timeout ve açık bir override listesi olmadan göndermeyi reddet.
- Runner paylaşılan state'li bir worker içinde çalışıyorsa, JSONL append etrafında dosya kilidi atlamayı reddet. Çoklu yazıcılar dosyayı yırtar.

Çıktı yapısı:

```
<repo>/
├── feedback_record.jsonl
└── tools/
    ├── run_with_feedback.py
    ├── feedback_loader.py
    └── test_feedback_runner.py
```

"Bundan sonra ne okumalı" notu ile bitir:

- Kayıtları tüketen verification gate için Lesson 38.
- Bir çalıştırmayı skorlarken feedback okuyan reviewer agent için Lesson 39.
- Feedback sağlam olduktan sonra telemetry tarafına ekleme için OTel GenAI conventions için Lesson 23.
