---
name: attention-variant-picker
description: Context length, retrieval ihtiyaçları ve compute profili verildiğinde yeni bir model için full / sliding-window / sparse / differential attention topolojisi seç.
version: 1.0.0
phase: 7
lesson: 15
tags: [attention, transformer, long-context, inference, memory]
---

# Attention Varyant Seçici

Bir geliştiriciye yeni bir transformer için, veya daha uzun context'e genişlettiği mevcut bir transformer için bir attention topolojisi seçip gerekçelendirmesinde yardım et.

## Toplanacak girdiler

1. **Hedef context length** eğitimde ve çıkarımda (genellikle farklıdır — birçok model 16K'da eğitilir ve çıkarımda genişletilir).
2. **Retrieval talebi** 1–5 ölçeğinde: 1 = saf sohbet, 5 = needle-in-haystack / RAG / uzun repository context'li kod.
3. **Çıkarım bellek bütçesi** istek başına KV cache toleransı (katman başına token başına byte doğru birim).
4. **Eğitim maliyet toleransı** — sıfırdan SWA eğitmek ucuzdur; differential attention'ı önceden eğitilmiş bir modele sonradan eklemek pahalıdır.
5. **Donanım hedefi** — Hopper+ tam FlashAttention-3'e sahiptir, Ada FA2'ye sahiptir, daha eski GPU'lar mask-sınırlıdır.

## Karar kuralları

- **Context ≤ 16K ve retrieval ≤ 3**: FlashAttention ile full attention. Erken optimize etme.
- **Context 16–128K ve retrieval ≤ 3**: 5:1 oranında karışık SWA + global, window 1024 (Gemma 3 şekli). KV'yi çökerirken retrieval'i çalışılabilir tutar.
- **Context > 128K**: her 4–6 katmanda bir global katman ile full SWA, artı position interpolation / YaRN ölçeklemesi (Ders 04).
- **Retrieval = 5 ve eğitim bütçesi izin veriyor**: sadece üst 4 katmanda differential attention'ı düşün (KV ikiye katlamasının yarısı, sink-cancellation kazanımının çoğu).
- **Public API gönderiyorsun**: stabil desenleri tercih et (full, SWA, Gemma-3 mix). Kernel mühendislerin yoksa native-sparse / DIFF'i atla.
- **Base model'i değiştiremezsin**: SWA çıkarımda masking ile sonradan eklenebilir; differential ve sparse eklenemez.

## Her zaman işaretle

- 7B altındaki saf-SWA modeller akıl yürütme benchmark'larında ölçülebilir şekilde kaybeder. Önermemeyi tavsiye et.
- Window boyutu < 512 neredeyse hiç doğru değildir. Daha büyük git veya farklı bir topoloji kullan.
- Differential attention'ın makaledeki raporları küçük modeller üzerinedir (3–7B). Ölçek-büyütme kanıtı 2026 başı itibarıyla zayıftır.
- Her varyant RoPE / YaRN ölçeklemesi (Ders 04) ile etkileşir. Konum şemasını açıkça belirt.

## Çıktı formatı

Şunu döndür:

1. **Öneri** — tek bir adlandırılmış topoloji (örn. "Gemma-3 mix, W=1024, 5:1 SWA:global").
2. **Gerekçelendirme** — her girdiyi yukarıdaki karar kuralına eşle.
3. **KV cache tahmini** — hedef context'te, katman başına token başına byte ve batch 1'de GB.
4. **Migrasyon yolu** — base model zaten eğitilmişse, nasıl sonradan ekleneceği.
5. **Bilinen riskler** — hangi benchmark'lar / iş yükleri gerileyebilir.
