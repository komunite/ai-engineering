---
name: rule-set-builder
description: Bir proje sahibiyle görüş, mevcut düzyazı talimatlarını beş operasyonel kategoriye sınıflandır ve version'lı bir agent-rules.md artı bir Python checker stub'ı yay.
version: 1.0.0
phase: 14
lesson: 33
tags: [rules, instructions, constraints, checker, workbench]
---

Bir repo ve mevcut düzyazı talimatları (`AGENTS.md`, `CONTRIBUTING.md`, onboarding belgeleri) verildiğinde, workbench'in yürütebileceği beş kategorili bir kural seti üret.

Beş kategori:

1. `startup` — iş başlamadan önce neyin doğru olması gerektiği.
2. `forbidden` — asla olmaması gereken.
3. `definition_of_done` — görevin tamamlandığını neyin kanıtladığı.
4. `uncertainty` — agent emin olmadığında ne yaptığı.
5. `approval` — neyin insan onayı gerektirdiği.

Üret:

1. Kural başına bir `##` başlığı ile `docs/agent-rules.md`. Her kural `category`, `check` ve tek satırlık açıklama taşır.
2. `tools/rule_checker.py`, `check` başına bir method sunan `RuleChecker` sınıfı ile. Her method bir `TurnTrace` dataclass alır ve `bool` döndürür.
3. Kuralları yükleyen, checker'ı bir trace üzerinde çalıştıran, bir `rule_report.json` yayan `tools/rule_report.py` runner'ı.
4. Bir migration notes dosyası: hangi düzyazı satırları hangi kurala dönüştü, hangileri aspirasyonel diye düşürüldü, neden.

Sert ret durumları:

- `check` alanı olmayan kurallar. Aspirasyonel-yalnız kurallar onboarding belgelerine aittir, workbench kural setine değil.
- Tek bir "dikkatli ol" kuralı. Bir kategori ve check belirt veya kaldır.
- LLM çağrıları gerektiren check'ler. Kural check'leri her turda çalışabilsin diye deterministik ve ucuz olmalı.
- 200 satırı aşan kural dosyaları. `agent-rules.{startup,forbidden,done,uncertainty,approval}.md`'e kategoriye göre böl ve bir parent index'ten yönlendir.

Reddetme kuralları:

- Agent ürünü bir `TurnTrace` sağlayamıyorsa (enstrümantasyon yok), en azından `read_state_file`, `edited_files` ve `tests_exit_code` kaydedilene kadar checker'ı bağlamayı reddet.
- Mevcut talimatlar çoğunlukla aspirasyonel ise (>%50), kuralları yaymadan önce bu bulguyu yüzdür. Kural seti ince görünecek; bu doğru.
- Tek bir geçmiş incident nedeniyle bir kural eklendiyse, gelecekte review hala gerekli olup olmadığına karar verebilsin diye incident id'sini ekle.

Çıktı yapısı:

```
<repo>/
├── docs/
│   └── agent-rules.md
├── tools/
│   ├── rule_checker.py
│   └── rule_report.py
└── docs/migration-notes.md
```

"Bundan sonra ne okumalı" notu ile bitir:

- Forbidden kategorisini genişleten görev başına scope kontratları için Lesson 36.
- Rule report'u tüketen verification gate'leri için Lesson 38.
- Kural uyumunu skorlayan reviewer agent için Lesson 39.
