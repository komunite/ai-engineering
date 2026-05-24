---
name: skill-vit-patch-and-pos-embed-inspector
description: Bir ViT'in patch embedding ve positional embedding shape'lerinin modelin beklediği dizi uzunluğuyla eşleştiğini doğrula
version: 1.0.0
phase: 4
lesson: 14
tags: [vision-transformer, debugging, pytorch]
---

# ViT Patch ve Positional Embedding Inspector

En yaygın ViT taşıma bug'ı: 224x224'te pretrained edilmiş bir checkpoint'i 384x384 için yapılandırılmış bir modele yüklemek (ya da tersi). Positional embedding yanlış dizi uzunluğuna sahiptir ve model sessizce çöp üretir.

## Ne zaman kullan

- Default olmayan bir çözünürlükte pretrained bir ViT'i fine-tune ederken.
- ViT-B/16 ile ViT-B/32 arası ağırlık taşımanın neden başarısız olduğunu denetlerken; inspector patch-size uyumsuzluğunu işaretler ki çağıran taşımayı zorlamak yerine mimariyi değiştirmesi gerektiğini bilsin.
- Hatasız yüklenen ama kötü eğitilen bir ViT'i ayıklarken.

## Girdiler

- `model`: instantiate edilmiş bir ViT `nn.Module`.
- `expected_image_size`: modelin production'da göreceği H x W.
- `patch_size`: beklenen patch size.

## Adımlar

1. Model içindeki patch embedding conv'u bul. `kernel_size`, `stride`, `in_channels`, `out_channels`'ını raporla.
2. Beklenen patch sayısını hesapla. Kare görsel için: `(image_size / patch_size)^2`. Dikdörtgen için: `(H / patch_size) * (W / patch_size)`. `H % patch_size == 0` ve `W % patch_size == 0` zorunlu; aksi halde işaretle ve reddet.
3. Öğrenilmiş positional embedding'i bul. Shape'ini `(1, N, dim)` raporla.
4. `N`'i `num_patches + 1` (CLS ile) ya da `num_patches` (CLS olmadan) ile karşılaştır. Uyumsuzluk checkpoint'in farklı bir çözünürlük ya da patch size'da pretrain edildiği anlamına gelir.
5. Patch conv'un `out_channels`'ının positional embedding'in `dim`'ine eşit olduğunu kontrol et.
6. Modelin yeni çözünürlükler için positional embedding'leri interpolate etmesi gerekiyorsa, interpolation yardımcısının var olduğunu doğrula (çoğu `timm` ViT'i bunu otomatik olarak `resize_pos_embed` ile yapar).

## Rapor

```
[vit-inspector]
  image_size:         HxW
  patch_size:         <int>
  num_patches (computed): <int>
  patch_conv:         k=<int>  s=<int>  in=<int>  out=<int>
  pos_embed shape:    (1, N, dim)
  has CLS token:      yes | no
  pos_embed N:        <int>    expected: <int>
  verdict:            ok | mismatch

[if mismatch]
  action:  reinitialise pos_embed for new sequence length
  tool:    timm.models.vision_transformer.resize_pos_embed
```

## Kurallar

- Uyarı vermeden asla sessizce interpolate etme; aksiyonu yüzeye çıkar ki kullanıcı pretrained positional yapının kaymış olabileceğini bilsin.
- Patch_size uyumsuzsa, interpolation önermeyi reddet — doğru mimariye geç.
- Modeli yerinde düzeltmeye çalışma; raporla ve öner.
