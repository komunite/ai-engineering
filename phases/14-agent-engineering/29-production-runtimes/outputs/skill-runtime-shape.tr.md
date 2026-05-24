---
name: runtime-shape
description: Bir production runtime şekli seç (request-response, streaming, queue, event, cron, durable) ve observability'yi bağla.
version: 1.0.0
phase: 14
lesson: 29
tags: [production, runtime, queue, event, durable, observability]
---

Bir görev sınıfı (beklenen süre, adım sayısı, tetikleyici tipi, latency bütçesi) verildiğinde, runtime şeklini seç.

Karar:

1. < 30s, kullanıcı bekliyor -> **request-response**.
2. Progressive UX veya voice -> **streaming**.
3. Dakikalardan saatlere, kullanıcı beklemiyor -> **queue-tabanlı**.
4. Harici event'lere reaktif -> **event-driven**.
5. Periyodik housekeeping -> **cron**.
6. Restart maliyeti yüksek olan yukarıdakilerden biri -> **durable execution** ekle.

Üret:

1. Stack'inde şekil iskelesi.
2. Observability: OTel GenAI span'leri (Lesson 23), backend bağlı (Lesson 24).
3. Queue için: DLQ + retry politikası + queue depth metriği.
4. Event için: açık subscriber registry + replay yolu.
5. Cron için: örtüşen çalıştırmaları önlemek için lock file veya distributed lock.
6. Durable için: checkpointer backend + resume semantikleri.

Sert ret durumları:

- 5 dakikalık görev için senkron HTTP. Kullanıcılar telefonu kapatır; worker'lar yığılır.
- DLQ olmadan queue-tabanlı. Başarısız işler kaybolur.
- Trace export olmadan background iş. Kullanıcılar şikayet edene kadar başarısızlıklar görünmez.
- "Durable state yok, sadece retry yapacağız." Uzun horizon'lar checkpoint atmalı.

Reddetme kuralları:

- Ürünün SLA + replay gereksinimleri varsa, swarm topoloji + non-durable runtime'ı reddet.
- Görev compliance-bağlı ise, denetim izi olmadan event-driven'ı reddet.
- Kullanıcı cron + lock yok isterse, reddet. Örtüşen cron çalıştırmaları en iyi ihtimalle çift iş, en kötü ihtimalle veri bozulmasıdır.

Çıktı: runtime iskelesi + observability kancaları + SLA, retry politikası, checkpointer seçimi içeren README. "Bundan sonra ne okumalı" notu ile bitir: Lesson 23 (OTel), Lesson 24 (observability) veya Lesson 17 (hosted uzun süreli çalışmalar için Managed Agents).
