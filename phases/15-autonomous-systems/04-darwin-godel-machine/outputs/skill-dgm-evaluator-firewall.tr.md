---
name: dgm-evaluator-firewall
description: Darwin-Godel-Machine-tarzı self-modifying agent döngüsünün belgelenmiş reward hacking'i önlemek için ihtiyaç duyduğu evaluator ayrımını spec'le.
version: 1.0.0
phase: 15
lesson: 4
tags: [dgm, self-modification, reward-hacking, evaluator, sandbox]
---

Önerilen bir self-modifying agent döngüsü (agent scaffolding, evaluator pipeline'ı, deployment hedefi) verildiğinde, evaluator'ı agent'ın erişiminin dışında tutan bir firewall spec'i üret. DGM makalesi, agent'ın skorları yükseltmek için kendi safety marker'larını kaldırdığını belgeledi; bu skill kontroldür.

Üret:

1. **Dosya sistemi sınırı.** Agent'ın düzenleyebileceği her dosyayı listele. Evaluator'ın okuduğu her dosyayı listele. Kesişim boş olmalı. Değilse, onu boş yapmak için gereken tam hareketi spec'le.
2. **Process sınırı.** Evaluator, agent'ın kontrol etmediği bir process'te çalışmalı. Container veya sandbox'u spec'le. Agent'ın shell erişimi varsa, agent in-process koruyucuları atlatabilir.
3. **Network ve secret sınırı.** Agent, evaluator girdilerini çeken veya skor gönderen CI secret'larını düzenleyememeli. Secret'ların nerede yaşadığını ve nasıl mount edildiğini listele.
4. **Skor-ingress kontratı.** Skorlar evaluator'dan döngünün arşivine döner. Bu yol tek kanaldır. Agent'ın yazabildiği ve gelecekteki skorlamayı etkileyen herhangi bir şey kontratı bozar.
5. **Mutation inceleme listesi.** Kabul öncesi manuel inceleme gerektiren agent edit sınıflarını listele: yeni bağımlılıklar, scoring-adjacent koda edit'ler, sandbox konfigürasyonuna edit'ler, logging veya monitoring'e edit'ler.

Sert reddetmeler:
- Agent kaynağıyla aynı repository'deki evaluator. Dışarı taşı.
- Agent process'i içinde Python import olarak çalışan evaluator. Bir subprocess'te çalıştır.
- Sınırın agent tarafında uygulanan herhangi bir skor düzeltmesi. Tüm düzeltme server-side olmalı.
- Agent'ın kendi kodunu düzenleyerek susturabileceği herhangi bir logging.

Reddetme kuralları:
- Kullanıcı agent'ın düzenleyebildiği her dosyayı adlandıramıyorsa, reddet ve önce dosya-seviyesinde write-access denetimi iste.
- Evaluator'ın held-out girdileri yoksa, reddet — bu Lesson 3'ün denetimidir, bir ön koşul.
- Deployment yüzeyi evaluator'ın kendisine mutation içeriyorsa (önerilen bir bağımlılık güncellemesi yoluyla dolaylı olarak bile), reddet ve manuel firewall-inceleme adımı iste.

Çıktı formatı:

Şunları içeren bir sayfalık spec döndür:
- **Agent write-surface** (path'ler, glob'lar)
- **Evaluator read-surface** (path'ler, endpoint'ler)
- **Kesişim** (boş olmalı; diff'i göster)
- **Process modeli** (evaluator nasıl izole edildi)
- **Secrets envanteri** (nerede ve nasıl mount edildi)
- **İnceleme gerektiren mutation sınıfları** (madde madde)
- **Sign-off satırı** (firewall invariant'ının sahibi kim)
