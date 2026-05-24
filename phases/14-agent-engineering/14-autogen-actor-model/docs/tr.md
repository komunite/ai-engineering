# AutoGen v0.4: Actor Model ve Agent Framework

> AutoGen v0.4 (Microsoft Research, Ocak 2025) agent orkestrasyonunu actor model etrafında yeniden tasarladı. Asenkron mesaj exchange, event-driven agent'lar, fault isolation, doğal concurrency. Framework artık maintenance mode'da; Microsoft Agent Framework (public preview Ekim 2025) halefi olarak gelirken.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 12 (Workflow Desenleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Actor model'i açıkla: aktörler olarak agent'lar, tek IPC olarak mesajlar, aktör başına failure isolation.
- AutoGen v0.4'ün üç API katmanını — Core, AgentChat, Extensions — ve her birinin ne için olduğunu adlandır.
- Mesaj iletimini işlemden ayırmanın neden fault isolation ve doğal concurrency verdiğini açıkla.
- Python'da bir stdlib actor runtime uygula ve iki-agent kod-inceleme akışını ona port et.

## Sorun

Çoğu agent framework'ü senkron: bir agent üretir, bir agent tüketir, call stack'te. Başarısızlıklar stack'i çökertir. Concurrency üstüne bolted-on. Distribution yeniden yazma gerektirir.

AutoGen v0.4'ün yanıtı: actor model. Her agent özel bir inbox'lı bir aktör. Mesajlar tek interaksiyon. Runtime iletimi işlemden ayırır. Başarısızlıklar bir aktöre izole olur. Concurrency native. Distribution sadece farklı transport.

## Kavram

### Aktörler

Bir aktörün:

- Özel bir state'i var (dışarıdan asla doğrudan dokunulmaz).
- Bir inbox'ı var (mesaj kuyruğu).
- Bir handler'ı var: `receive(message) -> effects` burada effect'ler "yanıt ver," "başka aktöre gönder," "yeni aktör spawn et," "state güncelle," "kendini durdur" olabilir.

İki aktör bellek paylaşamaz. Yalnızca mesaj gönderebilirler.

### AutoGen v0.4'te üç API katmanı

1. **Core.** Düşük-seviye actor framework. `AgentRuntime`, `Agent`, `Message`, `Topic`. Asenkron mesaj exchange, event-driven.
2. **AgentChat.** Task-driven yüksek-seviye API (v0.2'nin ConversableAgent'ının değiştireni). `AssistantAgent`, `UserProxyAgent`, `RoundRobinGroupChat`, `SelectorGroupChat`.
3. **Extensions.** Entegrasyonlar — OpenAI, Anthropic, Azure, tool'lar, bellek.

### Ayırma neden önemli

v0.2 model'inde `agent_a.chat(agent_b)` çağrısı agent_a'yı agent_b dönene kadar senkron bloklar. v0.4'te `send(agent_b, msg)` mesajı agent_b'nin inbox'ına koyar ve döner. Runtime sonra iletir. Üç sonuç:

- **Fault isolation.** Agent B'nin çökmesi Agent A'yı çökertmez — runtime başarısızlığı B'nin handler'ında yakalar ve ne yapacağına karar verir (log, retry, dead-letter).
- **Doğal concurrency.** Aynı anda çok mesaj uçuşta; aktörler inbox'larını eşzamanlı işler.
- **Distribution-hazır.** Inbox + transport aktör in-process ya da başka bir host'ta olsun, aynı abstraction.

### Topolojiler

- **RoundRobinGroupChat.** Aktörler sabit bir rotasyonda sıra alır.
- **SelectorGroupChat.** Bir selector agent konuşma context'ine göre kimin sırada olduğunu seçer.
- **Magentic-One.** Web tarama, kod yürütme, dosya işleme için referans çoklu-agent takımı. AgentChat üzerine kurulu.

### Observability

OpenTelemetry desteği built-in. Her mesaj bir span yayar; tool çağrıları 2026 OTel GenAI semantik konvansiyonlarına göre `gen_ai.*` attribute'larını taşır (Ders 23).

### Durum: maintenance mode

2026 başı: AutoGen v0.7.x araştırma ve prototipleme için stabil. Microsoft aktif geliştirmeyi Microsoft Agent Framework'üne kaydırdı (public preview 1 Ekim 2025; 1.0 GA Q1 2026 sonu hedeflendi). AutoGen desenleri ileriye temiz şekilde port olur — dayanıklı fikir actor model.

## İnşa Et

`code/main.py` bir stdlib actor runtime uyguluyor:

- `Message` — `sender`, `recipient`, `topic`, `body`'li tipli payload.
- `Actor` — `receive(message, runtime)` ile soyut.
- `Runtime` — paylaşılan kuyruk, iletim, failure isolation'lı event loop.
- İki-aktör demo: `ReviewerAgent` kodu inceler, `ChecklistAgent` bir checklist çalıştırır; consensus'a kadar mesaj exchange ederler.

Çalıştır:

```
python3 code/main.py
```

Trace mesaj iletimini, bir aktörde diğerini çökertmeyen simüle edilmiş bir başarısızlığı ve paylaşılan bir verdict'te yakınsamayı gösterir.

## Kullan

- **AutoGen v0.4/v0.7** (maintenance) — araştırma, prototipleme, çoklu-agent desenleri için stabil.
- **Microsoft Agent Framework** (public preview) — ileri yol; tazelenmiş bir API'de aynı actor-model fikirleri.
- **LangGraph swarm topolojisi** (Ders 13) — paylaşılan-tool handoff'ları üzerinden benzer desen.
- **Custom actor runtime** — spesifik transport (NATS, RabbitMQ, gRPC) gerektiğinde.

## Yayınla

`outputs/skill-actor-runtime.md` belirli bir çoklu-agent görevi için minimal bir actor runtime artı bir takım şablonu (RoundRobin ya da Selector) üretir.

## Alıştırmalar

1. Bir dead-letter queue ekle: bir handler raise ettiğinde, başarısız mesajı insan incelemesi için park et. DLQ oyuncağında ne sıklıkla vuruluyor?
2. `SelectorGroupChat` uygula: bir selector aktör konuşma state'ine göre bir sonraki mesajı kimin işleyeceğini seçer.
3. Distributed transport ekle: in-process kuyruğu bir JSON-over-HTTP server ile değiştir, böylece aktörler ayrı süreçlerde çalışabilir.
4. Mesaj başına OTel span'i (ya da no-op stand-in) kablola. Ders 23'e göre `gen_ai.agent.name`, `gen_ai.operation.name` yay.
5. AutoGen v0.4 mimari yazısını oku. Oyuncağını gerçek `autogen_core` API'sine port et. Üretimde önemli olan neyi atladın?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Aktör | "Agent" | Özel state + inbox + handler; paylaşılan bellek yok |
| Mesaj | "Event" | Tipli payload; aktörlerin tek etkileşim yolu |
| Inbox | "Mailbox" | Aktör başına bekleyen mesaj kuyruğu |
| Runtime | "Agent host" | Mesajları yönlendiren ve başarısızlıkları izole eden event loop |
| Topic | "Channel" | Aktörler arası adlandırılmış publish-subscribe route |
| Fault isolation | "Let it crash" | Bir aktörün başarısız olması diğerlerini çökertmez |
| RoundRobinGroupChat | "Sabit-rotasyon takım" | Aktörler sırayla tur alır |
| SelectorGroupChat | "Context-routed takım" | Selector kimin sırada olduğunu seçer |
| Magentic-One | "Referans takım" | Web + kod + dosya için çoklu-agent ekibi |

## İleri Okuma

- [AutoGen v0.4, Microsoft Research](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — yeniden tasarım yazısı
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — graph-şekilli alternatif
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — AutoGen'in varsayılan olarak yaydığı span'ler
