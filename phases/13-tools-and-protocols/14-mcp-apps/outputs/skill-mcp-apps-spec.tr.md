---
name: mcp-apps-spec
description: İnteraktif bir UI resource'una ihtiyaç duyan bir tool için tam MCP Apps kontratı üret.
version: 1.0.0
phase: 13
lesson: 14
tags: [mcp, apps, ui-resources, csp, iframe-sandbox]
---

İnteraktif bir UI'dan yararlanabilecek bir tool (timeline, form, dashboard, harita, chart) verildiğinde, MCP Apps kontratını üret.

Şunları üret:

1. `ui://` URI. UI resource için tek bir canonical name (örneğin `ui://notes/timeline`).
2. Tool sonuç şekli. `text` preamble ve `ui_resource` block içeren `content[]`; `_meta.ui` doldurulmuş.
3. CSP. `default-src`, `script-src`, `connect-src`, `img-src`, `style-src` için minimum allowlist. Gerekmedikçe `'unsafe-inline'`'dan kaçın.
4. İzinler listesi. Gerekiyorsa kamera / mikrofon / geolocation / network; gerekmiyorsa boş.
5. postMessage giriş noktaları. UI'nın yapacağı `host.*` çağrıları ve ne döndürdükleri.
6. Güvenlik checklist'i. Host'tan ayırt edilebilirlik, clickjacking yok, strict connect-src, herhangi bir kullanıcı içeriği render ediliyorsa HTML sanitization.

Sert retler:
- `default-src *` ile CSP. Tamamen açık güvenlik riski.
- UI'nın gerçekten kullandığının ötesinde herhangi bir `permissions` isteği. Minimum ayrıcalık.
- Dış scriptler yükleyen herhangi bir ui:// resource. Bundle et ya da reddet.
- Sanitization olmadan kullanıcı kontrollü HTML render eden herhangi bir UI. XSS vektörü.

Reddetme kuralları:
- UI sadece statik bir sonuçsa, App iskelemeyi reddet; text content döndür.
- Tool native host widget'larından (progress bar'lar, onay diyalogları) yararlanabilecekse, onları öner.
- Host henüz MCP Apps'i desteklemiyorsa (VS Code stable, Zed, 2026-04 itibarıyla Windsurf), text'e fallback yolunu işaretle.

Çıktı: `ui://` URI, tool sonuç JSON'u, CSP, izinler, postMessage giriş noktaları ve güvenlik checklist'i içeren tek sayfalık bir kontrat. Bu UI'yı render edecek minimum host'la ilgili tek bir cümleyle bitir.
