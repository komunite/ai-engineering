# Konuşmacı Tanıma ve Doğrulama

> ASR "ne söyledi?" diye sorar. Konuşmacı tanıma "kim söyledi?" diye sorar. Matematik aynı görünür — embedding artı kosinüs — ama her üretim kararı tek bir EER sayısına bağlıdır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar ve Mel), Faz 5 · 22 (Embedding Modelleri)
**Süre:** ~45 dakika

## Sorun

Bir kullanıcı bir passphrase söylüyor. Bilmek istiyorsun: bu, iddia ettiği kişi mi (*verification*, 1:1) yoksa enrollment bankandaki ilk kişi mi (*identification*, 1:N)? Ya da hiçbiri — bu bilinmeyen bir konuşmacı mı (*open-set*)?

2018 öncesi: GMM-UBM + i-vector'lar. Makul EER ama channel shift'e (telefon vs laptop) ve duyguya karşı kırılgan. 2018–2022: x-vector'lar (angular margin ile eğitilmiş TDNN backbone). 2022+: ECAPA-TDNN ve WavLM-large embedding'leri. 2026'ya gelindiğinde alan üç model ve bir metrik tarafından domine ediliyor.

Metrik **EER** — Equal Error Rate. Karar eşiğini False Accept Rate = False Reject Rate olacak şekilde ayarla. Kesişim noktası EER'dir. Her makalede, her leaderboard'da, her tedarik çağrısında kullanılır.

## Kavram

![Embedding + kosinüs + EER ile enrollment + verification pipeline'ı](../assets/speaker-verification.svg)

**Pipeline.** Enrollment: hedef konuşmacının 5–30 saniyesini kaydet; sabit-boyutlu bir embedding hesapla (ECAPA-TDNN için 192-d, WavLM-large için 256-d). Verification: test utterance embedding'ini al; kosinüs benzerliği hesapla; eşikle karşılaştır.

**ECAPA-TDNN (2020, 2026'da hâlâ baskın).** Emphasized Channel Attention, Propagation and Aggregation - Time-Delay Neural Network. Squeeze-excitation'lı 1D conv blokları, multi-head attention pooling, ardından 192-d'ye lineer katman. VoxCeleb 1+2 (2.700 konuşmacı, 1.1M utterance) üzerinde Additive Angular Margin loss (AAM-softmax) ile eğitilmiş.

**WavLM-SV (2022+).** Önceden eğitilmiş bir WavLM-large SSL backbone'unu AAM loss ile fine-tune et. Daha yüksek kalite ama daha yavaş — 15 MB'a karşı 300+ MB.

**x-vector (baseline).** TDNN + statistics pooling. Klasik; CPU / edge'de hâlâ kullanışlı.

**AAM-softmax.** Angular uzayda eklenmiş margin `m`'li standart softmax: doğru sınıf için `cos(θ + m)`. Sınıflar arası angular ayrımı zorlar. Tipik `m=0.2`, ölçek `s=30`.

### Scoring

- **Kosinüs**: enrollment ve test embedding'leri arasında. Eşik tabanlı karar.
- **PLDA (Probabilistic LDA).** Embedding'leri, same-speaker vs different-speaker'ın kapalı-form likelihood ratio'sunun olduğu bir latent uzaya projekte eder. EER'i +%10–20 düşürmek için kosinüsün üstüne eklenir. 2020 öncesi standart; şimdi sadece closed-set kurulumlarında kullanılır.
- **Score normalization.** `S-norm` ya da `AS-norm`: her score'u imposter mean ve std cohort'una karşı normalize et. Cross-domain değerlendirme için kritik.

### Bilmen gereken rakamlar (2026)

| Model | VoxCeleb1-O EER | Param | Throughput (A100) |
|-------|-----------------|--------|-------------------|
| x-vector (klasik) | %3.10 | 5 M | 400× RT |
| ECAPA-TDNN | %0.87 | 15 M | 200× RT |
| WavLM-SV large | %0.42 | 316 M | 20× RT |
| Pyannote 3.1 segmentasyon + embedding | %0.65 | 6 M | 100× RT |
| ReDimNet (2024) | %0.39 | 24 M | 100× RT |

### Diarization

Çok konuşmacılı bir klipte "kim ne zaman konuştu". Pipeline: VAD → segment → her segmenti embed et → kümele (agglomerative ya da spectral) → sınırları yumuşat. Modern yığın: konuşmacı segmentasyonu + embedding + clustering'i tek çağrının arkasına paketleyen `pyannote.audio` 3.1. AMI'de 2026 SOTA DER ~%15 (2022'de %23'tü).

## İnşa Et

### Adım 1: MFCC istatistiklerinden toy embedding

```python
def embed_mfcc_stats(signal, sr):
    frames = featurize_mfcc(signal, sr, n_mfcc=13)
    mean = [sum(f[i] for f in frames) / len(frames) for i in range(13)]
    std = [
        math.sqrt(sum((f[i] - mean[i]) ** 2 for f in frames) / len(frames))
        for i in range(13)
    ]
    return mean + std  # 26-d
```

SOTA'dan kilometrelerce uzak — sadece öğretim için. `code/main.py` bunu sentetik konuşmacı verisi üzerinde proof-of-concept olarak kullanır.

### Adım 2: Kosinüs benzerliği + eşik

```python
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

def verify(enroll, test, threshold=0.75):
    return cosine(enroll, test) >= threshold
```

### Adım 3: Benzerlik çiftlerinden EER

```python
def eer(same_scores, diff_scores):
    thresholds = sorted(set(same_scores + diff_scores))
    best = (1.0, 1.0, 0.0)  # (fa, fr, threshold)
    for t in thresholds:
        fr = sum(1 for s in same_scores if s < t) / len(same_scores)
        fa = sum(1 for s in diff_scores if s >= t) / len(diff_scores)
        if abs(fa - fr) < abs(best[0] - best[1]):
            best = (fa, fr, t)
    return (best[0] + best[1]) / 2, best[2]
```

(eer, threshold_at_eer) döndürür. İkisini de raporla.

### Adım 4: SpeechBrain ile üretim

```python
from speechbrain.pretrained import EncoderClassifier

clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")

# enroll: 3-5 temiz örneğin embedding'lerini ortala
enroll = torch.stack([clf.encode_batch(load(x)) for x in enrollment_clips]).mean(0)
# verify
score = clf.similarity(enroll, clf.encode_batch(load("test.wav"))).item()
verdict = score > 0.25   # ECAPA tipik eşik; verinde tune et
```

### Adım 5: pyannote ile diarize

```python
from pyannote.audio import Pipeline

pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
diarization = pipe("meeting.wav", num_speakers=None)
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{turn.start:.1f}–{turn.end:.1f}  {speaker}")
```

## Kullan

2026 yığını:

| Durum | Seç |
|-----------|------|
| Closed-set 1:1 verification, edge | ECAPA-TDNN + kosinüs eşiği |
| Open-set verification, cloud | WavLM-SV + AS-norm |
| Diarization (toplantı, podcast) | `pyannote/speaker-diarization-3.1` |
| Anti-spoofing (replay / deepfake algılama) | AASIST ya da RawNet2 |
| Tiny embedded (KWS + enrollment) | Titanet-Small (NeMo) |

## Tuzaklar

- **Channel uyuşmazlığı.** VoxCeleb (web video) üzerinde eğitilmiş model ≠ telefon görüşmesi sesi. Her zaman hedef channel'da değerlendir.
- **Kısa utterance'lar.** 3 saniyenin altındaki test sesinde EER sert düşer.
- **Gürültülü enrollment.** Bir gürültülü enrollment anchor'ı zehirler. ≥3 temiz örnek kullan ve ortala.
- **Koşullar arası sabit eşik.** Eşiği her zaman hedef domain'den held-out dev set'inde tune et.
- **Non-normalized embedding'lerde kosinüs.** Önce L2-normalize et; aksi halde magnitüd domine eder.

## Yayınla

`outputs/skill-speaker-verifier.md` olarak kaydet. Model, enrollment protokolü, threshold-tuning planı ve dolandırıcılık önlemlerini seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Sentetik "konuşmacılar" inşa eder (farklı ton profilleri), enroll eder, 100-çiftli trial listesinde EER hesaplar.
2. **Orta.** SpeechBrain ECAPA'yı 30 VoxCeleb1 utterance üzerinde (5 konuşmacı × 6 her biri) kullan. Kosinüs vs PLDA ile EER hesapla.
3. **Zor.** `pyannote.audio` ile tam enroll → diarize → verify pipeline'ı kur. AMI dev set'inde DER değerlendir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| EER | Başlık metriği | False Accept = False Reject olduğu eşik. |
| Verification | 1:1 | "Bu Alice mi?" |
| Identification | 1:N | "Kim konuşuyor?" |
| Open-set | Bilinmeyen mümkün | Test set'i enroll olmamış konuşmacılar içerebilir. |
| Enrollment | Kayıt | Konuşmacının referans embedding'ini hesaplama. |
| AAM-softmax | Loss | Eklenmiş angular margin'li softmax; kluster ayrımı zorlar. |
| PLDA | Klasik scoring | Probabilistic LDA; embedding'lerin üzerinde likelihood-ratio scoring. |
| DER | Diarization metriği | Diarization Error Rate — miss + false alarm + karışıklık. |

## İleri Okuma

- [Snyder et al. (2018). X-Vectors: Robust DNN Embeddings for Speaker Recognition](https://www.danielpovey.com/files/2018_icassp_xvectors.pdf) — klasik deep-embedding makalesi.
- [Desplanques et al. (2020). ECAPA-TDNN](https://arxiv.org/abs/2005.07143) — 2020–2026 baskın mimari.
- [Chen et al. (2022). WavLM: Large-Scale Self-Supervised Pre-Training for Full Stack Speech Processing](https://arxiv.org/abs/2110.13900) — SV ve diarization için SSL backbone.
- [Bredin et al. (2023). pyannote.audio 3.1](https://github.com/pyannote/pyannote-audio) — üretim diarization + embedding yığını.
- [VoxCeleb leaderboard (updated 2026)](https://www.robots.ox.ac.uk/~vgg/data/voxceleb/) — modeller arası güncel EER sıralaması.
