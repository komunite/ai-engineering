# Çoklu-Agent Primitive Modeli

> 2026'da çıkan her çoklu-agent framework'ü — AutoGen, LangGraph, CrewAI, OpenAI Agents SDK, Microsoft Agent Framework — dört boyutlu bir tasarım uzayında bir noktadır. Dört primitive, fazlası değil: agent, handoff, paylaşılan state, orchestrator. Bu ders bunları sıfırdan inşa eder, dört primitive üzerinde oyuncak bir sistem çalıştırır, sonra her büyük framework'ü aynı eksenlere eşler — böylece herhangi bir yeni sürümü tek paragrafta okuyabilirsin.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 (Agent Engineering), Faz 16 · 01 (Neden Çoklu-Agent)
**Süre:** ~60 dakika

## Sorun

Her altı ayda bir yeni bir çoklu-agent framework'ü çıkar. 2023'te AutoGen. 2024'te CrewAI. 2024'te LangGraph ve OpenAI Swarm. Nisan 2025'te Google ADK. Şubat 2026'da Microsoft Agent Framework RC. Her basın bülteni "doğru soyutlama" olduğunu iddia eder.

Onları teker teker öğrenmeye çalışırsan tükenirsin. API'lar farklı görünür. Dokümanlar bir "agent"ın ne olduğu konusunda anlaşmaz. Bir framework paylaşılan belleğine "blackboard", diğeri "message pool", üçüncüsü "StateGraph" der. Alanın sadece kendini tekrar ettiğinden şüphelenmeye başlarsın.

Etmiyor. Pazarlamanın altında dört primitive stabildir. Bir kez öğren, her yeni framework'ü tek paragrafta oku.

## Kavram

### Dört primitive

1. **Agent** — bir sistem prompt'u artı bir tool listesi. Stateless; her çalıştırma sistem prompt'u ve mevcut mesaj geçmişinden başlar.
2. **Handoff** — bir agent'tan diğerine yapılandırılmış kontrol transferi. Mekanik olarak, yeni bir agent döndüren bir tool çağrısı ya da bir koşulu izleyen bir graf kenarı.
3. **Paylaşılan state** — birden fazla agent'ın okuyabildiği (bazen yazabildiği) herhangi bir veri yapısı. Message pool, blackboard, key-value store, vektör belleği.
4. **Orchestrator** — sıradakinin kim konuşacağına karar veren. Seçenekler: açık bir graf (deterministik), bir LLM speaker-selector (yumuşak), son konuşmacının handoff çağrısı (OpenAI Swarm) ya da bir kuyruk üzerinde scheduler (sürü mimarisi).

Tüm tasarım uzayı bu. Her framework her eksen için varsayılanlar seçer; gerisi yüzey sözdizimi.

### Her 2026 framework'ünün buna nasıl eşlendiği

| Framework | Agent | Handoff | Paylaşılan state | Orchestrator |
|-----------|-------|---------|--------------|--------------|
| OpenAI Swarm / Agents SDK | `Agent(instructions, tools)` | tool Agent döndürür | arayanın sorunu | LLM'in sıradaki handoff çağrısı |
| AutoGen v0.4 / AG2 | `ConversableAgent` | GroupChat üzerinde speaker-selector | message pool | selector fonksiyonu (LLM ya da round-robin) |
| CrewAI | `Agent(role, goal, backstory)` | `Process.Sequential / Hierarchical` | Task çıktıları zincirli | manager LLM ya da statik sıra |
| LangGraph | node fonksiyonu | graf kenarı + koşul | `StateGraph` reducer | graf, deterministik |
| Microsoft Agent Framework | agent + orkestrasyon desenleri | desene özgü | thread / context | desene özgü |
| Google ADK | agent + A2A card | A2A task | A2A artifact'ları | host karar verir |

Yüzey farkları büyük görünür. Altta: aynı dört düğme.

### Bu neden önemli

Primitive'leri gördükten sonra framework karşılaştırması kısa bir kontrol listesi olur:

- Orchestrator yönlendirme için LLM'e mi güveniyor (Swarm) yoksa yönlendirmeyi kodda mı sabitliyor (LangGraph)?
- Paylaşılan state tam geçmiş mi (GroupChat) yoksa projeksiyonlu mu (StateGraph reducer)?
- Agent'lar birbirinin prompt'unu değiştirebilir mi (CrewAI manager) yoksa sadece handoff mı yapabilir (Swarm)?

Bu üç soru, hangi framework'ün belirli bir soruna uyduğunun %80'ini yanıtlar. "En iyi çoklu-agent framework'ü"nü aramayı bırakır, gerçekten önemsediğin eksene göre tasarım yapmaya başlarsın.

### Stateless içgörüsü

Paylaşılan state hariç her primitive stateless'tir. Agent (prompt, tools)'un fonksiyonudur. Handoff bir fonksiyon çağrısıdır. Orchestrator bir scheduler'dır. **Sistemdeki tek stateful şey paylaşılan state'tir.** İlginç bug'ların hepsi orada yaşar: bellek zehirlenmesi (Ders 15), mesaj sıralaması, sürümleme, yazma çekişmesi.

Paylaşılan state'i gizleyen framework'ler (Swarm) sorunu arayana iter. Onu merkezileştirenler (LangGraph checkpoint, AutoGen pool) onu denetlenebilir yapar ama koordinasyon maliyetini paylaşılan-state implementasyonuna kaydırır.

### Tek bir primitive'in anatomisi

#### Agent

```
Agent = (system_prompt, tools, model, optional_name)
```

Bellek yok. State yok. Aynı sistem prompt'u ve tool'lara sahip iki agent değiştirilebilirdir. Agent-başına state gibi görünen her şey aslında paylaşılan state'te ya da handoff protokolündedir.

#### Handoff

```
Handoff = (from_agent, to_agent, reason, payload)
```

Üç implementasyon hakim:

- **Fonksiyon return** — tool sıradaki agent'ı döndürür. Bu OpenAI Swarm desenidir. Agent'lar yönlendirmeyi tool şemalarında taşır.
- **Graf kenarı** — LangGraph. Kenarlar bildirimseldir. LLM bir değer üretir; bir koşul sıradaki node'u seçer.
- **Speaker selection** — AutoGen GroupChat. Bir selector fonksiyonu (bazen kendisi bir LLM çağrısı) pool'u okur ve sıradakinin kim konuşacağını seçer.

#### Paylaşılan state

```
SharedState = { messages: [], artifacts: {}, context: {} }
```

En azından bir mesaj listesi. Çoğu zaman daha fazlası: yapılandırılmış artefaktlar (CrewAI Task çıktıları), tipli context (LangGraph reducer'ları), dışsal bellek (MCP, vektör DB).

İki topoloji: **tam pool** (her agent her mesajı görür) ve **projeksiyonlu** (agent'lar role-kapsamlı bir görünüm görür). Tam pool'lar basittir ve kötü ölçeklenir. Projeksiyonlu pool'lar ölçeklenir ama önceden şema tasarımı gerektirir.

#### Orchestrator

```
Orchestrator = ({state, last_speaker}) -> next_agent
```

Dört çeşit:

- **Statik** — graf build zamanında sabitlenmiş (LangGraph deterministik, CrewAI Sequential).
- **LLM-seçili** — bir LLM pool'u okur ve sıradaki konuşmacıyı seçer (AutoGen, CrewAI Hierarchical).
- **Handoff-driven** — mevcut agent bir handoff tool'u çağırarak karar verir (Swarm).
- **Queue-driven** — worker'lar paylaşılan bir kuyruktan çeker; açık bir sıradaki-konuşmacı yok (sürü mimarileri, Matrix).

### Framework'ler arasında ne değişir

Primitive'ler sabitlendikten sonra kalan tasarım kararları:

- **Bellek stratejisi** — geçici vs dayanıklı checkpoint'leme (LangGraph checkpointer).
- **Güvenlik sınırı** — handoff'u kim onaylayabilir (human-in-the-loop).
- **Maliyet muhasebesi** — agent başına token bütçeleri.
- **Observability** — handoff'ları izleme, replay için state'i kalıcılaştırma.

Hepsi primitive'lerin üzerinde uygulanabilir. Hiçbiri yeni primitive değil.

## İnşa Et

`code/main.py` dört primitive'i ~150 satır stdlib Python'da uygular. Gerçek LLM yok — her agent senaryolu bir politikadır, böylece odak koordinasyon yapısında kalır.

Dosya şunları export eder:

- `Agent` — isim, sistem prompt'u, tool'lar, politika fonksiyonundan oluşan bir dataclass.
- `Handoff` — yeni bir agent döndüren bir fonksiyon.
- `SharedState` — thread-safe bir message pool.
- `Orchestrator` — üç varyant: `StaticOrchestrator`, `HandoffOrchestrator`, `LLMSelectorOrchestrator` (simüle edilmiş).

Demo aynı üç-agent pipeline'ını (research → write → review) üç orchestrator tipi üzerinden çalıştırır ve sonunda message pool'u yazar. Çıktıların yalnızca *sıradakini kimin seçtiği* konusunda farklılaştığını görebilirsin; agent'lar ve paylaşılan state çalıştırmalar arasında aynıdır.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: üç orchestrator çalıştırması, desen başına bir. Her biri final message pool'unu yazar. Handoff-driven çalıştırma, araştırmacı erken bittiğine karar verirse daha az agent'a ulaşır — küçük ölçekte LLM-yönlendirme takası budur.

## Kullan

`outputs/skill-primitive-mapper.md`, herhangi bir çoklu-agent kod tabanını veya framework dokümanını okuyup dört-primitive eşlemesini döndüren bir skill'dir. Yeni bir framework sürümünde, dokümanları derinlemesine okumadan önce tek paragraflık bir anlayış için onu çalıştır.

## Yayınla

Yeni bir framework benimsemeden önce, onun için primitive eşlemesini yaz. Yazamazsan, dokümanlar eksiktir ya da framework beşinci bir primitive icat ediyordur (nadir — daha önce görmediğin bir paylaşılan-state çeşidini kontrol et).

Eşlemeyi mimari dokümanına sabitle. Yeni bir takım üyesi katıldığında, API dokümanlarından önce ona eşlemeyi gönder. Framework sürümleri değiştiğinde, changelog'u değil, eşlemeyi diff'le.

## Alıştırmalar

1. `code/main.py`'yi farklı agent politikalarıyla üç kez çalıştır. Orchestrator seçiminin hangi agent'ların çalıştığını nasıl değiştirdiğini gözlemle.
2. Dördüncü bir orchestrator tipi uygula: agent'ların paylaşılan state'i iş için poll'ladığı queue-driven biri. Hangi deadlock olabilir ve nasıl tespit edersin?
3. LangGraph quickstart'ı (https://docs.langchain.com/oss/python/langgraph/workflows-agents) al ve onu dört primitive olarak yeniden yaz. LangGraph'in soyutlamalarından hangisi 1:1 eşleniyor ve hangisi kolaylık wrapper'ı?
4. OpenAI Swarm cookbook'unu (https://developers.openai.com/cookbook/examples/orchestrating_agents) oku. Swarm'ın dört primitive'den hangisini en ergonomik yaptığını ve hangisini arayana ittiğini belirle.
5. Bu tabloda paylaşılan state'i tamamen gizleyen bir framework bul. Agent'ların geçmişi yeniden okumadan handoff'lar arasında koordine olması gerektiğinde ne kırılıyor açıkla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Agent | "Tool'lu LLM" | Bir `(system_prompt, tools, model)` üçlüsü. Stateless. |
| Handoff | "Kontrol transferi" | Sıradaki agent'ı ve opsiyonel payload'ı isimlendiren yapılandırılmış çağrı. Üç implementasyon: fonksiyon return, graf kenarı, speaker selection. |
| Paylaşılan state | "Bellek" / "context" | Çoklu-agent sisteminin tek stateful kısmı. Message pool ya da blackboard. |
| Orchestrator | "Koordinatör" | Sıradakinin kim çalışacağına karar veren. Statik graf, LLM selector, handoff-driven ya da queue-driven. |
| Primitive | "Soyutlama" | Her framework'ün parametrize ettiği dört eksenden biri. Framework özelliği değil. |
| Message pool | "Paylaşılan sohbet geçmişi" | Tam-geçmiş paylaşılan state. Akıl yürütmesi kolay, kötü ölçeklenir. |
| Projected state | "Kapsamlı görünüm" | Paylaşılan state'e rol-özgü görünüm. Ölçeklenir, şema tasarımı gerektirir. |
| Speaker selection | "Sıradaki kim konuşacak" | Bir fonksiyonun (genellikle LLM) bir gruptan sıradaki agent'ı seçtiği orchestrator deseni. |

## İleri Okuma

- [OpenAI cookbook: Orchestrating Agents — Routines and Handoffs](https://developers.openai.com/cookbook/examples/orchestrating_agents) — handoff-driven orkestrasyonun en net ifadesi
- [AutoGen stable docs](https://microsoft.github.io/autogen/stable/) — GroupChat + speaker selection, LLM-seçili orkestrasyon referansıdır
- [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) — graf-kenar orkestrasyonu ve reducer tabanlı paylaşılan state
- [CrewAI introduction](https://docs.crewai.com/en/introduction) — role-goal-backstory agent'ları, Sequential / Hierarchical süreçler
- [AG2 (topluluk AutoGen devamı)](https://github.com/ag2ai/ag2) — Microsoft v0.4'ü bakıma aldıktan sonra canlı AutoGen v0.2 hattı
