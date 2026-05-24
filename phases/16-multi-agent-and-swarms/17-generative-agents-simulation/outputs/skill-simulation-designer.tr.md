---
name: simulation-designer
description: Belirli bir senaryo için generative-agent simülasyonu (Smallville tarzı) tasarla. Memory şemasını, reflection cadence'ini, plan ufkunu, mekansal/sosyal kısıtları ve değerlendirme metriklerini belirtir.
version: 1.0.0
phase: 16
lesson: 17
tags: [multi-agent, simulation, generative-agents, emergence, memory]
---

Bir agent popülasyonundan emergent davranış gerektiren bir senaryo verildiğinde (sosyal simülasyon, oyun NPC'leri, politika provası, piyasa dinamikleri), simülasyonu tasarla.

Üret:

1. **Popülasyon boyutu ve heterojenlik.** N agent; hangileri base model paylaşıyor vs farklı; prompt aileleri; rol dağılımı. Smallville bireyselleştirilmiş persona'larla 25 homojen agent kullandı; daha büyük popülasyonlar heterojenlikten yararlanır.
2. **Memory şeması.** Girdi başına alanlar: `(ts, kind, content, importance, embedding_ref, source_ids)`. Recency-decay sabiti; importance scoring prosedürü; relevance metriği (X embedding modeliyle cosine). Compaction için saklama politikası.
3. **Reflection cadence.** Trigger: işlenmemiş importance toplamı > eşik, ya da her N gözlem, ya da periyodik tick. Trigger başına reflection sayısı. Reflection prompt şablonu.
4. **Plan ufku.** Gün / saat / eylem seviyeleri. Hangileri zorunlu; hangileri isteğe bağlı. Revizyon trigger'ı: aktif planla çelişen importance > eşik olan yeni bir gözlem.
5. **Dünya modeli.** Mekansal grid, sosyal graph, kaynak kısıtları. Neyi bir gözlem oluşturur (line-of-sight, conversation, notification). Mimarinin ÖĞRENMEDİĞİ ve açıkça kodlanması gereken normatif kısıtlar (kapasite limitleri, kapanış saatleri, private alanlar).
6. **Tohum hedefler.** Hangi agent'lar hangi önceliklerle tohumlanmış. Rekabet edebilen örtüşen hedefler; bir arada var olması gereken rekabet etmeyen hedefler.
7. **Bütçe.** Agent başına tick başına LLM çağrısı (observe + retrieve + reflect + plan + act). Tick başına agent başına beklenen token'lar. T tick için toplam simülasyon maliyeti.
8. **Değerlendirme metriği.** İnandırıcılık (human-rater), hedef başarı oranı, sayılan koordinasyon olayları, başarısızlık sinyali olarak mekansal-norm ihlalleri.

Sert ret durumları:

- Açık mekansal / sosyal norm kodlaması olmayan tasarımlar. Mimari bunları ihlal edecektir (Park 2023'ten kapalı-mağaza, tek-banyo başarısızlıkları).
- Değiştirilebilir memory'li tasarımlar. Memory append-only olmalı; düzeltmeler yeni girdilerdir.
- Her tick'te reflection çalıştıran tasarımlar. Bütçe verimsizdir; reflection pahalıdır ve trigger'lar eşik tabanlı olmalıdır.
- Memory-compaction stratejisi olmadan büyük N'de (> 50) simülasyonlar. Retrieval maliyeti stream uzunluğuyla büyür.

Reddetme kuralları:

- Senaryo emergent *sosyal davranış* yerine emergent *görev yürütme* gerektiriyorsa, onun yerine supervisor / roller / primitives pattern'larını öner (Faz 16 · 05-08). Smallville sosyal simülasyon içindir.
- Bütçe toplamda tick başına < 100 LLM çağrısına izin veriyorsa, daha büyük popülasyonlar yerine yoğun etkileşimli N = 3-5 öner.
- Senaryo emergence'tan yararlanmıyorsa (sıkı senaryolu görev), tek-agent + tool'lar öner.

Çıktı: bir sayfalık tasarım brief'i. Tek cümlelik özetle başla ("Smallville tarzı simülasyon: 15 heterojen agent, importance toplamı > 120'de reflection, 3-seviyeli plan ufku, kapasite kısıtlı mekansal grid, inandırıcılık + koordinasyon olaylarıyla ölçülür."), ardından yukarıdaki sekiz bölüm. Beklenen emergent davranışlar ve izlenecek ilk üç hata moduyla bitir.
