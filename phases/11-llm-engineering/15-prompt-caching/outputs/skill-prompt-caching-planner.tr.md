---
name: prompt-caching-planner
description: Cache-dostu bir prompt yerleşimi tasarla ve doğru sağlayıcı caching modunu seç.
version: 1.0.0
phase: 11
lesson: 15
tags: [llm-engineering, caching, cost]
---

Bir prompt (system + tool'lar + few-shot + retrieval + geçmiş + user) ve bir kullanım profili (saatte istek, gerekli TTL, sağlayıcı) verildiğinde, şunları çıkar:

1. Yerleşim. Tek bir cache breakpoint işaretli olacak şekilde yeniden sıralanmış bölümler; hangi bölümlerin stabil, hangilerinin volatile olduğunu açıkla.
2. Sağlayıcı modu. Anthropic cache_control, OpenAI otomatik veya Gemini CachedContent. TTL ve yeniden kullanım pattern'inden gerekçelendir.
3. Başabaş. TTL içinde yazma başına beklenen okuma sayısı; matematikle no-cache'e karşı net maliyet.
4. Doğrulama planı. İkinci aynı istekte cache_read_input_tokens > 0 olduğuna dair CI assertion; cache'lenmiş vs cache'siz token'lara göre bölünmüş dashboard.
5. Failure mode'lar. Bu kurulumda cache'in miss olmasının en olası üç nedenini (dinamik timestamp, tool reorder, yakın-duplikat metin) listele ve her birini nasıl önleyeceğini.

Breakpoint'in üzerine dinamik bir alan yerleştiren bir cache planını ship etmeyi reddet. 2x yazma primini geri ödeyen bir yeniden kullanım sayısı olmadan 1h TTL'yi etkinleştirmeyi reddet.
