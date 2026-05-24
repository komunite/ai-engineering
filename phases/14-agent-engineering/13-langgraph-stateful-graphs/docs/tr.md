# LangGraph: Durumlu Graph'lar ve Dayanıklı Yürütme

> LangGraph düşük seviye durumlu orkestrasyon için 2026 referansı. Agent bir state machine; node'lar fonksiyonlar; edge'ler geçişler; state immutable ve her adımdan sonra checkpoint'lenir. Herhangi bir başarısızlıktan tam olarak kaldığı yerden devam et.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 12 (Workflow Desenleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- LangGraph'ın çekirdek modelini açıkla: immutable state'li, fonksiyon node'lu, koşullu edge'li ve adım-sonrası checkpoint'li state machine.
- Dokümanların vurguladığı dört yeteneği adlandır: dayanıklı yürütme, streaming, human-in-the-loop, kapsamlı bellek.
- LangGraph'ın desteklediği üç orkestrasyon topolojisini açıkla: supervisor, peer-to-peer (swarm), hiyerarşik (yuvalanmış alt-graph'lar).
- Immutable state, koşullu edge'ler ve checkpoint/resume döngülü bir stdlib state graph uygula.

## Sorun

Agent'lar ve workflow'lar bir sorunu paylaşır: 40 adımlık bir koşu adım 38'de başarısız olduğunda, baştan değil adım 38'den devam etmek istersin. İkinci-sınıf state modelleri operatörleri taze koşular varsayan bir kütüphane etrafında retry hack'lemeye bırakır.

LangGraph'ın tasarım yanıtı: state birinci-sınıf tipli bir obje, mutasyonlar açık ve checkpoint'ler her node'dan sonra persist eder. Resume bir `load_state(session_id)` çağrısı.

## Kavram

### Graph

Bir graph şununla tanımlanır:

- **State type.** Her node'un okuduğu ve mutate ettiği tipli bir dict (ya da Pydantic modeli).
- **Node'lar.** Saf fonksiyonlar `(state) -> state_update`. Güncellemeler return'den sonra state'e merge edilir.
- **Edge'ler.** Node'lar arası koşullu ya da doğrudan geçişler.
- **Giriş ve çıkış.** `START` ve `END` sentinel node'lar sınırı işaretler.

Örnek: `classify`, `refund`, `bug`, `sales`, `done` node'lu bir agent — graph olarak bir routing workflow'u.

### Dayanıklı yürütme

Her node return ettikten sonra, runtime state'i serialize eder ve bir checkpointer'a (SQLite, Postgres, Redis, custom) yazar. N adımındaki başarısızlıkta, runtime `resume(session_id)` çağırabilir ve tam state ile N+1 adımından devam edebilir.

LangGraph dokümanları bunun önemli olduğu üretim kullanıcılarını açıkça vurgular: Klarna, Uber, J.P. Morgan. İddia graph şekli değil; graph şekli artı checkpointing kurtarmayı ucuz yapması.

### Streaming

Her node kısmi çıktı yield edebilir. Graph per-node-delta event'lerini çağırana stream eder, böylece UI'lar graph çalışırken güncellenir.

### Human-in-the-loop

Node'lar arasında state'i incele ve değiştir. Uygulamalar: kritik bir node'dan önce duraklat, state'i bir insana yüzeye çıkar, değişiklikleri kabul et, devam et. Checkpointer bunu kolaylaştırıyor çünkü state zaten serialize.

### Bellek

Kısa vadeli (bir koşu içinde — state'te konuşma geçmişi) ve uzun vadeli (koşular arası — checkpointer artı ayrı bir uzun vadeli store üzerinden kalıcı). LangGraph dış bellek sistemleriyle (Mem0, custom) tool'lar üzerinden entegre.

### Üç topoloji

1. **Supervisor.** Merkezi router LLM uzman alt-agent'lara dispatch eder. `langgraph-supervisor`'da `create_supervisor()` (gerçi 2026'da LangChain ekibi daha fazla context kontrolü için bunu doğrudan tool çağrılarıyla yapmayı öneriyor).
2. **Swarm / peer-to-peer.** Agent'lar paylaşılan bir tool yüzeyi üzerinden doğrudan handoff yapar. Merkezi router yok.
3. **Hiyerarşik.** Alt-supervisor'ları yöneten supervisor'lar, yuvalanmış alt-graph'lar olarak uygulanır.

### Bu desen nerede ters gider

- **Çok küçük checkpoint'ler.** Yalnızca konuşma turlarını checkpoint'lemek tool state'i ve bellek yazılarını kurtarılamaz bırakır. Tam state serialize olmalı.
- **Non-deterministik node'lar.** Resume node girdilerinin aynı state güncellemesi ürettiğini varsayar. Random seed'ler, wall-clock, dış API'lar yakalanmalı.
- **Koşullu edge'lerin aşırı kullanımı.** Her edge'i koşullu olan bir graph akıl yürütülemez bir state machine. Ara sıra dallı doğrusal zincirleri tercih et.

## İnşa Et

`code/main.py` bir stdlib durumlu graph uyguluyor:

- `State` — `messages`, `step`, `route`, `output`, `human_approval`'lı tipli bir dict.
- `Node` — state alan ve bir update dict döndüren callable.
- `StateGraph` — node'lar + edge'ler + koşullu edge'ler + run + resume.
- `SQLiteCheckpointer` (in-memory sahte) — her node'dan sonra state'i serialize eder; `load(session_id)` restore eder.
- Bir demo graph: classify -> branch(refund / bug / sales) -> human gate -> send.

Çalıştır:

```
python3 code/main.py
```

Trace ilk koşunun human gate'te başarısız olduğunu, kalıcılığı, sonra resume'un nihai çıktıyı ürettiğini gösterir.

## Kullan

- **LangGraph** — referans, üretim-hazır. `create_react_agent`, `create_supervisor` kullan ya da kendi graph'ını kur.
- **AutoGen v0.4** (Ders 14) — yüksek-eşzamanlı senaryolar için actor model alternatifi.
- **Claude Agent SDK** (Ders 17) — built-in session store ile yönetilen harness.
- **Custom** — state şekli ya da checkpointer backend üzerinde tam kontrole ihtiyacın olduğunda.

## Yayınla

`outputs/skill-state-graph.md` herhangi bir hedef runtime'da checkpointing ve resume kablolanmış LangGraph-şekilli bir state graph üretir.

## Alıştırmalar

1. Classification güveni bir eşiğin altındayken `classify`'dan `end`'e koşullu bir edge ekle. Bir insan manuel olarak `route` belirledikten sonra koşuyu devam ettir.
2. SQLite-benzeri sahteyi gerçek bir SQLite checkpointer ile değiştir. Adım başına serialization yükünü ölç.
3. Paralel edge'ler uygula: iki node eşzamanlı çalışır, custom bir reducer ile merge edilir. Immutable state burada ne kazandırır?
4. `langgraph-supervisor` referansını oku. Oyuncağı `create_supervisor`'a port et. Trace şekillerini karşılaştır.
5. Streaming ekle: her node çalışırken kısmi state yield eder. Delta'ları geldikçe yazdır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| State graph | "State machine olarak agent" | Tipli state + node'lar + edge'ler + reducer'lar |
| Checkpointer | "Kalıcılık backend'i" | Her node'dan sonra state'i serialize eder; resume'u mümkün kılar |
| Reducer | "State merger" | Mevcut state'i bir node'un güncellemesiyle birleştiren fonksiyon |
| Koşullu edge | "Dal" | State'in bir fonksiyonu ile seçilen edge |
| Subgraph | "Yuvalanmış graph" | Başka bir graph'ın içinde node olarak kullanılan bir graph |
| Dayanıklı yürütme | "Başarısızlıktan devam" | Tam state ile son başarılı node'da yeniden başla |
| Supervisor | "Router LLM" | Uzman alt-agent'lar için merkezi dispatcher |
| Swarm | "P2P agent'lar" | Agent'lar paylaşılan tool'lar üzerinden handoff yapar; merkezi router yok |

## İleri Okuma

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — referans dokümanlar
- [langgraph-supervisor reference](https://reference.langchain.com/python/langgraph/supervisor/) — supervisor pattern API
- [AutoGen v0.4, Microsoft Research](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — actor-model alternatifi
- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — session store ve alt-agent'lar
