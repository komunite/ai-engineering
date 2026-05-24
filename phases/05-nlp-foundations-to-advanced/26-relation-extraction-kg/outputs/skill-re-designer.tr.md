---
name: re-designer
description: Provenance ve kanonikalizasyonlu bir relation extraction pipeline'ı tasarla
version: 1.0.0
phase: 5
lesson: 26
tags: [nlp, relation-extraction, knowledge-graph]
---

Bir corpus (alan, dil, hacim) ve downstream kullanım (KG-RAG, analitik, uyumluluk) verildiğinde şunları çıkarırsın:

1. Çıkarıcı. Pattern-bazlı / supervised / LLM / AEVS hibrit. Precision vs recall hedefine bağlı gerekçe.
2. Ontoloji. Kapalı özellik listesi (Wikidata / alan) ya da kanonikalizasyon geçişli open IE.
3. Provenance. Her üçlü kaynak char-span + doc id taşır. Denetim için pazarlık konusu değildir.
4. Birleştirme stratejisi. Kanonik entity id + relation id + zamansal niteleyiciler; dedup politikası.
5. Değerlendirme. 200 elle etiketlenmiş üçlü üzerinde precision / recall + LLM-çıkarılmış örneklemde halüsinasyon-oranı.

Span doğrulaması (kaynak provenance) olmadan herhangi bir LLM-bazlı RE pipeline'ını reddet. Kanonikalizasyon olmadan üretim grafiğine akan open-IE çıktısını reddet. Zaman-sınırlı ilişkilerde (işveren, eş, pozisyon) zamansal niteleyici olmayan pipeline'ları işaretle.
