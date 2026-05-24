---
name: skill-conv-shape-calculator
description: Bir CNN spec'ini katman katman gezip her blok için çıktı shape'ini, receptive field'ı ve parametre sayısını raporla
version: 1.0.0
phase: 4
lesson: 2
tags: [computer-vision, cnn, architecture, debugging]
---

# Conv Shape Calculator

Bir CNN planlamak ya da hata ayıklamak için deterministik yardımcı. Girdi shape'i ve katman spec listesi verildiğinde, modeli çalıştırmadan shape'leri, receptive field'ları ve parametre sayılarını izle.

## Ne zaman kullan

- Yeni bir CNN tasarlıyorsun ve her downsample'ın temiz bir boyuta düştüğünü doğrulamak istiyorsun.
- Bir paper okuyorsun ve mimari tablosunu koda çeviriyorsun.
- Bir pretrained backbone classifier head'inde shape mismatch ile çöküyor ve hangi katmanın spatial size'ı değiştirdiğini bilmen gerekiyor.
- İki backbone'u parametre verimliliği açısından, hiçbirini eğitmeden karşılaştırıyorsun.

## Girdiler

- `input_shape`: `(C, H, W)`.
- `layers`: sıralı katman dict listesi. Her biri şunları destekler:
  - `{type: "conv", c_out, k, s, p, groups=1, bias=true}`
  - `{type: "pool", mode: "max"|"avg", k, s, p=0}`
  - `{type: "adaptive_pool", out_h, out_w}`
  - `{type: "flatten"}`
  - `{type: "linear", out_features, bias=true}`

## Adımlar

1. **Trace'i başlat**: `(C, H, W)`, receptive field `1`, effective stride `1`, kümülatif params `0`.

2. **Her katman için** şu sırayla güncelle:
   - `C_out`'u hesapla (conv/linear) ya da `C_in`'i taşı (pool).
   - Spatial çıktıyı hesapla: conv ve pool için `(H + 2P - K) / S + 1`, adaptive pool için `out_h/out_w`, flatten çıktı shape'i için linear öncesi `(C * H * W, 1, 1)` olarak `(1, 1)`, linear için skaler `1x1`.
   - Receptive field ve effective stride'ı güncelle:
     - Conv/pool: `RF_new = RF_old + (K - 1) * effective_stride`, `effective_stride *= S`.
     - Adaptive pool: effective `S = H_in / out_h` (aşağı yuvarla) olan bir pool gibi davran. `RF_new = RF_old + (H_in - 1) * effective_stride_old`; `effective_stride *= S`. Adaptive pool'un RF'sinin tüm önceki spatial extent'e eşit olduğuna dikkat et.
     - Flatten / linear: RF ve effective stride artık anlamlı değil; flatten öncesi değerlerde dondur ve sonraki satırlarda gösterme.
   - Params'ı hesapla:
     - Conv: `C_out * (C_in / groups) * K * K + (bias ise C_out yoksa 0)`.
     - Linear: `out_features * in_features + (bias ise out_features yoksa 0)`.
     - Pool ve flatten: 0.

3. **Problemleri tespit et** ve işaretle:
   - Tam sayı olmayan çıktı boyutu (yanlış hizalanmış stride/padding).
   - Stack sonu öncesi `H_out <= 0`.
   - Receptive field'ın girdi boyutunu aşması (o noktadan sonra boşa giden compute olabilir).
   - Katman başına params'ta yanlış kanal planına işaret eden ani 10x sıçramalar.

4. **Tek bir tabloyla raporla**:

```
idx  layer                C_in  C_out  K  S  P  H_out  W_out  RF    params     cum_params
1    conv 3x3 s=1 p=1     3     32     3  1  1  224    224    3     896        896
2    conv 3x3 s=2 p=1     32    64     3  2  1  112    112    7     18,496     19,392
3    pool max 2x2         64    64     2  2  0  56     56     11    0          19,392
...
```

5. **Özet satırı**: final `(C, H, W)`, final receptive field, toplam params, uyarılar.

## Kurallar

- Spatial boyutlar için her zaman tam sayı döndür. Formül tam sayı üretmezse hata olarak işaretle, sessizce floor alma.
- `groups > 1` olduğunda `C_in % groups == 0` ve `C_out % groups == 0` doğrula; aksi halde hata.
- Depthwise conv (`groups == C_in`) için `layer` kolonunda etiketle ki okuyan paramsların neden düşük olduğunu görsün.
- Kullanıcı BatchNorm ya da aktivasyon katmanı verirse, shape açısından yok say ama params'ı taşı (BatchNorm başına `2 * C`).
- Eksik alanlar için varsayılan tahmin etme. Her conv ve pool'da `k`, `s`, `p` zorunlu.
