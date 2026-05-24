---
name: skill-structured-outputs
description: Sağlayıcı, güvenilirlik ve karmaşıklığa göre doğru structured output stratejisini seçmek için karar çerçevesi
version: 1.0.0
phase: 11
lesson: 03
tags: [structured-output, json, schema, constrained-decoding, pydantic, function-calling]
---

# Structured Output Stratejisi

Yapılandırılmış veri gerektiren bir LLM uygulaması kurarken, bu karar çerçevesini uygula.

## Her yaklaşımı ne zaman kullan

**Prompt-bazlı ("JSON döndür"):** Sadece prototipleme. Zaman zaman parse hatalarının tolere edilebildiği iç araçlar için kabul edilebilir. try/except ve retry ekle. Asla production pipeline'larda kullanma.

**JSON mode (API flag):** Geçerli JSON garantili istiyorsun ama şema basit veya esnek. Şekli uygulama tarafında doğruladığında çalışır. Mevcut: OpenAI, Anthropic (tool use ile), Google.

**Schema mode (constrained decoding):** Her çıktının belirli bir şemaya uyması gereken production sistemleri. Sıfır parse hatası. Sıfır şema ihlali. Production çıkarım veya sınıflandırma görevleri için varsayılan olarak bunu kullan. Mevcut: OpenAI structured outputs, Outlines, Guidance.

**Function calling / tool use:** Modelin hangi fonksiyonu çağıracağını seçmesi gerekiyor, sadece parametreleri doldurması değil. Birden fazla şeman var ve model uygun olanı seçiyor. Ayrıca mevcut tool/function altyapısıyla entegrasyon için de kullan.

**Instructor kütüphanesi:** Herhangi bir sağlayıcı arasında Pydantic validation ve otomatik retry istiyorsun. Python projeleri için en iyi DX. OpenAI, Anthropic, Google ve açık kaynak modelleri sarar.

## Sağlayıcıya özgü rehberlik

**OpenAI:** `response_format`'ı `json_schema` tipi ile kullan. Constrained decoding dahili. Pydantic modelleri doğrudan çalışır. En güvenilir structured output implementasyonu.

**Anthropic:** Structured output için tool use kullan. İstenen şemayla tek bir tool tanımla. Model şemaya uyan tool çağrı argümanları döndürür. Güvenilir ama tool use API pattern'ini gerektirir.

**Açık kaynak modeller (vLLM, Ollama):** Constrained decoding için Outlines veya Guidance kullan. Bu kütüphaneler JSON Schema'ları üretim sırasında geçersiz token'ları maskeleyen finite state machine'lere derler. Yerel çıkarım gerektirir.

## Şema tasarım kılavuzu

1. Mümkün olduğunda şemaları düz tut. 2 seviyenin ötesindeki iç içe nesneler çıkarım hatalarını artırır.
2. Kategorik alanlar için enum kullan. Modelin doğru string'i icat etmesine güvenme.
3. Muğlak alanları opsiyonel yerine açık null desteğiyle required yap. Modeli karar vermeye zorlar.
4. Şema property'lerine description ekle. Model bunları talimat olarak okur.
5. Gerekmedikçe union tiplerinden (oneOf/anyOf) kaçın. Decoding karmaşıklığını artırırlar.
6. Sayılarda minimum/maximum ayarla. Halüsinasyonlu uç değerleri yakalar.
7. Dizilerde minItems/maxItems kullan, boş veya sınırsız çıktıları önle.

## Sık karşılaşılan başarısızlık pattern'leri ve çözümleri

- **Model JSON'u markdown çitlerine sarıyor**: prompt-bazlıdan JSON mode veya schema mode'a geç
- **Şema-geçerli ama gerçek-yanlış**: çıkarımdan sonra bir LLM-as-judge doğrulama adımı ekle
- **Tutarsız enum değerleri**: constrained decoding'e geç veya post-processing normalizasyonu ekle
- **Eksik opsiyonel alanlar**: onları required yap veya uygulama kodunda varsayılan değerler ekle
- **Çok yavaş çıkarım**: constrained decoding %5-15 gecikme ekler, gecikme hassasiysen şema karmaşıklığını azalt
- **Çeşitli öğelerle büyük diziler**: girdiyi chunk'la ve chunk başına çıkar, sonra sonuçları birleştir

## Güvenilirlik merdiveni

| Yaklaşım | Parse Başarısı | Şema Eşleşmesi | Kurulum Eforu |
|----------|-------------|-------------|-------------|
| Prompt-bazlı | ~%90 | ~%80 | 1 dakika |
| JSON mode | %100 | ~%90 | 5 dakika |
| Schema mode | %100 | ~%99 | 15 dakika |
| Constrained decoding | %100 | %100 | 30 dakika |
| Instructor + retry | %100 | ~%99.5 | 10 dakika |
