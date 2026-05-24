# Konuşma Tanıma (ASR) — CTC, RNN-T, Attention

> Konuşma tanıma, her timestep'te ses sınıflandırmadır; İngilizce ve sessizliği bilen bir sıra modeliyle birbirine yapıştırılmıştır. CTC, RNN-T ve attention bunu yapmanın üç yoludur. Birini seç ve nedenini anla.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 02 (Spektrogramlar ve Mel), Faz 5 · 08 (Metin için CNN'ler ve RNN'ler), Faz 5 · 10 (Attention)
**Süre:** ~45 dakika

## Sorun

10 saniyelik 16 kHz bir klibin var. Bir string istiyorsun: "mutfak ışıklarını aç". Zorluk yapısaldır: ses frame'leri karakterlerle bire-bir hizalanmaz. "okay" kelimesi 200 ms ya da 1200 ms sürebilir. Sessizlik utterance'a noktalama ekler. Bazı fonemler diğerlerinden uzundur. Çıktı token sayısı önceden bilinmez.

Üç formülasyon bunu çözer:

1. **CTC (Connectionist Temporal Classification).** Özel bir *blank* dahil frame başına token olasılıkları yayar. Decode zamanında tekrarları ve blank'leri sıkıştır. Non-autoregressive, hızlı. wav2vec 2.0, MMS tarafından kullanılır.
2. **RNN-T (Recurrent Neural Network Transducer).** Joint network, encoder frame ve önceki token'lar verilen bir sonraki token'ı tahmin eder. Streamable. Google'ın on-device ASR'si, NVIDIA Parakeet tarafından kullanılır.
3. **Attention encoder-decoder.** Encoder sesi gizli durumlara sıkıştırır, decoder token'ları otoregresif üretmek için cross-attend yapar. Whisper, SeamlessM4T tarafından kullanılır.

2026'da LibriSpeech test-clean üzerinde SOTA WER %1.4 (Parakeet-TDT-1.1B, NVIDIA) ve %1.58 (Whisper-Large-v3-turbo). Farklar küçük; deployment farkları kocaman.

## Kavram

![Üç ASR formülasyonu: CTC, RNN-T, attention-encoder-decoder](../assets/asr-formulations.svg)

**CTC sezgisi.** Encoder'ın `V+1` token (V karakter + blank) üzerinde `T` frame seviyesi dağılım çıkarmasına izin ver. `U < T` uzunluğunda bir hedef string `y` için, `y`'ye sıkışan herhangi bir frame hizalaması sayılır. CTC loss tüm böyle hizalamalar üzerinden toplar. Çıkarım: frame başına argmax, tekrarları sıkıştır, blank'leri kaldır.

Avantajlar: non-autoregressive, streamable, sıfır lookahead. Dezavantaj: *koşullu bağımsızlık varsayımı* — her frame tahmini diğerlerinden bağımsızdır, dolayısıyla içsel dil modeli yoktur. Beam search ya da shallow fusion üzerinden harici LM ile düzelt.

**RNN-T sezgisi.** Token geçmişini gömen bir *predictor* ağı ve predictor durumunu encoder frame ile `V+1` (`+1` null / no-emit) üzerinde joint dağılıma birleştiren bir *joiner* ekler. CTC'nin yok saydığı koşullu bağımlılığı açıkça modeller. Streamable çünkü her adım yalnızca geçmiş frame'lere ve geçmiş token'lara koşullu.

Avantajlar: streamable + içsel LM. Dezavantaj: eğitim daha karmaşık ve bellek aç (3D loss lattice); RNN-T loss kernel'ları başlı başına bir kütüphane kategorisidir.

**Attention encoder-decoder.** Log-mel frame'leri üzerinde encoder (6-32 transformer katmanı). Token'ları otoregresif üretmek için encoder çıktılarına cross-attend yapan decoder (6-32 transformer katmanı). Hizalama kısıtı yok — attention sesin herhangi bir yerine bakabilir. Attention'ı sınırlamadıkça non-streamable (chunked Whisper-Streaming, 2024).

Avantajlar: offline ASR'da en yüksek kalite, standart seq2seq araçlarıyla eğitmesi kolay. Dezavantaj: otoregresif gecikme çıktı uzunluğuyla orantılıdır; mühendislik olmadan streaming yapamaz.

### WER: tek rakam

**Word Error Rate** = `(S + D + I) / N`, burada S=ikameler, D=silmeler, I=eklemeler, N=referans kelime sayısı. Kelime seviyesinde Levenshtein edit mesafesiyle eşleşir. Daha düşük daha iyi. %20 üzerinde WER genellikle kullanılamaz; %5 altında okuma konuşması için insan eşdeğeri. Standart benchmark'larda 2026 rakamları:

| Model | LibriSpeech test-clean | LibriSpeech test-other | Boyut |
|-------|------------------------|------------------------|------|
| Parakeet-TDT-1.1B | %1.40 | %2.78 | 1.1B param |
| Whisper-Large-v3-turbo | %1.58 | %3.03 | 809M |
| Canary-1B Flash | %1.48 | %2.87 | 1B |
| Seamless M4T v2 | %1.7 | %3.5 | 2.3B |

Tümü encoder-decoder ya da RNN-T tabanlı. Saf CTC sistemleri (wav2vec 2.0) test-clean'de %1.8–2.1 civarındadır.

## İnşa Et

### Adım 1: Greedy CTC decode

```python
def ctc_greedy(frame_logits, blank=0, vocab=None):
    # frame_logits: per-frame probability vector listesi
    preds = [max(range(len(p)), key=lambda i: p[i]) for p in frame_logits]
    out = []
    prev = -1
    for p in preds:
        if p != prev and p != blank:
            out.append(p)
        prev = p
    return "".join(vocab[i] for i in out) if vocab else out
```

İki kural: ardışık tekrarları sıkıştır, blank'leri at. Örnek: `a a _ _ a b b _ c` → `a a b c`.

### Adım 2: Beam-search CTC

```python
def ctc_beam(frame_logits, beam=8, blank=0):
    import math
    beams = [([], 0.0)]  # (tokens, log_prob)
    for p in frame_logits:
        log_p = [math.log(max(pi, 1e-10)) for pi in p]
        candidates = []
        for seq, lp in beams:
            for t, lpt in enumerate(log_p):
                new = seq[:] if t == blank else (seq + [t] if not seq or seq[-1] != t else seq)
                candidates.append((new, lp + lpt))
        candidates.sort(key=lambda x: -x[1])
        beams = candidates[:beam]
    return beams[0][0]
```

Üretim LM fusion ile prefix tree beam search kullanır; bu kavramsal iskelettir.

### Adım 3: WER

```python
def wer(ref, hyp):
    r, h = ref.split(), hyp.split()
    dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        dp[i][0] = i
    for j in range(len(h) + 1):
        dp[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[len(r)][len(h)] / max(1, len(r))
```

### Adım 4: Whisper'a karşı çıkarım

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe("clip.wav")
print(result["text"])
```

2026'nın en güçlü genel ASR'si için tek satır. 24 GB GPU'da ~20× realtime çalışır.

### Adım 5: Parakeet ya da wav2vec 2.0 ile streaming

```python
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="nvidia/parakeet-tdt-1.1b")
for chunk in streaming_audio():
    print(asr(chunk, return_timestamps=True))
```

Streaming ASR, chunked encoder attention ve carryover state'e ihtiyaç duyar; bunu destekleyen bir kütüphane kullan (Parakeet için NeMo, `chunk_length_s` ile `transformers` pipeline).

## Kullan

2026 yığını:

| Durum | Seç |
|-----------|------|
| İngilizce, offline, maks kalite | Whisper-large-v3-turbo |
| Çok dilli, robust | SeamlessM4T v2 |
| Streaming, düşük gecikme | Parakeet-TDT-1.1B ya da Riva |
| Edge, mobil, <500 ms gecikme | Quantize edilmiş Whisper-Tiny ya da Moonshine (2024) |
| Uzun-form | VAD tabanlı chunking ile Whisper (WhisperX) |
| Domain-specific (medical, legal) | wav2vec 2.0'ı fine-tune et + domain LM fusion |

## 2026'da Hâlâ Yayına Çıkan Tuzaklar

- **VAD yok.** Whisper'ı sessizlik üzerinde çalıştırmak halüsinasyon üretir ("Thanks for watching!"). Her zaman VAD ile kapıla.
- **Karakter vs kelime vs subword WER.** Normalizasyon (küçük harf, noktalama kaldırma) *sonrası* kelime seviyesinde WER raporla.
- **Dil ID drift'i.** Whisper'ın otomatik LID'i gürültülü klipleri yanlışlıkla Japonca ya da Galce'ye yönlendirir; bildiğinde `language="en"` zorla.
- **Chunking olmadan uzun klipler.** Whisper'ın 30 saniyelik penceresi vardır. Daha uzun her şey için `chunk_length_s=30, stride=5` kullan.

## Yayınla

`outputs/skill-asr-picker.md` olarak kaydet. Verilen bir deployment hedefi için model, decoding stratejisi, chunking ve LM fusion seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Elle yazılmış bir CTC çıktısını greedy decode eder ve referansa karşı WER hesaplar.
2. **Orta.** Adım 2'deki prefix-tree beam search'ü düzgünce uygula (blank merge kuralını hesaba kat). 10-örnekli sentetik veri setinde greedy ile karşılaştır.
3. **Zor.** [LibriSpeech test-clean](https://www.openslr.org/12) üzerinde `whisper-large-v3-turbo` kullan. İlk 100 utterance üzerinde WER hesapla. Yayınlanmış rakamlarla karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| CTC | Blank-token loss'u | Tüm frame'den token'a hizalamalar üzerinde marjinal; non-AR. |
| RNN-T | Streaming loss'u | CTC + next-token predictor; kelime sırasını ele alır. |
| Attention enc-dec | Whisper-tarzı | Encoder + cross-attending decoder; en iyi offline kalite. |
| WER | Raporladığın rakam | Kelime seviyesinde `(S+D+I)/N`. |
| Blank | Boşluk | CTC'de "bu frame'de emisyon yok" anlamına gelen özel token. |
| LM fusion | Harici dil modeli | Beam search sırasında ağırlıklı LM log-prob ekle. |
| VAD | Sessizlik kapısı | Voice activity detector; konuşma olmayanı keser. |

## İleri Okuma

- [Graves et al. (2006). Connectionist Temporal Classification](https://www.cs.toronto.edu/~graves/icml_2006.pdf) — CTC makalesi.
- [Graves (2012). Sequence Transduction with RNNs](https://arxiv.org/abs/1211.3711) — RNN-T makalesi.
- [Radford et al. / OpenAI (2022). Whisper: Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — 2022 kanonik makale; v3-turbo eklentisi 2024.
- [NVIDIA NeMo — Parakeet-TDT card](https://huggingface.co/nvidia/parakeet-tdt-1.1b) — 2026 Open ASR Leaderboard lideri.
- [Hugging Face — Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) — 25+ model arasında canlı benchmark.
