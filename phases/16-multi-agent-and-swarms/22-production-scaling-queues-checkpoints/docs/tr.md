# Üretim Ölçekleme — Kuyruklar, Checkpoint'ler, Dayanıklılık

> Çoklu-agent sistemlerini binlerce eş zamanlı çalıştırmaya ölçeklendirmek **dayanıklı yürütme** gerektirir. LangGraph runtime'ı her super-step'ten sonra `thread_id` ile anahtarlanmış bir checkpoint yazar (varsayılan Postgres); worker çökmeleri bir lease'i serbest bırakır ve başka bir worker sürdürür. Agent'lar insan girdisini sınırsız bekleyebilir. **MegaAgent** (arXiv:2408.09955) üç durumlu (Idle / Processing / Response) agent başına producer-consumer kuyruk ve iki-katmanlı koordinasyon (grup-içi chat + gruplar-arası admin chat) çalıştırdı. **Fiber/async** LLM streaming için thread-per-job'u yener: thread'ler token beklerken zamanın %99'unu boşta oturur, fiber'lar I/O'da iş birlikçi yield eder. Karşı görüş: Ashpreet Bedi'nin "Scaling Agentic Software"ı yük başka türlü kanıtlanana kadar **FastAPI + Postgres + başka hiçbir şey** öneriyor — basit mimariler beklenenden öteye gider. Bu ders dayanıklı bir checkpoint log'u, durum geçişli agent başına bir iş kuyruğu, async-vs-thread demosu inşa eder ve pragmatik "basit başla" kuralını yerleştirir.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib, `asyncio`, `sqlite3`)
**Ön koşullar:** Faz 16 · 09 (Parallel Swarm Networks), Faz 16 · 13 (Paylaşılan Bellek)
**Süre:** ~75 dakika

## Sorun

Bir prototip çoklu-agent sistemi tek laptop'ta üç agent ile in-memory event loop'ta çalışıyor. Üretime taşıyorsun:

- Agent'lar bazen saatlerce çalışır (uzun araştırma, human-in-the-loop bekleme).
- Worker process'leri çöker. Yeniden başlatma state'i kaybeder.
- Pik yük ortalamanın 10×'u; yatay ölçeklendirme gerekli.
- Kullanıcılar agent-çalıştırma başına öder; ücretlendirme için exactly-once semantik gerekli.

In-memory event loop bunların hiçbirini yapmaz. Altında dayanıklı bir yürütme katmanına ihtiyacın var. 2026 kanonik seçenekler:

1. Checkpoint'li bir workflow engine (Temporal, LangGraph runtime).
2. State store'lu mesaj kuyruğu (Postgres + SQS/RabbitMQ).
3. Actor-model framework'leri (MegaAgent'ın agent başına producer-consumer'ı).
4. El yapımı FastAPI + Postgres (Bedi'nin argümanı).

Bu ders her birinin minyatürünü inşa eder.

## Kavram

### Dayanıklı yürütme, desen

Dayanıklı-yürütme motoru her "adım"dan sonra tam program state'ini kalıcılaştırır (LangGraph dilinde super-step). Çökmede:

```
worker adım ortasında çöker
  -> lease timeout
  -> başka bir worker thread_id'i alır
  -> son checkpoint'ten sürdürür
  -> mükerrer side effect yok
```

Bunun çalışması için gereksinimler:

- **Serileştirilebilir state.** Tüm agent state'i kalıcılaştırılabilir olmalı. Canlı veritabanı bağlantılı fonksiyon closure'ları hayatta kalmaz.
- **Deterministik sürdürme.** Aynı state ve aynı girdiler verili, agent aynı eylemleri üretir (ya da LLM çağrıları için dışsal deterministik bir oracle'a erteler).
- **Idempotent side effect'ler.** Dışsal çağrılar (tool çağrıları, ödemeler) idempotent olmalı ya da bir dedup anahtarı kullanmalı.

LangGraph her super-step'ten sonra checkpoint yazar; Temporal her activity'den sonra yazar; Restate event-sourced journal kullanır. Üçü de aynı deseni uygular.

### LangGraph'in runtime'ı

Her agent'ın bir `thread_id`'si vardır; state tipli bir dict'tir; her super-step checkpoints tablosuna bir satır yazar. Sürdürmede runtime sıfırdan değil, son checkpoint'ten replay yapar. Agent'lar insan girdisi beklerken `interrupt()` edebilir; runtime kalıcılaştırır ve worker'ı serbest bırakır. Girdi geldiğinde herhangi bir worker sürdürebilir.

Bu Nisan 2026'da referans üretim tasarımıdır.

### MegaAgent'ın agent başına kuyruğu

arXiv:2408.09955 bir ölçek deneyini tanımlar: bir cluster'da binlerce eş zamanlı agent. Mimari:

```
agent i:
  state ∈ {Idle, Processing, Response}
  in_queue   <- agent i'ye adreslenmiş mesajlar
  out_queue  -> yanıtlar + side effect'ler

koordinatörler:
  grup-içi chat  (aynı gruptaki agent'lar)
  gruplar-arası admin chat  (üst seviye yönlendirme)
```

İki-katmanlı koordinasyon grup-içi konuşmanın yoğun olmasına izin verirken gruplar-arası seyrek kalır — binlerce agent'ta maliyeti doğrusal tutmak için kullanılan desen.

### Async vs thread-per-job

LLM çağrıları I/O-bound'dur. Sıradaki token'ı bekleyen bir thread zamanın %99'u boştadır. Thread'ler her biri ~1MB RAM mal olur; 10.000 eş zamanlı çağrıda bu sadece stack'ler için 10GB.

Fiber'lar (Python `asyncio`, Go goroutine'lar, Rust `tokio`) I/O'da iş birlikçi yield eder. Aynı 10.000 çağrı process'e rahatça sığar. LLM-agent ölçeğinde async optimizasyon değil — mimaridir.

İstisna: CPU-bound post-processing (embedding, tokenizer hileleri) hâlâ thread ya da process ister. I/O katmanını CPU katmanından ayır.

### Bedi'nin karşı görüşü

"Scaling Agentic Software" (Ashpreet Bedi, 2026) çoğu takımın yükü ölçmeden önce aşırı-mühendislik yaptığını savunuyor. Pragmatik varsayılan:

- FastAPI + Postgres.
- Her agent çalıştırması bir satır; state iyimser eş zamanlılıkla yerinde güncellenir.
- `pg_notify` ya da basit bir Celery worker üzerinden arka plan iş'leri.
- Uygulama kodunda retry politikası.

Yönetilebilir görevlerde ~100 eş zamanlı agent-çalıştırmasının altındaki yükler için, çoğu zaman ihtiyacın olan budur. Başarısız olduğunu ölçtüğünde yükselt.

Kural: basit mimarilerin çözemeyeceği somut bir problem ile karşılaştığında dayanıklı-yürütme framework'leri benimse. Erken benimseme karşılığını ödemeyecek seremoniler için zaman yakar.

### Exactly-once semantik

Ödenen agent çalıştırmaları için "etkili exactly-once"a (at-least-once teslimi + idempotent tüketici) ihtiyacın var. Mühendislik hamleleri:

- **Çalıştırma başına dedup anahtarı.** Her side-effect çağrısına dahil et.
- **Outbox deseni.** Side effect'ler önce bir tabloya yazar, sonra ayrı bir process onları yürütür. Her iki adım idempotent.
- **Telafi eden işlemler.** Bir side effect başarılı olduğunda ama takip yazımı başarısız olduğunda, telafi planla.

Bunlar veritabanı-mühendisliği desenleri, LLM'e özgü değil. LLM vergisi yalnızca LLM çağrılarının yavaş olmasıdır; geri kalan her şey standart dağıtık sistemlerdir.

### Rainbow deployment

Anthropic'in çoklu-agent araştırma sistemi "rainbow deployment'lar" kullanır: uzun-süreli agent'ların her kod dağıtımında öldürülmek zorunda olmaması için agent runtime'ının birden çok sürümü eş zamanlı çalışır. Yeni sürümleri trafiğin bir diliminde canary; agent'ları bittiğinde eski sürümleri emekli et.

Bu uzun-süreli stateful sistemler için standarttır; 2026 uyarlaması agent'ların saatlerce yaşayabilmesidir, dolayısıyla dağıtım döngüleri buna uymalıdır.

### Kanonik üretim kontrol listesi

- Dayanıklı state (checkpoint'ler, snapshot'lar ya da outbox + replay edilebilir log).
- Idempotent side effect'ler.
- LLM çağrıları için async I/O katmanı.
- Dedup'lu at-least-once teslimi.
- Stateful workload'lar için rainbow/canary deployment.
- Observability: agent başına izler, super-step audit, retry sayacı.

## İnşa Et

`code/main.py` şunları uygular:

- `CheckpointStore` — thread-id anahtarlı SQLite-destekli checkpoint log'u. Her super-step bir satır ekler.
- `run_with_checkpoint(agent, thread_id)` — çalıştırma ortasında bir çökmeyi simüle eder; ikinci bir worker son checkpoint'ten sürdürür.
- `AgentQueue` — küçük bir iş kuyruğuyla agent başına Idle / Processing / Response state machine.
- `demo_async_vs_threads()` — asyncio ve thread'ler aracılığıyla 500 eş zamanlı simüle edilmiş "LLM çağrısı" çalıştırır; duvar-saati ve pik belleği (yaklaşık) rapor eder.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: simüle edilmiş çökmeden sonra checkpoint sürdürme başarılı; async versiyon < 1s'de 500 eş zamanlı çağrıyı ele alır; thread versiyonu birkaç saniye alır ve eş zamanlı birim başına çok daha fazla bellek kullanır.

## Kullan

`outputs/skill-scaling-advisor.md` dayanıklı-yürütme seçimi üzerine tavsiye verir: FastAPI + Postgres, LangGraph runtime, Temporal ya da özel. Yüke, state-saklama ihtiyaçlarına ve deploy sıklığına göre kalibre edilmiş.

## Yayınla

Kanonik üretim sertleştirmesi:

- **Basit başla (Bedi'nin kuralı).** Başarısız olduğunu ölçene kadar FastAPI + Postgres.
- **Optimize etmeden önce her şeyi enstrümante et.** Çalıştırma başına gecikme histogramı, adım başına zaman, retry sayısı, başarısızlık kategorizasyonu.
- **Side effect'ler için outbox deseni.** Özellikle ödemeler ve dışsal API çağrıları.
- **Rainbow deploy'lar.** Deploy'lar sırasında devam eden agent çalıştırmalarını asla öldürme.
- **Dayanıklı-yürütme motorlarını (Temporal / LangGraph / Restate) şu durumlarda benimse:** saat-uzunluğu human-in-the-loop bekleme, çapraz-bölge koordinasyonu, karmaşık retry/telafi politikalarına çarptığında.
- **I/O katmanı için async.** CPU-bound post-processing için yalnızca thread'ler.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Checkpoint sürdürmenin çalıştığını doğrula; async vs thread eş zamanlılık farkını ölç.
2. Bir **outbox** tablosu uygula: her tool çağrısı önce outbox'a yazar, sonra ayrı bir goroutine/task yürütür. Tool çağrısını iki kez çalıştırarak idempotency'yi doğrula.
3. Bir **rainbow deploy** simüle et: iki eş zamanlı runtime sürümü; yeni thread_id'lerin yarısını her birine yönlendir; eski sürümdeki devam eden thread'lerin kesintiye uğramadığını doğrula.
4. LangGraph'in runtime dokümanını (aşağıda bağlantı) oku. Runtime'ın hangi özelliklerini el yapımı FastAPI + Postgres versiyonunda replike etmenin en uzun süreceğini belirle. Bu benimseme nedeni mi, yoksa erteleyebilir misin?
5. MegaAgent (arXiv:2408.09955) Bölüm 3'ü oku. İki-katmanlı koordinasyon (grup-içi + gruplar-arası admin chat) açık. Bunu iki kuyruk ailesi olan bir mesaj kuyruğuna nasıl eşleyeceğini taslak et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Dayanıklı yürütme | "Program state'ini kalıcılaştır" | Motor her super-step'ten sonra state yazar; çökme kurtarımı deterministiktir. |
| Super-step | "İşlemsel sınır" | Checkpoint'ler arası iş birimi. LangGraph terimi. |
| thread_id | "Agent çalıştırma tanımlayıcısı" | Checkpoint'leri ve sürdürme mantığını bağlayan anahtar. |
| Idempotency | "Retry için güvenli" | Bir side effect'i tekrarlamak bir denemeyle aynı sonucu üretir. |
| Outbox deseni | "Side effect'leri ayır" | Bir tabloya niyet yaz; ayrı bir executor yapar ve tamamlandı işaretler. |
| At-least-once teslimi | "Olası mükerrerler" | Mesaj kuyruğu semantiği; dedup anahtarı tüketiciyi etkili-tek-sefer yapar. |
| Rainbow deploy | "Örtüşen sürümler" | Uzun-süreli workload'lar sırasında birden çok runtime sürümü eş zamanlı. |
| Async fiber | "İş birlikçi yield" | User-mode eş zamanlılık; I/O-bound yükler için thread'lere göre ucuz. |
| Checkpoint | "State anlık görüntüsü" | Bir super-step sınırında serileştirilmiş state; sürdürme için anahtar. |

## İleri Okuma

- [LangChain — The runtime behind production deep agents](https://www.langchain.com/conceptual-guides/runtime-behind-production-deep-agents) — LangGraph runtime tasarımı
- [MegaAgent](https://arxiv.org/abs/2408.09955) — binlerce eş zamanlı agent'ta agent başına producer-consumer kuyruk; iki-katmanlı koordinasyon
- [Matrix](https://arxiv.org/abs/2511.21686) — koordinasyon substratı olarak mesaj kuyruklarıyla merkeziyetsiz framework
- [Temporal docs](https://docs.temporal.io/) — dayanıklı yürütme için referans workflow engine
- [Anthropic — Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — rainbow deployment dahil üretim dersleri
