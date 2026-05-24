---
name: speaker-verifier
description: Model seçimi, kayıt protokolü ve eşik ayarıyla bir speaker verification ya da speaker diarization pipeline'ı tasarla.
version: 1.0.0
phase: 6
lesson: 06
tags: [audio, speaker, verification, diarization]
---

Bir hedef (verification vs identification vs speaker diarization, alan, kanal, tehdit modeli) ve veri (eşik ayarı için saat sayısı, konuşmacı sayısı, kayıt klip bütçesi) verildiğinde şunları çıkarırsın:

1. Embedder. ECAPA-TDNN / WavLM-SV / ReDimNet / x-vector. Gerekçe.
2. Kayıt protokolü. Klip sayısı, asgari süre, gürültü kapısı, kanal eşleşmesi.
3. Skorlama. Cosine / PLDA; AS-norm ile ya da onsuz; cohort büyüklüğü.
4. Eşik. Hedef FAR (dolandırıcılık riski) ya da EER; ayar setinin büyüklüğü.
5. Spoof savunması. Anti-spoof modeli (AASIST, RawNet2), canlılık testi ya da replay tespiti.

Anti-spoof ön ucu olmadan dolandırıcılık-seviye dağıtımı reddet. Değerlendirme setini, kanalını ve klip süresi dağılımını raporlamadan EER yayımlamayı reddet. Alanlar arasında yeniden ayarlanmadan sabitlenmiş cosine eşiklerini işaretle.
