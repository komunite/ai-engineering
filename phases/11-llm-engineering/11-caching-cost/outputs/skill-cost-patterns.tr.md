---
name: skill-cost-patterns
description: LLM maliyet optimizasyonu için karar çerçevesi -- caching stratejileri, rate limiting, model routing ve bütçe kontrolleri
version: 1.0.0
phase: 11
lesson: 11
tags: [caching, cost-optimization, rate-limiting, model-routing, budget, llm-ops]
---

# LLM Maliyet Optimizasyon Pattern'leri

Maliyetleri kontrol etmesi gereken bir LLM uygulaması kurarken, bu karar çerçevesini uygula.

## Ne zaman optimize et

**Hemen optimize et:**
- Aylık LLM harcaması $500'ü veya altyapı bütçesinin %10'unu aşıyorsa
- Tüketici ürünü için sorgu başına maliyet $0.01'in üstündeyse
- System prompt'un 1.000 token'ı aşıyor ve her istekle gönderiliyorsa
- Sorguların %30'undan fazlası duplikat veya yakın-duplikatsa
- 100'den 10.000+ günlük kullanıcıya ölçekleniyorsan

**Henüz optimize etme:**
- 100'den az DAU'n varsa ve hala product-market fit'i doğruluyorsan
- Aylık harcama $100'ün altında ve yavaş büyüyorsa
- Hala prompt tasarımında iterate ediyorsan (caching seni bir prompt'a kilitler)

## Caching stratejisi seçimi

### Exact caching

**Kullan:** temperature=0, aynı prompt'lar tekrarlanıyorsa, deterministik çıktı gerekiyorsa.

```python
key = sha256(json.dumps({"model": m, "messages": msgs, "temp": 0}))
```

- Implementation: 30 dakika
- Hit oranı: çoğu app için %10-25, FAQ bot'ları için %40-60
- Gecikme: <1ms (dict lookup)
- Risk: altta yatan veri değişirse bayat yanıtlar

**Atla:** temperature > 0, her sorgu benzersizse, gerçek zamanlı veri gerekiyorsa.

### Semantic caching

**Kullan:** kullanıcılar aynı soruyu farklı kelimelerle soruyorsa, FAQ-ağırlıklı ürünler, müşteri destek.

- Implementation: 2-4 saat (embedding + benzerlik + depolama)
- Hit oranı: exact cache üzerine %15-35
- Gecikme: 10-50ms (embedding + ANN arama)
- Risk: false positive'ler (benzer ama farklı bir soru için yanlış cache'lenmiş cevabı döndürme)

**Eşik kılavuzu:**
- 0.98+: çok muhafazakâr, neredeyse hiç false positive yok, daha düşük hit oranı
- 0.95: factual Q&A için iyi denge
- 0.90: agresif, daha yüksek hit oranı ama yanlış cevap riski
- 0.85: sadece düşük riskli uygulamalar için (öneri, autocomplete)

**Atla:** her sorgunun benzersiz context'i varsa (kod üretimi), yanıtlar en güncel veriyi yansıtmalı, sorgu uzayı sınırsızsa.

### Provider prompt caching

**Kullan:** system prompt > 1.024 token (OpenAI) veya modele özgü minimum, aynı prefix tekrar tekrar gönderiliyorsa.

| Sağlayıcı | Eylem | Tasarruf |
|----------|--------|---------|
| Anthropic | System mesajına `cache_control: {"type": "ephemeral"}` ekle | Cache'lenmiş prefix'te %90 (%25 yazma primi sonrası) |
| OpenAI | Hiçbir şey (otomatik) | Cache'lenmiş prefix'te %50 |
| Google | Açık TTL ile Context Caching API kullan | Cache'lenmiş context'te ~%75 |

**Atla:** system prompt istek başına değişiyorsa, prompt minimum uzunluğun altındaysa.

## Model routing kuralları

### Anahtar kelime bazlı (basit, hızlı)

```
basit:  <= 5 kelime VEYA FAQ anahtar kelimeleriyle eşleşiyor -> gpt-4o-mini ($0.15/$0.60)
orta:   genel sorgular, özetler                              -> claude-sonnet ($3/$15)
karmaşık: "analiz et", "karşılaştır", "debug et"             -> gpt-4o ($2.50/$10)
```

- Implementation: 1 saat
- Doğruluk: %70-80
- Tasarruf: model maliyetlerinin %40-60'ı

### Embedding bazlı (daha doğru)

Kategori başına 50-100 etiketli sorguyu embed et. Yeni sorguları en yakın komşuya göre sınıflandır.

- Implementation: 4-8 saat
- Doğruluk: %85-92
- Tasarruf: model maliyetlerinin %50-70'i
- Ek maliyet: sınıflandırma embedding'leri için ~$0.02/1M token (ihmal edilebilir)

### ML bazlı (production seviyesi)

Tarihsel sorgu/model çiftleri üzerinde küçük bir sınıflandırıcı (logistic regression veya küçük BERT) eğit.

- Implementation: 1-2 hafta
- Doğruluk: %90-95
- Tasarruf: model maliyetlerinin %60-75'i
- Gerekli: production trafiğinden etiketli eğitim verisi

## Rate limiting konfigürasyonu

### Tier başına token bucket parametreleri

| Tier | Bucket Boyutu | Refill Oranı | Maks RPM | Günlük Cap |
|------|-------------|-------------|---------|-----------|
| Ücretsiz | 50K token | 500/sn | 10 | 50K |
| Pro | 500K token | 5K/sn | 60 | 500K |
| Enterprise | 5M token | 50K/sn | 300 | 5M |

### Implementation checklist

1. Bucket'ları multi-instance app'ler için Redis'te sakla (in-memory'de değil)
2. Race condition'ları önlemek için atomik operasyonlar kullan (MULTI/EXEC)
3. Reddetme yanıtlarıyla birlikte `Retry-After` header'ı döndür
4. Reddedilen istekleri bir metrik olarak izle (>%5 reddetme = tier limitleri çok sıkı)
5. Graceful degradation uygula: önce pahalı model isteklerini reddet, ucuz model erişimini koru

## Bütçe kontrolleri

### Üç eşikli devre kesici

| Eşik | Eylem | Geri alınabilir |
|-----------|--------|------------|
| Aylık bütçenin %70'i | Uyarı logla, ekibe Slack/PagerDuty ile uyar | Evet (oto) |
| Aylık bütçenin %85'i | Tüm trafiği en ucuz modele yönlendir | Evet (oto, sonraki fatura döngüsü) |
| Aylık bütçenin %95'i | Sadece cache'lenmiş yanıtları sun, yeni LLM çağrılarını reddet | Evet (manuel reset veya sonraki döngü) |

### Kullanıcı başına maliyet izleme

Kullanıcı başına kümülatif maliyeti izle. Medyanın 10 katını aşan kullanıcıları işaretle. Yaygın nedenler:
- Meşru power user (tier'ını yükselt)
- Prompt injection döngüsü (otomatik istek gönderen bot)
- Verimsiz entegrasyon (her hatada retry yapan client)

## Maliyet izleme alanları

Her API çağrısını şu alanlarla logla:

```json
{
  "timestamp": "2026-04-02T10:30:00Z",
  "model": "gpt-4o",
  "input_tokens": 1523,
  "output_tokens": 487,
  "cached_input_tokens": 1024,
  "latency_ms": 1847,
  "cost_usd": 0.006142,
  "user_id": "user_abc123",
  "cache_status": "partial_hit",
  "request_category": "customer_support",
  "complexity_class": "medium",
  "routed_from": "gpt-4o"
}
```

### Dashboard'a koyulacak ana metrikler

- **Sorgu başına maliyet** (P50, P95, P99) -- model başına, özellik başına, kullanıcı tier'ı başına
- **Cache hit oranı** -- exact vs semantic, zaman içinde trend
- **Model dağılımı** -- model başına trafik %'si, model başına maliyet
- **Bütçe yakma oranı** -- mevcut oranda projeksiyonlu aylık harcama vs mevcut harcama
- **Reddetme oranı** -- rate-limit'lenen isteklerin %'si, tier başına

## Sık yapılan hatalar

| Hata | Neden zarar verir | Çözüm |
|---------|-------------|-----|
| Temperature > 0 ile caching | Non-deterministik çıktılar, bayat cache yanlış çeşit verir | Sadece temp=0 çağrılarını cache'le veya cache'lenmiş yanıtların rastgeleliği kaybedeceğini kabul et |
| Semantic cache eşiği çok düşük | Yüzeyel olarak benzer sorgular için yanlış cevaplar döndürür | 0.95'ten başla, sadece false positive oranını ölçtükten sonra düşür |
| Cache invalidation yok | Altta yatan veri değiştiğinde yanıtlar bayatlar | TTL ayarla (dinamik veri için 1 saat, statik için 24 saat), veri güncellemelerinde invalidate et |
| Tüm trafiği en ucuz modele yönlendirmek | Kalite düşer, kullanıcılar fark eder | Karmaşıklığa göre yönlendir, tier başına kaliteyi ölç, minimum kalite eşikleri ayarla |
| Kullanıcı başına limit yok | Tek kötüye kullanıcı tüm bütçeyi yakar | Cömert olsa bile her zaman kullanıcı başına kota uygula |
| Output token'ları görmezden gelmek | Output token başına input'tan 2-5x daha pahalıya mal olur | max_tokens'ı uygun ayarla, stop sequence kullan, çıktıları sıkıştır |
| Prompt stabil olmadan cache'lemek | Cache eski prompt'ların yanıtlarıyla dolar | Sadece prompt finalize edildikten sonra caching'i etkinleştir, prompt değişikliklerinde cache'i temizle |

## Fiyat referansı (Nisan 2026 itibarıyla)

| Model | Input ($/1M) | Output ($/1M) | Cached Input ($/1M) | En İyi |
|-------|-------------|--------------|--------------------|---------| 
| gpt-4.1-nano | $0.10 | $0.40 | $0.025 | Yüksek hacimli basit görevler |
| gpt-4o-mini | $0.15 | $0.60 | $0.075 | Basit routing, sınıflandırma |
| gemini-2.5-flash | $0.15 | $0.60 | $0.0375 | Bütçe multimodal |
| claude-haiku-3.5 | $0.80 | $4.00 | $0.08 | Hızlı orta-tier görevler |
| o4-mini | $1.10 | $4.40 | $0.275 | Bütçeyle muhakeme |
| gemini-2.5-pro | $1.25 | $10.00 | $0.3125 | Uzun context, multimodal |
| gpt-4o | $2.50 | $10.00 | $1.25 | Genel amaçlı, function calling |
| claude-sonnet-4 | $3.00 | $15.00 | $0.30 | Kalite/maliyet dengeli |
| claude-opus-4 | $15.00 | $75.00 | $1.50 | Maksimum kalite, karmaşık muhakeme |
