# MCP Apps — `ui://` Üzerinden İnteraktif UI Resource'ları

> Yalnızca-text tool çıktısı agent'ların gösterebileceğini sınırlar. MCP Apps (SEP-1724, 26 Ocak 2026 resmi), bir tool'un Claude Desktop, ChatGPT, Cursor, Goose ve VS Code'da inline render edilen sandbox'lanmış interaktif HTML döndürmesine izin verir. Dashboard'lar, formlar, haritalar, 3D sahneler, hepsi tek bir uzantı üzerinden. Bu ders `ui://` resource şemasını, `text/html;profile=mcp-app` MIME'ını, iframe-sandbox postMessage protokolünü ve bir sunucunun HTML render etmesine izin vermenin getirdiği güvenlik yüzeyini gezer.

**Tür:** Yapım
**Diller:** Python (stdlib, UI resource emitter), HTML (örnek uygulama)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu), Faz 13 · 10 (resource'lar)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Bir tool çağrısından `ui://` resource döndür ve doğru MIME ve metadata ayarla.
- Bir tool'un ilişkili UI'sını `_meta.ui.resourceUri`, `_meta.ui.csp` ve `_meta.ui.permissions` ile bildir.
- UI-host iletişimi için iframe sandbox postMessage JSON-RPC'sini implemente et.
- UI-kökenli saldırılara karşı savunan CSP ve permissions-policy varsayılanlarını uygula.

## Sorun

2025-dönemi bir `visualize_timeline` tool'u "İşte 14 not kronolojik olarak organize edildi: ..." döndürebilir. Bu bir paragraf. Kullanıcılar aslında interaktif timeline istiyor. MCP Apps'ten önce, seçenekler şunlardı: client'a özgü widget API'leri (Claude artifact'ları, OpenAI Custom GPT HTML) ya da hiç UI yok.

MCP Apps (SEP-1724, 26 Ocak 2026'da yayınlandı) sözleşmeyi standartlaştırır. Bir tool sonucu URI'si `ui://...` ve MIME'i `text/html;profile=mcp-app` olan bir `resource` içerir. Host onu sınırlı CSP'li ve açıkça verilmediği sürece network erişimi olmayan bir sandbox'lı iframe'de render eder. Iframe içindeki UI host'a ufak bir postMessage JSON-RPC dialect'i üzerinden mesaj post eder.

Her uyumlu client (Claude Desktop, ChatGPT, Goose, VS Code) aynı `ui://` resource'unu aynı şekilde render eder. Bir sunucu, bir HTML bundle, evrensel UI.

## Kavram

### `ui://` resource şeması

Bir tool döndürür:

```json
{
  "content": [
    {"type": "text", "text": "Here is your notes timeline:"},
    {"type": "ui_resource", "uri": "ui://notes/timeline"}
  ],
  "_meta": {
    "ui": {
      "resourceUri": "ui://notes/timeline",
      "csp": {
        "defaultSrc": "'self'",
        "scriptSrc": "'self' 'unsafe-inline'",
        "connectSrc": "'self'"
      },
      "permissions": []
    }
  }
}
```

Host sonra `ui://notes/timeline` URI'sinde `resources/read` çağırır ve şunu geri alır:

```json
{
  "contents": [{
    "uri": "ui://notes/timeline",
    "mimeType": "text/html;profile=mcp-app",
    "text": "<!doctype html>..."
  }]
}
```

### Iframe sandbox

Host HTML'yi şu özelliklerle sandbox'lanmış bir `<iframe>` içinde render eder:

- `sandbox="allow-scripts allow-same-origin"` (ya da sunucu bildirimine göre daha sıkı)
- Response header'ları üzerinden uygulanan sunucu-bildirilmiş CSP.
- Cookie yok, host'un origin'inden localStorage yok.
- CSP'deki `connectSrc` ile sınırlı network erişimi.

### postMessage protokolü

Iframe host ile `window.postMessage` üzerinden iletişim kurar. Ufak bir JSON-RPC 2.0 dialect'i:

`targetOrigin`'i her zaman peer'ın tam origin'ine pinle ve alıcı tarafta `event.origin`'i herhangi bir payload'u işlemeden önce bir allowlist'e karşı doğrula. Bu kanalın iki tarafı için de asla `"*"` kullanma — body tool çağrılarını ve resource read'lerini taşır.

```js
// iframe to host  (pin to host origin)
window.parent.postMessage({
  jsonrpc: "2.0",
  id: 1,
  method: "host.callTool",
  params: { name: "notes_update", arguments: { id: "note-14", title: "..." } }
}, "https://host.example.com");

// host to iframe  (pin to iframe origin)
iframe.contentWindow.postMessage({
  jsonrpc: "2.0",
  id: 1,
  result: { content: [...] }
}, "https://iframe.example.com");

// receiver on both sides
window.addEventListener("message", (event) => {
  if (event.origin !== "https://expected-peer.example.com") return;
  // safe to process event.data
});
```

UI'nin çağırabildiği mevcut host-tarafı method'lar:

- `host.callTool(name, arguments)` — bir sunucu tool'unu çağırır.
- `host.readResource(uri)` — bir MCP resource'u okur.
- `host.getPrompt(name, arguments)` — bir prompt template'i fetch eder.
- `host.close()` — UI'ı kapatır.

Her çağrı hâlâ MCP protokolünden geçer ve sunucunun izinlerini miras alır.

### İzinler

`_meta.ui.permissions` listesi ekstra capability'ler talep eder:

- `camera` — kullanıcının kamerasına erişim (scan-a-document UI'lar için kullanılır).
- `microphone` — ses input'u.
- `geolocation` — konum.
- `network:*` — yalnızca `connectSrc`'nin izin verdiğinden daha geniş network erişimi.

Her izin, UI render olmadan önce kullanıcının gördüğü bir prompt'tur.

### Güvenlik riskleri

Iframe içindeki HTML hâlâ HTML'dir. Yeni saldırı yüzeyi:

- **UI üzerinden prompt-injection.** Kötü niyetli bir sunucu UI'sı sistem mesajı gibi görünen text gösterebilir ve kullanıcıyı kandırabilir. Host rendering sunucu UI'sını host UI'sından görsel olarak ayırt etmelidir.
- **`connectSrc` üzerinden exfiltration.** CSP `connect-src: *` izin verirse, UI veriyi herhangi bir yere gönderebilir. Varsayılan sıkı olmalıdır.
- **Clickjacking.** UI host chrome'unun üstüne biner. Host'lar z-index manipülasyonunu önlemeli ve opacity kurallarını zorlamalıdır.
- **Focus çalma.** UI klavye focus'unu alır ve sonraki mesajı yakalar. Host'lar müdahale etmelidir.

Faz 13 · 15 MCP güvenliğinin parçası olarak bunları derinlemesine ele alır; bu ders onları tanıtır.

### `ui/initialize` handshake

Iframe yüklendikten sonra, postMessage üzerinden `ui/initialize` gönderir:

```json
{"jsonrpc": "2.0", "id": 0, "method": "ui/initialize",
 "params": {"theme": "dark", "locale": "en-US", "sessionId": "..."}}
```

Host capability'ler ve bir session token ile yanıt verir. UI session token'ı sonraki her host çağrısında kullanır.

### AppRenderer / AppFrame SDK primitive'leri

ext-apps SDK iki convenience primitive açar:

- `AppRenderer` (sunucu tarafı) — bir React / Vue / Solid component'i sarar ve doğru MIME ve metadata ile bir `ui://` resource yayar.
- `AppFrame` (client tarafı) — resource'u alır, iframe'i mount eder ve postMessage'a aracılık eder.

Bunları kullanabilir ya da HTML ve JSON-RPC'yi elle yazabilirsin.

### Ekosistem durumu

MCP Apps 26 Ocak 2026'da yayınlandı. Nisan 2026 itibarıyla client desteği:

- **Claude Desktop.** Ocak 2026'dan beri tam destek.
- **ChatGPT.** Apps SDK üzerinden tam destek (aynı alt MCP Apps protokolü).
- **Cursor.** Beta; ayarlardan etkinleştir.
- **VS Code.** Yalnızca Insider build'leri.
- **Goose.** Tam destek.
- **Zed, Windsurf.** Roadmap'te.

Üretimdeki sunucular: dashboard'lar, harita görselleştirmeleri, veri tabloları, chart builder'lar, sandbox IDE preview'ları.

## Kullan

`code/main.py` notes sunucusunu, bir `ui://notes/timeline` resource'u döndüren bir `visualize_timeline` tool'u ile genişletir, artı o URI'da SVG timeline'ı olan ufak ama tam bir HTML bundle döndüren bir `resources/read` handler'ı. HTML stdlib-template'lenmiştir — build system yok. postMessage JS yorumlarında taslaklanmıştır çünkü stdlib bir tarayıcıyı süremez.

Bakılacak şeyler:

- Tool yanıtındaki `_meta.ui` resourceUri, CSP, izinleri taşır.
- HTML network erişimi olmadan render olur; tüm veri inline'dır.
- JS `window.parent.postMessage` üzerinden `host.callTool` çağırır (belgelenmiş ama bu stdlib demosunda inert).

## Yayınla

Bu ders `outputs/skill-mcp-apps-spec.md` üretir. İnteraktif bir UI'dan yararlanacak bir tool verildiğinde, skill tam MCP Apps sözleşmesini üretir: `ui://` URI, CSP, izinler, postMessage entrypoint'leri ve bir güvenlik checklist'i.

## Alıştırmalar

1. `code/main.py`'ı çalıştır ve yayınlanan HTML'i incele. HTML'i doğrudan bir tarayıcıda aç; SVG'nin render olduğunu doğrula. Sonra UI'nin `host.callTool("notes_update", ...)`'ı çağırmak için kullanacağı postMessage sözleşmesini taslakla.

2. CSP'yi sıkılaştır: `'unsafe-inline'`'ı kaldır ve nonce-tabanlı bir script policy kullan. HTML üretim kodunda ne değişir?

3. Bir notu yerinde düzenlemek için bir form ile ikinci bir UI resource'u `ui://notes/editor` ekle. Kullanıcı submit ettiğinde, iframe `host.callTool("notes_update", ...)`'ı çağırır.

4. UI'nin saldırı yüzeyini denetle. Kötü niyetli bir sunucu nereye içerik enjekte edebilir? Iframe sandbox neye karşı savunur ve neye karşı savunmaz?

5. SEP-1724 spec'ini oku ve bu toy implementasyonun kullanmadığı MCP Apps SDK'sındaki bir capability'yi tanımla. (İpucu: component-seviyesi state sync.)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MCP Apps | "İnteraktif UI resource'ları" | 2026-01-26'da yayınlanan SEP-1724 uzantısı |
| `ui://` | "App URI şeması" | UI bundle'ları için resource şeması |
| `text/html;profile=mcp-app` | "MIME" | MCP App HTML için content-type |
| Iframe sandbox | "Render container'ı" | UI'nin CSP ve izinlerle tarayıcı sandbox'lanması |
| postMessage JSON-RPC | "UI-to-host wire" | Host çağrıları için ufak JSON-RPC-over-postMessage dialect'i |
| `_meta.ui` | "Tool-UI binding'i" | Bir tool sonucunu UI resource'una bağlayan metadata |
| CSP | "Content-Security-Policy" | Script'ler, network, style'lar için izin verilen kaynakları bildirir |
| AppRenderer | "Sunucu SDK primitive'i" | Bir framework component'ini `ui://` resource'una çevirir |
| AppFrame | "Client SDK primitive'i" | postMessage'a aracılık eden iframe mount helper'ı |
| `ui/initialize` | "Handshake" | UI'den host'a ilk postMessage |

## İleri Okuma

- [MCP ext-apps — GitHub](https://github.com/modelcontextprotocol/ext-apps) — referans implementasyon ve SDK
- [MCP Apps specification 2026-01-26](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx) — formal spec dokümanı
- [MCP — Apps extension overview](https://modelcontextprotocol.io/extensions/apps/overview) — yüksek-seviye dokümantasyon
- [MCP blog — MCP Apps launch](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/) — Ocak 2026 launch yazısı
- [MCP Apps API reference](https://apps.extensions.modelcontextprotocol.io/api/) — JSDoc-style SDK referansı
