---
name: horizon-interpretation
description: Bir vendor'ın time-horizon iddiasını incele ve benchmark iddiası ile deployment gerçekliği arasındaki gap analizini üret.
version: 1.0.0
phase: 15
lesson: 21
tags: [metr, time-horizon, hcast, re-bench, eval-vs-deploy, external-evaluation]
---

Bir vendor'ın yayınlanmış time-horizon iddiası verildiğinde (örn. "modelimiz 14 saatlik task'ları %50 güvenilirlikte tamamlıyor"), deployment-gerçeklik delta'sını niceleyen ve metodolojik zayıflıkları işaretleyen bir gap analizi üret.

Üret:

1. **Metodoloji denetimi.** Task suite'i belirle (HCAST, RE-Bench, SWAA veya proprietary). Lojistik fit'in açıklandığını doğrula (slope, örneklem büyüklüğü, confidence interval). Metodoloji açıklaması olmayan bir horizon bir pazarlama iddiasıdır.
2. **Task dağılım fit'i.** Vendor'ın benchmark task dağılımını kullanıcının production task dağılımına haritala. Materyal olarak ayrılıyorlarsa (vendor SWE task'larını ölçüyor, production müşteri-destek akışları), sayı transfer olmaz.
3. **Eval-bağlam gap'i.** Benchmark horizon'u ile deployment gerçekliği arasına %10-40 gap uygula. Eval-bağlam gaming üzerine Anthropic 2024 alignment-faking çalışmasını ve 2026 International AI Safety Report'u alıntıla. Gerçek gap eval protokolüne bağlıdır; gaming yapılandırılmamış task'larda daha yüksektir.
4. **Tooling gap'i.** Benchmark tooling'i temiz ve iyi-instrumented'dir. Production tooling'i daha dağınıktır. Ek %5-30 güvenilirlik indirimi tahmin et.
5. **Human-in-the-loop varsayımı.** Benchmark'lar HITL olmadığını varsayar. HITL ile production agent'lar daha yüksek güvenilirlikte ama daha düşük otonomide çalışır. Horizon yorumunu buna göre ayarla.

Sert reddetmeler:
- Kaynak metodoloji veya örneklem büyüklüğü olmayan horizon iddiaları.
- Bir benchmark horizon'unun deployment güvenilirliğini öngördüğü iddiaları.
- 2025-veya-öncesi bir horizon sayısını güncel olarak alıntılayan vendor'lar (doubling time ~7 ay; 2025 sayıları bir yıl içinde eskidir).
- %50 horizon'u "çoğu zaman çalışacak" olarak ele almak — %50 güvenilirlik bir yazı-tura atışıdır.

Reddetme kuralları:
- Vendor metodoloji açıklamıyorsa, reddet ve kaynak makaleyi veya blog yazısını iste.
- Benchmark dağılımı production dağılımıyla örtüşmüyorsa, reddet ve iç değerlendirme iste.
- Vendor spesifik eval pipeline'larında gaming denetimi olmadan horizon'lar alıntılıyorsa, sayıyı güvenilirlik öngörüsü olarak alıntılamayı reddet.

Çıktı formatı:

Şunları içeren bir horizon-yorumlama memo'su döndür:
- **Kaynak metodoloji** (suite, fit yöntemi, örneklem büyüklüğü, CI)
- **Dağılım örtüşmesi** (benchmark vs production; % haritalama)
- **Eval-bağlam gap tahmini** (low / med / high, gerekçeyle)
- **Tooling gap tahmini** (low / med / high)
- **HITL varsayımı** (benchmark-tarzı otonom vs production HITL)
- **Deploy-ayarlı horizon** (gap ve tooling indirimleri sonrası horizon)
- **Hazırlık kararı** (production / staging / yalnızca araştırma)
