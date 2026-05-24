---
name: coding-scaffold-audit
description: Önerilen bir coding-agent scaffold'unu (retrieval, verifier loop, sandbox, benchmark fit) production kod değişiklikleri için benimsemeden önce denetle.
version: 1.0.0
phase: 15
lesson: 9
tags: [coding-agent, scaffolding, swe-bench, codeact, openhands]
---

Önerilen bir coding-agent scaffold'u (SWE-agent, OpenHands, Aider, Cline, Devin, Claude Code veya in-house bir build) verildiğinde, dört eksen üzerinde puanla ve benchmark sayılarının production kalitesini abartacağı yerleri işaretle.

Üret:

1. **Retrieval.** Scaffold'un agent'ın eylem öncesi okuyacağı dosyaları nasıl seçtiğini açıkla. Repo map, embedding araması, açık dosya listesi veya agent-driven `grep` çağrıları. Retrieval kalitesi sessiz baskın güvenilirlik faktörüdür.
2. **Verifier loop.** Scaffold testleri çalıştırıyor, stack trace'i okuyor ve başarısızlığı bir sonraki tur'a besliyor mu? Verifier loop yoksa, eksik olarak işaretle — bu genellikle SWE-bench-tarzı task'larda 10+ puanlık mutlak delta'dır.
3. **Sandbox ve blast radius.** Eylemler nerede execute oluyor? Local file system, ephemeral container, managed VM. CodeAct-tarzı scaffold'lar için sandbox'ın sertleştirildiğini doğrula (egress yok, host mount yok, zaman limiti). JSON tool-call scaffold'ları için, tool validator'ların her amaçlanmamış side effect'i reddettiğini doğrula.
4. **Benchmark fit.** Raporlanan sayının (örn. "SWE-bench Verified'da %80.9") gerçekte hangi dağılımı kapsadığını belirle. Benchmark'ın 1-2 satırlık task'lardan oluşan kısmını say; raporlanan skoru aynı model için SWE-bench Pro (10+ satırlık task'lar) ile karşılaştır. Headline sayısı easy tail tarafından sürülen bir scaffold production sinyali değildir.

Sert reddetmeler:
- Trivial complexity'nin üzerindeki task'lar için verifier loop'u olmayan herhangi bir scaffold.
- Gerçek repository'lere yönelik sandbox izolasyonu (Docker yok, rootless container yok, VM yok) olmayan CodeAct scaffold'ları.
- Dağılımı açıklamayan benchmark iddiaları (easy-tail kesri, Pro-eşdeğer skor).
- Tek bir tool'un validator olmadan keyfi path'lere dokunabildiği tool-call scaffold'ları (örn. modele açılmış ham bir `shell_exec` tool'u).

Reddetme kuralları:
- Kullanıcı scaffold'un test-suite pass-rate'ini temsili bir iç dağılımda üretemezse, reddet ve önce küçük örneklem ölçümü iste. Public benchmark'lar rank-order'ı öngörür, mutlak kaliteyi değil.
- Önerilen scaffold staging dry-run olmadan bir production repository'sine karşı çalışacaksa, reddet ve önce staging iste. Coding agent'lar dosyaları yeniden yazar; kötü retrieval'a sahip coding agent'lar yanlış dosyaları yeniden yazar.
- Kullanıcı go/no-go kararı vermek için yalnızca benchmark skorlarını kullanmayı planlıyorsa (kendi eval'ları olmadan), reddet ve iç eval verisi iste.

Çıktı formatı:

Şunları içeren puanlı bir memo döndür:
- **Retrieval skoru** (0-5, mekanizma açıklamasıyla)
- **Verifier loop skoru** (0-5, feedback formatıyla)
- **Sandbox skoru** (0-5, izolasyon mekanizmasıyla)
- **Benchmark fit skoru** (0-5, iç dağılım delta'sıyla)
- **Deployment tavsiyesi** (production / staging / yalnızca araştırma)
- **Tek satır risk özeti** (en olası ilk production failure)
