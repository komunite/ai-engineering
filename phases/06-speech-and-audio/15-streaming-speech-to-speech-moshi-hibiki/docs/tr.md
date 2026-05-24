# Streaming Speech-to-Speech — Moshi, Hibiki ve Full-Duplex Diyalog

> 2024-2026 ses AI'ı yeniden tanımladı. Moshi, 200 ms gecikmede aynı anda dinleyen ve konuşan tek bir model yayınlıyor. Hibiki konuşmadan-konuşmaya çeviriyi chunk-by-chunk yapıyor. İkisi de ASR → LLM → TTS pipeline'ını terk edip Mimi codec token'ları üzerinde birleşik full-duplex mimariye geçiyor. Bu yeni referans tasarım.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 6 · 13 (Nöral Ses Codec'leri), Faz 6 · 11 (Real-Time Ses), Faz 7 · 05 (Full Transformer)
**Süre:** ~75 dakika

## Sorun

Ders 11 + 12'den inşa edilmiş her ses ajanının 300-500 ms civarında temel bir latency tabanı vardır: VAD ateşler, STT işler, LLM akıl yürütür, TTS üretir. Her aşamanın kendi minimum gecikmesi var. Tune edip paralelleştirebilirsin, ama pipeline şekli seni sınırlar.

Moshi (Kyutai, 2024-2026) farklı bir soru soruyor: ya pipeline yoksa? Tek bir model sesi doğrudan alıp doğrudan ses çıkarsa, sürekli, gereken bir aşama yerine ara bir "iç monolog" olarak metinle?

Cevap **full-duplex speech-to-speech**. Teorik gecikme 160 ms (80 ms Mimi frame + 80 ms akustik gecikme). Tek bir L4 GPU'da pratik gecikme 200 ms. Sınıfının en iyisi pipeline'lı ses ajanının yarısı.

## Kavram

![Moshi mimarisi: iki paralel Mimi stream + iç-monolog metin](../assets/moshi-hibiki.svg)

### Moshi mimarisi

**Girdiler.** İki Mimi codec stream'i, ikisi de 12.5 Hz × 8 codebook'ta:

- Stream 1: kullanıcı sesi (Mimi-encoded, sürekli geliyor)
- Stream 2: Moshi'nin kendi sesi (Moshi tarafından üretilen)

**Transformer.** 7B-paramlı bir Temporal Transformer her iki stream'i ve bir metin "iç monolog" stream'ini işler. Her 80 ms adımda:

1. En son kullanıcı Mimi token'larını tüketir (8 codebook).
2. En son Moshi Mimi token'larını tüketir (8 codebook, üretildiği gibi).
3. Bir sonraki Moshi metin token'ını üretir (iç monolog).
4. Küçük bir Depth Transformer üzerinden bir sonraki Moshi Mimi token'larını üretir (8 codebook).

Üç stream — kullanıcı sesi, Moshi sesi, Moshi metni — paralel çalışır. Moshi konuşurken kullanıcıyı duyabilir; kullanıcı kestiğinde kendini kesebilir; ana utterance'ını bozmadan back-channel ("mhm") yapabilir.

**Depth transformer.** Bir frame içinde 8 codebook paralel tahmin edilmez — inter-codebook bağımlılıkları vardır. Küçük 2-katmanlı bir "depth transformer" onları 80 ms içinde sırayla tahmin eder. Bu AR codec LM'leri için standart faktörizasyondur (VALL-E, VibeVoice tarafından da kullanılır).

### İç-monolog metin neden yardım eder

Açık metin olmadan, modelin akustik stream'inde dili implicit modellemesi gerekir. Moshi'nin içgörüsü: onu sesle birlikte metin token'ları yaymaya zorla. Metin stream'i esasen Moshi'nin söylediklerinin transkriptidir. Bu semantik tutarlılığı iyileştirir, dil modeli head'ini değiştirmeyi kolaylaştırır ve sana bedava transkript verir.

### Hibiki: streaming konuşma-konuşma çeviri

Aynı mimari, çeviri çiftleri üzerinde eğitilmiş. Kaynak ses in, hedef-dil ses out, sürekli. Hibiki-Zero (Şub 2026) kelime seviyesi hizalanmış eğitim verisi ihtiyacını ortadan kaldırır — cümle seviyesi veri + latency optimizasyonu için GRPO reinforcement learning kullanır.

Başlangıçta dört dil çifti destekleniyor; yeni bir dile ≈1000 saatle adapte edilebilir.

### Daha geniş Kyutai yığını (2026)

- **Moshi** — full-duplex diyalog (önce Fransızca, İngilizce iyi destekli)
- **Hibiki / Hibiki-Zero** — eş zamanlı konuşma çevirisi
- **Kyutai STT** — streaming ASR (500 ms ya da 2.5 sn look-ahead)
- **Kyutai Pocket TTS** — CPU'da çalışan 100M-param TTS (Oca 2026)
- **Unmute** — bunları public sunucularda birleştiren tam pipeline

L40S GPU'da throughput: 3× real-time'da 64 eş zamanlı session.

### Sesame CSM — kuzen

Sesame CSM (2025) benzer fikir kullanır — Mimi codec head ile Llama-3 backbone. Ama CSM tek yönlüdür (bağlam + metin alır, konuşma üretir), full-duplex değil. Piyasada en iyi "voice presence" TTS'si; Moshi'nin full-duplex yeteneği ile tam aynı değil.

### 2026 performans rakamları

| Model | Gecikme | Kullanım | Lisans |
|-------|---------|----------|---------|
| Moshi | 200 ms (L4) | full-duplex İngilizce / Fransızca diyalog | CC-BY 4.0 |
| Hibiki | 12.5 Hz framerate | Fransızca ↔ İngilizce streaming çeviri | CC-BY 4.0 |
| Hibiki-Zero | aynı | 5 dil çifti, hizalanmış veri yok | CC-BY 4.0 |
| Sesame CSM-1B | 200 ms TTFA | bağlam-koşullu TTS | Apache-2.0 |
| GPT-4o Realtime | ~300 ms | kapalı, OpenAI API | ticari |
| Gemini 2.5 Live | ~350 ms | kapalı, Google API | ticari |

## İnşa Et

### Adım 1: Arayüz

Moshi, 80 ms Mimi-encoded ses chunk'ları alan ve 80 ms Mimi-encoded ses chunk'ları döndüren bir WebSocket server expose eder. İki yönlü. Sürekli.

```python
import asyncio
import websockets
from moshi.client_utils import encode_audio_mimi, decode_audio_mimi

async def moshi_chat():
    async with websockets.connect("ws://localhost:8998/api/chat") as ws:
        mic_task = asyncio.create_task(stream_mic_to(ws))
        spk_task = asyncio.create_task(stream_from_to_speaker(ws))
        await asyncio.gather(mic_task, spk_task)
```

### Adım 2: Full-duplex döngü

```python
async def stream_mic_to(ws):
    async for chunk_80ms in mic_stream_at_12_5_hz():
        mimi_tokens = encode_audio_mimi(chunk_80ms)
        await ws.send(serialize(mimi_tokens))

async def stream_from_to_speaker(ws):
    async for msg in ws:
        mimi_tokens, text_token = deserialize(msg)
        audio = decode_audio_mimi(mimi_tokens)
        await play(audio)
```

İki yön eş zamanlı çalışır. Python asyncio ya da Rust futures standart transport.

### Adım 3: Eğitim hedefi (kavramsal)

Her 80 ms frame `t` için:

- Girdi: `user_mimi[0..t]`, `moshi_mimi[0..t-1]`, `moshi_text[0..t-1]`
- Tahmin et: `moshi_text[t]`, sonra `moshi_mimi[t, codebook_0..7]`

Metin sesten önce tahmin edilir (iç monolog); ses depth transformer içinde codebook-sıralı tahmin edilir.

### Adım 4: Moshi nerede kazanır ve kazanmaz

Moshi kazanır:

- Ucuz donanımda alt-250 ms end-to-end.
- Doğal back-channel'lar ve kesintiler.
- Pipeline glue kodu yok.

Moshi kazanmaz:

- Tool calling (bunun için eğitilmemiş; ayrı bir LLM yolu lazım).
- Uzun akıl yürütme (Moshi 8B-ish diyalog modeli, Claude/GPT-4 değil).
- Niş konularda olgusal doğruluk.
- Çoğu üretim enterprise kullanım durumu (2026'da hâlâ pipeline kullanır).

## Kullan

| Durum | Seç |
|-----------|------|
| En düşük gecikmeli ses arkadaşı | Moshi |
| Canlı çeviri araması | Hibiki |
| Ses demo / araştırma | Moshi, CSM |
| Tool'lu enterprise ajanı | Pipeline (Ders 12), Moshi değil |
| Bağlamda custom ses TTS | Sesame CSM |
| Speech-to-speech, herhangi dil | GPT-4o Realtime ya da Gemini 2.5 Live (ticari) |

## Tuzaklar

- **Sınırlı tool calling.** Moshi bir diyalog modeli, agent framework değil. Tool'lar için pipeline ile birleştir.
- **Specific-voice koşullaması.** Moshi tek bir eğitilmiş persona kullanır; klonlama ayrı bir eğitim koşusu.
- **Dil kapsamı.** Fransızca + İngilizce mükemmel; diğerleri sınırlı. Hibiki-Zero yardımcı olur, ama yine de eğitim verisi gerek.
- **Kaynak maliyeti.** Tam bir Moshi session bir GPU slotunu tutar; ucuz shared-tenant deploy kalıbı değil.

## Yayınla

`outputs/skill-duplex-pipeline.md` olarak kaydet. Bir ses-ajan iş yükü için pipeline vs full-duplex mimariyi nedeniyle birlikte seç.

## Alıştırmalar

1. **Kolay.** `code/main.py`'yi çalıştır. İki-stream + iç-monolog mimarisini sembolik simüle eder.
2. **Orta.** HuggingFace'ten Moshi'yi çek, server'ı çalıştır, bir konuşma test et. End-of-user-speech'ten start-of-Moshi-response'a duvar saati gecikmesini ölç.
3. **Zor.** Ders 12 pipeline ajanını al ve 20 eşleşmiş test utterance'ında Moshi'ye karşı P50 gecikmeyi karşılaştır. Yine de pipeline'ın mimari olarak ne zaman kazandığını yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Full-duplex | Aynı anda duy ve konuş | Aynı modelde eş zamanlı aktif iki ses stream'i. |
| İç monolog | Modelin metin stream'i | Moshi ses çıkışı ile birlikte metin token'ları yayar. |
| Depth transformer | Inter-codebook tahmincisi | Bir 80 ms frame içinde 8 codebook tahmin eden küçük transformer. |
| Mimi | Kyutai'nin codec'i | 12.5 Hz × 8 codebook; semantic+acoustic; Moshi'yi çalıştırır. |
| Streaming S2S | Ses → canlı ses | Chunk-by-chunk çeviri/diyalog, pipeline aşaması yok. |
| Back-channeling | "Mhm" tepkiler | Moshi turunu bozmadan küçük onaylar yayabilir. |

## İleri Okuma

- [Défossez et al. (2024). Moshi — speech-text foundation model](https://arxiv.org/html/2410.00037v2) — makale.
- [Kyutai Labs (2026). Hibiki-Zero](https://arxiv.org/abs/2602.12345) — hizalanmış veri olmadan streaming çeviri.
- [Sesame (2025). Crossing the uncanny valley of voice](https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice) — CSM spec.
- [Kyutai — Moshi repo](https://github.com/kyutai-labs/moshi) — install + server.
- [OpenAI — Realtime API](https://platform.openai.com/docs/guides/realtime) — kapalı ticari muadil.
- [Kyutai — Delayed Streams Modeling](https://github.com/kyutai-labs/delayed-streams-modeling) — arka plandaki STT/TTS framework'ü.
