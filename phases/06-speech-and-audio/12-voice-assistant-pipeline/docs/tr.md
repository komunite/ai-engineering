# Ses Asistanı Pipeline'ı İnşa Et — Faz 6 Bitirme

> 01-11 derslerinden her şey birbirine dikilmiş. Dinleyen, akıl yürüten ve geri konuşan bir ses asistanı inşa et. 2026'da bu çözülmüş bir mühendislik problemi, araştırma problemi değil — ama entegrasyon ayrıntıları yayına çıkıp çıkmayacağına karar veriyor.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 6 · 04, 05, 06, 07, 11; Faz 11 · 09 (Function Calling); Faz 14 · 01 (Agent Loop)
**Süre:** ~120 dakika

## Sorun

End-to-end bir asistan inşa et:

1. Mikrofon girdisini yakalar (16 kHz mono).
2. Kullanıcı konuşmasının başlangıcını/sonunu algılar.
3. Streaming transkribe eder.
4. Transkripti, araç çağırabilen (zamanlayıcı, hava durumu, takvim) bir LLM'e geçirir.
5. LLM metnini bir TTS'e streamler.
6. Sesi kullanıcıya geri çalar.
7. Kullanıcı cevap ortasında keserse durur.

Gecikme hedefi: laptop CPU'da kullanıcı utterance'ını bitirmesinden sonraki 800 ms içinde ilk TTS ses byte'ı. Kalite hedefi: kaçırılan kelime yok, sessizlikte halüsinasyon altyazısı yok, ses klon sızıntısı yok, prompt injection başarısı yok.

## Kavram

![Ses asistanı pipeline'ı: mic → VAD → STT → LLM+tool → TTS → hoparlör](../assets/voice-assistant.svg)

### Yedi bileşen

1. **Ses yakalama.** Mic → 16 kHz mono → 20 ms chunk. Genellikle Python'da `sounddevice` ya da üretimde native AudioUnit/ALSA/WASAPI.
2. **VAD (Ders 11).** Silero VAD @ eşik 0.5, min konuşma 250 ms, sessizlik hang-over 500 ms. "Start" ve "end" sinyalleri.
3. **Streaming STT (Ders 4-5).** Whisper-streaming, Parakeet-TDT ya da Deepgram Nova-3 (API). Partial + final transkript.
4. **Tool calling ile LLM.** GPT-4o / Claude 3.5 / Gemini 2.5 Flash. Tool'lar için JSON schema. Token stream'le.
5. **Streaming TTS (Ders 7).** Kokoro-82M (en hızlı açık) ya da Cartesia Sonic (ticari). 20 LLM token'ı sonrası TTS'i başlat.
6. **Playback.** Hoparlör çıkışı; düşük bant genişliği network'leri için opus-encode.
7. **Kesinti handler'ı.** TTS playback sırasında VAD ateşlerse playback'i durdur, LLM'i iptal et, STT'yi yeniden başlat.

### Karşılaşacağın üç başarısızlık modu

1. **First-word clip.** VAD bir tık geç başlar. Kullanıcının "hey"i eksik. Start eşiğini 0.3'te tut, 0.5'te değil.
2. **Mid-response interrupt karışıklığı.** Kullanıcı kestikten sonra LLM üretmeye devam eder; asistan kullanıcının üstünden konuşur. VAD → cancel-LLM bağla.
3. **Sessizlik halüsinasyonu.** Whisper sessiz warm-up frame'lerinde "Thanks for watching" çıkarır. Her zaman VAD-gate.

### 2026 üretim referans yığınları

| Yığın | Gecikme | Lisans | Notlar |
|-------|---------|---------|-------|
| LiveKit + Deepgram + GPT-4o + Cartesia | 350-500 ms | ticari API | 2026 endüstri varsayılanı |
| Pipecat + Whisper-streaming + GPT-4o + Kokoro | 500-800 ms | çoğunlukla açık | DIY dostu |
| Moshi (full-duplex) | 200-300 ms | CC-BY 4.0 | Tek model; farklı mimari, ders 15 |
| Vapi / Retell (managed) | 300-500 ms | ticari | En hızlı launch; sınırlı customization |
| Whisper.cpp + llama.cpp + Kokoro-ONNX | offline | açık | Gizlilik / edge |

## İnşa Et

### Adım 1: Chunking ile mic capture (pseudokod)

```python
import sounddevice as sd

def mic_stream(chunk_ms=20, sr=16000):
    q = queue.Queue()
    def cb(indata, frames, time, status):
        q.put(indata.copy().flatten())
    with sd.InputStream(channels=1, samplerate=sr, blocksize=int(sr * chunk_ms/1000), callback=cb):
        while True:
            yield q.get()
```

### Adım 2: VAD-gated tur yakalama

```python
def capture_turn(stream, vad, pre_roll_ms=300, silence_ms=500):
    buf, pre, triggered = [], collections.deque(maxlen=pre_roll_ms // 20), False
    silent = 0
    for chunk in stream:
        pre.append(chunk)
        if vad(chunk):
            if not triggered:
                buf = list(pre)
                triggered = True
            buf.append(chunk)
            silent = 0
        elif triggered:
            silent += 20
            buf.append(chunk)
            if silent >= silence_ms:
                return b"".join(buf)
```

### Adım 3: Streaming STT → LLM → TTS

```python
async def turn(audio_bytes):
    transcript = await stt.transcribe(audio_bytes)
    async for token in llm.stream(transcript):
        async for audio in tts.stream(token):
            await speaker.play(audio)
```

### Adım 4: LLM döngüsü içinde tool calling

```python
tools = [
    {"name": "get_weather", "parameters": {"location": "string"}},
    {"name": "set_timer", "parameters": {"seconds": "int"}},
]

async for chunk in llm.stream(user_text, tools=tools):
    if chunk.type == "tool_call":
        result = dispatch(chunk.name, chunk.args)
        continue_streaming(result)
    if chunk.type == "text":
        await tts.stream(chunk.text)
```

### Adım 5: Kesinti işleme

```python
tts_task = asyncio.create_task(tts_loop())
while True:
    chunk = await mic.get()
    if vad(chunk):
        tts_task.cancel()
        await speaker.stop()
        await new_turn()
        break
```

## Kullan

Yedi bileşenin tümünü stub modellerle bağlayan çalıştırılabilir simülasyon için `code/main.py`'ye bak; donanım olmadan bile pipeline şeklini görebilirsin. Gerçek implementasyon için stub'ları şununla değiştir:

- `silero-vad` (`pip install silero-vad`)
- `deepgram-sdk` ya da `openai-whisper`
- `openai` (`gpt-4o`) ya da `anthropic`
- `kokoro` ya da `cartesia`
- I/O için `sounddevice`

## Tuzaklar

- **Sonsuza dek PII loglama.** Tam-tur ses çoğu yargı bölgesinde PII'dir. 30 günlük tutma, at-rest encrypted.
- **Barge-in yok.** Kullanıcılar keser. Asistanının konuşmayı durdurması gerek.
- **Bloklayan TTS.** Senkron TTS event loop'u bloklar. Async ya da ayrı thread kullan.
- **Tool-call hata işleme yok.** Tool'lar başarısız olur. LLM hatayı geri almalı + bir kere retry etmeli, sonra zarif degrade etmeli.
- **Aşırı şevkli halüsinasyon filtreleri.** Aşırı filtrele, asistan "Bunu yapamam." tekrarlar. Az filtrele, her şeyi söyler. Held-out set'te kalibre et.
- **Wake-word seçeneği yok.** Sürekli-dinleme bir gizlilik yükümlülüğü. Bir wake-word kapısı ekle (Porcupine ya da openWakeWord).

## Yayınla

`outputs/skill-voice-assistant-architect.md` olarak kaydet. Bütçe + ölçek + dil + compliance kısıtları verildiğinde tam yığın spec'i üret.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. Stub modüllerle end-to-end bir tam tur simüle eder ve aşama başına gecikmeyi yazdırır.
2. **Orta.** STT stub'ını önceden kaydedilmiş bir `.wav` üzerinde gerçek Whisper modeliyle değiştir. WER ve end-to-end gecikmeyi ölç.
3. **Zor.** Tool calling ekle: `get_weather` (herhangi bir API) ve `set_timer` implement et. LLM'i tool'lar üzerinden yönlendir ve kullanıcı "5 dakikalık zamanlayıcı kur" dediğinde doğru fonksiyonun ateşlendiğini ve sözlü cevabın bunu onayladığını doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Tur | Kullanıcı + asistan round-trip | Bir VAD-sınırlı kullanıcı konuşması + bir LLM-TTS cevabı. |
| Barge-in | Kesinti | Asistan konuşurken kullanıcı konuşur; asistan durur. |
| Wake word | "Hey asistan" | Kısa keyword detektörü; Porcupine, Snowboy, openWakeWord. |
| End-pointing | Tur sonu | Kullanıcının bitirdiğine dair VAD + min-silence kararı. |
| Pre-roll | Konuşma-öncesi buffer | First-word clip'ten kaçınmak için VAD ateşlemeden önce 200-400 ms ses tut. |
| Tool call | Fonksiyon çağrısı | LLM JSON yayar; runtime dispatch eder; sonuç döngüde geri besler. |

## İleri Okuma

- [LiveKit — voice agent quickstart](https://docs.livekit.io/agents/) — üretim seviyesi referans.
- [Pipecat — voice agent examples](https://github.com/pipecat-ai/pipecat) — DIY dostu framework.
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) — managed voice-native yol.
- [Kyutai Moshi](https://github.com/kyutai-labs/moshi) — full-duplex referans (Ders 15).
- [Porcupine wake-word](https://picovoice.ai/products/porcupine/) — wake-word kapılama.
- [Anthropic — tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) — LLM function calling.
