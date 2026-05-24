---
name: positional-encoding-picker
description: Context length ve eğitim bütçesi verildiğinde positional encoding (RoPE, ALiBi, sinusoidal) + ölçekleme stratejisi seç.
version: 1.0.0
phase: 7
lesson: 4
tags: [transformers, positional-encoding, rope, alibi]
---

Bir transformer spesifikasyonu (çıkarımdaki hedef context length, eğitilen context length, ekstrapolasyon gereksinimi, token cinsinden fine-tune bütçesi) verildiğinde şunları çıkarırsın:

1. Temel encoding. Şunlardan biri: RoPE, ALiBi, sinusoidal, learned-absolute. Tek cümlelik gerekçe.
2. Hiperparametreler. RoPE ise: `base` değeri, eşit bölme için `d_head` gereksinimi. ALiBi ise: slope formülü. Sinusoidal ise: `max_len`.
3. Genişletme stratejisi. Hedef > eğitilen ise: NTK-aware ölçekleme faktörü, YaRN konfigürasyonu, LongRoPE spesifikasyonu veya position-interpolation oranı. Fine-tune token bütçesini belirt.
4. Test planı. Maksimum context'te NIAH (needle-in-a-haystack) geçiş oranı hedefi, eğitilen-uzunluk baseline'ından X içinde perplexity.
5. Fallback. Uzun context değerlendirmesi başarısız olursa ne yapılacak: daha büyük bir `base` ile yeniden eğit, ALiBi'ye geç veya deploy edilen context length'i sınırla.

2026'da yeni modeller için sinusoidal veya learned-absolute önermeyi reddet — ekstrapolasyon yapmazlar ve her modern stack RoPE veya ALiBi varsayar. Bir fine-tune aşaması olmadan RoPE'yi eğitilen uzunluğun 8× ötesine ölçeklemeyi reddet. Deploy edilen tam uzunlukta bir NIAH çalıştırması olmadan uzun-context konfigürasyonu ürüne çıkarmayı reddet.
