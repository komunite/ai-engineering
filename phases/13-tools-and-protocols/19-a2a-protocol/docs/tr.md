# A2A — Agent-to-Agent Protokolü

> MCP agent-to-tool'dur. A2A (Agent2Agent) agent-to-agent'tır — farklı framework'ler üzerinde inşa edilmiş opak agent'ların işbirliği yapmasına izin veren açık bir protokol. Nisan 2025'te Google tarafından yayınlandı, Haziran 2025'te Linux Foundation'a bağışlandı, Nisan 2026'da AWS, Cisco, Microsoft, Salesforce, SAP ve ServiceNow dahil 150+ destekçi ile v1.0'a ulaştı. IBM'in ACP'sini absorbe etti ve AP2 payments uzantısını ekledi. Bu ders Agent Card'ı, Task lifecycle'ı ve iki transport binding'ini gezer.

**Tür:** Yapım
**Diller:** Python (stdlib, Agent Card + Task harness)
**Ön koşullar:** Faz 13 · 06 (MCP temelleri), Faz 13 · 08 (MCP client'ı)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Agent-to-tool (MCP)'u agent-to-agent (A2A) kullanım durumlarından ayırt et.
- `/.well-known/agent.json`'da skill'ler ve endpoint metadata ile bir Agent Card yayınla.
- Task lifecycle'ı gez (submitted → working → input-required → completed / failed / canceled / rejected).
- Part'larla (text, file, data) Message'ları ve çıktı olarak Artifact'ları kullan.

## Sorun

Bir customer-service agent'ının rapor yazımını uzmanlaşmış bir writer agent'ına delege etmesi gerekiyor. A2A öncesi seçenekler:

- Custom REST API. Çalışır ama her eşleştirme tek-seferliktir.
- Paylaşılan codebase. İki agent'ın aynı framework'ü çalıştırmasını gerektirir.
- MCP. Uymuyor: MCP tool'ları çağırmak içindir, iki agent'ın her agent'ın opak iç muhakemesini korurken işbirliği yapması için değil.

A2A boşluğu doldurur. Etkileşimi bir agent'ın başkasına bir Task göndermesi olarak modeller, lifecycle, mesajlar ve artifact'larla. Çağrılan agent'ın iç state'i opak kalır — caller yalnızca task state geçişlerini ve nihai çıktıları görür.

A2A "framework'ler arası agent'ların birbirleriyle konuşmasına izin ver" protokolüdür. MCP'nin yerini almaz; ikisi tamamlayıcıdır.

## Kavram

### Agent Card

Her A2A-uyumlu agent `/.well-known/agent.json`'da bir kart yayınlar:

```json
{
  "schemaVersion": "1.0",
  "name": "research-agent",
  "description": "Summarizes academic papers and drafts citations.",
  "url": "https://research.example.com/a2a",
  "version": "1.2.0",
  "skills": [
    {
      "id": "summarize_paper",
      "name": "Summarize a paper",
      "description": "Read a paper PDF and produce a 3-paragraph summary.",
      "inputModes": ["text", "file"],
      "outputModes": ["text", "artifact"]
    }
  ],
  "capabilities": {"streaming": true, "pushNotifications": true}
}
```

Discovery URL-tabanlıdır: kartı fetch et, A2A endpoint'inin URL'sini öğren, skill'leri enumerate et.

### İmzalı Agent Card'lar (AP2)

AP2 uzantısı (Eylül 2025) Agent Card'lara kriptografik imzalar ekler. Bir publisher kendi kartını bir JWT ile imzalar; tüketiciler doğrular. İmpersonation'ı önler.

### Task lifecycle'ı

```
submitted -> working -> completed | failed | canceled | rejected
             -> input_required -> working (mesaj üzerinden döngü)
```

Client'lar `tasks/send` ile başlatır. Çağrılan agent state'ler arasında geçer; client'lar state güncellemelerine SSE üzerinden subscribe olur ya da poll eder.

### Message'lar ve Part'lar

Bir mesaj bir ya da daha fazla Part taşır:

- `text` — düz içerik.
- `file` — mimeType ile base64 blob.
- `data` — tipli JSON payload (çağrılan agent için yapılandırılmış input).

Örnek:

```json
{
  "role": "user",
  "parts": [
    {"type": "text", "text": "Summarize this paper."},
    {"type": "file", "file": {"name": "paper.pdf", "mimeType": "application/pdf", "bytes": "..."}},
    {"type": "data", "data": {"targetLength": "3 paragraphs"}}
  ]
}
```

### Artifact'lar

Çıktılar Artifact'lardır, çıplak string'ler değil. Bir Artifact isimlendirilmiş, tipli bir çıktıdır:

```json
{
  "name": "summary",
  "parts": [{"type": "text", "text": "..."}],
  "mimeType": "text/markdown"
}
```

Artifact'lar chunk olarak stream'lenebilir. Caller biriktirir.

### İki transport binding'i

1. **HTTP üzerinde JSON-RPC.** `/a2a` endpoint, request'ler için POST, streaming için opsiyonel SSE. Varsayılan binding.
2. **gRPC.** gRPC'nin native olduğu enterprise ortamlar için.

İki binding de aynı mantıksal mesaj şeklini taşır.

### Opaklık koruma

Bir anahtar tasarım prensibi: çağrılan agent'ın iç state'i opaktır. Caller task state ve artifact'ları görür. Çağrılan agent'ın chain-of-thought'u, tool çağrıları, sub-agent delegasyonu — hepsi görünmez. Bu, tool çağrılarının transparent olduğu MCP'den farklıdır.

Mantığı: A2A rakiplerin iç bileşenleri açıklamadan işbirliği yapmasını sağlar. A2A, çağıran agent'ın o agent'ın servisi nasıl uyguladığını öğrenmesi olmadan "bu customer-service agent'ını çağır" olabilir.

### Timeline

- **2025-04-09.** Google A2A'yı duyurdu.
- **2025-06-23.** Linux Foundation'a bağışlandı.
- **2025-08.** IBM'in ACP'sini absorbe etti.
- **2025-09.** AP2 uzantısı (Agent Payments) yayınlandı.
- **2026-04.** 150+ destekleyici organizasyon ile v1.0 yayınlandı.

### MCP ile ilişki

| Boyut | MCP | A2A |
|-----------|-----|-----|
| Kullanım durumu | Agent-to-tool | Agent-to-agent |
| Opaklık | Transparent tool çağrıları | Opak iç muhakeme |
| Tipik çağıran | Agent runtime'ı | Başka bir agent |
| State | Tool-call sonucu | Lifecycle'lı Task |
| Authorization | OAuth 2.1 (Faz 13 · 16) | JWT-imzalı Agent Card'lar (AP2) |
| Transport | Stdio / Streamable HTTP | HTTP üzerinde JSON-RPC / gRPC |

Belirli bir tool çağırmak istediğinde MCP kullan. Tüm bir task'ı başka bir agent'a delege etmek istediğinde A2A kullan. Birçok üretim sistemi her ikisini kullanır: bir agent tool katmanı için MCP ve işbirliği katmanı için A2A kullanır.

## Kullan

`code/main.py` minimal bir A2A harness implemente eder: bir research agent kartını yayınlar, bir writer agent bir PDF ve bir text talimatı içeren part'larla bir `tasks/send` alır, working → input_required → working → completed arasında geçer ve bir text artifact döndürür. Tüm stdlib; mesaj şekillerine odaklanmak için bellekte transport kullanır.

Bakılacak şeyler:

- Agent Card JSON şekli.
- Task id ataması ve state geçişleri.
- Karışık-tipli part'lı mesajlar.
- Task ortasında input-required dalı.
- Tamamlamada artifact dönüşü.

## Yayınla

Bu ders `outputs/skill-a2a-agent-spec.md` üretir. Diğer agent'lar tarafından çağrılabilir olması gereken yeni bir agent verildiğinde, skill Agent Card JSON'u, skill'ler şemasını ve endpoint blueprint'ini üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Çağrılan agent'ın bir açıklama istediği input-required duraklaması dahil tam Task lifecycle'ını izle.

2. İmzalı bir Agent Card ekle. Kartın kanonik JSON'u üzerinde HMAC ile imzala. Bir verifier yaz ve mutate olmuş bir kartta başarısız olduğunu doğrula.

3. Task streaming implemente et: writer agent SSE üzerinden üç artımlı artifact chunk'ı yayar ve caller onları biriktirir.

4. Bir MCP sunucusunu saran bir A2A agent'ı tasarla. Her MCP tool'unu bir A2A skill'ine eşle. Trade-off'ları not et — hangi opaklık kayboluyor?

5. A2A v1.0 duyurusunu oku ve Nisan 2026 itibarıyla herhangi bir framework tarafından henüz implemente edilmemiş bir feature'ı tanımla. (İpucu: multi-hop task delegasyonu ile ilgili.)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| A2A | "Agent-to-Agent protokolü" | Opak agent işbirliği için açık protokol |
| Agent Card | "`.well-known/agent.json`" | Bir agent'ın skill'lerini ve endpoint'ini tanımlayan yayınlanmış metadata |
| Skill | "Çağrılabilir birim" | Agent'ın desteklediği isimlendirilmiş operasyon (MCP tool'una analog) |
| Task | "Delegasyon birimi" | Lifecycle'ı ve nihai artifact'ı olan iş öğesi |
| Message | "Task input'u" | Part'lar (text, file, data) taşır |
| Part | "Tipli chunk" | Bir mesajın `text` / `file` / `data` öğesi |
| Artifact | "Task çıktısı" | Tamamlamada döndürülen isimlendirilmiş, tipli çıktı |
| AP2 | "Agent Payments Protocol" | Güven ve ödemeler için imzalı Agent Card uzantısı |
| Opaklık | "Black-box işbirliği" | Çağrılan agent'ın iç bileşenleri caller'dan gizlenir |
| Input-required | "Task duraklaması" | Agent'ın daha fazla bilgiye ihtiyaç duyduğu lifecycle state'i |

## İleri Okuma

- [a2a-protocol.org](https://a2a-protocol.org/latest/) — kanonik A2A spesifikasyonu
- [a2aproject/A2A — GitHub](https://github.com/a2aproject/A2A) — referans implementasyonlar ve SDK'lar
- [Linux Foundation — A2A launch press release](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents) — Haziran 2025 governance devri
- [Google Cloud — A2A protocol upgrade](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade) — roadmap ve partner momentum'u
- [Google Dev — A2A 1.0 milestone](https://discuss.google.dev/t/the-a2a-1-0-milestone-ensuring-and-testing-backward-compatibility/352258) — v1.0 release notları ve backward-compat rehberi
