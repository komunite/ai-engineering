---
name: swarm-fit
description: Bir görevin swarm (merkeziyetsiz) mimariye mi yoksa supervisor (merkezi) mimariye mi uyduğuna karar ver.
version: 1.0.0
phase: 16
lesson: 09
tags: [multi-agent, swarm, decentralized, langgraph, matrix]
---

Bir görev ve throughput / determinism gereksinimleri verildiğinde, swarm ya da supervisor öner ve spesifik kuyruk ile guardrail tercihlerini listele.

Üret:

1. **Görev bağımsızlığı kontrolü.** Alt görevler bağımsız mı yoksa birbirine bağımlı mı? Swarm yalnızca bağımsızlık yüksek olduğunda uyar.
2. **Süre dağılımı.** Üniform vs değişken. Swarm çoğunlukla değişken-süreli iş yüklerinde kazanır.
3. **Sıralama gereksinimi.** Katı, gevşek ya da yok. Swarm sırayı korumaz; supervisor korur.
4. **Hata ayıklanabilirlik ihtiyacı.** Yüksek (finans, tıp) → supervisor. Orta → görev başına trace ID'li swarm.
5. **Kuyruk seçimi.** Demolar için in-memory (`queue.Queue`); production için Kafka / Redis Streams / NATS / dayanıklı DB-destekli.
6. **Worker tasarım gereksinimleri.** Idempotent olmalı; görev başına trace yaymalı; back-pressure'ı ele almalı.
7. **Anti-starvation planı.** Priority aging, worker uzmanlaşması, bounded queue.
8. **Gözlemlenebilirlik planı.** Görev başına ID'ler, start/end event'leri, sonuç havuzu şeması.

Sert ret durumları:

- Katı sıralama gereksinimleri olan görevler için swarm önerisi.
- Idempotent olmayan worker'larla swarm.
- Production'da durable queue olmadan swarm.

Reddetme kuralları:

- Görev saniyede 10'dan az bağımsız birimden oluşuyorsa, swarm'ı reddet ve supervisor öner. Düşük throughput'ta swarm ek yükü gerekçeli değildir.
- Gözlemlenebilirlik gereksinimleri tek tutarlı trace gerektiriyorsa (denetim, uyumluluk), swarm'ı reddet ve onun yerine LangGraph deterministik graph öner.

Çıktı: bir sayfalık mimari brief'i. Uygunluk kararıyla aç, hedef throughput için spesifik message broker önerisiyle kapat.
