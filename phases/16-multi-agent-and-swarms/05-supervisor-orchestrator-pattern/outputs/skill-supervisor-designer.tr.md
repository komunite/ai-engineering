---
name: supervisor-designer
description: Belirli bir araştırma tarzı sorgu için supervisor/orchestrator-worker sistemi tasarla; lead prompt, worker rolleri, decomposition kuralları ve sentez şablonunu belirt.
version: 1.0.0
phase: 16
lesson: 05
tags: [multi-agent, supervisor, orchestrator, anthropic-research, langgraph]
---

Paralel subagent araştırmasından yararlanacak bir kullanıcı sorgusu verildiğinde, herhangi bir framework'e (LangGraph, OpenAI Agents SDK, CrewAI Hierarchical) bağlanmaya hazır bir supervisor-pattern tasarımı üret.

Üret:

1. **Karmaşıklık tahmini.** Bu sorgu basit (1 agent, 3-10 tool çağrısı), orta (2-4 worker) ya da karmaşık mı (5+ worker)? Anthropic'in scale-effort heuristic'ini kullanarak tek cümleyle gerekçelendir.
2. **Lead system prompt.** İçermeli: (a) decomposition talimatları, (b) sentez talimatları, (c) lead'in asla ham kaynak içeriğini okumadığı, yalnızca worker özetlerini okuduğu açık kural.
3. **Worker system prompt'ları.** Her rol için bir tane; her biri kendi dar kapsamını ve lead'in beklediği çıktı formatını adlandırır.
4. **Alt-soru decomposition kuralları.** Lead sorguyu nasıl bölüyor? Önce-geniş-sonra-daraltma mı, doğrudan decomposition mu? Bir alt-soruyu ne diskalifiye eder (başka biriyle örtüşme, fazla geniş)?
5. **Sentez şablonu.** Açık çatışma yönetim kuralı: iki worker çelişkili olgular dönerse, sentez sessizce birini seçmek yerine anlaşmazlığı yüzeye çıkarmalı.
6. **Model eşleştirmesi.** Lead için hangi model (reasoning katmanı), worker'lar için hangisi (daha hızlı/daha ucuz katman). Ödünü açıkla.
7. **Gözlemlenebilirlik gereksinimleri.** Minimum trace noktaları: plan, her worker başlangıç/bitişi, sentez girdisi, sentez çıktısı.

Sert ret durumları:

- Lead'in tool kullandığı herhangi bir tasarım. Lead yalnızca planlar ve sentezler.
- Scope kaymasına izin veren worker prompt'ları (ör. sınır olmadan "X ile ilgili her şeyi araştır").
- Çatışmaları gizleyen sentez şablonları.

Reddetme kuralları:

- Sorgu basitse (toplam tahmini 10 tool çağrısı altında), tasarımı reddet ve tek-agent öner. Anthropic'in 15× token maliyet bulgusunu alıntıla.
- Sorgu sıralı ise (2. adım 1. adımın çıktısına ihtiyaç duyuyor), reddet ve bir pipeline/chain pattern öner.
- Kullanıcı determinism ve denetim için optimize ediyorsa, supervisor'u reddet ve LangGraph statik graph öner.

Çıktı: bir sayfalık tasarım brief'i. Karmaşıklık tahmini ve pattern-uygunluk kararıyla başla ("supervisor uyar"). Sistem sürekli çalışacaksa rainbow-deployment hatırlatmasıyla kapat.
