---
name: structured-output-designer
description: Serbest metin çıkarım hedefi için strict-mode uyumlu bir JSON Schema ve Pydantic modeli tasarla; tipli reddetme ve retry işlemeyi de iskeleye dahil et.
version: 1.0.0
phase: 13
lesson: 04
tags: [structured-output, json-schema, pydantic, strict-mode, extraction]
---

Bir serbest metin çıkarım hedefi (faturalar, özgeçmişler, destek talepleri, araştırma özetleri) verildiğinde, production'a hazır bir çıkarım kontratı üret: JSON Schema 2020-12, Pydantic modeli, reddetme handler'ı ve retry policy.

Şunları üret:

1. JSON Schema 2020-12. Her property tipli. `required` her property'yi listeler. Her object'te `additionalProperties: false`. Kapalı değer kümeleri için enum kullanılır. `$ref` yok. Belirsiz `oneOf` / `anyOf` yok. OpenAI strict-mode gereksinimlerine karşı doğrulanır.
2. Pydantic v2 BaseModel. Şemanın Python tipleriyle aynası. `model_json_schema()` (1)'e eşdeğer bir şema üretmelidir.
3. Reddetme handler'ı. Tipli `Refusal(reason: str, category: str)` sonucu. Kategorileri listele: `safety`, `input_mismatch`, `insufficient_info`.
4. Retry policy. Üç retry şekli: (a) doğrulama hatalarını enjekte et ve bir kez retry et (strict mode dışında); (b) reddetmeyi nihai olarak kabul et (strict mode); (c) tekrarlanan reddetmede daha güçlü bir modele yükselt.
5. Test vektörleri. Mutlu yol, hasmane alanlar, kısmi girdi ve reddetme tetikleyici bir vakayı kapsayan on girdi. Her biri beklenen sonuçla birlikte.

Sert retler:
- Tipsiz alanlara sahip herhangi bir şema. Hem strict mode'da hem validator'da başarısız olur.
- `additionalProperties: false` eksik herhangi bir şema. Halüsinasyon sızdırır.
- Bir discriminator alanı olmadan `oneOf` kullanan herhangi bir şema. Belirsiz decoding.
- JSON Schema round-trip'i kontrol edilmemiş herhangi bir Pydantic modeli.

Reddetme kuralları:
- Hedef domain belgelenmiş bir amaç olmadan kişisel kimlik tanımlayıcı veri içeriyorsa reddet ve hukuki temel argümanı için Phase 18'e (etik) yönlendir.
- Kullanıcı JSON Schema 2020-12'de ifade edilemeyen bir şema isterse (örneğin özyinelemeli keyfi grafikler) reddet ve ifade edilebilir en yakın gevşemeyi öner.
- Çıkarım hedefi "herhangi bir şeyden yapılandırılmış veri çıkar" ise reddet ve spesifik domain'i iste.

Çıktı: şema JSON'u, Pydantic class'ı, reddetme ve retry policy ve on test vektörünü içeren tek sayfalık bir kontrat. Hedef alınacak ilk provider ve nedenini içeren bir notla bitir.
