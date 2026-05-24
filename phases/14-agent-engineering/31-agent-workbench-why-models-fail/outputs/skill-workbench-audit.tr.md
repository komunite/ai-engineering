---
name: workbench-audit
description: Bir repo'yu yedi agent workbench yüzeyi için denetle ve herhangi bir agent çalışması başlamadan önce hangisinin eksik, kısmi veya sağlıklı olduğunu raporla.
version: 1.0.0
phase: 14
lesson: 31
tags: [workbench, audit, reliability, agent-engineering]
---

Bir repository yolu ve içinde çalışacak agent ürünü verildiğinde, yedi workbench yüzeyini denetle ve bir hazırlık raporu üret.

Yedi yüzey:

1. Instructions: agent'in önce okuduğu kök bir dosya (örn. `AGENTS.md`), kısa, daha derin kurallara yönlendirir.
2. State: görev, dokunulan dosyalar, blocker'lar, sonraki eylem'i kaydeden durable, makine-okunabilir bir dosya.
3. Scope: görev başına izin verilen dosyaları, yasak dosyaları, kabul kriterlerini, rollback planını listeleyen bir kontrat.
4. Feedback: komutu, stdout, stderr, exit code'u yakalayan ve sonucu döngüye geri besleyen bir runner.
5. Verification: testleri, lint, type-check, smoke run'ı çalıştıran ve kabul kriterlerini onaylayan bir gate.
6. Review: farklı rolle ikinci bir pas, builder kendi işini işaretleyemez.
7. Handoff: neyin değiştiğini, neden, neyin kaldığını ve sonraki en iyi eylemi özetleyen bir artifact.

Üret:

- Yüzey başına bir skor: 0 eksik, 1 kısmi, 2 sağlıklı. Her skoru gözlemlediğin bir dosya veya sürece bağla.
- Leverage'a göre sıralanmış üç öncelik: ilk eklenirse en çok failure mode'u hangisi kaldırır.
- Bir `workbench_audit.json` makine-okunabilir rapor artı `workbench_audit.md` insan-okunabilir özet.
- En zayıf yüzey için bir starter patch: skoru 0'dan 1'e taşıyan en küçük dosya değişikliği.

Sert ret durumları:

- Dosya yolu veya süreç referansı olmadan "sağlıklı" skorlar. Kanıtsız denetimler çürür.
- Tek bir birleşik "agent config" yüzeyi. Yüzeyleri birleştirmek bir görev kırıldığında hangisinin başarısız olduğunu gizler.
- Testler yavaş diye verification'ı atlamak. Verification workbench'te değilse, builder'lar kendi ödevlerini işaretler.

Reddetme kuralları:

- Repo'nun hiç test komutu yoksa, verification skorunu reddet ve bunu bir bloklayıcı bulgu olarak yüzdür.
- Repo'nun version control geçmişi yoksa, handoff skorunu reddet ve bunu bir bloklayıcı bulgu olarak yüzdür.
- Agent ürünü root olarak veya kısıtlanmamış dosya erişimiyle çalışıyorsa, sandbox veya write list tanımlanana kadar scope skorunu reddet.

Çıktı yapısı:

```
workbench-audit/
├── workbench_audit.json
├── workbench_audit.md
├── patches/
│   └── <weakest-surface>.patch
└── README.md
```

"Bundan sonra ne okumalı" notu ile bitir:

- Minimal repo düzeni için Lesson 32.
- Derinlemesine instructions yüzeyi için Lesson 33.
- Verification gate için Lesson 38.
