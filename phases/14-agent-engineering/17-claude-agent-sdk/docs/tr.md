# Claude Agent SDK: Alt-Agent'lar ve Session Store

> Claude Agent SDK Claude Code harness'inin kütüphane formu. Built-in tool'lar, context isolation için alt-agent'lar, hook'lar, W3C trace propagation, session store pariteliği. Claude Managed Agents uzun-süren async iş için hosted alternatif.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 10 (Skill Library'leri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Anthropic Client SDK (raw API) ile Claude Agent SDK (harness şekli) arasındaki farkı açıkla.
- Alt-agent'ları açıkla — parallelization ve context isolation — ve ne zaman onlara uzanmalı.
- Python SDK'nın session store yüzeyini (`append`, `load`, `list_sessions`, `delete`, `list_subkeys`) ve `--session-mirror`'ın rolünü adlandır.
- Built-in tool'lar, izole context'li alt-agent spawn, lifecycle hook'lar ve session store'lu bir stdlib harness uygula.

## Sorun

Raw bir LLM API sana bir round-trip verir. Üretim agent'ı tool yürütmesi, MCP server'lar, lifecycle hook'lar, alt-agent spawn'ı, session kalıcılığı, trace propagation gerektirir. Claude Agent SDK bu şekli bir kütüphane olarak yayınlıyor — Claude Code'un kullandığı aynı harness, custom agent'lar için açığa çıkarılmış.

## Kavram

### Client SDK vs Agent SDK

- **Client SDK (`anthropic`).** Raw Messages API. Sen döngüyü, tool'ları, state'i sahiplenirsin.
- **Agent SDK (`claude-agent-sdk`).** Built-in tool yürütmesi, MCP bağlantıları, hook'lar, alt-agent spawn'ı, session store. Claude Code döngüsü bir kütüphane olarak.

### Built-in tool'lar

SDK kutudan 10+ tool yayar: file read/write, shell, grep, glob, web fetch, daha fazlası. Custom tool'lar standart tool-schema arayüzü üzerinden kayıt olur.

### Alt-agent'lar

Anthropic tarafından dokümante edilen iki amaç:

1. **Parallelization.** Bağımsız işi eşzamanlı çalıştır. "Bu 20 modülün her biri için test dosyasını bul" 20 paralel alt-agent task'ı.
2. **Context isolation.** Alt-agent'lar kendi context window'larını kullanır; yalnızca sonuçlar orchestrator'a döner. Orchestrator'ın bütçesi korunur.

Python SDK son eklemeler: alt-agent transkriptlerini okumak için `list_subagents()`, `get_subagent_messages()`.

### Session store

TypeScript ile protocol pariteliği:

- `append(session_id, message)` — tur ekle.
- `load(session_id)` — konuşmayı restore et.
- `list_sessions()` — listele.
- `delete(session_id)` — alt-agent session'larına cascade ile.
- `list_subkeys(session_id)` — alt-agent anahtarlarını listele.

`--session-mirror` (CLI flag) transkripti stream ederken bir dış dosyaya yansıtır, debug için.

### Hook'lar

Register edebileceğin lifecycle hook'lar:

- `PreToolUse`, `PostToolUse` — tool çağrılarını kapı ya da audit et.
- `SessionStart`, `SessionEnd` — kur ve sök.
- `UserPromptSubmit` — model görmeden önce kullanıcı input'una aksiyon al.
- `PreCompact` — context kompaksiyondan önce çalıştır.
- `Stop` — agent çıkışında temizlik.
- `Notification` — yan kanal uyarıları.

Hook'lar pro-workflow (Faz 14 müfredat referansı) ve benzer sistemlerin cross-cutting davranış ekleme yolu.

### W3C trace context

Çağıranda aktif OTel span'leri W3C trace context header'ları üzerinden CLI subprocess'e propagate olur. Tüm çoklu-süreç trace'i backend'inde tek bir trace olarak görünür.

### Claude Managed Agents

Hosted alternatif (beta header `managed-agents-2026-04-01`). Uzun-süren async iş, built-in prompt caching, built-in kompaksiyon. Yönetilen altyapı için kontrolü takas et.

### Bu desen nerede ters gider

- **Alt-agent over-spawn.** 100 minik task için 100 alt-agent spawn etmek. Overhead baskın olur. Yerine batch yap.
- **Hook creep.** Her ekip hook ekler; başlangıç zamanı şişer. Hook'ları üç ayda bir gözden geçir.
- **Session bloat.** Session'lar birikir; boyut büyür. `list_sessions` + expiry policy kullan.

## İnşa Et

`code/main.py` SDK şeklini stdlib'de uyguluyor:

- Built-in `read_file`, `write_file`, `list_dir`'li `Tool`, `ToolRegistry`.
- `Subagent` — özel context, izole koşu, döndürülen sonuçlar.
- `SessionStore` — append, load, list, delete, list_subkeys.
- `Hooks` — `pre_tool_use`, `post_tool_use`, `session_start`, `session_end`.
- Demo: main agent paralel 3 alt-agent (her biri izole) spawn eder, sonuçları toplar, session'ı persist eder.

Çalıştır:

```
python3 code/main.py
```

Trace alt-agent context isolation'ı (orchestrator context boyutu sınırlı kalır), hook yürütmesini ve session kalıcılığını gösterir.

## Kullan

- **Claude Agent SDK** Claude Code harness şekli isteyen Claude-first ürünler için.
- **Claude Managed Agents** hosted uzun-süren async iş için.
- **OpenAI Agents SDK** (Ders 16) OpenAI-first karşılıkları için.
- **LangGraph + custom tool'lar** graph-şekilli state machine istediğinde.

## Yayınla

`outputs/skill-claude-agent-scaffold.md` alt-agent'lar, hook'lar, session store, MCP server attachment ve W3C trace propagation ile bir Claude Agent SDK uygulamasını iskeler.

## Alıştırmalar

1. 20 task'ı 5 paralel alt-agent gruplarına batch'leyen bir alt-agent spawner ekle. Orchestrator context boyutunu task-başına-bir'e karşı ölç.
2. `write_file` çağrılarını rate-limit'leyen bir `PreToolUse` hook uygula (session başına dakikada 5). Davranışı trace et.
3. `list_subkeys`'i bir alt-agent tree'sini render etmeye kablola. Derin nesting neye benzer?
4. Oyuncağı gerçek `claude-agent-sdk` Python paketine taşı. Tool registration hakkında ne değişir?
5. Claude Managed Agents dokümanlarını oku. Self-hosted'tan managed'e ne zaman geçersin?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Agent SDK | "Bir kütüphane olarak Claude Code" | Harness şekli: tool'lar, MCP, hook'lar, alt-agent'lar, session store |
| Subagent | "Child agent" | Ayrı context, kendi bütçesi; sonuçlar yukarı çıkar |
| Session store | "Konuşma DB'si" | Alt-agent cascade ile turları persist et, yükle, listele, sil |
| Hook | "Lifecycle callback" | Pre/post tool, session, prompt submit, compact, stop |
| W3C trace context | "Cross-process trace" | Parent span CLI subprocess'e propagate olur |
| Managed Agents | "Hosted harness" | Anthropic-hosted uzun-süren async iş |
| `--session-mirror` | "Transcript mirror" | Session turlarını stream ederken bir dış dosyaya yazar |
| MCP server | "Tool yüzey" | Agent'a iliştirilmiş dış tool/resource kaynağı |

## İleri Okuma

- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — Claude Code'un kütüphane formu
- [Anthropic, Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — üretim desenleri
- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) — hosted alternatif
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — karşılık
