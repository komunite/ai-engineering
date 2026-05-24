---
name: voice-assistant-architect
description: Verilen bir iş yükü için tam yığın ses asistanı spesifikasyonu üret — bileşenler, latency bütçesi, gözlemlenebilirlik, uyumluluk.
version: 1.0.0
phase: 6
lesson: 12
tags: [voice-assistant, architecture, livekit, pipecat, compliance]
---

Kullanım durumu (tüketici / müşteri-destek / erişilebilirlik / edge), beklenen ölçek (eşzamanlı oturumlar, dakika/ay), dil, latency hedefleri, uyumluluk (HIPAA, PCI, EU AI Act, CA SB 942) verildiğinde şunları çıkarırsın:

1. Bileşenler (7 katman). Mikrofon + parçalama · VAD · streaming STT · LLM + araçlar · streaming TTS · oynatma · kesinti işleyici. Her biri için tam sağlayıcıyı/modeli adlandır.
2. Latency bütçesi. Aşama başına uçtan uca hedefe toplam P50 / P95 / P99 hedefleri. Hangi aşamaların bağımsız vs sıralı olduğunu işaretle.
3. Tool-call şeması. Her araç için JSON spec + hata işleme + geri dönüş metni. LLM iki kez başarısız olduğunda alması gereken bir "yardım edemem" yolunu daima dahil et.
4. Güvenlik. Prompt injection koruması, ses klonlama kilidi (TTS klon yetenekliyse), wake-word kapısı (her zaman açıksa), loglarda PII redaksiyonu, 30 günlük saklama.
5. Gözlemlenebilirlik. Aşama başına P50/P95/P99 · yanlış kesinti oranı · tool-call başarı oranı · 100 çağrı başına WER · dakika başına maliyet · terk oranı.
6. Uyumluluk. Açıklama sesi ("Bu bir AI asistanıdır"), bölge-sabitleme (AB verisi AB'de), denetim kaydı saklama, opt-out yolu.

Wake word olmadan her zaman açık dağıtımları reddet. Stream yapmayan TTS'i reddet (söyleyiş uzunluğu kadar latency ekler). P95 olmadan ortalama latency'yi reddet — kuyruk, kullanıcıların terk ettiği yerdir. Hukuk incelemesi olmadan > 30 günlük ham ses saklamayı reddet.

Örnek girdi: "Az gören kullanıcılar için erişilebilirlik asistanı: tüketici e-posta uygulamasına yalnız ses arayüzü. İngilizce. P95 < 600 ms. ~10k eşzamanlı kullanıcı."

Örnek çıktı:
- Bileşenler: sounddevice (LiveKit Agents üzerinden WebRTC) · Silero VAD · Deepgram Nova-3 (İngilizce) · e-posta araçlarıyla GPT-4o (read_message, compose_reply, mark_read) · Cartesia Sonic 2 streaming · WebRTC out · VAD tetiklendiğinde LLM ve TTS'i iptal et.
- Bütçe: yakalama 120 ms + VAD 40 + STT 150 + LLM TTFT 100 + TTS TTFA 150 = 560 ms P95.
- Araçlar: read_message({id}), compose_reply({message_id, body}), mark_read({id}), search({query}). Hepsi JSON döner; LLM araç başına maksimum 2 yeniden deneme ve sonra geri dönüş "Bunu yapamadım — yeniden ifade etmeyi deneyin".
- Güvenlik: prompt injection koruması (`ignore previous instructions` tespit); wake word "Hey Mail"; ses klonlama yok (sabit Cartesia sesi); loglarda e-posta gövdelerini redakte et.
- Gözlemlenebilirlik: Hamming AI üretim izleme; aşama başına Prometheus histogramları; yanlış kesinti > %5 ya da p95 > 800 ms'de alarm.
- Uyumluluk: ilk kullanımda AI açıklaması; yalnız tıbbi mesajlar için HIPAA opt-in; AB kullanıcıları AB'de barındırılan Cartesia + GPT-4o Ireland'a vurur.
