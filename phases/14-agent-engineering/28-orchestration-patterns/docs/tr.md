# Orkestrasyon Desenleri: Supervisor, Swarm, Hiyerarşik

> Dört orkestrasyon deseni 2026 framework'leri arasında yineleniyor: supervisor-worker, swarm / peer-to-peer, hiyerarşik, debate. Anthropic rehberi: "İhtiyaçlarına göre doğru sistemi kurmakla ilgili." Basit başla; tek agent artı beş workflow deseni yetersiz olduğunda topoloji ekle.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 12 (Workflow Desenleri), Faz 14 · 25 (Multi-Agent Debate)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Dört yinelenen orkestrasyon desenini ve her birinin ne zaman uyduğunu adlandır.
- 2026 LangChain önerisini açıkla: tool-call-tabanlı supervision vs supervisor kütüphaneleri.
- Anthropic'in "doğru sistemi kur" kuralını ve topoloji seçimini nasıl kapı olarak kullandığını açıkla.
- Dördünü de ortak scripted bir LLM'e karşı stdlib'de uygula.

## Sorun

Ekipler ihtiyaç duymadan önce "multi-agent"a uzanır. Dört desen framework'ler arasında yineleniyor; onları adlandırabildiğinde, doğru olanı seçebilir — ya da topolojiyi tamamen atlayabilirsin.

## Kavram

### Supervisor-worker

- Merkezi bir routing LLM uzman agent'lara dispatch eder.
- Karar verir: kendine geri loop, uzmana handoff, sonlandır.
- Uzmanlar birbiriyle konuşmaz; tüm routing supervisor üzerinden gider.

Framework'ler: LangGraph `create_supervisor`, Anthropic orchestrator-workers, CrewAI Hierarchical Process.

**2026 LangChain önerisi:** supervision'ı `create_supervisor` yerine doğrudan tool çağrıları üzerinden yap. Daha ince context engineering kontrolü verir — her uzmanın tam olarak ne göreceğine sen karar verirsin.

### Swarm / peer-to-peer

- Agent'lar paylaşılan bir tool yüzeyi üzerinden doğrudan handoff yapar.
- Merkezi router yok.
- Supervisor'dan daha düşük latency (daha az hop).
- Akıl yürütmek daha zor (tek kontrol noktası yok).

Framework'ler: LangGraph swarm topolojisi, OpenAI Agents SDK handoff'ları (tüm agent'lar diğer tümüne handoff yapabildiğinde).

### Hiyerarşik

- Worker'ları yöneten alt-supervisor'ları yöneten supervisor'lar.
- LangGraph'ta yuvalanmış alt-graph'lar olarak uygulanır; CrewAI'de yuvalanmış crew'lar.
- Büyük agent popülasyonlarına ölçeklenir, operasyonel karmaşıklık maliyetiyle.

Ne zaman gerekir: tek bir supervisor'ın context bütçesi tüm uzmanların açıklamalarını tutamadığında.

### Debate

- Paralel öneren + iteratif cross-critique (Ders 25).
- Gerçekten orkestrasyon değil — daha çok doğrulama — ama framework'lerde topoloji seçimi olarak görünür.

### CrewAI Crew vs Flow

CrewAI iki deployment modunu formalize eder:

- Deterministik event-driven otomasyon için **Flow** (üretim için önerilen başlangıç noktası).
- Otonom rol-tabanlı işbirliği için **Crew**.

Bu yukarıdaki dört desene ortogonal ama topolojiye eşlenir: Flow tipik olarak supervisor ya da hiyerarşik; Crew tipik olarak LLM router'lı supervisor.

### Anthropic rehberi

"LLM alanında başarı en sofistike sistemi kurmakla ilgili değil. İhtiyaçlarına göre doğru sistemi kurmakla ilgili."

Karar sırası:

1. Single agent + workflow desenleri (Ders 12) — burada başla.
2. Supervisor-worker — 2-4 uzmanın olduğunda.
3. Swarm — latency akıl yürütme netliğinden daha önemli olduğunda.
4. Hiyerarşik — yalnızca supervisor context bütçesi başarısız olduğunda.
5. Debate — doğruluk maliyetten daha önemli olduğunda.

### Bu desen nerede ters gider

- **Topoloji-first düşünme.** Multi-agent'ın hangi problemi çözdüğünü tanımlamadan önce "multi-agent'a ihtiyacımız var."
- **Swarm'da zıplayan handoff'lar.** A -> B -> A -> B. Hop counter'lar kullan.
- **Sahte hiyerarşi.** "Enterprise" diye üç katman; iki gerçek takım. Çök.

## İnşa Et

`code/main.py` dört deseni de scripted bir LLM'e karşı stdlib'de uyguluyor:

- `Supervisor` — merkezi router.
- `Swarm` — doğrudan handoff'lu peer-to-peer.
- `Hierarchical` — supervisor'lerin supervisor'ı.
- `Debate` — paralel öneren + eleştiri.

Her desen aynı üç-niyetli görevi (refund / bug / sales) ele alır. Trace şekilleri farklı.

Çalıştır:

```
python3 code/main.py
```

Çıktı: desen başına trace + op sayısı. Supervisor en temiz; swarm en kısa; hiyerarşik en derin; debate en pahalı.

## Kullan

- **LangGraph** supervisor ve hiyerarşik için (yuvalanmış alt-graph'lar).
- **OpenAI Agents SDK** handoff-as-tool için (supervisor-şekilli).
- **CrewAI Flow** üretim deterministik için.
- **Custom** debate için ya da tam kontrol istediğinde.

## Yayınla

`outputs/skill-orchestration-picker.md` bir topoloji seçer ve onu uygular.

## Alıştırmalar

1. Bir supervisor-worker'ı router'ı kaldırarak swarm'a dönüştür. Ne bozulur? Ne gelişir?
2. Swarm'a bir hop counter ekle: 3 handoff sonrası reddet. A->B->A zıplamasını yakalar mı?
3. 12-uzmanlı bir domain için iki seviyeli hiyerarşik sistem kur. Yuvalamasız context bütçesi nerede başarısız oluyor?
4. Dört deseni üretim-şekilli bir workload'da profille. Hangisi hangi metrikte kazanır (latency, maliyet, doğruluk, debug edilebilirlik)?
5. Anthropic'in "Building Effective Agents" yazısını oku. Üretim akışlarının her birini dörtten birine eşle. Temiz eşlenmeyen var mı?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Supervisor-worker | "Router + uzmanlar" | Merkezi LLM uzmanlara dispatch eder; birbiriyle konuşmazlar |
| Swarm | "Peer-to-peer" | Paylaşılan tool'larla doğrudan handoff'lar; merkezi router yok |
| Hiyerarşik | "Supervisor'ların supervisor'ı" | Büyük popülasyonlar için yuvalanmış alt-graph'lar |
| Debate | "Öneren + eleştiri" | Paralel öneren, cross-critique (Ders 25) |
| Tool-call-tabanlı supervision | "Kütüphanesiz supervisor" | Context kontrolü için supervisor'ı doğrudan tool çağrıları olarak uygula |
| Crew | "Otonom takım" | CrewAI'nin rol-tabanlı işbirliği modu |
| Flow | "Deterministik workflow" | CrewAI'nin event-driven üretim modu |

## İleri Okuma

- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — beş desen + agent vs workflow
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — supervisor, swarm, hiyerarşik
- [CrewAI docs](https://docs.crewai.com/en/introduction) — Crew vs Flow
- [Du et al., Society of Minds (arXiv:2305.14325)](https://arxiv.org/abs/2305.14325) — debate deseni
