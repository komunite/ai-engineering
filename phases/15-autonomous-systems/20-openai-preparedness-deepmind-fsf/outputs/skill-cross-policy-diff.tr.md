---
name: cross-policy-diff
description: OpenAI Preparedness Framework v2, Anthropic RSP v3.0 ve DeepMind FSF v3'ü referans olarak kullanarak spesifik bir capability için cross-policy karşılaştırması üret.
version: 1.0.0
phase: 15
lesson: 20
tags: [preparedness-framework, fsf, rsp, cross-policy, scaling-policy]
---

Spesifik bir frontier capability verildiğinde (örn. "long-range autonomy," "otonom replication ve adaptation," "R&D otomasyonu"), üç framework'ün her birinin capability'i nasıl sınıflandırdığını ve hangi mitigation'ların tetiklendiğini gösteren bir cross-policy diff üret.

Üret:

1. **OpenAI PF v2 sınıflandırması.** Tracked veya Research. Tracked ise, Capabilities + Safeguards Report tetikleyicilerini adlandır. Research ise, politika dilinin "potential" mitigation'lar olduğunu not et.
2. **Anthropic RSP v3.0 sınıflandırması.** Hangi eşik (ASL-3, AI R&D-4, hardcoded prohibition)? Hangi mitigation (affirmative case, security + deployment)? Taahhüdün Anthropic-tek-taraflı tier'da mı yoksa endüstri-tavsiye tier'da mı yaşadığını doğrula.
3. **DeepMind FSF v3 sınıflandırması.** Hangi domain (Cyber, Bio, ML R&D, CBRN)? Hangi CCL veya Tracked Capability Level? Deceptive alignment monitörlemesi devreye alındı mı?
4. **Convergence özeti.** Üç politika capability'nin ciddiyetinde anlaşıyor mu, yoksa anlamlı bir uyuşmazlık var mı? Hangi sınıflandırma en titiz, hangisi en az?
5. **Ölçüm bağımlılığı.** Her sınıflandırma capability ölçümüne bağlıdır. Capability'nin nasıl ölçüldüğünü ve hangi eval sağlayıcısının (METR, Apollo, internal, third-party) o ölçümü sahiplendiğini adlandır.

Sert reddetmeler:
- Doküman-seviyesi kanıt olmadan announcement-language benzerliğine dayalı cross-policy uyum iddiaları.
- Kaynak dokümanda spesifik bir clause'a işaret edemeyen herhangi bir sınıflandırma.
- "Research Category"yi (OpenAI) "Tracked Category" ile eşdeğer ele almak — farklı operasyonel sonuçları vardır.

Reddetme kuralları:
- Kullanıcı her sınıflandırma için kaynak doküman pasajlarını üretemezse, reddet ve önce alıntılar iste.
- Kullanıcı policy-existence'ı pratikteki mitigation kanıtı olarak ele alıyorsa, reddet ve spesifik mitigation'ların tetiklendiğine dair kanıt iste.
- Capability bir framework tarafından "kapsandığı" iddia ediliyor ama kelime dokümanda geçmiyorsa, reddet ve somut bir clause referansı iste.

Çıktı formatı:

Şunları içeren bir diff dokümanı döndür:
- **Capability tanımı** (bir cümle)
- **OpenAI PF v2 satırı** (sınıflandırma, tetikleyici, kaynak clause)
- **Anthropic RSP v3.0 satırı** (sınıflandırma, tetikleyici, tek-taraflı-vs-tavsiye)
- **DeepMind FSF v3 satırı** (domain, CCL / TCL, deceptive-alignment dahil olma)
- **Convergence özeti** (anlaşma + anlamlı uyuşmazlık)
- **Ölçüm sahipliği** (eval sağlayıcı, eval cadence'ı)
- **Okuyucu tavsiyesi** (en titiz, en az titiz, gerekçeli)
