---
name: duplex-pipeline
description: Bir ses-ajanı iş yükü için tam-dupleks (Moshi) vs pipeline (VAD + STT + LLM + TTS) mimarisi seç.
version: 1.0.0
phase: 6
lesson: 15
tags: [moshi, hibiki, full-duplex, voice-agent, streaming]
---

İş yükü (latency hedefi, tool-calling ihtiyaçları, dil kapsamı, donanım bütçesi, bulut vs edge) verildiğinde şunları çıkarırsın:

1. Mimari. Tam-dupleks (Moshi / GPT-4o Realtime / Gemini Live) vs pipeline (LiveKit + STT + LLM + TTS, Ders 12). Tek cümlelik gerekçe.
2. Model. Moshi · Hibiki · Hibiki-Zero · Sesame CSM · GPT-4o Realtime · Gemini 2.5 Live · geleneksel pipeline. Gerekçe.
3. Ölçek. Oturum başına GPU maliyeti (Moshi bir slot tutar), maksimum eşzamanlı oturum, soğuk başlatma etkisi.
4. Tool-calling yolu. Gerekirse — hibrit pipeline (tool çağrıları için dupleks + harici LLM) ya da saf pipeline. Trade-off'u açıkla.
5. Dil kapsamı. Tam-dupleks modeller dar dil desteğine sahip; pipeline'lar LLM'in çok dilli yeteneğini miras alır.

Tool-calling / retrieval gerektiren kurumsal ajanlar için yalnız tam-dupleks mimariyi reddet — Moshi bir diyalog modeli, ajan çerçevesi değil. Sub-250 ms konuşma ajanları için yalnız pipeline'ı reddet — aşamalar toplanır. Tek GPU'da > 4 eşzamanlı oturum için Moshi'yi reddet — çekişmeye vurur.

Örnek girdi: "Dil öğrenimi için ses arkadaşı — konuşma akıcılığı pratiği. İngilizce + Fransızca. < 250 ms tepki. 10k günlük aktif."

Örnek çıktı:
- Mimari: tam-dupleks (Moshi). Sub-250 ms latency gereksinimi + konuşma akıcılığı Moshi'nin güçlü yanlarına uyuyor.
- Model: Moshi. EN + FR iyi desteklenir. CC-BY 4.0 lisansı.
- Ölçek: 4-6 eşzamanlı oturum başına bir L4 GPU → %10 eşzamanlılıkta 10k DAU için zirvede ~1500 GPU. Sessiz yol için Kyutai Pocket TTS + yerel Whisper kullanarak cihaz üstü hafif mod planla.
- Tool çağrısı: minimum — "gramer ipucu göster" ve "bu ifadeyi çevir" küçük bir LLM sidecar üzerinden yönlendirilebilir; etkileşimin çoğu Moshi'nin parladığı açık uçlu diyalog.
- Dil kapsamı: EN + FR (yerli); ES / DE / JP Hibiki-Zero adaptasyonu üzerinden (yeni dil başına 1000 sa ses gerekir).
