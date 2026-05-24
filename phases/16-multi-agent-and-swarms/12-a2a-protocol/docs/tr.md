# A2A — Agent-to-Agent Protokolü

> Google A2A'yı Nisan 2025'te duyurdu; Nisan 2026'da spec https://a2a-protocol.org/latest/specification/ adresinde ve 150+ organizasyon onu destekliyor. A2A, MCP'nin (Ders 13) yatay tamamlayıcısıdır: MCP dikey iken (agent ↔ tool'lar), A2A peer-to-peer'dir (agent ↔ agent). Agent Card'ları (keşif), artefaktlı task'ları (metin, yapılandırılmış veri, video), opak görev yaşam döngülerini ve auth'u tanımlar. Üretim sistemleri MCP ile A2A'yı giderek daha çok eşliyor. Google Cloud 2025-2026 boyunca A2A desteğini Vertex AI Agent Builder'a entegre etti.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib, `http.server`, `json`)
**Ön koşullar:** Faz 16 · 04 (Primitive Model)
**Süre:** ~75 dakika

## Sorun

Agent'ın başka bir sistemdeki başka bir agent'ı çağırması gerekiyor. Nasıl? Bir HTTP endpoint sunabilir, özel bir JSON şeması tanımlayabilir ve diğer tarafın onu konuşmasını umabilirsin. Her agent çifti özel bir entegrasyon olur.

A2A bu çağrı için evrensel wire protokolüdür. Standart keşif, standart task modeli, standart transport, standart artefaktlar. HTTP+REST gibi, ama first-class vatandaş olarak agent'lar için.

## Kavram

### Dört eleman

**Agent Card.** Agent'ı tanımlayan `/.well-known/agent.json`'da bir JSON dokümanı: isim, skill'ler, endpoint'ler, desteklenen modaliteler, auth gereksinimleri. Keşif card'ı okuyarak olur.

```
GET https://agent.example.com/.well-known/agent.json
→ {
    "name": "code-review-agent",
    "skills": ["review-python", "review-typescript"],
    "endpoints": {
      "tasks": "https://agent.example.com/tasks"
    },
    "auth": {"type": "bearer"},
    "modalities": ["text", "structured"]
  }
```

**Task.** İş birimi. Bir yaşam döngüsüyle asenkron, stateful nesne: `submitted → working → completed / failed / canceled`. İstemci bir task gönderir, güncellemeler için poll'lar ya da abone olur.

**Artifact.** Bir task tarafından üretilen sonuç tipi. Metin, yapılandırılmış JSON, görüntü, video, ses. Artefaktlar tiplidir, böylece farklı modaliteler first-class'tır.

**Opak yaşam döngüsü.** A2A uzak agent'ın görevi *nasıl* çözdüğünü öngörmez. İstemci durum geçişlerini ve artefaktları görür; implementasyon herhangi bir framework'ü kullanmakta serbesttir.

### MCP/A2A bölünmesi

- **MCP** (Ders 13): agent ↔ tool. Agent JSON-RPC üzerinden bir tool sunucusuna okur/yazar. Varsayılan olarak stateless.
- **A2A**: agent ↔ agent. Peer protokol; her iki taraf da kendi akıl yürütmesine sahip agent'lardır.

Üretim çoklu-agent sistemleri ikisini de kullanır. Bir A2A peer kendi tarafında MCP tool'larını çağırır. Bölünme iki endişeyi temiz tutar.

### Keşif akışı

```
İstemci                  Agent sunucusu
  ├──GET /.well-known/agent.json──>
  <──Agent Card JSON─────────────
  ├──POST /tasks {skill, input}──>
  <──201 task_id, state=submitted
  ├──GET /tasks/{id}──────────────>
  <──state=working, 42% tamam──────
  ├──GET /tasks/{id}──────────────>
  <──state=completed, artefaktlar─
```

Ya da streaming ile: push güncellemeleri için `/tasks/{id}/events`'e SSE aboneliği.

### Auth

A2A üç yaygın deseni destekler:

- **Bearer token** — OAuth2 ya da opak.
- **mTLS** — karşılıklı TLS; organizasyonlar birbirine kimlik kanıtlar.
- **İmzalı istekler** — payload üzerinde HMAC.

Auth Agent Card'da bildirilir; istemciler keşfeder ve uyar.

### Nisan 2026'ya kadar 150+ organizasyon

Kurumsal benimsenme A2A ölçeğini sürdü. Manşet: A2A kurumsal agent sistemlerinin güven sınırlarını aşma yolu oldu. Google Cloud Vertex AI Agent Builder A2A desteğini gönderdi; Microsoft Agent Framework onu destekler; çoğu büyük framework (LangGraph, CrewAI, AutoGen) A2A adapter'ları gönderir.

### A2A nerede kazanır

- **Org-arası çağrılar.** Şirket A'daki agent şirket B'deki agent'ı çağırır. A2A olmadan, her çift özel bir kontrattır.
- **Heterojen framework'ler.** LangGraph agent CrewAI agent'ı çağırır, o da custom Python agent'ı çağırır. A2A normalleştirir.
- **Tipli artefaktlar.** Video sonuç, yapılandırılmış JSON, ses — hepsi first-class.
- **Uzun süreli görevler.** Opak yaşam döngüsü + polling saatlerce süren görevleri basitleştirir.

### A2A nerede zorlanır

- **Gecikme-hassas mikro-çağrılar.** A2A'nın yaşam döngüsü asenkron. Sub-milisaniye agent-to-agent uymaz; doğrudan RPC kullan.
- **Sıkı eşleşmiş process-içi agent'lar.** İki agent da aynı Python process'inde çalışıyorsa, A2A'nın HTTP gidiş-dönüşü aşırı.
- **Küçük takımlar.** Spec overhead gerçek; sadece iç agent'lar formaliteye ihtiyaç duymayabilir.

### A2A vs ACP, ANP, NLIP

2024-2026'da birkaç ilgili spec ortaya çıktı:

- **ACP** (IBM/Linux Foundation) — A2A'nın öncülü, daha dar kapsam.
- **ANP** (Agent Network Protocol) — peer-keşif-ağırlıklı, merkeziyetsiz-öncelikli.
- **NLIP** (Ecma Natural Language Interaction Protocol, Aralık 2025'te standartlaştırıldı) — doğal-dil içerik tipi.

A2A, Nisan 2026 itibariyle en çok benimsenen peer protokolüdür. Karşılaştırma için arXiv:2505.02279 (Liu ve diğ., "A Survey of Agent Interoperability Protocols")'a bak.

## İnşa Et

`code/main.py` `http.server` ve JSON kullanarak A2A-minimal bir sunucu ve istemci uygular. Sunucu:

- `/.well-known/agent.json` sunar,
- `POST /tasks` kabul eder,
- task state'i yönetir,
- `GET /tasks/{id}`'de artefaktları döndürür.

İstemci:

- Agent Card'ı çeker,
- bir task gönderir,
- tamamlanmaya kadar poll'lar,
- artefaktı okur.

Çalıştır:

```
python3 code/main.py
```

Script sunucuyu arka plan thread'inde başlatır, sonra ona karşı istemciyi çalıştırır. Tam akışı görürsün: keşif, gönder, poll, artefakt.

## Kullan

`outputs/skill-a2a-integrator.md` bir A2A entegrasyonu tasarlar: Agent Card içerikleri, task şemaları, auth seçimi, streaming vs polling.

## Yayınla

Kontrol listesi:

- **Spec sürümünü sabitle.** A2A hâlâ evrim geçiriyor; Agent Card protokol sürümünü bildirmeli.
- **Idempotent task oluşturma.** Mükerrer gönderimler (ağ retry'ları) bir task üretmeli.
- **Artefakt şemaları.** Agent'ın ne şekiller döndürdüğünü bildir; tüketiciler doğrulamalı.
- **Rate limit + auth.** A2A halka açık; standart web güvenliğini uygula.
- **Başarısız task'lar için dead-letter.** Tekrar eden başarısızlık tipleri için zaman içindeki desenleri denetle.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. İstemcinin sunucuyu keşfettiğini ve doğru artefaktı aldığını doğrula.
2. Sunucuya ikinci bir skill ekle (ör. "summarize"). Agent Card'ı güncelle. Skill'i görev tipine göre seçen bir istemci yaz.
3. Bir SSE streaming endpoint uygula: durum değişikliklerini yayan `/tasks/{id}/events`. İstemcinin farklı yapması gereken ne?
4. A2A spec'ini (https://a2a-protocol.org/latest/specification/) oku. Spec'in zorunlu kıldığı ama bu demonun uygulamadığı üç şeyi belirle.
5. A2A'yı (Agent Card keşfi) MCP ile (sunucu-tarafı yetenek listeleme via `listTools`) karşılaştır. Kendini tanımlayan agent'lar ve yetenek-yoklama arasındaki takas nedir?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| A2A | "Agent-to-agent" | Sistemler arası agent'ların diğer agent'ları çağırması için peer protokol. Google 2025. |
| Agent Card | "Agent'ın kartviziti" | `/.well-known/agent.json`'da skill'leri, endpoint'leri, auth'u tanımlayan JSON. |
| Task | "İş birimi" | Yaşam döngüsüyle asenkron stateful nesne; tamamlanmada artefaktlar üretilir. |
| Artifact | "Sonuç" | Tipli çıktı: metin, yapılandırılmış JSON, görüntü, video, ses. First-class medya. |
| Opak yaşam döngüsü | "Nasıl çözüldüğü agent'ın işi" | İstemci durum geçişlerini görür; sunucu framework/tool seçmekte serbesttir. |
| Keşif | "Agent'ı bulma" | `GET /.well-known/agent.json` card'ı döndürür. |
| MCP vs A2A | "Tool'lar vs peer'lar" | MCP: dikey agent ↔ tool. A2A: yatay agent ↔ agent. |
| ACP / ANP / NLIP | "Kardeş protokoller" | Komşu spec'ler; A2A 2026'da en çok benimsenen. |

## İleri Okuma

- [A2A specification](https://a2a-protocol.org/latest/specification/) — kanonik spec
- [Google Developers Blog — A2A duyurusu](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) — Nisan 2025 lansman yazısı
- [A2A GitHub repo](https://github.com/a2aproject/A2A) — referans implementasyonlar ve SDK'lar
- [Liu ve diğ. — A Survey of Agent Interoperability Protocols](https://arxiv.org/html/2505.02279v1) — MCP, ACP, A2A, ANP karşılaştırması
