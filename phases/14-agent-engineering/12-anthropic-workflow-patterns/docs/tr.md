# Anthropic'in Workflow Desenleri: Karmaşık Yerine Basit

> Schluntz ve Zhang (Anthropic, Aralık 2024) workflow'ları (önceden tanımlanmış yollar) agent'lardan (dinamik tool-use) ayırıyor. Beş workflow deseni çoğu durumu kapsar. Doğrudan API çağrılarıyla başla. Yalnızca adımlar tahmin edilemediğinde agent ekle.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Anthropic'in beş workflow desenini adlandır: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer.
- Agent-vs-workflow ayrımını ve her birinin mühendislik maliyetini açıkla.
- Bir agent yerine bir workflow ne zaman seçileceğini (ve tersini) tanı.
- Beş deseni de scripted bir LLM'e karşı stdlib'de uygula.

## Sorun

Ekipler tek bir fonksiyon çağrısı isteyen problemler için multi-agent framework'lere uzanıyor. Maliyet gerçek: framework'ler prompt'ları gizleyen, kontrol akışını saklayan ve erken karmaşıklığa davet eden katmanlar ekler. Schluntz ve Zhang'in Aralık 2024 yazısı en çok-cite edilen endüstri itirazı: basit başla, maliyetini hak ettiğinde karmaşıklık ekle.

## Kavram

### Workflow'lar vs agent'lar

- **Workflow.** Önceden tanımlanmış kod yollarıyla orkestre edilen LLM'ler ve tool'lar. Mühendisler graph'ı sahiplenir.
- **Agent.** LLM'ler kendi tool'larını dinamik olarak yönlendirir ve kendi adımlarını atar. Model graph'ı sahiplenir.

Her ikisinin de yeri var. Workflow'lar daha ucuz, daha hızlı ve hata ayıklamak daha kolay. Agent'lar açık-uçlu problemleri açar ama başarısızlık modlarını akıl yürütmesi daha zordur.

### Augmented LLM

Beş desenin de temeli: kablolanmış üç yeteneğe sahip bir LLM — arama (retrieval), tool'lar (aksiyonlar), bellek (kalıcılık). Herhangi bir API çağrısı bunları kullanabilir.

### Beş desen

1. **Prompt chaining.** Çağrı 1'in çıktısı çağrı 2'nin girdisi. Bir görev temiz doğrusal dekompozisyona sahip olduğunda kullan. Adımlar arasında opsiyonel programatik kapılar.

2. **Routing.** Bir classifier LLM hangi downstream LLM ya da tool'un invoke edileceğini seçer. Kategorik olarak farklı girdilerin farklı ele alma gerektirdiğinde kullan (tier-1 destek vs refund vs bug vs sales).

3. **Parallelization.** N LLM çağrısını eşzamanlı çalıştır, sonuçları topla. İki şekil: sectioning (farklı chunk'lar) ve voting (aynı prompt, N koşu, majority/synthesis).

4. **Orchestrator-workers.** Bir orchestrator LLM hangi worker'ların (ayrıca LLM'ler) çalıştırılacağını dinamik olarak karar verir ve çıktılarını sentezler. Agent döngülerine benzer ama orchestrator sınırsız döngü yapmaz.

5. **Evaluator-optimizer.** Bir LLM bir yanıt önerir, başka bir LLM onu değerlendirir. Evaluator geçene kadar iterate et. Bu Self-Refine (Ders 05) genelleştirilmiş hali.

### Workflow'ların agent'ları yendiği yerler

- **Tahmin edilebilir görevler.** Adımları sıralayabiliyorsan, yapmalısın.
- **Maliyet-bound görevler.** Workflow'lar sınırlı adım sayılarına sahip; agent'lar spiral yapabilir.
- **Compliance-bound görevler.** Denetçiler graph'ı okumak ister, trajectory'lerden çıkarmak değil.

### Agent'ların workflow'ları yendiği yerler

- **Açık-uçlu araştırma.** Bir sonraki adım önceki adımın döndürdüğüne bağlı olduğunda.
- **Değişken-uzunluk görevler.** Adım sayısının bilinmediği dakikadan saate iş.
- **Yeni domain'ler.** Doğru workflow'u henüz bilmediğinde — önce keşif, sonra kodifiye.

### Bağlam-mühendisliği yoldaşı

"Effective context engineering for AI agents" (Anthropic 2025) komşu disiplini formalize ediyor: 200k window bir bütçe, bir konteyner değil. Neyi dahil etmeli, ne zaman kompakte etmeli, bağlamı ne zaman büyütmeye izin vermeli. Bağlam sıkıştırması üzerine Faz 14 dersinde detaylı kapsanıyor (numaralandırmadan önce bu müfredatta önceki Faz 14 ders 06).

## İnşa Et

`code/main.py` bir `ScriptedLLM`'e karşı beş workflow desenini de uyguluyor:

- `prompt_chain(input, steps)` — sıralı.
- `route(input, classifier, handlers)` — sınıflandırma + dispatch.
- `parallel_vote(prompt, n, aggregator)` — N koşu, topla.
- `orchestrator_workers(task, workers)` — orchestrator worker'ları seçer.
- `evaluator_optimizer(task, proposer, evaluator, max_iter)` — geçene kadar döngü.

Çalıştır:

```
python3 code/main.py
```

Her desen trace'ini yazdırır. Desen başına toplam kod satırı ~10-15; bir framework'ün maliyeti binlerle ölçülür.

## Kullan

- Çoğu görev için doğrudan API çağrıları.
- Yalnızca desen gerçekten dayanıklı state (LangGraph), actor-model concurrency (AutoGen v0.4) ya da rol şablonlaması (CrewAI) gerektirdiğinde framework.
- Onu yeniden inşa etmeden Claude Code harness şekli istediğinde Claude Agent SDK'ya uzan.

## Yayınla

`outputs/skill-workflow-picker.md` belirli bir görev açıklaması için doğru deseni seçer; karar mantığı ve workflow'lar yetersiz kalırsa bir agent'a refactor yolu dahil.

## Alıştırmalar

1. Güven eşikli routing uygula. Eşiğin altında -> insana yükselt. Tier-1 destek use case'i için eşik nereye iniyor?
2. `parallel_vote`'a bir timeout ekle. Bir çağrı asıldığında ne olur? Eksik oylarla nasıl toplarsın?
3. `evaluator_optimizer`'ı bir bandit'e dönüştür: iterasyonlar arasında top-2 çıktıları tut, böylece geç iyi bir sonuç geç kötü bir sonuçla üzerine yazılmaz.
4. Prompt chaining'i routing ile birleştir: bir router üç zincirden birini seçer. Token maliyetini tek büyük-prompt alternatife karşı ölç.
5. Üretim özelliklerinden birini seç. Workflow graph'ını çiz. Adımları say. Burada gerçekten bir agent daha iyi olur muydu?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Workflow | "Önceden tanımlanmış akış" | LLM ve tool çağrılarının mühendis-sahipli graph'ı |
| Agent | "Otonom AI" | Model-sahipli graph; dinamik tool yönlendirmesi |
| Augmented LLM | "Tool'lu LLM" | LLM + arama + tool'lar + bellek; atomik birim |
| Prompt chaining | "Sıralı çağrılar" | Çağrı N'in çıktısı çağrı N+1'in girdisi |
| Routing | "Classifier dispatch" | Girdiyi hangi chain/model'in halledeceğini seç |
| Parallelization | "Fan out" | N eşzamanlı çağrı; sectioning ya da voting ile topla |
| Orchestrator-workers | "Dispatcher agent" | Orchestrator LLM uzman LLM'leri dinamik seçer |
| Evaluator-optimizer | "Öneren + yargıç" | Evaluator geçene kadar iterate et; Self-Refine genelleştirilmiş |

## İleri Okuma

- [Anthropic, Building Effective Agents (Aralık 2024)](https://www.anthropic.com/research/building-effective-agents) — beş workflow deseni
- [Anthropic, Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — yoldaş disiplin
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — durumlu graph'lar maliyetini ne zaman hak eder
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — orchestrator-workers deseni, ürünleştirilmiş
