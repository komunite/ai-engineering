---
name: skill-classification-diagnostics
description: Bir confusion matrix ve sınıf adları verildiğinde, sınıf başına başarısızlıkları yüzeye çıkar ve en yüksek etkili tek düzeltmeyi öner
version: 1.0.0
phase: 4
lesson: 4
tags: [computer-vision, classification, evaluation, debugging]
---

# Classification Diagnostics

Confusion matrix'ler için bir okuma merceği. Toplam accuracy sana bir sınıflandırıcının çalıştığını söyler. Confusion matrix sana *henüz neyi bilmediğini* söyler.

## Ne zaman kullan

- Eğitilmiş bir sınıflandırıcının validation performansına ilk bakış.
- Eğitim turları arasında sırada neyi değiştireceğine karar verirken.
- Bir modeli ship etmeden önce: hiçbir kritik sınıfın sessizce başarısız olmadığını doğrulamak için.
- Toplam accuracy bir puan düştüğü ve nedenini bilmen gereken bir production regression'ı ayıklarken.

## Girdiler

- `cm`: CxC confusion matrix (satırlar = true, kolonlar = predicted).
- `labels`: aynı sırada C sınıf adının listesi.
- Opsiyonel `class_priors`: sınıf başına eğitim frekansı (varsayılan `cm`'nin satır toplamları).

## Adımlar

1. **Sınıf başına metrikleri hesapla.** Sıfıra bölmeyi o sınıf için metriğin tanımsız olması olarak ele al ve `n/a` olarak raporla; asla sessizce 0 ile değiştirme.
   - precision_i = cm[i,i] / sum(cm[:, i])   (sınıf hiç tahmin edilmediyse tanımsız)
   - recall_i    = cm[i,i] / sum(cm[i, :])   (sınıfın ground-truth örneği yoksa tanımsız)
   - f1_i        = 2 * p * r / (p + r)        (bileşenlerden biri tanımsızsa tanımsız)

2. **F1'e göre en kötü üç sınıfa kadar sırala.** Confusion matrix üçten az sınıfa sahipse, kaç tane varsa o kadar sırala. Tüm metrikleri tanımsız olan sınıfları hariç tut.

3. **Satır başına en üst diagonal-dışı hücreyi bul** — bu sınıftan en sık çalan tek sınıf. `true -> predicted` olarak raporla.

4. **En kötü her sınıf için failure mode'u sınıflandır.** Etiketin tekrarlanabilir olması için şu nicel eşikleri kullan:
   - `ambiguity` — başka bir sınıfla iki yönlü karışıklık: hem `cm[i,j] / sum(cm[i, :]) >= 0.15` hem de `cm[j,i] / sum(cm[j, :]) >= 0.15`.
   - `imbalance` — sınıfın eğitim sayısı en sık karıştığı sınıfın `< 0.5x`'i.
   - `label_noise` — `|precision_i - recall_i| >= 0.2` ve sınıf imbalance / ambiguity yollarında değil.
   - `systematic` — tek bir karıştırıcı bu sınıfın hatalarının 0.2 payını aşmıyor; hatalar üç ya da daha çok diğer sınıfa yayılıyor.

5. **En yüksek etkili tek sonraki aksiyonu öner**:
   - `ambiguity` -> ayırt edici örnekler topla ya da sentezle, ayırt edici özelliği koruyan hedefli augmentation ekle.
   - `imbalance` -> azınlık sınıfını oversample et ya da class-weighted loss uygula.
   - `label_noise` -> sınıfın stratified bir örneğini denetle; başka değişiklik yapmadan yanlış etiketleri düzelt.
   - `systematic` -> sınıf için veri arttır ya da bu sınıfın loss'una daha yüksek ağırlıkla fine-tune et.

## Rapor

```
[diagnostics]
  aggregate accuracy: X.XX
  macro F1:           X.XX

[top-3 worst classes]
  1. class <name>  F1 = X.XX  prec = X.XX  rec = X.XX
     top confusion: <name> -> <other>  (N cases)
     failure mode:  ambiguity | imbalance | label_noise | systematic
     action:        <one sentence>

  2. ...
  3. ...

[recommendation]
  single biggest lever: <one sentence naming the class and the fix>
```

## Kurallar

- En fazla üç sınıf döndür. Daha çoğu sinyali gizler.
- En kötü her sınıf için baskın karıştırıcıyı adlandır; asla "çoğuyla karışıyor" diye özetleme.
- Her öneriyi confusion matrix kanıtına dayandır. Hangi sınıfı belirtmeden genel "daha çok veri ekle" yok.
- Precision ve recall 0.2'den fazla uyuşmuyorsa, her zaman label noise'u aday olarak işaretle — gerçek sınıflar eğitimden sonra genellikle hizalı P ve R'ye sahiptir.
