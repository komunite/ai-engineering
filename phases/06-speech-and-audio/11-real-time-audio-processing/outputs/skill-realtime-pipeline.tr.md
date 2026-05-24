---
name: realtime-voice-pipeline
description: Uçtan uca hedef latency için transport, VAD, streaming STT, LLM, streaming TTS ve orkestrasyon seç.
version: 1.0.0
phase: 6
lesson: 11
tags: [voice-agent, livekit, pipecat, silero, streaming, latency]
---

Hedef (latency P50/P95, dil, kanal, çevrimdışı vs bulut, çağrı hacmi) verildiğinde şunları çıkarırsın:

1. Transport. WebRTC (LiveKit / Daily) · WebSocket · SIP trunking (Twilio / Telnyx). Jitter toleransı + kullanım durumuna bağlı gerekçe.
2. VAD + sıra alımı. Silero VAD (açık, %99.5 TPR) · Cobra (ticari) · LiveKit turn-detector. Eşik, asgari konuşma süresi, sessizlik bekleme süresi.
3. Streaming STT. Parakeet TDT (en hızlı açık) · Kyutai STT (flush hilesiyle) · Deepgram Nova-3 (API, ~150 ms) · Whisper-streaming. Gerekçe.
4. LLM + streaming. TTS başlamadan önce ilk 20 token'ı sabitle. Model + streaming yapılandırması + prompt injection için guardrail'ler.
5. Streaming TTS. Kokoro-82M (~100 ms TTFA) · Orpheus · Cartesia Sonic · ElevenLabs Turbo. Ses paketi ya da klonlama koruması (Ders 8).
6. Orkestrasyon. LiveKit Agents · Pipecat · Vapi · Retell · özel Rust. Takım becerileri + ölçeğe bağlı gerekçe.
7. Gözlemlenebilirlik. Aşama başına P50/P95/P99 histogramları; yanlış-pozitif kesinti oranı; çağrı düşürme oranı; çağrı örneklerinde WER.

STT öncesi tüm söyleyişleri buffer'layan dağıtımları reddet. Stream yapmayan TTS'i reddet. Ortalama latency ile değerlendirmeyi reddet — P95 iste. > 100k dakika/ay için yönetilen platformları (Vapi / Retell) kendi-yapımıyla maliyet karşılaştırması olmadan reddet.

Örnek girdi: "Araba sigortası teklif veren ses ajanı. < 500 ms P95. İngilizce, ABD. 50k dakika/hafta. Uyumluluk: HIPAA-yakını (loglarda PII yok)."

Örnek çıktı:
- Transport: LiveKit Agents + Twilio SIP. Çağrı merkezi ölçeğinde kanıtlanmış, HIPAA-modu opt-in.
- VAD: Silero VAD @ eşik 0.45, asgari konuşma 220 ms, sessizlik beklemesi 400 ms. LiveKit turn-detector overlay.
- STT: Deepgram Nova-3 İngilizce (~150 ms P95); on-prem denetim gerekirse Parakeet-TDT'ye geri dönüş.
- LLM: OpenAI realtime API üzerinden streaming GPT-4o; post-filter ile prompt injection'a karşı koru; ilk 20 token'ı TTS'e sabitle.
- TTS: Cartesia Sonic 2 (~150 ms TTFA, ses klonlama kullanılmadı — önceden tanımlı ses).
- Orkestrasyon: LiveKit Agents. Üretim için Hamming AI üzerinden gözlemlenebilirlik.
- Loglar: kalıcılaştırmadan önce regex + NER pass ile CVV / SSN / DOB strip et. 30 gün sakla.
