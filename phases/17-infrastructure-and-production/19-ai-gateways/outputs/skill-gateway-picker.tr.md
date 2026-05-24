---
name: gateway-picker
description: Ölçek, latency bütçesi, uyumluluk, operasyon tutumu ve fiyatlandırma toleransı verildiğinde bir AI gateway (LiteLLM, Portkey, Kong AI, Cloudflare/Vercel) seç.
version: 1.0.0
phase: 17
lesson: 19
tags: [ai-gateway, litellm, portkey, kong, cloudflare, vercel, bifrost, fallback, rate-limit, guardrails]
---

RPS (mevcut ve projeksiyonlanmış 12 aylık), latency bütçesi, uyumluluk (self-host gerekli mi?), guardrail ihtiyacı (PII redaksiyon, jailbreak detection, audit) ve fiyatlandırma toleransı verildiğinde, bir gateway önerisi üret.

Üret:

1. Birincil gateway. Aracı adlandır. RPS tavanı, overhead ve özellik uyumuyla gerekçelendir.
2. Fallback zinciri. Sırayla üç sağlayıcı; OpenAI → Anthropic → self-hosted kanonik olanıdır. Beklenen availability'i hesapla.
3. Rate-limit politikası. >500 RPS'de sliding-window önerilir; aksi takdirde token-bucket kabul edilebilir. Tenant başına kademeli.
4. Guardrail'ler. PII/jailbreak gerekiyorsa Portkey; ölçek + guardrail gerekiyorsa Kong; yalnızca dev katmanı için LiteLLM.
5. Observability devir teslimi. Phase 17 · 13 seçimine yönlendir; OTel GenAI konvansiyonlarının aktığını doğrula.
6. Migrasyon. Uygulama düzeyi entegrasyondan taşınıyorsa, aşamalı rollout (gateway üzerinde %1 canary, başarıda genişlet).

Hard rejects:
- >2000 RPS'de LiteLLM. Reddet — Kong benchmark cascade arızalarını gösterir; önce migrasyon yap.
- TTFT P99 < 100 ms SLA'da Portkey. Reddet — 30 ms overhead bütçenin çoğunu yer.
- Regüle bir on-prem müşteri için Cloudflare AI Gateway. Reddet — yalnızca managed; self-host yok.

Reddetme kuralları:
- Ölçek belirsizliği büyükse (mevcut 100 RPS, 6 ayda planlanan 2K+), LiteLLM'e taahhüt etmeden önce migrasyon planı iste.
- Uyumluluk SOC 2 Type II gerektiriyorsa ve seçilen gateway managed SLA olmadan yalnızca OSS ise, müşterinin kendi SOC 2 attestation'unu iste.
- Takımda Kubernetes yoksa ve Kong self-host seçerse, reddet — managed Kong veya Portkey managed öner.

Çıktı: gateway, fallback zinciri, rate-limit politikası, guardrail tutumu, observability akışı, migrasyon planı içeren tek sayfalık karar. Bir metrikle bitir: son saatte gateway P99 latency'si; ihlalde alarm.
