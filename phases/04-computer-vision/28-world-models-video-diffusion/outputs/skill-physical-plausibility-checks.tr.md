---
name: skill-physical-plausibility-checks
description: Ship etmeden önce üretilen herhangi bir videoda nesne kalıcılığı, yerçekimi ve devamlılık için otomatik kontroller
version: 1.0.0
phase: 4
lesson: 28
tags: [video-generation, quality, physics, evaluation]
---

# Physical Plausibility Checks

Üretilen videonun production deployment'ları otomatik guardrail gerektirir. İnsan incelemesi ölçeklenmez; fizik kontrolleri klasik failure mode'ları yakalar.

## Ne zaman kullan

- Metin ya da görsel prompt'lardan video üreten herhangi bir ürün.
- Bir video üretim API endpoint'inde QA otomatize ederken.
- Bir fine-tune ya da base model güncellemesi sonrası bir video modelinin kalite drift'ini izlerken.

## Girdiler

- `video`: bir `(T, H, W, 3)` tensor ya da bir mp4 path'i.
- Opsiyonel referans bilgisi: beklenen nesne sayısı, başlangıç sahne açıklaması.

## Kontroller

### 1. Nesne kalıcılığı
SAM 3.1 Object Multiplex ile her tespiti frame'ler arası izle. Kararlı bir track <=3 frame için kaybolup yeniden ortaya çıktığında işaretle — model nesneyi geçici olarak kaybetti. Bir nesne frame merkezi yakınında (kenarda değil) kaybolduğunda sert fail; kenarlarda soft fail.

### 2. Hareket pürüzsüzlüğü
Ardışık frame'ler arası optical flow çoğunlukla sürekli olmalı. Ani piksel başına flow zirveleri ışınlanmayı işaret eder. RAFT ile flow hesapla; 99. percentile flow büyüklüğü medyanı > 10 faktörü aşan frame'leri işaretle.

### 3. Yerçekimi / destek
Katı tespit edilen nesneler (yiyecek, top, alet) için, kaldırma aksiyonu yokken dikey konumunun azalmadığını kontrol et. Nesne yakınında "kavrayan el" tespit edilmediği sürece yukarı drift'i işaretle.

### 4. Kimlik tutarlılığı
İnsanlar ya da karakterler için, frame'ler arası bir yüz tanıma embedding'i kullan. Kalıcı bir kimlik için cosine similarity 5-frame pencerelerinde > 0.8 kalmalı. Eşik altı karakterin morphing yaptığı anlamına gelir.

### 5. Eller ve uzuvlar
Bir poz tahmincisi çalıştır (Ders 21). Bir elin > 5 ya da < 4 görünür parmağı olan frame'leri işaretle; bir kolun frame'ler arası uzunluğunun iki katına çıktığı; uzuvların bir yüzey aracılığıyla vücutla kesiştiği yerleri.

### 6. Metin rendering'i (prompt metin istediyse)
Kullanıcı prompt'u tırnak içinde bir string içeriyorsa, üretilen frame'leri OCR et ve istenen string'e karşı CER hesapla. > %20 CER'i işaretle.

## Rapor

```
[plausibility]
  video frames:           <T>
  permanence violations:  <N>
  smoothness violations:  <N>
  gravity violations:     <N>
  identity drift:         <N of 5-frame windows>
  limb anomalies:         <N>
  OCR CER vs requested:   <float>

[verdict]
  ship | hold | reject

[samples for review]
  her başarısızlığın gerçekleştiği frame aralıkları
```

## Kurallar

- Tek bir kontrol üzerinde hard-block etme; skorları topla ve toplam anomaliler bir eşiği aştığında videoyu inceleme için tut.
- Kimlik drift'ini ve kalıcılık ihlallerini en yüksek ağırlıkla ağırlıkla — kullanıcılar onları ilk fark eder.
- Zaman içinde kontrol başına failure rate'leri logla; yükselen trend genellikle base model'in güncellendiği ya da prompt dağılımının kaydığı anlamına gelir.
- Flag'lenmiş videoyu asla silme; model debug ve post-mortem için sakla.
- Hassas içerik (insanlar, çocuklar, kamu figürleri) için, skordan bağımsız her videonun insan incelemesini zorunlu kıl.
