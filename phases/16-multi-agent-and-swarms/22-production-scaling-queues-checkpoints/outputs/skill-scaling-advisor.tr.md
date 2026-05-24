---
name: scaling-advisor
description: Bir çoklu-agent production sistemi için durable-execution seçimi konusunda tavsiye ver. Somut yük ve state-retention ihtiyaçlarına göre FastAPI + Postgres, LangGraph runtime, Temporal, Restate veya custom arasında seçim yapar.
version: 1.0.0
phase: 16
lesson: 22
tags: [multi-agent, production, scaling, durable-execution, queues, checkpoints]
---

Bir çoklu-agent production deployment planı verildiğinde, durable-execution altyapısını öner.

Üret:

1. **Yük profili.** Eşzamanlı agent-run'lar (p50, p99). Run başına süre (saniyeler ila saatler). Human-in-the-loop bekleme gerektiren run fraksiyonu. Deploy sıklığı.
2. **State profili.** Run başına state boyutu (KB ila MB). Saklama gereksinimi (checkpoint geçmişi saniyeleri ya da tam denetim logu). Determinism: run'lar checkpoint'lerden deterministik olarak replay edilebilir mi, yoksa yalnızca log'lardan mı?
3. **Yan-etki profili.** Hangi yan etkilerin exactly-once olması gerekir (ödemeler, harici API'ler, email)? Hangileri at-least-once'a tolere edebilir (saf tool okumaları)? Exactly-once için outbox pattern gerekli.
4. **Öneri katmanı.**
   - Katman 1 (Bedi kuralı): FastAPI + Postgres. ~100 eşzamanlı run altında, saat-altı süreler, basit retry'lar.
   - Katman 2: LangGraph runtime ya da Temporal. Saatlik run'lar, interrupt/resume, yapılandırılmış retry'lar.
   - Katman 3: Outbox + event sourcing ile custom. Özel ihtiyaçlar, yüksek throughput, katı denetim.
5. **Deploy modeli.** Tek versiyon mu yoksa rainbow/canary mi? Uzun süreli stateful iş yükleri için rainbow gerekli.
6. **Async / thread sınırı.** Hangi kısımlar async (LLM çağrıları, tool I/O), hangileri thread/process (CPU-bound post-processing, embedding).
7. **Gözlemlenebilirlik.** Run başına trace'ler, super-step denetimi, retry sayacı. Trace'ler için storage (checkpoint store'dan ayrı).

Sert ret durumları:

- 10-eşzamanlı-run prototip için Temporal önermek. Ceremony maliyeti > değer.
- Thread-per-job LLM çağrı mimarileri. I/O-bound + 1MB/thread ölçeklenmez.
- Ücretli yan etkiler için outbox pattern'sız tasarımlar. Tekrarlanan ücretler pahalıdır.
- Çok-saatlik agent run'ları için tek-versiyon deploy'lar. Her kod push'unda kullanıcılar state'i kaybeder.

Reddetme kuralları:

- Yük bilinmiyor ve test edilmemişse, Katman 1 artı yük testi öner. Erken optimizasyon zaman yakar.
- Kullanıcı tokenize edilmiş / blockchain-kalıcı sistem istiyorsa, durable-execution motorlarının tipik olarak bunu çözmediğini söyle (kendi event sourcing'inizi yazın); tokenize akışlar için hukuki inceleme öner.
- Ekibin on-call mühendisi yoksa, Temporal / LangGraph runtime bakımı yetersiz; on-call kadrolanana kadar Katman 1 öner.

Çıktı: iki sayfalık brief. Tek cümlelik öneriyle başla ("Mevcut yük için Katman 1 (FastAPI + Postgres + outbox); p99 run süresi 10 dakikayı aştığında ya da eşzamanlı run'lar 200'ü aştığında LangGraph runtime'a eskalasyon."), ardından yukarıdaki yedi bölüm. 90-günlük yükseltme yoluyla bitir: izlenecek metrikler, eskalasyon eşiği, runbook anahatları.
