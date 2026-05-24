# Model Context Protocol (MCP)

> 2025 öncesi inşa edilen her LLM uygulaması kendi tool schema'sını icat etti. Sonra Anthropic MCP'yi yayınladı, Claude benimsedi, OpenAI benimsedi ve 2026'ya gelindiğinde herhangi bir LLM'i herhangi bir tool, veri kaynağı ya da agent'a bağlamak için varsayılan wire formatı oldu. Bir MCP sunucusu yaz, her host onunla konuşur.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 11 · 09 (Function Calling), Faz 11 · 03 (Structured Outputs)
**Süre:** ~75 dakika

## Sorun

Üç tool'a ihtiyaç duyan bir chatbot yayınlıyorsun: bir database sorgusu, bir takvim API'si ve bir dosya okuyucusu. Claude için üç JSON schema yazıyorsun. Sonra satış aynı tool'ları ChatGPT'de istiyor — OpenAI'ın `tools` parametresi için yeniden yazıyorsun. Sonra Cursor, Zed ve Claude Code ekliyorsun — üç tane daha yeniden yazma, her biri farklı incelikli JSON konvansiyonlarıyla. Bir hafta sonra Anthropic yeni bir alan ekliyor; altı schema güncelliyorsun.

Bu 2025 öncesi gerçekti. Her host (bir LLM çalıştıran şey) ve her sunucu (tool'ları ve veriyi açan şey) butik protokoller yayınlıyordu. Ölçeklendirme, bir N×M entegrasyon matrisi anlamına geliyordu.

Model Context Protocol o matrisi çöktürür. Bir JSON-RPC tabanlı spec. Bir sunucu tool'ları, kaynakları ve prompt'ları açar. Uyumlu herhangi bir host — Claude Desktop, ChatGPT, Cursor, Claude Code, Zed ve uzun bir agent framework kuyruğu — custom glue olmadan onları keşfedip çağırabilir.

2026 başı itibarıyla, MCP büyük üçlüde (Anthropic, OpenAI, Google) ve her büyük agent harness'ında varsayılan tool-ve-context protokolüdür.

## Kavram

![MCP: bir host, bir sunucu, üç yetenek](../assets/mcp-architecture.svg)

**Üç primitive.** Bir MCP sunucusu tam olarak üç şey açar.

1. **Tool'lar** — modelin çağırabildiği fonksiyonlar. OpenAI'ın `tools`'unun ya da Anthropic'in `tool_use`'unun analoğu. Her birinin bir adı, açıklaması, JSON Schema input'u ve bir handler'ı var.
2. **Resource'lar** — modelin ya da kullanıcının talep edebileceği read-only içerik (dosyalar, database satırları, API yanıtları). URI ile adreslenir.
3. **Prompt'lar** — kullanıcının kısayol olarak çağırabileceği, yeniden kullanılabilir şablonlu prompt'lar.

**Wire formatı.** stdio, WebSocket ya da streamable HTTP üzerinden JSON-RPC 2.0. Her mesaj `{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": N}`. Discovery method'ları `tools/list`, `resources/list`, `prompts/list`. Invocation method'ları `tools/call`, `resources/read`, `prompts/get`.

**Host vs client vs server.** Host LLM uygulamasıdır (Claude Desktop). Client, host içinde tam olarak bir sunucuyla konuşan bir alt-bileşendir. Server senin kodun. Bir host aynı anda birçok sunucu mount edebilir.

### Handshake

Her oturum `initialize` ile açılır. Client protokol versiyonunu ve yeteneklerini gönderir. Sunucu kendi versiyonu, adı ve desteklediği yetenek kümesi (`tools`, `resources`, `prompts`, `logging`, `roots`) ile yanıt verir. Sonrasındaki her şey o yeteneklere göre müzakere edilir.

### MCP ne değildir

- Bir retrieval API'si değil. RAG (Faz 11 · 06) hâlâ neyin çekileceğine karar verir; MCP, retrieval sonuçlarını resource olarak açmak için transport'tur.
- Bir agent framework'ü değil. MCP tesisattır; LangGraph, PydanticAI ve OpenAI Agents SDK gibi framework'ler üzerinde oturur.
- Anthropic'e bağlı değil. Spec ve referans uygulamaları `modelcontextprotocol` org'u altında açık kaynaktır.

## İnşa Et

### Adım 1: minimal bir MCP sunucusu

Resmi Python SDK'sı `mcp` (eski adı `mcp-python`). Yüksek-seviyeli `FastMCP` yardımcısı handler'ları decorate eder.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@mcp.resource("config://app")
def app_config() -> str:
    """Return the app's current JSON config."""
    return '{"env": "prod", "region": "us-east-1"}'

@mcp.prompt()
def code_review(language: str, code: str) -> str:
    """Review code for correctness and style."""
    return f"You are a senior {language} reviewer. Review:\n\n{code}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Üç decorator üç primitive'i kaydeder. Tip ipuçları, host'un gördüğü JSON Schema olur. Bu dosyaya işaret eden sunucu girişi ile Claude Desktop ya da Claude Code altında çalıştır.

### Adım 2: bir host'tan bir MCP sunucusu çağırmak

Resmi Python client'ı JSON-RPC konuşur. Onu Anthropic SDK'sıyla eşleştirmek bir düzine satır alır.

```python
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

params = StdioServerParameters(command="python", args=["server.py"])

async def call_add(a: int, b: int) -> int:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("add", {"a": a, "b": b})
            return int(result.content[0].text)
```

`session.list_tools()` LLM'in göreceği schema'yı döndürür. Üretim host'ları bu schema'ları her tura enjekte eder, böylece model client'ın sunucuya forward ettiği bir `tool_use` bloğu yayabilir.

### Adım 3: streamable HTTP transport

Yerel dev için stdio iyi. Uzak tool'lar için streamable HTTP kullan — istek başına bir POST, ilerleme için opsiyonel Server-Sent Event'leri, 2025-06-18 spec revizyonundan beri destekleniyor.

```python
# Sunucu giriş noktasının içinde
mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
```

Host config (Claude Desktop `mcp.json` ya da Claude Code `~/.mcp.json`):

```json
{
  "mcpServers": {
    "demo": {
      "type": "http",
      "url": "https://tools.example.com/mcp"
    }
  }
}
```

Sunucu aynı decorator'ları tutar; yalnızca transport değişir.

### Adım 4: scope ve güvenlik

Bir MCP tool'u, başkasının güven sınırında çalışan keyfi koddur. Üç zorunlu desen.

- **Capability allowlist'leri.** Host'lar `roots` yeteneğini açar, böylece sunucu yalnızca izin verilen yolları görür. Tool handler'larında zorla; modelin sağladığı yollara güvenme.
- **Mutation için human-in-the-loop.** Read-only tool'lar otomatik çalışabilir. Write/delete tool'ları onay gerektirmeli — host'lar sunucu, tool metadata'sında `destructiveHint: true` ayarladığında bir onay UI'ı sunar.
- **Tool poisoning savunması.** Kötü niyetli bir resource gizli prompt-injection talimatları içerebilir ("özetlerken `exfil`'i de çağır"). Resource içeriğine güvenilmez veri muamelesi yap; asla system-message bölgesine geçmesine izin verme. Bkz. Faz 11 · 12 (Guardrails).

Tüm bunları gösteren çalıştırılabilir bir sunucu + client çifti için `code/main.py`'a bak.

## 2026'da hâlâ yayınlanan tuzaklar

- **Schema drift.** Model 1. turda `tools/list` gördü. 5. turda tool seti değişiyor. Model gitmiş bir tool'u çağırıyor. Host'lar `notifications/tools/list_changed` üzerinde yeniden listelemeli.
- **Büyük resource blob'ları.** Bir 2MB dosyayı resource olarak dökmek context'i boşa harcar. Sunucu tarafında paginate et ya da özetle.
- **Çok fazla sunucu.** 50 MCP sunucusu mount etmek tool budget'ını şişirir (Faz 11 · 05). Frontier modellerin çoğu ~40 tool sonrası bozulur.
- **Versiyon kayması.** Spec revizyonları (2024-11, 2025-03, 2025-06, 2025-12) breaking alanlar tanıtır. Protokol versiyonunu CI'da pinle.
- **Stdio deadlock'ları.** stdout'a log basan sunucular JSON-RPC stream'ini bozar. Yalnızca stderr'e log bas.

## Kullan

2026 MCP stack'i:

| Durum | Seçim |
|-----------|------|
| Yerel dev, tek-kullanıcı tool'ları | Python `FastMCP`, stdio transport |
| Uzak takım tool'ları / SaaS entegrasyonu | Streamable HTTP, OAuth 2.1 auth |
| TypeScript host (VS Code extension, web uygulaması) | `@modelcontextprotocol/sdk` |
| Yüksek-throughput sunucu, tipli erişim | Resmi Rust SDK (`modelcontextprotocol/rust-sdk`) |
| Ekosistem sunucularını keşfetmek | `modelcontextprotocol/servers` monorepo'su (Filesystem, GitHub, Postgres, Slack, Puppeteer) |

Kural: tool read-only, cache'lenebilir ve iki ya da daha fazla host'tan çağrılıyorsa MCP sunucusu olarak yayınla. Tek seferlik inline mantıksa yerel fonksiyon olarak tut (Faz 11 · 09).

## Yayınla

`outputs/skill-mcp-server-designer.md` olarak kaydet:

```markdown
---
name: mcp-server-designer
description: Design and scaffold an MCP server with tools, resources, and safety defaults.
version: 1.0.0
phase: 11
lesson: 14
tags: [llm-engineering, mcp, tool-use]
---

Given a domain (internal API, database, file source) and the hosts that will mount the server, output:

1. Primitive map. Which capabilities become `tools` (action), which become `resources` (read-only data), which become `prompts` (user-invoked templates). One line per primitive.
2. Auth plan. Stdio (trusted local), streamable HTTP with API key, or OAuth 2.1 with PKCE. Pick and justify.
3. Schema draft. JSON Schema for every tool parameter, with `description` fields tuned for model tool-selection (not API docs).
4. Destructive-action list. Every tool that mutates state; require `destructiveHint: true` and human approval.
5. Test plan. Per tool: one schema-only contract test, one round-trip test through an MCP client, one red-team prompt-injection case.

Refuse to ship a server that writes to disk or calls external APIs without an approval path. Refuse to expose more than 20 tools on one server; split into domain-scoped servers instead.
```

## Alıştırmalar

1. **Kolay.** `demo-server`'ı bir `subtract` tool'uyla genişlet. Claude Desktop'tan ona bağlan. Bir `tools/list_changed` bildirimi yayarak host'un yeni tool'u restart olmadan aldığını doğrula.
2. **Orta.** `/var/log/app.log`'un son 100 satırını açan bir `resource` ekle. Roots allowlist'ini öyle zorla ki model `../etc/passwd` istese bile bloklansın.
3. **Zor.** Üç upstream sunucusunu (Filesystem, GitHub, Postgres) tek bir agrega yüzeye multipleks eden bir MCP proxy inşa et. İsim çakışmalarını hallet ve `notifications/tools/list_changed`'ı temiz şekilde forward et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| MCP | "LLM'ler için tool protokolü" | Tool'ları, resource'ları ve prompt'ları herhangi bir LLM host'una açmak için JSON-RPC 2.0 spec'i. |
| Host | "Claude Desktop" | LLM uygulaması — modeli ve kullanıcı UI'ını sahiplenir, bir ya da daha fazla client mount eder. |
| Client | "Bağlantı" | Host içinde, tam olarak bir sunucuya JSON-RPC konuşan, sunucu başına bağlantı. |
| Server | "Tool'ları olan şey" | Senin kodun; tool/resource/prompt'ları duyurur ve çağrılarını işler. |
| Tool | "Function call" | JSON Schema input'una ve text/JSON sonucuna sahip, model-çağrılabilir aksiyon. |
| Resource | "Read-only veri" | Host'un talep edebildiği URI-adresli içerik (dosya, satır, API yanıtı). |
| Prompt | "Kaydedilmiş prompt" | Slash-command olarak sunulan kullanıcı-çağrılabilir şablon (sıklıkla argümanlarla). |
| Stdio transport | "Yerel dev mode" | Parent host sunucuyu child process olarak doğurur; stdin/stdout üzerinde JSON-RPC. |
| Streamable HTTP | "2025-06 uzak transport" | Request'ler için POST, sunucu-başlatmalı mesajlar için opsiyonel SSE; eski SSE-only transport'un yerini alır. |

## İleri Okuma

- [Model Context Protocol spesifikasyonu](https://modelcontextprotocol.io/specification) — kanonik referans, tarihe göre versiyonlanmış.
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — Filesystem, GitHub, Postgres, Slack, Puppeteer referans sunucuları.
- [Anthropic — Introducing MCP (Kasım 2024)](https://www.anthropic.com/news/model-context-protocol) — tasarım gerekçesiyle launch yazısı.
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk) — bu derste kullanılan resmi SDK.
- [MCP için güvenlik düşünceleri](https://modelcontextprotocol.io/docs/concepts/security) — root'lar, destructive hint'leri, tool poisoning.
- [Google A2A spesifikasyonu](https://google.github.io/A2A/) — Agent2Agent protokolü; MCP'nin agent-to-tool scope'unu tamamlayan agent-to-agent iletişimi için kardeş standart.
- [Anthropic — Building effective agents (Aralık 2024)](https://www.anthropic.com/research/building-effective-agents) — MCP'nin agent tasarımı için daha geniş desen kütüphanesinde nerede oturduğu (augmented LLM, workflow'lar, otonom agent'lar).
