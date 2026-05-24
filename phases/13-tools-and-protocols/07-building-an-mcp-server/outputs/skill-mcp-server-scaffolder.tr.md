---
name: mcp-server-scaffolder
description: Domain'e özgü bir MCP server'ı doğru tool/resource/prompt ayrımı ve SDK mezuniyet yoluyla iskelele.
version: 1.0.0
phase: 13
lesson: 07
tags: [mcp, server, fastmcp, scaffold]
---

Bir domain (notes, ticket'lar, dosyalar, veritabanı, ne olursa olsun) verildiğinde, bir MCP server planı üret: hangi kabiliyetler tool olarak, hangileri resource olarak, hangileri prompt olarak açılır, ayrıca Python ya da TypeScript SDK'ye mezuniyet yolu.

Şunları üret:

1. Tool listesi. Kullanıcının açıkça gerçekleştirmek istediği atomik operasyonlar. Name, description (Use-when pattern), input schema ve annotation hint'leri dahil et.
2. Resource listesi. Kullanıcının okumak istediği veriler. URI scheme, mime type ve `resources/subscribe`'ı etkinleştirip etkinleştirmeyeceğin.
3. Prompt listesi. Host'un slash-command olarak göstermesi gereken yeniden kullanılabilir template'ler. Argüman listesi.
4. Kabiliyet bildirimi. Server'ın `initialize`'da döndürdüğü tam `capabilities` nesnesi.
5. Mezuniyet notları. Her parça için FastMCP (Python) ya da TypeScript SDK eşdeğerleri. İskeleden el yapımı bir stdlib pattern'inin yerini alan bir SDK özelliğini (örneğin `lifespan`, `context`) adlandır.

Sert retler:
- Sadece tool olarak açılan ve resource olarak açılmayan herhangi bir "veritabanı sorgusu". Doğru ayrım: `/list` ve `/read` için resource, parametreli `/query` için tool.
- Annotation olmadan kullanıcı girdili tool'larla ayrıcalıklı tool'ları aynı namespace'te karıştıran herhangi bir server.
- Dayanıklı bir notification mekanizması olmadan `resources/subscribe` kabiliyetini iddia eden herhangi bir server iskeletinin.

Reddetme kuralları:
- Domain'in read-only yüzeyi yoksa resource iskelemeyi reddet; sadece tool barındıran bir server öner.
- Domain'in doğal slash-command template'leri yoksa prompt iskelemeyi reddet.
- Kullanıcı bir auth şeması isterse reddet ve Phase 13 · 16'ya (OAuth 2.1) yönlendir.

Çıktı: üç primitive listesi, kabiliyet nesnesi ve 10 satırlık örnek `@app.tool()` decorator tarzı mezuniyet snippet'i içeren tek sayfalık bir server planı. Server'ın ayarlaması gereken en önemli annotation bayrağıyla bitir.
