# Agent Framework Tradeoff'ları — LangGraph vs CrewAI vs AutoGen vs Agno

> Her framework aynı demo'yu satar (research agent rapor üretir) ve aynı hatayı saklar (state schema orchestration katmanıyla kavga eder). Abstraction'ları senin probleminin şekline uyan framework'ü seç; geri kalan her şey iki kez yazdığın glue kodudur.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 11 · 09 (Function Calling), Faz 11 · 16 (LangGraph)
**Süre:** ~45 dakika

## Sorun

Birden fazla LLM çağrısına ihtiyaç duyan bir görevin var. Belki bir araştırma akışı (planla, ara, özetle, alıntıla). Belki bir code-review pipeline'ı (diff'i parse et, eleştir, patch'le, doğrula). Belki uçuş ayırtan, e-posta yazan ve gider raporu dolduran çok turlu bir asistan. Bir framework seçiyorsun.

Üç gün sonra, framework'ün abstraction'larının sızdığını keşfediyorsun. CrewAI sana rol veriyor ama "researcher" "writer"'a yapılandırılmış bir plan devretmesi gerektiğinde sana karşı çıkıyor. AutoGen agent'lar arasında sohbet veriyor ama birinci-sınıf state'i yok, dolayısıyla checkpoint'in bir konuşma log'unun pickle'ı. LangGraph sana bir state graph veriyor ama agent'ın ne yapacağını bilmeden önce her geçişi adlandırmaya zorluyor. Agno tek-agent primitive'i veriyor ve üç eşzamanlı worker'a fan-out yapmaya çalıştığında çığlık atıyor.

Düzeltme "en iyi framework'ü seç" değil. Düzeltme, framework'ün çekirdek abstraction'ını senin probleminin şekline eşlemektir. Bu ders o haritayı çiziyor.

## Kavram

![Agent framework matrisi: çekirdek abstraction vs problem şekli](../assets/framework-matrix.svg)

Dört framework 2026 ortamına hakim. Çekirdek abstraction'ları aynı değil.

| Framework | Çekirdek abstraction | En iyi uyum | En kötü uyum |
|-----------|------------------|----------|-----------|
| **LangGraph** | `StateGraph` — tipli state, node'lar, conditional edge'ler, checkpointer. | Açık state ve human-in-the-loop interrupt'lara sahip workflow'lar; time-travel debugging'e ihtiyaç duyan üretim agent'ları. | Topolojinin bilinmediği gevşek, rol-odaklı brainstorming. |
| **CrewAI** | `Crew` — roller (goal, backstory), task'lar, process (sequential veya hierarchical). | Kısa lineer/hiyerarşik plana sahip rol-yapma ya da persona-odaklı workflow'lar. | Crew'in tur geçmişinin ötesinde stateful olan herhangi bir şey; karmaşık dallanma. |
| **AutoGen** | `ConversableAgent` çifti — bir çıkış koşuluna kadar sırayla konuşan iki ya da daha fazla agent. | Düşüncenin sohbetten ortaya çıktığı multi-agent *diyalog* (öğretmen-öğrenci, öneren-eleştirmen, oyuncu-gözden geçiren). | Bilinen DAG'a sahip deterministik workflow'lar; restart'lar arası dayanıklı state'e ihtiyaç duyan herhangi bir şey. |
| **Agno** | `Agent` — tek bir LLM + tool'lar + bellek, takımlara compose edilebilir. | Hızlı inşa edilen tek agent'lar ve hafif takımlar; güçlü multi-modality ve dahili storage driver'ları. | Custom reducer'lara sahip derin, açıkça-dallanmış graph'lar. |

### "Abstraction" gerçekten ne demek

Bir framework'ün çekirdek abstraction'ı, mimariyi sunarken beyaz tahtaya çizdiğin şeydir.

- **LangGraph** → bir graph çizersin. Node'lar adımlar, edge'ler geçişlerdir ve her noktadaki state nesnesi tipli. Zihinsel model bir state machine.
- **CrewAI** → bir org şeması çizersin. Her rolün bir iş tanımı vardır ve bir yönetici task'ları yönlendirir. Zihinsel model küçük bir uzmanlar takımı.
- **AutoGen** → bir Slack DM'i çizersin. İki agent birbirine mesaj atar; bir moderatöre ihtiyacın olursa üçüncü katılır. Zihinsel model sohbet.
- **Agno** → tool'ları aşağıya sarkmış tek bir kutu çizersin. Bir takım için kutuları yan yana koy. Zihinsel model "batarya dahil agent".

### State sorusu

State, framework seçimlerinin çoğunun üretimde patladığı yerdir.

- **LangGraph.** Tipli state (`TypedDict` ya da Pydantic model), alan başına reducer'lar, birinci-sınıf checkpointer (SQLite/Postgres/Redis). Resume, interrupt ve time-travel bedava. *(Bkz. Faz 11 · 16.)*
- **CrewAI.** State, task'lar arasında string olarak `context` alanı üzerinden ya da `output_pydantic` üzerinden yapılandırılmış olarak akar. Kutudan çıkar çıkmaz crew başına dayanıklı bir store yok; crew bir restart'tan sağ çıkmak zorundaysa kendi yapını üzerine cıvatalarsın.
- **AutoGen.** State, sohbet geçmişi ve kullanıcı tanımlı `context`'tir. Konuşma transkriptleri kalıcıdır; sen adapter yazmazsan keyfi workflow state'i değildir.
- **Agno.** `Agent`'a `storage=` ile bağlanan dahili storage driver'ları (SQLite, Postgres, Mongo, Redis, DynamoDB) — konuşma session'ları ve kullanıcı bellekleri otomatik kalıcı. Tam bir graph checkpointer'ı değil; bir session store'u.

### Dallanma sorusu

Trivial olmayan her agent dallanır. Dalın kararını kim verir, önemli.

- **LangGraph** — sen karar verirsin, conditional edge'ler üzerinden. Routing, adlandırılmış dallara sahip bir Python fonksiyonudur. Dallar derlenmiş graph'ta birinci-sınıf; checkpointer hangi dalın alındığını kaydeder.
- **CrewAI** — hierarchical mode'da yönetici karar verir; sequential mode'da sen build zamanında karar verirsin. Routing task listesinde örtük; yöneticinin prompt'unun dışında birinci-sınıf bir "if" yok.
- **AutoGen** — agent'lar sohbet üzerinden karar verir. Dallanma, sonra kimin konuştuğundan ortaya çıkar. `GroupChatManager` sonraki konuşmacıyı seçer; bir `speaker_selection_method` elle yazabilirsin ama varsayılan LLM-odaklıdır.
- **Agno** — agent sonra hangi tool'u çağıracağına göre karar verir. Takımlarda coordinator/router/collaborator mode var; bunun ötesinde dallanma geliştiricinin sorumluluğu.

### Observability sorusu

- **LangGraph** — LangSmith ya da herhangi bir OTel exporter üzerinden OpenTelemetry. Her node geçişi bir trace span; checkpoint'ler tekrar oynatılabilir trace'lere ikinci sıfat olarak hizmet eder. LangSmith birinci-taraf seçenek; Langfuse/Phoenix'in de adapter'ları var.
- **CrewAI** — 2025 sonundan beri birinci-sınıf OpenTelemetry; Langfuse, Phoenix, Opik, AgentOps ile entegrasyonlar.
- **AutoGen** — `autogen-core` üzerinden OpenTelemetry entegrasyonu; AgentOps ve Opik'in connector'ları var. Trace ayrıntı düzeyi node başına değil, agent mesajı başına.
- **Agno** — dahili `monitoring=True` bayrağı artı OpenTelemetry exporter'ları; session trace'leri için Langfuse ile sıkı entegrasyon.

### Maliyet ve gecikme

Dört framework de çağrı başına ek yük ekler (framework mantığı, doğrulama, serileştirme). Artan ek yük sırası kabaca: Agno ≈ LangGraph < CrewAI ≈ AutoGen. Fark, framework'ün ne kadar ekstra LLM routing yaptığına hâkimdir. CrewAI'ın hierarchical yöneticisi sırada kimin gideceğine karar vermek için token harcar; AutoGen'in `GroupChatManager`'ı da öyle. LangGraph yalnızca `llm.invoke` yazdığın yerde token harcar. Agno'nun tek-agent yolu ince.

Çalışma başına maliyet önemli olduğunda, LLM-seçimli routing yerine açık routing'i (LangGraph edge'leri, AutoGen `speaker_selection_method`) tercih et.

### Birlikte çalışabilirlik

- **LangGraph** ↔ **LangChain** tool'ları, retriever'ları, LLM'leri. Birinci-sınıf MCP adapter'ı (tool'lar MCP sunucuları olarak içe aktarılır).
- **CrewAI** ↔ tool'lar `BaseTool`'dan miras alır; LangChain tool'ları, LlamaIndex tool'ları ve MCP tool'ları hepsi adapte olur. `allow_delegation=True` üzerinden crew-to-crew delegasyon.
- **AutoGen** → `FunctionTool` herhangi bir Python callable'ı sarar; MCP adapter mevcut. Agent-to-agent desenleri için AG2 ekosistemine sıkı bağlılık.
- **Agno** → `@tool` decorator'ı ya da BaseTool alt sınıfı; MCP adapter; tool'lar agent'lar ve takımlar arasında paylaşılabilir.

## Beceri

> Verilen bir agent problemi için verilen bir framework'ün neden doğru olduğunu tek cümleyle açıklayabilirsin.

İnşa öncesi checklist:

1. **Şekli çiz.** Bu bir graph mı (tipli state, adlandırılmış geçişler)? Bir rol oyunu mu (uzmanlar işi devreder)? Bir sohbet mi (agent'lar bitene kadar konuşur)? Tool'lara sahip tek bir agent mı?
2. **Kimin dallandığına karar ver.** Geliştirici-kararlı dallanma → LangGraph. Yönetici-agent-kararlı → CrewAI hierarchical. Sohbet-ortaya çıkarmalı → AutoGen. Tool-call-kararlı → Agno.
3. **State budget'ını kontrol et.** Checkpoint'ten resume'a ihtiyacın var mı? Time-travel? Çalışmanın ortasında insan interrupt'ı? Evetse, LangGraph varsayılan; Agno session'ları konuşma kapsamlı state'i kapsar.
4. **Maliyet budget'ını kontrol et.** LLM-seçimli routing tur başına ekstra token'a mal olur. Agent günde binlerce kez çalışıyorsa açık routing'i tercih et.
5. **Framework ek yükünü budget'la.** Her framework başka bir bağımlılık. Görev iki LLM çağrısı ve bir tool ise 30 satır düz Python yaz; hiçbir framework, framework olmamaktan daha ucuz değil.

Graph'ı, org şemasını, sohbeti ya da agent kutusunu çizemeden önce bir framework'e uzanmayı reddet. Gerçekten ihtiyacın olan şey için state modeliyle kavga etmeye zorlayan birini seçmeyi reddet.

## Karar Matrisi

| Problem şekli | Tercih edilen framework | Neden |
|---------------|---------------------|-----|
| Tipli state'li, insan onaylı, uzun süre çalışan workflow DAG | LangGraph | Birinci-sınıf state, checkpointer, interrupt'lar, time-travel. |
| Belirgin rollere sahip araştırma / yazma pipeline'ı | CrewAI (sequential) ya da LangGraph alt-graph'ları | Task başına rol CrewAI'de ifade etmesi ucuz; dallanma karmaşıklaştığında LangGraph ile ölçeklendir. |
| Öneren-eleştirmen ya da öğretmen-öğrenci diyalog | AutoGen | İki-agent sohbeti onun yerli şekli. |
| Tool'lar, session'lar, bellek içeren tek agent | Agno | En ince kurulum, dahili storage ve bellek. |
| Reducer'larla binlerce paralel fan-out | LangGraph + `Send` | Birinci-sınıf paralel dispatch primitive'ine sahip tek olan. |
| Hızlı prototip, framework bağlılığı yok | Düz Python + sağlayıcı SDK'sı | Hiç framework olmaması en hızlı framework'tür. |

## Alıştırmalar

1. **Kolay.** Aynı görevi al — "Anthropic'in merkezini araştır, 200 kelimelik özet yaz, kaynak alıntıla" — ve LangGraph'ta (dört node: planla, ara, yaz, alıntıla) ve CrewAI'de (üç rol: researcher, writer, editor) uygula. Çalışma başına token maliyetini ve kod satırı sayısını raporla.
2. **Orta.** Aynı görevi AutoGen'de (researcher ↔ writer sohbeti, editor `GroupChat` üzerinden katılır) ve Agno'da (`search_tools` ve `write_tools`'a artı bir session store'una sahip tek bir agent) inşa et. Dört uygulamayı (a) çalışma başına maliyet, (b) bir crash sonrası resume yeteneği, (c) yazma adımından önce insan onayı ekleme yeteneği üzerinde sırala.
3. **Zor.** Kısa bir problem tanımı (JSON: `{has_typed_state, has_roles, has_dialogue, has_parallel_fanout, needs_resume}`) alıp tek cümlelik gerekçeyle bir öneri döndüren karar-ağacı script'i `pick_framework.py` inşa et. Kendi tasarladığın altı durumda doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Orchestration | "Agent'lar nasıl koordine olur" | Sonra hangi node/role/agent'ın çalışacağına karar veren katman. |
| Dayanıklı state | "Restart sonrası resume" | Bir checkpoint ya da session store'una bağlı, process ölümünden sağ çıkan state. |
| LLM-seçimli routing | "Modelin karar vermesine izin ver" | Bir planlayıcı LLM her turda sonraki adımı seçer; esnek ama her kararda token öder. |
| Açık routing | "Geliştirici karar verir" | Bir Python fonksiyonu ya da statik edge sonraki adımı seçer; ucuz ve denetlenebilir. |
| Crew | "Bir CrewAI takımı" | Tek bir runnable'a bağlı roller + task'lar + process (sequential ya da hierarchical). |
| GroupChat | "AutoGen'in multi-agent sohbeti" | Konuşmacı seçici ile N agent arasında yönetilen bir konuşma. |
| Team (Agno) | "Multi-agent Agno" | Bir agent kümesi üzerinde route / coordinate / collaborate mode. |
| StateGraph | "LangGraph'ın graph'ı" | Tipli-state, node, conditional-edge, checkpointer primitive'i. |

## İleri Okuma

- [LangGraph dokümantasyonu](https://langchain-ai.github.io/langgraph/) — StateGraph, checkpointer'lar, interrupt'lar, time-travel.
- [CrewAI dokümantasyonu](https://docs.crewai.com/) — Crew'lar, Flow'lar, Agent'lar, Task'lar, Process'ler.
- [AutoGen dokümantasyonu](https://microsoft.github.io/autogen/) — ConversableAgent, GroupChat, takımlar, tool'lar.
- [Agno dokümantasyonu](https://docs.agno.com/) — Agent, Team, Workflow, storage, memory.
- [Anthropic — Building effective agents (Aralık 2024)](https://www.anthropic.com/research/building-effective-agents) — desen kütüphanesi (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer), framework-agnostik.
- [Yao et al., "ReAct: Synergizing Reasoning and Acting" (ICLR 2023)](https://arxiv.org/abs/2210.03629) — her framework'ün giydirdiği primitive.
- [Wu et al., "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation" (2023)](https://arxiv.org/abs/2308.08155) — AutoGen'in tasarım makalesi.
- [Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (UIST 2023)](https://arxiv.org/abs/2304.03442) — CrewAI-tarzı persona yığınlarının üzerine inşa edildiği rol-yapma temeli.
- Faz 11 · 16 (LangGraph) — bu dersin karşılaştırma yaptığı framework.
- Faz 11 · 19 (Reflexion) — LangGraph'a temiz, CrewAI'a hantalca eşlenen bir desen.
- Faz 11 · 22 (Üretim observability) — seçtiğin framework'ü nasıl enstrümante edersin.
