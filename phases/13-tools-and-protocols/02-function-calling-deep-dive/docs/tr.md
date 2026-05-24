# Function Calling Derinlemesine — OpenAI, Anthropic, Gemini

> Üç frontier sağlayıcı 2024'te aynı tool-call döngüsünde birleşti ve sonra diğer her şeyde ayrıldı. OpenAI `tools` ve `tool_calls` kullanıyor. Anthropic `tool_use` ve `tool_result` blokları kullanıyor. Gemini `functionDeclarations` ve unique-id korelasyonu kullanıyor. Bu ders, bir sağlayıcıda yayınlanan kod başka birine port edildiğinde kırılmasın diye üçünü yan yana fark eder.

**Tür:** Yapım
**Diller:** Python (stdlib, schema translator'lar)
**Ön koşullar:** Faz 13 · 01 (tool interface)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- OpenAI, Anthropic ve Gemini function-calling payload'ları arasındaki üç şekil farkını söyle (declaration, call, result).
- Bir tool declaration'ını üç sağlayıcı formatında çevir ve strict-mode kısıtlamalarının nerede ayrılacağını tahmin et.
- Tool çağrılarını zorlamak, yasaklamak ya da otomatik seçtirmek için her sağlayıcıda `tool_choice` kullan.
- Sağlayıcı başına sert sınırları (tool sayısı, şema derinliği, argüman uzunluğu) ve sınırlar ihlal edildiğinde her birinin yaydığı hata imzalarını bil.

## Sorun

Bir function-calling request'inin şekli sağlayıcıya göre farklılaşır. 2026 üretim yığınlarından üç somut örnek:

**OpenAI Chat Completions / Responses API.** `tools: [{type: "function", function: {name, description, parameters, strict}}]` geçirirsin. Modelin yanıtı `choices[0].message.tool_calls: [{id, type: "function", function: {name, arguments}}]` içerir; burada `arguments` parse etmen gereken bir JSON string'idir. Strict mode (`strict: true`) kısıtlı decoding ile şema uyumunu zorlar.

**Anthropic Messages API.** `tools: [{name, description, input_schema}]` geçirirsin. Yanıt `content: [{type: "text"}, {type: "tool_use", id, name, input}]` olarak geri gelir. `input` zaten parse edilmiştir (string değil, obje). Bir `{type: "tool_result", tool_use_id, content}` bloğu içeren yeni bir `user` mesajıyla yanıt verirsin.

**Google Gemini API.** `tools: [{functionDeclarations: [{name, description, parameters}]}]` geçirirsin (`functionDeclarations` altında iç içe). Yanıt `candidates[0].content.parts: [{functionCall: {name, args, id}}]` olarak gelir; burada `id` parallel-call korelasyonu için Gemini 3 ve üstünde unique'dir. `{functionResponse: {name, id, response}}` ile yanıt verirsin.

Aynı döngü. Farklı alan isimleri, farklı iç içe geçme, farklı string-vs-obje konvansiyonları, farklı korelasyon mekanizmaları. OpenAI'da hava durumu agent'ı yazan bir takım yalnızca tesisat için Anthropic'e iki günlük, Gemini'ye bir günlük daha port maliyeti öder.

Bu ders, üç formatı tek kanonik bir tool declaration'a birleştiren ve kenarda yönlendirme yapan bir translator inşa eder. Faz 13 · 17 aynı deseni bir LLM gateway'ine genelleştirir.

## Kavram

### Ortak yapı

Her sağlayıcının beş şeye ihtiyacı var:

1. **Tool listesi.** Tool başına name, description ve input schema.
2. **Tool choice.** Belirli bir tool'u zorla, tool'ları yasakla ya da modele bırak.
3. **Call emission.** Tool ve argümanları adlandıran yapılandırılmış çıktı.
4. **Call id.** Yanıtı doğru çağrıyla korele et (paralel için önemli).
5. **Result injection.** Sonucu çağrıya bağlayan bir mesaj ya da blok.

### Şekil farkları, alan alan

| Yön | OpenAI | Anthropic | Gemini |
|--------|--------|-----------|--------|
| Declaration zarfı | `{type: "function", function: {...}}` | `{name, description, input_schema}` | `{functionDeclarations: [{...}]}` |
| Schema alanı | `parameters` | `input_schema` | `parameters` |
| Yanıt container'ı | assistant mesajındaki `tool_calls[]` | `tool_use` tipinde `content[]` | `functionCall` tipinde `parts[]` |
| Argümanlar tipi | stringified JSON | parse edilmiş obje | parse edilmiş obje |
| Id formatı | `call_...` (OpenAI üretir) | `toolu_...` (Anthropic) | UUID (Gemini 3+) |
| Result bloğu | rol `tool`, `tool_call_id` | `tool_result` ile `user`, `tool_use_id` | eşleşen `id` ile `functionResponse` |
| Bir tool'u zorla | `tool_choice: {type: "function", function: {name}}` | `tool_choice: {type: "tool", name}` | `tool_config: {function_calling_config: {mode: "ANY"}}` |
| Tool'ları yasakla | `tool_choice: "none"` | `tool_choice: {type: "none"}` | `mode: "NONE"` |
| Strict schema | `strict: true` | schema-is-schema (her zaman zorlanır) | request seviyesinde `responseSchema` |

### Gerçekten çarpacağın limitler

- **OpenAI.** Request başına 128 tool. Şema derinliği 5. Argüman string'i <= 8192 byte. Strict mode `$ref` istemez, örtüşmeli `oneOf`/`anyOf`/`allOf` istemez, her property `required`'da listelenmeli.
- **Anthropic.** Request başına 64 tool. Şema derinliği efektif olarak sınırsız ama pratik limit 10. Strict-mode bayrağı yok; şema bir sözleşmedir ve model uyma eğilimindedir.
- **Gemini.** Request başına 64 function. Şema tipleri OpenAPI 3.0 alt kümesi (JSON Schema 2020-12'den hafif sapma). Paralel çağrılar Gemini 3'ten beri unique-id.

### `tool_choice` davranışı

Herkesin desteklediği üç mod, farklı isimlerle.

- **Auto.** Model tool ya da text seçer. Varsayılan.
- **Required / Any.** Model en az bir tool çağırmalıdır.
- **None.** Model tool çağıramaz.

Artı her sağlayıcıya özgü bir mod:

- **OpenAI.** Belirli bir tool'u isme göre zorla.
- **Anthropic.** Belirli bir tool'u isme göre zorla; `disable_parallel_tool_use` bayrağı tek vs çoklu ayırır.
- **Gemini.** `mode: "VALIDATED"` model niyetinden bağımsız olarak her yanıtı bir schema validator'dan geçirir.

### Paralel çağrılar

OpenAI'ın `parallel_tool_calls: true`'su (varsayılan) tek bir assistant mesajında birden fazla çağrı yayar. Hepsini çalıştırırsın ve `tool_call_id` başına bir girdi içeren batched tool-role mesajıyla yanıt verirsin. Anthropic tarihsel olarak tek-çağrıydı; `disable_parallel_tool_use: false` (Claude 3.5'ten itibaren varsayılan) çokluyu etkinleştirir. Gemini 2 paralel çağrılara izin verdi ama stabil id vermedi; Gemini 3 sıra dışı yanıtların temiz korele edilmesi için UUID'ler ekler.

### Streaming

Üçü de stream'lenen tool call'ları destekler. Wire formatı farklılaşır:

- **OpenAI.** `tool_calls[i].function.arguments` delta chunk'ları artımlı olarak gelir. `finish_reason: "tool_calls"` olana kadar biriktirirsin.
- **Anthropic.** Block-start / block-delta / block-stop event'leri. `input_json_delta` chunk'ları kısmi argümanları taşır.
- **Gemini.** `streamFunctionCallArguments` (Gemini 3'te yeni) bir `functionCallId` ile chunk'lar yayar, böylece birden fazla paralel çağrı interleave olabilir.

Faz 13 · 03 paralel + streaming reassembly'de derinleşir. Bu ders declaration ve tek-çağrı şekillerine odaklanır.

### Hatalar ve onarım

Geçersiz-argüman hataları da farklı görünür.

- **OpenAI (non-strict).** Model `arguments: "{bad json}"` döndürür, JSON parse başarısız olur, bir hata mesajı enjekte edip yeniden çağırırsın.
- **OpenAI (strict).** Doğrulama decoding sırasında olur; geçersiz JSON imkansızdır ama `refusal` görünebilir.
- **Anthropic.** `input` beklenmeyen alanlar içerebilir; şema yol gösterici. Sunucu tarafında doğrula.
- **Gemini.** OpenAPI 3.0 garipliği: obje alanlarındaki `enum` sessizce göz ardı edilir; kendin doğrula.

### Translator deseni

Kodundaki kanonik bir tool declaration şöyle görünür (şekli sen seçersin):

```python
Tool(
    name="get_weather",
    description="Use when ...",
    input_schema={"type": "object", "properties": {...}, "required": [...]},
    strict=True,
)
```

Üç ufak fonksiyon onu üç sağlayıcı şekline çevirir. `code/main.py`'daki harness tam olarak bunu yapar, sonra sahte bir tool call'u her sağlayıcının yanıt şekline round-trip yapar. Network gerektirmez — bu ders şekilleri öğretir, HTTP'yi değil.

Üretim takımları bu translator'ı `AbstractToolset` (Pydantic AI), `UniversalToolNode` (LangGraph) ya da `BaseTool` (LlamaIndex) içine sarar. Faz 13 · 17, üçünden herhangi birinin önünde OpenAI-şeklinde bir API açan bir gateway yayınlar.

## Kullan

`code/main.py` bir kanonik `Tool` dataclass'ı ve OpenAI, Anthropic ve Gemini declaration JSON'unu yayan üç translator tanımlar. Sonra her şekildeki el-yapımı bir sağlayıcı yanıtını aynı kanonik call objesine parse eder, alttaki semantiğin aynı olduğunu göstererek. Çalıştır ve üç declaration'ı yan yana diff'le.

Bakılacak şeyler:

- Üç declaration bloğu yalnızca zarf ve alan isimlerinde farklılaşır.
- Üç yanıt bloğu, çağrının nerede yaşadığında farklılaşır (top-level `tool_calls`, `content[]` bloğu, `parts[]` girdisi).
- Tek bir `canonical_call()` fonksiyonu üç yanıt şeklinin hepsinden `{id, name, args}` çıkarır.

## Yayınla

Bu ders `outputs/skill-provider-portability-audit.md` üretir. Bir sağlayıcıya karşı bir function-calling entegrasyonu verildiğinde, skill bir portability audit üretir: hangi sağlayıcı limitlerine dayandığı, hangi alanların yeniden adlandırılması gerektiği ve her diğer sağlayıcıya port edildiğinde ne kırıldığı.

## Alıştırmalar

1. `code/main.py`'ı çalıştır ve üç sağlayıcı declaration JSON'unun hepsinin aynı alt `Tool` objesine serialize olduğunu doğrula. Kanonik tool'u bir enum parametre eklemek için değiştir ve yalnızca Gemini translator'ının OpenAPI gariplikini ele alması gerektiğini doğrula.

2. Bir modelin `list_tools` ya da discovery çağrısından sonra döndürdüğü tool listesini çıkaran her sağlayıcı için bir `ListToolsResponse` parser ekle. OpenAI'da native olan yok; bu asimetriyi not et.

3. `tool_choice` dönüşümünü implemente et: kanonik bir `ToolChoice(mode="force", tool_name="x")`'i üç sağlayıcı şeklinin hepsine eşle. Sonra `mode="any"` ve `mode="none"`'u eşle. Dersin diff tablosunu kontrol et.

4. Üç sağlayıcıdan birini seç ve function-calling rehberini başından sonuna oku. Şema spec'inde diğer ikisinin desteklemediği bir alan bul. Adaylar: OpenAI `strict`, Anthropic `disable_parallel_tool_use`, Gemini `function_calling_config.allowed_function_names`.

5. Bir test vektörü yaz: argümanları bildirilen şemayı ihlal eden bir tool call. Her sağlayıcının validator'ından geçir (Ders 01'deki stdlib olan proxy olarak iş görür) ve hangi hataların atıldığını kaydet. Üretimde strict'lik için hangi sağlayıcıyı kullanacağını belgele.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Function calling | "Tool use" | Yapılandırılmış tool-call yayımı için sağlayıcı-seviyesi API |
| Tool declaration | "Tool spec" | Name + description + JSON Schema input payload |
| `tool_choice` | "Force / forbid" | Auto / required / none / specific-name modları |
| Strict mode | "Şema zorlaması" | Decoding'i şemaya uyacak şekilde kısıtlayan OpenAI bayrağı |
| `tool_use` bloğu | "Anthropic'in call şekli" | id, name, input içeren inline content bloğu |
| `functionCall` part | "Gemini'nin call şekli" | name, args ve id içeren bir `parts[]` girdisi |
| Arguments-as-string | "Stringified JSON" | OpenAI args'ı obje değil JSON string'i olarak döndürür |
| Parallel tool calls | "Tek turda fan-out" | Tek bir assistant mesajında birden fazla tool çağrısı |
| Refusal | "Model reddediyor" | Bir çağrı yerine yalnızca strict-mode refusal bloğu |
| OpenAPI 3.0 alt kümesi | "Gemini şema garipliği" | Gemini, minor farklarla JSON-Schema'ya benzer bir dialect kullanır |

## İleri Okuma

- [OpenAI — Function calling guide](https://platform.openai.com/docs/guides/function-calling) — strict mode ve paralel çağrılar dahil kanonik referans
- [Anthropic — Tool use overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) — `tool_use` ve `tool_result` blok semantiği
- [Google — Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling) — paralel çağrılar, unique id'ler ve OpenAPI alt kümesi
- [Vertex AI — Function calling reference](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling) — Gemini'nin enterprise yüzeyi
- [OpenAI — Structured outputs](https://platform.openai.com/docs/guides/structured-outputs) — strict-mode şema zorlama ayrıntıları
