---
name: skill-cot-patterns
description: Görev karmaşıklığı, doğruluk gereksinimleri ve maliyet kısıtlarına göre doğru muhakeme tekniğini seçmek için karar çerçevesi
version: 1.0.0
phase: 11
lesson: 02
tags: [chain-of-thought, few-shot, self-consistency, tree-of-thought, react, reasoning, prompting]
---

# Muhakeme Tekniği Seçim Kılavuzu

Bir LLM'in problem üzerinde muhakeme etmesini istediğinde, prompt'u yazmadan önce tekniği seç. Teknik muhakeme mimarisini belirler. Prompt onu doldurur.

## Hızlı Karar Ağacı

1. Görev basit factual arama veya tek adımlı sınıflandırma mı?
   - Evet: **zero-shot** kullan. CoT doğruluk kazancı olmadan maliyet ekler.
   - Hayır: devam et.

2. Görev çok adımlı muhakeme gerektiriyor mu (matematik, mantık, planlama)?
   - Evet: **Chain-of-Thought** kullan. Adım 3'e devam et.
   - Hayır: format önemliyse **few-shot**, değilse zero-shot kullan.

3. Tek bir muhakeme hatası kabul edilebilir mi?
   - Evet: **few-shot CoT** kullan (tek örnek, temperature 0.0).
   - Hayır: **self-consistency** kullan (N=5, temperature 0.7). Adım 4'e devam et.

4. Problem birçok olası yola sahip bir arama/planlama problemi mi?
   - Evet: **Tree-of-Thought** kullan.
   - Hayır: self-consistency yeterli.

5. Görev dış bilgi veya hesaplama gerektiriyor mu?
   - Evet: **ReAct** kullan (muhakeme + tool çağrıları).
   - Hayır: saf muhakeme teknikleri yeterli.

## Teknik Matrisi

| Teknik | Doğruluk Artışı | Maliyet Çarpanı | Gecikme | En İyi |
|-----------|--------------|-----------------|---------|----------|
| Zero-shot | Baseline | 1x | ~1s | Basit görevler, factual Q&A |
| Few-shot | +%5-15 | 1.2x | ~1s | Format eşleştirme, sınıflandırma |
| Zero-shot CoT | +%10-20 | 1.3x | ~1.5s | Hızlı muhakeme artışı |
| Few-shot CoT | +%15-25 | 1.5x | ~2s | Matematik, mantık, çok adım |
| Self-Consistency (N=5) | CoT üzerine +%2-5 | 5x | ~5s | Yüksek riskli muhakeme |
| Self-Consistency (N=10) | N=5 üzerine +%1-2 | 10x | ~10s | Sadece kritik kararlar |
| Tree-of-Thought | Göreve bağlı | 10-40x | ~30s+ | Arama, planlama, bulmaca |
| ReAct | Göreve bağlı | 3-10x | ~5-15s | Bilgiye dayalı görevler |
| Prompt Chaining | Tek üzerine +%5-10 | 2-5x | ~5-10s | Karmaşık çok parçalı görevler |

## Modele Özgü Rehberlik

### GPT-4o / GPT-4.1
- Güçlü baseline muhakeme. Zero-shot CoT genelde yeterli.
- 3 örnekli few-shot CoT GSM8K'da %95'e ulaşır.
- Self-consistency marjinal kazanç verir (%95'ten %97'ye) — sadece kritik görevler için değer.
- Cevap çıkarımı için structured outputs'u native destekler.

### Claude 3.5 Sonnet / Claude 3.7 Sonnet
- Yapılandırılmış prompt formatlarını (XML tag'leri) takip etmede mükemmel.
- XML-delimited örneklerle few-shot CoT en iyi çalışır.
- Extended thinking (Claude 3.7) native CoT'tir — prompt'lamaya gerek yok.
- Claude'un muhakemesi temperature 0.7'de iyi varyans gösterdiği için self-consistency etkilidir.

### Llama 3.1/3.3 70B
- En çok few-shot CoT'tan fayda görür (zero-shot'a göre daha büyük doğruluk farkı).
- Muhakeme görevleri için N=5 ile self-consistency önerilir.
- Ticari modellerden daha açık format talimatlarına ihtiyaç duyar.
- Yerel çıkarımda ToT pahalıdır — sadece batch işleme için düşün.

### Gemini 2.5 Pro
- Kutu dışı çok adımlı muhakemede güçlü.
- Thinking mode prompt engineering olmadan dahili CoT sağlar.
- Few-shot örnekleri doğruluktan çok format tutarlılığına yardımcı olur.
- Büyük context window (1M) örnek-yoğun few-shot'u pratik kılar.

## Anti-Pattern'ler

**Basit görevler için CoT**: "2+2 nedir? Adım adım düşünelim" demek token israfıdır. Model basit aritmetiği muhakeme izi olmadan doğru yapar. CoT 3+ adım olduğunda yardımcı olur.

**Temperature 0.0'da self-consistency**: tüm N örnek aynı olur. Çeşitli muhakeme yolları için temperature > 0 (0.5-0.8 önerilir) kullanmalısın.

**Her şey için ToT**: ToT O(b^d) LLM çağrısı gerektirir; b=branching factor, d=derinlik. b=3, d=3 olan bir ağaç 39 çağrıya kadar ihtiyaç duyar. Daha ucuz tekniklerin başarısız olduğu problemlere sakla.

**Kötü örneklerle few-shot**: muhakeme hatası içeren örnekler modele o hataları yapmayı öğretir. Her örnek doğrulanmalıdır. Yanlış bir örnek sıfır örnekten daha fazla doğruluk düşürür.

**Tutarlı format olmadan cevap çıkarmak**: self-consistency örnekler arasında cevap karşılaştırmayı gerektirir. Cevap formatı değişirse ("18$", "18 dolar", "on sekiz"), oylama başarısız olur. Her zaman zorla: "Cevap [sayı]."

## Maliyet Optimizasyonu

GPT-4o fiyatlandırmasında ($2.50/1M input, $10/1M output) günlük 10.000 sorgu işleyen bir production sistemi için:

| Teknik | Sorgu Başına Ort. Token | Günlük Maliyet | Doğruluk |
|-----------|-----------------|------------|----------|
| Zero-shot | ~200 | ~$5 | %78 |
| Few-shot CoT | ~600 | ~$15 | %95 |
| Self-Consistency (N=5) | ~3.000 | ~$75 | %97 |
| ToT (b=3, d=2) | ~6.000 | ~$150 | Göreve bağlı |

Çoğu uygulama için maliyet-optimal strateji: few-shot CoT ile başla. Self-consistency'i sadece güvenin düşük olduğu sorgulara ekle (Build It bölümündeki escalation pattern'i).

## Prompt Chaining ile Entegrasyon

Muhakeme teknikleri prompt chaining ile birleşir:

**Zincir Adım 1** (Çıkar): zero-shot, temperature 0.0
**Zincir Adım 2** (Muhakeme): few-shot CoT, temperature 0.0
**Zincir Adım 3** (Doğrula): N=3 ile self-consistency, temperature 0.7

Bu üç adımlı zincir tek bir CoT çağrısına göre yaklaşık 3 kat maliyet ekler ama çıkarım hatalarını, muhakeme hatalarını yakalar ve doğrulama adımından bir güven skoru sağlar.

## Prompt'lamadan Ne Zaman İleri Gidilir

Uygulama kodu yazmaktan daha çok prompt mühendisliği yapıyorsan, şunları düşün:

1. **Fine-tuning**: 500+ etiketli örneğin varsa ve görev darsa
2. **DSPy compilation**: otomatik prompt optimizasyonu istiyorsan
3. **Agent framework'leri**: görev çok turlu tool kullanımı gerektiriyorsa (Faz 14)
4. **RAG**: model gizli/güncel bilgiye erişmeli (Ders 06-07)

Prompt'lama teknikleri temeldir. Her modelle, her sağlayıcıyla çalışır ve eğitim verisi gerektirmez. Ama sınırları vardır. Bir sonraki seviyeye ne zaman geçileceğini bilmek tekniklere hakim olmak kadar önemlidir.
