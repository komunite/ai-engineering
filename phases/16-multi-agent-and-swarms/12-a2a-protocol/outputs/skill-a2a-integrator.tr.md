---
name: a2a-integrator
description: İki agent arasında A2A entegrasyonu tasarla — Agent Card, task şemaları, auth, streaming ya da polling.
version: 1.0.0
phase: 16
lesson: 12
tags: [multi-agent, a2a, protocol, interoperability, google]
---

Birlikte çalışması gereken iki agent sistemi verildiğinde, A2A entegrasyon planını üret: Agent Card içerikleri, task şemaları, auth, transport modu.

Üret:

1. **Agent Card.** Ad, versiyon, skill'ler, endpoint'ler, desteklenen modaliteler (metin, structured, görüntü, ses, video), protocol_version, auth bildirimi.
2. **Skill başına task şemaları.** Girdi JSON schema + artifact JSON schema. Açık ol — client'lar doğrulama yapacak.
3. **Auth seçimi.** Bearer token (OAuth2 veya opaque), mTLS ya da imzalı istekler. Tehdit modeli verildiğinde gerekçelendir (halka açık internet, VPC, karışık).
4. **Transport modu.** Polling vs SSE streaming vs webhook callback'leri. Uzun süreli veya ilerleme-yoğun görevler için streaming; kısa görevler için polling.
5. **Rate limit'ler.** Client başına ve task başına limitler. Kötüye kullanıma karşı koruma.
6. **Idempotency.** Tekrarlayan `POST /tasks` istekleri için strateji (client-side task-key, server-side deduplication).
7. **Hata yönetimi.** `failed` ötesinde task state'leri (retriable vs fatal), dead-letter politikası, hata artifact şeması.
8. **MCP vs A2A bölünmesi.** Uzak agent dahili olarak MCP kullanıyorsa, hangi tool'ların açık olduğunu vs dahili tutulduğunu belirt.

Sert ret durumları:

- Bildirilmiş protocol version'ı olmayan Agent Card'lar.
- Use case yapı gerektirdiğinde serbest metin olan task şemaları.
- Halka açık internet deploy'larında auth=none.

Reddetme kuralları:

- İki agent aynı process'te çalışıyorsa, A2A'yı reddet ve doğrudan Python/JS çağrıları öner. A2A sistem-arası sınırlar içindir.
- Latency gereksinimleri sub-100ms gidiş-dönüş ise, A2A'yı reddet ve ortak şema ile doğrudan RPC öner.
- Uzak agent Agent Card bildirmiyorsa, entegrasyonu reddet ve önce bir tane yayınlamayı öner.

Çıktı: bir sayfalık entegrasyon brief'i. Mühendislik ekibinin `/.well-known/agent.json`'a bırakabilmesi için Agent Card JSON'u inline yapıştırılmış olarak kapat.
