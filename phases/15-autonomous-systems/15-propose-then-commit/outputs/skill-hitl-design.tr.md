---
name: hitl-design
description: Önerilen bir Human-in-the-Loop workflow'unu propose-then-commit şekli için incele ve eksik metadata, idempotency, verify veya challenge-and-response katmanlarını işaretle.
version: 1.0.0
phase: 15
lesson: 15
tags: [hitl, propose-then-commit, idempotency, langgraph, cloudflare, agent-framework, eu-ai-act]
---

Önerilen bir HITL workflow'u verildiğinde, propose-then-commit referansına karşı denetle ve neyin eksik, az-spec'lenmiş veya regulator-uyumsuz olduğunu işaretle.

Üret:

1. **Proposal metadata'sı.** Her proposal'ın şunları yüzeye çıkardığını doğrula: intent (neden), data lineage (kaynak content), dokunulan permission'lar, blast radius (en kötü durum), rollback planı. Eksik alanlar blocker'dır; "agent X yapmak istiyor" bir proposal değildir.
2. **Idempotency.** Idempotency key bileşimini adlandır. Proposal içeriğinden türetilebilir olmalı, böylece retry'lar aynı record'u döndürür. Wall-clock zamanı içeren key'ler idempotency key değildir; logging timestamp'lerdir.
3. **Durability.** Store'u adlandır (PostgreSQL, Redis, Durable Object, integrity check'li object storage). Onayların agent restart'ı, host restart'ı ve deploy'u atlattığını doğrula. In-memory queue'lar kalifiye olmaz.
4. **Approval yüzeyi.** Rubber-stamp onay (tek Approve butonu) bu denetimi geçemez. Gerekli: intent anlayışı, blast-radius doğrulaması ve rollback hazırlığı üzerine pozitif acknowledgement içeren challenge-and-response checklist. Checklist'in spesifik eylem sınıfına özel olduğunu doğrula, generic değil.
5. **Post-commit verify.** Workflow'un execution sonrası hedef kaynağı yeniden okuduğunu ve verify failure'da alert verdiğini doğrula. "Tool 200 döndü" verify değildir.

Sert reddetmeler:
- Proposal'ları durably persist etmeyen HITL yüzeyleri.
- Reviewer'ın agent'ın kendisi olduğu approval akışları.
- Challenge-and-response olmayan herhangi bir geri alınamayan production eylemi.
- Wall-clock bileşenleri olan idempotency key'leri.
- Sonuçsal eylemlerde post-commit verify'ın olmadığı workflow'lar.

Reddetme kuralları:
- Kullanıcı approval UI'sini adlandırıp ardındaki durable store'u adlandıramıyorsa, reddet ve önce store iste.
- Kullanıcı "max_budget_usd ve confirmation dialog'u" yeterli HITL olarak ele alıyorsa, reddet. Bütçeler maliyeti sınırlar, doğruluğu değil.
- Deployment yüksek-riskli EU kapsamına dokunuyor ve rubber-stamp pattern'ları kalıyorsa, Article 14 gerekçesiyle reddet.

Çıktı formatı:

Şunları içeren bir propose-then-commit denetimi döndür:
- **Proposal alan tablosu** (intent / lineage / blast / rollback / permission'lar — beşi de gerekli)
- **Idempotency notu** (key bileşimi, retry test sonucu)
- **Durability satırı** (store, restart'ı atlatır y/n)
- **Approval yüzeyi** (rubber-stamp / checklist; checklist ise soruları listele)
- **Post-commit verify** (mevcut y/n, neyi yeniden okur)
- **Hazırlık** (production / staging / yalnızca araştırma)
