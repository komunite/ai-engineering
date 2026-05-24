# CrewAI: Rol-Tabanlı Crew'lar ve Flow'lar

> CrewAI 2026 rol-tabanlı çoklu-agent framework'ü. Dört primitif: Agent, Task, Crew, Process. İki üst-seviye şekil: Crew'lar (otonom, rol-tabanlı işbirliği) ve Flow'lar (event-driven, deterministik). Dokümanlar açık: "üretime-hazır herhangi bir uygulama için, bir Flow ile başla."

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 12 (Workflow Desenleri), Faz 14 · 14 (Actor Model)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- CrewAI'nin dört primitifini (Agent, Task, Crew, Process) ve her birinin neyi sahiplendiğini adlandır.
- Sequential, Hierarchical ve Consensual process'leri ayır; workload başına birini seç.
- Crew'ları (otonom rol-tabanlı) Flow'lardan (event-driven deterministik) ayır ve dokümanların üretim önerisini açıkla.
- Tool'ları `@tool` decorator ve `BaseTool` subclass ile kablola; yapılandırılmış çıktılar vs free text üzerine akıl yürüt.
- Dört CrewAI bellek tipini ve her birinin ne zaman karşılığını verdiğini adlandır.
- Bir brief üreten stdlib üç-agent crew (researcher, writer, editor) uygula.
- Üç CrewAI başarısızlık modunu tespit et: prompt-bloat, manager-LLM tax, kırılgan handoff'lar.

## Sorun

Multi-agent framework benimseyen ekipler aynı duvara çarpar. "Otonom işbirliği" demoda kulağa harika geliyor. Sonra bir müşteri bug raporlar ve deterministik replay'e ihtiyacın olur. Ya da finans LLM-routed bir crew'un koşu başına ne kadara mal olduğunu sorar. Ya da on-call sabah 3'te hangi agent'ın takıldığını bilmek ister.

Free-form LLM-routed crew'lar bunların hiçbirini temiz yanıtlamaz. Saf DAG'lar hepsini yanıtlar ama bir brainstorming agent'ının ihtiyaç duyduğu keşifsel şekli kaybeder.

CrewAI'nin ayrımı takas hakkında dürüst. İşbirlikçi, rol-tabanlı, keşifsel iş için Crew'lar. Event-driven, kod-sahipli, denetlenebilir üretim için Flow'lar. Aynı framework, iki şekil, yüzey başına seç.

## Kavram

### Dört primitif

CrewAI'nin yüzeyi küçük. Bunu ezberle, gerisi config.

- **Agent.** `role + goal + backstory + tools + (opsiyonel) llm`. Backstory taşıyıcı. Ton, yargı, agent'ın ne zaman duracağını şekillendirir. Tool'lar agent'ın çağırabileceği fonksiyonlar (aşağıda daha fazla).
- **Task.** `description + expected_output + agent + (opsiyonel) context + (opsiyonel) output_pydantic`. Yeniden kullanılabilir iş birimi. `expected_output` kontrat. `context` çıktıları geçilen upstream task'ları listeler. `output_pydantic` yapılandırılmış bir şekli zorlar.
- **Crew.** Konteyner. `agents` listesini, `tasks` listesini, `process`'i ve opsiyonel `memory` + `verbose` + `manager_llm` ayarlarını sahiplenir.
- **Process.** Yürütme stratejisi. Sequential, Hierarchical, Consensual. Koşunun şeklini seçer.

Agent'lar birbirini doğrudan görmez. Task'lar agent'lara referans verir. Crew task'ları sıralar. Process kimin sonraki task'ı seçeceğine karar verir. Tüm zihinsel model bu.

### Sequential vs Hierarchical vs Consensual

- **Sequential.** Task'lar deklarasyon sırasında çalışır. Task N'in çıktısı task N+1'e `context` olarak mevcut. En düşük maliyet. En tahmin edilebilir. Sıra sabit olduğunda kullan.
- **Hierarchical.** Bir manager Agent (ayrı LLM çağrısı) uzmanlar arasında route eder. CrewAI manager'ı ya senin `manager_llm` config'inden ya da default'tan spawn eder. Manager her turda sonraki task'ı seçer ve reddedebilir ya da yeniden route edebilir. Dört ya da daha fazla uzmanın olduğunda ve sıra gerçekten önceki çıktıya bağlı olduğunda kullan.
- **Consensual.** Beta. Agent'lar sonraki adıma oy verir. Araştırma dışında round trip'lere nadiren değer.

Hierarchical her uzman çağrısının üstüne her turda bir LLM çağrısı (manager) ekler. Beş-adımlık bir koşuda token maliyeti üçe katlanabilir. Yalnızca routing gerektiğinde öde.

### Crew'lar vs Flow'lar

2026'da dokümanların öne çıkardığı çerçeveleme bu.

- **Crew.** LLM-driven otonomi. Framework şekli runtime'da seçer. Şuna iyi: araştırma, brainstorming, ilk taslaklar, yolun yanıtın bir parçası olduğu her yer. Replay zor. Test zor. Prototiplemesi ucuz.
- **Flow.** Sahip olduğun event-driven graph. `@start` girişi işaretler. `@listen(topic)` başka bir adım o topic'i yaydığında tetiklenen bir adım işaretler. Her adım düz Python (içeride bir Crew çağırabilir). Şuna iyi: üretim. Observable. Test edilebilir. Deterministik.

Dokümanların 2026 üretim önerisi: bir Flow ile başla. Otonomi maliyetini hak ettiğinde Crew'ları Flow adımları içinden `Crew.kickoff()` çağrıları olarak katla. Flow audit trail'ini verir, Crew keşfi verir. Compose et, seçme.

### Tool entegrasyonu

Bir Agent'a tool vermenin üç yolu. Uyan en basitini seç.

1. **`@tool` decorator.** Saf fonksiyonlar tool'a dönüşür. Signature şema; docstring LLM'in gördüğü açıklama. Tek seferlik helper'lar için en iyisi.

   ```python
   from crewai.tools import tool

   @tool("Search the web")
   def search(query: str) -> str:
       """Return top results for the query."""
       return run_search(query)
   ```

2. **`BaseTool` subclass.** Açık args şema, async desteği, retry'lı class-tabanlı tool. Tool'un state'i (bir client, bir cache) ya da yapılandırılmış args ihtiyacı olduğunda kullan.

   ```python
   from crewai.tools import BaseTool
   from pydantic import BaseModel

   class SearchArgs(BaseModel):
       query: str
       limit: int = 10

   class SearchTool(BaseTool):
       name = "web_search"
       description = "Search the web and return top results."
       args_schema = SearchArgs

       def _run(self, query: str, limit: int = 10) -> str:
           return self.client.search(query, limit=limit)
   ```

3. **Built-in toolkit'ler.** CrewAI birinci-parti adapter'lar yayar: `SerperDevTool`, `FileReadTool`, `DirectoryReadTool`, `CodeInterpreterTool`, `RagTool`, `WebsiteSearchTool`. Tek import ile kablolanır.

Yapılandırılmış çıktılar Pydantic kullanır. Task'a `output_pydantic=MyModel` geç. CrewAI LLM yanıtını modele karşı doğrular ve ya coerce eder ya da retry eder. Bunu sıkı bir `expected_output` string'i ile eşleştir. Free-text çıktılar taslaklar için iyi; yapılandırılmış çıktılar downstream Flow'ların tüketebileceği şey.

### Bellek hook'ları

CrewAI kutudan dört bellek tipi yayar. Kompoze olurlar: bir Crew dördünü birden etkinleştirebilir.

- **Short-term.** Tek bir koşu içinde konuşma buffer'ı. Sonunda silinir.
- **Long-term.** Koşular arası persist eder. Vector DB'de saklanır (varsayılan Chroma, değiştirilebilir). Mevcut task'a benzerlikle getirilir.
- **Entity.** Entity başına olgular. "Müşteri X enterprise plan'da." Benzerlikle değil entity ile anahtarlanmış. Koşular arası hayatta kalır.
- **Contextual.** Assembly-time retrieval. Agent ihtiyaç duyduğu anda alakalı belleği çeker, preload değil.

Crew'da `memory=True` ya da tip-başına config ile etkinleştir. Yapılandırdığın bir embedding sağlayıcı (varsayılan OpenAI, lokal'e değiştirilebilir) destekler. Bellek CrewAI'nin daha ince framework'lere karşı varlığını kazandığı yerlerden biri; saf LangGraph her birini kendin kablolamanı gerektirir.

### CrewAI ne zaman uyar

- Adlandırılmış roller ve işbirlikçi bir workflow'lu üç ila altı agent. Taslak hazırlama, inceleme, planlama, brainstorming.
- LLM'in sonraki adım yargısının değerin bir parçası olduğu routing (Hierarchical).
- Ekibin graph tanımı yerine `role + goal + backstory` okumaktan daha mutlu olduğu her yer.

### CrewAI ne zaman uymaz

- Katı sıralamalı deterministik DAG'lar. LangGraph (Ders 13) kullan. Graph şekli doğru abstraction; CrewAI'nin rol çerçevelemesi sürtünme.
- Saniye-altı latency bütçeleri. Hierarchical round trip ekler. Sequential bile backstory'leri ve önceki çıktıları içeren prompt'ları serialize eder.
- Single-agent döngüleri. Framework'ü atla; bir agent döngüsü (Ders 1) artı bir tool registry daha kısa.

Ders 17 (Agent Framework Tradeoff'ları) bunu bir matriste açıklar. Kısa versiyon: CrewAI "işbirlikçi rol-tabanlı" köşesinde oturur.

### Bağımlılık şekli

LangChain'den bağımsız. Python 3.10'dan 3.13'e. `uv` kullanır. 2026 başında 30k+ GitHub yıldızı. AWS Bedrock entegrasyonu dokümante; benchmark'ları QA görevlerinde LangGraph'a karşı 5.76x hızlanma cite eder. Framework-vendor sayılarını yönsel olarak ele al.

### Bu desen nerede ters gider

- **Backstory'lerden prompt-bloat.** Agent başına 2000-kelimelik bir backstory ve beş-agent'lık bir crew context bütçesini ilk tool çağrısından önce yakar. Backstory'leri 200 kelimenin altında tut. Agent'lar arasında ifadeleri yeniden kullan; ev stilini beş kere tekrarlama.
- **Manager-LLM token tax.** Hierarchical process her uzman çağrısından önce bir manager LLM çağrısı ekler. Beş-task'lık bir crew'da bu beş yerine altı LLM çağrısı ve manager çağrısı tam task listesini artı önceki çıktıları taşır. Routing çıktıya bağlı değilse Sequential'a geç.
- **Kırılgan handoff'lar.** Task N'in `expected_output`'u "bir outline." Task N+1 onu `context` olarak okur ve üç bölümü parse etmeye çalışır. LLM dört üretti. Downstream Agent ad-lib yapar. Task N+1'in free text değil tipli bir obje okuması için Task N'de `output_pydantic` ile düzelt.
- **Crew-as-prod.** Bir Flow wrapper olmadan free-form Crew üretime yayılmış. Çıktı varyansı yüksek; replay imkansız; on-call kötü bir koşuyu iyiye karşı diff edemez. Bir Flow ile sar.

## İnşa Et

`code/main.py` iki şekli de artı bir üç-agent crew'u stdlib versiyonlarında uyguluyor.

Şekil:

- CrewAI'nin yüzeyiyle eşleşen `Agent`, `Task` dataclass'ları.
- `SequentialCrew.kickoff(inputs)` task'ları deklarasyon sırasında çalıştırır, çıktıları `context` olarak iletir.
- `HierarchicalCrew.kickoff(topic)` her turda sonraki uzmanı seçen bir manager Agent ekler, "done"da durur.
- `@start` ve `@listen(topic)` decorator'lı `Flow`, minik bir event loop ve bir trace.
- CrewAI'nin `@tool` şeklini yansıtan `tool(name)` decorator.
- `short_term`, `long_term`, `entity` store'lu `Memory`; mock benzerlik numpy kullanır.
- Mock LLM yanıtları rol artı input prefix'i ile anahtarlanmış hardcoded string'ler. Ağ yok. Deterministik.

Somut demo: "agent engineering 2026" üzerine brief üreten researcher, writer, editor crew. Researcher (mock'lanmış) kaynakları çeker. Writer taslak hazırlar. Editor sıkılaştırır. Aynı crew deterministik şekli göstermek için Flow boyunca çalışır.

Çalıştır:

```bash
python3 code/main.py
```

Trace şunları kapsar: çıktıları `context` üzerinden ileten sequential crew, manager seçimli hierarchical crew (researcher, writer, editor, sonra "done"), aynı üç adımı açık topic'lerle (`researched`, `drafted`, `edited`) çalıştıran flow, `@tool` üzerinden yönlendirilen tool çağrıları ve iki kickoff arasında hayatta kalan long-term memory.

Crew trace'i akıcı; manager prensipte yeniden sıralayabilir. Flow trace'i sabit. Ders bu seçim.

## Kullan

- **CrewAI Flow** üretim için. Flow `Crew.kickoff()` çağıran tek bir adım olsa bile. Flow audit sınırını verir.
- **CrewAI Crew (Sequential)** net-sıralamalı işbirlikçi iş için, özellikle ilk taslaklar ve inceleme döngüleri.
- **CrewAI Crew (Hierarchical)** routing çıktıya bağlı olduğunda ve dört ya da daha fazla uzmanın olduğunda.
- **LangGraph** (Ders 13) açık state machine'ler, dayanıklı resume, katı sıralama için.
- **AutoGen v0.4** (Ders 14) actor-model concurrency ve fault isolation için.
- **OpenAI Agents SDK** (Ders 16) handoff'lar ve guardrail'lerle OpenAI-first ürünler için.
- **Claude Agent SDK** (Ders 17) alt-agent'lar ve session store ile Claude-first ürünler için.

## Yayınla

`outputs/skill-crew-or-flow.md` bir görev için Crew vs Flow seçer ve minimal uygulamayı iskeler. Backstory'siz-Crew, explicit-topic-siz-Flow, üç-altı uzmanlı Hierarchical'da sert reject eder.

## Tuzaklar

- **Lezzet olarak backstory.** Çıktıları şekillendirir. Agent başına üç varyantı test et; varyans gerçek. Birini seç, dondur.
- **`expected_output`'u atlama.** Task başına kontrat olmadan, downstream task'lar LLM'in ürettiği her şeyi alır. Crew çalışır; audit başarısız olur.
- **Memory always-on.** Long-term her koşuda yazar. Vector DB büyür. Retrieval gürültülü olur. Yazıları olgunun kalıcı olduğu task'lara scope'la.
- **Manager prompt drift'i.** Hierarchical'in manager prompt'u zımni. Routing tuhaflaşırsa, verbose mode'da dump et ve oku.
- **Crew'larda tool yan etkileri.** Bir Crew bir tool'u beklenenden fazla çağırabilir. POST, DELETE, payment Flow adımına aittir, Crew tool'una asla.

## Alıştırmalar

1. Sequential crew'u Flow'a dönüştür. Varyansın düştüğü dokunuş noktalarını say. Okunabilirliğin düştüğü yere not düş.
2. Crew'a entity memory ekle: bir müşteri hakkında olgular kickoff'lar arası persist eder. Retrieval'ın doğru entity'yi çektiğini doğrula.
3. Manager'ın writer'ın çıktısı en az üç paragraf olana kadar editor'a route etmeyi reddettiği bir Hierarchical process uygula. Retry'ı trace et.
4. (Mock'lanmış) bir web search için bir `BaseTool` subclass kablola. Trace şeklini `@tool` decorator versiyonuna karşı karşılaştır.
5. Editor task'ına `output_pydantic=Brief` ekle, burada `Brief`'in `title`, `summary`, `sections`'ı var. Writer task'ının bir kez bozuk JSON çıktısı vermesini sağla; trace'te CrewAI'nin retry davranışını doğrula.
6. CrewAI dokümanlar girişini oku. Oyuncağı gerçek `crewai` API'sine taşı. Stdlib versiyonu hangi garantileri atladı?
7. Gerçek bir koşuya AgentOps ya da Langfuse'u (Ders 24) kablola. Stdlib versiyonunda hangi trace'leri kaçırdın?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Agent | "Persona" | Role + goal + backstory + tools |
| Task | "İş birimi" | Description + expected output + assignee + opsiyonel yapılandırılmış çıktı |
| Crew | "Agent takımı" | Agent'lar + Task'lar + Process konteyneri |
| Process | "Yürütme stratejisi" | Sequential / Hierarchical / Consensual |
| Flow | "Deterministik workflow" | Event-driven, kod-sahipli, test edilebilir |
| Backstory | "Persona prompt'u" | Agent için ton ve yargı şekillendirici |
| `@tool` | "Function tool" | Bir fonksiyonu Agent'ın çağırabileceği bir tool'a dönüştüren decorator |
| `BaseTool` | "Class tool" | Args şema, retry, async desteği ile class-tabanlı tool |
| Entity memory | "Entity başına olgular" | Bir müşteri / hesap / issue'ya scope'lanmış bellek |
| Long-term memory | "Cross-run memory" | Kickoff'lar arası hayatta kalan vector-destekli bellek |
| Contextual memory | "Just-in-time retrieval" | Agent ihtiyaç duyduğu anda çekilen bellek |
| Manager LLM | "Router agent" | Hierarchical process'te sonraki task'ı seçen ekstra LLM |
| `expected_output` | "Task kontratı" | Agent'a (ve audit'e) hangi şekli döndüreceğini söyleyen string |

## İleri Okuma

- [CrewAI docs introduction](https://docs.crewai.com/en/introduction): kavramlar ve önerilen üretim yolu
- [CrewAI Flows guide](https://docs.crewai.com/en/concepts/flows): event-driven şekil, `@start`, `@listen`
- [CrewAI tools reference](https://docs.crewai.com/en/concepts/tools): `@tool`, `BaseTool`, built-in toolkit'ler
- [CrewAI memory](https://docs.crewai.com/en/concepts/memory): short-term, long-term, entity, contextual
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents): multi-agent ne zaman yardım eder ne zaman etmez
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview): state-machine alternatifi
