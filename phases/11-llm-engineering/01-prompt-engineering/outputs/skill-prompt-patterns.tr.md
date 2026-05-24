---
name: skill-prompt-patterns
description: Görev tipi, güvenilirlik gereksinimleri ve hedef modele göre doğru prompt pattern'ini seçmek için karar çerçevesi
version: 1.0.0
phase: 11
lesson: 01
tags: [prompt-engineering, patterns, llm, temperature, cross-model, few-shot, chain-of-thought]
---

# Prompt Pattern Seçim Kılavuzu

LLM destekli bir özellik kurarken, prompt'u yazmadan önce pattern'i seç. Pattern yapıyı belirler. İçerik onu doldurur.

## Pattern Karar Matrisi

| Görev Tipi | Birincil Pattern | İkincil Pattern | Temperature | Few-Shot Gerekli mi? |
|-----------|----------------|-------------------|-------------|-----------------|
| Veri çıkarımı | Template Fill | Few-Shot | 0.0 | Evet (2-3 örnek) |
| Sınıflandırma | Few-Shot | Guardrail | 0.0 | Evet (3-5 örnek) |
| Özetleme | Persona + Template | Audience Adapt | 0.3 | Hayır |
| Kod üretimi | Persona | Chain-of-Thought | 0.0 | Opsiyonel |
| Yaratıcı yazım | Persona | Critique | 0.7-1.0 | Hayır |
| Çok adımlı muhakeme | Chain-of-Thought | Decomposition | 0.3 | Opsiyonel |
| Soru yanıtlama | Persona + Guardrail | Boundary | 0.3 | Hayır |
| Prompt üretimi | Meta-Prompt | Critique | 0.7 | Evet (1-2 örnek) |
| İçerik moderasyonu | Guardrail + Boundary | Few-Shot | 0.0 | Evet (5+ örnek) |
| Çeviri/uyarlama | Audience Adapt | Few-Shot | 0.3 | Evet (2-3 örnek) |

## Her Pattern Ne Zaman Kullanılır

**Persona Pattern**: her prompt için baseline olarak kullan. Tek soru rolü ne kadar spesifik yapacağın. Genel görevler için geniş bir rol yeterli. Domain'e özgü görevler için rol domain'i, kıdem seviyesini ve bağlamı isimlendirmeli.

**Few-Shot Pattern**: çıktı formatı içerikten daha önemliyse kullan. Model spesifik bir JSON şekli, CSV formatı veya sınıflandırma etiketi üretmesi gerekiyorsa, örnekler talimatlardan daha etkilidir. Kural: basit formatlar için 2-3 örnek, karmaşık veya muğlak formatlar için 5+.

**Chain-of-Thought Pattern**: matematik, mantık, çok adımlı analiz ve modelin "çalışmasını göstermesi" gereken her görev için kullan. Muhakeme görevlerinde doğruluğu %10-40 artırır (Wei vd., 2022). Basit factual aramalar veya çıkarım için KULLANMA — token israfıdır.

**Template Fill Pattern**: her çıktının aynı şekle sahip olması gereken yapılandırılmış çıkarım için kullan. temperature=0.0 ve eksik alanlar için açık "N/A" işlemiyle en iyi çalışır.

**Critique Pattern**: hız değil kalite önemliyse kullan. Model üretir, eleştirir ve iyileştirir. Yaklaşık iki kat token maliyetine mal olur ama doğruluğu ve eksiksizliği önemli ölçüde artırır. Yüksek riskli çıktılar için en iyisi (raporlar, öneriler, halka açık içerikler).

**Guardrail Pattern**: kullanıcıya bakan her sistem için kullan. Her zaman dahil et: kapsam sınırları, kapsam dışı isteklere reddetme davranışı ve açık "Bilmiyorum" işleme. Uygulama tarafındaki input validation ile birleştir.

**Meta-Prompt Pattern**: yeni görevler için prompt üretmek için kullan. Sıfırdan prompt yazmak yerine, görevi tarif et ve modele prompt'u yazdır. Sonra test et ve iterate et. İlk prompt geliştirmede zaman kazandırır.

**Decomposition Pattern**: böl-yönet'ten faydalanan karmaşık problemler için kullan. Model problemi parçalara böler, her birini çözer ve birleştirir. 3-7 alt problemli görevlerde en etkili.

**Audience Adaptation Pattern**: aynı içeriğin farklı kitlelere hizmet etmesi gerektiğinde kullan. Kitleyi açıkça belirt — modelin bağlamdan tahmin etmesine güvenme.

**Boundary Pattern**: belirli soru tiplerine ASLA cevap vermemesi gereken production sistemleri için kullan. Guardrail'lerden daha güçlü çünkü kesin bir reddetme mesajı ile sert bir kapsam tanımlar. Compliance hassasiyeti olan domain'ler için şart.

## Cross-Model Uyumluluğu

GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro ve Llama 3 arasında ne kadar tutarlı çalıştıklarına göre pattern'ler:

| Pattern | Cross-Model Tutarlılığı | Notlar |
|---------|------------------------|-------|
| Few-Shot | Çok yüksek | Örnekler tüm modellerde iyi transfer olur |
| Template Fill | Çok yüksek | Açık yapı sapma için az alan bırakır |
| Chain-of-Thought | Yüksek | Tüm büyük modeller "adım adım düşün"ü destekler |
| Persona | Yüksek | Her yerde çalışır ama farklı modeller farklı rol spesifikliklerine yanıt verir |
| Guardrail | Orta | Claude guardrail'leri en sıkı takip eder; GPT-4o uzun konuşmalarda bazen sapar |
| Critique | Orta | Self-critique kalitesi modele göre önemli ölçüde değişir |
| Meta-Prompt | Orta | GPT-4o ve Claude farklı prompt stilleri üretir |
| Boundary | Düşük-Orta | Reddetme davranışı değişir; model başına test et |

## Sık Yapılan Hatalar

1. **Her şey için Chain-of-Thought kullanmak**: CoT token ve gecikme ekler. Sadece muhakeme adımları gerektiğinde kullan.
2. **Çok fazla kısıt**: 5-7'den fazla kısıt olursa model bazılarını düşürmeye başlar. En önemli 3'üne öncelik ver.
3. **Çelişkili persona + kısıtlar**: "Sen yaratıcı bir yazarsın" + "Asla metafor kullanma" modeli karıştırır.
4. **Temperature belirtmemek**: Deterministik çıktı gerektiğinde temperature'ı varsayılan (genelde 1.0) bırakmak.
5. **Prompt'ları modeller arasında kopyala-yapıştır**: her zaman test et. GPT-4o için ayarlanmış bir prompt Claude'da kötü performans gösterebilir, tersi de.
6. **System mesajını ihmal etmek**: Kalıcı kurallar için system mesajını kullanmak yerine her şeyi user mesajına koymak.
7. **Negatif kısıtlara aşırı bağımlılık**: "X, Y, Z, A, B, C YAPMA" demek "SADECE W yap" demekten daha az etkilidir. Pozitif çerçeveleme modele net bir hedef verir.

## Güvenilirlik Hedefleri

| Kullanım Senaryosu | Pattern Kombinasyonu | Beklenen Doğruluk | Token Maliyeti |
|----------|-------------------|-------------------|------------|
| Production çıkarımı | Template + Few-Shot | %95+ | Düşük (500-1K) |
| Kullanıcıya bakan Q&A | Persona + Guardrail + Boundary | %90+ | Orta (1-2K) |
| Kod üretimi | Persona + Chain-of-Thought | %85+ | Orta (1-3K) |
| İçerik üretimi | Persona + Critique | %90+ kalite | Yüksek (2-4K, çift pass) |
| Sınıflandırma | Few-Shot + Guardrail | %95+ | Düşük (300-800) |
| Karmaşık analiz | Decomposition + Chain-of-Thought | %85+ | Yüksek (3-5K) |
