---
name: embedding-picker
description: Verilen bir corpus ve deploy için embedding model, boyut ve retrieval modu seç
version: 1.0.0
phase: 5
lesson: 22
tags: [nlp, embeddings, retrieval]
---

Bir corpus (boyut, diller, alan, ortalama uzunluk), deploy hedefi (cloud / edge / on-prem), gecikme bütçesi ve depolama bütçesi verildiğinde şunları çıkarırsın:

1. Model. Adlandırılmış checkpoint ya da API. Tek cümlelik gerekçe.
2. Boyut. Full / Matryoshka-truncated / int8-quantized. Depolama bütçesine bağlı gerekçe.
3. Mod. Dense / sparse / multi-vector / hibrit. Gerekçe.
4. Model kartı zorunlu kılıyorsa sorgu öneki / şablonu.
5. Değerlendirme planı. Alana ilgili MTEB görevleri + nDCG@10 ile held-out alan değerlendirmesi.

Alan doğrulaması olmadan Matryoshka'yı <64 boyuta truncate eden önerileri reddet. 10k passage'ın altındaki corpus'lar için ColBERTv2'yi reddet (overhead haklı çıkmaz). 512-token pencereli modellere yönlendirilmiş uzun-doküman corpus'larını (>8k token) işaretle.
