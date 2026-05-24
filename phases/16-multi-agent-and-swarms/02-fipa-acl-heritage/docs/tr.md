# FIPA-ACL ve Söz Eylemleri Mirası

> MCP'den önce, A2A'dan önce FIPA-ACL vardı. 2000'de IEEE Foundation for Intelligent Physical Agents yirmi performative, iki içerik dili ve bir dizi etkileşim protokolüyle (contract net, subscribe/notify, request-when) bir agent iletişim dili onayladı. Ontoloji yükü web için fazla ağır olduğundan endüstriden silindi, ama çoklu-agent sistemlerinin LLM canlanması formel anlambilim olmadan aynı fikirleri sessizce yeniden uyguluyor: JSON kontratları performative'lerin yerine, doğal dil ontolojilerin yerine geçiyor. Bu ders FIPA-ACL'i ciddi şekilde okur — böylece 2026 protokol kararlarından hangisinin yeniden icat, hangisinin yenilik olduğunu ve mevcut dalganın 2000'lerin çoktan çözdüğü hangi sorunları yeniden keşfedeceğini görebilirsin.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 01 (Neden Çoklu-Agent)
**Süre:** ~60 dakika

## Sorun

2026 agent-protokol manzarası yoğun: tool'lar için MCP, agent'lar için A2A, kurumsal denetim için ACP, merkeziyetsiz güven için ANP, doğal-dil içerik için NLIP, artı CA-MCP ve onlarca araştırma önerisi. Her spec kendini temel olarak duyurur.

Dürüst okuma çoğunun yirmi yıllık çok belirli bir karar ağacını yeniden keşfettiği. Austin (1962) ve Searle'in (1969) söz eylemi teorisi bize "söylemler eylemdir"i verdi. KQML (1993) bunu bir wire protokolüne dönüştürdü. FIPA-ACL (2000'de onaylandı) referans standardizasyonu üretti: yirmi performative, içerik dilleri SL0/SL1, contract-net ve subscribe-notify için etkileşim protokolleri. JADE ve JACK Java referans platformlarıydı. Çaba 2010 dolaylarında silindi çünkü ontoloji yükü çok ağırdı ve web kazanıyordu.

MCP'nin `tools/call`'ına, A2A'nın görev yaşam döngüsüne ya da CA-MCP'nin paylaşılan context store'una baktığında, FIPA kararlarının daha yumuşak, JSON-native bir tekrarına bakıyorsun. Mirası bilmek sana iki şey söyler: hangi yeni "yeniliklerin" aslında yeniden icat olduğu ve yeni spec'lerin hangi eski başarısızlık modlarını yeniden keşfedeceği.

## Kavram

### Söz eylemleri, tek paragrafta

Austin bazı cümlelerin dünyayı betimlemediğini fark etti — onu değiştirirler. "Söz veriyorum." "Rica ediyorum." "İlan ediyorum." Bunlara performatif söylemler dedi. Searle beş kategoride formelleştirdi: assertive, directive, commissive, expressive, declarative. KQML (Finin ve diğ., 1993) bunu yazılım agent'ları için operasyonel hale getirdi: mesaj bir performative (eylem) artı içerikten (eylemin neyle ilgili olduğu) oluşur. FIPA-ACL KQML'in boşluklarını temizledi ve yaklaşık yirmi performative etrafında standartlaştırdı.

### Yirmi FIPA performative'i (kısmi liste)

| Performative | Niyet |
|---|---|
| `inform` | "Sana P doğrudur diyorum" |
| `request` | "Senden X yapmanı istiyorum" |
| `query-if` | "P doğru mu?" |
| `query-ref` | "X'in değeri nedir?" |
| `propose` | "X yapmamızı öneriyorum" |
| `accept-proposal` | "Öneriyi kabul ediyorum" |
| `reject-proposal` | "Öneriyi reddediyorum" |
| `agree` | "X yapmayı kabul ediyorum" |
| `refuse` | "X yapmayı reddediyorum" |
| `confirm` | "P doğru olduğunu onaylıyorum" |
| `disconfirm` | "P'yi inkar ediyorum" |
| `not-understood` | "Mesajın parse edilemedi" |
| `cfp` | "X üzerine teklif çağrısı" |
| `subscribe` | "X değiştiğinde beni bilgilendir" |
| `cancel` | "Devam eden X'i iptal et" |
| `failure` | "X'i denedim ve başarısız oldum" |

Tam liste `fipa00037.pdf`'de (FIPA ACL Message Structure). Amaç ezberlemek değil — amaç bunların her birinin, bir LLM protokolünün eninde sonunda yeniden eklediği bir primitive'e karşılık geldiğidir.

### Kanonik FIPA-ACL mesajı

```
(inform
  :sender       agent1@platform
  :receiver     agent2@platform
  :content      "((price IBM 83))"
  :language     SL0
  :ontology     finance
  :protocol     fipa-request
  :conversation-id   conv-42
  :reply-with   msg-17
)
```

Yedi alan protokol zarfını taşır; bir alan (`content`) payload'ı taşır. Geri kalan alanlar, bir JSON protokolüne retry'lar, threading ve ontoloji eklediğinde her seferinde yeniden icat ettiğin tam olarak şeyler.

### İki eski platform

**JADE** (Java Agent DEvelopment framework, 1999–2020'ler) en çok kullanılan FIPA-uyumlu runtime'dı. Agent'lar bir temel sınıfı genişletti, ACL mesajları alışverişi yaptı, container'lar içinde çalıştı ve "behaviors" kullanarak koordine oldu. Etkileşim protokolü kütüphanesi contract-net, subscribe-notify, request-when ve propose-accept ile geldi.

**JACK** (Agent Oriented Software, ticari) FIPA mesajları üzerine BDI (Belief-Desire-Intention) akıl yürütmeyi vurguladı. Daha formel, daha az benimsenen.

İkisi de web yığını çoklu-agent kullanım durumlarını yutunca düşüşe geçti. MCP ve A2A 2026'nın runtime "container"larıdır.

### FIPA neden silindi

- **Ontoloji yükü.** FIPA, `content`'i parse etmek için paylaşılan bir ontoloji gerektiriyordu. Ontolojiler üzerinde anlaşmak yıllar süren standartlar sürecidir. Web sadece HTTP + JSON kullandı.
- **Kimsenin kullanmadığı formel anlambilim.** SL (Semantic Language) titiz doğruluk koşulları verdi, ama çoğu üretim sistemi serbest formatlı içerik kullandı ve formalizmi görmezden geldi.
- **Tooling kilidi.** JADE yalnızca Java'ydı; JACK ticariydi. Çoklu-dil takımları ikisini de baypas etti.
- **İnternet yığını kazandı.** REST, sonra JSON-RPC, sonra gRPC ACL'in transport'unun yerini aldı.

### LLM canlanması FIPA-lite

Bir FIPA `request`'i bir MCP `tools/call` ile karşılaştır:

```
(request                                {
  :sender  agent1                         "jsonrpc": "2.0",
  :receiver tool-server                   "method":  "tools/call",
  :content "(lookup stock IBM)"           "params":  {"name":"lookup_stock",
  :ontology finance                                   "arguments":{"symbol":"IBM"}},
  :conversation-id c42                    "id": 42
)                                        }
```

Aynı zarf, farklı sözdizimi. Her ikisi de şunları taşır: kim, kime, niyet, payload, korelasyon id'si. Hiçbiri diğerine göre bir devrim değil — aynı tasarım üzerinde farklı takaslar.

Liu ve diğ.'in 2025 taraması ("A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, ANP", arXiv:2505.02279) bu soy ağacını açıkça ortaya koyar: MCP tool-kullanım söz eylemlerine, A2A agent-peer söz eylemlerine, ACP audit-trail söz eylemlerine, ANP merkeziyetsiz-kimlik uzantılarına karşılık gelir. Yeni spec'ler JSON sözdizimi ve daha gevşek semantik ile ACL torunlarıdır.

### Takas, açıkça ifade edildi

**FIPA'nın sana verdikleri ve modern spec'lerin düşürdükleri:**

- Formel anlambilim — `inform`'un göndericinin içeriğe inandığını ima ettiğini kanıtlayabilirsin.
- Kanonik bir performative kataloğu — "bir `cancel`'imiz olmalı mı?" tartışmasını yeniden açmana gerek yok.
- Onlarca yıllık etkileşim protokolü deseni — contract-net, subscribe-notify, propose-accept — bilinen doğruluk özellikleriyle.

**Modern spec'lerin sana verdikleri ve FIPA'nın vermedikleri:**

- Her modern tool ile uyumlu JSON-native payload'lar.
- LLM'lerin elle kodlanmış bir ontoloji olmadan yorumlayabileceği doğal-dil içeriği.
- Web-yığın transport (HTTP, SSE, WebSocket).
- Kendi kendini tanımlayan dokümanlar aracılığıyla yetenek keşfi (MCP `listTools`, A2A Agent Card).

Daha kolay uygulama için daha gevşek niyet anlambilimi. Takas tam olarak bu.

### Taşınmaya değer etkileşim protokolleri

FIPA ~15 etkileşim protokolü taşıdı. Üçü LLM çoklu-agent sistemlerine taşınmaya değer:

1. **Contract Net Protocol (CNP).** Manager `cfp` (call for proposals) yayınlar; teklif verenler `propose` ile yanıt verir; manager kabul/red eder. Bu kanonik görev-pazarı desenidir (Faz 16 · 16 Negotiation).
2. **Subscribe/Notify.** Abone `subscribe` gönderir; yayıncı konu değiştiğinde `inform` gönderir. Bu 2026'daki her event-bus'tır.
3. **Request-When.** "Y koşulu sağlandığında X'i yap." Ön-koşullarla geciktirilmiş eylem. 2026 analoğu dayanıklı workflow motorlarında ertelenmiş görevlerdir (Faz 16 · 22 Production Scaling).

Her biri modern mesaj kuyruklarına, HTTP + polling'e ya da SSE streaming'e temiz şekilde eşlenir.

### Ontolojiyi düşürdüğünde ne kırılır

Paylaşılan bir ontoloji olmadan, agent'lar doğal-dil içeriğinden anlam çıkarsar. Belgelenen 2026 başarısızlık modu **semantik kayma**'dır: iki agent aynı kelimeyi (`"customer"`) ince farklı kavramlar için kullanır, alıcının agent'ı yanlış yorum üzerinde hareket eder, hiçbir şema doğrulayıcı yakalayamaz. FIPA'nın ontoloji gereksinimi mesajı parse zamanında reddederdi.

Tam ontolojiye geçmeden hafifletmeler:

- `content` üzerinde JSON Schema — yapısal hataları wire'da reddeder.
- Tipli artefaktlar (A2A) — yanlış modaliteyi reddeder.
- Zarfta açık performative — içerik doğal dil olsa bile niyeti net hale getirir.

### 2026 spec'leri, söz eylemi mirasına eşlenmiş

| Modern spec | FIPA analoğu | Tuttuğu | Düşürdüğü |
|---|---|---|---|
| MCP `tools/call` | `request` | açık niyet, korelasyon id | formel anlambilim, ontoloji |
| MCP `resources/read` | `query-ref` | açık niyet, korelasyon id | formel anlambilim |
| A2A Task lifecycle | contract-net + request-when | async yaşam döngüsü, state geçişleri | formel bütünlük garantileri |
| A2A streaming events | subscribe/notify | async push | tipli-predicate aboneliği |
| CA-MCP shared context | blackboard (Hayes-Roth 1985) | çok-yazıcılı paylaşılan bellek | mantıksal tutarlılık modeli |
| NLIP | doğal-dil içeriği | LLM-native | şema |

Tabloyu yukarıdan aşağıya okuduğunda desen şu: yapısal primitive'i tut, formalizmi düşür, LLM'lerin belirsizliği kapatmasına izin ver.

## İnşa Et

`code/main.py` saf-stdlib bir FIPA-ACL çevirmeni uygular. Kanonik ACL zarfını kodlar ve çözer ve her MCP / A2A mesaj şeklinin nasıl aynı yedi alana indirgendiğini gösterir. Demo:

- Beş MCP-stili ve A2A-stili mesajı FIPA-ACL olarak kodlar.
- FIPA-ACL'i modern eşdeğerine geri çözer.
- `cfp`, `propose`, `accept-proposal`, `reject-proposal` kullanarak bir manager ve üç teklif veren arasında oyuncak bir Contract Net müzakeresi çalıştırır.

Çalıştır:

```
python3 code/main.py
```

Çıktı, her modern mesajı hem 2026 JSON formunda hem de FIPA-ACL formunda gösteren yan yana bir trace, ardından bir contract-net teklifinin gidiş-dönüşüdür. Aynı protokol primitive'leri gidiş-dönüşü atlatır; sadece sözdizimi farklıdır.

## Kullan

`outputs/skill-fipa-mapper.md` herhangi bir agent-protokol spec'ini okuyup FIPA-ACL eşlemesini üreten bir skill'dir. Yeni bir protokol benimsemeden önce şunu yanıtlamak için kullan: "Bu gerçekten yeni mi, yoksa JSON sözdizimiyle `inform` mi?"

## Yayınla

FIPA-ACL'i geri getirme. Onun kontrol listesini geri getir:

- Her mesajın niyet primitive'i (performative) nedir?
- Request-response ve iptal için bir korelasyon id'si var mı?
- Açık bir içerik dili var mı (JSON-RPC, düz metin, yapılandırılmış tipli artefakt)?
- Etkileşim protokolleri first-class mı, yoksa contract-net'i sıfırdan mı uyguluyorsun?
- İki agent içerik anlamı üzerinde anlaşamadığında ne olur (semantik kayma)?

Üretime herhangi bir yeni protokol göndermeden önce bu beş soruyu belgele.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Gidiş-dönüş kodlamayı gözlemle. `tools/call`, `resources/read` ve A2A görev oluşturmaya hangi FIPA performative'inin karşılık geldiğini belirle.
2. Manager'ın görevi teklif ortasında geri çekmesine izin veren bir `cancel` performative ile contract-net demosunu genişlet. `cancel`, retry'ların tek başına çözmediği hangi başarısızlık durumunu çözer?
3. FIPA ACL Message Structure (http://www.fipa.org/specs/fipa00037/) bölüm 4.1–4.3'ü oku. Bu derste kapsanmayan bir performative seç ve onun modern JSON-RPC analoğunu açıkla.
4. Liu ve diğ., arXiv:2505.02279'u oku. MCP, A2A, ACP, ANP'nin her biri için tuttukları ve düşürdükleri FIPA performative ailelerini listele.
5. Kendi sistemindeki bir `request` performative'inin `content` alanı için minimal bir JSON-Schema tasarla. O şema sana saf doğal-dilin vermediği neyi verir ve neye mal olur?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Söz eylemi | "Bir şey yapan söylem" | Austin/Searle: söylemler eylem olarak. ACL'in teorik ebeveyni. |
| FIPA | "O eski XML şeyi" | IEEE Foundation for Intelligent Physical Agents. ACL'i 2000'de standartlaştırdı. |
| ACL | "Agent Communication Language" | FIPA'nın zarf formatı: performative + content + metadata. |
| Performative | "Fiil" | Bir mesajın niyet sınıfı: `inform`, `request`, `propose`, `cfp` vs. |
| KQML | "FIPA'nın öncülü" | Knowledge Query and Manipulation Language (1993). Daha basit, daha dar. |
| Ontoloji | "Paylaşılan kelime dağarcığı" | İçerik dilinin bahsettiği kavramların formel tanımı. |
| SL0 / SL1 | "FIPA içerik dilleri" | Semantic Language seviye 0 ve 1 — formel içerik dili ailesi. |
| Contract Net | "Görev pazarı" | Manager cfp yayınlar; teklif verenler önerir; manager kabul eder. Kanonik etkileşim protokolü. |
| Etkileşim protokolü | "Mesaj deseni" | Bilinen doğruluğa sahip performative dizisi: request-when, subscribe-notify vs. |

## İleri Okuma

- [Liu ve diğ. — A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, ANP](https://arxiv.org/html/2505.02279v1) — modern spec'leri FIPA mirasına bağlayan kanonik 2025 taraması
- [FIPA ACL Message Structure Specification (fipa00037)](http://www.fipa.org/specs/fipa00037/) — 2000'de onaylanan zarf formatı
- [FIPA Communicative Act Library Specification (fipa00037)](http://www.fipa.org/specs/fipa00037/) — tam performative kataloğu
- [MCP specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — `request`/`query-ref`'in modern tool-kullanım eşdeğeri
- [A2A specification](https://a2a-protocol.org/latest/specification/) — contract-net ve subscribe-notify'ın modern agent-peer eşdeğeri
