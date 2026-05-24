# Ses Değerlendirme — WER, MOS, UTMOS, MMAU, FAD ve Açık Leaderboard'lar

> Ölçemediğini yayınlayamazsın. Bu ders her ses görevi için 2026 metriklerini isimlendiriyor: ASR (WER, CER, RTFx), TTS (MOS, UTMOS, SECS, ASR-round-trip WER), audio-language (MMAU, LongAudioBench), müzik (FAD, CLAP) ve konuşmacı (EER). Ve karşılaştırdığın leaderboard'lar.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 6 · 04, 06, 07, 09, 10; Faz 2 · 09 (Model Değerlendirme)
**Süre:** ~60 dakika

## Sorun

Her ses görevinin birden çok metriği var, her biri farklı bir eksen ölçüyor. Yanlış metriği kullanmak dashboard'unda harika ama üretimde berbat görünen bir modeli yayınlamanın yoludur. 2026 kanonik listesi:

| Görev | Birincil | İkincil |
|------|---------|-----------|
| ASR | WER | CER · RTFx · ilk-token gecikme |
| TTS | MOS / UTMOS | SECS · ASR-round-trip WER · CER · TTFA |
| Ses klonlama | SECS (ECAPA kosinüsü) | MOS · CER |
| Konuşmacı doğrulama | EER | minDCF · operating point'te FAR / FRR |
| Diarization | DER | JER · konuşmacı karışıklığı |
| Ses sınıflandırma | top-1 · mAP | macro F1 · sınıf bazlı recall |
| Müzik üretimi | FAD | CLAP · dinleyici paneli MOS |
| Ses dil modeli | MMAU-Pro | LongAudioBench · AudioCaps FENSE |
| Streaming S2S | gecikme P50/P95 | WER · MOS |

## Kavram

![Ses değerlendirme matrisi — metrikler vs görevler vs 2026 leaderboard'lar](../assets/eval-landscape.svg)

### ASR metrikleri

**WER (Word Error Rate).** `(S + D + I) / N`. Puanlamadan önce küçük harf, noktalama strip, sayı normalize. `jiwer` ya da OpenAI'ın `whisper_normalizer`'ını kullan. &lt; %5 = okuma konuşması insan eşdeğeri.

**CER (Character Error Rate).** Aynı formül, karakter seviyesi. Kelime segmentasyonunun belirsiz olduğu ton dilleri (Mandarin, Kantonca) için kullanılır.

**RTFx (inverse real-time factor).** Wall-clock saniye başına işlenen ses saniyesi. Daha yüksek daha iyi. Parakeet-TDT 3380×'e çıkar. Whisper-large-v3 ~30×.

**İlk-token gecikme.** Ses girdisinden ilk transkript token'ına wall-clock. Streaming için kritik. Deepgram Nova-3: ~150 ms.

### TTS metrikleri

**MOS (Mean Opinion Score).** 1-5 insan değerlendirmesi. Altın standart ama yavaş. Örnek başına 20+ dinleyici, model başına 100+ örnek topla.

**UTMOS (2022-2026).** Öğrenilmiş MOS tahmincisi. Standart benchmark'larda insan MOS'u ile ~0.9 korele. F5-TTS: UTMOS 3.95; ground truth: 4.08.

**SECS (Speaker Encoder Cosine Similarity).** Ses klonlama için. Referans ile klonlanmış çıktı arasında ECAPA embedding kosinüsü. &gt; 0.75 = tanınabilir klon.

**ASR-round-trip WER.** TTS çıktısını Whisper'dan geçir, girdi metnine karşı WER hesapla. Anlaşılırlık regresyonlarını yakalar. 2026 SOTA: &lt; %2 CER.

**TTFA (time-to-first-audio).** Wall-clock gecikme. Kokoro-82M: ~100 ms; F5-TTS: ~1 sn.

### Ses-klonlama-spesifik

**SECS + MOS + CER** üçlü olarak. Yüksek SECS ama düşük MOS skoru alan klonlama tını-doğru-ama-doğal-değil demek; tersi doğru ses ama yanlış konuşmacı demek.

### Konuşmacı doğrulama

**EER (Equal Error Rate).** False Accept Rate'in False Reject Rate'e eşit olduğu eşik. VoxCeleb1-O'da ECAPA: %0.87.

**minDCF (min Detection Cost).** Seçilen operating point'te (genellikle FAR=0.01) ağırlıklı maliyet. EER'den daha üretim-ilgili.

### Diarization

**DER (Diarization Error Rate).** `(FA + Miss + Confusion) / total_speaker_time`. Kaçırılan konuşma + yanlış-alarm konuşma + konuşmacı-karışıklığı, her biri oran olarak. AMI toplantılar: %10-20 DER gerçekçi. pyannote 3.1 + Precision-2 ticari: iyi kaydedilmiş seste &lt;%10 DER.

**JER (Jaccard Error Rate).** DER'e alternatif, kısa-segment bias'ına robust.

### Ses sınıflandırma

Multi-label: tüm sınıflar üzerinde **mAP (mean Average Precision)**. AudioSet: BEATs-iter3 için 0.548 mAP.

Multi-class exclusive: **top-1, top-5 doğruluğu**. Speech Commands v2: %99.0 top-1 (Audio-MAE).

Dengesiz: **macro F1** + **sınıf bazlı recall**. Sınıf bazlı raporla — toplu doğruluk hangi sınıfların başarısız olduğunu gizler.

### Müzik üretimi

**FAD (Fréchet Audio Distance).** Gerçek vs üretilmiş ses VGGish-embedding dağılımları arası mesafe. MusicCaps'te MusicGen-small: 4.5. MusicLM: 4.0. Daha düşük daha iyi.

**CLAP Score.** CLAP embedding'leri kullanan metin-ses hizalama skoru. &gt; 0.3 = makul hizalama.

**Dinleyici paneli MOS.** Tüketici-seviye müzik için hâlâ son söz. TTS Arena'da Suno v5 ELO 1293 (eşleştirilmiş insan tercihlerinden).

### Ses-dil benchmark'ları

**MMAU (Massive Multi-Audio Understanding).** 10k ses-QA çifti.

**MMAU-Pro.** 1800 zor öğe, dört kategori: konuşma / ses / müzik / multi-audio. 4-yönlü'de rastgele şans %25. Gemini 2.5 Pro genel ~%60; tüm modeller arası multi-audio ~%22.

**LongAudioBench.** Semantik sorgularla çok dakikalı klipler. Audio Flamingo Next, Gemini 2.5 Pro'yu yener.

**AudioCaps / Clotho.** Captioning benchmark'ları. SPICE, CIDEr, FENSE metrikleri.

### Streaming speech-to-speech

**Gecikme P50 / P95 / P99.** End-of-user-speech'ten ilk duyulabilir cevaba wall-clock. Moshi: 200 ms; GPT-4o Realtime: 300 ms.

Çıktıda **WER / MOS**.

**Barge-in tepki süresi.** Kullanıcı kesintisinden asistan mute'una süre. Hedef &lt; 150 ms.

### 2026 leaderboard'lar

| Leaderboard | Track'ler | URL |
|------------|--------|-----|
| Open ASR Leaderboard (HF) | İngilizce + çok dilli + uzun-form | `huggingface.co/spaces/hf-audio/open_asr_leaderboard` |
| TTS Arena (HF) | İngilizce TTS | `huggingface.co/spaces/TTS-AGI/TTS-Arena` |
| Artificial Analysis Speech | TTS + STT, eşleştirilmiş oylardan ELO | `artificialanalysis.ai/speech` |
| MMAU-Pro | LALM akıl yürütme | `mmaubenchmark.github.io` |
| SpeakerBench / VoxSRC | Konuşmacı tanıma | `voxsrc.github.io` |
| MMAU music subset | Müzik LALM | (MMAU içinde) |
| HEAR benchmark | Self-supervised ses | `hearbenchmark.com` |

## İnşa Et

### Adım 1: Normalizasyon ile WER

```python
from jiwer import wer, Compose, ToLowerCase, RemovePunctuation, Strip

transform = Compose([ToLowerCase(), RemovePunctuation(), Strip()])
score = wer(
    truth="Please turn on the lights.",
    hypothesis="please turn on the light",
    truth_transform=transform,
    hypothesis_transform=transform,
)
# ~0.17
```

### Adım 2: TTS round-trip WER

```python
def ttr_wer(tts_model, asr_model, texts):
    errors = []
    for txt in texts:
        audio = tts_model.synthesize(txt)
        recog = asr_model.transcribe(audio)
        errors.append(wer(truth=txt, hypothesis=recog))
    return sum(errors) / len(errors)
```

### Adım 3: Ses klonlama için SECS

```python
from speechbrain.inference.speaker import EncoderClassifier
sv = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb")

emb_ref = sv.encode_batch(load_wav("reference.wav"))
emb_clone = sv.encode_batch(load_wav("cloned.wav"))
secs = torch.nn.functional.cosine_similarity(emb_ref, emb_clone, dim=-1).item()
```

### Adım 4: Müzik üretimi için FAD

```python
from frechet_audio_distance import FrechetAudioDistance
fad = FrechetAudioDistance()
score = fad.get_fad_score("generated_folder/", "reference_folder/")
```

### Adım 5: Konuşmacı doğrulama için EER (Ders 6 ile aynı kod)

```python
def eer(same_scores, diff_scores):
    thresholds = sorted(set(same_scores + diff_scores))
    best = (1.0, 0.0)
    for t in thresholds:
        far = sum(1 for s in diff_scores if s >= t) / len(diff_scores)
        frr = sum(1 for s in same_scores if s < t) / len(same_scores)
        if abs(far - frr) < best[0]:
            best = (abs(far - frr), (far + frr) / 2)
    return best[1]
```

## Kullan

Her deploy'u her model güncellemesinde çalışan sabit eval harness'ı ile eşleştir. Üç ana kural:

1. **Puanlamadan önce normalize et.** Küçük harf, noktalama-strip, sayı-genişlet. Normalizasyon kuralını raporla.
2. **Ortalama değil, dağılım raporla.** Gecikme için P50/P95/P99. Sınıflandırma için sınıf bazlı recall. MMAU için kategori bazlı.
3. **Bir kanonik public benchmark çalıştır.** Üretim verin farklı olsa bile, Open ASR / TTS Arena / MMAU üzerinde raporlama reviewer'ların elma-elma karşılaştırmasına izin verir.

## Tuzaklar

- **UTMOS extrapolation'ı.** VCTK-tarzı temiz konuşma üzerinde eğitilmiş; gürültülü / klonlanmış / duygusal sesi kötü puanlar.
- **MOS panel bias'ı.** 20 Amazon Mechanical Turk işçisi ≠ 20 hedef kullanıcı. Riskler yüksekse domain panelini öde.
- **FAD referans set'ine bağlı.** Modeller arası aynı referans dağılımına karşı karşılaştır.
- **Toplu WER.** Genel %5 WER aksanlı konuşmada %30 WER'i gizleyebilir. Demografik dilim bazlı raporla.
- **Public benchmark doygunluğu.** Çoğu frontier model standart benchmark'larda tavana yakın. Trafiğini yansıtan bir in-house held-out set kur.

## Yayınla

`outputs/skill-audio-evaluator.md` olarak kaydet. Herhangi bir ses model yayını için metrikler, benchmark'lar ve raporlama formatı seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Toy girdilerde WER / CER / EER / SECS / FAD-ish / MMAU-ish hesapla.
2. **Orta.** TTS round-trip WER harness'ı kur. Kokoro ya da F5-TTS çıktını Whisper'dan geçir. 50 prompt üzerinde WER hesapla. WER &gt; %10 olan prompt'ları işaretle.
3. **Zor.** Ders 10 LALM seçimini MMAU-Pro konuşma + multi-audio alt kümelerinde (her biri 50 öğe) puanla. Kategori bazlı doğruluğu raporla ve yayınlanmış rakamla karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| WER | ASR skoru | Normalizasyon sonrası kelime seviyesinde `(S+D+I)/N`. |
| CER | Karakter WER | Ton dilleri ya da char-seviyesi sistemler için. |
| MOS | İnsan görüşü | 1-5 değerlendirme; 20+ dinleyici × 100 örnek. |
| UTMOS | ML MOS tahmincisi | Öğrenilmiş model; insan MOS'u ile ~0.9 korele. |
| SECS | Ses-klon benzerliği | Referans ile klon arası ECAPA kosinüsü. |
| EER | Konuşmacı verif skoru | FAR = FRR olduğu eşik. |
| DER | Diarization skoru | (FA + Miss + Confusion) / toplam. |
| FAD | Müzik-gen kalitesi | VGGish embedding'ler üzerinde Fréchet mesafesi. |
| RTFx | Throughput | Wall-clock saniye başına ses saniyesi. |

## İleri Okuma

- [jiwer](https://github.com/jitsi/jiwer) — normalizasyon yardımcı araçlarıyla WER/CER kütüphanesi.
- [UTMOS (Saeki et al. 2022)](https://arxiv.org/abs/2204.02152) — öğrenilmiş MOS tahmincisi.
- [Fréchet Audio Distance (Kilgour et al. 2019)](https://arxiv.org/abs/1812.08466) — müzik-gen standardı.
- [Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) — 2026 canlı sıralama.
- [TTS Arena](https://huggingface.co/spaces/TTS-AGI/TTS-Arena) — insan-oylu TTS leaderboard.
- [MMAU-Pro benchmark](https://mmaubenchmark.github.io/) — LALM akıl yürütme leaderboard'u.
- [HEAR benchmark](https://hearbenchmark.com/) — ses SSL benchmark'ları.
