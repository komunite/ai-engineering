# Uzun-Çalışan Arka Plan Agent'ları: Durable Execution

> Üretim uzun-horizon agent'lar `while True`'da çalışmaz. Her LLM çağrısı checkpoint, retry ve replay'li bir activity olur. Temporal'ın OpenAI Agents SDK entegrasyonu Mart 2026'da GA oldu. Claude Code Routines (Anthropic) zamanlanmış Claude Code çağrılarını kalıcı bir yerel process olmadan çalıştırır. Oturumlar human-input'ta duraklar, deploy'lardan sağ çıkar ve `thread_id` ile anahtarlanmış en son checkpoint'ten devam eder. Yeni ergonominin arkasında eski bir desen oturur — workflow orchestration — bir yeni input ile: kurtarmada deterministik olarak replay edilmesi gereken non-deterministik activity'ler olarak LLM çağrıları.

**Tür:** Öğrenim
**Diller:** Python (stdlib, minimal durable-execution state machine)
**Ön koşullar:** Faz 15 · 10 (Permission mode'ları), Faz 15 · 01 (Uzun-horizon agent'lar)
**Süre:** ~60 dakika

## Sorun

Dört saat çalışan bir agent düşün. Üç tool çağırır, kullanıcıya iki kez prompt'lar ve kırk LLM çağrısı yapar. Yarı yolda, üzerinde çalıştığı host yeniden başlar. Ne olur?

- Naive bir `while True` döngüsünde: her şey kaybolur. Koşu sıfırdan yeniden başlar. Üç tool çağrısı (gerçek yan etkilerle) tekrar yürütülür. Kullanıcı zaten onayladığı şeyler için yeniden prompt'lanır. Kırk LLM çağrısı yeniden fatura edilir.
- Durable execution ile: koşu en son checkpoint'ten devam eder. Zaten tamamlanmış activity'ler yeniden yürütülmez; sonuçları durable log'dan replay edilir. Kullanıcı zaten onayladığı şeyleri yeniden onaylamaz. Zaten yapılmış LLM çağrıları yeniden fatura edilmez.

Bu workflow engine'lerin on yıldır yayınladığı aynı desendir (Temporal, Cadence, Uber'in Cherami'si). Yeni olan LLM çağrılarının artık bir activity türü olmasıdır — non-deterministik, pahalı, yan etkili — ve bu desene temiz oturuyorlar.

Dersin çalışan teması: uzun-horizon güvenilirlik azalır (METR "35-dakika degradation"ı gözlemler — başarı oranı horizon ile yaklaşık olarak quadratically düşer). Durable execution güvenilirlik profilinin desteklediğinden daha uzun koşulara izin verir ki bu, tasarım doğruysa safe, tasarım yanlışsa unsafe şekilde başarısız olmanın yeni bir yoludur.

## Kavram

### Activity'ler, workflow'lar ve replay

- **Workflow**: deterministik orchestration kodu. Activity'lerin dizisini, dalları, bekleyişleri tanımlar. Event log'dan sürpriz divergence olmadan replay edilebilmesi için deterministik olmalıdır.
- **Activity**: non-deterministik, potansiyel olarak başarısız bir iş birimi. LLM çağrısı, tool çağrısı, dosya yazma, HTTP request. Her activity input'ları ve (tamamlandığında) output'ları ile loglanır.
- **Event log**: durable backing store. Her activity start, complete, fail, retry ve her workflow kararı kaydedilir.
- **Replay**: kurtarmada, workflow kodu baştan yeniden çalışır; zaten tamamlanmış her activity loglanmış sonucunu yeniden yürütmeden döner. Yalnızca tamamlanmamış activity'ler aslında çalıştırılır.

Bu, virtual DOM'a karşı yeniden render eden React veya commit'lerden bir working tree yeniden inşa eden Git ile aynı şekildir. Orchestrator'da determinizm, durability'yi ucuz yapan şeydir.

### LLM çağrıları desene neden uyar

LLM çağrıları:
- Non-deterministik (sıcaklık > 0; sıcaklık 0 bile model versiyonları arasında drift eder).
- Pahalı (para ve gecikme).
- Potansiyel olarak başarısız (rate limit'ler, timeout'lar).
- Yan etkili (tool çağırıyorlarsa).

Bu tam olarak activity profilidir. Her LLM çağrısını bir activity olarak sarmak sana exponential backoff'lu retry, restart'lar arasında checkpointing ve debugging için replay edilebilir bir trace verir.

### `thread_id` ile anahtarlanmış checkpoint'ler

LangGraph, Microsoft Agent Framework, Cloudflare Durable Objects ve Claude Code Routines hepsi aynı API şekline yakınsadı: bir `thread_id` (veya eşdeğeri) oturumu tanımlar; her state transition bir backend'e persist edilir (PostgreSQL varsayılan, dev için SQLite, cache için Redis); resume en son checkpoint'i okur.

Backend seçimi önemlidir:

- **PostgreSQL**: durable, queryable, deploy'lardan sağ çıkar. LangGraph için varsayılan.
- **SQLite**: yalnızca yerel-dev; host'lar arasında veri kaybeder.
- **Redis**: hızlı ama AOF/snapshot yapılandırılmamışsa geçici.
- **Cloudflare Durable Objects**: şeffaf dağıtık; unique bir key ile kapsamlı; saatlerden haftalara sağ çıkar.

### Birinci sınıf bir state olarak human-input

Propose-then-commit (Ders 15) durable bir "insan bekleniyor" state'i gerektirir. Workflow duraklar, harici kuyruk bekleyen request'i tutar ve bir onay tam olarak o noktadan devam eder. Durability olmadan bu best-effort'tır; onunla, gece bir onay gelir ve workflow sabah devam alır.

### 35-dakika degradation

METR ölçülen her agent sınıfının ~35 dakika sürekli işletimin ötesinde güvenilirlik bozulması gösterdiğini gözlemledi. Görev süresini ikiye katlamak failure oranını yaklaşık dört katına çıkarır. Durable execution bunu düzeltmez; güvenilirlik profilinin desteklediğinden daha uzun çalışmana izin verir. Safe desen, durability'yi yeniden-girişte taze HITL gerektiren checkpoint'lerle ve wall-clock süresinden bağımsız toplam compute'u kapsayan bütçe kill switch'leri (Ders 13) ile birleştirmektir.

### Durable execution'ın yanlış cevap olduğu zaman

- Human input'suz birkaç dakikadan kısa koşular. Overhead > fayda.
- Kesinlikle salt-okunur bilgi retrieval'ı.
- Doğruluğun bir context window içinde uçtan uca gerektirdiği görevler (bazı akıl yürütme görevleri; bazı one-shot üretim).

## Kullan

`code/main.py` stdlib Python'da minimal bir durable-execution engine uygular. Şunları destekler:

- Input'ları ve output'ları bir JSON event log'una loglayan `@activity` decorator'ı.
- Activity'leri sıralayan bir workflow fonksiyonu.
- Tamamlanmış activity'leri yeniden yürütmeden replay eden bir `run_or_replay(workflow, event_log)` fonksiyonu.

Driver üç-activity'li bir workflow simüle eder, yarı yolda crash olur ve (a) her şeyi yeniden yürüten naive bir retry'a karşı (b) yalnızca eksik activity'yi çalıştıran bir replay gösterir.

## Yayınla

`outputs/skill-durable-execution-review.md`, önerilen bir uzun-çalışan agent deployment'ını doğru durable-execution şekli için inceler: activity'ler, determinizm, checkpoint backend, human-input state ve HITL-on-resume politikası.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Naive retry ile replay arasında activity-yürütme sayımındaki farkı gözlemle. Crash noktasını değiştir ve replay sayımının buna göre değiştiğini göster.

2. Oyuncak engine'i `thread_id`'yi açık kullanmaya dönüştür. Engine'i paylaşan iki eşzamanlı oturum simüle et ve event log'larının çakışmadığını doğrula.

3. Oyuncak engine'deki bir activity'yi al. Bir non-determinizm tanıt (workflow kararı içinde bir wall-clock timestamp). Replay'de divergence'ı göster. Gerçek engine'lerin bunu nasıl ele aldığını açıkla (yan-etki kaydı, `Workflow.now()` API'leri).

4. LangChain "Runtime behind production deep agents" yazısını oku. Runtime'ın persist ettiği her state'i listele ve her birinin hangi failure mode'unu kapsadığını adlandır.

5. 6 saatlik otonom bir coding görevi için bir checkpoint politikası tasarla. Nerede checkpoint yaparsın? Crash'te resume nasıl görünür? Ne taze HITL gerektirir?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Workflow | "Agent'ın script'i" | Deterministik orchestration kodu; event log'dan replay edilebilir |
| Activity | "Bir adım" | Non-deterministik birim (LLM çağrısı, tool çağrısı); önce ve sonra loglanır |
| Event log | "Backing store" | Her state transition'ın durable kaydı |
| Replay | "Resume" | Workflow'u yeniden çalıştır; tamamlanmış activity'ler yeniden yürütmeden loglanmış sonuçları döner |
| Checkpoint | "Kayıt noktası" | thread_id ile anahtarlanmış persist edilmiş state; resume'da en son kazanır |
| thread_id | "Oturum key'i" | Durable state'i kapsayan tanımlayıcı |
| 35-dakika degradation | "Güvenilirlik bozulması" | METR: başarı oranı horizon ile ~quadratically düşer |
| Non-determinizm | "Replay'de drift" | Wall clock, random, LLM çıktısı; yan etki olarak kaydedilmeli |

## İleri Okuma

- [Anthropic — Claude Code Agent SDK: agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) — bütçe, tur ve resume semantiği.
- [Microsoft — Agent Framework: human-in-the-loop and checkpointing](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) — RequestInfoEvent şekli.
- [LangChain — The Runtime Behind Production Deep Agents](https://www.langchain.com/conceptual-guides/runtime-behind-production-deep-agents) — somut runtime gereksinimleri.
- [OpenAI Agents SDK + Temporal integration (Trigger.dev announcement)](https://trigger.dev) — LLM çağrıları için activity şekli.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — 35-dakika degradation referansı.
