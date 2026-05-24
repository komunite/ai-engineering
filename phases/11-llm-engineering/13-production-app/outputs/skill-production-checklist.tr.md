---
name: skill-production-checklist
description: LLM uygulamalarını production'a ship etmek için karar çerçevesi -- spesifik eşikler ve geçti/kaldı kriterleri ile her bileşeni kapsar
version: 1.0.0
phase: 11
lesson: 13
tags: [production, deployment, llm, architecture, scaling, cost, observability, guardrails]
---

# Production LLM Checklist

Bir LLM uygulamasını ship ederken, bu checklist'i sırayla işle. Her bölümün spesifik eşiklerle geçti/kaldı kriterleri vardır.

## 1. Güvenlik (Ship Engelleyiciler)

Buradaki her madde herhangi bir deployment'tan önce geçmelidir.

| Kontrol | Geçme Kriteri | Nasıl Doğrula |
|-------|--------------|---------------|
| Env var'larda API key | Kod tabanında sıfır hardcoded key | `grep -r "sk-" --include="*.py"` hiçbir şey döndürmez |
| Input guardrail'ler aktif | Prompt injection pattern'leri bloklanır | "Önceki tüm talimatları yok say" gönder -- bloklanmış yanıt döner |
| PII redaction | SSN, kredi kartı, e-posta pattern'leri yakalanır | "SSN'im 123-45-6789" gönder -- PII LLM çağrısından önce redakte edilir |
| Output filtreleme | Tehlikeli içerik bloklanır | Model `DROP TABLE`, `rm -rf`, `exec()` pattern'lerini döndüremez |
| Rate limiting | Kullanıcı başına istek capı uygulanır | Aynı kullanıcıdan 10 saniyede 100 istek -- son 50+ reddedilir |
| Tüm endpoint'lerde auth | Auth'suz LLM erişimi yok | Token'sız `curl /v1/chat` 401 döndürür |
| CORS kısıtlı | Sadece production domain'leri izinli | `Origin: evil.com` isteği reddedilir |
| Maks input token | Limiti aşan istekler reddedilir | 50K token input gönder -- 413 döner veya kesilir |

## 2. Güvenilirlik (İlk-Hafta Hayatta Kalma)

Bunlar ilk on-call olayını önler.

| Kontrol | Geçme Kriteri | Nasıl Doğrula |
|-------|--------------|---------------|
| Backoff ile retry | 5xx'te 3 retry, üstel gecikme | İstek ortasında LLM mock'unu öldür -- retry'lar log'larda görünür |
| Fallback model chain | Chain'de 2+ model | Birincil model erişilemez -- yanıt yine fallback'ten döner |
| İstek timeout'u | Tüm dış çağrılarda maks 30sn | Yavaş LLM mock'u (60sn) -- istek 30sn'de timeout olur |
| Graceful degradation | Cache/RAG başarısızlığı servisi çökertmez | Cache'i durdur -- istekler yine başarılı olur (daha yavaş, daha pahalı) |
| Health check endpoint | Bağımlılık durumu döner | `GET /health` `{"status": "healthy", "cache": ..., "llm": ...}` döner |
| Streaming çalışır | İlk token 500ms altında | Time-to-first-token ölçülür, tutarlı şekilde < 500ms |
| Hata mesajları güvenli | İç hatalar asla kullanıcıya sızmaz | 500'ü zorla -- kullanıcı generic hata görür, stack trace değil |

## 3. Maliyet Kontrolü (İlk-Ay Ekonomisi)

Bunlar $50K sürpriz faturayı önler.

| Kontrol | Geçme Kriteri | Nasıl Doğrula |
|-------|--------------|---------------|
| İstek başına maliyet izlenir | Her istek token sayısı + USD maliyeti logla | İstek log'u `input_tokens`, `output_tokens`, `cost_usd` alanlarına sahip |
| Semantic cache aktif | Tekrar pattern'lerinde > %20 hit oranı | 1000 test isteğinden sonra cache istatistikleri hit oranı gösterir |
| Cache TTL yapılandırılmış | Girişler süresi dolar (varsayılan: 1 saat) | Giriş eklenir -- TTL sonrası döndürülmez |
| Kullanıcı başına maliyet izleme | Maliyet user_id'ye göre toplanır | Dashboard/API maliyete göre top 10 kullanıcıyı gösterir |
| Maliyet uyarısı | Günlük bütçenin %80'inde uyarı | $10 günlük bütçe ayarla, $8.50 istek gönder -- uyarı tetiklenir |
| Maliyete göre model routing | Düşük karmaşıklıklı sorgular daha ucuz model kullanır | Basit soru gpt-4o-mini'ye, karmaşık gpt-4o'ya yönlenir |
| Maks output token ayarlanmış | Yanıtlar template başına sınırlı | max_output_tokens=512 olan template -- yanıt asla aşmaz |

**Maliyet tahmini formülü:**
```
Aylık LLM maliyeti = DAU x kullanıcı_başına_sorgu x 30 x (1 - cache_hit_oranı) x (ort_input_token x input_fiyat + ort_output_token x output_fiyat) / 1.000.000
```

**Ölçeğe göre benchmark eşikleri:**

| DAU | Hedef istek başına maliyet | Aylık bütçe |
|-----|-------------------|----------------|
| 1K | < $0.005 | < $750 |
| 10K | < $0.003 | < $4.500 |
| 100K | < $0.001 | < $15.000 |

## 4. Observability (Production'da Hata Ayıklama)

Göremediğini düzeltemezsin.

| Kontrol | Geçme Kriteri | Nasıl Doğrula |
|-------|--------------|---------------|
| Yapılandırılmış JSON logging | Her istek bir JSON log satırı üretir | Log şunları içerir: request_id, user_id, model, tokens, latency_ms, cost |
| İstek tracing'i | Bileşen zamanlamasıyla uçtan uca trace | Tek istek şunu gösterir: guardrail (5ms) + cache (2ms) + llm (3200ms) + eval (1ms) |
| Gecikme izleme | P50, P95, P99 ölçülür | 1000 istek sonrası: P50 < 2sn, P99 < 10sn |
| Hata oranı izleme | Hatalar sayılır ve kategorize edilir | Dashboard gösterir: %0.5 API hataları, %0.1 guardrail blokları, %0.01 timeout'lar |
| Cache metrikleri | Hit oranı, miss oranı, giriş sayısı görünür | `GET /v1/cache/stats` mevcut sayıları döndürür |
| A/B test metrikleri | Variant başına kalite metrikleri loglanır | Her istek karşılaştırma için prompt_template + version loglar |
| Eval logging | İstek başına kalite sinyalleri kaydedilir | Yanıt uzunluğu, gecikme, model, template versiyonu offline analiz için saklanır |

## 5. Prompt Yönetimi

Prompt'lar koddur. Onlara kod gibi davran.

| Kontrol | Geçme Kriteri | Nasıl Doğrula |
|-------|--------------|---------------|
| Versiyonlu template'ler | Her template'in adı + version string'i var | Template değişikliği yeni versiyon yaratır, eski versiyon korunur |
| A/B test desteği | Trafik deterministik user hash ile bölünür | Aynı kullanıcı bir deneyde her zaman aynı varyantı görür |
| Rollback yeteneği | Önceki versiyona < 1 dakikada dönme | Deney config değiştir -- trafik anında kayar |
| Template doğrulama | Render'dan önce değişkenler doğrulanır | Template'te eksik değişken net hata verir, KeyError değil |
| System prompt ayrımı | System ve user mesajları ayrı alanlarda | System prompt user mesajına concatenate edilmez |

## 6. Ölçekleme Hazırlığı

Lansmanda gerekli değil. 10x'te gerekli.

| Kontrol | Geçme Kriteri | Nasıl Doğrula |
|-------|--------------|---------------|
| Async LLM çağrıları | API çağrılarında thread bloklanması yok | 50 eşzamanlı istek -- sunucu CPU'su < %30 kalır |
| Connection pooling | HTTP bağlantıları yeniden kullanılır | Network trace LLM sağlayıcıya persistent connection'ları gösterir |
| Yatay ölçekleme | Stateless sunucu tasarımı | Load balancer arkasında 2 instance -- tüm istekler başarılı |
| Queue desteği | Gerçek-zamanlı olmayan görevler queue'ya gider | Özetleme isteği job_id döndürür, sonuç polling ile alınır |
| Yük test edilmiş | 100 eşzamanlı kullanıcı, < %5 hata oranı | `wrk` veya `locust` testi hedef concurrency'de geçer |

## Yeni projeler için implementation sırası

1. **Gün 1:** API sunucusu + prompt template'leri + retry'lı tek LLM çağrısı
2. **Gün 2:** Input guardrail'leri + output guardrail'leri + hata işleme
3. **Gün 3:** Semantic cache + istek başına maliyet izleme
4. **Gün 4:** Streaming (SSE) + health check endpoint
5. **Gün 5:** Yapılandırılmış logging + istek tracing + eval logging
6. **Hafta 2:** A/B testing + prompt versioning + rollback
7. **Hafta 3:** Fallback model chain + graceful degradation
8. **Hafta 4:** Yük testi + async optimizasyonu + yatay ölçekleme

## Hızlı teşhis

Production'da bir şey ters gidiyorsa, bu sırayla kontrol et:

1. **Kullanıcılar hata mı şikayet ediyor?** Health endpoint'i kontrol et, sonra log'larda hata oranı, sonra LLM sağlayıcı durum sayfası
2. **Yanıtlar yavaş mı?** P99 gecikmeyi kontrol et, sonra cache hit oranını, sonra trace'lerde LLM yanıt sürelerini
3. **Maliyet yükseliyor mu?** İstek başına maliyet trendini kontrol et, sonra cache hit oranını, sonra maliyete göre top kullanıcıları, sonra token sayısını artıran prompt template değişikliklerini ara
4. **Kalite mi düştü?** Yeni bir prompt versiyonunun deploy edilip edilmediğini kontrol et, RAG retrieval doğruluğunun değişip değişmediğini kontrol et, model sağlayıcının varsayılan model versiyonunu değiştirip değiştirmediğini kontrol et
5. **Güvenlik olayı mı?** Guardrail blok oranını kontrol et (ani düşüş = guardrail'ler kapalı), istek log'larında olağandışı pattern'leri kontrol et, API key'leri hemen döndür
