---
name: prompt-tokenizer-builder
description: LLM projeleri için üretim kalitesinde tokenizer oluştur ve hata ayıkla
version: 1.0.0
phase: 10
lesson: 2
tags: [tokenizer, bpe, byte-level, special-tokens, chat-template, multilingual]
---

# Üretim Tokenizer Oluşturucu

Bir LLM projesi için tokenizer oluştururken ya da hata ayıklarken bu çerçeveyi izle.

## Pipeline Kontrol Listesi

Her üretim tokenizer'ının bu beş aşamaya ihtiyacı vardır. Bir tanesi eksikse, üretimde uç durumlara çarparsın.

1. **Normalize** -- NFKC Unicode normalizasyonu uygula. Bu, ligature'ları çökeltir ("fi" -> "fi"), fullwidth karakterleri normalize eder ve whitespace'i standartlaştırır. Bunu atlarsan aynı kelime nasıl yazıldığına göre farklı token ID'leri alır.

2. **Pre-Tokenize** -- BPE öncesi metni parçalara böl. İngilizce odaklı modeller için GPT-2'nin regex desenini kullan. Çok dilli modeller için SentencePiece'in raw-byte yaklaşımını kullan. Bu seçim, BPE'nin kelime sınırları arasında birleşme yapıp yapamayacağını belirler.

3. **BPE Merge** -- Her chunk içindeki byte dizilerine öğrenilmiş merge tablosunu uygula. Merge tablosu, tokenizer'ın öğrenilmiş bilgisinin TA KENDİSİDİR. Geri kalan her şey tesisattır.

4. **Special Token Injection** -- BPE çalışmadan önce özel token'ları tam olarak eşle. [BOS], [EOS], [PAD], chat template işaretçileri sabit ID alır. Asla merge'lere katılmazlar.

5. **ID Mapping** -- Token string'lerini integer'lara dönüştür. Model sadece integer görür.

## Tokenizer Sorunlarında Hata Ayıklama

**Belirti: model chat girdisinde çöp üretiyor**
- Chat template'ini kontrol et. Her modelin farklı formatı vardır. Llama 3 `<|start_header_id|>` işaretçileri kullanır. ChatGPT `<|im_start|>` işaretçileri kullanır. Yanlış template, girdiyi eğitim dağılımı dışına çıkarır.

**Belirti: İngilizce dışı metin çok fazla token kullanıyor**
- Fertility'i kontrol et (kelime başına token). 2.0 üzeri, tokenizer'ın o dilde context window'u israf ettiği anlamına gelir. Çözümler: daha çok çok dilli veriyle yeniden eğit, vocabulary boyutunu artır veya Unigram ile SentencePiece kullan.

**Belirti: sayılar ve aritmetik başarısız**
- Rakamların nasıl tokenize edildiğini kontrol et. "1234" tek token olarak demek model digit-level işlemler yapamaz demektir. Pre-tokenization sırasında rakamları tek tek ayır.

**Belirti: kod token'ları verimsiz**
- Indentation'ın nasıl işlendiğini kontrol et. GPT-2'nin tokenizer'ı boşluklarda token israfı yapar. Codex ve StarCoder özel indentation token'ları kullanır (4 boşluk = 1 token).

## Vocabulary Boyutu Kararı

- 32K token: tek dilli, küçük model, sınırlı compute. Embedding katmanı 32K * d_model parametre.
- 50K-64K: çok dilli veya kod yoğun. Çoğu proje için iyi denge.
- 100K+ (GPT-4, Llama 3): yalnızca büyük eğitim verisiyle. Daha kısa diziler ama 100K * d_model embedding parametresi.

4096 boyutlu bir model için: 32K vocab = 131M embedding parametre. 128K vocab = 524M embedding parametre. Bu, sadece embedding katmanında 400M parametre demek.

## Hız Gereksinimleri

- Eğitim verisi tokenization: Rust tabanlı kütüphaneler kullan (tiktoken, HuggingFace tokenizers). Saf Python 10-100x daha yavaştır.
- Çıkarım tokenization: latency daha az önemli (tek dizi) ama yine de derlenmiş implementasyonları kullan.
- Benchmark: 1GB metni tokenize et ve duvar saati süresini ölç. 60 saniyeden uzun sürerse Rust backend'e geç.

## Chat Template Doğrulaması

Herhangi bir chat modelini deploy etmeden önce template'i doğrula:

1. Bilinen bir konuşmayı tokenizer ile encode et
2. Geri text'e decode et
3. Modelin dokümantasyonundaki beklenen formatla karakter karakter karşılaştır
4. Şuna dikkat et: header token'larından sonra newline'lar, içerikten önce boşluklar, end-of-turn işaretçileri
5. Uç durumları test et: boş sistem mesajı, çok uzun kullanıcı mesajı, birden fazla assistant turn

Chat template'i yanlış yapmak, bozulan chat model performansının en yaygın kaynağıdır.
