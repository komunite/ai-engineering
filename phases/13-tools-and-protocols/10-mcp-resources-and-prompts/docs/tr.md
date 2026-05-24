# MCP Resource'lar ve Prompt'lar — Tool'ların Ötesinde Context Exposure

> Tool'lar MCP dikkatinin %90'ını alır. Diğer iki sunucu primitive'i farklı sorunları çözer. Resource'lar okuma için veri açar; prompt'lar yeniden kullanılabilir şablonları slash-komutlar olarak açar. Birçok sunucu okuyuşları tool'larla sarmak yerine resource'ları, client prompt'larında workflow'ları hard-code etmek yerine prompt'ları kullanmalıdır. Bu ders karar kuralını adlandırır ve `resources/*` ve `prompts/*` mesajlarını gezer.

**Tür:** Yapım
**Diller:** Python (stdlib, resource + prompt handler)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Belirli bir domain için bir capability'yi tool, resource ya da prompt olarak açma arasında karar ver.
- `resources/list`, `resources/read`, `resources/subscribe` implemente et ve `notifications/resources/updated`'ı ele al.
- Argüman şablonları ile `prompts/list` ve `prompts/get` implemente et.
- Host'un prompt'ları slash-komut olarak yüzeyleştirdiğini vs otomatik enjekte edilen bağlam olarak yüzeyleştirdiğini tanı.

## Sorun

Bir notes uygulaması için naif bir MCP sunucusu her şeyi tool olarak açar: `notes_read`, `notes_list`, `notes_search`. Bu her veri erişimini model-sürülü bir tool çağrısına sarar. Sonuçlar:

- Modelin, bağlamdan yararlanabilecek her sorgu için `notes_read`'i çağırıp çağırmayacağına karar vermesi gerekir.
- Read-only içerik, host'un yan paneline subscribe edilemez ya da stream'lenemez.
- Client UI'ları (Claude Desktop'un resource attachment paneli, Cursor'un "Include file" picker'ı) veriyi yüzeyleştiremez.

Doğru bölüm: veriyi resource olarak aç, mutate eden ya da hesaplanan aksiyonları tool olarak aç, yeniden kullanılabilir çok-adımlı workflow'ları prompt olarak aç. Her primitive'in kendi UX affordance'ı ve erişim deseni vardır.

## Kavram

### Tools vs resources vs prompts — karar kuralı

| Capability | Primitive |
|------------|-----------|
| Kullanıcı veriyi aramak, filtrelemek ya da dönüştürmek istiyor | tool |
| Kullanıcı host'un bu veriyi bağlam olarak dahil etmesini istiyor | resource |
| Kullanıcı yeniden çalıştırabileceği template'li bir workflow istiyor | prompt |

Rehber: model her ilgili sorguda onu çağırmaktan yararlanacaksa, o bir tool'dur. Kullanıcı onu bir konuşmaya iliştirerek yararlanacaksa, o bir resource'tur. Kullanıcının yeniden kullanmak istediği birim tüm çok-adımlı bir workflow ise, o bir prompt'tur.

### Resource'lar

`resources/list` `{resources: [{uri, name, mimeType, description?}]}` döndürür. `resources/read` `{uri}` alır ve `{contents: [{uri, mimeType, text | blob}]}` döndürür.

URI'lar adreslenebilir herhangi bir şey olabilir:

- `file:///Users/alice/notes/mcp.md`
- `postgres://my-db/query/SELECT ...`
- `notes://note-14` (custom şema)
- `memory://session-2026-04-22/recent` (sunucuya özgü)

`contents[]` hem text hem binary destekler. Binary, bir `mimeType` artı base64-encoded string olarak `blob` kullanır.

### Resource subscription'ları

Capability'lerde `{resources: {subscribe: true}}` bildir. Client `resources/subscribe {uri}` çağırır. Sunucu resource değiştiğinde `notifications/resources/updated {uri}` gönderir. Client yeniden okur.

Kullanım durumu: resource'ları diskte dosyalar olan bir notes sunucusu; bir file watcher update notification'larını tetikler; Claude Desktop dosya host dışında düzenlendiğinde dosyayı bağlama yeniden çeker.

### Resource template'leri (2025-11-25 eklemesi)

`resourceTemplates` parametreli bir URI pattern'i açmana izin verir: `id` completion target olacak şekilde `notes://{id}`. Client resource picker'da id'leri autocomplete edebilir.

### Prompt'lar

`prompts/list` `{prompts: [{name, description, arguments?}]}` döndürür. `prompts/get` `{name, arguments}` alır ve `{description, messages: [{role, content}]}` döndürür.

Bir prompt, host'un modeline beslediği bir mesaj listesine doldurulan bir şablondur. Örneğin, bir `code_review` prompt'u bir `file_path` argümanı alır ve üç-mesajlı bir sekans döndürür: bir system mesajı, dosya gövdesi içeren bir user mesajı ve bir muhakeme şablonu ile bir assistant kickoff'u.

### Host'lar ve prompt'lar

Claude Desktop, VS Code ve Cursor chat UI'sında prompt'ları slash-komutlar olarak açar. Kullanıcı `/code_review` yazar ve bir form'dan argümanları seçer. Sunucunun prompt'u "kullanıcı kısayolu" ile "modele gönderilen tam prompt" arasındaki sözleşmedir.

Her client henüz prompt'ları desteklemez — capability negotiation'ı kontrol et. Prompt capability'si bildirilmiş bir sunucu ama prompt desteği olmayan bir client slash-komutları sadece göremez.

### "list changed" notification'ı

Hem resource'lar hem prompt'lar küme mutate olduğunda `notifications/list_changed` yayar. 20 yeni not import etmiş bir notes sunucusu `notifications/resources/list_changed` yayar; client eklemeleri almak için `resources/list`'i yeniden çağırır.

### Content type konvansiyonları

Text için: `mimeType: "text/plain"`, `text/markdown`, `application/json`.
Binary için: `image/png`, `application/pdf`, artı `blob` alanı.
MCP Apps için (Ders 14): bir `ui://` URI'da `text/html;profile=mcp-app`.

### Dinamik resource'lar

Bir resource URI'nin statik bir dosyaya karşılık gelmesi gerekmez. `notes://recent` her okumada en son beş notu döndürebilir. `db://query/users/active` parametreli bir sorgu yürütebilir. Sunucu içeriği dinamik olarak hesaplamakta serbesttir.

Kural: client URI ile cache'leyebiliyorsa, URI stabil olmalıdır. Hesaplama tek-seferlikse, URI bir timestamp ya da nonce içermelidir, böylece client cache eskimez.

### Subscription'lar vs polling

Subscription-yetenekli client'lar `notifications/resources/updated` üzerinden sunucu push'u alır. Subscription öncesi client'lar ya da bunu desteklemeyen host'lar yeniden okuyarak poll eder. İkisi de spec-uyumludur. Sunucunun capability bildirimi client'a hangisini desteklediğini söyler.

Subscription'ların maliyeti: sunucuda session başına state (kim neye subscribe). Subscribe edilmiş kümeyi sınırlı tut; bağlantısı kopan client'lar time out olmalıdır.

### Prompt'lar vs system prompt'ları

MCP'deki prompt'lar system prompt değildir. Host'un system prompt'u (kendi operasyon talimatları) ve MCP prompt'ları (kullanıcının çağırdığı sunucu-tarafından sağlanan şablonlar) yan yana yaşar. İyi davranan bir client, asla bir sunucu prompt'unun kendi system prompt'unu override etmesine izin vermez; onları katmanlar.

## Kullan

`code/main.py` Ders 07'deki notes sunucusunu şununla genişletir:

- `resources/subscribe` desteğiyle not başına resource'lar (`notes://note-1`, vb.).
- Üç-mesajlı bir şablona render olan bir `review_note` prompt'u.
- Bir not değiştirildiğinde `notifications/resources/updated` yayan bir file-watcher simülasyonu.
- Her zaman en son beş notu döndüren bir `notes://recent` dinamik resource'u.

Tam akışı görmek için demoyu çalıştır.

## Yayınla

Bu ders `outputs/skill-primitive-splitter.md` üretir. Önerilen bir MCP sunucusu verildiğinde, skill her capability'yi bir gerekçe ile tool / resource / prompt olarak kategorize eder.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. İlk resource listesini gözlemle, sonra bir not düzenlemesini tetikle ve `notifications/resources/updated` event'inin tetiklendiğini doğrula.

2. Bir `resources/list_changed` emitter ekle: yeni bir not oluşturulduğunda, client'ların yeniden keşfetmesi için notification'u gönder.

3. Bir GitHub MCP sunucusu için üç prompt tasarla: `summarize_pr`, `triage_issue`, `release_notes`. Her biri argüman şemalarıyla. Prompt gövdesi daha fazla düzenleme olmadan çalıştırılabilir olmalı.

4. Ders 07 sunucusundaki mevcut bir tool'u al ve tool olarak mı kalması gerektiğini yoksa bir resource artı tool çiftine mi bölünmesi gerektiğini sınıflandır. Tek bir cümleyle gerekçelendir.

5. Spec'in `server/resources` ve `server/prompts` bölümlerini oku. `resources/read`'te nadiren doldurulan ama spec-destekli olan bir alanı tanımla. İpucu: resource content'teki `_meta`'ya bak.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Resource | "Açılan veri" | Host'un okuyabileceği URI-adreslenebilir içerik |
| Resource URI | "Veriye pointer" | Şema-prefixli tanımlayıcı (`file://`, `notes://`, vb.) |
| `resources/subscribe` | "Değişiklikleri izle" | Belirli bir URI için client-opt-in sunucu-push güncellemeleri |
| `notifications/resources/updated` | "Resource değişti" | Subscribe edilmiş bir resource'un yeni içeriği olduğunun client'a sinyali |
| Resource template | "Parametreli URI" | Host picker'ı için completion ipuçları olan URI pattern'i |
| Prompt | "Slash-komut şablonu" | Argüman slot'larıyla isimlendirilmiş çok-mesajlı şablon |
| Prompt argümanları | "Şablon input'ları" | Host'un render etmeden önce topladığı tipli parametreler |
| `prompts/get` | "Şablonu render et" | Sunucu doldurulmuş mesaj listesini döndürür |
| Content bloğu | "Tipli chunk" | `{type: text | image | resource | ui_resource}` |
| Slash-komut UX | "Kullanıcı kısayolu" | Host prompt'ları `/` ile başlayan komutlar olarak yüzeyleştirir |

## İleri Okuma

- [MCP — Concepts: Resources](https://modelcontextprotocol.io/docs/concepts/resources) — resource URI'leri, subscription'lar ve template'ler
- [MCP — Concepts: Prompts](https://modelcontextprotocol.io/docs/concepts/prompts) — prompt template'leri ve slash-komut entegrasyonu
- [MCP — Server resources spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/resources) — tam `resources/*` mesaj referansı
- [MCP — Server prompts spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts) — tam `prompts/*` mesaj referansı
- [MCP — Protocol info site: resources](https://modelcontextprotocol.info/docs/concepts/resources/) — resmi dokümanlar üzerinde genişleyen topluluk rehberi
