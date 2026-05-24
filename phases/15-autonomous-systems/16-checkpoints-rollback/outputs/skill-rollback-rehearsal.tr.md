---
name: rollback-rehearsal
description: Önerilen otonom bir workflow için rollback-prova testi tasarla ve denetim izi kalıcılığı için checkpoint backend'ini denetle.
version: 1.0.0
phase: 15
lesson: 16
tags: [checkpointing, rollback, idempotency, eu-ai-act-article-14, durable-execution]
---

Önerilen uzun-horizon otonom bir workflow verildiğinde, idempotency + precondition + verify + rollback stack'inin gerçekten uçtan uca çalıştığını kanıtlayan bir rollback-prova testi tasarla ve regulator-hazırlığı için checkpoint backend'ini denetle.

Üret:

1. **Prova script'i.** (a) workflow'u başlatan, (b) commit ortasında crash eden, (c) devam eden, (d) eylemin tam olarak bir kez çalıştığını assert eden, (e) bir verify failure enjekte eden, (f) rollback'in çalıştığını ve state'in geri yüklendiğini assert eden somut bir test. Hiçbir production workflow'u bu test en az bir kez geçmeden çalışmamalıdır.
2. **Idempotency denetimi.** Idempotency key'in proposal içeriğinden türediğini (Lesson 15) ve commit logic'inin açık execution state'leri (`pending` -> `executing` -> `committed`/`failed`) kullandığını doğrula. Side effect öncesi idempotency key ile rezerve et/kilitle ve `committed`'i yalnızca side effect doğrulandıktan sonra işaretle.
3. **Precondition envanteri.** Workflow'un commit zamanında yeniden kontrol etmesi gereken her precondition'ı listele. Time-of-check vs time-of-use boşlukları en yaygın production bug'ıdır; precondition propose'da değil commit'te değerlendirilmelidir.
4. **Verify envanteri.** Her sonuçsal eylem için, side effect'in olduğunu doğrulayan spesifik read'i adlandır. "200 döndü" kabul edilemez.
5. **Rollback envanteri.** Her sonuçsal eylem için, rollback'i in-band, compensating transaction veya out-of-band alert olarak sınıflandır. No-op rollback'ler ("bunu geri alamayız") proposal'da açıkça adlandırılmalıdır (Lesson 15 metadata).

Sert reddetmeler:
- Prova edilmiş rollback olmayan workflow'lar.
- Deploy'da veri kaybeden checkpoint backend'leri.
- Status'un execution öncesi değil sonrası yazıldığı commit yolları.
- Yalnızca tool çağrısının return code'unu kontrol eden "verified" state'leri.
- Yalnızca propose zamanında çalışan, commit zamanında çalışmayan precondition kontrolleri.

Reddetme kuralları:
- Kullanıcı prova script'ini staging'de en az bir kez çalıştırmadıysa, production rollout'u reddet.
- Kullanıcı checkpoint store şemasını üretemezse, reddet ve önce şema dokümantasyonu iste. Regulator'lar sorgulanabilir state ister.
- Workflow in-memory checkpoint'e bağımlıysa (persistence yok), reddet.

Çıktı formatı:

Şunları içeren bir prova planı döndür:
- **Test script taslağı** (assertion'larla adımlar)
- **Idempotency tablosu** (key bileşimi, status-write sırası)
- **Precondition tablosu** (kontrol, ne zaman değerlendirildi, sonuç)
- **Verify tablosu** (eylem, doğrulayan read)
- **Rollback tablosu** (eylem, tip, hedef state)
- **Backend attestasyonu** (store, deploy'u atlatır y/n, sorgu-hazır y/n)
- **Hazırlık** (production / staging / yalnızca araştırma)
