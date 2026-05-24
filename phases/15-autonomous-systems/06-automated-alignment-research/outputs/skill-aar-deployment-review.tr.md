---
name: aar-deployment-review
description: Sandbox izolasyonu ve log bütünlüğü dahil, otomatik-alignment-research pipeline'ının deployment öncesi incelemesi.
version: 1.0.0
phase: 15
lesson: 6
tags: [aar, alignment-research, sandbox, log-integrity, rsp]
---

Önerilen bir Automated-Alignment-Research deployment'ı (model, sandbox, task queue, forum) verildiğinde, bir frontier-lab safety ekibinin onaylayacağı bir deployment öncesi inceleme üret.

Üret:

1. **Sandbox izolasyonu.** Her AAR instance'ı için filesystem, network ve process limitlerini doğrula. Hiçbir AAR'nin başka bir AAR'nin sandbox'ını okuyamadığını veya değiştiremediğini doğrula. Hiçbir AAR'nin forum storage'ın write endpoint'ine doğrudan ulaşamadığını doğrula (tüm post'lar ayrı bir service'ten geçer).
2. **Forum log bütünlüğü.** Forum append-only ve tamper-evident olmalı. Storage'ı spec'le (örn. object lock'lu S3, immutable ledger, append-only WAL). Doğrulama aralığını ve tampering tespit edilirse yanıtı spec'le.
3. **Task atama politikası.** Task'ların nasıl atandığını belirt: kim yazıyor, kim onaylıyor, AAR'ler kendi follow-up task'larını önerebilir mi, hangi koşullar altında. Özgür ayrıştırma performansta kazanır; talimatlandırılmış workflow auditability'de kazanır. Tradeoff'u açıkça belgele.
4. **İnsan inceleme kapısı.** Bir AAR çıktısı gerçek araştırma yönünü, eğitim verisini veya yayınlanan işi etkilemeden önce, adlandırılmış bir insan reviewer onaylamalı. İnceleme checklist'ini spec'le: deney tekrarlanabilirliği, log eksiksizliği, iddia-kanıt haritalaması.
5. **Eşik monitörlemesi.** AAR sisteminin RSP v3.0 AI R&D-4 bölgesine yaklaştığına dair sinyalleri takip et: task complexity delta, otonom sub-task spawning, cross-task bilgi transferi. Yükseltilmiş inceleme gerektiren eşikleri tanımla.

Sert reddetmeler:
- Tamper-evident, sandbox-dışı log'lar olmayan herhangi bir AAR deployment'ı.
- AAR'lerin çıktılarının doğrudan adlandırılmış insan incelemesi olmadan eğitim verisine veya production policy'ye beslendiği herhangi bir pipeline.
- Tek bir AAR'nin birden fazla downstream sistemi etkileyecek yeterli credential'a sahip olduğu herhangi bir pipeline.

Reddetme kuralları:
- Sandbox izolasyonu spec'lenmemişse veya tek bir katmana dayanıyorsa (yalnızca Docker, seccomp / gVisor yok), reddet ve defense-in-depth iste.
- Log storage herhangi biri tarafından düzenlenebilirse (operatörler bile), reddet ve write-once medya iste.
- Deployment'ın amacı capability pipeline'ının bir kısmını otomatikleştirmekse — yalnızca alignment research değil — reddet ve RSP incelemesine yükselt.

Çıktı formatı:

Şunları içeren bir inceleme memo'su döndür:
- **Pipeline özeti** (bir paragraf)
- **İzolasyon skoru** (boyut başına: fs, net, proc, peer)
- **Log bütünlüğü skoru** (doğrulama planıyla)
- **Task atama kararı** (sabit / özgür / hibrit, gerekçeyle)
- **İnsan inceleme kapısı** (reviewer adı, checklist)
- **Eşik monitörleri** (sinyal listesi, eşikler, yanıt)
- **Deployment kararı** (go / hold / no-go)
