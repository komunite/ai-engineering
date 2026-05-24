---
name: ecosystem-blueprint
description: Bir ürün ihtiyacı verildiğinde tam bir Phase 13 ekosistem mimarisi üret; primitifleri, güvenlik duruşunu, telemetriyi ve packaging'i adlandır.
version: 1.0.0
phase: 13
lesson: 22
tags: [mcp, capstone, ecosystem, architecture, a2a, otel]
---

Bir ürün ihtiyacı (araştırma, özetleme, otomasyon, herhangi bir agent destekli workflow) verildiğinde, tam mimariyi üret.

Şunları üret:

1. MCP primitifleri. Hangi tool'lar, resource'lar, prompt'lar ve task'lar gereklidir. Herhangi bir `ui://` app var mı? Herhangi bir async task var mı?
2. Güvenlik duruşu. OAuth 2.1 scope seti, gateway RBAC matrisi, pinned hash manifest'i, Rule of Two denetimi.
3. A2A işbirliği. Herhangi bir alt agent çağrısını tanımla. Agent Card'larını tanımla.
4. Telemetri. OTel GenAI span hiyerarşisi. Exporter ve backend seçimi.
5. Packaging. AGENTS.md, SKILL.md ve deployment yüzeyi (Docker Compose, K8s).
6. Phase 13 derslerine eşleme. Her tasarım seçiminin hangi derse referans verdiği.

Sert retler:
- Güvensiz girdiyi, hassas veriyi ve sonuç doğurucu eylemi tek bir turda birleştiren herhangi bir mimari (Rule of Two).
- MCP ve A2A hop'ları boyunca trace propagation olmayan herhangi bir mimari.
- LLM katmanında en az bir fallback provider'ı olmayan herhangi bir mimari.

Reddetme kuralları:
- Ürün ihtiyacı doğrudan bir LLM çağrısıyla daha iyi karşılanıyorsa, tam ekosistemi iskelelemeyi reddet.
- Ekibin gateway için SRE'si yoksa, managed bir gateway (Cloudflare MCP Portals, Portkey) öner.
- Mimari ödemeleri içeriyorsa, AP2'yi drift riski taşıyan bir A2A uzantısı olarak işaretle ve ayrı bir onay öner.

Çıktı: primitif, güvenlik duruşu, A2A hop'ları, telemetri planı, packaging ve ders haritasını içeren tek sayfalık bir blueprint. Deployment için en zor operasyonel riski tanımlayan tek bir cümleyle bitir.
