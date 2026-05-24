---
name: prompt-alignment-method-selector
description: Kullanım senaryon için doğru alignment yöntemini seç (SFT, RLHF, DPO, KTO, ORPO, SimPO)
version: 1.0.0
phase: 10
lesson: 8
tags: [alignment, dpo, rlhf, kto, orpo, simpo, preference-optimization, fine-tuning]
---

# Alignment Yöntem Seçici

Bir dil modeli için alignment yöntemi seçerken, verini, compute'unu ve kalite gereksinimlerini değerlendirmek için bu çerçeveyi kullan, sonra kısıtlamalarına en uygun yöntemi seç.

## Girdi Gereksinimleri

Şunu sağla:
- **Base model** (örn. Llama 3 8B, Mistral 7B, Qwen 2.5 72B)
- **Başlangıç noktası** (base model veya zaten SFT yapılmış mı?)
- **Mevcut veri** (instruction çiftleri, preference çiftleri, eşleştirilmemiş puanlar veya hiçbiri)
- **Compute bütçesi** (GPU saati, GPU sayısı)
- **Kalite hedefi** (prototip için yeterli, açık kaynakla rekabetçi, state-of-the-art)
- **Zaman çizelgesi** (gün, hafta, ay)

## Karar Matrisi

### Hızlı Seçim

| Durumun | Önerilen Yöntem | Neden |
|---------------|-------------------|-----|
| Preference verisi yok, sadece instruction çiftleri | Yalnızca SFT | Preference sinyali olmadan alignment yapamazsın |
| < 5000 preference çifti, sınırlı compute | DPO | Daha basit pipeline, küçük veriyle iyi çalışır |
| Eşleştirilmemiş feedback (sadece thumbs up/down) | KTO | Pairwise karşılaştırma olmadan çalışan tek yöntem |
| Tek eğitim koşusunda alignment istiyorsun | ORPO | SFT + alignment'ı birleştirir, reference model yok |
| Bellek kısıtlı (reference model sığmıyor) | SimPO | Reference model gerekmez |
| Büyük ölçekli, çok amaçlı alignment | RLHF (PPO) | Ayrı reward model karmaşık preference'ları yakalar |
| Online veriyle iteratif alignment | RLHF (PPO) | Bir döngüde üret, puanla ve yeniden eğit |
| RLHF sonrası iyileştirme | DPO | Hedefli preference üzerinde RLHF modelini fine-tune et |

### Detaylı Karşılaştırma

| Yöntem | Veri Gereksinimi | Bellekteki Model | Eğitim Döngüsü | İstikrar | En İyi Ölçek |
|--------|-----------------|-----------------|----------------|-----------|------------|
| SFT | Instruction çiftleri (10K+) | 1 | 1 | Yüksek | Herhangi |
| RLHF | Preference çiftleri (20K+) | 3-4 | 3 | Düşük | Büyük (70B+) |
| DPO | Preference çiftleri (5K+) | 2 | 2 (SFT + DPO) | Yüksek | Küçük-Orta (7B-70B) |
| KTO | Eşleştirilmemiş puanlar (5K+) | 2 | 2 (SFT + KTO) | Yüksek | Herhangi |
| ORPO | Preference çiftleri (10K+) | 1 | 1 | Yüksek | Küçük-Orta |
| SimPO | Preference çiftleri (5K+) | 1 | 2 (SFT + SimPO) | Yüksek | Küçük-Orta |

## Yönteme Özgü Konfigürasyon

### SFT

- **Ne zaman dur**: 1-3 epoch sonrası veya validation loss düşmeyi bıraktığında
- **Anahtar hiperparametre**: Learning rate (1e-5 - 5e-5, büyük modeller için düşük)
- **Kritik detay**: Loss'ta instruction token'larını maskele
- **Tuzak**: 3'ten fazla epoch ezberlemeye yol açar; %2-5 pretraining verisi karıştır

### RLHF (PPO)

- **Ne zaman kullan**: 20K+ karşılaştırma çiftin var, çok amaçlı alignment gerekiyor veya iteratif online learning istiyorsun
- **Anahtar hiperparametreler**: KL katsayısı (0.01-0.05), PPO clip oranı (0.1-0.3), learning rate (5e-6 - 3e-5)
- **Kritik detay**: Reward model >= policy model boyutu olmalı
- **Tuzak**: PPO istikrarsız; KL divergence ve reward eğrilerini sürekli izle

### DPO

- **Ne zaman kullan**: Preference çiftlerin var ve RLHF'den daha basit pipeline istiyorsun
- **Anahtar hiperparametre**: Beta (0.1-0.5; düşük = reference'tan daha fazla sapmaya izin verir)
- **Kritik detay**: Reference model, SFT checkpoint'in dondurulmuş kopyası olmalı
- **Tuzak**: Beta'ya çok hassas; [0.05, 0.1, 0.2, 0.5] üzerinde sweep çalıştır

### KTO

- **Ne zaman kullan**: Pairwise karşılaştırma olmadan sadece "iyi" veya "kötü" etiketlerin var
- **Anahtar hiperparametre**: Beta (DPO ile aynı), loss aversion çarpanı (kötü yanıtlarda 1.5x)
- **Kritik detay**: Kabaca dengeli iyi/kötü örnek gerekir (%40-60 dağılımı)
- **Tuzak**: Çiftler olmadan gradient sinyali daha zayıf; DPO'dan daha fazla veri gerekebilir

### ORPO

- **Ne zaman kullan**: SFT'yi tamamen atlayıp base'den doğrudan aligned'a gitmek istiyorsun
- **Anahtar hiperparametre**: Lambda (preference teriminin SFT terimine göre ağırlığı)
- **Kritik detay**: Tek veri setinde hem instruction etiketleri HEM preference çiftleri gerekir
- **Tuzak**: Birleşik amaç dengelemesi zor olabilir; SFT loss baskınsa alignment zayıf

### SimPO

- **Ne zaman kullan**: Reference model tutamayacağın bellek kısıtlı kurulum
- **Anahtar hiperparametre**: Beta, gamma (length normalization exponent)
- **Kritik detay**: Length normalization modelin kısa yanıtları tercih etmesini önler
- **Tuzak**: Reference model çapası olmadan model daha fazla sapabilir; dikkatli izle

## Pipeline Template'leri

### Template 1: Hızlı Prototip (1-2 gün)

```
Base Model -> SFT (1 epoch, 10K örnek) -> DPO (3 epoch, 5K çift)
```

Compute: A100'de 7B model için ~4 GPU-saati
Kalite: Sağlam instruction takibi, temel preference alignment

### Template 2: Üretim Kalitesi (1-2 hafta)

```
Base Model -> SFT (2 epoch, 50K örnek) -> DPO (5 epoch, 20K çift) -> Eval -> Iterate
```

Compute: 7B için ~40 GPU-saati, 70B için ~200 GPU-saati
Kalite: Açık kaynak RLHF modelleriyle rekabetçi

### Template 3: State-of-the-Art (1-3 ay)

```
Base Model -> SFT (2 epoch, 100K+ örnek) -> RLHF (PPO, 50K+ çift) -> DPO (hedefli iyileştirme) -> Eval -> Iterate
```

Compute: 70B için ~500+ GPU-saati
Kalite: Frontier model alignment'a yaklaşan

### Template 4: Minimal Veri (1-2 gün)

```
Base Model -> SFT (1 epoch, 5K örnek) -> KTO (kullanıcılardan eşleştirilmemiş thumbs up/down)
```

Compute: 7B için ~2 GPU-saati
Kalite: Minimal veri toplama yüküyle yalnızca SFT'den daha iyi

## Değerlendirme Protokolü

Alignment sonrası, şu boyutlarda değerlendir:

1. **Preference kazanma oranı**: 200+ test promptu üzerinde insan yargıçlarla aligned model vs SFT model karşılaştır. Hedef: > %60 kazanma oranı.
2. **Benchmark koruması**: MMLU, HumanEval veya domain'e özgü benchmark'lar. SFT baseline'dan > %5 düşmemeli.
3. **MT-Bench veya AlpacaEval**: Standart alignment kalite benchmark'ları. Yayımlanmış baseline'larla karşılaştır.
4. **Güvenlik değerlendirmesi**: Adversarial promptlara, jailbreak'lere ve zararlı istek kategorilerine karşı test et.
5. **Yanıt çeşitliliği**: 100 prompt üzerinde yanıtların entropisini ölç. Düşük entropy = mode collapse.

## Yaygın Başarısızlık Modları

| Belirti | Sebep | Yönteme Özgü Düzeltme |
|---------|-------|-------------------|
| Verbose, dolgulu yanıtlar | Reward model / implicit reward uzunluğu tercih ediyor | DPO: beta'yı artır. RLHF: uzunluk cezası ekle. SimPO: gamma'yı ayarla. |
| Model her şeye katılıyor | Preference veri önyargısından gelen sycophancy | Doğru yanıtın kullanıcıyla aynı fikirde olmadığı preference çiftleri ekle |
| Zararsız istekleri reddediyor | Güvenlik verisi üzerinde aşırı alignment | Güvenlik örnek oranını azalt, daha çok benign-refusal çifti ekle |
| Çıktılar SFT'ye neredeyse aynı | Beta fazla yüksek (DPO/KTO) veya KL katsayısı fazla yüksek (PPO) | Beta / KL katsayısını düşür; model öğrenmiyor |
| Eğitim loss salınıyor | Learning rate fazla yüksek veya yetersiz veri | lr'yi 2-3x azalt; preference verisini artır |
