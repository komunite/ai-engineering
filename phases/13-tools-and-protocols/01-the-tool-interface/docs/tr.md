# Tool Interface — Agent'ların Neden Yapılandırılmış I/O'ya İhtiyacı Var

> Bir dil modeli token üretir. Bir program aksiyon alır. İkisinin arasındaki boşluk tool interface'idir: modelin bir aksiyon talep etmesine ve host'un bunu yürütmesine izin veren bir sözleşme. 2026'daki her yığın — OpenAI, Anthropic ve Gemini'deki function calling; MCP'nin `tools/call`'ı; A2A'nın task part'ları — aynı dört adımlı döngünün farklı bir kodlamasıdır. Bu ders o döngüye isim verir ve onu çalıştırmak için gereken minimum mekanizmayı gösterir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, LLM yok)
**Ön koşullar:** Faz 11 (LLM completion API'leri)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Yalnızca text üretebilen bir LLM'in tek başına neden gerçek dünyaya karşı aksiyon alamadığını açıkla.
- Dört adımlı tool-call döngüsünü çiz (describe → decide → execute → observe) ve her adımın sahibini söyle.
- Bir tool tanımını üç parça halinde yaz: isim, JSON Schema input ve deterministik bir executor fonksiyonu.
- Pure ve side-effect üreten tool'ları ayırt et ve bu ayrımın güvenlik için neden önemli olduğunu söyle.

## Sorun

Bir LLM, bir sonraki token üzerinde bir olasılık dağılımı yayar. Tüm çıktı yüzeyi budur. Bir chat modeline "şu anda Bengaluru'da hava nasıl" diye sorarsan, mantıklı bir cümle yazabilir ama bir hava durumu API'sini arayamaz. Cümle tesadüfen doğru ya da üç gün eski olabilir.

O boşluğu kapatmak tool interface'inin amacıdır. Host program — agent runtime'ın, Claude Desktop, ChatGPT, Cursor ya da custom bir script — modele çağrılabilir tool'ların listesini duyurur. Model, bir aksiyona ihtiyaç olduğuna karar verdiğinde, bir tool'u ve argümanlarını adlandıran yapılandırılmış bir payload yayar. Host bu payload'u parse eder, tool'u gerçekten çalıştırır ve sonucu geri besler. Model artık çağrı gerekmediğine karar verene kadar döngü devam eder.

Bu sözleşmenin ilk versiyonu Haziran 2023'te OpenAI'ın "functions" parametresi olarak yayınlandı. Anthropic, Claude 2.1'de `tool_use` blokları ile takip etti. Gemini birkaç ay sonra `functionDeclarations` ekledi. Her sağlayıcı artık aynı şekli sunuyor: girişte JSON-Schema tipli bir tool listesi, çıkışta JSON-payload tool call'u. Model Context Protocol (Kasım 2024) sözleşmeyi genelleştirdi, böylece tek bir tool registry'si her modele hizmet ediyor. A2A (Nisan 2026, v1.0) aynı primitive'i agent'tan-agent'a delegasyon için katmanladı.

Dört adımlı döngü, tüm bunların altındaki değişmezdir. Faz 13'teki diğer her şey bunun bir elaborasyonudur.

## Kavram

### Adım bir: describe

Host her tool'u üç alanla bildirir.

- **Name.** Stabil, makine okunabilir bir tanımlayıcı. `get_weather`, "hava şeysi" değil.
- **Description.** Bir paragraflık doğal-dil özet. "Kullanıcı belirli bir şehir için mevcut koşulları sorduğunda kullan. Geçmiş veriler için kullanma."
- **Input schema.** Tool'un argümanlarını tanımlayan bir JSON Schema objesi (draft 2020-12).

Model listeyi alır. Modern sağlayıcılar bu bildirimleri sağlayıcıya özgü bir template kullanarak system prompt'a serialize ederler, böylece arayan olarak sen yalnızca yapılandırılmış form ile uğraşırsın.

### Adım iki: decide

Kullanıcının mesajı ve mevcut tool'lar verildiğinde, model üç davranıştan birini seçer.

1. **Doğrudan cevap ver**, text olarak. Tool çağrısı yok.
2. **Bir ya da daha fazla tool çağır.** Yapılandırılmış call objeleri yay. `parallel_tool_calls: true` (OpenAI ve Gemini'de varsayılan, Anthropic'te opt-in) altında model tek turda birden fazla çağrı yayabilir.
3. **Reddet.** Strict-mode structured output'lar bir çağrı yerine tipli bir `refusal` bloğu üretebilir.

Bir tool call payload'u üç stabil alana sahiptir: bir call `id`'si, bir tool `name`'i ve bir JSON `arguments` objesi. Id, host'un sonraki sonucu belirli çağrıyla korele edebilmesi için vardır — bu özellikle paralel çağrılar sıra dışı döndüğünde önemlidir.

### Adım üç: execute

Host çağrıyı alır, argümanları bildirilen şemaya karşı doğrular ve executor'u çalıştırır. Geçersiz argümanlar, modelin bir alan halüsinasyonu yaptığı ya da yanlış tip kullandığı anlamına gelir — zayıf modellerde çok yaygın bir başarısızlık modu. Üretim host'ları geçersiz argümanlarda üç şeyden birini yapar: hızlıca başarısız olup hatayı modele yüzeyleştirir, JSON'u kısıtlı bir parser ile onarır ya da validation hatasını prompt'a dahil ederek modeli yeniden çağırır.

Executor'un kendisi sıradan koddur. Python, TypeScript, bir shell komutu, bir database sorgusu. Genellikle string olan ama herhangi bir JSON değeri ya da yapılandırılmış bir content bloğu (MCP'de text, image ya da resource referansı) olabilen bir sonuç üretir. Sonuç serializable olmalıdır.

### Adım dört: observe

Host tool sonucunu konuşmaya ekler (eşleşen `id` ile `tool` rolü mesajı olarak) ve modeli yeniden çağırır. Model artık bağlamda tool çıktısına sahiptir ve nihai bir cevap üretebilir ya da daha fazla çağrı talep edebilir. Bu, model çağrı yaymayı bırakana ya da host iterasyon sayısı üzerindeki bir güvenlik sınırına ulaşana kadar devam eder.

### Trust split

Tool'lar güvenlik için önemli olan iki çeşitte gelir.

- **Pure.** Read-only, deterministik, side effect yok. `get_weather`, `search_docs`, `get_current_time`. Spekülatif olarak çağrılabilecek kadar güvenli.
- **Consequential.** State'i değiştirir, para harcar, kullanıcı verisine dokunur. `send_email`, `delete_file`, `execute_trade`. Gate'lenmek zorundadır.

Meta'nın 2026 agent güvenliği için "Rule of Two" kuralı, tek bir turun şunlardan en fazla ikisini birleştirebileceğini söyler: untrusted input, sensitive data, consequential action. Tool interface, bu kuralı uyguladığın yerdir — çağrıları reddederek, kullanıcı onayı isteyerek ya da scope'ları yükselterek. Tam güvenlik bölümü için Faz 13 · 15'e ve agent-seviyesi izin politikaları için Faz 14 · 09'a bak.

### Döngü nerede yaşar

| Bağlam | Kim describe eder | Kim decide eder | Kim execute eder |
|---------|---------------|-------------|--------------|
| Tek-turda function calling (OpenAI/Anthropic/Gemini) | Uygulama geliştiricisi | LLM | Uygulama geliştiricisi |
| MCP | MCP sunucusu | MCP client üzerinden LLM | MCP sunucusu |
| A2A | Agent Card yayıncısı | Çağıran agent | Çağrılan agent |
| Web tarayıcısı (function-calling agent) | Tarayıcı eklentisi / WebMCP | LLM | Tarayıcı runtime'ı |

Her yerde aynı dört adım. Sütun adları değişir; yapı değişmez.

### Neden modelden JSON yaymasını prompt'lamıyoruz?

"Modelden JSON ile yanıt vermesini iste" function calling öncesi dönemin desenidir. Frontier modellerde ~%5 ila %15 zaman başarısız olur, küçük modellerde çok daha fazla. Başarısızlık modları şunları içerir: eksik küme parantezleri, sondaki virgüller, halüsinasyonlu alanlar ve yanlış tipler. Sonra bir JSON repair pass'ine, bir retry'a ya da kısıtlı bir decoder'a ihtiyacın olur.

Native function calling üç nedenden daha iyidir. Birincisi, sağlayıcı modeli end-to-end olarak tam call şekli üzerinde eğitir, böylece geçerli-JSON oranı strict modda %98 ila %99'a çıkar. İkincisi, call payload'u serbest-text içinde değil, kendi protokol slot'unda oturur — yani bir tool call asla kullanıcıya görünen yanıta sızmaz. Üçüncüsü, sağlayıcılar şema uyumunu kısıtlı decoding ile zorlar (OpenAI'ın strict mode'u, Anthropic'in `tool_use`'u, Gemini'nin `responseSchema`'sı). Çıktının doğrulanması garantilenir.

Faz 13 · 02 üç sağlayıcı API'sini yan yana gezer. Faz 13 · 04 structured output'larda derinleşir.

### Circuit breaker'lar

Döngü, model çağrı yaymayı bıraktığında ya da host maksimum tur sayısına ulaştığında sonlanır. Üretim host'ları bunu 5 ile 20 tur arası ayarlar. Onun ötesinde, neredeyse kesinlikle modelin çıkamayacağı bir döngüdesin. Claude Code varsayılan olarak 20; OpenAI Assistants 10; Cursor'un agent mode'u 25.

Alternatif — sınırsız döngüler — her altı ayda bir "agent bir gecede 400 dolarlık API çağrısı harcadı" post-mortem'leri olarak ortaya çıkar. Bir sınır olmadan yayınlama.

Faz 14 · 12 error recovery ve self-healing'i derinlemesine ele alır; Faz 17 üretim rate limit'lerini ele alır.

### Faz 13 buradan nereye gidiyor

- 02 ile 05 arası dersler sağlayıcı-seviyesi tool-call yüzeyini cilalar.
- 06 ile 14 arası dersler döngüyü MCP'ye genelleştirir.
- 15 ile 18 arası dersler döngüyü düşman sunuculara, adversarial kullanıcılara ve doğrulanmamış uzak auth yüzeylerine karşı savunur.
- 19 ile 22 arası dersler deseni agent'tan-agent'a işbirliği, observability, routing ve paketlemeye genişletir.
- 23. ders her primitive'i kullanarak tam bir ekosistem yayınlar.

Kalan her ders bu dört adımlı döngünün bir elaborasyonudur. Onu değişmez olarak akılda tut.

## Kullan

`code/main.py` dört adımlı döngüyü bir LLM olmadan çalıştırır. Sahte bir "decider" fonksiyonu kullanıcı mesajı üzerinde pattern matching yaparak modeli simüle eder; executor, schema validator ve observe-step harness'ı gerçektir. Yazdırılabilir ara state ile tam request/response koreografisini görmek için çalıştır, sonra sahte decider'ı daha sonraki bir derste gerçek bir sağlayıcı ile değiştir.

Bakılacak şeyler:

- Tool registry'si her tool için üç alan tutar: name, description, schema ve executor referansı.
- Validator yalnızca stdlib ile yazılmış minimal bir JSON Schema alt kümesidir (types, required, enum, min/max). Faz 13 · 04 daha tam birini yayınlar.
- Döngü iterasyon sayısını beşte sınırlar. Üretim agent'larının tam olarak bu tür bir circuit breaker'a ihtiyacı vardır.

## Yayınla

Bu ders `outputs/skill-tool-interface-reviewer.md` üretir. Bir taslak tool tanımı (name + description + schema + executor outline) verildiğinde, skill onu döngü uygunluğu için denetler: isim makine-stabil mi, açıklama eksiksiz bir kullanım brief'i mi, şema JSON Schema 2020-12'yi doğru kullanıyor mu ve pure-vs-consequential sınıflandırması açık mı.

## Alıştırmalar

1. `code/main.py`'a `get_stock_price(ticker)` adlı dördüncü bir tool ekle. Açıklamasını "Kullanıcı bir ticker ile mevcut bir hisse fiyatı sorduğunda kullan. Tarihsel fiyatlar ya da pazar özetleri için kullanma." olarak yaz. Harness'ı çalıştır ve sahte decider'ın ticker bahseden sorguları yeni tool'a yönlendirdiğini doğrula.

2. Schema validator'ı kır. `arguments` objesinde gerekli bir alanın eksik olduğu bir çağrı geç ve host'un onu yürütmeden önce reddettiğini doğrula. Sonra ekstra bilinmeyen bir alanı olan bir çağrı geç. Karar ver: host reddetmeli mi yoksa görmezden mi gelmeli? Seçimini bir güvenlik argümanı ile gerekçelendir.

3. Harness'taki her tool'u pure ya da consequential olarak sınıflandır. İhtiyaç duyan registry girdilerine `consequential: true` bayrağı ekle ve döngüyü, bir consequential tool seçildiğinde "kullanıcı ile onay alacaktı" satırı yazdıracak şekilde değiştir. Bu, her üretim host'unun ihtiyaç duyduğu onay gate'inin şeklidir.

4. Dört adımlı döngüyü kağıda çiz, yukarıdaki sağlayıcı-sütun tablosunu favori client'ın için doldur (Claude Desktop, Cursor, ChatGPT ya da custom bir yığın). Faz 13 · 06'daki MCP-spesifik varyantla çapraz referans ver.

5. OpenAI'ın function-calling rehberini baştan sona oku. Burada sunulan dört adımlı döngüde değil de request'te oturan bir alanı tanımla. Ne eklediğini ve neden esansiyel değil ama kullanışlı olduğunu açıkla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Tool | "Modelin çağırabildiği şey" | name + JSON-Schema tipli input + executor fonksiyonu üçlüsü |
| Function calling | "Native tool use" | Prose yerine yapılandırılmış tool call yaymak için sağlayıcı-seviyesi API desteği |
| Tool call | "Modelin aksiyon talebi" | Model tarafından yayılan `id`, `name`, `arguments` içeren JSON payload |
| Tool result | "Tool'un döndürdüğü şey" | Executor'un çıktısı, eşleşen id ile bir `tool` role mesajına sarılmış |
| Parallel tool calls | "Aynı anda birçok çağrı" | Tek model turunda, bağımsız ve id ile sıralanabilir birden fazla call objesi |
| Strict mode | "Garantili JSON" | Modelin çıktısını bildirilen şemaya doğrulamak için zorlayan kısıtlı decoding |
| Pure tool | "Read-only tool" | Side effect yok; yeniden çalıştırılabilecek kadar güvenli |
| Consequential tool | "Aksiyon tool'u" | Dış state'i değiştirir; gate, audit ya da kullanıcı onayı gerektirir |
| Four-step loop | "Tool-call döngüsü" | describe → decide → execute → observe |
| Host | "Agent runtime" | Tool registry'sini tutan, modeli çağıran ve executor'u çalıştıran program |

## İleri Okuma

- [OpenAI — Function calling guide](https://platform.openai.com/docs/guides/function-calling) — OpenAI-style tool tanımları ve call şekilleri için kanonik referans
- [Anthropic — Tool use overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) — Claude'un `tool_use` / `tool_result` block formatı
- [Google — Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling) — Gemini'de `functionDeclarations` ve parallel-call semantiği
- [Model Context Protocol — Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — tool interface'inin sağlayıcı-agnostik genellemesi
- [JSON Schema — 2020-12 release notes](https://json-schema.org/draft/2020-12/release-notes) — her modern tool API'sinin konuştuğu şema dialect'i
