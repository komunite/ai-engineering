# Vaka Çalışmaları ve 2026 State of the Art

> Her biri çoklu-agent mühendisliğinin farklı bir dilimini gösteren, uçtan uca incelenecek üç üretim-grade referans. **Anthropic'in Research sistemi** (orchestrator-worker, 15× token, tek-agent Opus 4 üzerinde +%90.2, rainbow deployment'lar) kanonik supervisor vakasıdır. **MetaGPT / ChatDev** (yazılım mühendisliği için SOP-kodlanmış rol uzmanlaşması; ChatDev'in "communicative dehallucination"ı; DAG'lar yoluyla >1000 agent'a MacNet uzantısı, arXiv:2406.07155) kanonik rol-parçalama vakasıdır. **OpenClaw / Moltbook** (başlangıçta Peter Steinberger tarafından Clawdbot, Kasım 2025; iki kez yeniden adlandırıldı; Mart 2026'ya kadar 247k GitHub star; yerel ReAct-loop agent'lar; lansmandan günler içinde ~2.3M agent hesabıyla agent-yalnızca sosyal ağ olarak Moltbook, 2026-03-10'da Meta tarafından satın alındı) popülasyon ölçeğinde ne olduğunu gösterir: ortaya çıkan ekonomik aktivite, prompt-injection riskleri, devlet-seviye düzenleme (Çin OpenClaw'u hükümet bilgisayarlarında kısıtladı, Mart 2026). **Framework manzarası Nisan 2026:** LangGraph ve CrewAI üretimde önderlik eder; AG2 topluluk AutoGen devamıdır; Microsoft AutoGen bakım modundadır (Microsoft Agent Framework'e birleşti, RC Şub 2026); OpenAI Agents SDK üretim Swarm halefidir; Google ADK (Nisan 2025) A2A-native giriştir. Her büyük framework artık MCP desteği gönderir; çoğu A2A gönderir. Bu ders her vakayı uçtan uca okur ve ortak desenleri damıtır, böylece bir sonraki üretim sistemin için doğru referansı seçebilirsin.

**Tür:** Öğrenim (capstone)
**Diller:** —
**Ön koşullar:** Faz 16'nın tamamı (Dersler 01-24)
**Süre:** ~90 dakika

## Sorun

Çoklu-agent mühendisliği genç bir disiplin. Üretim referansları azdır ve her biri uzayın farklı bir bölümünü kapsar. Onları teker teker okumak yararlıdır; onları bir küme olarak karşılaştırmak daha yararlıdır. Bu ders üç kanonik 2026 vaka çalışmasını uçtan uca bir okuma listesi olarak ele alır, ortak desenleri sabitler ve framework manzarasını eşler, böylece pazarlamadan değil bilgiden framework seçimleri yapabilirsin.

## Kavram

### Anthropic Research sistemi

Üretim supervisor-worker vakası. Claude Opus 4 planlar ve sentezler; Claude Sonnet 4 subagent'lar paralel olarak araştırır. Yayınlanmış engineering yazısı: https://www.anthropic.com/engineering/multi-agent-research-system.

Temel ölçülen sonuçlar:

- Dahili araştırma eval'lerinde tek-agent Opus 4 üzerinde **+%90.2** iyileşme.
- BrowseComp varyansının **%80'i yalnızca token kullanımı** tarafından açıklanır — çoklu-agent büyük ölçüde her subagent yeni bir context penceresi aldığı için kazanır.
- Tek-agent vs **sorgu başına 15× token**.
- Agent'lar uzun süreli ve stateful olduğu için **rainbow deployment**.

Kodlanmış tasarım dersleri:

1. **Çabayı sorgu karmaşıklığına ölçeklendir.** Basit → 3-10 tool çağrılı 1 agent. Orta → 3 agent. Karmaşık araştırma → 10+ subagent.
2. **Önce geniş, sonra dar.** Subagent'lar geniş aramalar yapar; lead sentezler; takip subagent'ları hedefli derinlikler yapar.
3. **Rainbow deploy'lar.** Eski runtime sürümlerini, in-flight agent'ları bitene kadar canlı tut.
4. **Doğrulama opsiyonel değil.** Sistem açık verifier rolleri olmadan halüsinasyon yaptığı gözlemlendi.

Bu üretim ölçeğinde supervisor-worker topolojisi için referans vakadır (Faz 16 · 05).

### MetaGPT / ChatDev

Üretim SOP-rol-parçalama vakası. arXiv:2308.00352 (MetaGPT) ve arXiv:2307.07924 (ChatDev) kapsa.

MetaGPT yazılım-mühendisliği SOP'larını rol prompt'ları olarak kodlar: Product Manager, Architect, Project Manager, Engineer, QA Engineer. Makalenin çerçevesi: `Code = SOP(Team)`. Her rolün dar, uzmanlaşmış bir prompt'u vardır; rol-arası handoff'lar yapılandırılmış artefaktlar (PRD dokümanları, mimari dokümanları, kod) taşır.

ChatDev'in katkısı: **communicative dehallucination**. Agent'lar yanıt vermeden önce özellikleri ister — bir designer agent UI çizmeden önce programmer'a hangi dilin amaçlandığını sorar, tahmin etmek yerine. Makale bunun çoklu-agent pipeline'larındaki halüsinasyonu ölçülebilir şekilde azalttığını rapor ediyor.

MacNet (arXiv:2406.07155) ChatDev'i **DAG'lar yoluyla >1000 agent'a** genişletir. Her DAG node'u bir rol uzmanlaşmasıdır; edge'ler handoff kontratlarını kodlar. Ölçek mümkün çünkü yönlendirme açık ve offline-hesaplanabilirdir.

Tasarım dersleri:

1. **Yapı boyuttan daha önemli.** Sıkı 5-rol SOP takım, 50-agent yapısız bir grubu yener.
2. **Yazılı handoff kontratları.** Roller arası iletilen artefaktlar bir şemayı izler.
3. **Communicative dehallucination** ucuz, yük taşıyıcı bir desendir.
4. **DAG'lar chat'ten daha fazla ölçeklenir.** Akış bilinebilirse, onu kodla.

Bu rol uzmanlaşması (Faz 16 · 08) ve yapılandırılmış topoloji (Faz 16 · 15) için referans vakadır.

### OpenClaw / Moltbook ekosistemi

Üretim popülasyon-ölçek vakası. Zaman çizelgesi:

- **Kasım 2025:** Clawdbot (Peter Steinberger'ın yerel ReAct-loop kodlama agent'ı) çıkar.
- **Aralık 2025 – Mart 2026:** iki kez yeniden adlandırıldı (Clawdbot → OpenClaw → OpenClaw altında devam etti).
- **Şubat 2026:** Moltbook aynı primitive'ler üzerinde agent-yalnızca sosyal ağ olarak lanse edildi; günler içinde ~2.3M agent hesabı.
- **Mart 2026 (2026-03-10):** Meta Moltbook'u satın aldı.
- **Mart 2026:** Çin OpenClaw'u hükümet bilgisayarlarında kısıtladı.
- **Mart 2026:** OpenClaw 247k GitHub star'ı geçti.

Milyonlarca agent'ı paylaşılan bir substrat üzerine koyduğunda çoklu-agent şöyle görünür:

- **Ortaya çıkan ekonomik aktivite.** Agent'lar token-ödemeleri kullanarak birbirinden satın alır, satar ve birbirine hizmet eder.
- **Popülasyon ölçeğinde prompt-injection riskleri.** Viral bir agent profilindeki bir kötü niyetli prompt saatler içinde binlerce agent-to-agent etkileşimine yayılır.
- **Devlet-seviye düzenleyici yanıt.** Lansmandan haftalar içinde, düzenleme ekosisteme ulaşır.

Bu vakadan tasarım dersleri kısmen teknik, kısmen yönetimseldir:

1. **Popülasyon ölçeğinde çoklu-agent yeni bir rejim.** Bireysel-sistem en iyi uygulamaları (doğrulama, rol netliği) hâlâ geçerli ama yeterli değil.
2. **Prompt injection yeni XSS.** Agent profillerini ve agent-arası mesajları varsayılan olarak güvenilmez girdi olarak ele al.
3. **Düzenleme tasarım döngülerinden hızlıdır.** Onun için planla.
4. **Açık kaynak + viral ölçek bileşik olur.** ~4 ayda 247k star alışılmadık; deploy-burst-yükü için tasarla.

Ekosistem detayı için [OpenClaw Wikipedia](https://en.wikipedia.org/wiki/OpenClaw) ve CNBC / Palo Alto Networks haberciliğine bak. Teknik temeller için Clawdbot / OpenClaw repo'ları yerel ReAct döngüsünü açığa çıkarır; Moltbook'un halka açık yazıları üst sosyal-graf mimarisini ortaya koyar.

### Framework manzarası Nisan 2026

| Framework | Durum | Şunun için en iyi | Notlar |
|---|---|---|---|
| **LangGraph** (LangChain) | Üretim lideri | yapılandırılmış graph + checkpointing + human-in-the-loop | üretim için önerilen varsayılan |
| **CrewAI** | Üretim lideri | Sequential/Hierarchical süreçlerle rol-tabanlı crew'lar | rol parçalama için güçlü |
| **AG2** | Topluluk korunan | GroupChat + speaker selection | AutoGen v0.2 devamı |
| **Microsoft AutoGen** | Bakım modu (Şub 2026) | — | Microsoft Agent Framework RC'ye birleşti |
| **Microsoft Agent Framework** | RC (Şub 2026) | orkestrasyon desenleri + kurumsal entegrasyon | yeni giriş; izle |
| **OpenAI Agents SDK** | Üretim | Swarm halefi | tool-return handoff deseni |
| **Google ADK** | Üretim (Nisan 2025) | A2A-native | Google Cloud entegrasyonu |
| **Anthropic Claude Agent SDK** | Üretim | tek-agent + Research uzantısı | Research sistem yazısına bak |

Her büyük framework artık **MCP** desteği gönderir; çoğu **A2A** gönderir. Protokol uyumluluğu artık bir farklılaştırıcı değildir.

### Üç vaka arasındaki ortak desenler

1. **Orchestrator + worker'lar** (Anthropic açık supervisor, MetaGPT PM-as-supervisor, OpenClaw bireysel agent'lar + ağ etkileri).
2. **Yapılandırılmış handoff kontratları** (Anthropic subagent görev tanımları, MetaGPT PRD/mimari dokümanları, OpenClaw A2A artefaktları).
3. **First-class rol olarak doğrulama** (Anthropic'in verifier'ı, MetaGPT'nin QA Engineer'ı, OpenClaw'un ağ-içi validator'ları).
4. **Ölçek topoloji + substrat, sadece daha fazla agent değil** (rainbow deploy'lar, MacNet DAG'ları, popülasyon-ölçek substratları).
5. **Maliyet maddidir ve açıklanır** (15× token, MetaGPT'de rol başına bütçe, Moltbook'ta etkileşim başına fiyatlandırma).
6. **Güvenlik duruşu açıktır** (Anthropic'in sandboxing'i, MetaGPT'nin rol kısıtlamaları, OpenClaw'un bilinen saldırı yüzeyi olarak prompt-injection).

### Bir sonraki proje için referans seçimi

- **Üretim araştırma / bilgi görevi → Anthropic Research.** Taze-context subagent'lar kazanır.
- **Mühendislik / tool-chain iş akışı → MetaGPT / ChatDev.** Roller + SOP'lar + handoff kontratları.
- **Ağ etkili sosyal ürün → OpenClaw / Moltbook.** Substrat + ortaya çıkan ekonomi.
- **Klasik kurumsal otomasyon → CrewAI ya da LangGraph** (üretim lideri, stabil runtime).

### 2026 state-of-the-art özeti

Alanın Nisan 2026'da nerede olduğu:

- **Framework'ler yakınsıyor.** MCP + A2A desteği table stake'tir. Handoff semantiği geri kalan tasarım seçimidir.
- **Değerlendirme sertleşiyor.** SWE-bench Pro, MARBLE, STRATUS hafifletme benchmark'ları. Pro mevcut kontaminasyon-dirençli gerçeklik kontrolüdür.
- **Üretim başarısızlık oranları ölçülebilirdir** (Cemri 2025 MAST; gerçek MAS'ta %41-86.7). Alan "demo'da harika görünür" döneminden çıktı.
- **Maliyet merkezi mühendislik kısıtıdır.** Görev başına token maliyeti, etkileşim başına duvar-saati, rainbow-deploy overhead. Çoklu-agent doğrulukta kazanır ama maliyette kaybeder — ve bu takas iş kararıdır.
- **Düzenleme yakın-vadeli bir girdidir, arka plan endişesi değil.** Yargı bölgeleri bireysel deploy döngülerinden daha hızlı hareket ediyor.

## Kullan

`outputs/skill-case-study-mapper.md` önerilen bir çoklu-agent sistem tasarımını okur ve en yakın vaka çalışmasına eşler, o vaka çalışmasının zaten test ettiği tasarım kararlarını yüzeye çıkarır.

## Yayınla

2026'da üretim çoklu-agent için başlangıç kuralları:

- **Sıfırdan değil, bir vaka çalışmasından başla.** Anthropic Research / MetaGPT / OpenClaw'dan en yakını seç ve uyarla.
- **MCP + A2A benimse.** Framework'ler arası taşınabilirlik değerlidir; protokol desteği ücretsizdir.
- **SWE-bench Pro'ya ya da iç Pro-eşdeğerine karşı ölç.** Verified kontamine.
- **Doğrulama vergisini öde.** Bağımsız bir verifier token bütçenin ~%20-30'una mal olur ve ölçülebilir doğruluk satın alır.
- **Uzun-süreli agent'ları rainbow deploy yap.** Çok-saatlik agent çalıştırmalarının rutin olmasını bekle.
- **WMAC 2026'yı ve MAST takiplerini oku.** Disiplin hızlı hareket ediyor.

## Alıştırmalar

1. Anthropic Research sistem yazısını uçtan uca oku. Opus 4'ü daha küçük bir modelle (ör. Haiku 4) değiştirsen değişecek üç tasarım kararını belirle.
2. MetaGPT Bölüm 3-4'ü (arXiv:2308.00352) oku. Kendi alanından (yazılım dışı) bir SOP'u rol prompt'ları olarak kodla. SOP kaç rol ima ediyor?
3. ChatDev'i (arXiv:2307.07924) oku. "Communicative dehallucination" mekanizmasını belirle. Onu mevcut çoklu-agent sistemlerinden birinde uygula.
4. OpenClaw ve Moltbook hakkında oku. 5-agent bir sistemde görünmeyecek, popülasyon ölçeğinde ortaya çıkan belirli bir başarısızlık modunu seç. Buna karşı nasıl mühendislik yapardın?
5. Mevcut çoklu-agent projeni seç. Üç vaka çalışmasından hangisi en yakın referans? O vaka çalışmasından hangi tasarım kararlarını henüz benimsemedin? Bu çeyrek benimseyeceğin birini yaz.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Anthropic Research | "Supervisor referansı" | Claude Opus 4 + Sonnet 4 subagent'lar; 15× token; tek-agent üzerinde +%90.2. |
| MetaGPT | "Prompt olarak SOP" | Yazılım mühendisliği için rol parçalaması; `Code = SOP(Team)`. |
| ChatDev | "Roller olarak agent'lar" | Designer / programmer / reviewer / tester; communicative dehallucination. |
| MacNet | "DAG ile ChatDev'i ölçeklendir" | arXiv:2406.07155; açık DAG yönlendirmesi yoluyla 1000+ agent. |
| OpenClaw | "Yerel ReAct-loop agent'lar" | Steinberger'in projesi; Mart 2026'ya kadar 247k star. |
| Moltbook | "Agent-yalnızca sosyal ağ" | 2.3M agent hesabı; Mart 2026'da Meta tarafından satın alındı. |
| Rainbow deploy | "Birden çok sürüm eş zamanlı" | İn-flight uzun-süreli agent'lar için eski runtime sürümlerini canlı tut. |
| Communicative dehallucination | "Yanıtlamadan önce sor" | Agent'lar tahmin etmek yerine peer'lardan özellikler ister. |
| WMAC 2026 | "AAAI workshop" | Çoklu-agent koordinasyonu için Nisan 2026 topluluk odak noktası. |

## İleri Okuma

- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — supervisor-worker üretim referansı
- [MetaGPT — Meta Programming for Multi-Agent Collaborative Framework](https://arxiv.org/abs/2308.00352) — SOP-rol parçalaması
- [ChatDev — Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924) — communicative dehallucination
- [MacNet — scaling role-based agents to 1000+](https://arxiv.org/abs/2406.07155) — DAG-tabanlı ölçek
- [OpenClaw on Wikipedia](https://en.wikipedia.org/wiki/OpenClaw) — ekosistem genel bakışı
- [WMAC 2026](https://multiagents.org/2026/) — AAAI 2026 Bridge Program Workshop on Multi-Agent Coordination
- [LangGraph docs](https://docs.langchain.com/oss/python/langgraph/workflows-agents) — üretim lideri
- [CrewAI docs](https://docs.crewai.com/en/introduction) — rol-tabanlı framework
