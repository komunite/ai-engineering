---
name: voice-pipeline
description: Barge-in, güven kapısı ve latency bütçesi zorlaması ile Pipecat-şekilli bir voice pipeline'ı (VAD + STT + LLM + TTS + transport) iskelele.
version: 1.0.0
phase: 14
lesson: 22
tags: [voice, pipecat, livekit, webrtc, latency]
---

Bir voice ürün spec'i (dil, transport, provider'lar) verildiğinde, frame-tabanlı bir pipeline iskelele.

Üret:

1. `kind`, `payload`, `direction` (downstream / upstream) içeren `Frame` tipi.
2. Processor'lar: `VAD`, `STT`, `LLM`, `TTS`, `Transport`. Her biri `process(frame)` ile.
3. Processor'ları ileri ve geri zincirleyen `link()` helper'ı.
4. Cancel frame işleme: transport'tan TTS'e, LLM'e, STT'ye UPSTREAM yol, her aşamada bekleyen işi düşürerek.
5. Observer'lar: aşama başına latency metrikleri; bir processor'ı geçen her frame başına bir OTel span yay (Lesson 23).
6. STT'de güven kapısı: eşiğin altında, transkript yerine bir "lütfen tekrarlayın" text frame'i yay.

Sert ret durumları:

- UPSTREAM işleme olmadan pipeline. Voice için barge-in opsiyonel değildir.
- Streaming olmadan LLM çağrıları. First-token latency baskındır; stream edilmelidir.
- Güven-kör STT. LLM'e yanlış transkript beslemek yanlış yanıtlar üretir.

Reddetme kuralları:

- End-to-end latency soğuk çalıştırmada 1500ms'yi aşıyorsa, göndermeyi reddet. Zinciri optimize et ya da bir MultimodalAgent (LiveKit direct-audio) kullan.
- Ürün telephony-öncelikli ise ve pipeline'da SIP adaptörü yoksa, reddet. LiveKit SIP veya bir platform üzerinden yönlendir (Vapi/Retell).
- Ürün transit'te şifreleme olmadan PII ses taşıyorsa, reddet.

Çıktı: `frames.py`, `processors.py`, `pipeline.py`, `observers.py`, latency bütçesini, barge-in tasarımını ve transport seçimini açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 23 (OTel), Lesson 24 (observability backend'leri) veya WebRTC ayrıntıları için LiveKit dokümanları.
