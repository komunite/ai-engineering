# AI Gateway'ler — LiteLLM, Portkey, Kong AI Gateway, Bifrost

> Bir gateway uygulamalarının ve model sağlayıcıların arasında oturur. Çekirdek özellikler sağlayıcı routing, fallback, retry'lar, rate limiting, secret referansları, observability, guardrail'ler. 2026 pazar bölünmesi: **LiteLLM** 100+ sağlayıcılı, OpenAI-uyumlu MIT OSS, ama yayınlanmış benchmark'larda ~2000 RPS civarında çöküyor (8 GB bellek, kademeli başarısızlıklar); Python, <500 RPS, dev/prototipleme için en iyi. **Portkey** control-plane-konumlanmış (guardrail'ler, PII redaction, jailbreak detection, audit trail'ler), Mart 2026'da Apache 2.0 open-source oldu, 20-40 ms gecikme overhead'i, aylık $49 üretim tier'ı. **Kong AI Gateway** Kong Gateway üzerine kurulu — Kong'un aynı 12 CPU'da kendi benchmark'ı: Portkey'den %228 daha hızlı, LiteLLM'den %859 daha hızlı; model/ay başına $100 fiyatlandırma (Plus tier'da maks 5); zaten Kong'daysan enterprise-uygun. **Bifrost** (Maxim AI) — konfigüre edilebilir backoff'lu otomatik retry'lar, OpenAI 429'da Anthropic'e fallback. **Cloudflare / Vercel AI Gateway'leri** — yönetilen, sıfır-ops, temel retry. Veri ikametgâhı self-host kararını sürükler; Portkey ve Kong ortada oturuyor OSS + opsiyonel yönetilen ile.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak gateway-routing simülatörü)
**Ön koşullar:** Faz 17 · 01 (Yönetilen LLM Platformları), Faz 17 · 16 (Model Routing)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Altı çekirdek gateway özelliğini (routing, fallback, retry'lar, rate limit'ler, secret'lar, observability, guardrail'ler) say.
- Dört 2026 gateway'i (LiteLLM, Portkey, Kong AI, Bifrost) ölçek tavanları ve kullanım senaryolarına eşle.
- Kong benchmark'ını (Portkey'e karşı %228, LiteLLM'e karşı %859) alıntıla ve >500 RPS için neden önemli olduğunu açıkla.
- Veri ikametgâhı ve ops bütçesi verildiğinde self-hosted vs managed seç.

## Sorun

Ürünün OpenAI, Anthropic ve self-hosted Llama'yı çağırıyor. Her sağlayıcının farklı bir SDK'i, hata modeli, rate limit'i ve auth şeması var. Failover (OpenAI 429 verirse, Anthropic'i dene), tek bir kimlik bilgisi store'u, birleşik observability ve tenant başına rate limit istiyorsun.

Bunu uygulama katmanında yeniden icat etmek her servisi her sağlayıcıya bağlar. Bir gateway katmanı bunu sağlayıcılara fan-out yapan tek bir API'lı (tipik olarak OpenAI-uyumlu) tek bir process'te konsolide eder.

## Kavram

### Altı çekirdek özellik

1. **Sağlayıcı routing** — OpenAI, Anthropic, Gemini, self-hosted, vs. tek API arkasında.
2. **Fallback** — 429, 5xx ya da kalite başarısızlığında, başka yerde yeniden dene.
3. **Retry'lar** — exponential backoff, sınırlı deneme.
4. **Rate limit'ler** — tenant başına, key başına, model başına.
5. **Secret referansları** — kimlik bilgilerini çalıştırma zamanında vault'tan çek (asla uygulamada değil).
6. **Observability** — OTel + GenAI attribute'ları (Faz 17 · 13) + maliyet atıfı.
7. **Guardrail'ler** — PII redaction, jailbreak detection, izin verilen-konu filtreleri.

### LiteLLM — MIT OSS, Python

- 100+ sağlayıcı, OpenAI-uyumlu, router config'i, fallback, temel observability.
- Kong'un benchmark'ında 2000 RPS civarında çöker; 8 GB bellek ayak izi, sürdürülen yük altında kademeli başarısızlıklar.
- En iyi uyum: Python uygulaması, <500 RPS, dev/staging gateway'leri, deneysel routing.
- Maliyet: OSS için $0; cloud ücretsiz tier'ı var.

### Portkey — control plane konumlanması

- Mart 2026 itibarıyla Apache 2.0 OSS. Guardrail'ler, PII redaction, jailbreak detection, audit trail'ler.
- İstek başına 20-40 ms gecikme overhead'i.
- Retention + SLA'lı üretim tier'ı için aylık $49.
- En iyi uyum: guardrail'ler + observability'yi paket istediği regüle endüstriler.

### Kong AI Gateway — ölçek oyunu

- Kong Gateway üzerine kurulu (olgun API gateway ürünü, lua+OpenResty).
- Kong'un 12-CPU eşdeğerinde kendi benchmark'ı: Portkey'den %228 daha hızlı, LiteLLM'den %859 daha hızlı.
- Fiyatlandırma: model/ay başına $100, Plus tier'da maks 5.
- En iyi uyum: zaten Kong'da; >1000 RPS; lisanslamaya razı.

### Bifrost (Maxim AI)

- Konfigüre edilebilir backoff'lu otomatik retry'lar.
- OpenAI 429'da Anthropic'e fallback kanonik tarif.
- Yeni giren; ticari.

### Cloudflare AI Gateway / Vercel AI Gateway

- Yönetilen, sıfır-ops. Temel retry ve observability.
- En iyi uyum: Cloudflare/Vercel'de edge-servis eden JavaScript uygulamaları.
- Guardrail'ler ve rate limit'lerde Kong/Portkey'e karşı sınırlı.

### Self-hosted vs managed

Veri ikametgâhı zorlayıcı fonksiyon. Sağlık ve finans varsayılan olarak self-host (LiteLLM ya da Portkey OSS ya da Kong). Tüketici ürünleri varsayılan olarak managed (Cloudflare AI Gateway) ya da orta-tier (Portkey managed). Hibrit: regüle tenant için self-hosted, diğerleri için managed.

### Gecikme bütçesi

- LiteLLM: tipik olarak 5-15 ms overhead.
- Portkey: 20-40 ms overhead.
- Kong: 3-8 ms overhead.
- Cloudflare/Vercel: 1-3 ms overhead (edge avantajı).

Gateway gecikmesi doğrudan TTFT'ye eklenir. TTFT P99 < 100 ms SLA için, Kong ya da Cloudflare. P99 < 500 ms için, herhangi biri.

### Rate-limit semantiği önemli

Basit token-bucket orta ölçeğe kadar çalışır. Multi-tenant sliding-window + burst toleransı + tenant başına tier'lama gerektirir. LiteLLM token-bucket yayınlar; Kong sliding-window yayınlar; Portkey tier'lı yayınlar.

### Gateway + observability + routing bestelenir

Faz 17 · 13 (observability) + 16 (model routing) + 19 (gateway'ler) üretimde aynı katman. Üçünü kapsayan bir araç seç ya da onları dikkatlice tel'le: 2026 deployment'larının çoğu bölünmüş roller için Helicone (observability) ya da Portkey (guardrail'ler) ile Kong'u (ölçek) birleştirir.

### Hatırlaman gereken sayılar

- LiteLLM: ~2000 RPS'te kırılır, 8 GB bellek.
- Portkey: 20-40 ms overhead; Mart 2026'dan beri Apache 2.0.
- Kong: Portkey'den %228 daha hızlı, LiteLLM'den %859 daha hızlı.
- Kong fiyatlandırması: model/ay başına $100, Plus tier'da maks 5.
- Cloudflare/Vercel: edge'de 1-3 ms overhead.

## Kullan

`code/main.py` 429/5xx enjeksiyonu altında 3 sağlayıcı arasında fallback'li gateway routing simüle eder. Gecikme, retry oranı ve fallback hit oranı raporlar.

## Yayınla

Bu ders `outputs/skill-gateway-picker.md` üretir. Ölçek, ops duruşu, compliance, gecikme bütçesi verildiğinde, bir gateway seçer.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. OpenAI→Anthropic→self-hosted'a fallback'i configure et. %5 sağlayıcı hata oranında beklenen hit oranı ne?
2. SLA'in 300 ms baseline'da TTFT P99 < 200 ms. Hangi gateway'ler bütçede kalır?
3. Bir sağlık müşterisi self-hosted + PII redaction + audit gerektiriyor. Portkey OSS ya da Kong seç.
4. LiteLLM vs Kong'u karşılaştır: takım hangi RPS tavanında göç etmeli?
5. Multi-tenant bir SaaS için bir rate-limit politikası tasarla: ücretsiz tier, deneme tier, ücretli tier. Token-bucket ya da sliding-window?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Gateway | "API broker'ı" | Uygulamalar ve sağlayıcılar arasında oturan process |
| LiteLLM | "MIT olan" | Python OSS, 100+ sağlayıcı, 2K RPS'te kırılır |
| Portkey | "guardrail'ler gateway'i" | Control plane + observability, Apache 2.0 |
| Kong AI Gateway | "ölçek olanı" | Kong Gateway üzerine kurulu, benchmark lideri |
| Bifrost | "Maxim'in gateway'i" | Retry'lar + Anthropic fallback tarifi |
| Cloudflare AI Gateway | "edge managed" | Edge-deploy edilmiş managed gateway, sıfır-ops |
| PII redaction | "veri silme" | Modele göndermeden önce regex + NER mask |
| Jailbreak detection | "prompt injection koruması" | Kullanıcı input'unda sınıflandırıcı |
| Audit trail | "regüle log" | Her LLM çağrısının değişmez kaydı |
| Token-bucket | "basit rate limit" | Refill-tabanlı rate limiter |
| Sliding-window | "kesin rate limit" | Zaman-pencereli rate limiter; daha iyi adalet |

## İleri Okuma

- [Kong AI Gateway Benchmark](https://konghq.com/blog/engineering/ai-gateway-benchmark-kong-ai-gateway-portkey-litellm)
- [TrueFoundry — AI Gateways 2026 Comparison](https://www.truefoundry.com/blog/a-definitive-guide-to-ai-gateways-in-2026-competitive-landscape-comparison)
- [Techsy — Top LLM Gateway Tools 2026](https://techsy.io/en/blog/best-llm-gateway-tools)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Portkey GitHub](https://github.com/Portkey-AI/gateway)
- [Kong AI Gateway docs](https://docs.konghq.com/gateway/latest/ai-gateway/)
