---
name: skill-3dgs-export-router
description: Aşağı akış viewer ya da engine verildiğinde doğru 3DGS export formatını (.ply / .splat / glTF KHR_gaussian_splatting / USD) seç
version: 1.0.0
phase: 4
lesson: 22
tags: [3d-gaussian-splatting, export, glTF, OpenUSD, pipeline]
---

# 3DGS Export Router

Bir aşağı akış hedefini doğru 3DGS dosya formatına eşle. Saatlerce "yüklenmiyor" debug'ından kurtarır.

## Ne zaman kullan

- Bir 3DGS sahnesini eğittikten sonra, bir content pipeline'a teslim etmeden önce.
- Araştırma kalitesi (.ply) ve production kalitesi (glTF / USD) formatları arasında seçim yaparken.
- Pipeline teslimi: çekim ekibi -> 3DGS mühendisi -> oyun tasarımcısı / VFX sanatçısı / web geliştirici.

## Girdiler

- `target_engine`: unreal | unity | omniverse | blender | vision_pro | three_js | babylon_js | cesium | playcanvas | supersplat
- `priority`: portability | file_size | quality_preservation
- `include_sh_degree`: 0 | 1 | 2 | 3

## Format kararı

| Hedef | Önerilen format | Neden |
|--------|--------------------|-----|
| Unreal Engine (sanal production) | Volinga plugin ya da glTF KHR_gaussian_splatting | Native Unreal SDK yolu |
| Unity (XR / oyun) | Aras-P Unity-GaussianSplatting plugin ile .ply | Community-standart Unity pipeline |
| NVIDIA Omniverse, Pixar araçları | OpenUSD 26.03 (UsdVolParticleField3DGaussianSplat) | Native USD prim tipi |
| Apple Vision Pro | OpenUSD 26.03 | visionOS 2.x'e native |
| Blender | .ply + KIRI Engine add-on | Community add-on ham splat okur |
| Three.js web viewer | glTF KHR_gaussian_splatting ya da .splat | Browser standart, `GaussianSplats3D` ile çalışır |
| Babylon.js V9+ | glTF KHR_gaussian_splatting | V9 native destek ekledi |
| Cesium (CesiumJS 1.139+, Cesium for Unreal 2.23+) | glTF KHR_gaussian_splatting | Açık destek ship etti |
| PlayCanvas | .splat | PlayCanvas native quantised format |
| SuperSplat (editor) | .ply ya da .splat | Import + export |

## Quantisation trade-off'ları

- `.ply` full-precision: en büyük dosya, lossless, herhangi viewer.
- `.splat`: 4x-8x daha küçük, SH3 katsayılarında hafif kalite kaybı, PlayCanvas-ekosistem standardı.
- glTF KHR: EXT_meshopt_compression ile yapılandırılabilir; en yüksek uyumlulukla en küçük.
- USD: USDZ paketleme ile sıkıştırılmış; Apple pipeline'ları için en küçük.

## Çıktı raporu

```
[export plan]
  target:         <engine>
  format:         <name>
  sh degree:      <0|1|2|3>
  compression:    <none|meshopt|quantisation|usdz>
  expected size:  <MB>
  compatible with: <list of viewers>

[pipeline]
  1. source: <eğitimden .ply>
  2. optional: SuperSplat cleanup pass
  3. convert: <tool + CLI or API call>
  4. package: <.gltf / .glb / .usd / .usdz / .splat / .ply>
  5. validate: <viewer sanity check>
```

## Kurallar

- SH3 katsayılarını asla sessizce çıkarma — specular yansımaları görünür şekilde değiştirir.
- `priority == file_size` ise, meshopt ile `.splat` ya da glTF öner; kalite kaybı konusunda uyar.
- Apple platformları için, 2026'da glTF yerine USD / USDZ tercih et; USDZ'nin first-class visionOS desteği var.
- Hedef viewer'ın 3DGS desteği pre-standard ise (Şubat 2026 öncesi), `.ply` ve viewer'ın özel loader'ını öner; Khronos-standardı glTF henüz tanınmayacak.
- Teslim etmeden önce export edilen dosyayı her zaman en az bir viewer'da doğrula; quantisation sırasında sessiz corruption olur.
