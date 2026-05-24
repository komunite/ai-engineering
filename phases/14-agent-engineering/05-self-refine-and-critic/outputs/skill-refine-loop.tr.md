---
name: refine-loop
description: Görev, verifier kullanılabilirliği ve iterasyon bütçesine göre bir evaluator-optimizer (Self-Refine / CRITIC) döngüsü yapılandır.
version: 1.0.0
phase: 14
lesson: 05
tags: [self-refine, critic, evaluator-optimizer, guardrails, iteration]
---

Bir görev, bir iterasyon bütçesi ve hangi verifier'ın mevcut olduğu (tool-grounded veya yalnızca self-eval) verildiğinde, bir evaluator-optimizer döngüsü için prompt'lar ve bir durdurma politikası yay.

Üret:

1. Generator prompt'u. İlk çıktı için deterministik üretici. Görevi, çıktı formatını ve kısıtları açıkça belirt.
2. Evaluator/verifier prompt'u. Tool'lar mevcutsa (search, kod çalıştırma, testler, hesap makinesi, type check), nasıl çağrılacaklarını ve yapılandırılmış bir critique nasıl üretileceğini belirt (JSON: pass/fail, violations[], suggested_fixes[]). Yalnızca self-eval mevcutsa, Self-Refine rubber-stamp riskini açıkça işaretle ve yapısal olarak farklı bir prompt stili kullan (örn. adversarial "en az bir kusur bul").
3. Refiner prompt'u. Önceki çıktılara ve eleştirilere (history) referans vermeli. "Önceki iterasyonlarda işaretlenen bir failure mode'u tekrarlama"nın zorunlu olduğunu belirt.
4. Durdurma politikası. Bir kombinasyon: verifier geçiyor VEYA (self-eval iyi diyor VE iterasyonlar >= 2) VEYA iterasyonlar >= max_iterations. Asla tek-koşul olmasın.
5. Observability kancaları. Her iterasyonu Lesson 23'e göre bir OpenTelemetry GenAI span (evaluate, optimize) olarak logla; böylece tüm refine trajectory'si denetlenebilir.

Sert ret durumları:

- Generator ve critic için aynı prompt. Rubber-stamp riski — model kendisiyle anlaşır.
- İterasyon sınırı yok. Sonsuz refine döngüleri token yakar; her zaman varsayılan olarak 4'te sınırla.
- Verifier prompt'u serbest biçimli düzyazı geri bildirim isteyen. Yalnızca yapılandırılmış JSON — pass/fail artı kalemli ihlaller.
- Refiner prompt'undan history'i düşürmek. Paper, history olmadan kalitenin çöktüğünü gösteriyor.

Reddetme kuralları:

- Görevin verifier'ı yoksa ve oluşturulamıyorsa, CRITIC'i reddet ve Self-Refine'ın kullanılabilir daha zayıf seçenek olduğunu belirt — kullanıcıyı rubber-stamp riskine karşı uyar.
- max_iterations >= 10 ise, reddet ve görevi yeniden mimarlamayı öner. 3-4 pas'ı aşan refine-to-convergence genelde generator prompt'unun yanlış olduğunun sinyalidir.
- Verifier destructive tool'ları çağırıyorsa (shell, git write), reddet ve bir sandbox sınırı talep et (Lesson 09).

Çıktı: tüm prompt'ları, durdurma politikasını ve tool listesini içeren tek bir yapılandırma bloğu, artı deployment hedefine göre Lesson 16 (OpenAI Agents SDK guardrails), Lesson 12 (Anthropic evaluator-optimizer) veya Lesson 30 (eval-driven agent development) yönlendiren bir "bundan sonra ne okumalı" notu.
