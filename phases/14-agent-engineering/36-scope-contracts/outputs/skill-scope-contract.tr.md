---
name: scope-contract
description: Allowed/forbidden glob'lar, kabul kriterleri ve rollback planı ile görev başına scope kontratları üret, artı her agent diff'inde çalışan CI-ready glob-aware checker.
version: 1.0.0
phase: 14
lesson: 36
tags: [scope, contract, globs, diff-check, ci]
---

Bir görev tanımı ve bir repo düzeni verildiğinde, bir scope kontratı ve diff-aware checker üret.

Üret:

1. Görev için şu alanlarla `scope_contract.json`: `task_id`, `goal`, `allowed_files` (glob'lar), `forbidden_files` (glob'lar), `acceptance_criteria`, `rollback_plan`, `approvals_required`.
2. Bir kontrat yolu ve dokunulan dosyalar listesi alan, `ScopeReport` artı herhangi bir ihlalde sıfır olmayan exit döndüren `tools/scope_check.py`.
3. Checker'ı merge diff'e karşı çalıştıran CI adımı (`.github/workflows/scope-check.yml` veya eşdeğeri).
4. Kontratların değişiklik geçmişiyle birlikte gönderilmesi için `outputs/scope/closed/<task_id>.json` arşivleme konvansiyonu.

Sert ret durumları:

- `forbidden_files`'sız bir kontrat. Negatif alan kontratın parçasıdır.
- Code dizinleri için glob yerine ham yollar listeleyen bir kontrat. Refactor'lar ham yolları bir gecede geçersizleştirir.
- Boş veya "see runbook" olan bir `rollback_plan` alanı. Açıkça yaz.
- "Case by case" olarak listelenen onaylar. Onay sınırları sıralanabilir olmalı.

Reddetme kuralları:

- Görev tanımı repo'nun bir bölgesini kısıtlamıyorsa, yalnızca tanımdan `allowed_files`'i yazmayı reddet. Görevin yaşadığı dizini iste.
- Repo'nun test komutu yoksa, biri sağlanana veya stub'lanana kadar `acceptance_criteria` eklemeyi reddet. Doğrulanamayan kontrat bir dilektir.
- Agent runtime onay sınırlarını yerine getiremiyorsa (human-in-the-loop yok), göndermeden önce boşluğu yüzdür; onay-gerekli eylemlere scope creep baskın başarısızlık olacaktır.

Çıktı yapısı:

```
<repo>/
├── scope_contract.json
├── outputs/scope/closed/
│   └── T-XXX.json
├── tools/
│   └── scope_check.py
└── .github/
    └── workflows/
        └── scope-check.yml
```

"Bundan sonra ne okumalı" notu ile bitir:

- Çalıştırılan komutları kontrata bağlayan runtime feedback için Lesson 37.
- Scope raporunu tüketen verification gate için Lesson 38.
- Kapalı kontrat arşivini denetleyen reviewer agent için Lesson 39.
