# Prompt Caching ve Context Caching

> Senin system prompt'un 4.000 token. RAG context'in 20.000 token. İkisini de her istekle gönderiyorsun. İkisi için de ödüyorsun — her seferinde. Prompt caching, sağlayıcının o prefix'i kendi tarafında sıcak tutmasına ve tekrar kullanımda sana normal oranın %10'unu faturalandırmasına olanak verir. Doğru kullanılınca, çıkarım maliyetini %50–90, ilk-token gecikmesini ise %40–85 oranında düşürür.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 11 · 01 (Prompt Engineering), Faz 11 · 05 (Context Engineering), Faz 11 · 11 (Caching ve Maliyet)
**Süre:** ~60 dakika

## Sorun

Bir coding agent, bir konuşmanın her turunda Claude'a aynı 15.000-token'lık system prompt'u gönderiyor. $3/M input token üzerinden yirmi tur, kullanıcının gerçek mesajlarından önce sadece input maliyeti olarak $0.90 eder. Bunu günlük 10.000 konuşmayla çarp; hiç değişmeyen metin için fatura günde $9.000'a vurur.

Prompt'u kaliteden ödün vermeden küçültemezsin. Göndermekten kaçınamazsın — model her turda ona ihtiyaç duyar. Tek hamle, sağlayıcının zaten gördüğü bir prefix için tam fiyat ödemeyi bırakmaktır.

O hamle prompt caching. Anthropic Ağustos 2024'te yayınladı (2025'te 1-saatlik genişletilmiş-TTL varyantıyla), OpenAI yıl sonunda otomatikleştirdi, Google Gemini 1.5 ile birlikte açık context caching yayınladı ve şimdi üçü de bunu frontier modellerinde birinci-sınıf özellik olarak sunuyor.

## Kavram

![Prompt caching: bir kere yaz, ucuza oku](../assets/prompt-caching.svg)

**Mekanik.** Bir isteğin prefix'i yakın zamanlı bir istekten eşleşince, sağlayıcı token'ları yeniden encode etmek yerine önceki çalışmanın KV-cache'ini servis eder. İlk seferde küçük bir write primi ödersin, sonrası her seferinde büyük bir read indirimi alırsın.

**2026'da üç sağlayıcı çeşni.**

| Sağlayıcı | API stili | Hit indirimi | Write primi | Varsayılan TTL | Min cache'lenebilir |
|---------|-----------|--------------|---------------|-------------|---------------|
| Anthropic | İçerik bloklarında açık `cache_control` işaretçileri | Input'tan %90 off | %25 ek ücret | 5 dk (1 saate uzatılabilir) | 1.024 token (Sonnet/Opus), 2.048 (Haiku) |
| OpenAI | Otomatik prefix tespiti | Input'tan %50 off | yok | 1 saate kadar (best-effort) | 1.024 token |
| Google (Gemini) | Açık `CachedContent` API'si | Storage-faturalı; normalin ~%25'inde okuma | Token·saat başına storage ücreti | Kullanıcı-belirlenmiş (varsayılan 1 saat) | 4.096 token (Flash), 32.768 (Pro) |

**Değişmez.** Üçü de yalnızca prefix'i cache'ler. İstekler arasında herhangi bir token farklıysa, ilk farklılaşan token'dan sonraki her şey miss. *Kararlı* kısımları en üste, *değişken* kısımları en alta koy.

### Cache-dostu yerleşim

```
[system prompt]          <-- bunu cache'le
[tool tanımları]         <-- bunu cache'le
[few-shot örnekler]      <-- bunu cache'le
[getirilen belgeler]     <-- yeniden kullanılıyorsa cache'le, değilse koyma
[konuşma geçmişi]        <-- son tura kadar cache'le
[mevcut kullanıcı mesajı] <-- asla cache'leme (her seferinde farklı)
```

Sırayı ihlal et — kullanıcı mesajını system prompt'un üstüne koy, few-shot'lar arasına dinamik retrieval'lar serpiştir — cache asla isabet etmez.

### Break-even hesabı

Anthropic'in %25 write primi, cache'lenmiş bir bloğun net para kazandırması için en az iki kez okunması gerektiği anlamına gelir. 1 write + 1 read istek başına ortalama 0.675x maliyet (%32 tasarruf); 1 write + 10 read ortalama 0.205x (%80 tasarruf). Kural: TTL içinde en az 3 kez yeniden kullanmayı beklediğin her şeyi cache'le.

## İnşa Et

### Adım 1: açık işaretçilerle Anthropic prompt caching

```python
import anthropic

client = anthropic.Anthropic()

SYSTEM = [
    {
        "type": "text",
        "text": "You are a senior Python reviewer. Follow the rubric exactly.\n\n" + RUBRIC_15K_TOKENS,
        "cache_control": {"type": "ephemeral"},
    }
]

def review(code: str):
    return client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": code}],
    )
```

`cache_control` işaretçisi Anthropic'e bloğu 5 dakika saklamasını söyler. Bu pencere içinde yeniden kullanım isabet eder; süresi dolduktan sonra yeniden kullanım yeniden yazar.

**Response usage alanları:**

```python
response = review(code_a)
response.usage
# InputTokensUsage(
#     input_tokens=120,
#     cache_creation_input_tokens=15023,   # 1.25x oranında ödendi
#     cache_read_input_tokens=0,
#     output_tokens=340,
# )

response_b = review(code_b)
response_b.usage
# cache_creation_input_tokens=0
# cache_read_input_tokens=15023           # 0.1x oranında ödendi
```

CI'da iki alanı da kontrol et — `cache_read_input_tokens` istekler arasında sıfırda kalıyorsa cache anahtarların kayıyor demektir.

### Adım 2: bir saatlik genişletilmiş TTL

Uzun süre çalışan batch job'lar için 5-dakikalık varsayılan job'lar arasında sona erer. `ttl` ayarla:

```python
{"type": "text", "text": RUBRIC, "cache_control": {"type": "ephemeral", "ttl": "1h"}}
```

1-saatlik TTL write primini 2x'e çıkarır (taban %25 yerine %50) ama prefix'i 5'ten fazla kez yeniden kullanan herhangi bir batch'te hızla geri öder.

### Adım 3: OpenAI otomatik caching

OpenAI sana yapılandıracak hiçbir şey vermiyor. Yakın zamanlı bir istekle eşleşen, 1.024 token üstündeki herhangi bir prefix otomatik olarak %50 indirim alır.

```python
from openai import OpenAI
client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},   # uzun ve kararlı
        {"role": "user", "content": user_msg},
    ],
)
resp.usage.prompt_tokens_details.cached_tokens  # indirim uygulanan kısım
```

Aynı cache-dostu yerleşim kuralı geçerli. Anthropic'inkini öldürmeyen ama OpenAI'ınkini öldüren iki şey: `user` alanını değiştirmek (cache key bileşeni olarak kullanılır) ve tool'ları yeniden sıralamak.

### Adım 4: Gemini açık context caching

Gemini cache'i yarattığın ve isim verdiğin birinci-sınıf bir nesne olarak ele alır:

```python
from google import genai
from google.genai import types

client = genai.Client()

cache = client.caches.create(
    model="gemini-3-pro",
    config=types.CreateCachedContentConfig(
        display_name="rubric-v3",
        system_instruction=RUBRIC,
        contents=[FEW_SHOT_EXAMPLES],
        ttl="3600s",
    ),
)

resp = client.models.generate_content(
    model="gemini-3-pro",
    contents=["Review this code:\n" + code],
    config=types.GenerateContentConfig(cached_content=cache.name),
)
```

Gemini cache yaşadığı sürece token·saat başına storage ücreti alır ve normal input oranının ~%25'inde okur. Aynı dev prompt'u günler boyunca birçok session'da yeniden kullanırken doğru şekil budur.

### Adım 5: üretimde hit rate ölçme

Write/read/miss sayılarını izleyen ve 1K istek başına harmanlanmış maliyeti hesaplayan simüle edilmiş üç-sağlayıcı muhasebeci için `code/main.py`'a bak. Hedef hit rate'inde deploy'u gate'le — çoğu üretim Anthropic kurulumu warmup sonrası %80'den fazla read fraksiyonu görmeli.

## 2026'da hâlâ yayınlanan tuzaklar

- **Üstte dinamik timestamp'ler.** System prompt'un en üstünde `"Current time: 2026-04-22 15:30:02"`. Her istek miss. Timestamp'leri cache breakpoint'in altına taşı.
- **Tool yeniden sıralama.** Tool'ları kararlı bir sırada serileştir — deploy'lar arası bir dict yeniden karıştırma her hit'i bozar.
- **Free-text yakın-duplikatlar.** "You are helpful." vs "You are a helpful assistant." — bir bayt fark = tam miss.
- **Çok küçük bloklar.** Anthropic 1.024-token tabanını zorlar (Haiku için 2.048). Daha küçük bloklar sessizce cache'lenmez.
- **Kör maliyet dashboard'ları.** "Input token"ı cached vs uncached olarak ayır. Aksi halde bir trafik düşüşü cache kazancı gibi görünür.

## Kullan

2026 caching stack'i:

| Durum | Seçim |
|-----------|------|
| Kararlı 10k+ system prompt'a, birçok tura sahip agent | 5-dakikalık TTL ile Anthropic `cache_control` |
| 30+ dakika prefix yeniden kullanan batch job | `ttl: "1h"` ile Anthropic |
| GPT-5 üzerinde serverless endpoint, custom altyapı yok | OpenAI otomatik (sadece prefix'ini kararlı ve uzun tut) |
| Dev bir kod/belge corpus'unun çok-günlü yeniden kullanımı | Gemini açık `CachedContent` |
| Sağlayıcılar arası fallback | Cache'lenebilir prefix yerleşimini sağlayıcılar arasında özdeş tut, herhangi bir hit işe yarasın |

Kullanıcı-mesajı katmanı için semantik caching (Faz 11 · 11) ile birleştir: prompt caching *token-özdeş* yeniden kullanımı işler, semantik caching *anlam-özdeş* yeniden kullanımı.

## Yayınla

`outputs/skill-prompt-caching-planner.md` olarak kaydet:

```markdown
---
name: prompt-caching-planner
description: Design a cache-friendly prompt layout and pick the right provider caching mode.
version: 1.0.0
phase: 11
lesson: 15
tags: [llm-engineering, caching, cost]
---

Given a prompt (system + tools + few-shot + retrieval + history + user) and a usage profile (requests per hour, TTL needed, provider), output:

1. Layout. Reordered sections with a single cache breakpoint marked; explain which sections are stable, which are volatile.
2. Provider mode. Anthropic cache_control, OpenAI automatic, or Gemini CachedContent. Justify from TTL and reuse pattern.
3. Break-even. Expected reads per write within TTL; net cost vs no-cache with math.
4. Verification plan. CI assertion that cache_read_input_tokens > 0 on the second identical request; dashboard split by cached vs uncached tokens.
5. Failure modes. List the three most likely reasons the cache will miss in this setup (dynamic timestamp, tool reorder, near-duplicate text) and how you will prevent each.

Refuse to ship a cache plan that places a dynamic field above the breakpoint. Refuse to enable 1h TTL without a reuse count that makes the 2x write premium pay back.
```

## Alıştırmalar

1. **Kolay.** 5.000-token'lık system prompt'a sahip 10-turlu bir konuşmayı Claude'a karşı al. Önce `cache_control` olmadan, sonra ile çalıştır. Her birinin input-token faturasını raporla.
2. **Orta.** Bir prompt şablonu ve bir istek log'u verildiğinde, sağlayıcı başına beklenen hit rate'i ve dolar tasarrufunu (Anthropic 5dk, Anthropic 1sa, OpenAI otomatik, Gemini açık) hesaplayan bir test harness yaz.
3. **Zor.** Bir yerleşim optimize edici inşa et: bir prompt ve `stable=True/False` olarak işaretlenmiş alan listesi verildiğinde, bilgi kaybetmeden tek bir cache breakpoint'i maksimum cache-dostu pozisyona yerleştirecek şekilde prompt'u yeniden yaz. Gerçek bir Anthropic endpoint'i üzerinde doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Prompt caching | "Uzun prompt'ları ucuz yapar" | Eşleşen prefix'ler için sağlayıcı tarafı KV-cache'i yeniden kullanmak; tekrarlanan input token'larda %50-90 indirim. |
| `cache_control` | "Anthropic işaretçisi" | "Buraya kadar her şey cache'lenebilir" diyen içerik-bloğu özniteliği; `{"type": "ephemeral"}`. |
| Cache write | "Primi ödemek" | Cache'i dolduran ilk istek; Anthropic'te ~1.25x input oranında, OpenAI'da bedava. |
| Cache read | "İndirim" | Prefix'le eşleşen sonraki istekler; %10 (Anthropic), %50 (OpenAI), ~%25 (Gemini) oranında faturalanır. |
| TTL | "Ne kadar yaşar" | Cache'in sıcak kaldığı saniyeler; Anthropic 5dk varsayılan (1sa'e uzatılabilir), OpenAI 1sa'e kadar best-effort, Gemini kullanıcı-belirlenmiş. |
| Genişletilmiş TTL | "1-saatlik Anthropic cache" | `{"type": "ephemeral", "ttl": "1h"}`; 2x write primi ama batch yeniden kullanım için değer. |
| Prefix match | "Cache'im neden miss" | Cache'ler yalnızca başlangıçtan breakpoint'e kadar her token bayt-özdeş olduğunda isabet eder. |
| Context caching (Gemini) | "Açık olan" | Google'ın isim verilmiş, storage-faturalı cache nesnesi; büyük corpus'ların çok-günlü yeniden kullanımı için en iyisi. |

## İleri Okuma

- [Anthropic — Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — `cache_control`, 1sa TTL, break-even tabloları.
- [OpenAI — Prompt caching](https://platform.openai.com/docs/guides/prompt-caching) — otomatik prefix eşleme.
- [Google — Context caching](https://ai.google.dev/gemini-api/docs/caching) — `CachedContent` API'si ve storage fiyatlandırması.
- [Anthropic engineering — Prompt caching for long-context workloads](https://www.anthropic.com/news/prompt-caching) — gecikme sayılarıyla orijinal launch yazısı.
- Faz 11 · 05 (Context Engineering) — cache'in oturabilmesi için prompt'u nereden dilimleyeceğin.
- Faz 11 · 11 (Caching ve Maliyet) — prompt caching'i kullanıcı mesajlarında semantik cache ile eşleştir.
- [Pope et al., "Efficiently Scaling Transformer Inference" (2022)](https://arxiv.org/abs/2211.05102) — prompt caching'in kullanıcılara açtığı KV-cache bellek modeli; cache'lenmiş prefix'in yeniden okunmasının yeniden hesaplanmasından neden ~10× daha ucuz olduğunu açıklar.
- [Agrawal et al., "SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills" (2023)](https://arxiv.org/abs/2308.16369) — prefill, prompt caching'in kısayollayan fazıdır; bu makale cache hit'te TTFT'nin neden dramatik düştüğünü açıklarken TPOT'un etkilenmediğini açıklar.
- [Leviathan et al., "Fast Inference from Transformers via Speculative Decoding" (2023)](https://arxiv.org/abs/2211.17192) — prompt caching, çıkarım maliyet eğrisini büken kollar olarak speculative decoding, Flash Attention ve MQA/GQA ile yan yana oturur; diğer üçü için bunu oku.
