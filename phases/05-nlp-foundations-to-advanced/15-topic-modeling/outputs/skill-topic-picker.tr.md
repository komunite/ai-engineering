---
name: topic-picker
description: Bir corpus için LDA ya da BERTopic seç. Library, ayarlar, değerlendirme belirt
version: 1.0.0
phase: 5
lesson: 15
tags: [nlp, topic-modeling]
---

Bir corpus tanımı (doküman sayısı, ortalama uzunluk, alan, dil, hesaplama bütçesi) verildiğinde şunları çıkarırsın:

1. Algoritma. LDA / NMF / BERTopic / Top2Vec / FASTopic. Tek cümlelik gerekçe.
2. Konfigürasyon. Topic sayısı (~sqrt(n_docs)'tan başla), `min_df` / `max_df` filtreleri, neural yaklaşımlar için embedding modeli.
3. Değerlendirme. `gensim.models.CoherenceModel` üzerinden topic coherence (c_v), topic çeşitliliği ve 20 örneklik insan okuması.
4. Probelanacak failure mode. LDA için stopword ve sık terimleri emen "junk topics". BERTopic için belirsiz dokümanları yutan -1 outlier kümesi.

Chunking stratejisi olmadan embedding modelinin context window'undan uzun dokümanlarda BERTopic'i reddet. Çok kısa metinlerde (tweet, 10 token altı yorumlar) LDA'yı reddet — coherence çöker. 5'in altı ya da 200'ün üstü n_topics seçimini gerçek veri için muhtemelen yanlış olarak işaretle.
