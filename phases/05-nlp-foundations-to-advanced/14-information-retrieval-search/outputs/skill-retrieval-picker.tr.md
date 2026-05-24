---
name: retrieval-picker
description: Verilen bir corpus ve sorgu deseni için retrieval stack seç
version: 1.0.0
phase: 5
lesson: 14
tags: [nlp, retrieval, rag, search]
---

Gereksinimler (corpus boyutu, sorgu deseni, gecikme bütçesi, kalite barı, altyapı kısıtları) verildiğinde şunları çıkarırsın:

1. Stack. Sadece BM25, sadece dense, hibrit (BM25 + dense + RRF), hibrit + cross-encoder rerank ya da üçlü (BM25 + dense + learned-sparse).
2. Dense encoder. Spesifik modeli adlandır (`all-MiniLM-L6-v2`, `bge-large-en-v1.5`, `e5-large-v2`, `paraphrase-multilingual-MiniLM-L12-v2`). Dile, alana, context uzunluğuna eşle.
3. Reranker. Kullanılıyorsa cross-encoder modelini adlandır (`cross-encoder/ms-marco-MiniLM-L-6-v2`, `BAAI/bge-reranker-large`). Top-30'da ~30-100ms ek gecikme olarak işaretle.
4. Değerlendirme planı. Recall@10 birincil retriever metriğidir. Çoklu-cevap için MRR. Önce baseline, sonra ona göre ölçülen artımsal iyileştirmeler.

Adlandırılmış entity, hata kodu ya da ürün SKU'su içeren corpus'lar için kullanıcı dense'in tam eşleşmeleri yönetebildiğine dair kanıt sunmadıkça sadece-dense önermeyi reddet. Nihai top-5'in kullanıcının cevabını belirlediği yüksek-risk retrieval (hukuk, tıp) için reranking'i atlamayı reddet.
