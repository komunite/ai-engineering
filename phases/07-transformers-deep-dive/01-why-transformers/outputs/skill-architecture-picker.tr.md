---
name: sequence-architecture-picker
description: Uzunluk, throughput ve eğitim bütçesi verildiğinde dizi mimarisini (RNN, transformer, SSM, hibrit) seç.
version: 1.0.0
phase: 7
lesson: 1
tags: [transformers, architecture, rnn, ssm]
---

Bir dizi problemi (maksimum uzunluk, batch şekli, bütçelenmiş eğitim token sayısı, çıkarım gecikme hedefi, cihaz sınıfı) verildiğinde şunları çıkarırsın:

1. Birincil mimari. Şunlardan biri: transformer, state-space model (Mamba/RWKV), hibrit SSM+attention, RNN. Baskın kısıta bağlı tek cümlelik gerekçe.
2. Context length stratejisi. Transformer ise: full attention kesim noktası, sliding window boyutu, RoPE ölçekleme faktörü. SSM ise: scan chunk boyutu. RNN ise: gizli katman genişliği.
3. Eğitim FLOP profili. Mimari + context'ten token başına yaklaşık FLOP; spesifikasyonun compute bütçesine sığıp sığmadığını belirt.
4. Çıkarım bellek profili. Transformer'lar için KV cache, SSM'ler için state boyutu, RNN'ler için token başına bellek. Hedef cihaz tek bir batch=1'i tutabiliyor mu işaretle.
5. Risk notu. Bu seçimin spesifikasyonun ölçeğinde bilinen bir spesifik başarısızlık modu (örn. Flash Attention olmadan 24GB GPU'da 64K context'te transformer OOM).

1B token üzerindeki herhangi bir eğitim çalışması için saf RNN önermeyi reddet, gradyan akışı ve paralellik cezalarını açıkça belirtmeden. >64K context için full-attention transformer önermeyi reddet, `O(N^2)` bellek maliyetini belirtmeden. Adlandırılmış bir fallback olmadan üretim için yepyeni bir mimari (12 aydan daha az süre önce yayımlanmış) önermeyi reddet.
