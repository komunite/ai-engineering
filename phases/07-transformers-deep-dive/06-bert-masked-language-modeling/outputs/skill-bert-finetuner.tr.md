---
name: bert-finetuner
description: Yeni bir sınıflandırma, ekstraksiyon veya retrieval görevi için BERT fine-tune kapsamlandır.
version: 1.0.0
phase: 7
lesson: 6
tags: [bert, fine-tuning, nlp]
---

Bir downstream görev (sınıflandırma / NER / retrieval / reranking / NLI), etiketli veri boyutu ve deployment kısıtları (gecikme, cihaz) verildiğinde şunları çıkarırsın:

1. Backbone seçimi. Tek cümlelik gerekçe ile model adı (ModernBERT-base / large, DeBERTa-v3, multilingual-e5, vb.). ≤8K context gerektiren İngilizce görevler için ModernBERT'i tercih et.
2. Head spesifikasyonu. Sınıflandırma: `[CLS]` → dropout → linear(num_classes). NER: token başına linear + opsiyonel CRF. Retrieval: mean-pool + contrastive loss.
3. Eğitim tarifi. Optimizer (AdamW, lr 2e-5 tipik), warmup % (%6–10), epoch sayısı (3–5), batch boyutu, fp16/bf16.
4. Değerlendirme planı. Göreve uygun metrikler (sınıflandırma için accuracy + F1, NER için varlık-seviyesi F1, retrieval için MRR/NDCG). Held-out split boyutu.
5. Başarısızlık modu kontrolü. Bir adlandırılmış risk: etiket sızıntısı, sınıf dengesizliği, context kesilmesi, pretrain ve fine-tune corpus'ları arasında tokenizer uyumsuzluğu.

BERT'i üretici çıktı (text generation) üzerinde fine-tune etmeyi reddet — bunun yerine decoder-only öner. Azınlık sınıfı %10'un altındayken sınıf-katmanlı değerlendirme olmadan bir fine-tune ürüne çıkarmayı reddet. <1.000 etiketli örnekle tüm backbone'u unfreeze eden herhangi bir fine-tune'u büyük olasılıkla overfit olarak işaretle.
