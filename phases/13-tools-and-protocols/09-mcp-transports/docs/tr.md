# MCP Transport'ları — stdio vs Streamable HTTP vs SSE Migration

> stdio locally çalışır, başka hiçbir yerde değil. Streamable HTTP (2025-03-26) uzak standarttır. Eski HTTP+SSE transport'u deprecate ediliyor ve 2026 ortasında kaldırılıyor. Yanlış transport seçmek bir migration maliyeti çıkarır; doğrusunu seçmek session sürekliliği ve DNS-rebinding korumalı uzak-hostlanabilir bir MCP sunucusu satın alır.

**Tür:** Öğrenim
**Diller:** Python (stdlib, Streamable HTTP endpoint iskeleti)
**Ön koşullar:** Faz 13 · 07, 08 (MCP sunucusu ve client'ı)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Deployment şekline (local vs remote, single-process vs fleet) dayanarak stdio ve Streamable HTTP arasında seçim yap.
- Streamable HTTP single-endpoint desenini implemente et: request'ler için POST, session stream için GET.
- DNS-rebinding'i yenmek için `Origin` doğrulama ve session-id semantiğini zorla.
- 2026 ortası kaldırma deadline'larından önce bir legacy HTTP+SSE sunucusunu Streamable HTTP'ye migrate et.

## Sorun

İlk MCP uzak transport'u (2024-11) HTTP+SSE'ydi: iki endpoint, biri client'ın POST'ları için ve sunucudan-client'a stream için bir Server-Sent-Events kanalı. Çalıştı. Ayrıca hantaldı: session başına iki endpoint, bazı CDN'lerin önünde bozuk cache'ler ve bazı WAF'ların agresif şekilde sonlandırdığı uzun-ömürlü SSE bağlantılarına sert bir bağımlılık.

2025-03-26 spec'i onu Streamable HTTP ile değiştirdi: tek endpoint, client request'leri için POST, bir session stream'i kurmak için GET, ikisi de bir `Mcp-Session-Id` header'ı paylaşıyor. O zamandan beri inşa edilen ya da migrate edilen her sunucu Streamable HTTP kullanıyor. Eski SSE modu deprecate ediliyor — Atlassian Rovo 30 Haziran 2026'da kaldırdı; Keboola 1 Nisan 2026'da; kalan enterprise sunucuların çoğu 2026 sonuna kadar.

Ve stdio local sunucular için hâlâ önemli. Claude Desktop, VS Code ve her IDE-şekilli client sunucuları stdio üzerinden doğurur. Doğru zihinsel model: "bu makine" için stdio, "network üzerinde" için Streamable HTTP. Çapraz geçiş yok.

## Kavram

### stdio

- Child-process transport. Client sunucuyu doğurur, stdin/stdout üzerinden iletişim kurar.
- Satır başına bir JSON objesi. Newline-delimited.
- Session id yok; process kimliği session'dır.
- Auth gerekmez (child parent'in güven sınırını miras alır).
- Uzak sunucular için asla kullanma — tünellemek için SSH ya da socat gerekir, o noktada Streamable HTTP kullan.

### Streamable HTTP

Tek endpoint `/mcp` (ya da herhangi bir yol). Üç HTTP method'u destekler:

- **POST /mcp.** Client bir JSON-RPC mesajı gönderir. Sunucu ya tek bir JSON yanıt ya da bir-ya-da-daha-fazla yanıtın SSE stream'i ile yanıt verir (batched response'lar ve o request'le ilgili notification'lar için yararlı).
- **GET /mcp.** Client uzun-ömürlü bir SSE kanalı açar. Sunucu bunu sunucudan-client'a request'ler için (sampling, notification'lar, elicitation) kullanır.
- **DELETE /mcp.** Client session'ı açıkça sonlandırır.

Session'lar, sunucunun ilk yanıtta ayarladığı ve client'ın sonraki her request'te echo ettiği `Mcp-Session-Id` header'ı ile tanımlanır. Session id'leri kriptografik olarak random OLMALIDIR (128+ bit); client-seçimi id'ler güvenlik için reddedilir.

### Single endpoint vs iki

Eski spec'ten iki-endpoint mod 2026'da hâlâ çağrılabilir — spec bunu "legacy compatible" olarak bildirir. Ama tüm yeni sunucular single-endpoint olmalıdır. Resmi SDK'lar single-endpoint yayar; legacy mod'u yalnızca migrate edilmemiş bir uzakla konuşurken kullan.

### `Origin` doğrulama ve DNS-rebinding

Tarayıcılar MCP client değildir (bugün), ama bir saldırgan bir tarayıcıyı `localhost:1234/mcp`'ye POST etmeye ikna eden bir web sayfası hazırlayabilir — kullanıcının local MCP sunucusunun dinlediği yer. Sunucu `Origin`'i kontrol etmezse, tarayıcının same-origin policy'si onu kurtarmaz çünkü `Origin: http://evil.com` geçerli cross-origin'dir.

2025-11-25 spec'i sunucuların `Origin`'i bir allowlist'te olmayan request'leri reddetmesini gerektirir. Allowlist tipik olarak MCP client host'unu (`https://claude.ai`, `vscode-webview://*`) ve local UI'lar için localhost varyantlarını içerir.

### Session id lifecycle'ı

1. Client `Mcp-Session-Id` olmadan ilk request'i gönderir.
2. Sunucu random bir id atar, yanıt header'ında `Mcp-Session-Id` ayarlar.
3. Client o header'ı sonraki tüm request'lerde ve stream için `GET /mcp`'de echo eder.
4. Session sunucu tarafından iptal edilebilir; client sonraki request'lerde 404 görür ve yeniden initialize etmelidir.
5. Client temiz shutdown için session'ı açıkça DELETE edebilir.

### Keepalive ve reconnect

SSE bağlantıları düşer. Client aynı `Mcp-Session-Id` ile yeniden GET ederek yeniden kurar. Sunucu kesinti sırasında kaçırılan event'leri MUTLAKA queue'lar (makul bir pencereye kadar) ve client'ın echo ettiği `last-event-id` header'ı üzerinden tekrar oynatır.

Faz 13 · 13 Task'ları ele alır, bu da uzun süren işin tam bir session reconnect'inde bile hayatta kalmasını sağlar.

### Backwards compatibility probe

Hem eski hem yeni sunucuları desteklemek isteyen bir client:

1. `/mcp`'ye POST et.
2. Yanıt JSON ya da SSE ile `200 OK` ise, bu Streamable HTTP'dir.
3. Yanıt `Content-Type: text/event-stream` VE ikincil bir endpoint'e işaret eden bir `Location` header'ı ile `200 OK` ise, bu legacy HTTP+SSE; `Location`'ı takip et.

### Cloudflare, ngrok ve hosting

2026'daki üretim uzak MCP sunucuları Cloudflare Workers'da (MCP Agents SDK ile), Vercel Functions'ta ya da container'lı Node/Python'da çalışıyor. Anahtar: hosting'in SSE GET için uzun-ömürlü HTTP bağlantılarını desteklemeli. Vercel'in free tier'ı 10 saniyede sınırlar ve uygun değildir. Cloudflare Workers süresiz stream'leri destekler.

### Gateway kompozisyonu

Birden fazla MCP sunucusunun önüne bir gateway koyduğunda (Faz 13 · 17), gateway session id'leri yeniden yazan ve upstream'i multipleks eden tek bir Streamable HTTP endpoint'idir. Tool'lar gateway katmanında merge edilir; client tek bir mantıksal sunucu görür.

### Transport başarısızlık modları

- **stdio SIGPIPE.** Yazma ortasında child process ölümü SIGPIPE raise eder; sunucular temiz çıkmalıdır. Client'lar EOF'u algılamalı ve session'ı ölü olarak işaretlemelidir.
- **HTTP 502 / 504.** Cloudflare, nginx ve diğer proxy'ler upstream başarısızlığında bunları yayar. Streamable HTTP client'ları kısa bir backoff sonrası bir kez retry etmelidir.
- **SSE bağlantı kopması.** TCP RST, proxy timeout ya da client network değişikliği stream'i kapatır. Client devam etmek için `Mcp-Session-Id` ve opsiyonel `last-event-id` ile yeniden bağlanır.
- **Session revocation.** Sunucu bir session id'sini geçersiz kılar; client sonraki request'te 404 görür. Client yeniden handshake etmelidir.
- **Clock skew.** Client'taki Resource-TTL hesaplamaları sunucudan ayrılır. Client sunucu timestamp'lerini yetkili olarak kabul etmelidir.

### Streamable HTTP'yi ne zaman atlamalı

Bazı enterprise'lar MCP sunucularını kendi network'lerinde gRPC ya da message-queue transport'ları arkasında deploy eder. Bu non-standart — MCP'nin spec'i bunları formal olarak tanımlamaz. Gateway'ler MCP client'larına bir Streamable HTTP yüzeyi açabilirken dahili olarak gRPC kullanır. Dış yüzeyi spec-uyumlu tut; gateway çeviriyi sahiplenir.

## Kullan

`code/main.py` `http.server` (stdlib) kullanarak minimal bir Streamable HTTP endpoint implemente eder. `/mcp`'de POST, GET ve DELETE'i ele alır, ilk yanıtta `Mcp-Session-Id` ayarlar, `Origin`'i doğrular ve allowlist'te olmayan origin'lerden gelen request'leri reddeder. Handler, Ders 07'nin notes sunucusunun dispatch mantığını yeniden kullanır.

Bakılacak şeyler:

- POST handler JSON-RPC body'sini okur, dispatch eder ve bir JSON yanıt yazar (tek-yanıt varyantı; SSE varyantı yapısal olarak benzerdir).
- `Origin` kontrolü varsayılan `http://evil.example` probe'unu reddeder ama `http://localhost`'u kabul eder.
- Session id'leri random 128-bit hex string'leridir; sunucu session başına state'i bellekte tutar.

## Yayınla

Bu ders `outputs/skill-mcp-transport-migrator.md` üretir. Bir HTTP+SSE (legacy) MCP sunucusu verildiğinde, skill session-id sürekliliği, Origin kontrolleri ve backwards-uyumlu probe desteği ile Streamable HTTP'ye migration planı üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. `curl`'den bir `initialize` POST et ve `Mcp-Session-Id` yanıt header'ını gözlemle. Header'ı echo eden ikinci bir request POST et ve session sürekliliğini doğrula.

2. Bir SSE stream'i açan bir GET handler ekle. Her beş saniyede bir `notifications/progress` event'i gönder. Aynı session id ile yeniden GET ederek yeniden bağlan ve sunucunun kabul ettiğini doğrula.

3. `last-event-id` replay mantığını implemente et. Yeniden bağlanmada, o id'den sonra üretilen herhangi bir event'i tekrar oynat.

4. `Origin` doğrulamayı bir wildcard pattern (`https://*.example.com`) destekleyecek şekilde genişlet ve `https://app.example.com`'u kabul ettiğini ama `https://evil.example.com.attacker.net`'i reddettiğini doğrula.

5. Resmi registry'den legacy bir HTTP+SSE sunucusu al (birkaç tane var) ve migration'ı taslakla: endpoint handling'de, session id üretiminde ve header semantiğinde ne değişir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| stdio transport | "Local child process" | stdin/stdout üzerinde JSON-RPC, newline-delimited |
| Streamable HTTP | "Uzak transport" | Single-endpoint POST + GET + opsiyonel SSE, 2025-03-26 spec'i |
| HTTP+SSE | "Legacy" | 2026 ortasında kaldırılan iki-endpoint modeli |
| `Mcp-Session-Id` | "Session header'ı" | Sunucu-atanmış random id, sonraki her request'te echo'lanır |
| `Origin` allowlist | "DNS-rebinding savunması" | Origin'i onaylanmamış request'leri reddet |
| Single endpoint | "Tek URL" | `/mcp` tüm session operasyonları için POST / GET / DELETE'i ele alır |
| `last-event-id` | "SSE replay" | Düşen stream'i event kaçırmadan devam ettirmek için kullanılan header |
| Backwards-compat probe | "Eski vs yeni algılama" | Transport'u otomatik seçen client yanıt-şekli kontrolü |
| Long-lived HTTP | "SSE streaming" | Sunucu tek bir TCP bağlantısında dakikalarca ya da saatlerce event push eder |
| Session revocation | "Yeniden init zorla" | Sunucu bir session id'sini geçersizleştirir; client yeniden handshake etmelidir |

## İleri Okuma

- [MCP — Basic transports spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) — stdio ve Streamable HTTP için kanonik referans
- [MCP — Basic transports spec 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) — Streamable HTTP'yi tanıtan revizyon
- [Cloudflare — MCP transport](https://developers.cloudflare.com/agents/model-context-protocol/transport/) — Workers-hostlu Streamable HTTP desenleri
- [AWS — MCP transport mechanisms](https://builder.aws.com/content/35A0IphCeLvYzly9Sw40G1dVNzc/mcp-transport-mechanisms-stdio-vs-streamable-http) — deployment şekilleri arasında karşılaştırma
- [Atlassian — HTTP+SSE deprecation notice](https://community.atlassian.com/forums/Atlassian-Remote-MCP-Server/HTTP-SSE-Deprecation-Notice/ba-p/3205484) — somut migration deadline örneği
