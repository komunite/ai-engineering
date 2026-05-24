---
name: 3d-pipeline
description: Girdi tipi, çıktı formatı ve kullanım durumu verildiğinde bir 3D üretim ya da yeniden inşa pipeline'ı seç.
version: 1.0.0
phase: 8
lesson: 12
tags: [3d, gaussian-splatting, nerf, mesh]
---

Girdiler (metin prompt'u / tek görsel / birkaç görsel / fotoğraf çekimi / video), hedef çıktı (mesh / Gaussian splat / NeRF / point cloud) ve kullanım durumu (gerçek-zamanlı render, game engine, AR / VR, sinematik) verildiğinde, şunu çıkar:

1. Pipeline. (a) Multi-view diffusion + 3D fit (SV3D, CAT3D + 3DGS), (b) doğrudan tek-shot (LRM, TripoSR, InstantMesh), (c) PBR ile text-to-mesh (Meshy 4, Rodin Gen-1.5, Hunyuan3D 2.0), (d) fotoğraf çekimi + 3DGS (Gsplat, Postshot, Scaniverse).
2. Base model + hosting. İsimlendirilmiş model + open / hosted. Ticari kullanım için lisans uygunluğunu dahil et.
3. Iterasyon bütçesi. İlk çıktıya beklenen süre, iterasyon maliyeti, refinement stratejisi.
4. Topology + materyaller. Remesh geçişi gerekli mi? PBR channel gereksinimleri (albedo, roughness, metallic, normal)? UV layout otomatik mı manuel mi?
5. Değerlendirme. Tutulan view'larda SSIM, CLIP skoru, mesh watertightness'ı, poly count, texture çözünürlüğü.
6. Platform hedefi. Unity / Unreal / Blender / web (three.js / Babylon) / AR (USDZ / glb).

Bir 3DGS'i mesh dönüşüm geçişi olmadan doğrudan bir game engine'e shipping reddet (çoğu engine splat'ları native olarak render etmez). Karmaşık eklemli karakterler için text-to-3D'yi reddet - bunun yerine rigging-aware pipeline kullan. Aşağı akış aracı NeRF'leri render edemiyorsa (çoğu DCC aracı) herhangi bir yalnızca-NeRF çıktısını flag'le.
