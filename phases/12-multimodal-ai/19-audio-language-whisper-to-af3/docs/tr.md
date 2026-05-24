# Audio-Language Modelleri: Whisper'dan Audio Flamingo 3'e Yay

> Whisper (Radford et al., Aralık 2022) speech recognition'ı çözdü — 680k saat zayıf-supervised çok dilli konuşma, basit bir encoder-decoder transformer, sonraki her ASR yayınının kaynak gösterdiği bir benchmark. Ama tanıma akıl yürütme değil. "Bu kayıtta hangi enstrümanlar var" ya da "konuşmacı hangi duyguyu ifade ediyor" ya da "3. dakikada ne oldu" sormak transcription değil, audio anlama gerektirir. Qwen-Audio, SALMONN, LTU ve NVIDIA'nın Audio Flamingo 3'ü (AF3, Temmuz 2025) kademeli olarak bu yığını inşa etti: Whisper sınıfı encoder'ları tut, Q-former'ları cıvatala, audio-text instruction verisi üzerinde eğit, chain-of-thought akıl yürütme ekle. Bu ders yayı yürüyor.

**Tür:** Yapım
**Diller:** Python (stdlib, log-Mel spectrogram + audio Q-former iskeleti)
**Ön koşullar:** Faz 6 (Konuşma ve Ses), Faz 12 · 03 (Q-Former)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Bir waveform'dan log-Mel spectrogram hesapla: windowing, FFT, filter bank'lar, log transform.
- Encoder seçeneklerini karşılaştır: Whisper encoder, BEATs, AF-Whisper hibrit. Her biri ne zaman kazanır.
- Bir audio Q-former inşa et: spectrogram patch'lerine cross-attend eden N öğrenilebilir query.
- Cascaded (Whisper-sonra-LLM) vs end-to-end audio-LLM eğitimini açıkla: end-to-end akıl yürütme için neden daha iyi ölçekler.

## Sorun

Speech recognition Whisper tarafından çözüldü. OCR-of-audio bir commodity. Ama "commodity" transcription'da durur. Model duyduğunu — zamanlama, konuşmacılar, duygu, müzik yapısı, çevresel sesler — üzerinde akıl yürütemezse, yalnızca transcription ürün özelliklerini güdemez.

Üç aşikar yol:

1. Cascade: Whisper transcribe eder, LLM transcript üzerinde akıl yürütür. Saf-konuşma senaryoları için çalışır. Müzik, çevresel ses, çoklu-konuşmacı örtüşmesi, duygu için başarısız olur.

2. End-to-end audio-LLM: bir ses encoder ses token'larını doğrudan LLM'e besler, transcription'ı atlar. Akustik bilgiyi (duygu, konuşmacı, çevre) korur. Yeni eğitim verisi ister.

3. Hibrit: hem transcribe edebilen hem akıl yürütebilen audio encoder + text decoder. Qwen-Audio ve Audio Flamingo bu yolu seçer.

## Kavram

### Log-Mel spectrogram: input feature

Her ses encoder aynı feature ile başlar: log-Mel spectrogram.

1. 16 kHz'e resample.
2. 25ms pencereli, 10ms hop'lu short-time Fourier transform.
3. FFT sonucunun büyüklüğünü al.
4. Algısal frekansa warp etmek için Mel filter bank'ları (tipik olarak 0-8000 Hz log-aralıklı 80 filtre) uygula.
5. Dinamik aralık için log compress (log(1 + x)).

Sonuç: (T, 80) shape'inde 2D dizi, T zaman frame sayısı. 100 Hz frame oranında 30 saniyelik klip için: (3000, 80).

### Whisper'ın encoder'ı

Whisper'ın encoder'ı log-Mel spectrogram'ı zaman frame'leri dizisi olarak işleyen 12 katmanlı ViT tarzı transformer. Çıktı: zaman frame başına bir hidden-state vektörü.

ASR için Whisper'ın decoder'ı encoder çıktısına koşullu metin token'ları üreten cross-attention transformer. Standart encoder-decoder.

ALM'ler (audio-LLM'ler) için encoder çıktısını farklı bir LLM'e input olarak istersin. Kalıp: donmuş Whisper encoder, eğitilebilir Q-former, donmuş ya da tune edilmiş LLM.

### BEATs ve audio-spesifik encoder'lar

Whisper konuşma-baskın veride eğitildi. Müzik ve çevresel ses için daha zayıf.

BEATs (Chen et al., 2022) AudioSet üzerinde eğitilmiş self-supervised transformer. Aynı parametre sayısında Whisper'dan müzik ve çevresel sesleri daha iyi yakalar.

AF-Whisper (Audio Flamingo 3'ün hibriti): ses input olarak Whisper + BEATs feature'larını birleştir. Whisper dilsel sinyal taşır, BEATs akustik sinyal taşır.

### Audio Q-former

BLIP-2'nin görsel Q-former'ı ile aynı kalıp. Sabit sayıda öğrenilebilir query (sıklıkla 32 ya da 64) ses encoder'ın çıkış frame'lerine cross-attend eder. Query'ler LLM tarafından tüketilen ses token'ı olur.

Eğitim hizalama aşaması: yalnızca Q-former, audio-text çiftleri (AudioCaps, Clotho) üzerinde contrastive + captioning loss'ları. Instruction aşaması: end-to-end, LLM'i aç, instruction verisi üzerinde eğit.

### Yay — SALMONN, Qwen-Audio, AF3

SALMONN (Tang et al., 2023): Whisper + BEATs + Q-former + LLaMA. Ciddi akıl yürütme yetenekli ilk açık audio-LLM. MMAU'da ~0.55 compozite benchmark.

Qwen-Audio (Chu et al., 2023): benzer mimari, daha zengin dataset'te eğitildi, çoklu-tur diyalog için tune edildi. MMAU ~0.60.

LTU — Listen, Think, Understand (Gong et al., 2023): açık akıl yürütme verisi, ses klipleri üzerinde chain-of-thought odağı. Daha küçük ama daha odaklı.

Audio Flamingo 3 (Goel et al., Temmuz 2025): şu anki açık SOTA. 8B LLM backbone (Qwen2 7B), Whisper-large encoder BEATs ile concat, 64-query Q-former, 1M+ audio-text instruction çifti üzerinde eğitim. MMAU 0.72, bazı alt görevlerde proprietary frontier'ı eşler.

AF3 ayrıca ses için on-demand chain-of-thought tanıtır: model son cevaptan önce opsiyonel olarak thinking token'ları yayar ("önce enstrümanları tanımlayayım: ..."). Thinking etkinleştirildiğinde karmaşık akıl yürütme görevlerinde doğruluk 3-5 puan yükseliyor.

### Cascaded vs end-to-end

Cascaded pipeline:

1. Whisper sesi transcribe eder → metin.
2. LLM metin üzerinde akıl yürütür.

"Bu podcast'i özetle" için mükemmel çalışır. Şunlar için başarısız:
- "Bu şarkının ruh hali nedir?" — ruh hali kelimelerde değil, sesde.
- "Kim konuşuyor, Alice mı Bob mu?" — konuşmacı identification gerektirir.
- "Patlama hangi saniyede oluyor?" — temporal grounding metinde kaybolur.
- "Bu gerçek mi üretilmiş ses mi?" — deepfake detection akustik feature gerektirir.

End-to-end akustik sinyali korur. Qwen-Audio ve AF3 müziği, çevreyi ve duyguyu natively halleder.

### 2026 üretim tarifi

Yeni bir audio-understanding ürünü için:

- Cascaded eğer: transcription hedef, müzik yok, duygu çıkarımı yok.
- AF3 / Qwen-Audio-family eğer: müzik, duygu, çoklu-konuşmacı ya da karmaşık ses akıl yürütme.

Cascaded daha ucuz ve daha basit. End-to-end daha yetenekli.

### MMAU — ses akıl yürütme benchmark'ı

MMAU (Massive Multimodal Audio Understanding) 2024-2025 ses akıl yürütme benchmark'ı:

- Konuşma, müzik, çevresel sesler boyunca 10,000 audio-text QA çifti.
- Sınıflandırma, temporal akıl yürütme, causal akıl yürütme, açık uçlu QA kapsar.
- Cascaded pipeline'ların sistematik olarak kaçırdığını test eder.

Açık SOTA (AF3) 0.72'de; proprietary frontier ~0.78 (Gemini 2.5 Pro, Claude Opus 4.7). Fark VideoMME'nin açık-vs-kapalı farkından daha küçük, audio-LLM'lerin olgunlaştığını gösteriyor.

## Kullan

`code/main.py`:

- Stdlib'de log-Mel spectrogram hesabını uygular: windowing, naif DFT, Mel filter-bank.
- Audio Q-former iskeleti: encoder çıkış frame'leri verildiğinde Q, K, V, attention hesapla ve N token yay.
- Oyuncak bir görevde cascaded-vs-end-to-end karşılaştırması.

## Yayınla

Bu ders `outputs/skill-audio-llm-pipeline-picker.md` üretir. Bir ses görevi (transcription, müzik etiketleme, duygu çıkarımı, çoklu-konuşmacı diarization, çevre sınıflandırması) verildiğinde, cascaded, end-to-end AF3 ya da bir hibrit seçer.

## Alıştırmalar

1. 16kHz'de 30 saniyelik klip için 25ms pencere, 10ms hop, 80 Mel bin'de log-Mel spectrogram boyutunu hesapla. 48kHz'de nasıl değişir?

2. Whisper müzikte neden underperform eder? BEATs Whisper'ın yakalamadığı hangi ses feature'larını yakalar?

3. 64 query vs 32 audio Q-former: hangi görev karmaşıklığında 64 değer? 32 ne için compute tasarrufu sağlar?

4. AF3 Bölüm 4'ü on-demand thinking üzerine oku. Chain-of-thought'un en çok yardım ettiği üç ses görevi öner.

5. AF3 çıktısı kullanarak minimal bir diarization pipeline uygula. Konuşmacı değişimlerini nasıl sinyalliyorsun?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Log-Mel spectrogram | "Mel feature'ları" | Mel filter bank'larından sonra log-magnitude değerlerinin 2D (zaman, frekans) dizisi |
| Audio Q-former | "Audio Perceiver" | Ses encoder çıktısından LLM'i besleyen sabit-uzunluklu query'lere cross-attention bottleneck |
| Cascaded | "ASR-sonra-LLM" | Whisper'ın transcribe ettiği ve metin LLM'in akıl yürüttüğü pipeline; akustik bilgi kaybeder |
| End-to-end | "Audio-LLM" | Ses feature'ları Q-former üzerinden LLM'e doğrudan girer; akustik sinyali korur |
| BEATs | "Audio AudioSet encoder" | AudioSet üzerinde eğitilmiş SSL transformer; müzik + çevresel seslerde güçlü |
| MMAU | "Audio akıl yürütme bench'i" | Konuşma, müzik, çevre boyunca 10k QA çifti; 2024 eval standardı |
| On-demand thinking | "Audio CoT" | Model son cevaptan önce opsiyonel olarak akıl yürütme token'ları yayar, 3-5 puan doğruluk artırır |

## İleri Okuma

- [Radford et al. — Whisper (arXiv:2212.04356)](https://arxiv.org/abs/2212.04356)
- [Chu et al. — Qwen-Audio (arXiv:2311.07919)](https://arxiv.org/abs/2311.07919)
- [Goel et al. — Audio Flamingo 3 (arXiv:2507.08128)](https://arxiv.org/abs/2507.08128)
- [Tang et al. — SALMONN (arXiv:2310.13289)](https://arxiv.org/abs/2310.13289)
- [Gong et al. — LTU (arXiv:2305.10790)](https://arxiv.org/abs/2305.10790)
