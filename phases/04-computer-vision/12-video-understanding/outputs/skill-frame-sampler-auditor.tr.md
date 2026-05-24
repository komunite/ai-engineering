---
name: skill-frame-sampler-auditor
description: Bir video pipeline'ının frame sampler'ını off-by-one, kısa klip handle'ı ve crop tutarlılığı açısından denetle
version: 1.0.0
phase: 4
lesson: 12
tags: [computer-vision, video, sampling, debugging]
---

# Frame Sampler Auditor

Frame sampling video pipeline'larının kırıldığı yerdir. Buradaki bug'lar her aşağı akış metriğine yayılır.

## Ne zaman kullan

- Yeni bir video data loader yazarken.
- Bir paper'dan sayıları yeniden üretirken ve eğitim accuracy'si raporlanandan düşükken.
- Eval accuracy'si turlar arası kararsız olan bir video modeli ayıklarken.

## Girdiler

- `sampler_code`: (num_frames_total, T) alan ve T indeks döndüren Python fonksiyonu.
- `T`: hedef klip uzunluğu.
- Opsiyonel test case'leri: egzersiz için `num_frames_total` değerleri (örn. `[3, T-1, T, T+1, 30, 300, 3000]`).

## Kontroller

### 1. Kısa klip handle'ı
`num_frames_total < T` besle. Her döndürülen indeks `[0, num_frames_total - 1]` aralığında olmalı. Standart padding politikası kalan pozisyonlar için son frame'i tekrar etmektir.

### 2. Sınır indeksleri
`num_frames_total == T` besle. Döndürülen indeksler tam olarak `[0, 1, ..., T-1]` olmalı.

### 3. Uniform dağılım
`num_frames_total == 10 * T` besle. Döndürülen indeksler monoton artan ve kabaca eşit aralıklı olmalı.

### 4. Dense window sınırları
Dense sampling için, `num_frames_total == 3 * T` besle. Döndürülen indeksler bitişik bir pencere oluşturmalı, asla klip sonunu geçmemeli.

### 5. Determinizm
Aynı girdiler ve (deterministik sampler'lar için) aynı RNG ile sampler'ı iki kez çağır. İndeksler eşleşmeli.

### 6. Crop tutarlılığı
Pipeline frame başına spatial crop da döndürüyorsa, aynı seed ile aynı klip için sampler'ı iki kez çalıştır ve her frame'in aynı crop box'ını (aynı `(x, y, w, h)`) kullandığını teyit et. Bir klip içinde frame başına farklı crop temporal coherence'ı bozar ve klasik sessiz bir bug'dır. Kabul edilebilir varyasyon: *klip başına* uygulanan augmentation, bir klip içinde tutarlı.

## Rapor

```
[sampler audit]
  name: <function name>
  T:    <int>

[short-clip handling]
  passed | failed (<details>)

[boundary]
  passed | failed

[uniform spacing]
  passed | failed (<stddev of gaps>)

[dense window]
  passed | failed (<details>)

[determinism]
  passed | failed

[crop consistency]
  passed | failed (<per-frame crop varies: yes/no>)

[verdict]
  ok | fix required
```

## Kurallar

- Kısa klip handle'ı aralık dışı indeksler döndürüyorsa bir sampler'ı asla "ok" işaretleme.
- Dense sampler'lar asla `num_frames_total - 1`'i geçen bir pencere döndürmemeli.
- Sampler stokastik (dense) ise, determinizmi sadece açık seedlenmiş RNG ile test et.
- Kanonik politikaları öner ama sessizce düzeltme: son frame ile pad, pencereyi sona clamp et, yarı-açık aralıkları yuvarla.
