---
name: prompt-distributed-training-planner
description: Model boyutu ve mevcut donanım verildiğinde dağıtık eğitim koşusu planla
version: 1.0.0
phase: 10
lesson: 5
tags: [distributed-training, fsdp, deepspeed, tensor-parallelism, pipeline-parallelism, scaling]
---

# Dağıtık Eğitim Planlayıcısı

Büyük bir dil modeli için dağıtık eğitim koşusu planlarken, paralellik stratejisini, bellek bütçesini, iletişim yükünü ve beklenen throughput'u belirlemek için bu çerçeveyi kullan.

## Girdi Gereksinimleri

Şunu sağla:
- **Model boyutu** (milyar parametre)
- **Hedef eğitim token'ı** (trilyon)
- **Mevcut GPU'lar** (tip: A100/H100/H200, sayı, interconnect: NVLink/InfiniBand)
- **GPU belleği** (A100/H100 için 80GB, H200 için 141GB)
- **Node'lar** (node başına GPU, node sayısı)
- **Bütçe kısıtlamaları** (max maliyet dolar, max duvar saati süresi)

## Adım 1: Bellek Bütçesi

Her bileşen için GPU başına belleği hesapla:

| Bileşen | Formül | FP16 | FP32 |
|-----------|---------|------|------|
| Ağırlıklar | params x bytes_per_param | params x 2 | params x 4 |
| Adam optimizer (m + v) | params x 4 x 2 | her zaman 8 byte/param | 8 byte/param |
| Gradient'ler | params x bytes_per_param | params x 2 | params x 4 |
| Aktivasyonlar (tahmin) | seq_len x batch x hidden x layers x 2 | değişken | değişken |

Toplam GPU belleğini aşarsa sharding gerekir. Şu sırada dene:
1. ZeRO-1 (sadece optimizer shard'la) -- en ucuz iletişim
2. ZeRO-2 (+ gradient'ler) -- orta iletişim
3. FSDP/ZeRO-3 (+ ağırlıklar) -- en yüksek iletişim ama maksimum bellek tasarrufu
4. Aktivasyonlar hâlâ fazla büyükse activation checkpointing ekle
5. Tek katman tek GPU'ya sığmıyorsa tensor parallelism ekle

## Adım 2: Paralellik Stratejisi

### Karar Ağacı

1. **Bir katman bir GPU'ya sığar mı?**
   - Hayır: Tensor parallelism gerekir. TP = 2, 4 veya 8 ayarla (node içinde).
   - Evet: Tensor parallelism'i atla.

2. **Tüm model (sharding ile) bir node içindeki GPU'lara sığar mı?**
   - Hayır: Pipeline parallelism gerekir. PP = node sayısı / grup ayarla.
   - Evet: Pipeline parallelism'i atla.

3. **Data parallelism için kaç GPU kalır?**
   - DP = total_gpus / (TP x PP)

4. **Data parallel grup içinde hangi sharding seviyesi?**
   - FSDP (ZeRO-3) ile başla. İletişim darboğazıysa ZeRO-2 veya ZeRO-1'e indir.

### Tipik Konfigürasyonlar

| Model Boyutu | Toplam GPU | TP | PP | DP | Sharding |
|-----------|-----------|----|----|-----|----------|
| 7B | 8 | 1 | 1 | 8 | FSDP |
| 13B | 16 | 2 | 1 | 8 | FSDP |
| 70B | 64 | 8 | 1 | 8 | FSDP |
| 70B | 128 | 8 | 2 | 8 | FSDP |
| 405B | 16,384 | 8 | 16 | 128 | FSDP |

## Adım 3: İletişim Analizi

Eğitim adımı başına iletişim hacmini tahmin et:

- **Data parallel (all-reduce)**: adım başına 2 x gradient_size x (N-1)/N
- **FSDP (all-gather + reduce-scatter)**: adım başına ~3 x weight_size x (N-1)/N (DP'den yüksek)
- **Tensor parallel (katman başına all-reduce)**: adım başına 2 x activation_size x num_layers (NVLink gerekir)
- **Pipeline parallel (point-to-point)**: stage sınırı başına activation_size (minimal)

İletişim süresi compute süresinin %20'sini aşarsa, strateji communication-bound'dır. Çözümler:
- Gradient accumulation (all-reduce frekansını düşür)
- İletişimi computation ile örtüştür (FSDP bunu varsayılan olarak yapar)
- Micro-batch boyutunu artır (daha iyi compute-iletişim oranı)
- Daha az iletişim yoğun sharding aşamasına geç

## Adım 4: Throughput ve Maliyet Tahmini

**Eğitim adımı başına FLOPS:**
- Forward: ~2 x params x tokens_per_batch
- Backward: ~4 x params x tokens_per_batch (forward'ın 2 katı)
- Toplam: ~6 x params x tokens_per_batch

**Eğitim süresi:**
- total_flops = 6 x params x total_tokens
- time_seconds = total_flops / (num_gpus x gpu_tflops x 1e12 x utilization)
- Tipik utilization: %35-45 (iletişim, pipeline bubble, bellek yükü dikkate alınarak)

**Maliyet:**
- total_gpu_hours = num_gpus x time_seconds / 3600
- cost = total_gpu_hours x cost_per_gpu_hour

## Adım 5: Doğrulama Kontrol Listesi

Başlatmadan önce:

1. GPU başına bellek donanım sınırı içinde (%10 boşluk ile)
2. Effective batch boyutu hedefe uyuyor (per_gpu_batch x DP x gradient_accumulation_steps)
3. İletişim-compute oranı %20 altında
4. Pipeline bubble oranı %15 altında (yeterli micro-batch)
5. Learning rate effective batch boyutu için ölçeklenmiş
6. Checkpointing frekansı arıza olasılığını hesaba katıyor (büyük koşular için her 1-2 saatte kaydet)
7. Gradient clipping ayarlandı (büyük modeller için tipik olarak 1.0)
8. Warmup adımları toplam adımlara oranlı (tipik %0.1-1)

## Kırmızı Bayraklar

- **TP > 8**: Node'lar arası (InfiniBand üzerinden) tensor parallelism neredeyse her zaman pipeline parallelism'den yavaş
- **Pipeline stage > 32**: Çok sayıda micro-batch ile bile bubble yükü önemli hale gelir
- **Effective batch boyutu > 10M token**: Azalan getiriler; yakınsamayı bozabilir
- **Utilization %30 altında**: Communication-bound -- paralellik stratejisini yeniden değerlendir
- **13B üstünde activation checkpointing yok**: Backward pass sırasında bellek tükenir
- **Küçük per-GPU batch ile gradient accumulation yok**: Gradient gürültüsü artar; 256+ sample'lık effective batch'e biriktir
