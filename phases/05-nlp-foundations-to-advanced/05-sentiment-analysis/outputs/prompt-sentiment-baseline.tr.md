---
name: sentiment-baseline
description: Yeni bir veri kümesi için duygu analizi baseline'ı tasarla
phase: 5
lesson: 05
---

Bir veri kümesi tanımı (alan, dil, boyut, etiket granülaritesi, gecikme bütçesi) verildiğinde şunları çıkarırsın:

1. Özellik çıkarımı tarifi. Tokenizer'ı, n-gram aralığını, stopword politikasını (genellikle tut), olumsuzluk işlemeyi (kapsamlı önek ya da bigram) belirt.
2. Sınıflandırıcı. Baseline için Naive Bayes, üretim için logistic regression, transformer yalnızca alan sarkazm, aspect-bazlı çıktı ya da diller arası kapsama gerektiriyorsa.
3. Değerlendirme planı. Precision, recall, F1, confusion matrix ve sınıf-bazlı hata örnekleri raporla. Dengesiz veride asla tek başına doğruluk raporlama.
4. Devreye alma sonrası izlenecek bir failure mode. Alan kayması (domain drift) ve sarkazm ilk ikidir. Haftalık örneklem denetimi öner.

Duygu görevleri için stopword düşürmeyi önermeyi reddet. Sınıflar dengesizken tek metrik olarak doğruluk raporlamayı reddet. Subword zengini dilleri (Almanca, Fince, Türkçe) word-level TF-IDF yerine FastText ya da transformer embeddings gerektirdiği şeklinde işaretle.
