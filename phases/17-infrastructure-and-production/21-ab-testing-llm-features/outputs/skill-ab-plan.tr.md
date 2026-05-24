---
name: ab-plan
description: Bir LLM A/B testi tasarla — platform seç (Statsig veya GrowthBook), birincil metrik, guardrail'ler, LLM-gürültü tamponuyla örneklem boyutu, CUPED, sequential durdurma ve çoklu-karşılaştırma düzeltmesi.
version: 1.0.0
phase: 17
lesson: 21
tags: [ab-testing, statsig, growthbook, cuped, sequential, benjamini-hochberg, srm]
---

Özellik değişikliği (prompt / model / üretim parametresi), baseline metrikleri, beklenen lift ve takım tutumu (warehouse-native OSS vs bundled SaaS) verildiğinde, bir A/B planı üret.

Üret:

1. Platform. Statsig (bundled SaaS, OpenAI'nin sahip olduğu) veya GrowthBook (MIT OSS, warehouse-native). Gerekçelendir.
2. Birincil metrik + guardrail'ler. Birincil, hareket ettirmeye çalıştığın metriktir; guardrail'ler regresyona uğramamaları gereken şeylerdir (istek başına maliyet, latency P99, refusal oranı).
3. Örneklem boyutu. Klasik power hesaplaması × 1.4 (LLM non-determinizm tamponu).
4. Tasarım. Sabit-ufuk veya sequential. Güçlü sinyaller bekliyorsan sequential; değişiklik ince ise sabit.
5. CUPED. Birincil metrik için pre-periyot verisi varsa etkinleştir; regressor'ı belirt.
6. Düzeltme. Az sayıda test için Bonferroni; birçok ilgili test için Benjamini-Hochberg.
7. SRM. Her deneyde SRM kontrolünü iste; işaretlenirse durdur ve hata ayıkla.

Hard rejects:
- His üzerine ship etmek. Reddet — A/B veya belgelenmiş no-A/B istisnası iste.
- Aynı birincil metrik üzerinde BH/Bonferroni olmadan >5 deney çalıştırmak. Reddet — false discovery kesin.
- SRM kontrolünü atlamak. Reddet — atama bug'ları yaygındır.

Reddetme kuralları:
- Özellik için trafik < 1000 kullanıcı/hafta ise, sabit A/B'yi reddet — bunun yerine shadow + canary (Phase 17 · 20) iste.
- Birincil metrik objektif bir vekil olmadan subjektifse (ör. "kalite"), paralelde human eval iste.
- Lift hipotezi LLM gürültü tabanından küçükse, reddet — deney gerçekçi örneklem boyutuyla bunu tespit edemez.

Çıktı: platform, birincil + guardrail'ler, örneklem boyutu, tasarım, CUPED, düzeltme, SRM politikası içeren tek sayfalık plan. Karar kuralıyla bitir: birincil anlamlı + tüm guardrail'ler anlamlı-negatif değil → ship et; herhangi bir guardrail ihlali → birincil ne olursa olsun ship etme.
