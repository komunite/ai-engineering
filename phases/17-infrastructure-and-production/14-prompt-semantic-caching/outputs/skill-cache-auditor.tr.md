---
name: cache-auditor
description: Bir LLM prompt template'ini ve trafik pattern'ini cache'lenebilirlik için denetle. Prompt yeniden yapılandırma, TTL seçimi, paralelleştirme düzeltmesi ve semantic-cache eşiği öner.
version: 1.0.0
phase: 17
lesson: 14
tags: [caching, prompt-cache, semantic-cache, anthropic, openai, parallelization, ttl]
---

Bir prompt template'i, trafik pattern'i (geliş oranı, paralel faktör) ve sağlayıcı (Anthropic, OpenAI, Gemini, self-hosted vLLM) verildiğinde, bir cache denetimi üret.

Üret:

1. Prefix yapısı. Template'i statik (cache'lenebilir) ve dinamik (cache'lenemez) bölümlere ayır. Şu anda prefix'te bulunan herhangi bir dinamik içeriği işaretle ve yeniden yazımı öner.
2. TTL seçimi. Anthropic 5-dakika (1.25x yazma) vs 1-saat (2x yazma). Geliş oranına göre seç — prefix tutarlı şekilde saat içinde yeniden kullanılıyorsa 1-saat kazanır.
3. Paralelleştirme denetimi. Paylaşılan prefix'li paralel istekleri say. N > 2 ve paralelse, serialize-first-then-fanout pattern'i iste. Beklenen fatura azalmasını niceliklendir.
4. Semantic cache seçimi. L1'in değer olup olmadığına karar ver. Açık uçlu sohbet: belki değil (düşük hit). Yapılandırılmış SSS / destek: evet. Cosine eşiği ayarla, 0.95'ten başla; yalnızca yanıt-kalitesi değerlendirmeleriyle aşağı tune et.
5. Beklenen tasarruflar. Mevcut trafik ve projeksiyonlanmış hit oranları verildiğinde, no-cache baseline'a karşı aylık $ delta'sını hesapla.
6. Gözlemlenebilir. Regresyonları yakalayan bir dashboard metriği: son yuvarlanan saatte L2 cache hit oranı; >%20 düşerse alarm.

Hard rejects:
- Beklenen hit oranı ve yazma primini hesaplamadan "%50 tasarruf" iddia etmek. Reddet — katman başına hesapla.
- Basit bir yeniden yazım çıkarabiliyorken dinamik içeriği prefix'te bırakmak. Onaylamayı reddet.
- Paylaşılan prefix'li paralel isteklerin serialize-first pattern'i olmadan ateşlenmesi. Reddet — 5-10x fatura şişmesini belirt.

Reddetme kuralları:
- Prompt token bazında >%80 dinamik içerikse, cache tasarruflarını vaat etmeyi reddet. En iyi ihtimalle semantic caching öner.
- Semantic cache eşiği yanıt-kalitesi değerlendirmesi olmadan 0.85 altına düşürülürse, reddet — hallucination cache riski.
- Sağlayıcı açık cache_control'ü desteklemiyorsa (Anthropic dışı, Gemini-v1 dışı) ve yalnızca otomatik-caching varsa, hit oranının fırsatçı olduğunu, garantili olmadığını not et.

Çıktı: prefix yeniden yazımı, TTL, paralelleştirme pattern'i, L1 eşiği, beklenen tasarruflar, gözlemlenebilir listeleyen tek sayfalık denetim. Çeyreklik gözden geçirme önerisiyle bitir: herhangi bir template değişikliğinden sonra prompt'ları yeniden denetle.
