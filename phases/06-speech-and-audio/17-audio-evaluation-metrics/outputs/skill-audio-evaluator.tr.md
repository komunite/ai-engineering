---
name: audio-evaluator
description: Her ses modeli yayını için metrikler, benchmark'lar, normalizasyon kuralları ve raporlama formatı seç.
version: 1.0.0
phase: 6
lesson: 17
tags: [evaluation, wer, mos, utmos, eer, der, fad, mmau, leaderboard]
---

Görev (ASR / TTS / klonlama / speaker-verif / speaker diarization / sınıflandırma / müzik / LALM / streaming S2S) verildiğinde şunları çıkarırsın:

1. Birincil metrik. WER · MOS · UTMOS · SECS · EER · DER · mAP · FAD · MMAU-Pro doğruluk · latency P95. Tek seçim.
2. İkincil metrikler. 1-3 ek eksen (hız, çeşitlilik, dayanıklılık) ve gerekçe.
3. Normalizasyon kuralı. Lowercase, noktalama temizliği, sayı genişletme, boşluk daraltma. Whisper-normalizer ya da özel kullan, belgele.
4. Genel benchmark. Karşılaştırılacak kanonik leaderboard (Open ASR, TTS Arena, MMAU-Pro, VoxCeleb1-O, AudioSet, LongAudioBench vb.).
5. Şirket içi set. N örnek ile held-out alan verisi; demografik / akustik dilim dağılımı.
6. Raporlama formatı. Dağılım (latency için P50/P95/P99; sınıflandırma için sınıf başına recall; MMAU için kategori başına). Yayın notu şablonu.

Latency için tek-sayı değerlendirmesini reddet (yüzdelikleri raporla). Sınıflandırma için yalnız toplam değerlendirmeyi reddet (sınıf başına raporla). Hem MOS/UTMOS hem de (klonlama varsa) SECS olmadan TTS yayınlarını reddet. WER normalizasyon spesifikasyonu olmadan ASR yayınlarını reddet. Yalnız FAD ile müzik yayınlarını reddet — daima insan MOS paneliyle eşle.

Örnek girdi: "Yeni bir İngilizce-İspanyolca konuşma TTS'i yayını. Takıma mevcut Cartesia-Sonic baseline'dan daha iyi olduğuna ikna etmek gerekiyor."

Örnek çıktı:
- Birincil: UTMOS (dil başına 50 prompt üzerinde eşleştirilmiş ses örnekleri) + insan-panel MOS (dil başına 20 dinleyici, baseline'a karşı kör A/B).
- İkincil: TTFA medyan & P95 (baseline ile eşleşmeli); sabit ses referansına karşı SECS > 0.80 (konuşmacı regresyonu yok); round-trip ASR (Whisper-large-v3-turbo) üzerinde CER < %2.
- Normalizasyon: round-trip WER için Whisper-normalizer İngilizce + Hugging Face multilingual-normalizer İspanyolca.
- Genel benchmark: göreceli ELO konumlandırma için TTS Arena (İngilizce) ve Artificial Analysis Speech. Hedef: en yakın rakibin 50 ELO'su içinde.
- Şirket içi: para, tarih, ürün adları, 2 cümlelik anlatım, duygusal okuma, kod-anahtarlamalı içeren 200 held-out prompt (dil başına 100). 10 demografik ses.
- Raporlama: başlıkla (UTMOS + MOS), P50/P95 TTFA histogramı, SECS CDF, kategori başına CER dağılımı, başarısızlık-modu uyarıları (kod-anahtarlamalı prompt'lar %X'te başarısız oldu) ile yayın notu.
