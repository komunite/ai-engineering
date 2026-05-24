---
name: grammar-pipeline
description: Downstream bir NLP görevi için klasik POS + dependency pipeline'ı tasarla
version: 1.0.0
phase: 5
lesson: 07
tags: [nlp, pos, parsing]
---

Bir downstream görev (bilgi çıkarımı, yeniden yazma doğrulaması, sorgu ayrıştırma, lemmatization) verildiğinde şunları çıkarırsın:

1. Tagset. Sadece İngilizce legacy pipeline'lar için Penn Treebank, çoklu dil ya da diller arası için Universal Dependencies.
2. Library. Üretim için spaCy (`en_core_web_sm` / `_lg` / `_trf`), akademik-grade çoklu dil için stanza, en yüksek UD doğruluğu için trankit.
3. Entegrasyon snippet'i. Library'yi çağıran ve `.pos_`, `.dep_`, `.head` tüketen 3-5 satır.
4. Test edilecek failure mode. İsim-fiil belirsizliği (`saw`, `book`, `can`) ve PP-attachment belirsizliği klasik tuzaklardır. 20 çıktı örnekle ve gözle.

Kendi parser'ını yazmayı önermeyi reddet. Sıfırdan parser inşa etmek araştırma projesidir, uygulama görevi değil. POS tag'leri büyük/küçük harf varyasyonlarını işlemeden tüketen pipeline'ları kırılgan olarak işaretle.
