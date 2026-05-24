---
name: init-script
description: Bir proje ile görüş ve beş probe artı herhangi bir probe başarısız olursa agent'i başlatmayı reddeden bir CI workflow ile deterministik bir init_agent.py yay.
version: 1.0.0
phase: 14
lesson: 35
tags: [init, probes, ci, workbench, fail-loud]
---

Bir repo, agent ürünü ve onun bağımlılık yüzeyi verildiğinde, projeye özgü bir init script'i ve CI bağlantısı üret.

Üret:

1. Şu probe'larla `tools/init_agent.py`: runtime versiyonu, listelenen bağımlılıklar, test komutu resolvability'si, gerekli env var'lar, state dosyası tazeliği.
2. Script'in yanında belgelenen `init_report.json` şeması. Her probe `(name, status: pass|warn|fail, detail)` döndürür.
3. Script'i çalıştıran ve herhangi bir fail-şiddetinde probe'da agent işini bloklayan `.github/workflows/agent-init.yml` (veya eşdeğeri).
4. Agent runtime'ın her session başlamadan önce çağırabileceği bir `pre-task` hook script'i.
5. Her probe'u, şiddetini ve bir başarısızlığı nasıl düzelteceğini listeleyen `docs/init.md` dokümantasyonu.

Sert ret durumları:

- Timeout olmadan network'e çıkan probe'lar. Init hızlı ve offline-safe olmalı.
- LLM çağrıları gerektiren probe'lar. Init deterministik tesisattır.
- Wrapper'ın yuttuğu sıfır olmayan exit code. Fail loud tüm meseledir.
- Idempotency olmadan state'e dokunan probe'lar. Üst üste iki çalıştırma timestamp modulo aynı raporları üretmeli.

Reddetme kuralları:

- Proje test komutuna sahip değilse, script'i göndermeyi reddet. Boşluğu workbench denetimine ekle.
- Env var listesi script'in yazacağı secret'ları içeriyorsa, reddet ve redaksiyon zorla. Init raporları asla secret taşımamalı.
- Bir probe dry run'da üç saniyeden fazla sürüyorsa, göndermeden önce zamanlama bulgusunu yüzdür. Uzun probe'lar init'i ritüele çevirir.

Çıktı yapısı:

```
<repo>/
├── tools/
│   ├── init_agent.py
│   └── pre_task.sh
├── docs/
│   └── init.md
└── .github/
    └── workflows/
        └── agent-init.yml
```

"Bundan sonra ne okumalı" notu ile bitir:

- Init raporunun `repo_paths`'ını kullanan görev başına scope kontratı için Lesson 36.
- Çözümlenen test komutunu tüketen runtime feedback loop için Lesson 37.
- Probe'ların geçmesine bağımlı verification gate için Lesson 38.
