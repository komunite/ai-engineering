---
name: skill-linear-probe-runner
description: Herhangi bir dondurulmuş encoder ve etiketli dataset için tam linear-probe değerlendirmesini yaz
version: 1.0.0
phase: 4
lesson: 17
tags: [self-supervised, evaluation, linear-probe, pytorch]
---

# Linear Probe Runner

Üstüne tek bir lineer sınıflandırıcı eğiterek dondurulmuş bir encoder'ın feature'larını değerlendir. Her self-supervised paper için standart değerlendirme.

## Ne zaman kullan

- Self-supervised checkpoint'leri karşılaştırırken.
- Pretraining epoch'larına göre feature kalitesini izlerken.
- Aşağı akış görevi için fine-tune olmadan pretrained encoder'ın yeterince iyi olup olmadığına karar verirken.

## Girdiler

- `encoder`: görsel başına sabit boyutta feature döndüren dondurulmuş `nn.Module`.
- `feature_dim`: encoder çıktısının boyutu.
- `train_dataset`: etiketli dataset (image, class_id).
- `val_dataset`: ayrılmış set.
- `num_classes`: görev sınıfları.
- `epochs`: ImageNet ölçeği için tipik 100, daha küçük dataset'ler için 50.

## Adımlar

1. Encoder'ı eval moduna al ve her parametrede `requires_grad=False`.
2. Train ve val setlerini bir kez feature çıkar. numpy array ya da memory-mapped dosya olarak sakla.
3. Cached feature'lar üzerinde SGD + cosine schedule ile bir `nn.Linear(feature_dim, num_classes)` eğit.
4. Standart hyperparameter'lar: `lr=0.1`, `momentum=0.9`, `weight_decay=0`, `batch_size=1024`. Linear probe `lr`'ye şaşırtıcı derecede hassas — accuracy kötüyse sweep et.
5. Eğitim sonunda val'da top-1 accuracy raporla.

## Çıktı şablonu

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.optim import SGD
from torch.optim.lr_scheduler import CosineAnnealingLR

def extract(encoder, loader, device="cpu"):
    encoder.eval()
    feats, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            f = encoder(x.to(device)).cpu()
            feats.append(f)
            labels.append(y)
    return torch.cat(feats), torch.cat(labels)


def linear_probe(encoder, feature_dim, train_loader, val_loader,
                 num_classes, epochs=50, lr=0.1, device="cpu"):
    for p in encoder.parameters():
        p.requires_grad = False

    f_train, y_train = extract(encoder, train_loader, device)
    f_val, y_val = extract(encoder, val_loader, device)

    head = nn.Linear(feature_dim, num_classes).to(device)
    opt = SGD(head.parameters(), lr=lr, momentum=0.9, weight_decay=0)
    sched = CosineAnnealingLR(opt, T_max=epochs)

    ds = torch.utils.data.TensorDataset(f_train, y_train)
    train_iter = DataLoader(ds, batch_size=1024, shuffle=True)

    best_val = 0.0
    for ep in range(epochs):
        head.train()
        for x, y in train_iter:
            x, y = x.to(device), y.to(device)
            loss = F.cross_entropy(head(x), y)
            opt.zero_grad(); loss.backward(); opt.step()
        sched.step()

        head.eval()
        with torch.no_grad():
            acc = (head(f_val.to(device)).argmax(-1).cpu() == y_val).float().mean().item()
        best_val = max(best_val, acc)
    return best_val
```

## Rapor

```
[linear probe]
  encoder:     <name + pretrain checkpoint>
  feature_dim: <int>
  epochs:      <int>
  best_val_top1: <float>
```

## Kurallar

- Linear probe sırasında encoder ağırlıklarını asla güncelleme; o probe değil fine-tune olur.
- Feature'ları bir kez önceden hesapla; encoder'ı her epoch'ta yeniden eğitmek 100x compute israfıdır.
- Cosine schedule ve weight decay olmadan SGD kullan; Adam burada bazen yetersiz performans gösterir.
- Encoder ailesi başına en az bir kez learning rate sweep et; optimum SSL metodları arasında değişir.
