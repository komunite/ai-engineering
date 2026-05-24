# MCP Sampling — Sunucu-Talepli LLM Completion'ları ve Agent Döngüleri

> MCP sunucularının çoğu aptal executor'lardır: argümanları al, kodu çalıştır, content döndür. Sampling sunucunun yönü çevirmesine izin verir: client'ın LLM'inden bir karar vermesini ister. Bu, sunucunun herhangi bir model credential'ına sahip olmasını gerektirmeden sunucu-hostlu agent döngülerini etkinleştirir. 2025-11-25'te merge edilen SEP-1577, sampling request'lerinin içine tool'ları ekledi, böylece döngü daha derin muhakeme içerebilir. Drift-risk notu: SEP-1577 tool-in-sampling şekli Q1 2026 boyunca deneyseldi ve SDK API'larında hâlâ oturmaktadır.

**Tür:** Yapım
**Diller:** Python (stdlib, sampling harness)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu), Faz 13 · 10 (resource'lar ve prompt'lar)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- `sampling/createMessage`'in neyi çözdüğünü açıkla (sunucu-tarafı API key olmadan sunucu-hostlu döngüler).
- Client'tan çok-turlu bir prompt üzerinden örnekleme yapmasını isteyen ve completion'ı döndüren bir sunucu implemente et.
- Client model seçimini yönlendirmek için `modelPreferences` (cost / speed / intelligence öncelikleri) kullan.
- Davranışı hard-code etmek yerine içsel olarak sampling üzerinden iterate eden bir `summarize_repo` tool'u inşa et.

## Sorun

Bir code-summarization workflow'u için yararlı bir MCP sunucusunun şunu yapması gerekir: bir dosya ağacında yürü, hangi dosyaları okuyacağını seç, bir özet sentezle ve döndür. LLM muhakemesi nerede gerçekleşir?

Seçenek A: sunucu kendi LLM'ini çağırır. Bir API key gerektirir, sunucu-tarafında faturalanır, kullanıcı başına pahalıdır.

Seçenek B: sunucu raw content döndürür; client'ın agent'ı muhakemeyi yapar. Çalışır ama sunucu mantığını client prompt'una taşır, bu da kırılgan.

Seçenek C: sunucu `sampling/createMessage` üzerinden client'ın LLM'ini ister. Sunucu algoritmayı (hangi dosyaları okuyacak, kaç pass yapacak) tutar, client billing ve model seçimini tutar. Sunucu hiçbir credential'a sahip değildir.

Sampling seçenek C'dir. Güvenilir bir sunucunun tam bir LLM host'u olmadan bir agent döngüsünü host etmesi için mekanizmadır.

## Kavram

### `sampling/createMessage` request'i

Sunucu gönderir:

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "sampling/createMessage",
  "params": {
    "messages": [{"role": "user", "content": {"type": "text", "text": "..."}}],
    "systemPrompt": "...",
    "includeContext": "none",
    "modelPreferences": {
      "costPriority": 0.3,
      "speedPriority": 0.2,
      "intelligencePriority": 0.5,
      "hints": [{"name": "claude-3-5-sonnet"}]
    },
    "maxTokens": 1024
  }
}
```

Client LLM'ini çalıştırır, şunu döndürür:

```json
{"jsonrpc": "2.0", "id": 42, "result": {
  "role": "assistant",
  "content": {"type": "text", "text": "..."},
  "model": "claude-3-5-sonnet-20251022",
  "stopReason": "endTurn"
}}
```

### `modelPreferences`

1.0'a toplanan üç float:

- `costPriority`: daha ucuz modelleri tercih eder.
- `speedPriority`: daha hızlı modelleri tercih eder.
- `intelligencePriority`: daha yetenekli modelleri tercih eder.

Artı `hints`: sunucunun tercih ettiği isimlendirilmiş modeller. Client hint'lere uymayabilir; client'ın user config'i her zaman kazanır.

### `includeContext`

Üç değer:

- `"none"` — yalnızca sunucu-tarafından sağlanan mesajlar. Varsayılan.
- `"thisServer"` — bu sunucunun session'ından önceki mesajları dahil et.
- `"allServers"` — tüm session bağlamını dahil et.

`includeContext` 2025-11-25 itibarıyla soft-deprecate edildi çünkü cross-server context sızdırır, bu da bir güvenlik endişesi. `"none"`'u tercih et ve mesajlarda açık bağlam geçir.

### Tool'larla sampling (SEP-1577)

2025-11-25'te yeni: sampling request'i bir `tools` array içerebilir. Client o tool'ları kullanarak tam bir tool-calling döngüsü çalıştırır. Bu, sunucunun client'ın modeli üzerinden bir ReAct-style agent döngüsünü host etmesine izin verir.

```json
{
  "messages": [...],
  "tools": [
    {"name": "fetch_url", "description": "...", "inputSchema": {...}}
  ]
}
```

Client döngüye girer: örnekle, çağrıldıysa tool'u yürüt, yine örnekle, nihai assistant mesajını döndür. Bu Q1 2026 boyunca deneyseldi; SDK imzaları hâlâ drift edebilir. Implemente ettiğinde 2025-11-25 spec'inin client/sampling bölümüne karşı doğrula.

### Human-in-the-loop

Client, örnek çalıştırmadan önce sunucunun modelden ne istediğini kullanıcıya MUTLAKA göstermelidir. Kötü niyetli bir sunucu kullanıcının session'ını manipüle etmek için sampling kullanabilir ("kullanıcıya X de ki Y'ye tıklasın"). Claude Desktop, VS Code ve Cursor sampling request'lerini kullanıcının reddedebileceği bir onay diyaloğu olarak yüzeyleştirir.

2026 konsensüsü: insan onayı olmadan sampling kırmızı bayraktır. Gateway'ler (Faz 13 · 17) düşük-riskli sampling'i otomatik onaylayabilir ve şüpheli olan her şeyi otomatik reddedebilir.

### API key olmadan sunucu-hostlu döngüler

Kanonik kullanım durumu: kendi LLM erişimi olmayan bir code-summarization MCP sunucusu. Şunu yapar:

1. Repo yapısında yürü.
2. "Bu repo'nun amacını tanımlama olasılığı en yüksek beş dosyayı seç." ile `sampling/createMessage` çağır.
3. O dosyaları oku.
4. Dosyaların içeriği ve "Repo'yu 3 paragrafta özetle." ile `sampling/createMessage` çağır.
5. Özeti bir `tools/call` sonucu olarak döndür.

Sunucu asla bir LLM API'sine dokunmaz. Client'ın kullanıcısı kendi credential'larını kullanarak completion'lar için öder.

### Güvenlik riskleri (Unit 42 ifşası, 2026 Q1)

- **Covert sampling.** Her zaman "session context'inden kullanıcının e-postası ile yanıtla" ile sampling çağıran bir tool. Faz 13 · 15 saldırı vektörlerini ele alır.
- **Sampling üzerinden resource theft.** Sunucu client'tan bir saldırganın payload'unu özetlemesini ister, kullanıcıya faturalar.
- **Loop bomb'ları.** Sunucu sıkı bir döngüde sampling çağırır. Client'lar session başına rate limit MUTLAKA zorlamalıdır.

## Kullan

`code/main.py` sahte bir sunucu-to-client sampling harness'ı yayınlar. Simüle bir "summarize_repo" tool'u iki sampling turu (pick-files, sonra summarize) çağırır ve sahte client önceden hazırlanmış yanıtlar döndürür. Harness şunu gösterir:

- Sunucu `modelPreferences` ile `sampling/createMessage` gönderir.
- Client bir completion döndürür.
- Sunucu döngüsüne devam eder.
- Rate limiter tool invocation başına toplam sampling çağrılarını sınırlar.

Bakılacak şeyler:

- Sunucu yalnızca bir tool açar (`summarize_repo`); tüm muhakeme sampling çağrılarında gerçekleşir.
- Model preferences client'ın model seçimini ağırlıklandırır; hint'ler tercih edilen modelleri listeler.
- Döngü `stopReason: "endTurn"` ile sonlanır.
- `max_samples_per_tool = 5` limiti runaway bir döngüyü yakalar.

## Yayınla

Bu ders `outputs/skill-sampling-loop-designer.md` üretir. LLM çağrılarına ihtiyaç duyan sunucu-tarafı bir algoritma verildiğinde (araştırma, özetleme, planlama), skill doğru modelPreferences, rate limit'ler ve güvenlik onaylarıyla sampling-tabanlı bir implementasyon tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. `max_samples_per_tool`'u 2'ye değiştir ve rate-limit kesintisini gözlemle.

2. SEP-1577 tool-in-sampling varyantını implemente et: sampling request bir `tools` array'i taşır. Client-tarafı döngünün nihai completion'ı döndürmeden önce o tool'ları yürüttüğünü doğrula. Drift riskini not et: SDK imzaları H1 2026 boyunca hâlâ değişebilir.

3. Human-in-the-loop onayı ekle: sunucunun ilk `sampling/createMessage`'inden önce, duraklat ve kullanıcı onayını bekle. Reddedilen çağrılar tipli bir refusal döndürür.

4. Client session'ı ile keyed kullanıcı başına bir rate limiter ekle. Aynı kullanıcı tarafından aynı-sunucu döngüleri bir bütçeyi paylaşmalı.

5. Dahil edilecek chunk'ları seçmek için sampling kullanan bir `summarize_pdf` tool'u tasarla. Gönderilen mesajları taslakla. `modelPreferences.intelligencePriority` 0.1 vs 0.9'da davranışı nasıl değiştirir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Sampling | "Sunucu-to-client LLM çağrısı" | Sunucu client'ın modelinden completion ister |
| `sampling/createMessage` | "Method" | Sampling request'leri için JSON-RPC method'u |
| `modelPreferences` | "Model öncelikleri" | Cost / speed / intelligence ağırlıkları artı isim hint'leri |
| `includeContext` | "Cross-session sızıntı" | Soft-deprecate edilmiş bağlam dahil etme modu |
| SEP-1577 | "Sampling'de tool'lar" | Sunucu-hostlu ReAct için sampling içinde tool'lara izin ver |
| Human-in-the-loop | "Kullanıcı onaylar" | Client çalıştırmadan önce sampling request'ini kullanıcıya yüzeyleştirir |
| Loop bomb | "Runaway sampling" | Sunucu-tarafı sonsuz sampling döngüsü; client rate-limit'lemelidir |
| Covert sampling | "Gizli muhakeme" | Kötü niyetli sunucu niyeti sampling prompt'larında gizler |
| Resource theft | "Kullanıcının LLM bütçesini kullanma" | Sunucu client'ı istemediği sampling'e harcamaya zorlar |
| `stopReason` | "Generation neden durdu" | `endTurn`, `stopSequence` ya da `maxTokens` |

## İleri Okuma

- [MCP — Concepts: Sampling](https://modelcontextprotocol.io/docs/concepts/sampling) — sampling'in yüksek-seviye genel bakışı
- [MCP — Client sampling spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) — kanonik `sampling/createMessage` şekli
- [MCP — GitHub SEP-1577](https://github.com/modelcontextprotocol/modelcontextprotocol) — sampling içindeki tool'lar için Spec Evolution Proposal (deneysel)
- [Unit 42 — MCP attack vectors](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/) — covert sampling ve resource-theft desenleri
- [Speakeasy — MCP sampling core concept](https://www.speakeasy.com/mcp/core-concepts/sampling) — client-tarafı kod örnekleriyle gezinti
