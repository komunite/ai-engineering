# Root'lar ve Elicitation — Scope ve Akış Ortası Kullanıcı Input'u

> Hard-code edilmiş yollar, kullanıcı farklı bir proje açtığı anda kırılır. Önceden doldurulmuş tool argümanları, kullanıcı eksik belirttiğinde kırılır. Root'lar sunucuyu kullanıcı-kontrollü bir URI kümesine scope'lar; elicitation form ya da URL üzerinden kullanıcıdan yapılandırılmış input istemek için tool çağrısının ortasında duraklar. İki client primitive'i, yaygın MCP başarısızlık modları için iki düzeltme. SEP-1036 (URL-mode elicitation, 2025-11-25) H1 2026 boyunca deneysel — ona bağımlı olmadan önce SDK versiyonlarını kontrol et.

**Tür:** Yapım
**Diller:** Python (stdlib, roots + elicitation demo)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- `roots` bildir ve `notifications/roots/list_changed`'a yanıt ver.
- Sunucu dosya operasyonlarını bildirilen root kümesinin içindeki URI'lara kısıtla.
- Tool çağrısının ortasında kullanıcıdan bir onay ya da yapılandırılmış input istemek için `elicitation/create` kullan.
- Form-mode ve URL-mode elicitation arasında seç (ikincisi deneysel; drift-risk not edildi).

## Sorun

Üretimde bir notes MCP sunucusunun çarptığı iki somut başarısızlık.

**Bozuk yol varsayımı.** Sunucu `~/notes`'a karşı yazıldı. `~/Documents/Notes`'ta notları olan farklı bir makinedeki kullanıcı, sessizce başarısız olan (dosya bulunamadı) ya da daha kötüsü, yanlış yere yazan bir tool çağrısı alır.

**Kullanıcının bileceği eksik argüman.** Kullanıcı "eski TPS report notunu sil" diyor. Model `notes_delete(title: "TPS report")` çağırır ama 2023, 2024 ve 2025'ten üç eşleşen not var. Tool tahmin edemez. "Belirsiz" ile başarısız olmak can sıkıcı; üçünde de çalışmak felaket.

Root'lar ilkini düzeltir: client `initialize`'da sunucunun dokunabileceği URI kümesini bildirir. Elicitation ikincisini düzeltir: sunucu tool çağrısını duraklatır ve kullanıcıdan hangisini seçeceğini istemek için `elicitation/create` gönderir.

## Kavram

### Root'lar

Client `initialize`'da bir root listesi bildirir:

```json
{
  "capabilities": {"roots": {"listChanged": true}}
}
```

Sunucu sonra `roots/list` çağırabilir:

```json
{"roots": [{"uri": "file:///Users/alice/Documents/Notes", "name": "Notes"}]}
```

Sunucular root'ları sınır olarak ele almalıDIR: root kümesi dışındaki herhangi bir dosya okuma ya da yazma reddedilir. Bu client tarafından zorlanmaz (sunucu hâlâ kullanıcının güvendiği koddur) ama spec-uyumlu sunucular buna saygı duyar.

Kullanıcı bir root ekler ya da kaldırdığında, client `notifications/roots/list_changed` gönderir. Sunucu `roots/list`'i yeniden çağırır ve sınırını günceller.

### Root'lar neden bir client primitive'i

Root'lar client tarafından bildirilir çünkü kullanıcının onay modelini temsil eder. Kullanıcı Claude Desktop'a "bu notes sunucusuna bu iki dizine erişim ver" dedi. Sunucu o scope'u genişletemez.

### Elicitation: form-mode varsayılan

`elicitation/create` bir form schema artı doğal-dil prompt alır:

```json
{
  "method": "elicitation/create",
  "params": {
    "message": "Delete 'TPS report'? Multiple notes match; pick one.",
    "requestedSchema": {
      "type": "object",
      "properties": {
        "note_id": {
          "type": "string",
          "enum": ["note-3", "note-7", "note-14"]
        },
        "confirm": {"type": "boolean"}
      },
      "required": ["note_id", "confirm"]
    }
  }
}
```

Client bir form render eder, kullanıcının yanıtını toplar, döndürür:

```json
{
  "action": "accept",
  "content": {"note_id": "note-14", "confirm": true}
}
```

Üç olası aksiyon: `accept` (kullanıcı doldurdu), `decline` (kullanıcı kapattı), `cancel` (kullanıcı tüm tool çağrısını iptal etti).

Form şemaları düzdür — iç içe objeler v1'de desteklenmez. SDK'lar tipik olarak tek katmandan daha karmaşık bir şeyi reddeder.

### Elicitation: URL mode (SEP-1036, deneysel)

2025-11-25'te yeni. Bir şema yerine, sunucu bir URL gönderir:

```json
{
  "method": "elicitation/create",
  "params": {
    "message": "Sign in to GitHub",
    "url": "https://github.com/login/oauth/authorize?client_id=..."
  }
}
```

Client URL'yi bir tarayıcıda açar, tamamlanmasını bekler, kullanıcı geri döndüğünde döner. Bir form'un yetersiz kaldığı OAuth akışları, ödeme yetkilendirmesi ve doküman imzalama için yararlı.

Drift-risk notu: SEP-1036 yanıt şekli hâlâ oturmaktadır; bazı SDK'lar callback URL'sini döndürür, diğerleri bir completion token döndürür. Üretimde URL mode kullanmadan önce SDK'nın release note'larını oku.

### Elicitation doğru tool olduğunda

- Yıkıcı aksiyonlardan önce kullanıcı onayı (destructive hint + elicitation).
- Belirsizlik giderme (N eşleşmeden birini seç).
- İlk çalıştırma kurulumu (API key'ler, dizinler, tercihler).
- OAuth-style akışlar (URL mode).

### Elicitation yanlış olduğunda

- Modelin prose'da sorabileceği bir tool'un required argümanlarını doldurma. Bir elicitation diyaloğu değil, normal bir re-prompt kullan.
- Yüksek-frekanslı çağrılar. Elicitation konuşmayı keser; bir döngü içinde tetikleme.
- Sunucunun sonradan doğrulayabileceği herhangi bir şey. Doğrula, bir hata döndür, modelin text'te kullanıcıya sormasına izin ver.

### Human-in-the-loop köprüsü

Elicitation artı sampling birlikte MCP'nin "human-in-the-loop" modelini etkinleştirir. Bir sunucunun agent döngüsü ya kullanıcı input'u (elicitation) ya da model muhakemesi (sampling) için duraklayabilir. Faz 13 · 11 sampling'i ele aldı; bu ders elicitation'ı ele alıyor. Tam mid-loop kontrolü için onları bir araya getir.

## Kullan

`code/main.py` notes sunucusunu şununla genişletir:

- Sunucunun root-list-changed notification'larından sonra yeniden sorguladığı `roots/list` yanıtı.
- Birden fazla not eşleştiğinde belirsizliği gidermek için `elicitation/create` kullanan bir `notes_delete` tool'u.
- İlk çalıştırma config sayfası açmak için URL-mode elicitation kullanan bir `notes_setup` tool'u (simüle).
- Bildirilen root'ların dışındaki URI'lara operasyonları reddeden bir sınır kontrolü.

Demo üç senaryo çalıştırır: happy path (bir eşleşme), belirsizlik giderme (üç eşleşme, elicitation tetikler), out-of-root-write (reddedilir).

## Yayınla

Bu ders `outputs/skill-elicitation-form-designer.md` üretir. Kullanıcı onayı ya da belirsizlik giderme gerektirebilecek bir tool verildiğinde, skill elicitation form şemasını ve mesaj template'ini tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Belirsizlik giderme yolunu tetikle; simüle kullanıcı yanıtının tool'a geri yönlendirildiğini doğrula.

2. Her seferinde elicitation onayı gerektiren yeni bir `notes_archive` tool'u ekle (destructive hint). UX'i kontrol et: bu modelin text'te yeniden sormasıyla nasıl kıyaslanır?

3. İlk çalıştırma OAuth akışı için URL-mode elicitation implemente et. Drift riskini not et ve bir SDK-versiyon guard'ı ekle.

4. `roots/list` ele almayı genişlet: bir notification geldiğinde, sunucu atomik olarak yeniden okumalı ve şimdi scope dışında olabilecek açık dosya handle'larını yeniden taramalı.

5. GitHub'daki SEP-1036 issue tartışma thread'ini oku. Sunucuların URL-mode callback'leri nasıl ele alması gerektiğini etkileyen açık bir soruyu tanımla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Root | "Onay sınırı" | Client'ın sunucunun dokunmasına izin verdiği URI |
| `roots/list` | "Sunucu scope ister" | Client mevcut root kümesini döndürür |
| `notifications/roots/list_changed` | "Kullanıcı scope değiştirdi" | Client root kümesinin değiştiğini sinyaller |
| Elicitation | "Çağrı ortasında kullanıcıya sor" | Yapılandırılmış kullanıcı input'u için sunucu-initiated request |
| `elicitation/create` | "Method" | Elicitation request'leri için JSON-RPC method'u |
| Form mode | "Şema-sürülü form" | Client UI'sında bir form olarak render edilen düz JSON Schema |
| URL mode | "Tarayıcı redirect'i" | SEP-1036 deneysel; bir URL açar ve bekler |
| `accept` / `decline` / `cancel` | "Kullanıcı yanıt sonuçları" | Sunucunun ele aldığı üç dal |
| Belirsizlik giderme | "Birini seç" | Bir tool'un N adayı olduğunda yaygın elicitation kullanım durumu |
| Düz form | "Yalnızca top-level property'ler" | Elicitation şemaları iç içe geçemez |

## İleri Okuma

- [MCP — Client roots spec](https://modelcontextprotocol.io/specification/draft/client/roots) — kanonik root'lar referansı
- [MCP — Client elicitation spec](https://modelcontextprotocol.io/specification/draft/client/elicitation) — kanonik elicitation referansı
- [Cisco — What's new in MCP elicitation, structured content, OAuth enhancements](https://blogs.cisco.com/developer/whats-new-in-mcp-elicitation-structured-content-and-oauth-enhancements) — 2025-11-25 eklemeleri gezintisi
- [MCP — GitHub SEP-1036](https://github.com/modelcontextprotocol/modelcontextprotocol) — URL-mode elicitation önerisi (deneysel, drift-risk)
- [The New Stack — How elicitation brings human-in-the-loop to AI tools](https://thenewstack.io/how-elicitation-in-mcp-brings-human-in-the-loop-to-ai-tools/) — UX gezintisi
