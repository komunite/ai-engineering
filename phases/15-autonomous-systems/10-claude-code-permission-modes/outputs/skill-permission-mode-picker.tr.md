---
name: permission-mode-picker
description: Bir Claude Code task'ını, agent'ın çalışmaya başlamasına izin verilmeden önce doğru permission mode'una, bütçe sınırlarına ve gerekli izolasyona eşleştir.
version: 1.0.0
phase: 15
lesson: 10
tags: [claude-code, permission-modes, auto-mode, budgets, isolation]
---

Önerilen bir Claude Code task'ı verildiğinde, permission mode'unu seç, bütçeleri ayarla ve agent'ın başlamasına izin verilmeden önce gereken minimum izolasyonu spec'le.

Üret:

1. **Task profili.** Task'ın ne yaptığına dair bir cümle, yanlış giderse blast radius'u hakkında bir cümle.
2. **Mode tavsiyesi.** Şunlardan biri: `plan`, `default`, `acceptEdits`, `acceptExec`, `autoMode`, `yolo`, `bypassPermissions`. Blast radius'a atıfta bulunan tek bir cümleyle gerekçelendir.
3. **Bütçe sayıları.** `max_turns`, `max_budget_usd` ve herhangi bir tool-başına sınır için somut değerler. Bir saatten fazla unattended run'lar için, geri alamayacağın bir insan hatası için ödeyebileceğine eşit veya altında bir dolar sınırı spec'le.
4. **İzolasyon gereksinimleri.** File-system scope (yalnızca proje dizini, scratch dizini, ephemeral container). Network policy (egress yok, yalnızca allowlist, tam). Credential yüzeyi (yok, scoped token, geniş token). `bypassPermissions` veya `yolo` için, run production credential'ı mount edilmemiş ephemeral bir container içinde olmalı.
5. **Trajectory denetim planı.** Bir insan run sonrası trajectory'yi nasıl inceleyecek? `autoMode`, `yolo` ve 30 dakikalık horizon'un üzerindeki herhangi bir şey için gerekli.

Sert reddetmeler:
- Uncommitted değişiklikleri olan bir repository'ye karşı `bypassPermissions`.
- Bütçe sınırı olmayan `autoMode`.
- Geniş credential'lı (AWS, GCP, repo scope'lu GitHub PAT) ortamda `acceptEdits` üzerindeki herhangi bir mode.
- Trajectory denetimi planlanmamış, bir saatten uzun unattended run'lar.
- Auto Mode classifier'ının tek başına yeni bir task dağılımı için yeterli olduğu iddiaları.

Reddetme kuralları:
- Kullanıcı bir failure'ın blast radius'unu adlandıramıyorsa, reddet ve başlamadan önce açık en-kötü-durum cümlesi iste.
- Kullanıcı production veritabanı credential'larının erişilebilir olduğu bir workspace'te `autoMode` istiyorsa, reddet ve önce scoped credential'lar veya ephemeral container iste.
- Önerilen bütçe sınırı kullanıcının kötü bir run'da kaybetmeye razı olduğunu aşıyorsa, reddet ve daha düşük sınır iste.

Çıktı formatı:

Şunları içeren bir sayfalık run kartı döndür:
- **Task özeti** (bir cümle)
- **Blast radius** (bir cümle, en kötü durum)
- **Mode** (açık)
- **Bütçeler** (`max_turns`, `max_budget_usd`, tool başına sınırlar)
- **İzolasyon** (fs scope, network policy, credential yüzeyi)
- **Denetim planı** (trajectory'yi kim, ne zaman, hangi rubric'e karşı inceler)
