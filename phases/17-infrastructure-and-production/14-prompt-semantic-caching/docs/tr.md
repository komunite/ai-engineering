# Prompt Caching ve Semantic Caching Ekonomisi

> **Fiyatlandırma snapshot'ı: 2026-04.** Aşağıdaki sayısal iddialar bu dersin yayınında yakalanan vendor rate card'larını yansıtır; downstream alıntılamadan önce bağlantılı dokümanlara karşı doğrula.

> Caching iki katmanda olur. L2 (sağlayıcı-seviye) prompt/prefix caching tekrarlanan prefix'ler için attention KV'yi yeniden kullanır — Anthropic'in prompt-caching dokümanları uzun prompt'larda %90'a varan maliyet azaltma ve %85 gecikme azaltma reklamı yapar; Claude 3.5 Sonnet için cache okumalar 5-dakikalık TTL ile $3.00/M taze'ye karşı $0.30/M ve 1-saatlik TTL seçeneği için 2x yazma primi (docs.anthropic.com, 2026-04). OpenAI prompt caching ≥1024 token'lık prompt'lar için otomatik olarak uygulanır ve cache'lenmiş input'u taze'ye karşı kabaca %90 indirimle fiyatlandırır (platform.openai.com, 2026-04); modele-özel cache oranı canlı rate card'a bağlı. L1 (uygulama-seviyesi) semantic caching embedding benzerlik hit'lerinde LLM'i tamamen atlar. Vendor "%95 doğruluk" eşleşme doğruluğunu kasteder, hit oranını değil — raporlanan üretim hit oranları %10'dan (açık-uçlu sohbet) %70'e (yapılandırılmış FAQ) kadar değişir; hiçbir sağlayıcı resmi baseline yayınlamaz, dolayısıyla bunlara garanti değil, topluluk telemetrisi muamelesi yap. Üretim tuzakları: paralelizasyon caching'i öldürür (ilk cache yazımından önce verilen N paralel istek harcamayı birkaç katına şişirebilir) ve prefix içindeki dinamik içerik cache hit'leri tamamen önler. ProjectDiscovery dinamik metni cache'lenebilir prefix'ten çıkararak %7'den %74 hit oranına geçtiğini bildirdi (2025-11).

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak iki-katmanlı cache simülatörü)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 17 · 06 (SGLang RadixAttention)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- L2 prompt/prefix caching'i (sağlayıcıda KV yeniden kullanım) L1 semantic caching'den (benzer prompt'larda LLM bypass) ayır.
- Anthropic'in `cache_control` açık işaretlemesini ve iki TTL seçeneğini (5-dakika vs 1-saat) fiyat çarpanlarıyla açıkla.
- Hit oranı, prompt/yanıt karışımı ve token fiyatları verildiğinde beklenen aylık tasarrufu hesapla.
- Faturayı 5-10x şişiren paralelizasyon anti-pattern'ini ve hit oranını çökerten dinamik-içerik anti-pattern'ini adlandır.

## Sorun

RAG servisine prompt caching ekliyorsun. Fatura düz kalıyor. Hit oranını ölçüyorsun; %7. Prompt'ların statik görünüyor ama değil — system prompt dakikaya formatlanmış mevcut tarihi, bir request ID'yi ve çeşitlilik için randomize edilmiş bir örnek yeniden sıralama içeriyor. Her istek yeni bir cache girişi yazar, sıfır okur.

Ayrı olarak, agent'ın kullanıcı sorusu başına on paralel tool çağrı çalıştırıyor. Onu da ilk cache yazımı tamamlanmadan sağlayıcıya varır. On yazma, sıfır okuma. Faturan "caching ile" maliyetlenmesi gereken şeyin 5-10 katı.

Caching bir flag değil, bir protokol. İki katman, iki farklı başarısızlık modu.

## Kavram

### L2 — sağlayıcı prompt/prefix caching'i

Sağlayıcı cache'lenebilir bir prefix için attention KV'yi saklar ve prefix'le eşleşen sonraki istekte yeniden kullanır. Bir kez yazma maliyeti ödersin, okumalar neredeyse bedava.

**Anthropic (Claude 3.5 / 3.7 / 4 serisi)**: istekte açık `cache_control` işaretleyici. Hangi block'ların cache'lenebilir olduğunu etiketlersin. TTL: 5-dakika (yazma base'in 1.25x'i) ya da 1-saat (yazma base'in 2x'i). Cache okumalar: Claude 3.5 Sonnet'te $0.30/M, taze'ye karşı $3.00/M — 10x daha ucuz (docs.anthropic.com, 2026-04 itibarıyla). Oranlar modele göre değişir (Opus/Haiku ayrı yayınlanır); her zaman canlı fiyatlandırma sayfasıyla çapraz kontrol et.

**OpenAI**: ≥1024 token'lık prompt'lar için otomatik caching (platform.openai.com, 2026-04). Açık flag yok. Cache'lenmiş input mevcut gpt-4o/gpt-5 rate card'larında taze'den kabaca 10x daha ucuz. Ne dokümanlar ne de release notes resmi bir hit-oran baseline'ı yayınlar; topluluk raporları dikkatli prompt tasarımıyla %30-60 civarında kümelenir. Kendininkini ölçmek için `usage.cached_tokens`'ı izle.

**Google (Gemini)**: açık API üzerinden context caching; 1M-token'lık context caching'in daha da çok ödediği anlamına gelir.

**Self-hosted (vLLM, SGLang)**: Faz 17 · 06 RadixAttention'ı kapsar — kendi compute'unda aynı desen.

### L1 — uygulama-seviyesi semantic caching

LLM'i hiç çağırmadan önce, prompt'u hash'le, embed et ve benzer bir cache'lenmiş istek ara (cosine similarity eşiği üzerinde, tipik olarak 0.95+). Hit'te cache'lenmiş yanıtı döndür. Miss'te LLM'i çağır ve sonucu cache'le.

Open-source: Redis Vector Similarity, GPTCache, Qdrant. Ticari: Portkey Cache, Helicone Cache.

Vendor doğruluk iddiaları döndürülen cache'lenmiş yanıtın ne sıklıkta semantik olarak uygun olduğunu kasteder — ne sıklıkta hit aldığını değil. Üretim hit oranları:

- Açık-uçlu sohbet: %10-15.
- Yapılandırılmış FAQ / destek: %40-70.
- Kod soruları: %20-30 (küçük varyantlar hit'leri öldürür).
- Prompt'ları tekrar eden voice agent'lar: %50-80 (voice normalizasyonu sabit küme).

### Paralelizasyon anti-pattern'i

Agent'ın paralel 10 tool çağrısı yapıyor. 10'unun da aynı 4K-token'lık system prompt'u var. Anthropic cache yazımları istek başına; ilk cache-yazımı sağlayıcı prompt'u gördükten ~300 ms sonra tamamlanır. İstekler 2-10 aynı milisaniye penceresinde varır ve her biri cache miss görür. 10 yazma primi ödersin, 0 okuma indirimi.

Çözüm: önce-sıralı batch — önce istek 1'i tek başına yap, sonra 1'in cache'i dolduğunda 2-10'u ateşle. İlk tool çağrısına 300 ms ekler; faturanın 5-10x'ini tasarruf eder.

### Dinamik içerik anti-pattern'i

System prompt'un şöyle görünüyor:

```
You are a helpful assistant. The current time is 14:32:17.
User ID: abc123. Today is Tuesday...
```

Her istek benzersiz. Her istek yazar. Sıfır hit.

Çözüm: gerçekten statik olan her şeyi cache'lenebilir prefix'e taşı; dinamik içeriği cache sınırından sonra ekle:

```
[cache'lenebilir]
You are a helpful assistant. [kurallar, örnekler, talimatlar]
[/cache'lenebilir]
[dinamik, cache'lenmez]
Current time: 14:32:17. User: abc123.
```

ProjectDiscovery bu şekilde %7'den %74 cache hit oranına geçti ve anatomiyi yayınladı.

### Gece iş yükleri için batch + cache yığını

Batch API'ları (Faz 17 · 15) 24-saat turnaround'ta %50 indirim verir. Üstüne cache'lenmiş input ekleyince üstüne ~10x alırsın. Gecelik sınıflandırma, etiketleme ve rapor üretim iş yükleri yığarak senkron-cache'siz maliyetin ~%10'una düşebilir.

### Hatırlaman gereken sayılar

Fiyatlandırma noktaları bağlantılı vendor dokümanlarından 2026-04'te yakalanmış ve birkaç ayda bir kayar — onlara güvenmeden önce yeniden kontrol et.

- Anthropic cache okuma: Claude 3.5 Sonnet'te $0.30/M, taze input'tan kabaca 10x daha ucuz (docs.anthropic.com).
- Anthropic cache yazma primi: 1.25x (5-dakikalık TTL) ya da 2x (1-saatlik TTL).
- OpenAI auto-cache: ≥1024 token'lık prompt'lara uygulanır; cache'lenmiş input mevcut rate card'larda taze input'un kabaca %10'unda fiyatlandırılır (platform.openai.com).
- Semantic cache hit oranı (topluluk-raporlu): açık sohbet ~%10; yapılandırılmış FAQ ~%70'e kadar. Vendor-belgelenmiş baseline değil.
- ProjectDiscovery: dinamiği prefix'ten çıkararak %7 → %74 hit oranı (proje blog, 2025-11).
- Paralelizasyon anti-pattern: N paralel isteğin ilk cache yazımını kaçırdığında 5-10x fatura şişmesi tipik raporları.

## Kullan

`code/main.py` karma iş yüklerinde L1 + L2 caching simüle eder. Hit oranlarını, faturayı raporlar ve paralelizasyon cezasını gösterir.

## Yayınla

Bu ders `outputs/skill-cache-auditor.md` üretir. Prompt template ve trafik verildiğinde, cache'lenebilirliği denetler ve yeniden yapılandırma önerir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Paralelizasyon flag'ini değiştir. Fatura ne kadar değişir?
2. System prompt'unda bir tarih var. Onu dışarı taşı. Önce/sonra hit-oran matematiğini göster.
3. İstek varış oranın verildiğinde 1-saatlik TTL (2x yazma) ile 5-dakikalık TTL (1.25x yazma) için break-even'ı hesapla.
4. 0.95 eşiğinde semantic cache %20 hit eder. 0.85'te %50 hit eder ama yanlış cache'lenmiş yanıtlar görürsün. Doğru eşiği seç ve gerekçelendir.
5. Kullanıcı sorusu başına 10 paralel alt-sorgu batch'liyorsun. End-to-end gecikme eklemeden cache-dostu olacak şekilde yeniden yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| L2 prompt cache | "prefix cache" | Sağlayıcı tekrarlanan prefix için KV saklar |
| `cache_control` | "Anthropic cache işaretleyici" | Cache'lenebilir block'ları işaretleyen açık attribute |
| Cache yazma primi | "yazma vergisi" | İlk miss-to-cache için ekstra maliyet (1.25x ya da 2x) |
| L1 semantic cache | "embedding cache" | LLM'i çağırmadan önce uygulama-seviyesi hash-ve-embed |
| GPTCache | "LLM caching kütüphanesi" | Popüler OSS L1 cache kütüphanesi |
| Cache hit oranı | "hit / toplam" | Cache'ten servis edilen isteklerin fraksiyonu |
| Paralelizasyon anti-pattern'i | "N-yazma tuzağı" | N paralel istek cache'i N kez kaçırır |
| Dinamik içerik tuzağı | "prompt'taki zaman tuzağı" | Prefix'teki dinamik byte'lar hit oranını öldürür |
| RadixAttention | "intra-replica cache" | SGLang'in prefix-cache uygulaması |

## İleri Okuma

- [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — resmi `cache_control` semantiği ve TTL'ler.
- [OpenAI Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching) — otomatik caching davranışı ve uygunluk.
- [TianPan — Semantic Caching for LLMs Production](https://tianpan.co/blog/2026-04-10-semantic-caching-llm-production)
- [ProjectDiscovery — Cut LLM Costs 59% With Prompt Caching](https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching)
- [DigitalOcean / Anthropic — Prompt Caching](https://www.digitalocean.com/blog/prompt-caching-with-digital-ocean)
