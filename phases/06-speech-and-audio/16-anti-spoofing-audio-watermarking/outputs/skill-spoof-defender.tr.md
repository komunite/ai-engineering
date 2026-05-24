---
name: spoof-defender
description: Bir ses üretim / ses kimlik doğrulama dağıtımı için tespit modeli, watermark, köken manifestosu ve operasyonel oyun planı seç.
version: 1.0.0
phase: 6
lesson: 16
tags: [anti-spoofing, watermark, audioseal, asvspoof, c2pa, voice-fraud]
---

İş yükü (ses üretim vs ses kimlik doğrulama, dağıtım ölçeği, uyumluluk bölgesi, saldırgan profili) verildiğinde şunları çıkarırsın:

1. Tespit (CM). AASIST · RawNet2 · NeXt-TDNN + WavLM · ticari (Pindrop, Validsoft). Eğitim verisi: ASVspoof 2019 / ASVspoof 5 / alan-özgü. Hedef EER.
2. Watermarking (giden üretim). `(model_id, user_id, generation_ts)` kodlayan AudioSeal 16-bit payload · WaveVerify (alternatif) · yok (gerekçeyle). Gönderim öncesi her çıktıda CI'da dedektör çalışır.
3. Köken. Dağıtıcının anahtarıyla imzalanmış C2PA manifestosu · IPTC meta verisi · yok (tüketici olmayan ses için).
4. Ses kimlik doğrulama korumaları (uygulanabilirse). Canlılık testi (rastgele cümle TTS' + transkribe), replay saldırı tespiti (AASIST + PA modeli), kanal başına biyometrik eşik kalibrasyonu.
5. Operasyonel. Denetim kaydı saklama, onay artefaktı saklama (7+ yıl), kötüye kullanım tespit sinyalleri (ani hacim patlaması, adlandırılmış varlık prompt'ları), kill-switch prosedürü.

AudioSeal (ya da eşdeğer watermark) olmadan ses üretim dağıtımlarını reddet. Anti-spoofing tespiti olmadan ses biyometrik dağıtımlarını reddet — ses klonlama yalnızca cosine kimlik doğrulamayı önemsiz şekilde aşılabilir kılar. Yalnızca köken manifestosuna bağımlı dağıtımları reddet (çıkarılabilir). Kanal kalibrasyon taraması olmadan gerçek dünya dağıtımları için ASVspoof 2019'da eğitilmiş tespit eşiklerini reddet.

Örnek girdi: "Banka müşteri hizmetleri IVR'ı. Ses biyometrik kilit açma + AI üretilmiş ses ajanı. 10M çağrı/ay. ABD + AB."

Örnek çıktı:
- Tespit: Pindrop ticari (tercih edilen) ya da NeXt-TDNN + WavLM açık. ASVspoof 5 + 100k bankaya özgü çağrı örneğinde eğitim. Alan içi veride hedef EER < %0.5.
- Watermarking: her giden TTS söyleyişinde AudioSeal 16-bit payload; payload bank_id + session_id + timestamp kodlar. Dedektör iletim öncesi doğrular.
- Köken: müşteriye ses-dışa aktarım iş akışlarında C2PA manifestosu; yalnız iç çağrılar atlar.
- Ses kimlik doğrulama: her kimlik doğrulamada canlılık testi (TTS rastgele 4 haneli cümle; kullanıcı tekrarlar + dedektör + transkriber). Anti-spoofing her gelen kimlik doğrulama girişiminde çalışır. FAR %0.1, FRR %1'de biyometrik eşik.
- Operasyonel: bölgede onay + denetim kaydı için 7 yıl saklama (AB verisi AB-yerleşik). Ani klon-istek hacmi > 2σ'da alarm; kötüye kullanım tespitinde kill-switch.
