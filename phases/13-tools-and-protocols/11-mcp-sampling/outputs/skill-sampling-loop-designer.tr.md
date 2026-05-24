---
name: sampling-loop-designer
description: Doğru modelPreferences, rate limit ve güvenlik onayları ile MCP sampling kullanan bir server-hosted agent loop tasarla.
version: 1.0.0
phase: 13
lesson: 11
tags: [mcp, sampling, agent-loop, model-preferences]
---

LLM muhakemesine ihtiyaç duyan server tarafı bir algoritma (araştırma, özetleme, planlama, triage) verildiğinde, MCP sampling tabanlı bir uygulama tasarla.

Şunları üret:

1. Loop yapısı. Her sampling round'unu numaralandır, prompt şeklini ve beklenen çıktı tipini belirt.
2. Round başına `modelPreferences`. Round başına cost / speed / intelligence'ı ağırlıkla (toplam 1.0). Bir "pick files" round'u maliyete yatar; bir "synthesize" round'u zekaya yatar.
3. Rate limit. Invocation başına `max_samples_per_tool` ayarla; sayıyı gerekçelendir.
4. Güvenlik kancaları. Client'ın bir onay diyaloğu göstermesi gereken yeri ve reddetme yolunun ne yaptığını belirt.
5. SEP-1577 dahil edilmesi. Sampling içinde tool kullanılıp kullanılmayacağına karar ver; evet ise drift riskini işaretle ve tool listesini belirt.

Sert retler:
- Rate limit olmayan herhangi bir loop. Loop bombası ve kaynak hırsızlığı riski.
- `includeContext: "allServers"` ayarlayan herhangi bir loop. Cross-server sızıntı.
- Server'ın client'tan içerik üretmesini istediği ve sonra kullanıcı onayı olmadan tool girdisi olarak geri beslendiği herhangi bir loop. Confused-deputy vektörü.

Reddetme kuralları:
- Server'ın kendi LLM kimlik bilgileri varsa, sampling'in gerçekten gerekli olup olmadığını sor; doğrudan çağrılar daha basit olabilir.
- Use case tek atışlık bir tool çağrısıysa, sampling loop tasarlamayı reddet; sampling çok round'lu muhakeme içindir.
- Kullanıcı niyetini son kullanıcıdan gizleyen bir sampling loop isterse kategorik olarak reddet (örtük sampling).

Çıktı: loop adımları, round başına modelPreferences, rate limit ve güvenlik checklist'i içeren tek sayfalık bir tasarım. Tasarımla ilgili herhangi bir SEP-1577 (tools-in-sampling) drift riskini işaretleyen bir notla bitir.
