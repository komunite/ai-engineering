---
name: claude-agent-scaffold
description: Subagent'lar, lifecycle hook'ları, session store, MCP server bağlantısı ve W3C trace yayılımı ile bir Claude Agent SDK uygulamasını iskelele.
version: 1.0.0
phase: 14
lesson: 17
tags: [claude-agent-sdk, subagents, hooks, session-store, mcp]
---

Bir ürün alanı ve MCP server'lar listesi verildiğinde, bir Claude Agent SDK uygulamasını iskelele.

Üret:

1. Talimatlar, built-in tool erişimi (read_file, write_file, shell, grep, glob, web fetch) ve özel function tool'ları içeren ana agent tanımı.
2. Paralelleştirme ve context isolation için subagent spawner. Aksi takdirde orchestrator context bütçesini patlatacaksa kullan.
3. Kayıtlı lifecycle hook'ları: denetim için PreToolUse + PostToolUse, kurulum için SessionStart, teardown için SessionEnd, kural zorlaması için UserPromptSubmit (bkz. pro-workflow pattern'leri).
4. Subagent ağacını render etmek için `list_subkeys` bağlanmış session store (SQLite varsayılan).
5. Harici tool/resource yüzeyleri için MCP server bağlantısı.
6. Caller'dan gelen OTel span'lerinin CLI üzerinden devam etmesi için W3C trace context yayılımı.

Sert ret durumları:

- Tek-tool görevi için bir subagent spawn etmek. Subagent'lar paralelleştirme veya context isolation içindir; "tek bir read_file çağrısı" için değil.
- Senkron pahalı işlerle hook'lar. Hook'lar mikrosaniyelerden milisaniyelere olmalı. Uzun iş subagent'a aittir.
- Cascade-delete politikası olmayan session store'lar. Sahipsiz subagent session'ları depolamayı şişirir.

Reddetme kuralları:

- Ürün uzun süreli async iş gerektiriyorsa (saatlerden günlere), self-hosted SDK'yi reddet ve Claude Managed Agents'a yönlendir.
- Kullanıcı paylaşılan bir konuma `--session-mirror` isterse, reddet. Session transkriptleri PII taşır; kullanıcı başına şifrelenmiş depolamaya mirror et.
- Agent tool use olmadan UX için ham LLM streaming'e bağımlıysa, Agent SDK'yi reddet ve doğrudan Client SDK'yi öner.

Çıktı: `agent.py`, `tools.py`, `hooks.py`, `session.py`, subagent politikasını, hook registry'sini, session backend'ini, MCP bağlantılarını ve OTel bağlantısını açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: voice handoff'ları için Lesson 22, OTel span attribution için Lesson 23 veya ürün production runtime şekli gerektiriyorsa Lesson 18.
