---
name: skill-freeze-inspector
description: Hangi parametrelerin trainable olduğunu, hangi BatchNorm katmanlarının eval modunda olduğunu ve optimizer'ın gerçekten trainable parametreleri tüketip tüketmediğini raporla
version: 1.0.0
phase: 4
lesson: 5
tags: [computer-vision, transfer-learning, debugging, pytorch]
---

# Freeze Inspector

Transfer learning bug'ları üç yerde saklanır: donmuş olması gereken ama olmayan parametreler, trainable olması gereken ama olmayan parametreler ve freeze state değişmeden önce kurulmuş optimizer'lar. Bu skill üçünü de tek geçişte yüzeye çıkarır.

## Ne zaman kullan

- Parametrelerin bir alt kümesine `requires_grad` ayarladıktan hemen sonra.
- Bir fine-tune turunun ilk eğitim adımından önce.
- `freeze_bn_stats` ya da BN modunu değiştiren herhangi bir yardımcıyı çağırdıktan sonra.
- Val accuracy random'da takıldığında ve hiçbir şeyin gerçekten eğitilmediğinden şüphelendiğinde.

## Girdiler

- `model`: bir PyTorch `nn.Module`.
- `optimizer`: eğitim için kullanılmak üzere olan optimizer.
- Opsiyonel `expected_frozen_prefixes`: dondurulmuş olması gereken parametre adı prefix listesi (örn. `["conv1", "bn1", "layer1"]`).

## Adımlar

1. **Parametreleri gez.** Her `(name, param)` için:
   - `requires_grad`'ı kaydet
   - `shape` ve `numel`'ı kaydet

2. **Modülleri gez.** Her modül için:
   - BatchNorm ise eval modunda olup olmadığını ve affine parametrelerinin trainable olup olmadığını kaydet.

3. **Optimizer'ı incele.** Her parametre grubu için:
   - `params`'ını `id(p)` setine düzleştir.
   - `requires_grad == True` olan tüm params'in `id(p)` setiyle karşılaştır.

4. **Dört failure mode'u tespit et:**
   - `leaked_train`: bir param `requires_grad=True` ama optimizer'da görünmüyor (gradient hesaplanıyor ama hiç uygulanmıyor).
   - `ghost_train`: bir param optimizer'da görünüyor ama `requires_grad=False` (optimizer state israfı; sonradan requires_grad'i tekrar açarsan bug'a da yol açabilir).
   - `bn_mismatch`: ya (a) bir BN katmanı train modunda (running stats biriktiriyor) ama affine parametreleri (`weight`, `bias`) donmuş, ya da (b) bir BN katmanı eval modunda (donmuş stats) ama affine parametreleri trainable. İki durum da tutarsız ve neredeyse her zaman bug.
   - `expected_vs_actual`: `expected_frozen_prefixes` içinde listelenen herhangi bir prefix hâlâ trainable parametreye sahip.

## Rapor

```
[freeze-inspector]
  model trainable params: <N>
  model frozen params:    <N>
  batchnorm layers in eval mode: <count>
  batchnorm layers in train mode: <count>

[optimizer coverage]
  trainable params fed to optimizer: <M> of <N>
  leaked_train: <list of names> (trainable but not in optimizer)
  ghost_train:  <list of names> (in optimizer but frozen)

[bn audit]
  mismatched layers: <list of names>

[expectations]
  expected_frozen_prefixes: <...>
  violating params:         <list>

[verdict]
  ok | <one-line summary of the most severe issue>
```

## Kurallar

- Sadece parametre adlarını raporla; ağırlıkların kendisini asla yazdırma.
- Her listeyi parametre adına göre alfabetik sırala.
- Optimizer kapsamı %100 ise ve uyumsuzluk yoksa `ok` dön ve dur.
- `leaked_train` için, freeze state değiştikten sonra optimizer'ı yeniden kurmayı her zaman öner.
- `ghost_train` için, niyet onu eğitmekse parametre grubunu kaldırmayı ya da `requires_grad=True` ayarlamayı öner.
