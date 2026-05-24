# LangGraph — Agent'lar için State Machine'ler

> Elle yazılmış bir ReAct döngüsü bir `while True`'dur. LangGraph'ta yazılmış bir ReAct döngüsü, checkpoint'leyebileceğin, interrupt edebileceğin, dallandırabileceğin ve içinde time-travel yapabileceğin bir graph'tır. Agent değişmedi. Etrafındaki harness değişti.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 11 · 09 (Function Calling), Faz 11 · 14 (Model Context Protocol)
**Süre:** ~75 dakika

## Sorun

Bir function-calling agent yayınlıyorsun. Üç tur çalışıyor, sonra bir şey ters gidiyor: model 500 dönen bir tool deniyor, kullanıcı görev ortasında fikrini değiştiriyor ya da agent insan onayı olmadan bir sipariş iadesi yapmaya karar veriyor. `while True:` döngüsünün hiçbir hook'u yok. Onu duraklatamazsın, geri saramazsın ve "model diğer tool'u seçseydi ne olurdu" diye dallandıramazsın. Bunu demo'nun ötesine yayınladığın an, agent ya çalışan ya çalışmayan bir kara kutu olur.

Sonraki adım, gördüğün an açık. Agent zaten bir state machine — system prompt artı mesaj geçmişi artı bekleyen tool çağrıları artı sonraki aksiyon. State machine'i açık hale getir: "model düşünür," "bir tool çalışır," "bir insan onaylar" için node'lar ve aralarındaki koşullu geçişler için edge'ler. Graph açık olunca, harness dört şeyi bedava kazanır: checkpointing (adımlar arası state'i kaydet), interrupt'lar (bir insan için duraklat), streaming (token'ları ve ara olayları stream'le) ve time-travel (önceki bir state'e geri sar ve farklı bir dal dene).

LangGraph bu abstraction'ı yayınlayan kütüphane. LangChain anlamında bir agent framework'ü değil ("işte bir AgentExecutor, iyi şanslar"). Birinci-sınıf state'e, birinci-sınıf persistence'a ve birinci-sınıf interrupt'lara sahip bir graph runtime'ı. Agent döngüsü çizdiğin bir şeydir, elle yazdığın değil.

## Kavram

![LangGraph StateGraph: node'lar, edge'ler ve checkpointer](../assets/langgraph-stategraph.svg)

Bir `StateGraph`'ın üç şeyi vardır.

1. **State.** Graph boyunca akan tipli bir dict (TypedDict ya da Pydantic model). Her node tam state'i alır ve kısmi bir güncelleme döndürür; LangGraph bunu alan başına bir *reducer* kullanarak merge eder — birikmesi gereken listeler için `operator.add`, varsayılan olarak üzerine yaz.
2. **Node'lar.** Python fonksiyonları `state -> partial_state`. Her biri ayrı bir adımdır: "modeli çağır," "tool'ları çalıştır," "özetle."
3. **Edge'ler.** Node'lar arası geçişler. Statik edge'ler bir yere gider. Koşullu edge'ler bir router fonksiyonu `state -> next_node_name` alır, böylece graph model çıktısına göre dallanabilir.

Graph'ı derlersin. Derleme topolojiyi bağlar, bir checkpointer'ı bağlar (opsiyonel ama üretim için zorunlu) ve bir runnable döndürür. Onu bir initial state ve bir `thread_id` ile çağırırsın. Yürütmenin her adımı `(thread_id, checkpoint_id)` üzerinden anahtarlanan bir checkpoint'i kalıcı yapar.

### Dört süper güç

**Checkpointing.** Her node geçişi yeni state'i bir store'a yazar (testler için in-memory, üretim için Postgres/Redis/SQLite). Aynı `thread_id` ile graph'ı tekrar çağırarak resume et. Graph duraksadığı yerden devam eder.

**Interrupt'lar.** Bir node'u `interrupt_before=["human_review"]` ile işaretle; yürütme o node çalışmadan önce durur. State kalıcı kalır. API'n kullanıcıya "onay bekliyor" diye yanıt verir. Aynı `thread_id`'ye `Command(resume=...)` ile gelen sonraki bir istek yürütmeyi devam ettirir.

**Streaming.** `graph.stream(state, mode="updates")` state delta'larını oldukça yield eder. `mode="messages"` model node'larının içindeki LLM token'larını stream'ler. `mode="values"` tam snapshot'lar yield eder. UI'nda neyi göstereceğini seçersin.

**Time-travel.** `graph.get_state_history(thread_id)` tam checkpoint log'unu döndürür. Herhangi bir önceki `checkpoint_id`'yi `graph.invoke`'a geçirirsin ve o noktadan fork edersin. Debug için harika ("model B tool'unu seçseydi ne olurdu?") ve üretim trace'lerini tekrar oynatan regresyon testleri için.

### Reducer'lar mesele

Her state alanının bir reducer'ı vardır. Çoğu varsayılan iyi — yeni bir değer eskinin üzerine yazar. Ama mesaj listeleri `operator.add`'a ihtiyaç duyar, böylece yeni mesajlar replace etmek yerine append olur. Paralel edge'ler güncellemelerini reducer üzerinden merge eder. İki node aynı `messages`'ı güncellerse ve `Annotated[list, add_messages]`'ı unuttuysan, ikincisi sessizce kazanır ve turun yarısını kaybedersin. Reducer kütüphanedeki tek incelikli şey; doğru yap ve geri kalanı compose olur.

### Dört node'da ReAct graph'ı

Üretim ReAct agent'ı dört node ve iki edge'dir:

1. `agent` — mevcut mesaj geçmişiyle LLM'i çağırır. Assistant mesajını döndürür (tool_call'lar içerebilir).
2. `tools` — son assistant mesajındaki tool_call'ları yürütür, tool sonuçlarını tool mesajları olarak append eder.
3. `agent`'tan koşullu bir edge, son mesajda tool_call varsa `tools`'a, yoksa `END`'e yönlendirir.
4. `tools`'tan `agent`'a geri statik bir edge.

Hepsi bu. Tam ReAct döngüsünü (Düşünce → Aksiyon → Gözlem → Düşünce → …) checkpointing, interrupt'lar ve streaming ile, yaklaşık 40 satır kodda elde edersin.

### StateGraph vs Send (fanout)

`Send(node_name, state)` bir node'un paralel alt-graph'lar dispatch etmesine olanak verir. Örnek: agent aynı anda üç retriever'ı sorgulamaya karar verir. Her `Send` hedef node'un paralel bir yürütmesini doğurur; çıktıları state reducer üzerinden merge olur. LangGraph orchestrator-workers desenini threading primitive'leri olmadan böyle ifade eder.

### Alt-graph'lar

Derlenmiş bir graph başka bir graph'ta node olabilir. Dış graph tek bir node görür; iç graph'ın kendi state'i ve kendi checkpoint'leri vardır. Takımlar supervisor-worker agent'larını böyle inşa eder: supervisor graph'ı kullanıcı niyetini alan başına bir worker alt-graph'ına yönlendirir.

## İnşa Et

### Adım 1: state ve node'lar

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def agent_node(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: State) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

tool_node = ToolNode(tools=[search_web, read_file])

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=MemorySaver())
```

`add_messages`, mesaj listesinin üzerine yazmak yerine birikmesini sağlayan reducer'dır. Onu unutmak en yaygın LangGraph bug'ı.

### Adım 2: thread ile çalıştır

```python
config = {"configurable": {"thread_id": "user-42"}}
for event in app.stream(
    {"messages": [HumanMessage("find the Anthropic headquarters address")]},
    config,
    stream_mode="updates",
):
    print(event)
```

Her güncelleme bir `{node_name: state_delta}` dict'idir. Frontend'in bunları UI'a stream'leyebilir, böylece kullanıcılar "agent düşünüyor… search_web çağrılıyor… sonuç alındı… yanıtlanıyor" görürler.

### Adım 3: bir human-in-the-loop interrupt ekle

Bir node'u öyle işaretle ki yürütme çalışmadan önce duraklasın.

```python
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"],  # her tool çağrısından önce duraklat
)

state = app.invoke({"messages": [HumanMessage("delete the production database")]}, config)
# state["__interrupt__"] ayarlandı. Önerilen tool çağrılarını incele.
# Onaylanırsa:
from langgraph.types import Command
app.invoke(Command(resume=True), config)
# Reddedilirse: bir reddetme mesajı yaz ve devam et
app.update_state(config, {"messages": [AIMessage("Blocked by human reviewer.")]})
```

State, checkpoint ve thread interrupt boyunca kalıcı kalır. Yürütme süresi dışında bellekte hiçbir şey yok.

### Adım 4: debug için time-travel

```python
history = list(app.get_state_history(config))
for snapshot in history:
    print(snapshot.values["messages"][-1].content[:80], snapshot.config)

# Önceki bir checkpoint'ten fork et
target = history[3].config  # üç adım geri
for event in app.stream(None, target, stream_mode="values"):
    pass  # o noktadan ileri tekrar oynat
```

Input olarak `None` geçmek verilen checkpoint'ten tekrar oynar; bir değer geçmek, devam etmeden önce o checkpoint'in state'ine update olarak append eder. Tüm konuşmayı yeniden çalıştırmadan kötü bir agent çalışmasını böyle yeniden üretirsin.

### Adım 5: üretim için checkpointer'ı takas et

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string("postgresql://...") as checkpointer:
    checkpointer.setup()
    app = graph.compile(checkpointer=checkpointer)
```

SQLite, Redis ve Postgres yayınlandı. `MemorySaver` testler için. Restart'lar arasında kalıcı olan herhangi bir şey gerçek bir store ister.

## Beceri

> Agent'ları `while True` döngüsü olarak değil graph olarak inşa edersin.

LangGraph'a uzanmadan önce 60 saniyelik bir tasarım yap:

1. **Node'ları isimlendir.** Her ayrı karar ya da side-effecting aksiyon bir node'dur. "Agent düşünür," "tool çalışır," "reviewer onaylar," "yanıt stream'lenir." Onları sıralayamıyorsan, görev henüz agent-şekilli değil.
2. **State'i deklare et.** Her liste alanı için bir reducer'a sahip minimal TypedDict. Her şeyi `messages`'a tıkıştırma; task'a özel alanları (bir çalışan `plan`, bir `budget` sayacı, bir `retrieved_docs` listesi) en üst seviyeye çıkar.
3. **Edge'leri çiz.** Sonraki adım model çıktısına bağlı değilse statik. Her koşullu edge adlandırılmış dallara sahip bir router fonksiyonuna ihtiyaç duyar.
4. **Önceden bir checkpointer seç.** Testler için `MemorySaver`, başka her şey için Postgres/Redis/SQLite. Onsuz yayınlama — checkpointer yok demek resume yok, interrupt yok, time-travel yok demek.
5. **Interrupt'lara tool'lar çalışmadan önce karar ver, sonra değil.** Onaylar side-effecting node'a giden edge'e gider, böylece zarardan önce iptal edebilirsin; doğrulama modelden çıkan edge'e gider, böylece kötü çağrıları ucuza reddedebilirsin.
6. **Varsayılan olarak stream'le.** UI için `mode="updates"`, model node'larının içinde token-seviyesi streaming için `mode="messages"`, eval sırasında tam snapshot'lar için `mode="values"`.

Checkpointer'ı olmayan bir LangGraph agent'ı yayınlamayı reddet. Yan etkiden *sonra* interrupt yapanı yayınlamayı reddet. `add_messages`'ı reducer'ı olarak olmayan bir `messages` alanını yayınlamayı reddet.

## Alıştırmalar

1. **Kolay.** Yukarıdaki dört-node ReAct graph'ını bir hesap makinesi tool'u ve bir web-search tool'u ile uygula. İki-turlu bir konuşma için `list(app.get_state_history(config))`'in en az dört checkpoint döndürdüğünü doğrula.
2. **Orta.** `agent`'tan önce çalışan ve state'e yapılandırılmış bir `plan: list[str]` yazan bir `planner` node'u ekle. `agent`'ın plan adımlarını yapıldı olarak işaretlemesini sağla. `plan` bir checkpoint resume boyunca kaybolursa (yanlış reducer) testi başarısız kıl.
3. **Zor.** Üç alt-graph (`researcher`, `writer`, `reviewer`) arasında `Send` kullanarak yönlendiren bir supervisor graph'ı inşa et. Her alt-graph'ın kendi state'i ve checkpointer'ı var. Dış graph üzerine bir `interrupt_before=["writer"]` ekle, böylece bir insan araştırma özetini onaylayabilsin. Önceki bir checkpoint'ten time-travel'ın yalnızca fork edilmiş dalı yeniden çalıştırdığını doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| StateGraph | "LangGraph graph'ı" | Compile'dan önce node ve edge eklediğin builder nesnesi. |
| Reducer | "Alanın nasıl merge olduğu" | Bir node o alan için update döndürdüğünde uygulanan `(old, new) -> merged` fonksiyonu; varsayılan üzerine yaz, `add_messages` append eder. |
| Thread | "Bir konuşma ID'si" | Bir session için tüm checkpoint'leri scope'layan bir `thread_id` string'i. |
| Checkpoint | "Duraklatılmış bir state" | Bir node geçişi sonrası tam graph state'inin `(thread_id, checkpoint_id)` üzerinden anahtarlanan kalıcı snapshot'ı. |
| Interrupt | "Bir insan için duraklat" | `interrupt_before` / `interrupt_after` bir node sınırında yürütmeyi durdurur; `Command(resume=...)` ile devam et. |
| Time-travel | "Önceki bir adımdan fork" | `graph.invoke(None, config_with_old_checkpoint_id)` o checkpoint'ten ileri tekrar oynar. |
| Send | "Paralel alt-graph dispatch" | Bir node'un hedef node'un N paralel yürütmesini doğurmak için döndürebileceği bir constructor. |
| Subgraph | "Node olarak derlenmiş graph" | Başka bir graph'ta node olarak kullanılan derlenmiş StateGraph; kendi state scope'unu korur. |

## İleri Okuma

- [LangGraph dokümantasyonu](https://langchain-ai.github.io/langgraph/) — StateGraph, reducer'lar, checkpointer'lar ve interrupt'lar için kanonik referans.
- [LangGraph kavramları: state, reducer'lar, checkpointer'lar](https://langchain-ai.github.io/langgraph/concepts/low_level/) — bu dersin kullandığı zihinsel model, doğrudan kaynaktan.
- [LangGraph Persistence ve Checkpoint'ler](https://langchain-ai.github.io/langgraph/concepts/persistence/) — Postgres/SQLite/Redis store'ları, checkpoint namespace'leri ve thread ID'leri üzerine detay.
- [LangGraph Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) — `interrupt_before`, `interrupt_after`, `Command(resume=...)` ve edit-state deseni.
- [Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models" (ICLR 2023)](https://arxiv.org/abs/2210.03629) — her LangGraph agent'ının uyguladığı desen; reasoning trace gerekçesi için oku.
- [Anthropic — Building effective agents (Aralık 2024)](https://www.anthropic.com/research/building-effective-agents) — hangi graph şekillerinin (chain, router, orchestrator-workers, evaluator-optimizer) ne zaman tercih edileceği.
- Faz 11 · 09 (Function Calling) — her LangGraph agent node'unun yeniden kullandığı tool-call primitive'i.
- Faz 11 · 14 (Model Context Protocol) — MCP adapter üzerinden LangGraph `ToolNode`'a takılan dış tool keşfi.
- Faz 11 · 17 (Agent framework tradeoff'ları) — LangGraph'ı CrewAI, AutoGen ya da Agno yerine ne zaman seçmeli.
