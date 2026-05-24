# Ses-Dil Modelleri — Qwen2.5-Omni, Audio Flamingo, GPT-4o Audio

> 2026 ses-dil modelleri konuşma + çevresel ses + müzik üzerinde akıl yürütür. Qwen2.5-Omni-7B, MMAU-Pro'da GPT-4o Audio'ya eşleşir. Audio Flamingo Next, LongAudioBench'te Gemini 2.5 Pro'yu yener. Açık ve kapalı arası boşluk esasen kapandı — multi-audio görevler hariç; orada herkes rastgele seviyesinde.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 6 · 04 (ASR), Faz 12 · 03 (Görü-Dil Modelleri), Faz 7 · 10 (Ses Transformer'ları)
**Süre:** ~45 dakika

## Sorun

5 saniyelik sesin var: köpek havlıyor, biri "dur!" diye bağırıyor, sonra sessizlik. Faydalı sorular birden çok eksene yayılır:

- **Transkripsiyon.** "Ne söylendi?" — ASR bölgesi.
- **Semantik akıl yürütme.** "Bu kişi tehlikede mi?" — havlama + bağırma + sessizliğin ortak anlaşılmasını gerektirir.
- **Müzik akıl yürütmesi.** "Melodi çalan enstrümanlar hangileri?"
- **Uzun-ses retrieval.** "Bu 90 dakikalık derste eğitmen gradient descent'i nerede anlattı?"

Tek bir prompt'la hepsini cevaplayan tek bir model bir **ses-dil modeli**dir (LALM / ALM). Saf ASR'den ayrı: LALM'lar sadece transkript değil, serbest-form doğal-dil cevaplar üretir.

## Kavram

![Ses-dil modeli: ses encoder + projector + LLM decoder](../assets/alm-architecture.svg)

### Üç bileşenli şablon

2026 her LALM'ın aynı iskeleti vardır:

1. **Ses encoder.** Whisper encoder · BEATs · CLAP · WavLM · ya da model başına custom encoder.
2. **Projector.** Ses-encoder özniteliklerini LLM'in token embedding uzayına köprüleyen lineer ya da MLP.
3. **LLM.** Llama / Qwen / Gemma tabanlı decoder. İç içe metin + ses token'ları alır; metin üretir.

Eğitim:

- **Aşama 1.** Encoder + LLM'i dondur; sadece projector'u ASR / captioning verisi üzerinde eğit.
- **Aşama 2.** Instruction-following ses görevlerinde (QA, akıl yürütme, müzik anlama) full / LoRA fine-tune.
- **Aşama 3 (opsiyonel).** Voice-in / voice-out, bir konuşma decoder'ı ekler. Qwen2.5-Omni ve AF3-Chat bunu yapar.

### 2026 model haritası

| Model | Backbone | Ses encoder | Çıktı modalitesi | Erişim |
|-------|----------|---------------|-----------------|--------|
| Qwen2.5-Omni-7B | Qwen2.5-7B | Custom + Whisper | metin + konuşma | Apache-2.0 |
| Qwen3-Omni | Qwen3 | Custom | metin + konuşma | Apache-2.0 |
| Audio Flamingo 3 | Qwen2 | AF-CLAP | metin | NVIDIA non-commercial |
| Audio Flamingo Next | Qwen2 | AF-CLAP v2 | metin | NVIDIA non-commercial |
| SALMONN | Vicuna | Whisper + BEATs | metin | Apache-2.0 |
| LTU / LTU-AS | Llama | CAV-MAE | metin | Apache-2.0 |
| GAMA | Llama | AST + Q-Former | metin | Apache-2.0 |
| Gemini 2.5 Flash/Pro (kapalı) | Gemini | proprietary | metin + konuşma | API |
| GPT-4o Audio (kapalı) | GPT-4o | proprietary | metin + konuşma | API |

### Benchmark gerçeği kontrolü (2026)

**MMAU-Pro.** Konuşma / ses / müzik / karışık'ı kapsayan 1800 QA çifti. Multi-audio alt kümesi dahil.

| Model | Genel | Konuşma | Ses | Müzik | Multi-audio |
|-------|---------|--------|-------|-------|-------------|
| Gemini 2.5 Pro | ~%60 | %73.4 | %51.9 | %64.9 | ~%22 |
| Gemini 2.5 Flash | ~%57 | %73.4 | %50.5 | %64.9 | %21.2 |
| GPT-4o Audio | %52.5 | — | — | — | %26.5 |
| Qwen2.5-Omni-7B | %52.2 | %57.4 | %47.6 | %61.5 | ~%20 |
| Audio Flamingo 3 | ~%54 | — | — | — | — |
| Audio Flamingo Next | LongAudioBench'te SOTA | — | — | — | — |

**Multi-audio sütunu herkes için utanç verici.** 4-seçenekli çoktan seçmelide rastgele şans = %25; çoğu model orada puanlıyor. LALM'lar hâlâ iki klibi karşılaştırmakta zorlanıyor.

### LALM'ların 2026'da yararlı olduğu yerler

- **Çağrı merkezi kayıtlarının compliance audit'i.** "Agent gerekli açıklamayı yaptı mı?"
- **Erişilebilirlik.** Sağır kullanıcılara ses olaylarını anlat (sadece transkripsiyon değil).
- **İçerik moderasyonu.** Şiddet içeren dili + tehditkâr tonu + arka plan bağlamını algıla.
- **Podcast / toplantı chapter'lama.** Sadece konuşmacı sırası değil, semantik özet.
- **Müzik katalog analizi.** "B-section'da key change'i olan tüm parçaları bul."

### (Henüz) yararlı OLMADIKLARI yerler

- İnce ayrıntılı müzik teorisi (akor seviyesinin altı).
- Uzun konuşmalar üzerinde konuşmacı-atfedilmiş akıl yürütme (10 dakikadan sonra bozulur).
- Multi-audio karşılaştırması (%22-26 zar zor rastgele üstü).
- Real-time streaming akıl yürütme (çoğu offline batch çıkarımı).

## İnşa Et

### Adım 1: Qwen2.5-Omni sorgula

```python
from transformers import AutoModelForCausalLM, AutoProcessor

processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-Omni-7B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Omni-7B", torch_dtype="auto")

audio, sr = load_wav("clip.wav", sr=16000)
messages = [{
    "role": "user",
    "content": [
        {"type": "audio", "audio": audio},
        {"type": "text", "text": "What sounds do you hear, and what's happening?"},
    ],
}]
inputs = processor.apply_chat_template(messages, tokenize=True, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=200)
print(processor.decode(output[0], skip_special_tokens=True))
```

### Adım 2: Projector kalıbı

```python
import torch.nn as nn

class AudioProjector(nn.Module):
    def __init__(self, audio_dim=1280, llm_dim=4096):
        super().__init__()
        self.down = nn.Linear(audio_dim, llm_dim)
        self.act = nn.GELU()
        self.up = nn.Linear(llm_dim, llm_dim)

    def forward(self, audio_features):
        return self.up(self.act(self.down(audio_features)))
```

Hepsi bu. Projector genellikle 1-3 lineer katmandır. Onu ASR çiftleri (ses → transkript) üzerinde eğitmek Aşama-1 pretext görevidir.

### Adım 3: MMAU / LongAudioBench benchmark'ı

```python
from datasets import load_dataset
mmau = load_dataset("MMAU/MMAU-Pro")

correct = 0
for item in mmau["test"]:
    answer = call_model(item["audio"], item["question"], item["choices"])
    if answer == item["correct_choice"]:
        correct += 1
print(f"Accuracy: {correct / len(mmau['test']):.3f}")
```

Kategori başına (konuşma / ses / müzik / multi-audio) ayrı raporla. Toplu rakamlar modelin nerede başarısız olduğunu gizler.

## Kullan

| Görev | 2026 seçimi |
|------|-----------|
| Serbest-form ses QA (açık) | Qwen2.5-Omni-7B |
| Uzun seste en iyi açık | Audio Flamingo Next |
| En iyi kapalı | Gemini 2.5 Pro |
| Voice-in / voice-out agent | Qwen2.5-Omni ya da GPT-4o Audio |
| Müzik akıl yürütme | Audio Flamingo 3 ya da 2 (müzik-özelleşmiş AF-CLAP) |
| Çağrı merkezi audit | Politika doc'larında RAG ile API üzerinden Gemini 2.5 Pro |

## Tuzaklar

- **Multi-audio'da aşırı güven.** Görevin "hangi klipte X var" gerektiriyorsa, random-chance seviyesinde performans gerçek.
- **Uzun-ses bozulması.** 10 dakika sonrası, çoğu modelin konuşmacı atfı bozulur. Önce diarize et (Ders 6), sonra özetle.
- **Sessizlikte halüsinasyon.** Whisper encoder kullanan LALM'lar tarafından miras alınan aynı Whisper-tarzı sorun. VAD-gate.
- **Benchmark cherry-picking.** Satıcı blog post'ları en iyi durumdaki kategorileri vurgular. MMAU-Pro multi-audio alt kümesini kendin çalıştır.

## Yayınla

`outputs/skill-alm-picker.md` olarak kaydet. Verilen bir ses-anlama görevi için LALM + benchmark alt kümesi + çıktı-modalitesi (metin vs konuşma) seç.

## Alıştırmalar

1. **Kolay.** Toy bir projector kalıbı + (ses-embedding, metin-token) → çıktı token'ları sahte LALM yönlendirmesi görmek için `code/main.py`'yi çalıştır.
2. **Orta.** Qwen2.5-Omni-7B'yi 100 MMAU-Pro konuşma maddesinde puanla. Makalenin raporladığı rakamla karşılaştır.
3. **Zor.** Minimal bir ses-captioning baseline'ı kur: BEATs encoder + 2-katmanlı projector + frozen Llama-3.2-1B. AudioCaps üzerinde sadece projector'ı fine-tune et. Clotho-AQA'da SALMONN ile karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| LALM | Ses ChatGPT'si | Ses encoder + projector + LLM decoder. |
| Projector | Adapter | Ses özniteliklerini LLM embedding uzayına eşleyen küçük MLP. |
| MMAU | Benchmark | Konuşma, ses, müzik arasında 10k ses-QA çifti. |
| MMAU-Pro | Daha zor MMAU | 1800 multi-audio / akıl-yürütme ağır soru. |
| LongAudioBench | Uzun-form değerlendirme | Semantik sorgularla çok dakikalı klipler. |
| Voice-in / voice-out | Konuşma-nativ | Model konuşmayı yutar ve metin sapma olmadan konuşma yayar. |

## İleri Okuma

- [Chu et al. (2024). Qwen2-Audio](https://arxiv.org/abs/2407.10759) — referans mimari.
- [Alibaba (2025). Qwen2.5-Omni](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) — speech-in-speech-out.
- [NVIDIA (2025). Audio Flamingo 3](https://arxiv.org/abs/2507.08128) — açık uzun-ses lideri.
- [NVIDIA (2026). Audio Flamingo Next](https://arxiv.org/abs/2604.10905) — LongAudioBench SOTA.
- [Tang et al. (2023). SALMONN](https://arxiv.org/abs/2310.13289) — dual-encoder öncüsü.
- [MMAU-Pro leaderboard](https://mmaubenchmark.github.io/) — canlı 2026 sıralaması.
