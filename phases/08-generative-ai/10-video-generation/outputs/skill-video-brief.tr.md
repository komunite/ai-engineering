---
name: video-brief
description: Bir video brief'ini 2026 video generator için model + prompt + shot planına çevir.
version: 1.0.0
phase: 8
lesson: 10
tags: [video, diffusion, sora, veo, kling]
---

Bir video brief'i (süre, en-boy oranı, stil, konu, kamera planı, ses ihtiyaçları, fidelity çıtası, bütçe) verildiğinde, şunu çıkar:

1. Model + hosting. Sora, Veo 3, Kling 2.1, Runway Gen-3, Pika 2.0, CogVideoX, HunyuanVideo, WAN 2.2 ya da Mochi-1. Süre / kalite / lisansa bağlı tek cümlelik gerekçe.
2. Prompt scaffolding. (a) kamera dili (establishing, tracking, dolly, crane, handheld), (b) konu + aksiyon, (c) aydınlatma + stil, (d) negative prompt ya da stil toggle'ları. Sora için 50-150 token, Runway için 20-60 hedefle.
3. Shot planı. Tek-klip vs dikilmiş çoklu çekim, keyframe ya da first-frame anchor'ları, shot başına I2V vs T2V.
4. Seed + tekrar üretilebilirlik. Çekim başına seed, version pin, tooling repo'su.
5. QA checklist. Flicker, kimlik tutarlılığı, fizik ihlalleri, watermark uyumu için frame-by-frame.
6. Ses. Veo 3'te native, aksi halde bolt-on (ElevenLabs, Suno ya da lisanslı stem'ler + lip-sync geçişi).

Free tier'da 1080p'de &gt; 10s sürekli hareket vaat etmeyi reddet (Pika / Kling / Runway 10s'de cap eder; daha uzun run'lar dikilmiş olur). Release olmadan gerçek insanların benzerliklerini üretmeyi reddet. 2026'da gerçek-zamanlı 4K üretim ima eden herhangi bir brief'i flag'le - şu anki en iyi, hosted endpoint'te 1080p'de 6s klip başına ~30s üretim.
