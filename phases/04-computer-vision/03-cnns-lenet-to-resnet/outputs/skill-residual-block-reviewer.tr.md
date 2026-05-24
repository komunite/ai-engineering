---
name: skill-residual-block-reviewer
description: Bir PyTorch residual bloğunu skip connection doğruluğu, BN konumu, aktivasyon sırası ve shape hizalama açısından incele
version: 1.0.0
phase: 4
lesson: 3
tags: [computer-vision, resnet, code-review, pytorch]
---

# Residual Block Reviewer

Bir residual blok implement ettiğini iddia eden herhangi bir PyTorch `nn.Module` için odaklı reviewer. Hemen her bozuk ResNet yeniden yazımının nedenini oluşturan dört hatayı yakalar.

## Ne zaman kullan

- Biri özel bir BasicBlock ya da Bottleneck yazdı ve loss NaN ya da accuracy takılı.
- Bir bloğu bir framework'ten diğerine taşıyorsun ve eşdeğerliği doğrulamak istiyorsun.
- ResNet iç yapılarını değiştiren bir PR'ı inceliyorsun (pre-activation, squeeze-excite, anti-alias).
- Bir model CIFAR boyutunda girdide sorunsuz ship oluyor ama shortcut yanlış olduğu için ImageNet çözünürlüğünde çöküyor.

## Girdiler

- Bir PyTorch class tanımı, ya kaynak metin olarak ya da import edilebilir bir path.
- Opsiyonel `variant`: `basic` | `bottleneck` | `preact` | `seblock`.

## Dört kontrol

### 1. Shortcut shape hizalaması

`stride != 1` ya da `in_channels != out_channels` olan herhangi bir blok için, shortcut yolu **mutlaka** shape eşleyen bir modül olmalı — tipik olarak 1x1 conv artı BN. Bu durumda çıplak bir `nn.Identity()` forward time'da garantili bir shape mismatch hatasıdır.

Teşhis:
```
[shortcut]
  detected:  nn.Identity | 1x1 Conv + BN | 1x1 Conv + BN + ReLU | other
  required:  shape-matching Conv if (stride != 1 or in_c != out_c) else Identity
  verdict:   ok | wrong | unnecessarily heavy
```

### 2. BN'in toplama göre konumu

`out + shortcut(x)` toplaması **son** ReLU'dan **önce** olmalı (post-activation, orijinal ResNet) ya da son ReLU tamamen yok olmalı (pre-activation ResNet v2). Ana branch'te ReLU uygulayıp sonra ham bir shortcut ekleyen bir blok, eğitime zarar veren asimetrik bir aktivasyon aralığı üretir.

Teşhis:
```
[activation order]
  pattern:  post-act (conv-BN-ReLU-conv-BN-add-ReLU) | pre-act (BN-ReLU-conv-BN-ReLU-conv-add) | other
  verdict:  ok | suspect
```

### 3. Conv katmanlarında bias

Hemen ardından BatchNorm gelen conv'ların `bias=False` olmalı. BN'nin beta'sı zaten bias'ı parametrize ediyor, dolayısıyla ekstra bir conv bias parametre israfı yapar ve yakınsamayı yavaşlatabilir.

Teşhis:
```
[bias]
  convs with BN and bias=True: <count>
  recommended fix: set bias=False on those layers
```

### 4. In-place ReLU ve autograd

Shortcut'a eklenecek tensor üzerindeki `nn.ReLU(inplace=True)`, residual toplaması için hâlâ ihtiyaç duyulabilecek değerlerin üzerine yazar. Toplama öncesi yeni bir tensor üreten bir katman tarafından takip edilmeyen herhangi bir `inplace=True`'yu işaretle.

Teşhis:
```
[in-place]
  risky inplace ops: <list>
  fix: inplace=False before the residual add
```

## Rapor

```
[block-review]
  variant:       basic | bottleneck | preact | se | other
  shortcut:      ok | wrong | heavy
  activation:    ok | suspect
  bias-bn:       ok | <N> convs need bias=False
  in-place:      ok | <N> risky ops
  summary:       one sentence
```

## Kurallar

- Bloğu yeniden yazma. Sadece raporla.
- Blok doğruysa, her yerde `ok` de ve dur. Öneri yok.
- Birden çok şey yanlışsa, yukarıdaki sırayla listele (shortcut ilk çünkü en sık çökme sebebi o).
- Kullanıcı belirtmişse bilinçli bir pre-activation ya da squeeze-excite varyantını asla yanlış olarak işaretleme.
