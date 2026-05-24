---
name: vad-tuner
description: Bir ses ajanı için VAD modeli, eşik, sessizlik bekleme süresi, pre-roll ve sıra-tespit stratejisi seç.
version: 1.0.0
phase: 6
lesson: 14
tags: [vad, silero, cobra, turn-detection, flush-trick]
---

İş yükü (tüketici / çağrı merkezi / edge / erişilebilirlik; gürültü profili; dil karışımı; latency) verildiğinde şunları çıkarırsın:

1. VAD. Silero VAD (varsayılan) · Cobra (ticari doğruluk) · pyannote segmentation (speaker diarization-seviye) · WebRTC VAD (eski / küçük). Tek cümlelik gerekçe.
2. Parametreler. Eşik (0.3-0.5), asgari konuşma (200-300 ms), sessizlik bekleme süresi (400-800 ms), pre-roll (250-500 ms).
3. Anlamsal sıra tespiti. Etkin (LiveKit turn-detector ya da özel MLP) ya da değil. Beklenen kullanıcı konuşma örüntülerine bağlı gerekçe.
4. Flush hilesi. Etkin (STT destekliyorsa — Kyutai / Deepgram) ya da değil. Beklenen latency tasarrufu.
5. Korumalar. Asgari süreden kısa konuşmayı reddet; pre-roll'u daima koru; kullanıcı başına sessizlik bekleme süresi geçersiz kılmayı sınırla; VAD servisi çökerse fail-open (her şeyi konuşma kabul et).

Üretim için yalnız enerji tabanlı VAD'yi reddet — çok gürültülü. Sıfır sessizlik beklemesini reddet — kullanıcıları keser. Adanmış Silero mevcutken Whisper tabanlı VAD'yi reddet (daha yavaş, daha az doğru).

Örnek girdi: "Havayolu yeniden rezervasyon için çağrı merkezi IVR'ı. Gürültülü arka plan (havalimanı). İngilizce + İspanyolca. < 500 ms sıra tespiti."

Örnek çıktı:
- VAD: gürültü-direnci avantajı için Cobra (ticari). Maliyet engelleyiciyse Silero'ya geri dönüş.
- Parametreler: eşik 0.4 (havalimanı gürültü zemini yüksek); asgari konuşma 300 ms; sessizlik beklemesi 600 ms (kullanıcılar IVR sırasında uçuş numaralarını okurken sık duraklar); pre-roll 400 ms.
- Anlamsal sıra: LiveKit turn-detector etkin — cümle ortası duraklamalar yaygın ("Uçuşumu... yarına değiştirmem gerek").
- Flush hilesi: Deepgram streaming üzerinde etkin. Beklenen tasarruf: 400 ms → 150 ms sıra-sonu latency.
- Korumalar: Cobra/Deepgram ulaşılamazsa fail-open; ayar için her VAD-tetiklenme olayını denetim logla.
