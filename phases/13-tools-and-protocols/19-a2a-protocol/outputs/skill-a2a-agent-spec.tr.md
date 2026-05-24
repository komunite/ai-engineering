---
name: a2a-agent-spec
description: A2A üzerinden çağrılabilir bir agent için Agent Card ve skill şemasını üret.
version: 1.0.0
phase: 13
lesson: 18
tags: [a2a, agent-card, task-lifecycle, delegation]
---

Bir agent'ın kabiliyetleri ve hedef işbirlikçileri verildiğinde, A2A Agent Card'ını ve skill tanımlarını üret.

Şunları üret:

1. Agent Card. `name`, `description`, `url`, `version`, `schemaVersion`, `capabilities` (streaming, pushNotifications), `skills[]`.
2. Skills listesi. Her biri `id`, `name`, `description`, `inputModes`, `outputModes` ile. Description'larda "Use when X. Do not use for Y." pattern'ini kullan.
3. Task state planı. Her skill için beklenen state geçişleri ve input_required yolları.
4. Imzalama planı. Card'ı AP2 üzerinden imzalayıp imzalamayacağın (dışarıdan çağrılabilir agent'lar için önerilir).
5. Transport. HTTP üzerinde JSON-RPC (varsayılan) ya da gRPC. v1.0 ile geriye dönük uyumluluğu not düş.

Sert retler:
- Stabil URL'i olmayan herhangi bir Agent Card. Keşfi bozar.
- Input ve output mod'ları bildirilmemiş herhangi bir skill. Çağıranlar uyumluluğu muhakeme edemez.
- AP2 imzalama planı olmayan dışarıdan çağrılabilir herhangi bir agent. Kimliğe bürünme vektörü.

Reddetme kuralları:
- Agent'ın use case'i tek bir tool çağrısıysa, A2A iskelelemeyi reddet; MCP öner.
- Agent içsel olarak göstermemesi gereken şeyleri (tool call izleri, chain-of-thought) açığa çıkarıyorsa reddet ve opaklığı zorunlu kıl.
- Agent ödemeler için A2A'ya ihtiyaç duyuyorsa (AP2 use case), AP2 uzantı versiyonunu doğrula ve AP2'nin core A2A'dan ayrı olduğunu işaretle.

Çıktı: tek sayfalık bir Agent Card JSON'u, her operasyon için skill şeması, state-transition planı, imzalama ve transport seçimleri. Agent'ın söz verdiği minimum v1.0 geriye dönük uyumluluk garantisiyle bitir.
