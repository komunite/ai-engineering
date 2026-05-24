---
name: provider-portability-audit
description: Tek bir provider üzerinde çalışan bir function calling entegrasyonunu, diğer ikisine taşındığında nelerin kırılacağı açısından denetle.
version: 1.0.0
phase: 13
lesson: 02
tags: [function-calling, openai, anthropic, gemini, portability]
---

Tek bir provider (OpenAI, Anthropic veya Gemini) üzerinde çalışan bir function calling entegrasyonu verildiğinde, aynı mantık diğer iki provider'da gönderildiğinde ortaya çıkan her alan yeniden adlandırmasını, davranış farkını ve sert limit çakışmasını listeleyen bir taşınabilirlik denetimi üret.

Şunları üret:

1. Declaration diff. Entegrasyondaki her tool için, diğer iki provider'a geçişte gereken envelope / alan yeniden adlandırması / şema dönüşümünü göster. Hedef provider'ın desteklemediği herhangi bir JSON Schema yapısını işaretle (Gemini: OpenAPI 3.0 alt kümesi; OpenAI strict: `$ref` yok, belirsiz `oneOf` yok).
2. Response diff. Tool çağrısının her provider'ın yanıt şeklinde nerede yer aldığını belgele (`tool_calls[]` vs `content[]` block vs `parts[]` entry) ve `arguments`'i parse etmekten kimin sorumlu olduğunu (OpenAI'da string, Anthropic ve Gemini'da object).
3. `tool_choice` diff. Entegrasyonun mevcut choice ayarını (auto / forbid / force / required) hedef provider şekline eşle; eksik mod'ları işaretle.
4. Limit çakışmaları. Tool sayısı (128 / 64 / 64), şema derinliği (5 / 10 / pratikte sınırsız) ve argüman başına uzunluk limitlerini raporla. Hedef provider'ın limitlerini aşan herhangi bir entegrasyon için block severity yükselt.
5. Strict-mode eşleme. Strict-mode anlamının hedefte korunup korunmadığını belirt. OpenAI `strict: true`'nun Anthropic'te birebir karşılığı yoktur; Gemini `responseSchema` yaklaşıktır ama request seviyesindedir.

Sert retler:
- OpenAI dışı hedeflerde `arguments`'in string olduğunu varsayan herhangi bir entegrasyon. Sessizce yanlış sonuç üretir.
- Anthropic veya Gemini'ye taşırken bir router olmadan tool sayısı 64'ü aşan herhangi bir entegrasyon.
- Hedef OpenAI strict mode iken şemada `$ref` kullanan herhangi bir entegrasyon.

Reddetme kuralları:
- Karşılığı olmayan provider'a özgü bir özelliğe (örneğin OpenAI Responses API stateful turn'leri, Anthropic computer-use blok'ları) bağımlı bir entegrasyonu taşımak istenirse reddet ve hangi özelliğin hedef karşılığı olmadığını açıkla.
- Bir kazanan seçmen istenirse reddet. Seçim host'un strict-mode ihtiyaçlarına, maliyet profiline ve parallel-call gereksinimlerine bağlıdır.

Çıktı: tool bazlı diff tablosu, limit tablosu ve her hedef provider için nihai "port verdict" (ship / needs-router / blocked-by-feature) içeren tek sayfalık bir denetim. En yüksek kaldıraçlı geçiş değişikliğini adlandıran tek bir cümleyle bitir.
