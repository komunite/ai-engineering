---
name: skill-embeddings-picker
description: Yeni bir dil modeli ya da metin pipeline'ı için tokenization yaklaşımı seç
version: 1.0.0
phase: 5
lesson: 04
tags: [nlp, tokenization, embeddings]
---

Bir görev ve veri kümesi tanımı verildiğinde şunları çıkarırsın:

1. Tokenization stratejisi (word-level, BPE, WordPiece, SentencePiece, byte-level BPE). Tek cümlelik gerekçe.
2. Vocabulary boyut hedefi. Sadece İngilizce LM: 32k. Çoklu dil: 64k-100k. Kod: 50k-100k.
3. Library çağrısı ve tam eğitim komutu. Library'yi isimlendir (Hugging Face `tokenizers`, `sentencepiece`). Argümanları tırnakla göster.
4. Bir tekrarlanabilirlik tuzağı. Tokenizer-model uyumsuzluğu, üretimdeki en sık sessiz bug'dır. Hangi tokenizer'ın hangi pretrained checkpoint ile eşleştiğini isimlendir ve değiştirmeye karşı uyar.

Kullanıcı pretrained bir LLM'i fine-tune ediyorsa özel tokenizer eğitmeyi önermeyi reddet (fine-tune pretrained tokenizer kullanmalı). Üretim çıkarım yolunda word-level tokenization önermeyi reddet. İngilizce olmayan ya da çoklu yazı sistemli corpus'ları byte fallback'li SentencePiece gerektirdiği şeklinde işaretle.
