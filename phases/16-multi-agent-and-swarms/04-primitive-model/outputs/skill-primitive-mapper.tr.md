---
name: primitive-mapper
description: Herhangi bir çoklu-agent framework'ünü ya da codebase'ini dört primitive ekseninde (agent, handoff, paylaşımlı state, orchestrator) eşle.
version: 1.0.0
phase: 16
lesson: 04
tags: [multi-agent, primitives, framework-comparison, architecture]
---

Bir çoklu-agent framework'ü (ya da onu kullanan bir codebase) verildiğinde, dört-primitive eşlemesini üret; böylece okuyucu framework'ü tek paragrafta anlayabilsin.

Üret:

1. **Agent tanımı.** Bir agent nasıl inşa ediliyor? Hangi parametrelerle? Hangi state'i taşıyor? Tam sınıfı ya da factory'yi adlandır.
2. **Handoff mekanizması.** Üç handoff pattern'ından hangisini kullanıyor — function return, graph edge ya da speaker selection? Hibritse, hangisi birincil? Bir handoff'u tetikleyen minimum kodu göster.
3. **Paylaşımlı state modeli.** Tam mesaj havuzu mu yoksa yansıtılmış görünüm mü? In-memory mi yoksa kalıcı (checkpoint'li) mi? Eşzamanlı yazıcılar için thread-safe mi? Çakışmaları kim uzlaştırır?
4. **Orchestrator türü.** Statik, LLM-seçimli, handoff-güdümlü ya da queue-güdümlü? LLM-seçimliyse, varsayılan model hangisi? Statikse, graph cyclic mi yoksa DAG mi?
5. **Çapraz-eksen ödünler.** Her biri için bir cümle: determinism, ölçeklenebilirlik tavanı, hata ayıklanabilirlik, tipik hata modu.

Sert ret durumları:

- Bir soyutlamanın dört primitive'dan birine indirgenmediğini göstermeden "yeni" olduğunu iddia eden eşlemeler. İndirgenemiyorsa, beşinci bir primitive icat etmek yerine boşluğu kesin olarak adlandır.
- Yalnızca pazarlama dokümanlarını alıntılayan framework karşılaştırmaları. Her zaman framework'ün reposundan veya resmi cookbook'undan somut bir kod örneği alıntıla.
- "Framework X agent'lar için daha iyidir" tarzı, hangi primitive'i optimize ettiğini belirtmeyen ifadeler.

Reddetme kuralları:

- Framework kapalı kaynaksa ve halka açık dokümanlar agent-handoff-state-orchestrator yüzeyini açmıyorsa, içyapı olmadan eşlemenin mümkün olmadığını belirt.
- Kullanıcı bir codebase sunuyor ama framework sunmuyorsa (elle yapılmış agent'lar), özel implementasyonu eşle ve hangi primitive'in yetersiz tasarlandığını işaretle.
- Framework 2024 öncesiyse (orijinal AutoGen v0.2, Swarm öncesi) ve artık bakım yapılmıyorsa, halefinin eşlemeyi koruyup korumadığına dair tek satırlık bir not ekle.

Çıktı: bir sayfalık framework brief'i. Tek cümlelik özetle başla ("Framework X handoff'u graph edge olarak sabitler ve paylaşımlı state'i bir reducer üzerinden açar."), ardından yukarıdaki beş bölüm, sonra kapanış paragrafı: bu framework'ün primitive'larına en iyi hangi production projesi uyar.
