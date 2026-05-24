---
name: ipi-audit
description: Agentic bir deployment'ı indirect prompt injection maruziyeti ve information-flow-control kapsamı için denetle.
version: 1.0.0
phase: 18
lesson: 15
tags: [ipi, indirect-prompt-injection, ifc, agent-security, owasp-llm01]
---

Agentic bir deployment tanımı verildiğinde, deployment'ı indirect prompt injection maruziyeti için denetle.

Üret:

1. Untrusted-içerik envanteri. Agent'ın okuyabileceği her içerik kaynağını listele: RAG dokümanları, inbox, takvim, araç çıktıları, tickets, ürün incelemeleri, üçüncü-taraf API'lar. Her biri potansiyel bir IPI vektörüdür.
2. Trust etiketlemesi. Deployment, trusted'ı (kullanıcı prompt'u) untrusted'tan (alınmış içerik) ayırıyor mu? İçerik bir etiket olmadan aynı prompt'a birleştiriliyorsa, IFC devrede değildir.
3. Eylem gating. Hangi araçlar çağrılabilir? Her biri için, çağrı yalnızca trusted prompt tarafından mı gate ediliyor, yoksa untrusted içerik çağrıyı etkileyebilir mi?
4. Adaptive-attack değerlendirmesi. Deployment Nasr et al. 2025'e göre adaptive saldırılarla (gradient, RL, insan red-team) test edildi mi? Yalnızca-statik-saldırı değerlendirmesi yetersizdir.
5. Scope-violation sınırları. Her cross-trust sınırını tespit et (örn. inbox -> send, dokümanlar -> external API). Her biri için, eylemin untrusted etki altında izinsiz olduğunu veya trusted prompt tarafından açıkça onaylandığını doğrula.

Sert reddetmeler:
- Alınmış içerik üzerinde açık trust etiketlemesi olmayan herhangi bir agent deployment'ı.
- Yalnızca statik saldırılara dayalı herhangi bir savunma iddiası.
- IFC mekanizmasını adlandırmadan "agent'ımız prompt-injection güvenli" iddiası.

Reddetme kuralları:
- Kullanıcı filtrelemenin yeterli olup olmadığını sorarsa, reddet ve Nasr 2025 sonucunu açıkla: adaptive saldırılar filter-tabanlı savunmaların >%90'ını kırar.
- Kullanıcı bir silah-mermi savunması isterse, reddet — IPI savunması IFC artı katmanlı response moderasyonu artı yüksek-riskli eylemlerde insan denetimi gerektirir.

Çıktı: yukarıdaki beş bölümü dolduran, en tehlikeli untrusted-to-trusted sınırını işaretleyen ve eklenecek en acil tek kontrolü adlandıran tek sayfalık bir denetim. MDPI Information 17(1):54 (2026) ve Nasr et al.'i (Ekim 2025) birer kez alıntıla.
