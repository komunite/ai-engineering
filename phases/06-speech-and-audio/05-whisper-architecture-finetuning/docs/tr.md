# Whisper — Mimari ve Fine-Tuning

> Whisper, 680k saatlik çok dilli zayıf-supervised ses-metin çifti üzerinde eğitilmiş 30 saniyelik pencereli bir transformer encoder-decoder'dır. Tek mimari, birden çok görev, 99 dilde robust. 2026 referans ASR'si.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 04 (ASR), Faz 5 · 10 (Attention), Faz 7 · 05 (Full Transformer)
**Süre:** ~75 dakika

## Sorun

Eylül 2022'de OpenAI tarafından yayınlanan Whisper, bir commodity olarak yayına çıkan ilk ASR modeliydi: ses yapıştır, metin al, 99 dil, gürültüye robust, laptop'ta çalışır. 2024'e gelindiğinde OpenAI Large-v3 ve Turbo varyantlarını yayınlamıştı; 2026'ya gelindiğinde Whisper, podcast transkripsiyonundan ses asistanlarına, YouTube altyazılarına kadar her şey için varsayılan baseline.

Ama Whisper sonsuza dek black box olarak ele alabileceğin bir pipeline değil. Domain shift onu öldürür — teknik jargon, konuşmacı aksanları, özel isimler, kısa klipler, sessizlik. Şunları bilmen gerek:

1. İçinde aslında ne olduğu.
2. Ona chunked, streaming ya da uzun-form ses doğru şekilde nasıl verileceği.
3. Ne zaman ve nasıl fine-tune edileceği.

## Kavram

![Whisper encoder-decoder, görevler, chunked çıkarım, fine-tune](../assets/whisper.svg)

**Mimari.** Standart transformer encoder-decoder.

- Girdi: 30 saniyelik log-mel-spektrogram, 80 mel, 10 ms hop → 3000 frame. Kısa klipler zero-pad edilir, uzun klipler chunk'lanır.
- Encoder: conv-downsample (stride 2) + `N` transformer blok. Large-v3 için: 32 katman, 1280-boyut, 20 head.
- Decoder: causal self-attn + encoder çıktısına cross-attn yapan `N` transformer blok. Encoder ile aynı boyut.
- Çıktı: 51.865-tokenlık vocab üzerinde BPE token'ları.

Large-v3 1.55B param. Turbo, 32'den 4-katmanlı decoder kullanarak gecikmeyi 8× kısar, WER'de <%1 kayıpla.

**Prompt formatı.** Whisper, decoder prompt'undaki özel token'larla yönlendirilen bir multitask modeldir:

```
<|startoftranscript|><|en|><|transcribe|><|notimestamps|> Hello world.<|endoftext|>
```

- `<|en|>` — dil etiketi; translation-vs-transcription davranışını zorlar.
- `<|transcribe|>` ya da `<|translate|>` — herhangi bir dil girdisini İngilizceye çevir ya da kelime kelime verdiği gibi yaz.
- `<|notimestamps|>` — kelime seviyesi timestamp'leri atla (daha hızlı).

Prompt, tek modelin birçok görevi yapmasını sağlayan şeydir. `<|en|>`'yi `<|fr|>` ile değiştir, Fransızca transkribe eder.

**30 saniyelik pencere.** Her şey 30 saniyeye sabitlenmiştir. Daha uzun klipler chunking gerektirir; daha kısa klipler pad edilir. Pencereler nativ olarak streamlenmez — WhisperX, Whisper-Streaming ve faster-whisper bu yüzden vardır.

**Log-mel normalizasyonu.** `(log_mel - mean) / std`; istatistikler Whisper'ın kendi eğitim corpus'undan gelir. Whisper'ın preprocessing'ini (`whisper.audio.log_mel_spectrogram`) kullanmak *zorundasın*, `librosa.feature.melspectrogram`'ı değil.

### 2026'da varyantlar

| Varyant | Param | Gecikme (A100) | WER (LibriSpeech-clean) |
|---------|--------|----------------|------------------------|
| Tiny | 39M | 1× realtime | %5.4 |
| Base | 74M | 1× | %4.1 |
| Small | 244M | 1× | %3.0 |
| Medium | 769M | 1× | %2.7 |
| Large-v3 | 1.55B | 2× | %1.8 |
| Large-v3-turbo | 809M | 8× | %1.58 |
| Whisper-Streaming (2024) | 1.55B | streaming | %2.0 |

### Fine-tuning

2026'da kanonik workflow:

1. Hizalanmış transkript ile 10–100 saatlik target-domain ses topla.
2. `generate_with_loss` callback ile `transformers.Seq2SeqTrainer` çalıştır.
3. Parameter-efficient: attention katmanlarının `q_proj`, `k_proj`, `v_proj`'larında LoRA, <0.3 WER maliyetiyle GPU belleğini 4× azaltır.
4. <10 saatin varsa encoder'ı dondur. Sadece decoder'ı tune et.
5. Whisper'ın kendi tokenizer ve prompt formatını kullan; asla tokenizer değiştirme.

Topluluk sonuçları: Medium'u 20 saatlik medikal dikte üzerinde fine-tune etmek, medikal kelime dağarcığında WER'i %12'den %4.5'e düşürür. Turbo'yu 4 saatlik İzlandaca üzerinde fine-tune etmek WER'i %18'den %6'ya düşürür.

## İnşa Et

### Adım 1: Whisper'ı kutudan çıkar çıkmaz çalıştır

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe(
    "clip.wav",
    language="en",
    task="transcribe",
    temperature=0.0,
    condition_on_previous_text=False,  # kontrolsüz tekrarı engeller
)
print(result["text"])
for seg in result["segments"]:
    print(f"[{seg['start']:.2f}–{seg['end']:.2f}] {seg['text']}")
```

Her zaman override etmen gereken kritik varsayılanlar: `temperature=0.0` (sampling varsayılanı 0.0 → 0.2 → 0.4 … fallback zinciri), `condition_on_previous_text=False` (kaskat halüsinasyon problemini engeller) ve `no_speech_threshold=0.6` (sessizlik algılama).

### Adım 2: Chunked uzun-form

```python
# whisperx, kelime seviyesi timestamp'li uzun-form için 2026 referansı
import whisperx
model = whisperx.load_model("large-v3-turbo", device="cuda", compute_type="float16")
segments = model.transcribe("1hour.mp3", batch_size=16, chunk_size=30)
```

WhisperX şunları ekler: (1) Silero VAD kapısı, (2) wav2vec 2.0 üzerinden kelime seviyesi hizalama, (3) `pyannote.audio` üzerinden diarization. 2026'da üretim transkripsiyonunun beygiri.

### Adım 3: LoRA ile fine-tune

```python
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from peft import LoraConfig, get_peft_model

model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v3-turbo")
lora = LoraConfig(
    r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1, bias="none", task_type="SEQ_2_SEQ_LM",
)
model = get_peft_model(model, lora)
# model.print_trainable_parameters()  -> ~3M eğitilebilir / 809M toplam
```

Sonra standart Trainer döngüsü. Her 1000 adımda checkpoint. Held-out üzerinde WER ile değerlendir.

### Adım 4: Her katmanın ne öğrendiğini incele

```python
# Decoder'ın nereye attend ettiğini görmek için decode sırasında cross-attention ağırlıklarını al.
with torch.inference_mode():
    out = model.generate(
        input_features=features,
        return_dict_in_generate=True,
        output_attentions=True,
    )
# out.cross_attentions: layer × head × step × src_len
```

Heatmap ile görselleştir — decoder adımları encoder frame'lerini taradıkça diagonal hizalama görürsün. Bu diagonal Whisper'ın kelime timestamp'i kavramıdır.

## Kullan

2026 yığını:

| Durum | Seç |
|-----------|------|
| Genel İngilizce, offline | `whisperx` üzerinden Large-v3-turbo |
| Mobil / edge | Quantize edilmiş Whisper-Tiny (int8) ya da Moonshine |
| Çok dilli uzun-form | `whisperx` + diarization üzerinden Large-v3 |
| Düşük-kaynaklı dil | Medium ya da Turbo'yu LoRA ile fine-tune et |
| Streaming (2 sn gecikme) | Whisper-Streaming ya da Parakeet-TDT |
| Kelime seviyesi timestamp'ler | WhisperX (wav2vec 2.0 üzerinden forced alignment) |

`faster-whisper` (CTranslate2 backend), 2026'da en hızlı CPU+GPU çıkarım runtime'ı — vanilla'dan 4× hızlı, çıktı özdeş.

## 2026'da Hâlâ Yayına Çıkan Tuzaklar

- **Sessizlikte halüsinasyon metin.** Caption üzerinde eğitilmiş Whisper "Thanks for watching!", "Subscribe!", şarkı sözleri içerir. Çağırmadan önce her zaman VAD-gate.
- **`condition_on_previous_text` kaskatı.** Bir halüsinasyon sonraki pencereleri kirletir. Chunk'lar arası fluency'e ihtiyacın yoksa `False` ayarla.
- **Kısa klip padding'i.** 30 saniyeye pad edilmiş 2 saniyelik klip, takip eden sessizlikte halüsinasyon yapabilir. `pad=False` kullan ya da VAD-gate.
- **Yanlış mel istatistikleri.** Whisper'ınki yerine librosa'nın mel'lerini kullanmak neredeyse rastgele çıktı üretir. `whisper.audio.log_mel_spectrogram` kullan.

## Yayınla

`outputs/skill-whisper-tuner.md` olarak kaydet. Verilen bir domain için bir Whisper fine-tune ya da çıkarım pipeline'ı tasarla.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Whisper-tarzı bir prompt'u tokenize eder, decoded shape bütçelerini hesaplar ve 10-dakikalık bir klip için chunk programını yazdırır.
2. **Orta.** `faster-whisper`'ı kur, 10-dakikalık bir podcast'i transkribe et, insan transkriptine karşı WER karşılaştır. `language="auto"` ile zorla `language="en"`'i dene.
3. **Zor.** HF `datasets` kullanarak Whisper'ın zorlandığı bir dil seç (örn. Urduca), Medium'u 2 saat üzerinde 2 epoch LoRA ile fine-tune et ve WER farkını raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| 30-sn pencere | Whisper'ın limiti | Sert input cap; daha uzun sesi chunk'la. |
| SOT | Start-of-transcript | `<|startoftranscript|>` decoder prompt'unu başlatır. |
| Timestamp'ler tokeni | Zamansal hizalama | Her 0.02 sn offset'i 51k vocab'ta özel bir token'dır. |
| Turbo | Hızlı varyant | 4-decoder katmanı, 8× hızlı, <%1 WER regresyonu. |
| WhisperX | Uzun-form wrapper'ı | VAD + Whisper + wav2vec hizalama + diarization. |
| LoRA fine-tune | Verimli tuning | Attention'a düşük-rank adapter'lar ekle; param'ın ~%0.3'ünü eğit. |
| Halüsinasyon | Sessiz hata | Whisper gürültü/sessizlikten akıcı İngilizce üretir. |

## İleri Okuma

- [Radford et al. (2022). Whisper paper](https://arxiv.org/abs/2212.04356) — orijinal mimari ve eğitim tarifi.
- [OpenAI (2024). Whisper Large-v3-turbo release](https://github.com/openai/whisper/discussions/2363) — 4-katmanlı decoder, 8× hız artışı.
- [Bain et al. (2023). WhisperX](https://arxiv.org/abs/2303.00747) — uzun-form, kelime-hizalı, diarized.
- [Systran — faster-whisper repo](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-destekli, 4× hızlı.
- [HuggingFace — Whisper fine-tune tutorial](https://huggingface.co/blog/fine-tune-whisper) — kanonik LoRA / full-FT adım adım rehber.
