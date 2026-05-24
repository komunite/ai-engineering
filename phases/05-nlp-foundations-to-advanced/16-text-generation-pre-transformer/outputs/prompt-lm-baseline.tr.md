---
name: lm-baseline
description: Bir neural LM eğitmeden önce tekrarlanabilir n-gram dil modeli baseline'ı inşa et
phase: 5
lesson: 16
---

Bir corpus ve hedef kullanım (sonraki-kelime tahmini, yeniden skorlama, perplexity baseline'ı) verildiğinde şunları çıkar:

1. N-gram derecesi. Genel İngilizce için trigram, corpus büyükse 4-gram, konuşma yeniden skorlama için 5-gram.
2. Smoothing. Varsayılan Modified Kneser-Ney; Laplace sadece öğretim için.
3. Library. Üretim için `kenlm`, öğretim için `nltk.lm`, matematiği öğrenmek için sıfırdan kendin yaz.
4. Değerlendirme. Train ve test setleri arasında tutarlı tokenization ile held-out perplexity.

Karşılaştırılan sistemler arasında farklı tokenization ile hesaplanmış perplexity raporlamayı reddet — perplexity sayıları sadece aynı tokenization altında karşılaştırılabilir. Test setindeki OOV oranını işaretle; eğitim sırasında özel `<UNK>` token'ı rezerve etmediysen KN, OOV'yi kötü yönetir.
