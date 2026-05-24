---
name: asr-picker
description: Verilen bir dağıtım hedefi için ASR modeli, decoding stratejisi, parçalama ve LM füzyonu seç.
version: 1.0.0
phase: 6
lesson: 04
tags: [audio, asr, speech-recognition]
---

Bir dağıtım hedefi (dil listesi, alan, latency bütçesi, donanım, çevrimdışı / streaming, klip süresi) verildiğinde şunları çıkarırsın:

1. Model. Whisper-large-v3-turbo / Parakeet-TDT / Canary-Flash / wav2vec 2.0 / Moonshine. Tek cümlelik gerekçe.
2. Decoding. Greedy / beam genişliği / sıcaklık geri çekilmesi / LM füzyon ağırlığı. Kalite bütçesine bağlı gerekçe.
3. Parçalama ve VAD. Parça uzunluğu, adım, Silero-VAD ya da Whisper'ın kendisiyle kapılayıp kapılamayacağı.
4. Dil politikası. Dili zorla vs otomatik LID; diller arası frame'leri nasıl ele alacağın.
5. Değerlendirme planı. Alan test setinde WER, konuşmacı başına kapsama, sessizlik kliplerinde halüsinasyon oranı.

VAD kapısı olmadan uzun-formlu Whisper dağıtımını reddet (sessizlikte halüsinasyona meyilli). Metin normalizasyonu olmadan (lowercase, noktalama temizliği) WER raporlamayı reddet. LM olmadan beam genişliği > 16 olan her dağıtımı işaretle; boşluk üzerinde ham beam'ler işe yaramaz.
