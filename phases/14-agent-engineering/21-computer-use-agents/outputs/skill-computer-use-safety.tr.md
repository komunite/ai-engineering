---
name: computer-use-safety
description: Bir computer-use agent için adım başına güvenlik classifier'ı + onay kapısı kur; allowlist navigasyonu ve injection-marker filtrelemesi ile.
version: 1.0.0
phase: 14
lesson: 21
tags: [computer-use, safety, claude, openai-cua, gemini]
---

Bir computer-use agent ve hedef uygulamalar listesi verildiğinde, her eylemi yürütülmeden önce sınıflandıran bir güvenlik katmanı üret.

Üret:

1. `allow`, `reason`, `needs_confirmation` alanlarına sahip `SafetyClassifier.assess(action, screen) -> SafetyVerdict`.
2. Agent'in tıklayabileceği element etiketlerinin allowlist'i; aksi takdirde ret.
3. Agent'in gezinebileceği URL'lerin allowlist'i; listenin dışına yönlendirmelerde ret.
4. DOM metni, geri alınan içerik ve yazılan metin üzerinde injection-marker filtresi. Herhangi bir eşleşme eylemi engeller.
5. Hassas eylemler için onay kapısı (login, satın alma, silme, yayınlama). Human-in-the-loop callback arayüzü.
6. Trace emitter'ı: her karar (action, verdict, reason) ile loglanır.

Sert ret durumları:

- Yalnızca ilk eylemde çalışan güvenlik classifier'ı. Her eylem sınıflandırılmalıdır.
- `*` biçiminde allowlist. Her şeye izin veren bir allowlist, bir allowlist değildir.
- Model "kendinden emin görünüyor" diye onayı atlamak. Güven, güvenlik değildir.

Reddetme kuralları:

- Agent adım başına güvenlik olmadan computer-use erişimine sahipse, göndermeyi reddet.
- Agent rastgele URL'lere gezinebiliyorsa, reddet. Allowlist veya blocklist talep et.
- Hassas eylemler herhangi bir modda onay kapısını atlıyorsa, reddet.

Çıktı: `classifier.py`, `allowlist.py`, `confirmation.py`, `trace.py`, kapı politikasını, injection marker'larını ve allowlist bakım sürecini açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 27 (prompt injection) ve Lesson 23 (güvenlik kararları için OTel span attribution).
