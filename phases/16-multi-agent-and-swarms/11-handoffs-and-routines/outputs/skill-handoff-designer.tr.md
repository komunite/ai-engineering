---
name: handoff-designer
description: Swarm/Agents-SDK tarzı bir sistem için handoff topolojisi tasarla: hangi agent'lar var, hangi handoff'ları çağırabilir, hangi context transfer edilir.
version: 1.0.0
phase: 16
lesson: 11
tags: [multi-agent, swarm, handoff, openai-agents-sdk]
---

Kullanıcıya yönelik bir görev (genellikle triage ya da skill tabanlı routing) verildiğinde, OpenAI Swarm ya da OpenAI Agents SDK'sına eşlenmeye hazır bir handoff topolojisi üret.

Üret:

1. **Agent roster'ı.** Her agent: ad, tek cümlelik amaç, tool'lar ve hangi diğer agent'lara handoff yapabileceği.
2. **Handoff fonksiyonları.** Agent başına tool imzaları. Her handoff fonksiyonu bir hedef Agent döner.
3. **Context transfer politikası.** Her handoff edge'inde: tam geçmiş, son N mesaj ya da özetlenmiş snapshot. Gerekçelendir.
4. **Guardrail'lar.** Agent başına girdi doğrulaması (hangi prompt'ların hassas uzmanlara handoff tetiklemesine izin verildiği), gerektiğinde handoff'ta authentication.
5. **Loop tespiti.** Ping-pong tespit kuralı (ör. "A, B'ye handoff yaptı; B, A'ya geri handoff yaptı" art arda birden fazla kez gerçekleşti).
6. **Fallback davranışı.** Handoff hedefi eksikse (kaldırılmış agent, auth başarısızlığı), oturumu hangi agent ele alır.
7. **Session / memory planı.** Agents SDK session'larını mı, caller-managed memory'yi mi yoksa hiç memory kullanmamayı mı tercih etmeli.

Sert ret durumları:

- Loop tespiti olmayan herhangi bir handoff tasarımı.
- Farklı tool izinleri olan uzmanlara tam geçmişi geçen handoff fonksiyonları (güvenlik riski).
- Swarm'ın stateless davranışını varsayan ama sonra çok-turlu memory gerektiren tasarımlar — onun yerine Agents SDK session'larını kullan.

Reddetme kuralları:

- Görev paralel yürütme gerektiriyorsa, Swarm'ı reddet ve onun yerine supervisor (Ders 05) öner.
- Görev deterministik denetim/replay gerektiriyorsa, reddet ve LangGraph statik graph öner.
- Görev basit bir aşama DAG'ı ise (araştırma → kod → review), onun yerine CrewAI Sequential öner.

Çıktı: bir sayfalık handoff brief'i. Prompt injection'ın istenmeyen handoff'ları nasıl tetikleyebileceğine ve hangi guardrail'ların bunu engellediğine dair güvenlik notuyla kapat.
