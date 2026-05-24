# MCP Temelleri — Primitive'ler, Lifecycle, JSON-RPC Tabanı

> MCP'den önceki her entegrasyon tek-seferlikti. Model Context Protocol, ilk olarak Kasım 2024'te Anthropic tarafından yayınlandı ve şimdi Linux Foundation'ın Agentic AI Foundation'ı tarafından yönetiliyor, discovery ve invocation'ı standartlaştırıyor, böylece herhangi bir client herhangi bir sunucu ile konuşabilir. 2025-11-25 spec'i altı primitive (üç sunucu, üç client), üç-fazlı bir lifecycle ve bir JSON-RPC 2.0 wire formatı adlandırır. Bunları öğren ve bu fazın geri kalan MCP bölümü okunacak hale gelir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, JSON-RPC parser)
**Ön koşullar:** Faz 13 · 01 ile 05 arası (tool interface ve function calling)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Altı MCP primitive'inin hepsini adlandır (sunucuda tools, resources, prompts; client'ta roots, sampling, elicitation) ve her birine bir kullanım durumu ver.
- Üç-fazlı lifecycle'ı (initialize, operation, shutdown) gez ve her fazda kimin hangi mesajı gönderdiğini söyle.
- JSON-RPC 2.0 request, response ve notification zarflarını parse et ve yay.
- `initialize`'da capability negotiation'ın ne olduğunu ve onsuz neyin kırıldığını açıkla.

## Sorun

MCP'den önce, tool kullanan her agent'ın kendi protokolü vardı. Cursor'un MCP-şekilli ama uyumsuz bir tool sistemi vardı. Claude Desktop farklı bir tane ile yayınlandı. VS Code'un Copilot eklentisinin üçüncüsü vardı. Bir "Postgres query" tool'u inşa eden takım aynı tool'u üç kere yazdı, her birini farklı bir host'un API'sine. Yeniden kullanmak kodu kopyalamayı gerektiriyordu.

Sonuç tek-seferlik entegrasyonların bir Kambriyen patlaması ve ekosistem hızında bir tavandı.

MCP bunu wire formatını standartlaştırarak çözer. Tek bir MCP sunucusu her MCP client'ında çalışır: Claude Desktop, ChatGPT, Cursor, VS Code, Gemini, Goose, Zed, Windsurf, Nisan 2026 itibarıyla 300+ client. Aylık 110M SDK indirme. 10.000+ public sunucu. Linux Foundation Aralık 2025'te yeni Agentic AI Foundation altında stewardship'i devraldı.

Bu fazda kullanılan spec revizyonu **2025-11-25**'tir. Async Tasks (SEP-1686), URL-mode elicitation (SEP-1036), tool'larla sampling (SEP-1577), incremental scope consent (SEP-835) ve OAuth 2.1 resource-indicator semantiği ekler. Faz 13 · 09 ile 16 arası bu uzantıları ele alır. Bu ders tabanda durur.

## Kavram

### Üç sunucu primitive'i

1. **Tools.** Çağrılabilir aksiyonlar. Faz 13 · 01'deki aynı dört adımlı döngü.
2. **Resources.** Açılan veri. URI ile adreslenebilir read-only içerik: `file:///path`, `db://query/...`, custom şemalar.
3. **Prompts.** Yeniden kullanılabilir şablonlar. Host UI'sındaki slash-komutlar; sunucu şablonu sağlar, client argümanları doldurur.

### Üç client primitive'i

4. **Roots.** Sunucunun dokunmasına izin verilen URI kümesi. Client bildirir; sunucu saygı duyar.
5. **Sampling.** Sunucu, bir completion gerçekleştirmek için client'ın modelini ister. Sunucu-tarafı API key'leri olmadan sunucu-hostlu agent döngülerini etkinleştirir.
6. **Elicitation.** Sunucu, akışın ortasında client'ın kullanıcısından yapılandırılmış input ister. Form'lar ya da URL'ler (SEP-1036).

MCP'deki her capability tam olarak bu altıdan birine ait. Faz 13 · 10 ile 14 arası her birini derinlemesine ele alır.

### Wire formatı: JSON-RPC 2.0

Her mesaj bu alanlara sahip bir JSON objesidir:

- Request'ler: `{jsonrpc: "2.0", id, method, params}`.
- Response'lar: `{jsonrpc: "2.0", id, result | error}`.
- Notification'lar: `{jsonrpc: "2.0", method, params}` — `id` yok, response beklenmez.

Base spec ~15 method'a sahip, primitive bazında gruplanmış. Önemli olanlar:

- `initialize` / `initialized` (handshake)
- `tools/list`, `tools/call`
- `resources/list`, `resources/read`, `resources/subscribe`
- `prompts/list`, `prompts/get`
- `sampling/createMessage` (sunucudan client'a)
- `notifications/tools/list_changed`, `notifications/resources/updated`, `notifications/progress`

### Üç-fazlı lifecycle

**Faz 1: initialize.**

Client `capabilities`'i ve `clientInfo`'su ile `initialize` gönderir. Sunucu kendi `capabilities`'i, `serverInfo`'su ve konuştuğu spec versiyonu ile yanıt verir. Client yanıtı sindirdiğinde `notifications/initialized` gönderir. Bundan sonra, her iki taraf da müzakere edilen capability'lere göre request gönderebilir.

**Faz 2: operation.**

Çift yönlü. Client keşfetmek için `tools/list` çağırır, sonra çağırmak için `tools/call`. Sunucu o capability'yi bildirdiyse `sampling/createMessage` gönderebilir. Sunucu tool kümesi mutate olduğunda `notifications/tools/list_changed` gönderebilir. Client kullanıcı root scope'u değiştirdiğinde `notifications/roots/list_changed` gönderebilir.

**Faz 3: shutdown.**

Her iki taraf transport'u kapatabilir. MCP'de yapılandırılmış shutdown method'u yok; transport (stdio ya da Streamable HTTP, Faz 13 · 09) end-of-connection sinyalini taşır.

### Capability negotiation

`initialize` handshake'indeki `capabilities` sözleşmedir. Bir sunucudan örnek:

```json
{
  "tools": {"listChanged": true},
  "resources": {"subscribe": true, "listChanged": true},
  "prompts": {"listChanged": true}
}
```

Sunucu, `tools/list_changed` notification'ları yayabileceğini ve `resources/subscribe`'ı desteklediğini bildirir. Client kendisininkini bildirerek kabul eder:

```json
{
  "roots": {"listChanged": true},
  "sampling": {},
  "elicitation": {}
}
```

Client `sampling`'i bildirmezse, sunucu `sampling/createMessage`'ı çağırmamalıdır. Simetrik: sunucu `resources.subscribe`'ı bildirmezse, client subscribe etmeye çalışmamalıdır.

Ekosistem kaymasını önleyen şey budur. Sampling'i desteklemeyen bir client hâlâ geçerli bir MCP client'ıdır; `sampling` çağırmayan bir sunucu hâlâ geçerli bir MCP sunucusudur. Sadece o feature'ı birlikte kullanmazlar.

### Yapılandırılmış content ve hata şekilleri

`tools/call`, tipli blokların bir `content` array'ini döndürür: `text`, `image`, `resource`. Faz 13 · 14 o listeye MCP Apps (`ui://` interaktif UI) ekler.

Hatalar JSON-RPC hata kodlarını kullanır. Spec-tanımlı eklemeler: `-32002` "Resource not found", `-32603` "Internal error", artı `error.data` olarak MCP-spesifik hata verisi.

### Client capability'leri vs tool call ayrıntıları

Yaygın bir kafa karışıklığı: `capabilities.tools`, client'ın tool-list-changed notification'larını destekleyip desteklemediğidir. Client'ın belirli tool'ları çağırıP çağırMAYACAĞI, capability bayrağı değil, modelin sürdüğü runtime seçimidir. Capability bayrağı spec-seviyesi sözleşmedir. Modelin seçimi ortogonaldir.

### Neden JSON-RPC ve REST değil?

JSON-RPC 2.0 (2010) hafif çift yönlü bir protokoldür. REST client-initiated'tır. MCP'nin sunucu-initiated mesajlarına (sampling, notification'lar) ihtiyacı vardı, bu yüzden simetrik request/response şekliyle JSON-RPC doğal uyumdu. JSON-RPC ayrıca HTTP'nin request şeklini yeniden icat etmeden stdio ve WebSocket/Streamable HTTP üzerinde temiz şekilde compose olur.

## Kullan

`code/main.py` minimal bir JSON-RPC 2.0 parser ve emitter yayınlar, sonra `initialize` → `tools/list` → `tools/call` → `shutdown` sırasını elle gezer, her mesajı yazdırarak. Gerçek transport yok; sadece mesaj şekilleri. Her zarfı doğrulamak için İleri Okuma'da linklenen spec ile karşılaştır.

Bakılacak şeyler:

- `initialize` her iki yönde capability bildirir; yanıt `serverInfo` ve `protocolVersion: "2025-11-25"`'e sahiptir.
- `tools/list` bir `tools` array'i döndürür; her girdi `name`, `description`, `inputSchema`'ya sahiptir.
- `tools/call` `params.name` ve `params.arguments` kullanır.
- Yanıttaki `content` `{type, text}` bloklarının bir array'idir.

## Yayınla

Bu ders `outputs/skill-mcp-handshake-tracer.md` üretir. Bir MCP client-sunucu etkileşiminin pcap-tarzı transcript'i verildiğinde, skill her mesajı hangi primitive, hangi lifecycle fazı ve hangi capability'ye bağlı olduğuyla annotate eder.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Capability negotiation'ın gerçekleştiği satırı tanımla ve sunucu `tools.listChanged`'ı bildirmeseydi neyin değişeceğini açıkla.

2. Parser'ı `notifications/progress`'i ele almak için genişlet. Mesaj şekli: `{method: "notifications/progress", params: {progressToken, progress, total}}`. Uzun süren bir `tools/call` devam ederken yay ve client handler'ın bir progress bar göstereceğini doğrula.

3. MCP 2025-11-25 spec'ini baştan sona oku — tüm doküman yaklaşık 80 sayfadır. Sunucuların çoğunun ihtiyaç DUYMADIĞI tek capability bayrağını tanımla. İpucu: resource subscription ile ilgili.

4. Hipotetik bir "cron job" feature'ının ait olacağı primitive'i kağıda taslakla. (İpucu: sunucu, client'ın onu zamanlanmış bir zamanda çağırmasını ister. Altı primitive'in hiçbiri bugün uymuyor.) MCP'nin 2026 roadmap'inde bunun için taslak bir SEP var.

5. GitHub'daki açık bir MCP sunucusundan bir oturum log'unu parse et. Request vs response vs notification mesajlarını say. Trafik'in lifecycle vs operation oranını hesapla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MCP | "Model Context Protocol" | Model-tool discovery ve invocation için açık protokol |
| Sunucu primitive'i | "Sunucunun açtığı şey" | tools (aksiyonlar), resources (veri), prompts (şablonlar) |
| Client primitive'i | "Client'ın sunuculara izin verdiği şey" | roots (scope), sampling (LLM callback'leri), elicitation (kullanıcı input'u) |
| JSON-RPC 2.0 | "Wire formatı" | Simetrik request/response/notification zarfları |
| `initialize` handshake | "Capability negotiation" | İlk mesaj çifti; sunucular ve client'lar destekledikleri feature'ları bildirir |
| `tools/list` | "Discovery" | Client sunucudan mevcut tool kümesini ister |
| `tools/call` | "Invocation" | Client sunucudan argümanlarla bir tool yürütmesini ister |
| `notifications/*_changed` | "Mutasyon event'leri" | Sunucu client'a primitive listesinin değiştiğini söyler |
| Content bloğu | "Tipli sonuç" | Tool sonucunda `{type: "text" | "image" | "resource" | "ui_resource"}` |
| SEP | "Spec Evolution Proposal" | İsimlendirilmiş taslak öneri (örn. async Tasks için SEP-1686) |

## İleri Okuma

- [Model Context Protocol — Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — kanonik spec dokümanı
- [Model Context Protocol — Architecture concepts](https://modelcontextprotocol.io/docs/concepts/architecture) — altı-primitive zihinsel modeli
- [Anthropic — Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) — Kasım 2024 launch yazısı
- [MCP blog — First MCP anniversary](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/) — bir yıllık retrospektif ve 2025-11-25 spec değişiklikleri
- [WorkOS — MCP 2025-11-25 spec update](https://workos.com/blog/mcp-2025-11-25-spec-update) — SEP-1686, 1036, 1577, 835 ve 1724 özeti
