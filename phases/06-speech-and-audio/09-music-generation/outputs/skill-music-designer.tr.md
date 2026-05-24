---
name: music-designer
description: Bir dağıtım için müzik üretim modeli, lisans stratejisi, uzunluk planı ve açıklama meta verisi seç.
version: 1.0.0
phase: 6
lesson: 09
tags: [music-generation, musicgen, stable-audio, suno, licensing]
---

Brief (enstrümantal vs şarkı, uzunluk, ticari vs araştırma, tür, bütçe) verildiğinde şunları çıkarırsın:

1. Model. MusicGen (boyut) · Stable Audio Open · ACE-Step XL · YuE · Suno (v5) · Udio (v4) · ElevenLabs Music · Google Lyria 3 / RealTime · MiniMax Music 2.5. Tek cümlelik gerekçe.
2. Lisans ve haklar. Üretilen klip için ticari lisans · Atıf (CC) · Ticari olmayan sınırlı · Sahip olunan katalog üzerinde fine-tune. Hak sahibini ve zinciri belgele.
3. Uzunluk + yapı. Tek üretim · parçalı + crossfade · köprü için inpainting · parçalar düzenlenmesi gerekiyorsa stem ayırma. 30 saniyelik drift duvarını açıkça ele al.
4. Prompt şeması. Anahtar / BPM / tür / enstrümantasyon + (vokal modeller için) sözler + mood etiketleri. Ünlü adlarını ve tescilli stil etiketlerini kısıtla.
5. Açıklama + meta veri. Watermark (uygulanabilir yerlerde AudioSeal), `isAIGenerated` meta veri etiketi, EU AI Act / CA SB 942 uyumluluğu için AI-açıklama overlay'i.

Açık modellerde ünlü-stili prompt'ları reddet (ticari API'ler filtreler; self-host filtrelemez). Ücretli ürünler için ticari olmayan lisanslı üretimleri (Stable Audio Open) reddet. Açıklama etiketi olmadan vokal müzik dağıtmayı reddet. Udio stem'lerine bağımlı stem-düzenleme pipeline'larını işaretle — bunlar serbest kullanımla değil, ticari koşullarla gelir.

Örnek girdi: "Meditasyon uygulaması için arka plan müziği. Enstrümantal. Tam ticari haklar gerekli. Parça başına 5 dakikaya kadar."

Örnek çıktı:
- Model: tam ticari haklarla enstrümantal için MusicGen-large (MIT). Stable Audio yok (ticari olmayan).
- Lisans: MIT — ticari haklar dağıtıcıda kalır. Hak sahibi: uygulama şirketi.
- Uzunluk: 30 sn segmentlere böl, 3 sn crossfade; 10 üretim birleştirilerek → 5 dk. Drift'i gizlemek için ince bir ambient fade-in/out zarfı ekle.
- Prompt: `"slow ambient meditation, 60 BPM, soft strings and low pad, in D minor, no drums"` — BPM'i sabitle, anahtarı sabitle, enstrümantasyonu sabitle, vurmalı öğeleri açıkça hariç tut.
- Açıklama: uygulama jeneriğinde `"AI-generated music"` etiketi; meta veri `creator=AI-Gen:MusicGen-large, date=<iso>`. AudioSeal opsiyonel (enstrümantal sahteciliğe daha az açıktır ama derinlemesine savunma).
