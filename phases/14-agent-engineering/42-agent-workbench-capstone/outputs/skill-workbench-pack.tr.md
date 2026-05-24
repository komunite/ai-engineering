---
name: workbench-pack
description: Projeye-ayarlanmış drop-in agent workbench pack üret — takımın geçmişine göre keskinleştirilmiş kurallar, repo'ya eşleşen scope glob'ları, alana özgü bir girdiyle genişletilmiş rubric boyutları.
version: 1.0.0
phase: 14
lesson: 42
tags: [capstone, workbench-pack, installer, schemas, drop-in]
---

Bir repo, takımın incident geçmişi ve içinde çalışan agent ürünü verildiğinde, ayarlanmış bir agent-workbench-pack ve bir installer yay.

Üret:

1. Kanonik düzene uyan `agent-workbench-pack/` dizini: AGENTS.md, docs/, schemas/, scripts/, bin/, README.md, VERSION.
2. `--force` olmadan mevcut bir pack'i ezmeyi reddeden ve hedef repo'ya `.workbench-version` yazan bir `bin/install.sh`.
3. `agent-rules.md` (takımın son altı incident'ından türetilen kategori başına en az bir kural ile), `reviewer-rubric.md` (altıncı bir alan boyutu ile) ve `scope_contract.schema.json` (projeye özgü glob'larla) projeye-ayarlanmış versiyonları.
4. Script'ler ve şemalar arasında veya VERSION ile şemaların `schema_version`'ı arasında drift'te başarısız olan bir `lint_pack.py` script'i.
5. Pack'i demo branch'lere talep üzerine kuran ve verification gate'i known-good bir göreve karşı çalıştıran opsiyonel CI entegrasyonu.

Sert ret durumları:

- Projeye özgü görevler içeren bir pack. Görevler hedef repo'nun board'unda yaşar.
- Tek bir vendor SDK'sine bağlı bir pack. Yalnızca framework-agnostic; SDK bağlantısı hedef repo'nun işidir.
- State dosyalarını mutate eden bir installer. Installer idempotent yüzey-yalnızdır; state agent'a ve insanlara aittir.
- Karşılık gelen bir check fonksiyonu olmayan kurallar. Aspirasyonel kurallar onboarding'e aittir, pack'e değil.

Reddetme kuralları:

- Incident geçmişi boşsa, ayarlanmış `agent-rules.md` göndermeyi reddet. Kanonik varsayılanı kullan ve boşluğu yüzdür.
- Hedef repo'nun CI'sı install ile uyumsuz ise (`.github/workflows/` yok, eşdeğeri yok), opsiyonel CI adımını reddet ve manuel yolu belgele.
- Takım pack'in özel bir fork'unu kullanıyorsa, public installer yazmayı reddet. Özel installer'lar özel invariantlar taşır.

Çıktı yapısı:

```
agent-workbench-pack/
├── AGENTS.md
├── docs/
├── schemas/
├── scripts/
├── bin/install.sh
├── lint_pack.py
├── VERSION
└── README.md
```

"Bundan sonra ne okumalı" notu ile bitir:

- Bu pack'in geliştirdiği before/after benchmark için Lesson 41.
- Pack'in verdict'lerini tüketen eval döngüsü için Lesson 30 (Eval-Driven Agent Development).
- Pack'i 32 AI agent arasında dağıtmak için [SkillKit](https://github.com/rohitg00/skillkit).
