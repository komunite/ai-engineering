---
name: primitive-splitter
description: Bir MCP server taslağındaki her kabiliyeti gerekçesiyle tool, resource ya da prompt olarak kategorize et.
version: 1.0.0
phase: 13
lesson: 10
tags: [mcp, primitives, resources, prompts]
---

Önerilen bir MCP server'ın kabiliyetleri (sade İngilizce ya da taslak tool listesi olarak) verildiğinde, her birini tek cümlelik bir gerekçeyle tool, resource ya da prompt olarak kategorize et.

Şunları üret:

1. Kabiliyet başına kategorizasyon. Her item için `{name, primitive: tool | resource | prompt, rationale}` döndür.
2. Resource URI scheme. Herhangi bir kabiliyet resource olursa, bir URI scheme (`notes://`, `gh://`, `db://`) ve template pattern öner.
3. Prompt argüman iskeletleri. Herhangi bir kabiliyet prompt olursa, argüman listesi ve required/optional bayraklarını öner.
4. Subscription adayları. Sık değişen ve `resources/subscribe`'tan yararlanabilecek resource'ları işaretle.
5. Anti-pattern bayrakları. Eski bir tasarımın bir okumayı tool'la (örneğin `notes_read(id)`) sardığı ancak resource'un daha iyi hizmet edebileceği durumları işaret et.

Sert retler:
- Ayırma yapılmadan "hem tool hem resource" olarak kategorize edilen herhangi bir kabiliyet. Birini seç ya da bir çift iskelele.
- Required argümanları tanımlanmamış herhangi bir prompt. Slash-command UI'larında yüzeye çıkarmak argüman şemalarına ihtiyaç duyar.
- Adreslenebilir olmayan herhangi bir resource URI scheme (URI değil, serbest formlu string'ler).

Reddetme kuralları:
- Tüm kabiliyetler tool olarak konumlanırsa reddet ve server'ın resource olabilecek read-only verisi olup olmadığını sor.
- Hiçbir kabiliyet prompt'a uymuyorsa, sorun değil; prompt'lar opsiyoneldir. İcat etme.
- Server'ın domain'i A2A (agent-to-agent işbirliği, opaque state) tarafından daha iyi hizmet ediyorsa reddet ve Phase 13 · 19'a yönlendir.

Çıktı: kategorizasyon tablosu, URI scheme önerisi, prompt iskeletleri ve subscription bayraklarını içeren tek sayfalık bir karar raporu. Bu server için en etkili tool -> resource dönüşümüyle bitir.
