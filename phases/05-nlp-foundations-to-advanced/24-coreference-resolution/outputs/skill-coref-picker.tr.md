---
name: coref-picker
description: Coreference yaklaşımı, değerlendirme planı ve entegrasyon stratejisi seç
version: 1.0.0
phase: 5
lesson: 24
tags: [nlp, coref, information-extraction]
---

Bir kullanım senaryosu (tek-doküman / çoklu-doküman, alan, dil) verildiğinde şunları çıkarırsın:

1. Yaklaşım. Kural tabanlı / neural span-bazlı / LLM-prompted / hibrit. Tek cümlelik gerekçe.
2. Model. Neural ise adlandırılmış checkpoint.
3. Entegrasyon. İşlem sırası: tokenize → NER → coref → downstream görev.
4. Değerlendirme. Held-out set üzerinde CoNLL F1 (MUC + B³ + CEAF-φ4 ortalaması) + 20 dokümanda manuel küme incelemesi.

Sliding-window birleştirmesi olmadan 2.000 token üzeri dokümanlar için sadece-LLM coref'i reddet. Mention-seviyesi precision-recall raporu olmadan coref çalıştıran pipeline'ları reddet. Demografik olarak çeşitli metinde devreye alınan cinsiyet-heuristikli sistemleri işaretle.
