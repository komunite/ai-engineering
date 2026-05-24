---
name: skill-bpe-vs-wordpiece
description: Verilen bir corpus ve deploy hedefi için tokenizer algoritması, vocab boyutu, library seç
version: 1.0.0
phase: 5
lesson: 19
tags: [nlp, tokenization]
---

Bir corpus (boyut, diller, alan) ve deploy hedefi (sıfırdan eğitim / fine-tuning / API-uyumlu çıkarım) verildiğinde şunları çıkarırsın:

1. Algoritma. BPE, Unigram ya da WordPiece. Tek cümlelik gerekçe.
2. Library. SentencePiece, HF Tokenizers ya da tiktoken. Gerekçe.
3. Vocab boyutu. En yakın 1k'ya yuvarlanmış. Model boyutu ve dil kapsaması ile bağlantılı gerekçe.
4. Kapsama ayarları. `character_coverage`, `byte_fallback`, özel-token listesi.
5. Doğrulama planı. Held-out set üzerinde kelime başına ortalama token, OOV oranı, sıkıştırma oranı, round-trip decode eşitliği.

Nadir yazı sistemli içerikli corpus'larda character-coverage <0.995 olan tokenizer eğitmeyi reddet. CI'da donmuş `tokenizer.json` hash kontrolü olmadan vocab ürüne çıkarmayı reddet. 16k vocab'in altındaki monolingual tokenizer'ları muhtemelen yetersiz olarak işaretle.
