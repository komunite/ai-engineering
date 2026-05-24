---
name: entity-linker
description: Entity linking pipeline'ı tasarla — KB, candidate generator, disambiguator, değerlendirme
version: 1.0.0
phase: 5
lesson: 25
tags: [nlp, entity-linking, knowledge-graph]
---

Bir kullanım senaryosu (alan KB'si, dil, hacim, gecikme bütçesi) verildiğinde şunları çıkarırsın:

1. Knowledge base. Wikidata / Wikipedia / özel KB. Sürüm tarihi. Yenileme sıklığı.
2. Candidate generator. Alias-index, embedding ya da hibrit. K'da hedef mention recall.
3. Disambiguator. Prior + bağlam, embedding-bazlı, generative ya da LLM-prompted.
4. NIL stratejisi. En yüksek skor üzerinde eşik, sınıflandırıcı ya da açık NIL adayı.
5. Değerlendirme. Held-out set üzerinde Mention recall @ 30, top-1 doğruluğu, NIL-tespit F1.

Mention-recall baseline'ı olmadan herhangi bir EL pipeline'ını reddet (candidate gen'in doğru entity'yi getirdiğini bilmeden disambiguator'ı değerlendiremezsin). Geçerli KB id'lerine kısıtlı çıktı olmadan LLM-prompted EL kullanan pipeline'ları reddet. Alan fine-tuning'i olmadan azınlık entity'lerini (örn. isim çakışmaları) etkileyen popülerlik biaslı sistemleri işaretle.
