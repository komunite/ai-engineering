# Paralel Tool Çağrıları ve Tool'larla Streaming

> Üç bağımsız hava durumu lookup'ı seri olarak yapıldığında üç round trip eder. Paralel çalıştırıldığında toplam süre en yavaş tek çağrıya kadar düşer. Her frontier sağlayıcı artık tek bir turda birden fazla tool çağrısı yayar. Kazanım gerçek; tesisat ince. Bu ders her iki yarıyı da gezer: paralel fan-out ve stream'lenen-argüman reassembly'si, id-korelasyon tuzağına vurgu yaparak.

**Tür:** Yapım
**Diller:** Python (stdlib, thread pool + streaming harness)
**Ön koşullar:** Faz 13 · 02 (function calling derinlemesine)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- `parallel_tool_calls: true`'nun neden var olduğunu ve ne zaman devre dışı bırakılacağını açıkla.
- Paralel fan-out sırasında stream'lenen argüman chunk'larını doğru tool-call id'sine korele et.
- Erken parse etmeden, kısmi `arguments` string'lerini tam JSON'a yeniden birleştir.
- Seri vs paralel gecikmeyi gösteren üç-şehirli bir hava durumu benchmark'ı çalıştır.

## Sorun

Paralel çağrılar olmadan, "Bengaluru, Tokyo ve Zurich'te hava nasıl" sorusunu yanıtlayan bir agent şunu yapar:

```
user -> LLM
LLM -> call get_weather(Bengaluru)
host -> run executor, reply with result
LLM -> call get_weather(Tokyo)
host -> run executor, reply with result
LLM -> call get_weather(Zurich)
host -> run executor, reply with result
LLM -> final text answer
```

Üç LLM round trip, her biri executor gecikmesini de öder. Yaklaşık ideal wall-clock süresinin 4 katı.

Paralel çağrılarla:

```
user -> LLM
LLM -> call get_weather(Bengaluru); call get_weather(Tokyo); call get_weather(Zurich)
host -> run all three executors concurrently, reply with three results
LLM -> final text answer
```

Tek bir LLM round trip. Executor süresi üçünün toplamı değil maksimumudur. OpenAI, Anthropic ve Gemini'de üretim benchmark'ları fan-out workload'ları için %60 ila %70 wall-clock azalması gösteriyor.

Bedeli korelasyon karmaşıklığıdır. Üç çağrı sıra dışı tamamlandığında, sonuçların eşleşen `tool_call_id`'yi taşıması gerekir, böylece model onları sıralayabilir. Sonuçlar stream'lendiğinde, yürütmeden önce kısmi argüman parçalarını tam JSON'a birleştirmen gerekir. Gemini 3, aynı tool'a yapılan iki paralel çağrının ayırt edilemez olduğu gerçek dünya sorununu çözmek için unique id'ler ekledi.

## Kavram

### Paraleli etkinleştirme

- **OpenAI.** `parallel_tool_calls: true` varsayılan olarak açık. Seri zorlamak için `false` ayarla.
- **Anthropic.** Paralel `disable_parallel_tool_use: false` üzerinden (Claude 3.5 ve üstünde varsayılan). Seri için `true` ayarla.
- **Gemini.** Her zaman paralel-yetenekli; `tool_config.function_calling_config.mode = "AUTO"` modelin karar vermesine izin verir.

Tool'ların sıralama bağımlılıkları olduğunda (`create_file` sonra `write_file`), bir çağrının çıktısı başkasının input'unu bilgilendirdiğinde ya da rate limiter fan-out'u kaldıramadığında paraleli devre dışı bırak.

### Id korelasyonu

Modelin yaydığı her çağrının bir `id`'si vardır. Host'un döndürdüğü her sonuç aynı id'yi içermelidir. Bu olmadan, sonuçlar belirsizdir.

- **OpenAI.** Her tool-role mesajında `tool_call_id`.
- **Anthropic.** Her `tool_result` bloğunda `tool_use_id`.
- **Gemini.** Her `functionResponse`'da `id` (Gemini 3 ve üstü; Gemini 2 aynı-isimli paralel çağrılar için kırılan isimle eşleştirdi).

### Çağrıları eşzamanlı çalıştırma

Host her çağrının executor'unu kendi thread'i, coroutine'i ya da uzak worker'ında çalıştırır. En basit harness bir thread pool kullanır; üretim `asyncio.gather` ya da structured concurrency ile asyncio kullanır. Tamamlanma sırası tahmin edilemez — id, tanımlayıcıdır.

Yaygın bir bug: tamamlanma sırası yerine call-list sırasında sonuçlarla yanıt vermek. Bu genellikle çalışır çünkü model yalnızca `tool_call_id`'yi umursar, ama bir sonuç düşerse ya da tekrarlanırsa, sıra dışı submission debug'ı zorlaştırır. Açık id'lerle tamamlanma sırasında yanıtlamayı tercih et.

### Tool call'ları stream'leme

Model stream'lediğinde, `arguments` parçalar halinde gelir. Üç paralel çağrı için üç ayrı chunk stream'i wire'da interleave olur. Id başına bir akümülatöre ihtiyacın var.

Sağlayıcıya göre şekil:

- **OpenAI.** Her chunk `choices[0].delta.tool_calls[i].function.arguments` (kısmi string). Chunk `index` (call listesindeki pozisyon) taşır. Per-index biriktirirsin, ilk göründüğünde `id`'yi okursun ve `finish_reason = "tool_calls"` olduğunda JSON parse edersin.
- **Anthropic.** Stream event'leri `message_start`, sonra `tool_use` tipinde her blok için bir `content_block_start` (id, name, boş input içerir). `content_block_delta` event'leri `input_json_delta` chunk'larını taşır. `content_block_stop` her bloğu kapatır.
- **Gemini.** `streamFunctionCallArguments` (Gemini 3 ve üstü) bir `functionCallId` ile chunk'lar yayar, böylece çağrılar temiz şekilde interleave olur. Gemini 3'ten önce streaming her seferinde bir tam çağrı döndürürdü.

### Kısmi JSON ve erken-parse tuzağı

`arguments`'ı tamamlanana kadar parse edemezsin. `{"city": "Beng` gibi kısmi JSON geçerli değildir ve raise eder. Doğru gate, sağlayıcının end-of-call sinyalidir: OpenAI'ın `finish_reason = "tool_calls"`'u, Anthropic'in `content_block_stop`'u ya da Gemini'nin stream-end event'i. Yalnızca o zaman `json.loads` dene. Daha sağlam bir yaklaşım, yapı tamamlandıkça event'ler yield eden artımlı bir JSON parser kullanır; OpenAI'ın streaming rehberi canlı "thinking" indicator gösteren UX için bunu önerir. Brace-counting tamlık testi olarak güvenilmezdir (alıntılanmış string'ler içindeki ya da escape edilmiş içerik içindeki brace'ler false positive'ler üretir) ve yalnızca informal debug heuristik'i olarak kullanılmalıdır.

### Sıra dışı tamamlanma

```
call_A: hızlı API, ilk döner
call_B: yavaş API, ikinci döner
call_C: ortalama API, üçüncü döner
```

Host yanıtının hâlâ id'leri belirtmesi gerekir:

```
[{role: "tool", tool_call_id: "call_A", content: ...},
 {role: "tool", tool_call_id: "call_B", content: ...},
 {role: "tool", tool_call_id: "call_C", content: ...}]
```

Yanıttaki sıra OpenAI ya da Anthropic'te doğruluk için önemli değildir. Gemini id'ler eşleştiği sürece herhangi bir sırayı kabul eder.

### Benchmark: seri vs paralel

`code/main.py`'daki harness 400, 600 ve 800 ms gecikmeli üç executor simüle eder. Seri toplam 1800 ms'de çalışır. Paralel max(400, 600, 800) = 800 ms'de çalışır. Fark sabittir, orantılı değildir, yani tasarruflar tool sayısıyla büyür.

Gerçek dünya uyarısı: paralel çağrılar downstream API'leri zorlar. Rate-limit'li bir servise 10-yollu fan-out başarısız olur. Faz 13 · 17 gateway-seviyesi backpressure'ı ele alır; retry semantiği gelecekteki bir faz için planlanmıştır.

### Streaming fan-out wall-clock

Modelin kendisi stream'lediğinde, tüm çağrıların finalize olmasını beklemek yerine bir çağrının argümanları tamamlanır tamamlanmaz yürütmeye başlayabilirsin. Bu OpenAI'ın belgelediği ama tüm SDK'ların açığa çıkarmadığı bir optimizasyondur. Bu dersteki harness bunu yapar: simüle stream tam bir argüman objesi yield ettiği anda, host o çağrıyı başlatır.

## Kullan

`code/main.py`'ın iki yarısı var. İlki `concurrent.futures.ThreadPoolExecutor` kullanarak üç simüle hava durumu çağrısını seri ve paralel çalıştırır ve wall-clock süresini yazdırır. İkinci yarı sahte bir streaming yanıtını oynatır — tek bir stream'de interleave olmuş üç paralel çağrı için `arguments` chunk'ları — ve `StreamAccumulator` ile id başına yeniden birleştirir. LLM yok, network yok, sadece reassembly mantığı.

Bakılacak şeyler:

- Seri timer 1.8 saniye vurur. Paralel timer aynı sahte gecikmelerde 0.8 saniye vurur.
- Akümülatör, id başına buffer'layarak ve yalnızca her çağrının JSON'u tamamlandığında parse ederek sıra dışı gelen chunk'ları ele alır.
- Executor, tüm stream'ler bitince değil, bir id'nin argümanları finalize olduğu anda başlatılır.

## Yayınla

Bu ders `outputs/skill-parallel-call-safety-check.md` üretir. Bir tool registry'si verildiğinde, skill hangi tool'ların paralelleştirilmesi güvenli olduğunu, hangilerinin sıralama bağımlılığı olduğunu ve hangilerinin downstream rate limit'lerini boğacağını denetler — tool başına `parallel_safe` bayraklarıyla revize edilmiş bir registry döner.

## Alıştırmalar

1. `code/main.py`'ı çalıştır ve simüle gecikmeleri değiştir. Paralel-seri oranının yaklaşık `max/toplam` olduğunu doğrula (gerçek çalıştırmalar, thread scheduling, serialization ve harness overhead nedeniyle idealden hafif sapar). Hangi gecikme dağılımında paralel önemini kaybeder?

2. Akümülatörü, "çağrı stream ortasında iptal edildi" durumunu buffer'ını düşürerek ve bir `cancelled` event'i yayarak ele alacak şekilde genişlet. Hangi sağlayıcı bu durumu açıkça belgeliyor? Anthropic'in `content_block_stop` semantiğini ve OpenAI'ın `finish_reason: "length"` davranışını kontrol et.

3. Thread pool'u `asyncio.gather` ile değiştir. İkisini de benchmark et. Daha düşük context-switch maliyeti yüzünden async'de küçük kazanımlar görmelisin, ama yalnızca executor'lar gerçek I/O yapıyorsa.

4. Paralelleştirilmemesi gereken iki tool seç (örn. `create_file` sonra `write_file`). Registry'ye bir `ordering_dependency` graph'ı ekle ve paralel fan-out'u o graph üzerinde gate'le. Bu bağımlılık-farkındalıklı scheduling için minimum mekanizmadır; gelecekteki bir agent-engineering fazı formalize eder.

5. OpenAI'ın paralel-function-calling bölümünü ve Anthropic'in `disable_parallel_tool_use` dokümanlarını oku. Anthropic'in paralelliği devre dışı bırakmayı önerdiği gerçek dünya tek tool tipini tanımla. (İpucu: aynı resource üzerinde consequential mutation'lar.)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Parallel tool calls | "Tek turda fan-out" | Model tek bir assistant mesajında birden fazla tool çağrısı yayar |
| `parallel_tool_calls` | "OpenAI'ın bayrağı" | Çoklu-çağrı yayımını etkinleştir ya da devre dışı bırak |
| `disable_parallel_tool_use` | "Anthropic'in tersi" | Opt-out bayrağı; varsayılan paralel etkin |
| Tool call id | "Korelasyon handle'ı" | Result mesajının echo etmesi gereken çağrı başına tanımlayıcı |
| Akümülatör | "Stream buffer" | Kısmi `arguments` chunk'ları için id başına string buffer |
| Sıra dışı tamamlanma | "Önce hızlı olan" | Paralel çağrılar tahmin edilemez sırada biter; id'ler yapıştırıcıdır |
| Bağımlılık graph'ı | "Sıralama kısıtlamaları" | Çıktıları diğer tool'ların input'larına beslenen tool'lar; paralelleştirilemez |
| Erken-parse tuzağı | "JSON.parse patladı" | Tamamlanmamış bir `arguments` string'ini parse etmeye çalışmak |
| `streamFunctionCallArguments` | "Gemini 3 özelliği" | Çağrı başına unique id'li stream'lenmiş argüman chunk'ları |
| Tamamlanma-sırası yanıt | "Hepsini bekleme" | Sonuçlarla geldikçe yanıt ver, id ile keyed |

## İleri Okuma

- [OpenAI — Parallel function calling](https://platform.openai.com/docs/guides/function-calling#parallel-function-calling) — varsayılan davranış ve opt-out bayrağı
- [Anthropic — Tool use: implementing tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implementing-tool-use) — `disable_parallel_tool_use` ve sonuç batching
- [Google — Gemini function calling parallel section](https://ai.google.dev/gemini-api/docs/function-calling) — Gemini 3'ten id-korele paralel çağrılar
- [OpenAI — Streaming responses with tools](https://platform.openai.com/docs/api-reference/responses-streaming) — OpenAI stream'leri için chunk'lı argüman reassembly
- [Anthropic — Streaming messages](https://docs.anthropic.com/en/api/messages-streaming) — `input_json_delta` ile `content_block_delta`
