# LLM Observability Stack Seçimi

> 2026 observability pazarı iki kategoriye ayrılıyor. Geliştirme platformları (LangSmith, Langfuse, Comet Opik) izlemeyi eval'ler, prompt yönetimi, session replay'lerle paketler. Gateway/enstrümantasyon araçları (Helicone, SigNoz, OpenLLMetry, Phoenix) telemetriye odaklanır. Langfuse güçlü OSS dengeli MIT-lisanslı çekirdeğe sahip (50K event/ay ücretsiz cloud). Phoenix Elastic License 2.0 altında OpenTelemetry-native — drift/RAG görselleştirme için mükemmel, kalıcı bir üretim backend'i değil. Arize AX zero-copy Iceberg/Parquet entegrasyonu kullanıyor ve monolitik observability'den 100x daha ucuz olduğunu iddia ediyor. LangSmith LangChain/LangGraph için liderdir, kullanıcı başına aylık $39, yalnız Enterprise'da self-host. Helicone proxy-tabanlı, 15-30 dakikada kurulur, aylık 100K istek ücretsiz, ama agent trace'lerinde daha az derinlik. Yaygın üretim deseni: OpenTelemetry ile yapıştırılmış Gateway (Helicone/Portkey) + eval platform (Phoenix/TruLens).

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak trace-örnekleme simülatörü)
**Ön koşullar:** Faz 17 · 08 (Çıkarım Metrikleri), Faz 14 (Agent Engineering)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Geliştirme platformlarını (paket: eval'ler + prompt'lar + oturumlar) gateway/telemetri araçlarından (yalnız trace'ler + metrikler) ayır.
- Altı büyük aracı (Langfuse, LangSmith, Phoenix, Arize AX, Helicone, Opik) lisanslama, fiyatlandırma ve sweet-spot kullanım senaryolarına eşle.
- Bir gateway aracını ayrı bir eval platformuyla birleştirmene izin veren OpenTelemetry-glue desenini açıkla.
- 2026 maliyet farklılaştırıcısını (Arize AX'in zero-copy yaklaşımı vs monolitik ingest) adlandır ve kabaca 100x çarpanı ifade et.

## Sorun

Bir LLM özelliği yayınladın. Çalışıyor. Prompt başarısızlıkları, tool loop'ları, gecikme regresyon'ları, maliyet sıçramaları ya da prompt-cache hit oranı üzerine görünürlüğün yok. "LLM observability" diye Google'larsın ve hepsi aynı sorunu üç farklı fiyat noktasında çözdüğünü iddia eden sekiz araç alırsın.

Aynı sorunu çözmüyorlar. LangSmith "bu LangGraph çalıştırması neden başarısız oldu?" sorusunu yanıtlıyor. Phoenix "RAG pipeline'ım drift oluyor mu?" sorusunu yanıtlıyor. Helicone "hangi uygulama token yakıyor?" sorusunu yanıtlıyor. Langfuse "hepsini self-host edebilir miyim?" sorusunu yanıtlıyor. Farklı araçlar, farklı kitleler.

Seçim dört eksen içerir: stack (LangChain? ham SDK? multi-vendor?), lisans toleransı (yalnız MIT? Elastic OK? ticari iyi?), bütçe (ücretsiz tier? $100/ay? $1000/ay?) ve self-host (zorunlu? olsa iyi olur? asla?).

## Kavram

### İki kategori

**Geliştirme platformları** observability'yi eval'ler, prompt yönetimi, dataset versiyonlama, session replay ile paketler. Deney çalıştırırsın, hangi prompt'un işe yaradığını görürsün, eski kazananlara karşı yeni bir prompt'u dataset-regresyon ederek karşılaştırırsın. LangSmith, Langfuse, Comet Opik.

**Gateway/telemetri araçları** çıkarım çağrılarını enstrümante eder — prompt, yanıt, token'lar, gecikme, model, maliyet. Helicone, SigNoz, OpenLLMetry, Phoenix. Minimalist. OpenTelemetry üzerinden ayrı bir eval aracıyla birleştirilebilir.

### Langfuse — OSS dengesi

- Çekirdek Apache / MIT lisanslı; Docker üzerinden self-host.
- Cloud ücretsiz tier: aylık 50K event. Ücretli: takım için aylık $29.
- Eval'ler, prompt yönetimi, trace'ler, dataset'ler. Dört dev-platform özelliğinin hepsinde makul kapsama.
- Sweet spot: LangSmith-sınıfı özellikler istiyorsun ama self-host etmeli ya da OSS lisansta kalmalısın.

### Phoenix (Arize) — telemetri-öncelikli, OpenTelemetry-native

- Elastic License 2.0; self-host önemsiz.
- RAG ve drift görselleştirmesinde mükemmel. Embedding-alan scatter plot'lar first-class olarak gelir.
- Kalıcı üretim backend'i olarak tasarlanmadı — birincil olarak geliştirme-zamanı observability.
- Sweet spot: RAG pipeline geliştirme, drift debug, üretim için ayrı bir gateway ile eşleşir.

### Arize AX — ölçek oyunu

- Ticari. Iceberg/Parquet üzerinden zero-copy data lake entegrasyonu.
- Ölçekte monolitik observability'den (Datadog-sınıfı) ~100x daha ucuz olduğunu iddia eder. Matematik: trace'leri kendi S3'üne Parquet olarak saklarsın; Arize doğrudan okur.
- Sweet spot: günde >10M trace, mevcut data lake, Datadog fiyatlandırması olmadan LLM-spesifik dashboard'lar.

### LangSmith — LangChain/LangGraph öncelikli

- Ticari, kullanıcı başına aylık $39. Yalnız Enterprise'da self-host.
- LangChain ve LangGraph stack'leri için sınıfın en iyisi. İkisinde de değilsen, daha az çekici.
- Sweet spot: LangChain'e bağlı takım, ödemeye razı.

### Helicone — proxy-tabanlı minimum yaşayabilir

- `OPENAI_API_BASE`'ini Helicone proxy ile değiştirerek 15-30 dakika kurulum.
- MIT lisanslı; aylık 100K istek ücretsiz, ücretli aylık $20+.
- Failover, caching, rate limit'ler içerir — gateway gibi de davranır.
- Agent / multi-step trace'lerde daha az derinlik.
- Sweet spot: hızlı başlangıç, tek-stack uygulama, gateway + observability'yi birde isteyen.

### Opik (Comet) — OSS dev platformu

- Apache 2.0, tamamen OSS.
- Comet mirasıyla Langfuse'a benzer özellik seti.
- Sweet spot: zaten Comet'te olan ML takımları, aynı panelde LLM observability isteyen.

### SigNoz — OpenTelemetry-öncelikli tam APM

- Apache 2.0. Genel APM artı LLM'i OpenTelemetry üzerinden halleder.
- Sweet spot: servisler ve LLM çağrıları arasında birleşik observability.

### Yapıştırıcı: OpenTelemetry + GenAI semantic conventions

OpenTelemetry 2025 sonunda GenAI semantic convention'larını yayınladı (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`). OTel'i tüketen araçlar birlikte çalışabilir. Beliren üretim deseni:

1. Her LLM çağrısından GenAI convention'larıyla OTel yayınla.
2. Günlük için gateway'e (Helicone / Portkey) yönlendir.
3. Regresyon'lar için eval platforma (Phoenix / Langfuse) çift yayınla.
4. Arize AX ya da DuckDB üzerinden uzun-vadeli analiz için data lake'e (Iceberg) arşivle.

### Tuzak: yanlış katmanda enstrümante etmek

Agent framework'ünün içinde enstrümante etmek (örn. LangSmith trace'leri eklemek) seni o framework'e bağlar. HTTP/OpenAI-SDK katmanında enstrümante etmek (OpenLLMetry ya da gateway'in üzerinden) taşınabilir.

### Sampling — her şeyi tutamazsın

Günde >1M istekte, tam-trace tutma LLM çağrılarından daha çok maliyetler. Kurallarla örnekle: %100 hatalar, %100 yüksek-maliyetli, %5 başarı. Toplamları her zaman tut; uzun kuyruk için ham tut.

### Hatırlaman gereken sayılar

- Langfuse ücretsiz cloud: aylık 50K event.
- LangSmith: kullanıcı başına aylık $39.
- Helicone ücretsiz: aylık 100K istek.
- Arize AX iddiası: ölçekte monolitikten ~100x daha ucuz.
- OpenTelemetry GenAI convention'ları: 2025 yayını, 2026 geniş benimseme.

## Kullan

`code/main.py` retention stratejileri (%100 ingest, sampling, sampling + hatalar) arasında 1M-trace'lik bir gün simüle eder. Depolama maliyetini ve her birinde neyin kaybedildiğini raporlar.

## Yayınla

Bu ders `outputs/skill-observability-stack.md` üretir. Stack, ölçek, bütçe, lisans duruşu verildiğinde, aracı/araçları seçer.

## Alıştırmalar

1. LangChain'deki takımın OSS self-hosted observability istiyor. Langfuse ya da Opik seç ve gerekçelendir.
2. Datadog'un $150K/ay verdiği günde 5M trace'te, Arize AX için break-even'ı hesapla.
3. Org rehberinin her LLM çağrısında zorunlu kılması gereken bir OpenTelemetry GenAI attribute kümesi tasarla.
4. Tek başına Phoenix'in üretim için yeterli olup olmadığını savun. Ne zaman yeterli olmaz?
5. Helicone 20ms proxy overhead'i. P99 TTFT 300 ms'de bu kabul edilebilir mi? SLA 100 ms ise?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| OpenLLMetry | "LLM'ler için OTel" | LLM'ler için açık-kaynak OpenTelemetry enstrümantasyonu |
| GenAI convention'ları | "OTel attribute'ları" | LLM çağrıları için standart OTel attribute adları |
| LangSmith | "LangChain observability" | LangChain ekosistemiyle paketlenmiş ticari platform |
| Langfuse | "OSS LangSmith" | Benzer özellik setiyle MIT OSS |
| Phoenix | "Arize dev aracı" | OpenTelemetry-native dev/eval platformu |
| Arize AX | "ölçek observability" | Ticari zero-copy Iceberg/Parquet observability |
| Helicone | "proxy observability" | LLM telemetri + gateway özellikleri toplayan HTTP proxy |
| Opik | "Comet LLM" | Comet'ten Apache 2.0 OSS dev platformu |
| Session replay | "trace yeniden çalıştırma" | Tool çağrılarıyla tam bir agent oturumunu yeniden oynat |
| Eval | "offline test" | Etiketli dataset üzerinde aday model/prompt çalıştırma |

## İleri Okuma

- [SigNoz — Top LLM Observability Tools 2026](https://signoz.io/comparisons/llm-observability-tools/)
- [Langfuse — Arize AX Alternative analysis](https://langfuse.com/faq/all/best-phoenix-arize-alternatives)
- [PremAI — Setting Up Langfuse, LangSmith, Helicone, Phoenix](https://blog.premai.io/llm-observability-setting-up-langfuse-langsmith-helicone-phoenix/)
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Arize Phoenix docs](https://docs.arize.com/phoenix)
- [Helicone docs](https://docs.helicone.ai/)
