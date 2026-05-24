---
name: skill-debug-checklist
description: Sinir ağı eğitim arızalarını hata ayıklamak için karar ağacı checklist'i
version: 1.0.0
phase: 3
lesson: 13
tags: [debugging, neural-networks, training, diagnostics, deep-learning]
---

# Sinir Ağı Debug Checklist'i

Eğitim ters gittiğinde sistematik hata ayıklama protokolü. Sırayla ilerle — bug'ların çoğu ilk 3 adımda yakalanır.

## Eğitim öncesi (bug'ları önle)

1. Model mimarisini ve parametre sayısını yazdır. Veri için boyut mantıklı mı?
2. Random girdiyle tek bir forward pass çalıştır. Çıktı shape'i hedef shape ile uyuşuyor mu?
3. Etiketlerin doğru dtype olduğunu kontrol et (CrossEntropyLoss Long ister, BCELoss Float ister)
4. Veri normalizasyonunu doğrula: girdilerin ortalaması 0'a, std'si 1'e yakın olmalı
5. 5 random (girdi, etiket) çiftini yazdır. Etiketler beklediğine uyuyor mu?
6. Train/test split'inde duplicate örnek olmadığını teyit et

## Tek-batch overfit testi (60 saniye, bug'ların %80'ini yakalar)

1. Eğitim setinden 8-32 örnek al
2. Makul bir learning rate ile 200 adım eğit
3. Loss 0'a yaklaşmalı. Eğitim doğruluğu %100'e ulaşmalı
4. Başarısız olursa: bug modelinde, loss fonksiyonunda ya da eğitim döngüsünde — veride ya da hyperparameter'larda değil
5. Geçerse: tam eğitime devam et

## Loss azalmıyor

1. Learning rate'i kontrol et. 3 değer dene: current/10, current, current*10
2. Katman başına gradient norm'larını yazdır. Hepsi sıfırsa ölü ağ ya da detach edilmiş graph
3. Parametrelerde `requires_grad=True` kontrol et. `loss.backward()` çağrıldığını teyit et
4. `loss.backward()` öncesi `optimizer.zero_grad()` çağrıldığını kontrol et
5. `loss.backward()` sonrası `optimizer.step()` çağrıldığını kontrol et
6. Model parametrelerinin optimizer'a geçildiğini doğrula: `optimizer = Adam(model.parameters())`

## Loss NaN ya da Inf

1. Learning rate'i 10x düşür
2. Tüm log() çağrılarına epsilon ekle: `torch.log(x + 1e-7)`
3. Tüm bölmelere epsilon ekle: `x / (y + 1e-8)`
4. Tahminleri clamp et: BCE loss öncesi `torch.clamp(pred, 1e-7, 1 - 1e-7)`
5. Operasyonu tam yerinde bulmak için `torch.autograd.detect_anomaly()` kullan
6. Girdi verisinde NaN kontrol et: `assert not torch.isnan(x).any()`

## Loss salınıyor

1. Learning rate'i 3-10x düşür
2. Batch size'ı arttır (gradient gürültüsünü düşürür)
3. Gradient clipping ekle: `torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)`
4. SGD'den Adam'a geç (parametre başına adaptif LR)
5. Eğitimin ilk %5-10'u için learning rate warmup ekle

## Overfitting (train acc yüksek, test acc düşük)

1. Dropout ekle (p=0.1 ile başla, 0.5'e çıkar)
2. Optimizer'a weight decay ekle: `Adam(params, weight_decay=1e-4)`
3. Model boyutunu düşür (daha az katman ya da daha dar katmanlar)
4. Data augmentation ekle
5. Early stopping kullan: validation loss 5+ epoch artarsa dur
6. Train ve test setleri arasında data leakage kontrol et

## Underfitting (hem train hem test acc düşük)

1. Model kapasitesini arttır (daha fazla katman, daha geniş katmanlar)
2. Daha fazla epoch eğit
3. Learning rate'i arttır (dikkatli)
4. Modelin öğrenebildiğini doğrulamak için regularization'ı geçici kaldır
5. Modelin görev için yeterince ifade gücü olduğunu kontrol et

## Dead ReLU nöronları

1. Katman başına sıfır aktivasyon oranını kontrol et. %50'den fazla problemli
2. LeakyReLU(0.01) ya da GELU'ya geç
3. Ağırlıklar için Kaiming initialization kullan
4. Learning rate'i düşür (büyük güncellemeler nöronları ölü bölgeye itebilir)
5. Aktivasyon fonksiyonlarından önce batch normalization ekle

## Hızlı referans: learning rate başlangıç noktaları

| Optimizer | Görev | Başlangıç LR |
|-----------|-------|--------------|
| Adam | Sıfırdan eğitim | 1e-3 |
| Adam | Pre-trained fine-tune | 1e-5 |
| SGD + momentum | Sıfırdan eğitim | 1e-1 |
| SGD + momentum | Pre-trained fine-tune | 1e-3 |
| AdamW | Transformer eğitimi | 3e-4 |

## Hızlı referans: batch size etkileri

| Batch size | Gradient gürültüsü | Bellek | Genelleştirme |
|------------|-------------------|--------|---------------|
| 8-16 | Yüksek (gürültülü) | Düşük | Sıklıkla daha iyi |
| 32-64 | Orta | Orta | İyi varsayılan |
| 128-256 | Düşük (yumuşak) | Yüksek | Warmup isteyebilir |
| 512+ | Çok düşük | Çok yüksek | LR ölçekleme ister |

## Hiçbir şey işe yaramayınca

1. Modeli 1 hidden layer'a sadeleştir. Öğreniyor mu?
2. Veriyi 100 örneğe sadeleştir. Overfit ediyor mu?
3. Loss'u MSE ile değiştir. Yakınsıyor mu?
4. Optimizer'ı SGD(lr=0.01) ile değiştir. İlerleme yapıyor mu?
5. Veriyi sentetik veri ile değiştir (örn. y = x[0] > 0). Öğreniyor mu?
6. Bunların hiçbiri işe yaramazsa: bug bakmadığın kodda (veri yükleme, ön işleme, tensor shape'leri)
