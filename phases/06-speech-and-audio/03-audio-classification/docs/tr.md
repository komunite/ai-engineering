# Ses Sınıflandırma — MFCC'ler Üzerinde k-NN'den AST ve BEATs'e

> "Köpek havlaması vs siren"den "bu hangi dil"e kadar her şey ses sınıflandırmadır. Öznitelikler mel'lerdir. Mimari her on yılda hareket eder. Değerlendirme AUC, F1 ve sınıf bazlı recall olarak kalır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar ve Mel), Faz 3 · 06 (CNN'ler), Faz 5 · 08 (Metin için CNN'ler ve RNN'ler)
**Süre:** ~75 dakika

## Sorun

10 saniyelik bir klip aldın. Bilmek istiyorsun: "bu ne?" Şehir sesi (siren, matkap, köpek), konuşma komutu (yes/no/stop), dil ID'si (en/es/ar), konuşmacı duygusu (kızgın/nötr) ya da çevresel ses (iç/dış, gürültü). Hepsi *ses sınıflandırma*dır ve 2026'da baseline mimari olgunlaşmıştır: log-mel → CNN ya da Transformer → softmax.

Temel zorluk ağ değildir. Veridir. Ses veri setlerinde acımasız sınıf dengesizliği, güçlü domain shift (temiz vs gürültülü) ve etiket gürültüsü vardır ("şehir gürültüsü" mü "restoran gürültüsü" mü olduğuna kim karar verdi?). Problemin %80'i CNN'i Transformer ile değiştirmek değil; küratörlük, augmentation ve değerlendirmedir.

## Kavram

![Ses sınıflandırma merdiveni: MFCC üzerinde k-NN, AST ve BEATs](../assets/audio-classification.svg)

**MFCC üzerinde k-NN (1990'ların baseline'ı).** Klip başına MFCC'leri düzleştir, etiketli bir bankaya kosinüs benzerliği hesapla, en üst K'nın çoğunluk oyunu döndür. Temiz, küçük veri setlerinde (Speech Commands, ESC-50) şaşırtıcı derecede güçlü. GPU olmadan çalışır.

**Log-mel üzerinde 2D CNN (2015-2019).** `(T, n_mels)` log-mel'i bir resim gibi ele al. ResNet-18 ya da VGG tarzı uygula. Zaman eksenini global mean pool. Sınıflar üzerinde softmax. 2026'da çoğu kaggle yarışmasında hâlâ baseline.

**Audio Spectrogram Transformer, AST (2021-2024).** Log-mel'i patch'le (örn. 16×16 patch), pozisyon embedding'leri ekle, ViT'e besle. Supervised öğrenmede AudioSet'te SOTA (mAP 0.485).

**BEATs ve WavLM-base (2024-2026).** Milyonlarca saat üzerinde self-supervised pretraining. İhtiyacın olacak supervised verinin %1-10'u ile görevine fine-tune et. 2026'da konuşma dışı ses için varsayılan başlangıç noktası. BEATs-iter3, 1/4 compute kullanırken AudioSet'te AST'i 1-2 mAP geçer.

**Frozen backbone olarak Whisper-encoder (2024).** Whisper'ın encoder'ını al, decoder'ı at, lineer sınıflandırıcı ekle. Sıfır ses augmentation'ı ile dil ID'si ve basit olay sınıflandırmasında SOTA'ya yakın. "Free lunch" baseline.

### Asıl zorluk sınıf dengesizliği

ESC-50: 50 sınıf, her biri 40 klip — dengeli, kolay. UrbanSound8K: 10 sınıf, 10:1 dengesiz. AudioSet: 632 sınıf, 100.000:1 uzun kuyruk. İşe yarayan teknikler:

- Eğitim sırasında dengeli örnekleme (değerlendirmede değil).
- Mixup: augmentation olarak iki klibi (ve etiketlerini) lineer enterpole et.
- SpecAugment: rastgele zaman ve frekans bantlarını maskele. Basit; kritik.

### Değerlendirme

- Multiclass exclusive (Speech Commands): top-1 doğruluğu, top-5 doğruluğu.
- Multiclass multi-label (AudioSet, UrbanSound-tarzı): mean average precision (mAP).
- Yoğun dengesiz: sınıf bazlı recall + macro F1.

Bilmen gereken 2026 rakamları:

| Benchmark | Baseline | SOTA 2026 | Kaynak |
|-----------|----------|-----------|--------|
| ESC-50 | %82 (AST) | %97.0 (BEATs-iter3) | BEATs makalesi (2024) |
| AudioSet mAP | 0.485 (AST) | 0.548 (BEATs-iter3) | HEAR leaderboard 2026 |
| Speech Commands v2 | %98 (CNN) | %99.0 (Audio-MAE) | HEAR v2 sonuçları |

## İnşa Et

### Adım 1: Öznitelikleştir

```python
def featurize_mfcc(signal, sr, n_mfcc=13, n_mels=40, frame_len=400, hop=160):
    mag = stft_magnitude(signal, frame_len, hop)
    fb = mel_filterbank(n_mels, frame_len, sr)
    mels = apply_filterbank(mag, fb)
    log = log_transform(mels)
    return [dct_ii(frame, n_mfcc) for frame in log]
```

### Adım 2: Sabit uzunlukta özet

```python
def summarize(mfcc_frames):
    n = len(mfcc_frames[0])
    mean = [sum(f[i] for f in mfcc_frames) / len(mfcc_frames) for i in range(n)]
    var = [
        sum((f[i] - mean[i]) ** 2 for f in mfcc_frames) / len(mfcc_frames) for i in range(n)
    ]
    return mean + var
```

Basit ama güçlü: zaman üzerinde mean + variance, 13-katsayılı MFCC için 26-boyutlu sabit embedding verir. Anında çalışır. 2017'ye kadar ESC-50'de SOTA NN baseline'larını yendi.

### Adım 3: k-NN

```python
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-12
    nb = math.sqrt(sum(x * x for x in b)) or 1e-12
    return dot / (na * nb)

def knn_classify(q, bank, labels, k=5):
    sims = sorted(range(len(bank)), key=lambda i: -cosine(q, bank[i]))[:k]
    votes = Counter(labels[i] for i in sims)
    return votes.most_common(1)[0][0]
```

### Adım 4: Log-mel üzerinde CNN'e yükselt

PyTorch'ta:

```python
import torch.nn as nn

class AudioCNN(nn.Module):
    def __init__(self, n_mels=80, n_classes=50):
        super().__init__()
        self.body = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Linear(128, n_classes)

    def forward(self, x):  # x: (B, 1, T, n_mels)
        return self.head(self.body(x).flatten(1))
```

3M parametre. ESC-50'de tek bir RTX 4090 ile ~10 dakikada eğitilir. %80+ doğruluk.

### Adım 5: 2026 varsayılanı — BEATs'i fine-tune et

```python
from transformers import ASTFeatureExtractor, ASTForAudioClassification

ext = ASTFeatureExtractor.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593")
model = ASTForAudioClassification.from_pretrained(
    "MIT/ast-finetuned-audioset-10-10-0.4593",
    num_labels=50,
    ignore_mismatched_sizes=True,
)

inputs = ext(audio, sampling_rate=16000, return_tensors="pt")
logits = model(**inputs).logits
```

BEATs için `beats` kütüphanesi üzerinden `microsoft/BEATs-base` kullan; transformers API'si aynı şekildedir.

## Kullan

2026 yığını:

| Durum | Şununla başla |
|-----------|-----------|
| Tiny veri seti (<1000 klip) | MFCC ortalamaları üzerinde k-NN (baseline'ın) + ses augmentation'ı |
| Orta veri seti (1K–100K) | BEATs ya da AST fine-tune |
| Büyük veri seti (>100K) | Sıfırdan eğit ya da Whisper-encoder fine-tune et |
| Real-time, edge | int8'e quantize edilmiş 40-MFCC CNN (KWS-tarzı) |
| Multi-label (AudioSet) | BCE loss + mixup + SpecAugment ile BEATs-iter3 |
| Dil ID'si | MMS-LID, SpeechBrain VoxLingua107 baseline |

Karar kuralı: **taze model değil, frozen backbone ile başla**. BEATs head'ini fine-tune etmek SOTA'nın %95'ini haftalar yerine saatler içinde verir.

## Yayınla

`outputs/skill-classifier-designer.md` olarak kaydet. Verilen bir ses sınıflandırma görevi için mimari, augmentation, sınıf-denge stratejisi ve eval metriği seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. 4 sınıflı sentetik veri seti (farklı pitch'lerdeki saf tonlar) üzerinde k-NN MFCC baseline'ını eğitir. Confusion matrix raporla.
2. **Orta.** `summarize`'ı [mean, var, skew, kurtosis] ile değiştir. 4-moment pooling aynı sentetik veri setinde mean+var'ı yener mi?
3. **Zor.** `torchaudio` kullanarak ESC-50 fold 1 üzerinde 2D CNN eğit. 5-fold cross-validation doğruluğunu raporla. SpecAugment ekle (time mask = 20, freq mask = 10) ve farkı raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| AudioSet | Sesin ImageNet'i | Google'ın 2M-klipli, 632-sınıflı zayıf-etiketli YouTube veri seti. |
| ESC-50 | Küçük sınıflandırma benchmark'ı | 50 sınıf × 40 klip çevresel ses. |
| AST | Audio Spectrogram Transformer | Log-mel patch'leri üzerinde ViT; 2021 SOTA. |
| BEATs | Self-supervised ses | Microsoft modeli; iter3 2026 itibarıyla AudioSet'i yönetiyor. |
| Mixup | Çift augmentation'ı | `x = λ·x1 + (1-λ)·x2; y = λ·y1 + (1-λ)·y2`. |
| SpecAugment | Maske tabanlı augmentation | Spektrogramın rastgele zaman ve frekans bantlarını sıfırla. |
| mAP | Ana multi-label metriği | Sınıflar ve eşikler arasında mean average precision. |

## İleri Okuma

- [Gong, Chung, Glass (2021). AST: Audio Spectrogram Transformer](https://arxiv.org/abs/2104.01778) — 2021–2024 arası kayıt mimarisi.
- [Chen et al. (2022, rev. 2024). BEATs: Audio Pre-Training with Acoustic Tokenizers](https://arxiv.org/abs/2212.09058) — 2024+ varsayılan.
- [Park et al. (2019). SpecAugment](https://arxiv.org/abs/1904.08779) — baskın ses augmentation'ı.
- [Piczak (2015). ESC-50 dataset](https://github.com/karolpiczak/ESC-50) — yaşamaya devam eden 50-sınıflı benchmark.
- [Gemmeke et al. (2017). AudioSet](https://research.google.com/audioset/) — 632-sınıflı YouTube taksonomisi; hâlâ altın standart.
