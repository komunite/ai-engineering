# LLM Routing Katmanı — LiteLLM, OpenRouter, Portkey

> Provider lock-in pahalıdır. Farklı tool-calling workload'ları farklı modellere uyar. Routing gateway'leri tek bir API yüzeyi, retry'lar, failover, cost tracking ve guardrail'ler verir. 2026'da üç archetype baskındır: LiteLLM (open-source self-hosted), OpenRouter (managed SaaS), Portkey (production-grade, Mart 2026'da open-sourced edildi). Bu ders karar kriterlerini adlandırır ve bir stdlib routing gateway gezer.

**Tür:** Öğrenim
**Diller:** Python (stdlib, routing + failover + cost tracker)
**Ön koşullar:** Faz 13 · 02 (function calling), Faz 13 · 17 (gateway'ler)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Self-hosted, managed ve production-grade routing seçeneklerini ayırt et.
- Tanımlanmış bir öncelik sırasında sağlayıcı başarısızlıklarında retry yapan bir fallback chain implemente et.
- Sağlayıcılar boyunca request başına maliyet ve token kullanımı izle.
- Belirli bir üretim kısıtlaması için LiteLLM, OpenRouter ve Portkey arasında karar ver.

## Sorun

Sağlayıcı routing'inin önemli olduğu senaryolar:

1. **Maliyet.** Claude Sonnet, Haiku'nun maliyetinin 3 katı. Triage task için Haiku yeterli; synthesis task için Sonnet değer. Request başına yönlendir.

2. **Failover.** OpenAI'ın kötü bir saati var. Her request başarısız. Yeniden deploy etmeden otomatik Anthropic fallback istiyorsun.

3. **Gecikme.** Canlı bir chat UI'ı hızlı time-to-first-token'a ihtiyaç duyar. Bir batch summarizer duymaz. Gecikme SLA'sına göre yönlendir.

4. **Compliance.** EU kullanıcıları EU region'larında kalmalı. Bölgeye göre yönlendir.

5. **Deneyleme.** Aynı workload üzerinde iki modelde A/B yap. Test bucket'ına göre yönlendir.

Entegrasyon başına bunların hepsini el-kodlamak tekrarlayıcıdır. Bir routing gateway tek bir OpenAI-uyumlu API verir ve geri kalanını ele alır.

## Kavram

### OpenAI-uyumlu proxy şekli

Herkes OpenAI-şeklini konuşur. Routing gateway `/v1/chat/completions` açar, OpenAI şemasını kabul eder ve dahili olarak Anthropic / Gemini / Cohere / Ollama / her şeye proxy yapar. Client umursamaz.

### Model alias'ları

`claude-3-5-sonnet-20251022` yerine, kodun `our_smart_model` der. Gateway alias'ları gerçek modellere map'ler. Anthropic Claude 4 yayınladığında, alias'ı sunucu tarafında değiştirirsin; kodun hiçbir şeye dokunmaz.

### Fallback chain'ler

```
primary: openai/gpt-4o
on 5xx: anthropic/claude-3-5-sonnet
on 5xx: google/gemini-1.5-pro
on 5xx: refuse
```

Gateway'ler bunu bir config'de tanımlar. Retry'lar bir bütçeye sayılır, böylece fallback cascade'leri maliyeti patlatmaz.

### Semantic caching

Aynı-ya da-neredeyse-aynı prompt'lar sağlayıcı yerine bir cache'e vurur. Tekrarlayan agent döngülerinde tasarruflar %30 ila %60 olabilir. Anahtarlar embedding-tabanlıdır; neredeyse-aynı prompt'lar bir cache slot'unu paylaşır.

### Guardrail'ler

Gateway-seviyesi:

- **PII redaction.** Prompt'ları göndermeden önce regex ya da ML-tabanlı pass.
- **Policy violations.** Yasaklı içerikli prompt'ları reddet.
- **Output filter'ları.** Completion'ları sızıntı için temizle.

Portkey ve Kong ikisi de görüşlü guardrail'ler yayınlar. LiteLLM onları opsiyonel bırakır.

### Key başına rate limit'ler

Bir API key = bir takım. Key başına bütçeler bir takımın paylaşılan kotayı tüketmesini önler. Gateway'lerin çoğu bunu destekler.

### Self-hosted vs managed trade-off'lar

| Faktör | LiteLLM (self-hosted) | OpenRouter (managed) | Portkey (production) |
|--------|----------------------|----------------------|----------------------|
| Kod | Open source, Python | Managed SaaS | Open source (Mar 2026) + managed |
| Kurulum | Bir proxy deploy et | Sign up | İkisi de |
| Sağlayıcılar | 100+ | 300+ | 100+ |
| Faturalama | Kendi key'lerin | OpenRouter credit'leri | Kendi key'lerin |
| Observability | OpenTelemetry | Dashboard | Tam OTel + PII redaction |
| En iyi | Tam kontrol isteyen takımlar | Hızlı prototyping | Compliance'lı production |

LiteLLM SRE takımın olduğunda ve veri sovereignty istediğinde kazanır. OpenRouter tek bir subscription ve hiç altyapı istediğinde kazanır. Portkey out-of-the-box guardrail'ler ve compliance gerektiğinde kazanır.

### Cost tracking

Her request `provider`, `model`, `input_tokens`, `output_tokens` taşır. Token başına model başına fiyatlarla çarp (gateway'in sürdüğü bir pricing sheet'ten çekilir). Kullanıcı / takım / proje başına agrega.

### MCP artı routing

Bir gateway hem LLM çağrılarını HEM DE MCP sampling request'lerini yönlendirebilir. Bir sampling request'inin modelPreferences'ı belirli bir modeli tercih ettiğinde, gateway doğru backend'e çevirir. Faz 13 · 17 (MCP gateway) ve bu dersin routing gateway'i bazen tek bir servise birleştiği yer burasıdır.

### Routing stratejileri

- **Statik öncelik.** Listede ilk; hatada fallback.
- **Load balancing.** Round-robin ya da weighted.
- **Cost-aware.** Gecikme / kalite ile karşılayan en ucuz modeli seç.
- **Latency-aware.** Son N dakikadaki en hızlı modeli seç.
- **Task-aware.** Prompt classifier coding'i bir modele, summarization'ı başka birine yönlendirir.

## Kullan

`code/main.py` ~150 satırda bir routing gateway implemente eder: OpenAI-şekilli request'leri kabul eder, sağlayıcı başına stub'lara çevirir, bir öncelik fallback chain'i çalıştırır, request başına maliyet izler ve input'lara bir PII redaction pass uygular. Üç senaryo ile çalıştır: normal request, fallback tetikleyen primary-provider outage, redaction tarafından yakalanan PII leakage.

Bakılacak şeyler:

- `ROUTES` dict: alias -> öncelik-sıralı somut sağlayıcı listesi.
- Fallback loop 5xx'te retry yapar.
- Cost tracker token kullanımını model başına oranlarla çarpar.
- PII redactor forward etmeden önce SSN-şekilli pattern'leri temizler.

## Yayınla

Bu ders `outputs/skill-routing-config-designer.md` üretir. Bir workload profili (gecikme, maliyet, compliance) verildiğinde, skill LiteLLM / OpenRouter / Portkey seçer ve bir routing config üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Outage senaryosunu tetikle; fallback'in ikinci sağlayıcıya indiğini ve maliyetin doğru atfedildiğini doğrula.

2. Semantic caching ekle: prompt'un SHA256'sı bir lookup key; cache hit'ler anında döner. Tekrarlanan bir çağrıda maliyet tasarruflarını ölç.

3. "code ..." prompt'larını intelligence'ı destekleyen bir alias'a ve "summarize ..." prompt'larını speed'i destekleyen bir alias'a yönlendiren bir prompt classifier ekle.

4. Takım başına bütçeler tasarla: her takım aylık bir spend cap'i alır; cap'e ulaşıldığında gateway request'leri reddeder. Bir enforcement granülarite seç (request başına ya da pencereli).

5. LiteLLM, OpenRouter ve Portkey doc'larını yan yana oku. Her birinin yayınladığı diğer ikisinin yapmadığı tek feature'ı adlandır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Routing gateway | "LLM proxy" | Birçok sağlayıcının önünde tek-API-yüzey katmanı |
| OpenAI-uyumlu | "OpenAI şemasını konuşur" | `/v1/chat/completions` şeklini kabul eder, herhangi bir backend'e çevirir |
| Model alias'ı | "our_smart_model" | Gateway'in somut bir modele map'lediği kodundaki isim |
| Fallback chain | "Retry listesi" | Başarısızlıkta denenen sağlayıcıların sıralı listesi |
| Semantic caching | "Prompt-embedding cache" | Anahtar prompt'un embedding'i; neredeyse-duplicate'ler bir cache hit paylaşır |
| Guardrail'ler | "Input/output filter'ları" | PII redact et, policy ihlallerini reddet |
| Key başına rate limit | "Takım bütçesi" | Bir API key'ine scope'lu kota |
| Cost tracking | "Request başına spend" | Agrega token kullanımı x model başına fiyat |
| LiteLLM | "Açık proxy" | Self-hostable OSS routing gateway |
| OpenRouter | "Managed SaaS" | Credit-tabanlı faturalama ile hostlu gateway |
| Portkey | "Production seçeneği" | Open-source + managed, guardrail'ler dahili |

## İleri Okuma

- [LiteLLM — docs](https://docs.litellm.ai/) — self-hosted routing gateway
- [OpenRouter — quickstart](https://openrouter.ai/docs/quickstart) — managed routing SaaS
- [Portkey — docs](https://portkey.ai/docs) — guardrail'lerle production routing
- [TrueFoundry — LiteLLM vs OpenRouter](https://www.truefoundry.com/blog/litellm-vs-openrouter) — karar rehberi
- [Relayplane — LLM gateway comparison 2026](https://relayplane.com/blog/llm-gateway-comparison-2026) — vendor anketi
