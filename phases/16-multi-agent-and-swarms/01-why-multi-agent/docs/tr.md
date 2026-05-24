# Neden Çoklu-Agent?

> Tek agent duvara çarpar. Akıllı hamle daha büyük bir agent değil — daha çok agent.

**Tür:** Öğrenim
**Diller:** TypeScript
**Ön koşullar:** Faz 14 (Agent Engineering)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Tek-agent tavanını tanımla (context taşması, karışık uzmanlık, sıralı dar boğaz) ve birden fazla agent'a bölmenin ne zaman doğru hamle olduğunu açıkla
- Orkestrasyon desenlerini karşılaştır (pipeline, paralel fan-out, supervisor, hiyerarşik) ve belirli bir görev yapısı için doğru olanı seç
- Net rol sınırları, paylaşılan state ve bir iletişim kontratı ile bir çoklu-agent sistemi tasarla
- Çoklu-agent karmaşıklığının (gecikme, maliyet, hata ayıklama zorluğu) tek-agent sadeliğine karşı takaslarını analiz et

## Sorun

Faz 14'te tek agent inşa ettin. Çalışıyor. Dosya okuyabiliyor, komut çalıştırabiliyor, API çağırabiliyor ve sonuçlar üzerine akıl yürütebiliyor. Sonra onu gerçek bir kod tabanına yönlendiriyorsun: 200 dosya, üç dil, altyapıya bağımlı testler ve kod yazmadan önce dış API'leri araştırma gerekliliği.

Agent boğuluyor. LLM aptal olduğu için değil, görev bir agent döngüsünün kaldırabileceğinin ötesinde olduğu için. Context penceresi dosya içerikleriyle doluyor. Agent 40 tool çağrısı önce okuduğunu unutuyor. Aynı anda araştırmacı, kodcu ve gözden geçirici olmaya çalışıyor ve üçünü de kötü yapıyor.

İşte tek-agent tavanı bu. Bir görev şunları gerektirdiğinde her seferinde buna çarparsın:

- **Tek bir pencereye sığandan fazla context** — 50 dosya okumak 200k token'ı aşar
- **Farklı aşamalarda farklı uzmanlık** — araştırma, kod üretiminden farklı prompting gerektirir
- **Paralel yapılabilecek işler** — üç dosyayı sırayla okumak yerine eş zamanlı okuyabilirken neden sırayla?

## Kavram

### Tek-Agent Tavanı

Tek agent bir döngü, bir context penceresi, bir sistem prompt'u. Hayal et:

```
┌─────────────────────────────────────────┐
│            TEK AGENT                    │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │         Context Penceresi         │  │
│  │                                   │  │
│  │  araştırma notları                │  │
│  │  + kod dosyaları                  │  │
│  │  + test çıktısı                   │  │
│  │  + inceleme geri bildirimi        │  │
│  │  + API dokümanları                │  │
│  │  + ...                            │  │
│  │                                   │  │
│  │  ██████████████████████ DOLU ███  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Tek sistem prompt'u araştırma +        │
│  kodlama + inceleme + test'i kapsamaya  │
│  çalışır                                │
│                                         │
│  Sonuç: her şeyde vasat                 │
└─────────────────────────────────────────┘
```

Üç şey kırılır:

1. **Context doygunluğu** — tool sonuçları üst üste yığılır. 30. turda agent dosya içerikleri, komut çıktıları ve önceki akıl yürütmeden 150k token tüketmiştir. 5. turdaki kritik detaylar kaybolur.

2. **Rol karışıklığı** — "araştırmacı, kodcu, gözden geçirici ve testçisin" diyen bir sistem prompt'u yarı-araştıran, yarı-kodlayan ve incelemeyi asla bitirmeyen bir agent üretir.

3. **Sıralı dar boğaz** — agent A dosyasını, sonra B'yi, sonra C'yi okur. Üç sıralı LLM çağrısı. Üç sıralı tool yürütmesi. Paralelizm yok.

### Çoklu-Agent Çözümü

İşi böl. Her agent'a tek bir iş, tek bir context penceresi ve o iş için ayarlanmış tek bir sistem prompt'u ver:

```
┌──────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│                                                          │
│  "Kullanıcı yönetimi için bir REST API inşa et"          │
│                                                          │
│         ┌──────────┬──────────┬──────────┐               │
│         │          │          │          │               │
│         ▼          ▼          ▼          ▼               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│   │ARAŞTIRMA │ │  KODCU   │ │ İNCELEME │ │  TESTÇİ  │  │
│   │          │ │          │ │          │ │          │  │
│   │ Doküman  │ │ Araştır- │ │ Kod      │ │ Test     │  │
│   │ okur,    │ │ ma + spec│ │ kalitesi │ │ çalış-   │  │
│   │ desenler │ │ temelli  │ │ kontrol  │ │ tırır,   │  │
│   │ bulur    │ │ kod yazar│ │ eder,    │ │ sonuç    │  │
│   │          │ │          │ │ bug bulur│ │ raporlar │  │
│   └─────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│         │           │            │             │         │
│         └───────────┴────────────┴─────────────┘         │
│                          │                               │
│                     Sonuçları birleştir                  │
└──────────────────────────────────────────────────────────┘
```

Her agent'ın şunları var:
- Odaklı bir sistem prompt'u ("Kod gözden geçiricisin. Tek işin bug bulmak.")
- Kendi context penceresi (diğer agent'ların işiyle kirlenmemiş)
- Net bir input/output kontratı (araştırma notları alır, kod çıktısı verir)

### Bunu Yapan Gerçek Sistemler

**Claude Code subagent'ları** — Claude Code `Task` ile bir subagent doğurduğunda, kapsamlı bir görevle bir alt agent yaratır. Parent context'ini temiz tutar. Çocuk odaklı iş yapar ve özet döndürür.

**Devin** — bir planlayıcı agent, bir kodcu agent ve bir tarayıcı agent çalıştırır. Planlayıcı işi adımlara böler. Kodcu kod yazar. Tarayıcı dokümantasyon araştırır. Her birinin ayrı context'i vardır.

**Çoklu-agent kodlama takımları (SWE-bench)** — SWE-bench'te en iyi performans gösteren sistemler kod tabanını okuyan bir araştırmacı, düzeltmeyi tasarlayan bir planlayıcı ve uygulayan bir kodcu kullanır. Tek-agent sistemler daha düşük puan alır.

**ChatGPT Deep Research** — paralel olarak birden çok arama agent'ı doğurur, her biri farklı bir açı keşfeder, sonra sonuçları sentezler.

### Spektrum

Çoklu-agent ikili değildir. Bir spektrumdur:

```
BASİT ──────────────────────────────────────────── KARMAŞIK

 Tek           Sub-         Pipeline      Takım        Sürü
 Agent         agent'lar

 ┌───┐       ┌───┐        ┌───┐───┐    ┌───┐───┐    ┌─┐┌─┐┌─┐
 │ A │       │ A │        │ A │ B │    │ A │ B │    │ ││ ││ │
 └───┘       └─┬─┘        └───┘─┬─┘    └─┬─┘─┬─┘    └┬┘└┬┘└┬┘
               │                │        │   │       ┌┴──┴──┴┐
             ┌─┴─┐          ┌───┘───┐    │   │       │paylaş.│
             │ a │          │ C │ D │  ┌─┴───┴─┐    │ state │
             └───┘          └───┘───┘  │  msg   │    └───────┘
                                       │  bus   │
 1 döngü     Parent +      Aşama       │       │    N peer,
 1 context   alt görevler  aşama       └───────┘    yükselen
                                       Açık rol     davranış
```

**Tek agent** — bir döngü, bir prompt. Basit görevler için iyi.

**Subagent'lar** — bir parent, odaklı alt görevler için çocuklar doğurur. Parent planı yönetir. Çocuklar geri rapor verir. Claude Code bunu yapar.

**Pipeline** — agent'lar sırayla çalışır. Agent A'nın çıktısı Agent B'nin girdisi olur. Aşamalı iş akışları için iyi: araştırma -> kod -> inceleme -> test.

**Takım** — agent'lar paylaşılan bir mesaj bus'ı ile paralel çalışır. Her birinin bir rolü vardır. Bir orchestrator koordine eder. Farklı yeteneklerin aynı anda gerekli olduğu durumlarda iyi.

**Sürü** — paylaşılan state ile çok sayıda özdeş veya neredeyse özdeş agent. Sabit orchestrator yok. Agent'lar bir kuyruktan iş alır. Yüksek-throughput paralel görevler için iyi.

### Dört Çoklu-Agent Deseni

#### Desen 1: Pipeline

```
Input ──▶ Agent A ──▶ Agent B ──▶ Agent C ──▶ Output
          (araştır.)   (kod)       (inceleme)
```

Her agent veriyi dönüştürür ve ileri iletir. Akıl yürütmesi kolay. Bir aşamadaki başarısızlık geri kalanı bloklar.

#### Desen 2: Fan-out / Fan-in

```
                ┌──▶ Agent A ──┐
                │              │
Input ──▶ Böl   ├──▶ Agent B ──├──▶ Birleştir ──▶ Output
                │              │
                └──▶ Agent C ──┘
```

İşi paralel agent'lara böl, sonra sonuçları birleştir. Bağımsız alt görevlere ayrılabilen görevler için iyi.

#### Desen 3: Orchestrator-Worker

```
                    ┌──────────┐
                    │  Orch.   │
                    └──┬───┬───┘
                  task │   │ task
                 ┌─────┘   └─────┐
                 ▼               ▼
           ┌──────────┐   ┌──────────┐
           │ Worker A │   │ Worker B │
           └──────────┘   └──────────┘
```

Akıllı bir orchestrator ne yapılacağına karar verir, worker'lara delege eder ve sonuçları sentezler. Orchestrator'ın kendisi de worker doğurmak için tool'lara sahip bir agent'tır.

#### Desen 4: Peer Sürü

```
         ┌───┐ ◄──── msg ────▶ ┌───┐
         │ A │                  │ B │
         └─┬─┘                  └─┬─┘
           │                      │
      msg  │    ┌───────────┐     │ msg
           └───▶│ Paylaşılan│◄────┘
                │  State    │
           ┌───▶│  / Kuyruk │◄────┐
           │    └───────────┘     │
      msg  │                      │ msg
         ┌─┴─┐                  ┌─┴─┐
         │ C │ ◄──── msg ────▶ │ D │
         └───┘                  └───┘
```

Merkezi orchestrator yok. Agent'lar peer-to-peer iletişim kurar. Kararlar etkileşimden çıkar. Hata ayıklaması daha zor ama çok sayıda agent'a ölçeklenir.

### Çoklu-Agent NE ZAMAN Kullanılmamalı

Çoklu-agent karmaşıklık ekler. Agent'lar arasındaki her mesaj potansiyel bir başarısızlık noktasıdır. Hata ayıklama "tek konuşmayı oku"dan "beş agent boyunca mesajları izle"ye geçer.

**Şu durumlarda tek-agent kal:**
- Görev tek context penceresine sığıyorsa (yaklaşık 100k token'ın altında çalışma verisi)
- Farklı aşamalar için farklı sistem prompt'larına ihtiyacın yoksa
- Sıralı yürütme yeterince hızlıysa
- Görev, bölmenin değerinden daha fazla overhead eklediği kadar basit ise

**Karmaşıklık maliyeti:**
- Her agent sınırı kayıplı bir sıkıştırma adımıdır: agent A'nın tam context'i agent B için bir mesaja özetlenir
- Koordinasyon mantığı (kim ne yapacak, ne zaman, hangi sırada) kendi başına bir bug kaynağıdır
- Gecikme artar: N agent en az N sıralı LLM çağrısı demektir, ileri-geri konuşmaları gerekiyorsa daha fazla
- Maliyet çarpar: her agent bağımsız olarak token yakar

Yaklaşık kural: bir görev 20'den az tool çağrısı alıyorsa ve 100k token'a sığıyorsa, tek-agent tut.

## İnşa Et

### Adım 1: Aşırı Yüklenmiş Tek Agent

İşte her şeyi yapmaya çalışan tek bir agent. Tek devasa sistem prompt'u ve araştırma, kod ve incelemeleri tutan tek context penceresi var:

```typescript
type AgentResult = {
  content: string;
  tokensUsed: number;
  toolCalls: number;
};

async function singleAgentApproach(task: string): Promise<AgentResult> {
  const systemPrompt = `You are a full-stack developer. You must:
1. Research the requirements
2. Write the code
3. Review the code for bugs
4. Write tests
Do ALL of these in a single conversation.`;

  const contextWindow: string[] = [];
  let totalTokens = 0;
  let totalToolCalls = 0;

  const research = await fakeLLMCall(systemPrompt, `Research: ${task}`);
  contextWindow.push(research.output);
  totalTokens += research.tokens;
  totalToolCalls += research.calls;

  const code = await fakeLLMCall(
    systemPrompt,
    `Given this research:\n${contextWindow.join("\n")}\n\nNow write code for: ${task}`
  );
  contextWindow.push(code.output);
  totalTokens += code.tokens;
  totalToolCalls += code.calls;

  const review = await fakeLLMCall(
    systemPrompt,
    `Given all previous context:\n${contextWindow.join("\n")}\n\nReview the code.`
  );
  contextWindow.push(review.output);
  totalTokens += review.tokens;
  totalToolCalls += review.calls;

  return {
    content: contextWindow.join("\n---\n"),
    tokensUsed: totalTokens,
    toolCalls: totalToolCalls,
  };
}
```

Bu yaklaşımın sorunları:
- Context penceresi her aşamayla birlikte büyür. İnceleme adımına gelindiğinde araştırma notları VE kod VE önceki akıl yürütme içerir.
- Sistem prompt'u jeneriktir. Her aşama için ayarlanamaz.
- Hiçbir şey paralel çalışmaz.

### Adım 2: Uzman Agent'lar

Şimdi böl. Her agent bir iş alır:

```typescript
type SpecialistAgent = {
  name: string;
  systemPrompt: string;
  run: (input: string) => Promise<AgentResult>;
};

function createSpecialist(name: string, systemPrompt: string): SpecialistAgent {
  return {
    name,
    systemPrompt,
    run: async (input: string) => {
      const result = await fakeLLMCall(systemPrompt, input);
      return {
        content: result.output,
        tokensUsed: result.tokens,
        toolCalls: result.calls,
      };
    },
  };
}

const researcher = createSpecialist(
  "researcher",
  "You are a technical researcher. Read documentation, find patterns, and summarize findings. Output only the facts needed for implementation."
);

const coder = createSpecialist(
  "coder",
  "You are a senior TypeScript developer. Given requirements and research notes, write clean, tested code. Nothing else."
);

const reviewer = createSpecialist(
  "reviewer",
  "You are a code reviewer. Find bugs, security issues, and logic errors. Be specific. Cite line numbers."
);
```

Her uzmanın odaklı bir prompt'u var. Her biri sadece ihtiyaç duyduğu girdiyle temiz bir context penceresi alır.

### Adım 3: Mesajlar Üzerinden Koordine Et

Uzmanları açık mesaj iletimi ile birbirine bağla:

```typescript
type AgentMessage = {
  from: string;
  to: string;
  content: string;
  timestamp: number;
};

async function multiAgentApproach(task: string): Promise<AgentResult> {
  const messages: AgentMessage[] = [];
  let totalTokens = 0;
  let totalToolCalls = 0;

  const researchResult = await researcher.run(task);
  messages.push({
    from: "researcher",
    to: "coder",
    content: researchResult.content,
    timestamp: Date.now(),
  });
  totalTokens += researchResult.tokensUsed;
  totalToolCalls += researchResult.toolCalls;

  const coderInput = messages
    .filter((m) => m.to === "coder")
    .map((m) => `[From ${m.from}]: ${m.content}`)
    .join("\n");

  const codeResult = await coder.run(coderInput);
  messages.push({
    from: "coder",
    to: "reviewer",
    content: codeResult.content,
    timestamp: Date.now(),
  });
  totalTokens += codeResult.tokensUsed;
  totalToolCalls += codeResult.toolCalls;

  const reviewerInput = messages
    .filter((m) => m.to === "reviewer")
    .map((m) => `[From ${m.from}]: ${m.content}`)
    .join("\n");

  const reviewResult = await reviewer.run(reviewerInput);
  messages.push({
    from: "reviewer",
    to: "orchestrator",
    content: reviewResult.content,
    timestamp: Date.now(),
  });
  totalTokens += reviewResult.tokensUsed;
  totalToolCalls += reviewResult.toolCalls;

  return {
    content: messages.map((m) => `[${m.from} -> ${m.to}]: ${m.content}`).join("\n\n"),
    tokensUsed: totalTokens,
    toolCalls: totalToolCalls,
  };
}
```

Her agent sadece kendisine adreslenmiş mesajları alır. Context kirlenmesi yok. Araştırmacının 50k token'lık dokümantasyon okuması inceleyenin context'ine asla girmez.

### Adım 4: Karşılaştır

```typescript
async function compare() {
  const task = "Build a rate limiter middleware for an Express.js API";

  console.log("=== Single Agent ===");
  const single = await singleAgentApproach(task);
  console.log(`Tokens: ${single.tokensUsed}`);
  console.log(`Tool calls: ${single.toolCalls}`);

  console.log("\n=== Multi-Agent ===");
  const multi = await multiAgentApproach(task);
  console.log(`Tokens: ${multi.tokensUsed}`);
  console.log(`Tool calls: ${multi.toolCalls}`);
}
```

Çoklu-agent versiyonu toplamda daha fazla token kullanır (üç agent, üç ayrı LLM çağrısı) ama her agent'ın context'i temiz kalır. Her aşamanın kalitesi sistem prompt'u özelleştirildiği için artar.

## Kullan

Bu ders, çoklu-agent'a ne zaman gidileceğine karar vermek için yeniden kullanılabilir bir prompt üretir. `outputs/prompt-multi-agent-decision.md` dosyasına bak.

## Alıştırmalar

1. Dördüncü bir uzman ekle: kodcudan kod ve inceleyenden geri bildirim alan ve sonra test yazan bir "testçi" agent
2. Pipeline'ı, inceleyenin geri bildirimini revizyon döngüsü için kodcuya gönderebileceği şekilde değiştir (maks 2 tur)
3. Sıralı pipeline'ı bir fan-out'a dönüştür: araştırmacıyı ve bir "gereksinim analisti" agent'ı paralel çalıştır, sonra çıktılarını kodcuya iletmeden önce birleştir

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|----------------------|
| Sürü (Swarm) | "AI agent'larının kovan zihni" | Paylaşılan state'i olan ve sabit lider olmayan peer agent kümesi. Davranış yerel etkileşimlerden çıkar. |
| Orchestrator | "Patron agent" | Tool'ları diğer agent'ları doğurmayı ve yönetmeyi içeren agent. Planlar ve delege eder ama gerçek işi yapmayabilir. |
| Koordinatör | "Trafik polisi" | Mesajları kurallara göre agent'lar arasında yönlendiren agent-olmayan bir bileşen (genellikle sadece kod, LLM değil). |
| Konsensüs | "Agent'lar anlaşır" | İlerlemeden önce birden çok agent'ın anlaşmaya varması gereken protokol. Çelişen çıktıların çözülmesi gerektiğinde kullanılır. |
| Yükselen davranış (emergence) | "Agent'lar kendileri çözmüş" | Agent etkileşimlerinden ortaya çıkan ama açıkça programlanmamış sistem-seviyesi desenler. Faydalı ya da zararlı olabilir. |
| Fan-out / fan-in | "Agent'lar için map-reduce" | Bir görevi paralel agent'lara bölmek (fan-out), sonra sonuçlarını birleştirmek (fan-in). |
| Mesaj iletimi | "Agent'lar birbiriyle konuşur" | Agent'lar arasındaki iletişim mekanizması: bir agent'tan diğerine gönderilen yapılandırılmış veri, paylaşılan context pencerelerinin yerini alır. |

## İleri Okuma

- [The Landscape of Emerging AI Agent Architectures](https://arxiv.org/abs/2409.02977) — çoklu-agent desenlerinin taraması
- [AutoGen: Enabling Next-Gen LLM Applications](https://arxiv.org/abs/2308.08155) — Microsoft'un çoklu-agent konuşma framework'ü
- [Claude Code subagent'lar dokümantasyonu](https://docs.anthropic.com/en/docs/claude-code) — Claude Code'un Task ile nasıl delege ettiği
- [CrewAI dokümantasyonu](https://docs.crewai.com/) — rol tabanlı çoklu-agent framework'ü
