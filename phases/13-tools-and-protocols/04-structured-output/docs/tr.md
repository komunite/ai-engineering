# Structured Output — JSON Schema, Pydantic, Zod, Constrained Decoding

> "Modelden JSON döndürmesini kibarca iste" frontier modellerde bile %5 ila %15 zaman başarısız olur. Structured output'lar o boşluğu constrained decoding ile kapatır: model, şemayı ihlal edecek bir token yaymaktan kelimenin tam anlamıyla alıkonur. OpenAI'ın strict mode'u, Anthropic'in şema-tipli tool use'u, Gemini'nin `responseSchema`'sı, Pydantic AI'ın `output_type`'ı ve Zod'un `.parse`'ı aynı fikrin beş yüzey formudur. Bu ders öğrencilerin her üretim çıkarım pipeline'ı için kullanacağı schema validator'ını ve strict-mode sözleşmesini inşa eder.

**Tür:** Yapım
**Diller:** Python (stdlib, JSON Schema 2020-12 alt kümesi)
**Ön koşullar:** Faz 13 · 02 (function calling derinlemesine)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Bir çıkarım hedefi için doğru kısıtlamaları (enum, min/max, required, pattern) kullanarak bir JSON Schema 2020-12 yaz.
- Strict mode ve constrained decoding'in "üretimden sonra doğrula"dan neden farklı garantiler verdiğini açıkla.
- Üç başarısızlık modunu ayırt et: parse hatası, şema ihlali, model reddi.
- Tipli onarım ve tipli reddetme ele alma ile bir çıkarım pipeline'ı yayınla.

## Sorun

Bir satın alma siparişi e-postası okuyan bir agent serbest text'i `{customer, line_items, total_usd}`'a çevirmek zorundadır. Üç yaklaşım.

**Yaklaşım bir: JSON için prompt'la.** "JSON ile customer, line_items, total_usd alanlarıyla yanıt ver." Frontier modellerde %85 ila %95 zaman çalışır. Altı şekilde başarısız olur: eksik brace, sondaki virgül, yanlış tipler, halüsinasyonlu alanlar, token limitinde kesilme, "İşte JSON'unuz:" gibi sızdırılan prose.

**Yaklaşım iki: üretimden sonra doğrula.** Serbestçe üret, parse et, şemaya karşı doğrula, başarısızlıkta yeniden dene. Güvenilir ama pahalı — her retry için ödersin ve truncation bug'ları her oluşumda bir ekstra tur maliyetlidir.

**Yaklaşım üç: constrained decoding.** Sağlayıcı şemayı decode zamanında zorlar. Geçersiz token'lar sampling dağılımından maskelenir. Çıktının parse olacağı garantilidir ve doğrulanacağı garantilidir. Başarısızlık tek bir moda kollapse olur: refusal (model input'un şemaya uymadığına karar verir).

Her 2026 frontier sağlayıcısı üçüncü yaklaşımın bir formunu yayınlar.

- **OpenAI.** `response_format: {type: "json_schema", strict: true}` artı model reddederse yanıtta `refusal`.
- **Anthropic.** `tool_use` input'larında şema zorlaması; `stop_reason: "refusal"` diye bir şey yok ama tool call'suz `end_turn` sinyaldir.
- **Gemini.** Request seviyesinde `responseSchema`; 2026'da Gemini seçili tipler için token-seviyesi grammar kısıtlamaları yayınlıyor.
- **Pydantic AI.** `output_type=InvoiceModel` `InvoiceModel`'a tipli yapılandırılmış bir `RunResult` yayar.
- **Zod (TypeScript).** Sağlayıcı çıktısını bir Zod şemasına karşı doğrulayan runtime parser; OpenAI'ın `beta.chat.completions.parse`'ı ile eşleşir.

Ortak iplik: şemayı bir kere bildir, end-to-end zorla.

## Kavram

### JSON Schema 2020-12 — ortak dil

Her sağlayıcı JSON Schema 2020-12'yi kabul eder. En çok kullandığın yapılar:

- `type`: `object`, `array`, `string`, `number`, `integer`, `boolean`, `null`'dan biri.
- `properties`: alan isminden alt şemaya map.
- `required`: görünmesi gereken alan isimleri listesi.
- `enum`: izin verilen kapalı değer kümesi.
- `minimum` / `maximum` (sayılar), `minLength` / `maxLength` / `pattern` (string'ler).
- `items`: her array elemanına uygulanan alt şema.
- `additionalProperties`: `false` ekstra alanları yasaklar (varsayılan moda göre değişir).

OpenAI strict mode üç gereksinim ekler: her property `required`'da listelenmeli, her yerde `additionalProperties: false` ve çözülmemiş `$ref` yok. Bunları kırarsan API request zamanında 400 döner.

### Pydantic, Python binding'i

Pydantic v2, `model_json_schema()` üzerinden dataclass-şekilli modellerden JSON Schema üretir. Pydantic AI bunu öyle sarar ki şöyle yazarsın:

```python
class Invoice(BaseModel):
    customer: str
    line_items: list[LineItem]
    total_usd: Decimal
```

ve agent framework şemayı kenarda OpenAI strict mode, Anthropic `input_schema` ya da Gemini `responseSchema`'ya çevirir. Modelin çıktısı tipli `Invoice` instance olarak geri gelir. Doğrulama hataları tipli hata yollarıyla `ValidationError` raise eder.

### Zod, TypeScript binding'i

Zod (`z.object({customer: z.string(), ...})`) TS eşdeğeridir. OpenAI'ın Node SDK'sı API'nin JSON Schema payload'una çeviren `zodResponseFormat(Invoice)` açar.

### Refusal'lar

Strict mode modeli yanıtlamaya zorlayamaz. Input şemaya sığamıyorsa ("e-posta bir şiirdi, fatura değil"), model nedeni içeren bir `refusal` alanı yayar. Kodun bunu birinci sınıf bir sonuç olarak ele almalı, bir başarısızlık olarak değil. Refusal aynı zamanda güvenlik sinyali olarak yararlıdır: korumalı içerik e-postasından kredi kartı numarası çıkarması istenen bir model, ekli güvenlik nedeniyle bir refusal döner.

### Açıkta constrained decoding

Open-weights uygulamaları üç teknik kullanır.

1. **Grammar-tabanlı decoding** (`outlines`, `guidance`, `lm-format-enforcer`): şemadan deterministik bir finite automaton inşa et; her adımda, FSM'i ihlal edecek token'ların logit'lerini maskele.
2. **JSON parser ile logit masking**: streaming JSON parser'ı modelle lockstep çalıştır; her adımda geçerli-sonraki-token kümesini hesapla.
3. **Verifier'lı speculative decoding**: ucuz taslak model token önerir, verifier şemayı zorlar.

Ticari sağlayıcılar perde arkasında bunlardan birini seçer. 2026 state of the art kısa yapılandırılmış çıktılar için düz üretimden daha hızlı ve uzun olanlarda kabaca aynı hızdadır.

### Üç başarısızlık modu

1. **Parse hatası.** Çıktı geçerli JSON değil. Strict mode altında olamaz. Non-strict sağlayıcılarda hâlâ olabilir.
2. **Şema ihlali.** Çıktı parse olur ama şemayı ihlal eder. Strict mode altında olamaz. Onun dışında yaygın.
3. **Refusal.** Model reddediyor. Tipli sonuç olarak ele alınmalı.

### Retry stratejisi

Strict mode'un dışındaysan (Anthropic tool use, non-strict OpenAI, eski Gemini), recovery deseni şudur:

```
üret -> parse et -> doğrula -> başarısızsa, hatayı enjekte et ve yeniden dene, maks 3x
```

Bir retry genellikle yeterlidir. Üç retry zayıf-model titremelerini yakalar. Üçün ötesi kötü bir şemanın işaretidir: model bazı input'lar için tatmin edemez ve prompt ya da şema düzeltilmelidir.

### Küçük-model desteği

Constrained decoding küçük modellerde çalışır. Grammar zorlamalı 3B-parametreli açık bir model, yapılandırılmış görevlerde raw prompting'li 70B-parametreli bir modelden daha iyi performans gösterir. Structured output'ların üretim için önemli olmasının ana nedeni budur: güvenilirliği model boyutundan ayırır.

## Kullan

`code/main.py` stdlib'de minimal bir JSON Schema 2020-12 validator yayınlar (types, required, enum, min/max, pattern, items, additionalProperties). Bir `Invoice` şemasını sarar ve sahte bir LLM çıktısını validator'dan geçirir, parse hatası, şema ihlali ve refusal yollarını gösterir. Üretimde sahte çıktıyı herhangi bir sağlayıcının gerçek yanıtıyla değiştir.

Bakılacak şeyler:

- Validator yol ve mesajla tipli bir `[ValidationError]` listesi döndürür. Retry prompt'a yüzeyleştirmek istediğin şekil budur.
- Refusal dalı retry YAPMAZ. Loglar ve tipli bir refusal döner. Faz 14 · 09 refusal'ları bir güvenlik sinyali olarak kullanır.
- `additionalProperties: false` kontrolü adversarial test input'unda devreye girer, strict mode'un halüsinasyonlu alanlara kapıyı neden kapadığını gösterir.

## Yayınla

Bu ders `outputs/skill-structured-output-designer.md` üretir. Bir serbest-text çıkarım hedefi verildiğinde (faturalar, destek talepleri, özgeçmişler, vb.), skill strict-mode-uyumlu bir JSON Schema 2020-12 ve onu yansıtan bir Pydantic modeli üretir, tipli refusal ve retry ele alma stub'lanmış olarak.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. `total_usd`'si negatif bir sayı olan dördüncü bir test case ekle. Validator'ın `minimum` kısıtlama yoluyla reddettiğini doğrula.

2. Validator'ı bir discriminator'lı `oneOf`'u desteklemek için genişlet. Yaygın durum: `line_item` ya bir ürün ya da bir servistir, `kind` ile etiketlenir. Strict mode'un burada ince kuralları vardır; OpenAI'ın structured output'lar rehberini kontrol et.

3. Aynı Invoice şemasını bir Pydantic BaseModel olarak yaz ve `model_json_schema()` çıktısını el-yapımı şemanla karşılaştır. Pydantic'in varsayılan olarak ayarladığı, el-yapımı versiyonun atladığı bir alanı tanımla.

4. Refusal oranlarını ölç. Çıkarılamayacak on input oluştur (bir şarkı sözü, bir matematik kanıtı, boş bir e-posta) ve strict mode ile gerçek bir sağlayıcıdan geçir. Halüsinasyonlu çıktılara karşı refusal sayısını say. Bu, refusal-farkındalıklı retry'lar için ground truth'undur.

5. OpenAI'ın structured output'lar rehberini başından sonuna oku. Strict mode'da açıkça yasakladığı, ama düz JSON Schema'nın izin verdiği bir yapıyı tanımla. Sonra yasak yapıyı non-essential olarak kullanan bir şema tasarla ve strict-uyumlu olacak şekilde refactor et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| JSON Schema 2020-12 | "Şema spec'i" | Her modern sağlayıcının konuştuğu IETF-draft şema dialect'i |
| Strict mode | "Garantili şema" | Constrained decoding ile şemayı zorlayan OpenAI bayrağı |
| Constrained decoding | "Logit masking" | Geçersiz sonraki-token'ları maskeleyen decode-zamanı zorlama |
| Refusal | "Model reddediyor" | Input şemaya sığamadığında tipli sonuç |
| Parse hatası | "Geçersiz JSON" | Çıktı JSON olarak parse olmadı; strict altında imkansız |
| Şema ihlali | "Yanlış şekil" | Parse oldu ama types / required / enum / range ihlal etti |
| `additionalProperties: false` | "Ekstra yok" | Bilinmeyen alanları yasaklar; OpenAI strict'te gerekli |
| Pydantic BaseModel | "Tipli çıktı" | JSON Schema yayan ve doğrulayan Python sınıfı |
| Zod şeması | "TypeScript çıktı tipi" | Sağlayıcı çıktısı doğrulaması için TS runtime şeması |
| Grammar zorlaması | "Open-weights constrained decode" | FSM-tabanlı logit masking, outlines / guidance gibi |

## İleri Okuma

- [OpenAI — Structured outputs](https://platform.openai.com/docs/guides/structured-outputs) — strict mode, refusal'lar ve şema gereksinimleri
- [OpenAI — Introducing structured outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — Ağustos 2024 launch yazısı, decoding garantisini açıklar
- [Pydantic AI — Output](https://ai.pydantic.dev/output/) — her sağlayıcıya serialize olan tipli output_type binding'leri
- [JSON Schema — 2020-12 release notes](https://json-schema.org/draft/2020-12/release-notes) — kanonik spec
- [Microsoft — Structured outputs in Azure OpenAI](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs) — enterprise deployment notları ve strict-mode uyarıları
