---
name: alm-picker
description: Bir ses-anlama görevi için audio-language modeli, benchmark alt kümesi, çıktı modalitesi (metin vs konuşma) ve guardrail'ler seç.
version: 1.0.0
phase: 6
lesson: 10
tags: [alm, lalm, qwen-omni, audio-flamingo, gemini-audio, mmau]
---

Görev (konuşma / ses / müzik / çoklu-ses / uzun-ses, çıktı modalitesi, latency, lisans) verildiğinde şunları çıkarırsın:

1. Model. Qwen2.5-Omni-7B · Qwen3-Omni · SALMONN · Audio Flamingo 3 · AF-Next · LTU · GAMA · Gemini 2.5 Pro (API) · GPT-4o Audio (API). Tek cümlelik gerekçe.
2. Doğrulanacak benchmark alt kümesi. MMAU-Pro speech / sound / music / multi-audio · LongAudioBench · AudioCaps · ClothoAQA. Kullanıcı göreviyle eşleşen ekseni seç.
3. Çıktı modalitesi. Yalnız metin · metin + konuşma (Qwen-Omni, GPT-4o Audio). Gerekirse ek bir konuşma decoder'ı için bütçele.
4. Guardrail'ler. Modelinizin çoklu-ses skoru < %30 (rastgeleye yakın) olduğunda çoklu-ses karşılaştırması gerektiren prompt'ları reddet. > 10 dakikalık girdiler için LALM öncesi diarize et.
5. Eskalasyon. Bu görev ne zaman özelleşmiş bir modele geri dönmeli — transkripsiyon için Whisper, sınıflandırma için BEATs, speaker diarization için pyannote. LALM her birinin en iyisi değildir.

Modelinizin MMAU-Pro çoklu-ses alt kümesinde > %40 skor aldığını doğrulamadan çoklu-ses karşılaştırma görevlerini ürüne çıkarmayı reddet. Yukarı akış speaker diarization olmadan uzun-ses (> 10 dk) reddet. Bağımsız yeniden doğrulama yapmadan satıcı raporlu sayıları kullanan her dağıtımı işaretle.

Örnek girdi: "Uyumluluk denetimi: 10 dakikalık banka çağrı kayıtlarını transkribe et + temsilcinin zorunlu açıklamayı okuyup okumadığını tespit et."

Örnek çıktı:
- Model: transkripsiyon için Whisper-large-v3-turbo + transkript üzerinden açıklama-kontrol QA için Gemini 2.5 Pro (API üzerinden). Ham ses üzerinde doğrudan LALM cazip ama uzun-ses LALM doğruluğu 10 dk sonrası düşüyor.
- Benchmark alt kümesi: MMAU-Pro speech alt kümesi (Gemini 2.5 Pro = %73.4) — konuşma-akıl yürütme eksenini kapsar. Ayrıca kendi 50 çağrılık altın setinizde spot kontrol.
- Çıktı modalitesi: yalnız metin. Denetim raporu için konuşma çıktısı gerekmez.
- Guardrail'ler: önce pyannote 3.1 ile diarize et; konuşmacı başına segmentleri ayrı gönder; çağrı başına güven skorunu logla.
- Eskalasyon: bir çağrı açıklama kontrolünü geçemezse, otonom işaretleme yerine insan inceleyiciye yönlendir.
