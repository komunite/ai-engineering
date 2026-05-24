# Ses Klonlama ve Ses Dönüştürme

> Ses klonlama metnini başka birinin sesiyle okur. Ses dönüştürme, söylediklerini koruyarak senin sesini başka birinin sesine yeniden yazar. İkisi de aynı ilkelle asılır: konuşmacı kimliğini içerikten ayır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 06 (Konuşmacı Tanıma), Faz 6 · 07 (TTS)
**Süre:** ~75 dakika

## Sorun

2026'da, herhangi birinin sesinin yüksek kaliteli klonunu tüketici GPU'su ile üretmek için 5 saniyelik bir ses klibi yeterli. ElevenLabs, F5-TTS, OpenVoice v2, VoiceBox'ın hepsi zero-shot ya da few-shot klonlama ile yayınlanıyor. Teknoloji hem bir nimet (erişilebilirlik TTS'si, dublaj, yardımcı sesler) hem bir silah (dolandırıcılık aramaları, siyasi deepfake'ler, IP hırsızlığı).

İki yakın akraba görev:

- **Ses klonlama (TTS-tarafı):** metin + 5 saniyelik referans ses → o seste ses.
- **Ses dönüştürme (konuşma-tarafı):** kaynak ses (A kişisi X'i söylüyor) + B kişisinin referans sesi → B'nin X'i söylediği ses.

İkisi de bir dalga formunu (içerik, konuşmacı, prozodi) olarak çarpanlara ayırır ve içeriği bir kaynaktan, konuşmacıyı başka birinden alarak yeniden birleştirir.

2026'da artık altında yayın yaptığın kritik kısıt: **AB'de (AI Act, Ağustos 2026'da uygulanabilir) ve California'da (AB 2905, 2025'te yürürlükte) watermarking ve rıza kapıları yasal olarak zorunlu**. Pipeline'ının duyulmaz bir watermark yayması ve rıza dışı klonları reddetmesi gerek.

## Kavram

![Ses klonlama vs dönüştürme: çarpanlara ayır, konuşmacıyı değiştir, yeniden birleştir](../assets/voice-cloning.svg)

**Zero-shot klonlama.** Binlerce konuşmacı üzerinde eğitilmiş bir modele 5 saniyelik klip geç. Konuşmacı encoder'ı klibi bir konuşmacı embedding'ine eşler; TTS decoder o embedding artı metne koşullanır.

Kullananlar: F5-TTS (2024), YourTTS (2022), XTTS v2 (2024), OpenVoice v2 (2024).

**Few-shot fine-tuning.** Hedef sesin 5-30 dakikasını kaydet. Bir saat boyunca base modeli LoRA-fine-tune et. Kalite "tamam"dan "ayırt edilemez"e sıçrar. Coqui ve ElevenLabs ikisi de bu kalıbı destekler; topluluk bunu F5-TTS ile kullanır.

**Ses dönüştürme (VC).** İki aile:

- **Recognition-synthesis.** İçerik temsili çıkarmak için ASR benzeri model çalıştır (örn. soft fonem posterior'ları, PPG'ler), sonra hedef konuşmacı embedding'i ile yeniden sentezle. Dile ve aksana robust. KNN-VC (2023), Diff-HierVC (2023) tarafından kullanılır.
- **Disentanglement.** İçeriği, konuşmacıyı ve prozodiyi bottleneck'teki latent uzayda ayıran bir autoencoder eğit. Çıkarımda konuşmacı embedding'ini değiştir. Daha düşük kalite ama daha hızlı. AutoVC (2019), VITS-VC varyantları tarafından kullanılır.

**Neural codec tabanlı klonlama (2024+).** VALL-E, VALL-E 2, NaturalSpeech 3, VoiceBox — sesi SoundStream / EnCodec'ten gelen discrete token'lar olarak ele alır, codec token'ları üzerinde büyük autoregressive ya da flow-matching model eğit. Kısa prompt'larda ElevenLabs'a kıyaslanabilir kalite.

### Etik parçası, bir eklenti değil

**Watermarking.** PerTh (Perth) ve SilentCipher (2024), sese ~16-32 bit ID'yi algılanamaz şekilde gömerler. Yeniden kodlama, streaming ve yaygın düzenlemeleri atlatır. Üretime hazır open source.

**Rıza kapıları.** Her klonlanmış çıktıyı doğrulanabilir bir rıza kaydıyla eşleştirmek zorunda. "Ben, Rohit, 2026-04-22'de bu sesi X amacı için yetkilendiriyorum." Tamper-evident bir log'da sakla.

**Algılama.** AASIST, RawNet2 ve Wav2Vec2-AASIST detektör olarak yayınlanır. ASVspoof 2025 challenge, ElevenLabs, VALL-E 2 ve Bark çıktılarına karşı state-of-the-art detektörler için %0.8–2.3 EER yayınladı.

### Rakamlar (2026)

| Model | Zero-shot? | SECS (hedef sim) | WER (intel.) | Param |
|-------|-----------|--------------------|--------------|--------|
| F5-TTS | Evet | 0.72 | %2.1 | 335M |
| XTTS v2 | Evet | 0.65 | %3.5 | 470M |
| OpenVoice v2 | Evet | 0.70 | %2.8 | 220M |
| VALL-E 2 | Evet | 0.77 | %2.4 | 370M |
| VoiceBox | Evet | 0.78 | %2.1 | 330M |

SECS > 0.70 çoğu dinleyici için hedeften genellikle ayırt edilemez.

## İnşa Et

### Adım 1: Recognition-synthesis ile ayrıştır (main.py'de sadece kod demosu)

```python
def clone_pipeline(ref_audio, text, target_embedder, tts_model):
    speaker_emb = target_embedder.encode(ref_audio)
    mel = tts_model(text, speaker=speaker_emb)
    return vocoder(mel)
```

Kavramsal olarak basit; uygulama kütlesi `tts_model` ve konuşmacı encoder'ındadır.

### Adım 2: F5-TTS ile zero-shot klon

```python
from f5_tts.api import F5TTS
tts = F5TTS()
wav = tts.infer(
    ref_file="rohit_5s.wav",
    ref_text="The quick brown fox jumps over the lazy dog.",
    gen_text="Please add milk and bread to my list.",
)
```

Referans transkript, sesle tam olarak eşleşmek zorundadır; uyuşmazlık hizalamayı kırar.

### Adım 3: KNN-VC ile ses dönüştürme

```python
import torch
from knnvc import KNNVC  # 2023 model, https://github.com/bshall/knn-vc
vc = KNNVC.load("wavlm-base-plus")
out_wav = vc.convert(source="my_voice.wav", target_pool=["alice_1.wav", "alice_2.wav"])
```

KNN-VC, kaynak ve hedef havuz için frame başına embedding çıkarmak için WavLM çalıştırır, sonra her kaynak frame'i havuzdaki en yakın komşusuyla değiştirir. Non-parametric, hedef konuşmanın bir dakikasıyla çalışır.

### Adım 4: Bir watermark göm

```python
from silentcipher import SilentCipher
sc = SilentCipher(model="2024-06-01")
payload = b"consent_id:abc123;ts:1745353200"
watermarked = sc.embed(wav, sr=24000, message=payload)
detected = sc.detect(watermarked, sr=24000)   # payload byte'larını döndürür
```

~32 bit payload, MP3 yeniden kodlama ve hafif gürültü sonrası algılanabilir.

### Adım 5: Rıza kapısı

```python
def cloned_inference(text, ref_audio, consent_record):
    assert verify_signature(consent_record), "İmzalı rıza gerekli"
    assert consent_record["speaker_id"] == hash_speaker(ref_audio)
    wav = tts.infer(ref_file=ref_audio, gen_text=text)
    wav = watermark(wav, payload=consent_record["id"])
    return wav
```

## Kullan

2026 yığını:

| Durum | Seç |
|-----------|------|
| 5-sn zero-shot klon, open-source | F5-TTS ya da OpenVoice v2 |
| Ticari üretim klonlama | ElevenLabs Instant Voice Clone v2.5 |
| Ses dönüştürme (yeniden yazma) | KNN-VC ya da Diff-HierVC |
| Çok konuşmacılı fine-tune | StyleTTS 2 + konuşmacı adapter'ı |
| Cross-lingual klonlama | XTTS v2 ya da VALL-E X |
| Deepfake algılama | Wav2Vec2-AASIST |

## Tuzaklar

- **Yanlış hizalanmış referans transkripti.** F5-TTS ve benzerleri referans metninin referans sesle tam eşleşmesini gerektirir, noktalama dahil.
- **Reverberant referans.** Eko klonu öldürür. Kuru, close-mic kaydet.
- **Duygusal uyuşmazlık.** "Neşeli" eğitim referansı her şeyin neşeli klonunu üretir. Referans duygusunu hedef kullanıma uydur.
- **Dil sızıntısı.** İngilizce bir konuşmacıyı klonlayıp modelden Fransızca konuşmasını istemek genellikle aksanı yine de taşır; cross-lingual modeller kullan (XTTS, VALL-E X).
- **Watermark yok.** Ağu 2026'dan itibaren AB'de yasal olarak yayınlanamaz.

## Yayınla

`outputs/skill-voice-cloner.md` olarak kaydet. Rıza kapısı + watermark + kalite hedefiyle klonlama ya da dönüştürme pipeline'ı tasarla.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Swap öncesi ve sonrası iki "konuşmacı" arasında kosinüs hesaplayarak konuşmacı-embedding değişimini gösterir.
2. **Orta.** Kendi sesini klonlamak için OpenVoice v2 kullan. Referans ile klon arası SECS ölç. Whisper üzerinden CER ölç.
3. **Zor.** SilentCipher watermark'ını 20 klona uygula, 128 kbps MP3 encode+decode'dan geçir, payload'u algıla. Bit-doğruluğunu raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Zero-shot klon | 5 saniye yeter | Pretrained model + konuşmacı embedding'i; eğitim yok. |
| PPG | Phonetic posteriorgram | Dil-bağımsız içerik temsili olarak kullanılan frame başına ASR posterior'ları. |
| KNN-VC | Nearest-neighbor dönüştürme | Her kaynak frame'i en yakın hedef-havuz frame'i ile değiştir. |
| Neural codec TTS | VALL-E tarzı | EnCodec/SoundStream token'ları üzerinde AR model. |
| Watermark | Duyulmaz imza | Sese gömülmüş bit'ler, yeniden kodlama sonrası kalır. |
| SECS | Klonlama fidelity'si | Hedef ve klon konuşmacı embedding'leri arası kosinüs. |
| AASIST | Deepfake detektörü | Anti-spoof model; sentezlenmiş konuşmayı algılar. |

## İleri Okuma

- [Chen et al. (2024). F5-TTS](https://arxiv.org/abs/2410.06885) — open-source SOTA zero-shot klonlama.
- [Baevski et al. / Microsoft (2023). VALL-E](https://arxiv.org/abs/2301.02111) ve [VALL-E 2 (2024)](https://arxiv.org/abs/2406.05370) — neural-codec TTS.
- [Qian et al. (2019). AutoVC](https://arxiv.org/abs/1905.05879) — disentanglement tabanlı ses dönüştürme.
- [Baas, Waubert de Puiseau, Kamper (2023). KNN-VC](https://arxiv.org/abs/2305.18975) — retrieval tabanlı VC.
- [SilentCipher (2024) — Audio Watermarking](https://github.com/sony/silentcipher) — üretime hazır 32-bit ses watermark.
- [ASVspoof 2025 results](https://www.asvspoof.org/) — detektör vs sentezleyici silah yarışı, 2026'da güncellendi.
