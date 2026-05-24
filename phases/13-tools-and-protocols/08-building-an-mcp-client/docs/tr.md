# Bir MCP Client'ı İnşa Etmek — Discovery, Invocation, Session Management

> MCP içeriğinin çoğu sunucu tutorial'ları yayınlar ve client'a el sallar. Client kodu zor orkestrasyonun yaşadığı yerdir: process spawn'lama, capability negotiation, birden fazla sunucu boyunca tool list merge'leme, sampling callback'leri, yeniden bağlanma ve namespace collision çözümü. Bu ders, model için üç farklı MCP sunucusunu tek bir düz tool namespace'ine kaldıran çoklu-sunucu bir client inşa eder.

**Tür:** Yapım
**Diller:** Python (stdlib, çoklu-sunucu MCP client'ı)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu inşa etmek)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Bir MCP sunucusunu child process olarak doğur, `initialize`'ı tamamla ve bir `notifications/initialized` gönder.
- Sunucu başına session state'i (capability'ler, tool listesi, son görülen notification id'leri) sürdür.
- Çoklu sunucular boyunca tool listelerini collision handling ile tek bir namespace'e merge'le.
- Bir tool call'unu ona sahip olan sunucuya yönlendir ve yanıtı yeniden birleştir.

## Sorun

Gerçek bir agent host (Claude Desktop, Cursor, Goose, Gemini CLI) aynı anda birden fazla MCP sunucusu yükler. Bir kullanıcının aynı anda çalışan bir filesystem sunucusu, bir Postgres sunucusu ve bir GitHub sunucusu olabilir. Client'ın işi:

1. Her sunucuyu doğur.
2. Her birini bağımsız olarak handshake'le.
3. Her birinde `tools/list` çağır ve sonucu düzleştir.
4. Model `notes_search` yaydığında, onu birleştirilmiş namespace'de ara ve doğru sunucuya yönlendir.
5. Engellemeden herhangi bir sunucudan notification'ları (`tools/list_changed`) ele al.
6. Transport başarısızlığında yeniden bağlan.

Bunların hepsini elle yazmak "toy"u "kullanılabilir"den ayıran şeydir. Resmi SDK'lar bunu sarar ama zihinsel modelin senin olmalı.

## Kavram

### Child-process spawn'lama

`stdin=PIPE, stdout=PIPE, stderr=PIPE` ile `subprocess.Popen`. `bufsize=1` ayarla ve satır-satır okumalar için text mode kullan. Her sunucu bir process; client sunucu başına bir `Popen` handle tutar.

### Sunucu başına session state

Sunucu başına bir `Session` objesi şunları tutar:

- `process` — Popen handle.
- `capabilities` — sunucunun `initialize`'da bildirdiği.
- `tools` — son `tools/list` sonucu.
- `pending` — request id'sinden response'u bekleyen bir promise/future'a map.

Request'ler doğası gereği async'tir; sunucu B çağrı ortasındayken sunucu A'ya gönderilen bir `tools/call` bloklamamalıdır. Ya queue'lu thread'ler ya da asyncio kullan.

### Merged namespace

Client agrega tool listesini gördüğünde, isimler çakışabilir. İki sunucu da `search` açabilir. Client'ın üç seçeneği var:

1. **Sunucu adı ile prefix.** `notes/search`, `files/search`. Net ama çirkin.
2. **Sessiz first-come.** Sonraki sunucunun `search`'ü öncekini override eder. Riskli; collision'ları gizler.
3. **Collision reddi.** İkinci sunucuyu yüklemeyi reddet; kullanıcıyı bilgilendir. Güvenlik-hassas host'lar için en güvenli.

Claude Desktop sunucu-ile-prefix kullanır. Cursor net bir hatayla collision reddi kullanır. VS Code MCP de sunucu-ile-prefix benimser.

### Routing

Merge'den sonra, bir dispatch table'ı `tool_name -> session` map'ler. Model isim ile bir çağrı yayar; client session'ı bulur ve o sunucunun stdin'ine bir `tools/call` mesajı yazar, sonra response'u bekler.

### Sampling callback

Sunucu `initialize`'da `sampling` capability'sini bildirdiyse, client'tan LLM'ini çalıştırmasını isteyen `sampling/createMessage` gönderebilir. Client şunu yapmalıdır:

1. Örnek çözülene kadar o sunucuya daha fazla request'i blokla ya da implementation'ı eşzamanlılığı destekliyorsa pipeline'la.
2. LLM sağlayıcısını çağır.
3. Yanıtı sunucuya geri gönder.

Ders 11 sampling'i end-to-end ele alır. Bu ders bütünlük için onu stub'lar.

### Notification handling

`notifications/tools/list_changed`, `tools/list`'i yeniden çağırmak demektir. `notifications/resources/updated`, resource kullanımdaysa onu yeniden okumak demektir. Notification'lar yanıt üretmemelidir — onları ack'lemeye çalışma.

Yaygın bir client bug'ı: stream'de bir notification beklerken `tools/call` üzerinde okuma döngüsünü bloklamak. Her mesajı bir queue'ya push eden bir arka plan reader thread'i kullan; ana thread dequeue eder ve dispatch eder.

### Reconnection

Transport başarısız olabilir: sunucu çöktü, OS process'i öldürdü, stdio pipe kırıldı. Client stdout'ta EOF'u algılar ve session'ı ölü olarak işler. Seçenekler:

- Sunucuyu sessizce yeniden başlat ve yeniden handshake'le. Pure read-only sunucular için OK.
- Başarısızlığı kullanıcıya yüzeyleştir. Kullanıcıya görünür session'ları olan stateful sunucular için OK.

Faz 13 · 09 Streamable HTTP yeniden bağlanma semantiğini ele alır; stdio daha basittir.

### Keepalive ve session id

Streamable HTTP `Mcp-Session-Id` header'ı kullanır. Stdio'nun session id'si yoktur — process kimliği session'ın TA KENDİSİDİR. Keepalive ping'leri opsiyoneldir; stdio pipe'ları inactivity altında kırılmaz.

## Kullan

`code/main.py` üç simüle MCP sunucusunu subprocess olarak doğurur, her birini handshake'ler, tool listelerini merge'ler ve tool çağrılarını doğru olana yönlendirir. "Sunucular" aslında toy responder'lar çalıştıran diğer Python process'leridir (gerçek LLM yok). Şunu görmek için çalıştır:

- Üç initialization, her biri kendi capability kümesiyle.
- 7-tool'lu bir namespace'e merge'lenmiş üç `tools/list` sonucu.
- Tool ismine dayanan bir routing kararı.
- Namespace prefixing ile önlenen bir collision.

Bakılacak şeyler:

- `Session` dataclass'ı sunucu başına state'i temiz şekilde tutar.
- Arka plan reader thread'i stdout'taki her satırı ana thread'i bloklamadan dequeue eder.
- Dispatch table basit bir `dict[str, Session]`.
- Collision handling açık: iki sunucu aynı ismi bildirdiğinde, sonraki bir prefix ile yeniden adlandırılır.

## Yayınla

Bu ders `outputs/skill-mcp-client-harness.md` üretir. Bildirimsel bir MCP sunucu listesi (name, command, args) verildiğinde, skill onları doğuran, tool listelerini merge'leyen ve collision çözümlü bir routing fonksiyonu yayınlayan bir harness üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır ve sunucu spawn log'unu izle. Simüle sunucu process'lerinden birini SIGTERM ile öldür ve client'ın EOF'u nasıl algıladığını ve o session'ı ölü olarak işaretlediğini gözlemle.

2. Namespace prefixing'i implemente et. İki sunucu `search` açtığında, ikincisini `<server>/search` olarak yeniden adlandır. Dispatch table'ı güncelle ve tool çağrılarının doğru yönlendiğini doğrula.

3. Sunucu yeniden başlatma için bir connection-pool-style backoff ekle: ardışık başarısızlıklarda exponential backoff, 30 saniyede sınırla, üç başarısızlıktan sonra kullanıcıya bir notification yay.

4. 100 eşzamanlı MCP sunucusunu destekleyen bir client taslakla. Basit dispatch dict'i hangi veri yapısı değiştirir? (İpucu: prefix namespacing için trie, artı sunucu-başına-tool-sayısı için bir metric.)

5. Client'ı resmi MCP Python SDK'sına port et. SDK `stdio_client` ve `ClientSession`'ı sarar. Kod, çoklu-sunucu routing'i korurken ~200 satırdan ~40 satıra düşmelidir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MCP client | "Agent host" | Sunucuları doğuran ve tool çağrılarını orkestre eden process |
| Session | "Sunucu başına state" | Capability'ler, tool listesi ve pending-request defter tutma |
| Merged namespace | "Tek tool listesi" | Tüm aktif sunucular boyunca düz tool isimleri kümesi |
| Namespace collision | "İki sunucu aynı tool" | Client prefix'lemeli, reddetmeli ya da first-come uygulamalı |
| Routing | "Bu çağrıyı kim alır?" | Tool isminden sahip sunucuya dispatch |
| Background reader | "Non-blocking stdout" | Sunucu stdout'unu bir queue'ya boşaltan thread ya da task |
| Sampling callback | "LLM-as-a-service" | Sunucudan `sampling/createMessage` için client handler |
| `notifications/*_changed` | "Primitive değişti" | Client'ın yeniden keşfetmesi ya da yeniden okuması gerektiğinin sinyali |
| Reconnection policy | "Sunucu öldüğünde" | Transport başarısız olduğunda yeniden başlatma semantiği |
| Stdio session | "Process = session" | Session id yok; child process ömrü session'dır |

## İleri Okuma

- [Model Context Protocol — Client spec](https://modelcontextprotocol.io/specification/2025-11-25/client) — kanonik client davranışı
- [MCP — Quickstart client guide](https://modelcontextprotocol.io/quickstart/client) — Python SDK ile hello-world client tutorial
- [MCP Python SDK — client module](https://github.com/modelcontextprotocol/python-sdk) — referans `ClientSession` ve `stdio_client`
- [MCP TypeScript SDK — Client](https://github.com/modelcontextprotocol/typescript-sdk) — TS paraleli
- [VS Code — MCP in extensions](https://code.visualstudio.com/api/extension-guides/ai/mcp) — VS Code'un tek bir editör host'unda birden fazla MCP sunucusunu nasıl multipleks ettiği
