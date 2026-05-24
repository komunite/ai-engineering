---
name: tool-registry
description: JSON Schema doğrulaması, paralel dispatch ve observability ile production tool kataloğu ve registry kur.
version: 1.0.0
phase: 14
lesson: 06
tags: [function-calling, tools, schema, validation, bfcl, parallel-tools]
---

Bir görev alanı verildiğinde, bir agent'in BFCL V4 eksenlerinde (agentic, multi-turn, live, non-live, hallucination) güvenilir şekilde kullanabileceği bir tool kataloğu üret.

Üret:

1. Tool tanımları. Her tool için: `name` (snake_case), `description` (modele ne zaman kullanacağını VE ne zaman KULLANMAYACAĞINI söyler), tipli özelliklerle JSON Schema input, required alanlar, uygulanabilir yerlerde enum'lar, numerik'ler için minimum/maximum, tool başına timeout, tool başına sandbox politikası (fs yüzeyi, network, bellek sınırı).
2. Açıklama kalite kontrolü. Her açıklamayı "bu, modele bu tool'u diğerlerinin yerine ne zaman seçmesi gerektiğini söylüyor mu?" testinden geçir. İki tool'un açıklamaları örtüşüyorsa, reddet ve yeniden yaz.
3. Paralel-dispatch planı. Her gerçekçi görev için, hangi tool çağrılarının bağımsız (paralelleştirilebilir) ve hangilerinin sıralı olması gerektiğini belirle. Beklenen bir dispatch grafiği yay.
4. Doğrulama politikası. Enum kontrolleri, type coercion kuralları (örn. "int-as-string kabul et, float-as-string reddet"), required-field zorlaması. Her başarısızlık yapılandırılmış bir observation string döndürür, asla döngüye yükseltmez.
5. Observability. Her tool, `gen_ai.tool.name`, `gen_ai.tool.call.id`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` (content policy gerektirdiğinde inline değil, referans olarak) niteliklerine sahip bir OpenTelemetry GenAI `tool_call` span'i yayar.

Sert ret durumları:

- Genel shell/command-exec tool'u. Reddet ve spesifik fiillere böl (`git_status`, `fs_read`, `npm_test`).
- Parametre kapalı bir değer kümesine sahipken eksik enum'lar. Enum doğrulaması drift'i yakalamanın en ucuz yoludur.
- İki farklı tool için aynı açıklama. Model aralarında güvenilir şekilde seçim yapamaz.
- Yalnızca tool'u isimlendiren `description` ("İki sayı toplar"). Alternatifler yerine NE ZAMAN seçeceğini dahil et.
- Timeout yok. Her tool çağrısının bir tavanı olmalı.

Reddetme kuralları:

- Tool listesi tek bir agent için 30 tool'u aşıyorsa, reddet ve subagent delegasyonu öner (Lesson 17).
- Herhangi bir tool onay kapısı olmadan destructive bir eylem yapıyorsa, reddet ve Lesson 09'a (izinler, sandboxing) yönlendir.
- Görev computer use (tıklama, yazma, screenshot) ise, reddet ve Lesson 21'e yönlendir — bu, vision tabanlı eylemli ayrı bir tool şeklidir.

Çıktı: Anthropic / OpenAI / Gemini SDK çağrılarına yapıştırmaya hazır bir JSON tool kataloğu, bir dispatch-graph diyagramı, bir doğrulama politikası belgesi ve registry'nin geçmesi gereken BFCL stili bir mini-eval.

"Bundan sonra ne okumalı" işaretleyicisi ile bitir: Lesson 09 (sandboxing), Lesson 23 (OTel GenAI span'leri) veya Lesson 30 (eval-driven).
