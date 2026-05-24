---
name: skill-pytorch-patterns
description: PyTorch eğitim, değerlendirme ve deployment için referans pattern'ler
version: 1.0.0
phase: 03
lesson: 11
tags: [pytorch, training, deep-learning, gpu, patterns]
---

## Kanonik Eğitim Döngüsü

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = Model().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

for epoch in range(num_epochs):
    model.train()
    for inputs, targets in train_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

    model.eval()
    with torch.no_grad():
        for inputs, targets in val_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
```

## Mixed Precision Eğitim

```python
from torch.amp import autocast, GradScaler

scaler = GradScaler()
for inputs, targets in train_loader:
    inputs, targets = inputs.to(device), targets.to(device)
    optimizer.zero_grad()
    with autocast(device_type="cuda"):
        outputs = model(inputs)
        loss = criterion(outputs, targets)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

Şunda kullan: float16 destekli donanımlı GPU'da (V100, A100, H100, RTX 3090+) eğitim. ~1.5-2x hızlanma ve ~%50 bellek azalması bekle.

## Gradient Accumulation

```python
accumulation_steps = 4
optimizer.zero_grad()
for i, (inputs, targets) in enumerate(train_loader):
    inputs, targets = inputs.to(device), targets.to(device)
    outputs = model(inputs)
    loss = criterion(outputs, targets) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

Şunda kullan: efektif batch size'ın GPU belleğinin izin verdiğinden büyük olması gerektiğinde. Loss'u accumulation_steps'e bölmek gradient ölçeğini tutarlı tutar.

## Kaydet ve Yükle

```python
torch.save({
    "epoch": epoch,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "loss": loss.item(),
}, "checkpoint.pt")

checkpoint = torch.load("checkpoint.pt", weights_only=True)
model.load_state_dict(checkpoint["model_state_dict"])
optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
```

Eğitime devam etmek için optimizer state'ini her zaman kaydet. Sadece inference için yalnızca `model.state_dict()` kaydet.

## Custom Dataset

```python
class CustomDataset(torch.utils.data.Dataset):
    def __init__(self, data_dir, transform=None):
        self.samples = self._load_samples(data_dir)
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y = self.samples[idx]
        if self.transform:
            x = self.transform(x)
        return x, y

    def _load_samples(self, data_dir):
        ...
```

## DataLoader Konfigürasyonu

```python
train_loader = torch.utils.data.DataLoader(
    dataset,
    batch_size=64,
    shuffle=True,
    num_workers=4,
    pin_memory=True,
    drop_last=True,
    persistent_workers=True,
)
```

| Parametre | Ne yapar | Ne zaman kullan |
|-----------|----------|-----------------|
| num_workers=4 | Paralel veri yükleme | Çok çekirdekli makinelerde her zaman |
| pin_memory=True | Page-locked CPU belleği | GPU'da eğitirken |
| drop_last=True | Son eksik batch'i at | BatchNorm kullanırken |
| persistent_workers=True | Worker'ları epoch'lar arası canlı tut | num_workers > 0 iken |

## Learning Rate Schedule'ları

```python
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer,
    max_lr=1e-3,
    total_steps=num_epochs * len(train_loader),
    pct_start=0.1,
)

for epoch in range(num_epochs):
    for inputs, targets in train_loader:
        ...
        optimizer.step()
        scheduler.step()
```

OneCycleLR: çoğu görev için en iyi varsayılan. max_lr'ye warmup yapar, sonra cosine decay eder. `scheduler.step()`'i her epoch sonrası değil, her batch sonrası çağır.

## Weight Initialization

```python
def init_weights(module):
    if isinstance(module, nn.Linear):
        nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    elif isinstance(module, nn.Conv2d):
        nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")

model.apply(init_weights)
```

## Inference Modu

```python
model.eval()

with torch.inference_mode():
    outputs = model(inputs)
```

`torch.inference_mode()` `torch.no_grad()`'den daha hızlıdır çünkü sadece gradient hesaplamasını bastırmak yerine autograd'ı tamamen devre dışı bırakır.

## Sık Yapılan Hatalar Checklist'i

1. CrossEntropyLoss öncesi softmax uygulamak (içeride log_softmax barındırır)
2. Validation sırasında model.eval() çağırmayı unutmak
3. Tensor'ları model ile aynı cihaza taşımayı unutmak
4. optimizer.zero_grad() çağırmamak (gradient'ler default birikir)
5. Eğitim sırasında torch.no_grad() kullanmak (gradient hesaplamasını kapatır)
6. num_workers'ı çok yüksek ayarlamak (çok fazla process spawn eder, belleği zorlar)
7. GPU'da eğitirken pin_memory=True kullanmamak
8. state_dict yerine tüm model nesnesini kaydetmek (refactor'da kırılır)
