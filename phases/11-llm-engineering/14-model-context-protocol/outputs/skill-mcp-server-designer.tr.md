---
name: mcp-server-designer
description: Tool'lar, kaynaklar ve güvenlik varsayılanları ile bir MCP server tasarla ve iskele kur.
version: 1.0.0
phase: 11
lesson: 14
tags: [llm-engineering, mcp, tool-use]
---

Bir domain (iç API, veritabanı, dosya kaynağı) ve sunucuyu mount edecek host'lar verildiğinde, şunları çıkar:

1. Primitive haritası. Hangi kapasiteler `tools` (eylem) olur, hangileri `resources` (read-only veri) olur, hangileri `prompts` (kullanıcı tarafından çağrılan template'ler) olur. Primitive başına tek satır.
2. Auth planı. Stdio (güvenilir yerel), API key ile streamable HTTP veya PKCE ile OAuth 2.1. Seç ve gerekçelendir.
3. Şema taslağı. Her tool parametresi için JSON Schema, model tool-seçimine göre ayarlanmış `description` alanlarıyla (API doc değil).
4. Yıkıcı eylem listesi. State değiştiren her tool; `destructiveHint: true` ve insan onayı iste.
5. Test planı. Tool başına: bir schema-only contract testi, bir MCP client üzerinden round-trip testi, bir red-team prompt-injection vakası.

Onay yolu olmadan diske yazan veya dış API çağıran bir sunucuyu ship etmeyi reddet. Tek bir sunucuda 20'den fazla tool expose etmeyi reddet; bunun yerine domain-kapsamlı sunuculara böl.
