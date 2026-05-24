---
name: mtp-planner
description: Yeni bir pretraining koşusu için multi-token prediction entegrasyonu planla.
version: 1.0.0
phase: 10
lesson: 18
tags: [mtp, multi-token-prediction, deepseek-v3, pre-training, speculative-decoding]
---

Bir pretraining koşu spesifikasyonu (model ölçeği, hidden size, layers, veri token'ı bütçesi, GPU topolojisi, hedef deployment) ve belirtilen bir hedef (daha yoğun eğitim sinyali vs speculative-decoding draft vs her ikisi) verildiğinde, bir MTP entegrasyon planı üret.

Şunları üret:

1. Derinlik D. 1 veya 2 seç. DeepSeek-V3 D=1 kullanır ve ilk derinlikte speculative-decoding kabul oranını %80+ olarak raporlar. D=2 çoğu koşu için azalan getiri bölgesidir. Seçimi compute bütçesine karşı gerekçelendir — her ekstra derinlik eğitim adımı başına kabaca bir transformer block compute ekler.
2. Lambda schedule. Varsayılan: eğitimin ilk %10'u için 0.3, sonrasında 0.1. Küçük modellerde (7B altı) daha yoğun sinyal daha önemli olduğunda erken 0.5'e kadar yukarı ayarla; MTP loss'un ana loss'a baskın olduğunu gözlemlersen aşağı ayarla.
3. Parametre bütçesi. Ana modele karşı modül başına parametre sayısını raporla. Overhead'in ana parametrelerin %5'inin altında (dense) veya %3'ün altında (MoE) olduğunu doğrula.
4. Bellek ve compute overhead. Adım başına ekstra forward-pass FLOP'larını (kabaca `D * transformer_block_cost`), ekstra backward-pass belleğini (D modül için aktivasyon belleği) ve ekstra peak VRAM'i (shared embedding ve head sayılmaz, projection ve transformer block sayılır) ölç.
5. Inference-zamanı kablolama. Inference'ta MTP modülünü speculative-decoding draft olarak nasıl tüketeceğini açıkla. Leviathan kural entegrasyon yolunu ve KV-rollback defter tutmayı adlandır. Hedef inference stack (vLLM, SGLang, TensorRT-LLM) ile uyumluluğu doğrula.

Sert redler:
- MTP'siz pretrain edilmiş dense modele MTP eklemek. Retrofit edilemez — MTP modülleri eğitilmemiş.
- İlk entegrasyon için D > 2. D=1 üzerindeki kazanç küçük; karmaşıklık hızla büyür.
- 1B altı aktif parametreli modelde MTP. Bu ölçekte sinyal overhead maliyetinden daha zayıf.
- Hedef speculative decoding olduğunda paralel (Gloeckle-stili) head kullanmak. Bunlar causally zincirlemez.

Reddetme kuralları:
- Pretraining verisi kısa diziler (2k altı) tarafından baskınsa, reddet. MTP kazançları depth-2 supervision'ın önemli olacağı kadar uzun diziler varsayar.
- Hedef inference stack speculative decoding'i hiç desteklemiyorsa, MTP'nin hâlâ daha yoğun eğitim sinyalini sağladığını not et ve devam et, ama uyumsuzluğu işaretle.
- Kullanıcı MTP olmadan mevcut dense checkpoint üzerinde pretraining'e devam ediyorsa, reddet ve MTP'yi yalnızca temiz bir eğitim koşusu başında veya temiz bir veri sınırı sıfırlamasında eklemeyi öner.

Çıktı: D, lambda schedule, parametre overhead (mutlak ve yüzde), compute overhead (eğitim adımı başına yüzde) ve inference-zamanı speculative-decoding kablolama planını listeleyen bir sayfalık entegrasyon planı. MTP'yi tutmayı haklı çıkaran ölçülen metriği adlandıran "başarı kriteri" paragrafıyla bitir: 50B eğitim token'ı sonrası derinlik 1'de kabul oranı %70'in üzerinde olmalı, aksi takdirde mimari geri alınmalı.
