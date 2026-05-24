# Üretim Runtime'ları: Queue, Event, Cron

> Üretim agent'ları altı runtime şeklinde çalışır: request-response, streaming, dayanıklı yürütme, queue-tabanlı arka plan, event-driven ve zamanlanmış. Framework seçmeden önce şekli seç. Observability her şekilde taşıyıcı.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 13 (LangGraph), Faz 14 · 22 (Voice)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Altı üretim runtime şeklini adlandır ve her birini bir framework / ürün desenine eşle.
- Uzun-ufuk görevler için dayanıklı yürütmenin (LangGraph) neden önemli olduğunu açıkla.
- Event-driven runtime'ı açıkla ve Claude Managed Agents'ın ne zaman uyduğunu.
- Multi-step agent'lar için observability-as-load-bearing iddiasını açıkla.

## Sorun

Üretim agent'ları bir Jupyter notebook'un yüzeye çıkarmadığı yollarla başarısız olur: adım 37'de network timeout, voice call ortasında kullanıcı kapatır, makine yeniden başlatıldığında cron job ölür, arka plan worker bellek tükenir. Runtime şekli hangi başarısızlıkların atlatılabilir olduğunu belirler.

## Kavram

### Request-response

- Senkron HTTP. Kullanıcı tamamlanmayı bekler.
- Yalnızca kısa görevler için uygun (<30sn).
- Stack'ler: Agno (Python + FastAPI), Mastra (TypeScript + Express/Hono/Fastify/Koa).
- Observability: standart HTTP access log'ları + OTel span'leri.

### Streaming

- Aşamalı çıktı için SSE ya da WebSocket.
- LiveKit bunu ses/video için WebRTC'ye genişletir (Ders 22).
- Stack'ler: streaming destekli herhangi bir framework + SSE/WS işleyen bir frontend.
- Observability: chunk başına timing, first-token latency, tail latency.

### Dayanıklı yürütme

- State her adımdan sonra checkpoint'lenir; başarısızlıkta auto-resume.
- AutoGen v0.4 actor model'i başarısızlıkları bir agent'a izole eder (Ders 14).
- LangGraph'ın çekirdek farklılaştırıcısı (Ders 13).
- Adım sayısı bilinmediğinde ve kurtarma maliyeti yüksek olduğunda zorunlu.

### Queue-tabanlı / arka plan

- Job bir queue'ya girer, worker'lar alır, sonuçlar webhook'lar ya da pub/sub üzerinden geri akar.
- Uzun-ufuk agent'lar için zorunlu (Anthropic'in computer use duyurusuna göre görev başına onlarca-yüzlerce adım).
- Stack'ler: Celery (Python), BullMQ (Node), SQS + Lambda (AWS), custom.
- Observability: queue derinliği, job başına latency dağılımı, DLQ boyutu.

### Event-driven

- Agent'lar trigger'lara subscribe olur: yeni e-posta, PR açıldı, cron tetiklendi.
- Claude Managed Agents bunu kutudan kapsar (Ders 17).
- CrewAI Flow'lar (Ders 15) event-driven deterministik workflow'ları yapılandırır.
- Observability: trigger kaynağı, event-to-start latency, agent latency.

### Zamanlanmış

- Periyodik çalışan cron-şekilli agent'lar.
- Dayanıklı yürütmeyle birleştir, böylece başarısız bir gecelik koşu sonraki tick'te devam eder.
- Stack'ler: Kubernetes CronJob + dayanıklı bir framework; hosted (Render cron, Vercel cron).

### 2026 deployment desenleri

- **CrewAI Flow'lar** event-driven üretim için.
- **Agno** stateless FastAPI Python microservice'ler için.
- **Mastra** server adapter'ları (Express, Hono, Fastify, Koa) embedding için.
- **Pipecat Cloud / LiveKit Cloud** yönetilen ses için (Ders 22).
- **Claude Managed Agents** hosted uzun-süren async için.

### Observability taşıyıcı

OpenTelemetry GenAI span'leri (Ders 23) artı bir Langfuse/Phoenix/Opik backend (Ders 24) olmadan, adım 40'ta başarısız olan multi-step bir agent'ı debug edemezsin. Bu üretim için opsiyonel değil. "Hızlı debug ederiz" ile "daha fazla log'la sıfırdan replay ederiz" arasındaki fark.

### Üretim runtime'ları nerede başarısız olur

- **Yanlış şekil seçimi.** 5-dakikalık bir görev için request-response seçmek. Kullanıcılar kapatır; worker'lar birikir; retry'lar compound olur.
- **DLQ yok.** Dead-letter'sız queue worker'ları. Başarısız job'lar kaybolur.
- **Opak arka plan işi.** Arka plan agent trace export'suz çalışır. Kullanıcı raporlayana kadar başarısızlıklar görünmez.
- **Dayanıklı state'i atlamak.** Yeniden başlamayı göze alamadığın > 30 saniyelik herhangi bir koşu dayanıklı yürütme gerektirir.

## İnşa Et

`code/main.py` bir stdlib multi-shape demo:

- Request-response endpoint (düz fonksiyon).
- Streaming handler (generator).
- DLQ'lu queue-tabanlı worker.
- Event trigger registry.
- Cron-şekilli scheduler.

Çalıştır:

```bash
python3 code/main.py
```

Çıktı: aynı görevde her şeklin davranışını gösteren beş trace. Aynı agent mantığı, farklı dış kabuklar. Dayanıklı yürütme (altıncı şekil) Ders 13'te LangGraph checkpointing ile kasten kapsanıyor.

## Kullan

- Chat-tarzı UX için **Request-response**.
- Aşamalı yanıtlar için **Streaming**.
- Uzun-ufuk görevler için **Dayanıklı**.
- Batch / async / uzun-süren için **Queue**.
- Agent reaktivitesi için **Event**.
- Housekeeping (memory consolidation, eval'ler, cost report'lar) için **Cron**.

## Yayınla

`outputs/skill-runtime-shape.md` bir görev için runtime şekli seçer ve observability gereksinimlerini kablolar.

## Alıştırmalar

1. Ders 01 ReAct döngünü stack'inde altı şeklin hepsine port et. Hangi şekil hangi ürün yüzeyine uyar?
2. Queue-tabanlı demoya bir DLQ ekle. %10 job başarısızlığı simüle et; DLQ boyutunu yüzeye çıkar.
3. Günün en iyi 20 trace'ine karşı gecelik çalışan bir cron-tetiklemeli eval agent yaz.
4. Backpressure'lı streaming uygula: client yavaşsa, agent'ı duraklat. Bu bir turn budget ile nasıl etkileşir?
5. Claude Managed Agents dokümanlarını oku. Self-hosted uzun-ufuk bir agent'ı managed'a ne zaman taşırsın?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Request-response | "Senkron" | Kullanıcı bekler; yalnızca kısa görevler |
| Streaming | "SSE / WS" | Aşamalı çıktı; daha iyi UX; chunk başına latency observable |
| Dayanıklı yürütme | "Başarısızlıktan devam" | Checkpoint'lenmiş state; son adımda yeniden başla |
| Queue-tabanlı | "Arka plan job'ları" | Producer / worker pool / DLQ |
| Event-driven | "Trigger-tabanlı" | Agent dış event'lere tepki verir |
| DLQ | "Dead-letter queue" | Başarısız job'lar için park yeri |
| Claude Managed Agents | "Hosted harness" | Caching + compaction ile Anthropic-hosted uzun-süren async |

## İleri Okuma

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — dayanıklı yürütme detayları
- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) — hosted uzun-süren async
- [Anthropic, Introducing computer use](https://www.anthropic.com/news/3-5-models-and-computer-use) — "görev başına onlarca-yüzlerce adım"
- [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — actor-model fault isolation
