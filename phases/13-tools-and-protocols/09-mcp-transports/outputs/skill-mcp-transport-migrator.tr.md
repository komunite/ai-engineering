---
name: mcp-transport-migrator
description: Legacy HTTP+SSE'den session id sürekliliği ve Origin doğrulamasıyla Streamable HTTP'ye geçiş planı üret.
version: 1.0.0
phase: 13
lesson: 09
tags: [mcp, streamable-http, sse-migration, session-id, origin]
---

Mevcut bir HTTP+SSE (legacy) MCP server verildiğinde, tek endpoint'li Streamable HTTP'ye geçiş planı üret.

Şunları üret:

1. Endpoint yeniden yazımı. `/messages` ve `/sse`'yi tek bir `/mcp`'de birleştir. POST'u request handling'e, GET'i SSE stream'ine, DELETE'i oturum sonlandırmaya eşle.
2. Oturum sürekliliği. İlk POST'ta yeni `Mcp-Session-Id` üret. Client tarafından sağlanan id'leri reddet. Client önce legacy bir oturum cookie'si gönderirse köprüleme mantığını koru.
3. Origin doğrulaması. Açık production origin'leri allowlist'le (`https://app.company.com`, `https://claude.ai`, localhost varyantları). Diğerlerini 403 ile reddet.
4. Last-event-id replay. Reconnect'lerin devam edebilmesi için oturum başına son event'lerin halka tamponunu tut.
5. Deprecation penceresi. Cut-over tarihini ve legacy endpoint'lerin yeni olana 301 ile uyarı header'ı ile yönlendirildiği 60 günlük grace period'u belgele.

Sert retler:
- Her iki endpoint'i süresiz olarak ayakta tutan herhangi bir plan. Legacy SSE 2026'da kaldırılıyor.
- Oturum id'lerinin client tarafından üretildiği herhangi bir plan. Kriptografik rastgelelik gereksinimini bozar.
- Origin doğrulaması olmayan herhangi bir plan. DNS rebinding zafiyeti.

Reddetme kuralları:
- Server sadece yereldeyse (stdio), HTTP'ye geçişi reddet; yerel için stdio doğrudur.
- Server henüz OAuth göndermiyorsa, herkese açmadan önce Phase 13 · 16'yı tamamla.
- Hosting hedefi uzun ömürlü HTTP'yi desteklemiyorsa (örneğin Vercel free tier), reddet ve Cloudflare Workers öner.

Çıktı: endpoint değişiklikleri, Origin allowlist'i, oturum id planı, deprecation takvimi ve initialize, tools/list, streaming notification'lar, last-event-id ile reconnect ve açık DELETE'i kapsayan bir test checklist'i içeren bir geçiş runbook'u.
