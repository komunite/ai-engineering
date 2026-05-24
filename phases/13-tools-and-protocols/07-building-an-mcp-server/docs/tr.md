# Bir MCP Sunucusu İnşa Etmek — Python + TypeScript SDK'lar

> MCP tutorial'larının çoğu yalnızca stdio hello-world'leri gösterir. Gerçek bir sunucu tool'ları artı resource'ları artı prompt'ları açar, capability negotiation'ı ele alır, yapılandırılmış hatalar yayar ve SDK'lar arasında aynı şekilde çalışır. Bu ders bir notes sunucusunu end-to-end inşa eder: stdlib stdio transport, JSON-RPC dispatch, üç sunucu primitive'i ve mezun olduğunda Python SDK'sının FastMCP'sine ya da TypeScript SDK'sına oturan pure-function bir stil.

**Tür:** Yapım
**Diller:** Python (stdlib, stdio MCP sunucusu)
**Ön koşullar:** Faz 13 · 06 (MCP temelleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- `initialize`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list` ve `prompts/get` method'larını implemente et.
- stdin'den JSON-RPC mesajlarını okuyan ve stdout'a yanıtlar yazan bir dispatch döngüsü yaz.
- JSON-RPC 2.0 spec'i ve MCP'nin ek kodları başına yapılandırılmış hata yanıtları yay.
- Bir stdlib implementasyonunu tool mantığını yeniden yazmadan FastMCP'ye (Python SDK) ya da TypeScript SDK'ya mezun et.

## Sorun

Uzak bir transport (Faz 13 · 09) ya da bir auth katmanı (Faz 13 · 16) kullanabilmek için, temiz bir local sunucuya ihtiyacın var. Local stdio demektir: sunucu client tarafından bir child process olarak doğurulur, mesajlar stdin/stdout üzerinden newline-delimited akar.

2025-11-25 spec'i stdio mesajlarının açık `\n` ayırıcı ile JSON objeleri olarak kodlanmasını öngörür. Burada SSE yok; SSE eski uzak mod'du ve 2026 ortasında kaldırılıyor (Atlassian'ın Rovo MCP sunucusu 30 Haziran 2026'da deprecate etti; Keboola 1 Nisan 2026'da). Stdio için satır başına bir JSON objesi tüm wire formatı.

Bir notes sunucusu iyi bir şekildir çünkü üç sunucu primitive'inin hepsini egzersiz eder. Tool'lar mutation yapar (`notes_create`). Resource'lar veri açar (`notes://{id}`). Prompt'lar şablonlar yayınlar (`review_note`). Bu dersin şekli herhangi bir domain'e genelleşir.

## Kavram

### Dispatch döngüsü

```
loop:
  line = stdin.readline()
  msg = json.loads(line)
  if has id:
    handle request -> write response
  else:
    handle notification -> no response
```

Üç kural:

- JSON-RPC zarfı olmayan hiçbir şeyi stdout'a yazdırma. Debug log'ları stderr'e gider.
- Her request, aynı `id`'yi taşıyan bir response ile eşleştirilMELİDİR.
- Notification'lara yanıt VERİLMEMELİDİR.

### `initialize` implementasyonu

```python
def initialize(params):
    return {
        "protocolVersion": "2025-11-25",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"listChanged": True, "subscribe": False},
            "prompts": {"listChanged": False},
        },
        "serverInfo": {"name": "notes", "version": "1.0.0"},
    }
```

Yalnızca desteklediğini bildir. Client feature'ları gate'lemek için capability kümesine güvenir.

### `tools/list` ve `tools/call` implementasyonu

`tools/list`, her girdi `name`, `description`, `inputSchema`'ya sahip olacak şekilde `{tools: [...]}` döndürür. `tools/call` `{name, arguments}` alır ve `{content: [blocks], isError: bool}` döndürür.

Content blokları tiplidir. En yaygınları:

```json
{"type": "text", "text": "Found 2 notes"}
{"type": "resource", "resource": {"uri": "notes://14", "text": "..."}}
{"type": "image", "data": "<base64>", "mimeType": "image/png"}
```

Tool hataları iki şekilde gelir. Protokol-seviyesi hatalar (bilinmeyen method, kötü params) JSON-RPC hatalarıdır. Tool-seviyesi hatalar (geçerli çağrı ama tool başarısız oldu) `{content: [...], isError: true}` olarak döner. Bu, modelin başarısızlığı bağlamında görmesini sağlar.

### Resource implementasyonu

Resource'lar tasarımı gereği read-only'dir. `resources/list` bir manifest döndürür; `resources/read` içeriği döndürür. URI'lar `file://...`, `http://...` ya da `notes://` gibi custom bir şema olabilir.

Veriyi bir tool yerine resource olarak açtığında:

- Model onu "çağırmaz"; client kullanıcı isteği üzerine onu bağlama enjekte edebilir.
- Subscription'lar, resource değiştiğinde sunucunun güncellemeler push etmesine izin verir (Faz 13 · 10).
- Faz 13 · 14 bunu interaktif resource'lar için `ui://` ile genişletir.

### Prompt implementasyonu

Prompt'lar adlandırılmış argümanlı şablonlardır. Host onları slash-komutlar olarak yüzeyleştirir. Bir `review_note` prompt'u bir `note_id` argümanı alabilir ve client'ın modeline beslediği çok-mesajlı bir prompt template üretebilir.

### Stdio transport incelikleri

- Newline-delimited JSON. Length-prefixed framing yok.
- Buffer'lama. Her yazımdan sonra `sys.stdout.flush()`.
- Client ömrü kontrol eder. stdin kapandığında (EOF), temiz çık.
- SIGPIPE'ı sessizce ele alma; logla ve çık.

### Annotation'lar

Her tool, güvenlik özelliklerini tanımlayan `annotations` taşıyabilir:

- `readOnlyHint: true` — pure read, retry için güvenli.
- `destructiveHint: true` — geri alınamaz side effect'ler; client onaylamalı.
- `idempotentHint: true` — aynı input'lar aynı çıktıları üretir.
- `openWorldHint: true` — dış sistemlerle etkileşir.

Client bunları UX'i (onay diyalogları, status indicator'ları) ve routing'i (Faz 13 · 17) belirlemek için kullanır.

### Mezuniyet yolu

`code/main.py`'daki stdlib sunucu yaklaşık 180 satırdır. FastMCP (Python) aynı mantığı decorator-style'a çöker:

```python
from fastmcp import FastMCP
app = FastMCP("notes")

@app.tool()
def notes_search(query: str, limit: int = 10) -> list[dict]:
    ...
```

TypeScript SDK'sı eşdeğer bir şekle sahiptir. Mezuniyet yolu hazır olduğunda drop-in'dir; kavramlar (capability'ler, dispatch, content blokları) aynıdır.

## Kullan

`code/main.py` stdio üzerinden tam bir notes MCP sunucusudur, yalnızca stdlib. `initialize`, üç tool için (`notes_list`, `notes_search`, `notes_create`) `tools/list`, `tools/call`, her not için `resources/list` ve `resources/read` ve bir `review_note` prompt'u ele alır. JSON-RPC mesajlarını pipe'layarak onu sürebilirsin:

```
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python main.py
```

Bakılacak şeyler:

- Dispatcher method ismi ile keyed bir `dict[str, Callable]`.
- Her tool executor, çıplak bir string değil, bir content blokları listesi döndürür.
- Executor raise ettiğinde `isError: true` ayarlanır.

## Yayınla

Bu ders `outputs/skill-mcp-server-scaffolder.md` üretir. Bir domain verildiğinde (notes, tickets, files, database), skill doğru tools / resources / prompts bölümlemesi ve SDK mezuniyet yolu ile bir MCP sunucusunu scaffold eder.

## Alıştırmalar

1. `code/main.py`'ı çalıştır ve onu elle inşa edilmiş JSON-RPC mesajlarıyla sür. `notes_create`'i, sonra yeni notu almak için `resources/read`'i egzersiz et.

2. `annotations: {destructiveHint: true}` ile bir `notes_delete` tool'u ekle. Client'ın bir onay diyaloğu yüzeyleştireceğini doğrula (bu gerçek bir host gerektirir; Claude Desktop çalışır).

3. Sunucunun bir not değiştirildiğinde `notifications/resources/updated` push etmesi için `resources/subscribe` implemente et. Bir keepalive task ekle.

4. Sunucuyu FastMCP'ye port et. Python dosyası 80 satırın altına düşmeli. Wire davranışı aynı olmalıdır; aynı JSON-RPC test harness'ı ile doğrula.

5. Spec'in `server/tools` bölümünü oku ve bu dersin sunucusunda implemente edilmemiş bir tool tanımı alanını tanımla. (İpucu: birkaç tane var; birini seç ve ekle.)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MCP sunucusu | "Tool'ları açan şey" | stdio ya da HTTP üzerinde MCP JSON-RPC konuşan process |
| stdio transport | "Child process modeli" | Sunucu client tarafından doğurulur; stdin/stdout üzerinden iletişim kurar |
| Dispatcher | "Method router" | JSON-RPC method isminden handler fonksiyonuna map |
| Content bloğu | "Tool result chunk" | Tool yanıtının `content` array'inde tipli element |
| `isError` | "Tool-seviyesi başarısızlık" | Tool'un başarısız olduğunu işaret eder; JSON-RPC hatasından ayırır |
| Annotation'lar | "Güvenlik ipuçları" | readOnly / destructive / idempotent / openWorld bayrakları |
| FastMCP | "Python SDK" | MCP protokolü üzerinde decorator-tabanlı yüksek-seviye framework |
| Resource URI | "Adreslenebilir veri" | Bir resource'u tanımlayan `file://`, `db://` ya da custom şema |
| Prompt template | "Slash-komut özet" | Host UI'leri için argüman slot'larıyla sunucu-tarafından sağlanan şablon |
| Capability declaration | "Feature toggle" | `initialize`'da bildirilen primitive başına bayraklar |

## İleri Okuma

- [Model Context Protocol — Python SDK](https://github.com/modelcontextprotocol/python-sdk) — referans Python implementasyonu
- [Model Context Protocol — TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) — paralel TS implementasyonu
- [FastMCP — server framework](https://gofastmcp.com/) — MCP sunucuları için decorator-style Python API
- [MCP — Quickstart server guide](https://modelcontextprotocol.io/quickstart/server) — her iki SDK'yı kullanan end-to-end tutorial
- [MCP — Server tools spec](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) — tools/* mesajları için tam referans
