---
name: skill-tokenizer
description: LLM projeleri için tokenizer seçimi ve oluşturulması
version: 1.0.0
phase: 10
lesson: 1
tags: [tokenizer, bpe, wordpiece, sentencepiece, llm, nlp]
---

# Tokenizer Seçimi ve Uygulanması

Bir LLM projesine başlarken, tokenizer seçimi için bu karar çerçevesini uygula.

## Her tokenizer ne zaman kullanılır

**Byte-level BPE (tiktoken):** GPT ailesi modeller üzerine inşa ediyor ya da fine-tuning yapıyorsun. Herhangi bir giriş byte dizisinin garantili işlenmesi gerekiyor. Unknown token istemiyorsun.

**WordPiece (Hugging Face):** BERT ailesi modellerle classification, NER veya embedding görevleri yapıyorsun. Kelime sınırı sinyaline dayalı downstream görevler için "##" devam ön ekine ihtiyacın var.

**SentencePiece (BPE veya Unigram):** Sıfırdan eğitiyorsun. Dile bağımsız tokenization gerekiyor. Verin CJK dilleri, Tay dili veya boşluk-kelime sınırları olmayan diğer script'leri içeriyor. LLaMA, T5 ve çoğu çok dilli model bunu kullanır.

## Vocabulary boyutu yönergeleri

- 32K token: tek dilli modeller için iyi varsayılan, embedding katmanını küçük tutar
- 50K-64K token: çok dilli veya kod yoğun modeller için daha iyi
- 100K+ token: sadece büyük eğitim verin varken ve kısa diziler istediğinde

Daha büyük vocabulary daha kısa diziler (daha ucuz çıkarım) ama embedding matrisinde daha fazla parametre demek. 4096 boyutlu embedding ile 100K vocabulary için, sadece embedding katmanı 400M parametredir.

## Önemli pre-tokenization kuralları

1. Cross-word birleşmeleri önlemek için BPE öncesi boşluğa göre böl
2. Modelin aritmetiği öğrenmesini istiyorsan rakamları tek tek ayır
3. Tutarlı davranış için tokenization öncesi Unicode normalize et (NFC)
4. Kullanım senaryon için özel token'lar ekle: `<pad>`, `<eos>`, `<bos>`, `<unk>` ve göreve özgü işaretçiler

## Tokenizer davranışında kırmızı bayraklar

- Hedef dilin için 2.0 üzeri fertility: model context window'u israf eder
- Yaygın domain kelimelerinin 3+ token'a bölünmesi: domain verisiyle yeniden eğit
- Sayıların tutarsız tokenize edilmesi: digit-splitting kurallarını kontrol et
- Tek kullanımlık çok sayıda token içeren büyük vocabulary: vocabulary boyutunu azalt

## Özel tokenizer oluşturma - kontrol listesi

1. Temsili eğitim verisi topla (hedef domain'de en az 1GB metin)
2. Algoritma seç: genel kullanım için BPE, çok dilli için Unigram
3. Yukarıdaki yönergelere göre vocabulary boyutu ayarla
4. Pre-tokenization yapılandır: whitespace splitting, digit handling, punctuation
5. Özel token'lar ekle
6. Hugging Face tokenizers kütüphanesi ile eğit (Rust backend, hızlı)
7. Doğrula: tüm hedef dillerde tutulan metin üzerinde fertility kontrol et
8. Uç durumları test et: boş string, çok uzun girdi, binary veri, emoji, RTL metin
9. Tokenizer'ı model checkpoint'leriyle birlikte kaydet ve sürümle
