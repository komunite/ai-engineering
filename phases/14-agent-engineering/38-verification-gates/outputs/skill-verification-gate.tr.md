---
name: verification-gate
description: Görev başına scope, kural ve feedback artifact'larını tek bir verification_report.json'da birleştiren deterministik bir verification gate üret, artı yeşil verdict olmadan merge etmeyi reddeden CI bağlantısı.
version: 1.0.0
phase: 14
lesson: 38
tags: [verification, gate, deterministic, ci, override-log]
---

Bir projenin kabul kriterleri ve mevcut workbench artifact'ları verildiğinde, verification gate'ini ve override audit log'unu üret.

Üret:

1. `verify(task_id, artifacts) -> VerdictReport` sunan `tools/verify_agent.py`. Pure fonksiyon, deterministik, LLM çağrısı yok.
2. Tek source of truth verdict olarak `outputs/verification/<task_id>.json`.
3. `outputs/verification/overrides.jsonl`'a imzalı override girdileri ekleyen `tools/override.py` (reason, user id, timestamp, finding code içermeli).
4. `passed: false`'ta başarısız olan ve raporu inline yüzdüren CI workflow'u.
5. Her check'i, şiddetini, kaynak artifact'ını ve override politikasını listeleyen `docs/verification.md`.

Sert ret durumları:

- LLM çağıran bir check. Gate deterministik tesisattır; LLM yargısı reviewer'a aittir.
- Agent'in imzalı girdi olmadan alabileceği bir override yolu. Override'lar yalnızca insan.
- Tükettiği artifact yollarını atlayan verification raporu. Raporlar denetlenebilir olmalı.
- Workflow'un sessizce düşürebileceği blok-şiddetinde bulgular. Şiddet write time'da sabittir, read time'da değil.

Reddetme kuralları:

- Projenin kabul komutu yoksa, biri var olana kadar gate'i göndermeyi reddet. Hiçbir şey kanıtlamayan bir gate tiyatrodur.
- Kural raporu mevcut değilse, kural check'ini atlamayı reddet; fail closed.
- Feedback log mevcut değilse, kabul check'ini atlamayı reddet; eksik log'lar kendileri bir blok.
- Override girdileri version-controlled değilse, override yolunu bağlamayı reddet; kayıt-dışı override'lar gate'i yener.

Çıktı yapısı:

```
<repo>/
├── tools/
│   ├── verify_agent.py
│   └── override.py
├── outputs/verification/
│   ├── overrides.jsonl
│   └── <task_id>.json
├── docs/verification.md
└── .github/workflows/verify.yml
```

"Bundan sonra ne okumalı" notu ile bitir:

- Yeşil verdict'ten sonra devralan reviewer agent için Lesson 39.
- Verdict'i pakete dahil eden handoff generator için Lesson 40.
- Gate'i real-style sample app'a karşı çalıştırmak için Lesson 41.
