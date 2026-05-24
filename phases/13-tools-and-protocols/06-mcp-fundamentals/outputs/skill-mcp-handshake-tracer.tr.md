---
name: mcp-handshake-tracer
description: Bir MCP client-server konuşmasının pcap tarzı transkriptini verdiğinde, her mesajı primitive'i, yaşam döngüsü fazı ve kabiliyet bağımlılığıyla annote et.
version: 1.0.0
phase: 13
lesson: 06
tags: [mcp, json-rpc, lifecycle, capabilities]
---

Bir MCP oturumundan yakalanmış JSON-RPC 2.0 envelope dizisi verildiğinde, her mesajın primitive'ini, yaşam döngüsü fazını ve altta yatan kabiliyet bayrağını adlandıran bir walk-through üret.

Şunları üret:

1. Mesaj başına annotation. Her `{request, response, notification}` için belirt: yön (client-to-server ya da server-to-client), primitive (tools / resources / prompts / roots / sampling / elicitation / lifecycle), yaşam döngüsü fazı ve bu mesajın geçerli olabilmesi için müzakere edilmesi gereken kabiliyet bayrağı.
2. Kabiliyet kontrolü. Transkriptten `initialize` değişimini yeniden inşa et ve tüm müzakere edilen kabiliyetleri listele. Mevcut olmayan bir kabiliyeti ihlal edecek herhangi bir mesajı işaretle.
3. Hata teşhisi. Her JSON-RPC hatası için kodu ve çevredeki bağlam göz önüne alındığında en olası nedeni adlandır.
4. Tamamlık denetimi. Şunlardan birini eksik bir transkripti işaretle: `initialize`, `initialized` notification, en az bir `tools/list` ya da eşdeğeri, graceful shutdown.
5. Spec uyumluluğu. Her request'in params'ını 2025-11-25 spec'inin minimum alan setine karşı kontrol et. Atlamaları işaretle.

Sert retler:
- Spec'in izin verdiği set dışında bir method kullanan ve `x-` prefix'i olmayan herhangi bir mesaj.
- Client `sampling` kabiliyetini bildirmediğinde herhangi bir `sampling/createMessage` mesajı.
- `notifications/initialized` gelmeden önce yapılan herhangi bir invocation.

Reddetme kuralları:
- MCP olmayan bir protokole ait bir transkripti denetlemen istenirse reddet ve alternatif olarak A2A spec'ine (Phase 13 · 19) işaret et.
- Transkripti "düzeltmen" istenirse reddet. Bu skill annote eder; yeniden yazmaz. Düzeltmeleri uygulayan SDK üzerinden yönlendir.

Çıktı: geliş sırasına göre mesaj başına annote edilmiş tek satır: `[phase/primitive/capability] <method or result shape>`. Herhangi bir kabiliyet ihlalini ve eksik yaşam döngüsü adımını adlandıran üç satırlık bir özetle bitir.
