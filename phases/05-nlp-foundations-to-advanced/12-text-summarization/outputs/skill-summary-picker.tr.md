---
name: summary-picker
description: Extractive ya da abstractive seç, library'yi isimlendir, factuality kontrolü ekle
version: 1.0.0
phase: 5
lesson: 12
tags: [nlp, summarization]
---

Bir görev (doküman tipi, uyumluluk gereksinimi, uzunluk, hesaplama bütçesi) verildiğinde şunları çıkarırsın:

1. Yaklaşım. Extractive ya da abstractive. Tek cümleyle nedenini açıkla.
2. Başlangıç modeli / library. Adlandır. `sumy.TextRankSummarizer`, `facebook/bart-large-cnn`, `google/pegasus-pubmed` ya da bir LLM prompt'u.
3. Değerlendirme planı. ROUGE-1, ROUGE-2, ROUGE-L (stemming ile `rouge-score` kullan). Abstractive ise ayrıca factuality kontrolü.
4. Probelanacak bir failure mode. Entity swap, abstractive haber özetlemesinde en yaygın olanıdır; kaynaktaki entity'lerin özette geçmediği örnekleri işaretle.

Factuality gate olmadan tıbbi, hukuki, finansal ya da regüle içerik için abstractive özetlemeyi reddet. Modelin context window'unu aşan girdiyi sadece truncation değil parçalı map-reduce özetleme gerektirdiği şeklinde işaretle.
