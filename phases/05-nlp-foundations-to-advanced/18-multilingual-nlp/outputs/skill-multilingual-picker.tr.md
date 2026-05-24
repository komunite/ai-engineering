---
name: multilingual-picker
description: Çoklu dil NLP görevi için kaynak dil, hedef model ve değerlendirme planı seç
version: 1.0.0
phase: 5
lesson: 18
tags: [nlp, multilingual, cross-lingual]
---

Gereksinimler (hedef diller, görev tipi, dil başına mevcut etiketli veri) verildiğinde şunları çıkarırsın:

1. Fine-tuning için kaynak dil. Varsayılan İngilizce; hedef dilin tipolojik olarak yakın yüksek-kaynaklı bir dili varsa LANGRANK ya da qWALS kontrol et.
2. Temel model. XLM-R (sınıflandırma), mT5 (üretim), NLLB (çeviri), Aya-23 (generative LLM).
3. Few-shot bütçesi. Varsa 100-500 hedef-dil örneğiyle başla. Etiketleme mümkün değilse yalnızca zero-shot.
4. Değerlendirme planı. Dil başına doğruluk (toplam değil), diller arası tutarlılık, Latin olmayan yazı sistemlerinde entity-level F1.

Dil başına değerlendirme olmadan çoklu dil model ürüne çıkarmayı reddet — toplam metrikler uzun-kuyruk başarısızlıklarını gizler. Düşük tokenization kapsamlı yazı sistemlerini (Amharca, Tigrinyaca, birçok Afrika dili) byte-fallback'li model gerektirdiği şeklinde işaretle (SentencePiece byte_fallback=True ya da GPT-2 gibi byte-level tokenizer).
