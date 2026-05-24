---
name: codec-picker
description: Verilen bir üretken ya da sıkıştırma görevi için nöral ses codec'i (EnCodec / DAC / SNAC / Mimi) seç.
version: 1.0.0
phase: 6
lesson: 13
tags: [codec, encodec, dac, snac, mimi, rvq, semantic-tokens]
---

Görev (üretken LM, sıkıştırma, tam-dupleks diyalog, müzik düzenleme, kalite hedefi) verildiğinde şunları çıkarırsın:

1. Codec. EnCodec-24k · EnCodec-48k · DAC-44.1k · SNAC-24k · Mimi · (geri dönüş: nöral olmayan sıkıştırma için Opus). Tek cümlelik gerekçe.
2. Frame rate + codebook'lar. Bitrate bütçesi, codebook sayısı (genellikle 4-12), hedef klip süresi için sequence uzunluğu.
3. Tokenizasyon şeması. Düz vs hiyerarşik (SNAC) vs semantik+akustik (Mimi). LM token'ları nasıl tüketir.
4. Decoder. Codec içi decoder · harici vocoder (HiFi-GAN) · yalnızca LM (vocoder yok, doğrudan codec token'ları tahmin et). Nedenini açıkla.
5. Eğitim sonuçları. Encoder/decoder eğitmek gerekiyor mu? Alan sesinde fine-tune (yalnız konuşma → alan-özgü müzik)? Hazır olarak donmuş mu?

Sıkı latency bütçesinde AR-LM iş yükleri için DAC'i reddet — 86 Hz frame rate × 8 codebook = 10 sn başına 5.504 token, hızlı üretim için çok uzun. Müzik için Mimi'yi reddet — konuşma-ayarlı. Anlamsal-koşullu üretim için EnCodec'i reddet — semantik codebook yok, metinden bulanık konuşma.

Örnek girdi: "Metinden konuşmaya TTS için AR LM kur. Hedef TTFA 200 ms. Yalnız İngilizce."

Örnek çıktı:
- Codec: Mimi. Semantik+akustik bölünmesi, hem hızlı hem de ses klonlamayı destekleyen metin → codebook 0 → codebook 1-7 faktörizasyonunu mümkün kılar.
- Frame rate + codebook'lar: 12.5 Hz · 8 codebook · 4.4 kbps. 10 sn = 1.000 token.
- Tokenizasyon: önce metin + konuşmacı referansından codebook 0'ı tahmin et; sonra codebook 0 + konuşmacı referansı verildiğinde codebook 1-7'yi tahmin et (depth-transformer örüntüsü).
- Decoder: Mimi'nin yerleşik decoder'ı, harici vocoder gerekmez.
- Eğitim: metinden-codec'e LM'i eğit; Mimi'yi dondur.
