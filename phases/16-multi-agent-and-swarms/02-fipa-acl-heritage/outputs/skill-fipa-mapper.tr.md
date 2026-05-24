---
name: fipa-mapper
description: 2026'nın herhangi bir agent-protokol spec'ini (MCP, A2A, ACP, ANP, CA-MCP, NLIP ya da yenisi) FIPA-ACL performative'larına ve etkileşim protokollerine eşle; böylece neyin gerçek yenilik, neyin yeniden icat olduğuna karar verilebilsin.
version: 1.0.0
phase: 16
lesson: 02
tags: [multi-agent, protocols, FIPA, speech-acts, interoperability]
---

Yeni bir agent-protokol spec'i verildiğinde, FIPA-ACL eşlemesini üret; böylece okuyucu hangi kısmın yeniden icat, hangi kısmın gerçek yeni yapı olduğunu ayırt edebilsin.

Üret:

1. **Envelope eşlemesi.** Spec'in tanımladığı her mesaj türü için, en yakın FIPA performative'ını adlandır (`inform`, `request`, `query-if`, `query-ref`, `propose`, `accept-proposal`, `reject-proposal`, `cfp`, `subscribe`, `cancel`, `failure`, `not-understood` ya da diğer ~20'sinden biri). Hiçbir performative uymuyorsa, boşluğu kesin olarak tanımla.
2. **Korelasyon modeli.** Spec; istekleri yanıtlara, cancellation'ı orijinal isteğe ve streamed event'leri subscribe'a nasıl ilişkilendiriyor? FIPA'nın `:conversation-id` ve `:reply-with` alanlarıyla karşılaştır.
3. **Content-language duruşu.** Spec bir content şeması zorunlu tutuyor mu (tipli artifact'lar, JSON-Schema), doğal dili kabul ediyor mu yoksa açık mı bırakıyor? FIPA'nın SL0/SL1 ve ontology alanlarıyla karşılaştır.
4. **Etkileşim-protokolü kütüphanesi.** Spec üzerinde hangi FIPA etkileşim protokolleri implement edilebilir: contract-net, subscribe-notify, request-when, propose-accept? Her birini implement edecek mesajları adlandır.
5. **Discovery modeli.** Bir agent karşı tarafları ve yetenekleri nasıl bulur (MCP `listTools`, A2A Agent Card, ANP DID + meta-protokol)? FIPA'nın directory facilitator'ı ve yellow-pages servisiyle karşılaştır.
6. **Yeniden icat vs yenilik.** Üç sütunlu kısa bir tablo üret: [FIPA kavramı, modern spec eşdeğeri, ne değişti]. Her satırı [yeniden-icat] ya da [yeni-yapı] olarak işaretle. Bir satır yalnızca spec, FIPA'da olmayan bir primitive getirdiğinde "yeni-yapı"dır — merkeziyetsiz kimlik, tipli çok modlu artifact'lar ve LLM tarafından yorumlanabilir content yaygın adaylardır.

Sert ret durumları:

- Bir spec'in FIPA'da olmayan bir primitive'i göstermeden "devrim niteliğinde" olduğunu iddia eden herhangi bir eşleme. Speech-act teorisi + ontoloji ek yükü, primitive'lar değil; başarısızlık modu buydu.
- Discovery katmanını yok sayan framework karşılaştırmaları. Discovery'siz bir spec eksiktir, yeni değil.
- "Protokol X, FIPA'yı değiştirir" tarzı, iki agent içerik anlamı konusunda anlaşamadığında (semantic drift) ne olacağını ele almayan ifadeler.

Reddetme kuralları:

- Spec standardizasyon öncesindeyse (taslak < 6 ay, halka açık implementasyon yok), eşlemenin geçici olduğunu belirt ve en olası üç değişikliği işaretle.
- Spec kapalı kaynak veya yalnızca kurumsalsa (bazı ACP varyantları), belgelenenleri eşle ve boşlukları adlandır.
- Kullanıcı yalnızca bir blog yazısı sunuyorsa (spec belgesi yok), eşlemeden önce spec iste.

Çıktı: bir sayfalık brief. Tek cümlelik özetle başla ("Protokol X, JSON sözdizimi ve DID tabanlı discovery katmanıyla FIPA `request`/`subscribe`'dır."), ardından yukarıdaki altı bölüm, sonra kapanış paragrafı: "Bu spec hangi eski FIPA başarısızlık modunu yeniden keşfedecek?"
