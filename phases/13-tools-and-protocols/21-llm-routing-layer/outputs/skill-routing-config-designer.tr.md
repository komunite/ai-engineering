---
name: routing-config-designer
description: Bir workload profili verildiğinde LiteLLM / OpenRouter / Portkey'i seç ve bir routing konfigürasyonu üret.
version: 1.0.0
phase: 13
lesson: 20
tags: [routing, litellm, openrouter, portkey, fallback]
---

Bir workload profili (gecikme gereksinimleri, compliance kısıtlamaları, ekip boyutu, harcama bütçesi) verildiğinde, bir routing gateway seçimi ve konfigürasyonu üret.

Şunları üret:

1. Gateway seçimi. LiteLLM (self-hosted), OpenRouter (managed SaaS) ya da Portkey (guardrail'li production). Tek paragraflık gerekçe.
2. Alias listesi. Uygulamanın kullandığı mantıksal model isimleri. Örnek: `smart`, `fast`, `coding`, `long_context`.
3. Fallback zincirleri. Alias başına, retry bütçesiyle birlikte öncelik sıralı somut model listesi.
4. Guardrail'ler. PII redaksiyon kuralları, policy ihlal listesi, çıktı filtreleme kuralları.
5. Maliyet bütçesi. Ekip başına / proje başına harcama tavanı, zorlama granülaritesi.

Sert retler:
- Compliance kısıtlamasını ihlal eden bir bölgeye prompt gönderen herhangi bir konfigürasyon.
- Yalnızca bir provider'a sahip herhangi bir fallback zinciri. Tek arıza alanı amacı yok eder.
- Workload doğrudan kullanıcı girdisi işliyorsa guardrail'siz herhangi bir kurulum.

Reddetme kuralları:
- Workload tek modelli bir prototip ise ve bu şekilde kalması bekleniyorsa, gateway önermeyi reddet; doğrudan API çağrıları daha basittir.
- Ekibin SRE'si yoksa ve self-hosted seçerse, operasyonel riski işaretle.
- Kullanıcı alternatifsiz spesifik bir model isterse reddet ve en az bir fallback iste.

Çıktı: gateway seçimi, alias'lar, fallback zincirleri, guardrail'ler ve maliyet planı içeren tek sayfalık bir routing konfigürasyonu. Deployment sonrası alarm verilecek ilk metrikle bitir (tipik olarak fallback kullanım oranı).
