# LLM'ler için FinOps — Unit Economics ve Multi-Tenant Atıf

> Geleneksel FinOps LLM harcamasında çöker. Maliyetler kaynak-uptime değil, token-transaksiyon. Tag'ler eşlenmiyor — bir API çağrısı bir asset değil, bir transaksiyondur. Mühendislik kararları (prompt tasarımı, context window, output uzunluğu) finansal kararlardır. 2026 playbook'unda birinci günden enstrümante edilmesi gereken üç atıf boyutu var: koltuk fiyatlandırması ve genişleme için kullanıcı başına (`user_id`); ürün yüzeyi maliyeti ve önceliklendirme için görev başına (`task_id` + `route`); unit economics ve renewal için tenant başına (`tenant_id`). Dört token katmanı — prompt, tool, memory, response — tek bir kova harcamayı gizler. Multi-tenant ürünler için yaptırım merdiveni: tenant başına rate limit'ler (beklenen tepenin 2-3x'i, net 429 + retry-after); günlük harcama tavanı (sözleşmeli tavanın 1.5-3x'i; rate sıkma + alert tetikler); harcama z-skoru > 4'te kill switch'ler (auto-pause + on-call'a page). Atıf desenleri: tag-and-aggregate, telemetry-joiner (trace-ID → billing; en yüksek doğruluk), sampling-and-extrapolation, model-based allocation, event-sourced, real-time streaming. Unit metrik: çözülen sorgu başına maliyet, üretilen artifact başına maliyet — $/M token değil. Retroaktif tag'leme her zaman kaçırır; istek oluşturmada enstrümante et.

**Tür:** Öğrenim
**Diller:** Python (stdlib, kill switch'li oyuncak cost-attribution simülatörü)
**Ön koşullar:** Faz 17 · 13 (Observability), Faz 17 · 14 (Caching)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Geleneksel FinOps'un (tag'ler + tier'lar) LLM harcamasında neden çöktüğünü açıkla ve üç yeni atıf boyutunu adlandır.
- Dört token katmanını (prompt, tool, memory, response) ve tek-kova faturalandırmanın maliyeti neden gizlediğini say.
- Multi-tenant bir ürün için bir yaptırım merdiveni (rate → spend cap → kill switch) tasarla.
- $/M token yerine bir unit metrik (çözülen sorgu / artifact başına maliyet) seç.

## Sorun

Faturan $40.000 diyor. Bilmiyorsun:
- Hangi tenant harcadı.
- Hangi ürün özelliği sürükledi.
- Bireysel bir kullanıcı suiistimal mi etti.
- Suçlu prompt şişmesi, tool çağrıları ya da bellek amplifikasyonu muydu.

Sağlayıcı-tarafı tag-and-aggregate tag'lerin line item'lara yayıldığı cloud kaynakları (EC2, S3) için çalışır. LLM API çağrıları auto-tag yapmaz — çağrı noktasında user/task/tenant damgalaman ve taşıman gerek. Retroaktif atıf her zaman kenar durumları kaçırır.

## Kavram

### Üç atıf boyutu

**Kullanıcı başına** (`user_id`): kim neye maliyetlendi. Koltuk fiyatlandırmasını, genişleme konuşmalarını sürükler, güçlü kullanıcıları tanımlar.

**Görev başına** (`task_id` + `route`): hangi ürün yüzeyi neye maliyetlendi. Özellik önceliklendirmesini, pahalı-özellikleri-öldür kararlarını sürükler.

**Tenant başına** (`tenant_id`): hangi müşteri kârlı. Unit economics'i, renewal fiyatlandırmasını, tier eşiklerini sürükler.

Birinci günden çağrı noktasında üçünü de enstrümante et. Retroaktif her zaman daha kötü.

### Dört token katmanı

| Katman | Örnek | Tipik toplam % |
|-------|---------|---------------------|
| Prompt | system + user input | %40-60 |
| Tool | geri beslenen tool-çağrı sonuçları | %20-40 (agent iş yükleri) |
| Memory | önceki konuşma / çekilen doc'lar | %10-30 |
| Response | model output'u | %10-30 |

Dördünü birlikte kovalamak optimizasyonu körleştirir. Atıf şemanda ayır.

### Yaptırım merdiveni

1. **Tenant başına rate limit**. Beklenen tepenin 2-3x'i. `Retry-After` ile 429 döndür. Tenant friction görür; sürpriz fatura yok.

2. **Tenant başına günlük harcama tavanı**. Sözleşmeli tavanın 1.5-3x'i. Tetikleyici: rate limit'i sık + müşteri-başarı'yı uyar.

3. **Tenant baseline'ına göre harcama z-skoru > 4'te kill switch**. Tenant'ı auto-pause et; on-call'a page; ops + CS'ye eskale et.

### Atıf desenleri

- **Tag-and-aggregate**: metadata header'ları damgala; sonra toplu. Basit; kaba.
- **Telemetry joiner**: trace ID'leri üzerinden trace'leri billing'e join'le. En yüksek doğruluk. Olgun takımların yaptığı.
- **Sampling + extrapolation**: %5-10 örnekle, çarp. Kaba harcama için maliyet-etkin; kuyrukları kaçırır.
- **Model-based allocation**: cost driver'ı çıkarsamak için regresyon. Tag'siz legacy veri için.
- **Event-sourced**: bir stream'de event olarak maliyet (Kafka / Kinesis). Gerçek zamanlı.
- **Real-time streaming**: dashboard alt-saniye günceller.

### Cost per X unit metrik

$/M token vendor konuşması. Ürün metrikleri:

- Çözülen destek ticket'ı başına maliyet.
- Üretilen makale başına maliyet.
- Başarılı agent görevi başına maliyet.
- Kullanıcı-oturum-dakikası başına maliyet.

Maliyeti bir ürün çıktısına bağla. Aksi takdirde optimizasyon yere basmaz.

### Cost attribution trace şekli

```
trace_id: abc123
  user_id: u_42
  tenant_id: t_7
  task_id: task_classify_doc
  route: model_haiku
  layers:
    prompt_tokens: 1800
    tool_tokens: 600
    memory_tokens: 400
    response_tokens: 150
  cost_usd: 0.0135
  cached_input: true
  batch: false
```

Her çağrıda yayınla. Data lake'te sakla. Boyut başına topla. Faz 17 · 13 observability stack'i bunun yaşadığı yer.

### Bileşik-tasarruflar yığını

Yığın: cache + batch + route + gateway. Dördüyle:
- Cache L2 (Faz 17 · 14): ~10x daha ucuz input.
- Batch (Faz 17 · 15): %50 indirim.
- Ucuz modele route (Faz 17 · 16): %60 maliyet azaltma.
- Gateway verimliliği (Faz 17 · 19): redundancy + retry'lar.

En-iyi-durum yığılı: naif baseline'ın ~%5-10'u. Çoğu takımın 2-3 manivelası devrede; az kişi dördünü yığıyor.

### Hatırlaman gereken sayılar

- Atıf boyutları: kullanıcı başına, görev başına, tenant başına.
- Dört token katmanı: prompt, tool, memory, response.
- Kill switch: harcama z-skoru > 4.
- Unit metrik: çözülen sorgu başına maliyet, $/M token değil.
- Yığılı optimizasyonlar: baseline'ın ~%5-10'u mümkün.

## Kullan

`code/main.py` üç-tier yaptırım merdiveniyle multi-tenant bir LLM servisi simüle eder. Suiistimal eden bir tenant enjekte eder ve kill switch'in ateşlemesini gösterir.

## Yayınla

Bu ders `outputs/skill-finops-plan.md` üretir. Ürün ve ölçek verildiğinde, atıf şemasını ve yaptırım merdivenini tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Kill switch hangi z-skorda ateşler? Eşiği nasıl seçersin?
2. Tenant başına, görev başına bir maliyet dashboard'u tasarla. İlk inşa ettiğin 5 görünüm ne?
3. En büyük tenant'ın unit-economics-negatif. Müşteri etkisine göre sıralanmış üç müdahale öner.
4. Bir destek ürünü için ticket başına çözülen maliyeti hesapla: ticket başına 3M token, günde ~800 ticket, GPT-5 cache'lenmiş oran.
5. Retroaktif tag'lemenin asla işe yarayıp yaramayacağını savun. Ne zaman kabul edilebilir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Kullanıcı başına atıf | "kullanıcı-seviyesi maliyet" | Her çağrıda damgalı `user_id` |
| Görev başına atıf | "özellik maliyeti" | `task_id` + `route` ürün yüzeyini tanımlar |
| Tenant başına atıf | "müşteri maliyeti" | `tenant_id`; unit economics'i sürükler |
| Dört token katmanı | "maliyet katmanları" | prompt + tool + memory + response |
| Rate limit | "429 koruması" | Gateway'de uygulanan tenant başına tavan |
| Günlük harcama tavanı | "günlük tavan" | Alert'li tenant-kapsamlı bütçe |
| Kill switch | "auto-pause" | Harcama z-skoru > 4 auto-süspansiyon tetikler |
| Cost per resolved | "ürün unit metriği" | Token'a değil, ürün çıktısına bağlı maliyet |
| Telemetry joiner | "trace-to-billing" | En-yüksek-doğrulukta atıf deseni |
| Yığılı optimizasyon | "cache+batch+route+gateway" | Baseline'ın ~%5-10'una bileşik tasarruflar |

## İleri Okuma

- [FinOps Foundation — FinOps for AI Overview](https://www.finops.org/wg/finops-for-ai-overview/)
- [FinOps School — Cost per Unit 2026 Guide](https://finopsschool.com/blog/cost-per-unit/)
- [Digital Applied — LLM Agent Cost Attribution 2026](https://www.digitalapplied.com/blog/llm-agent-cost-attribution-guide-production-2026)
- [PointFive — Managed LLMs in Azure OpenAI](https://www.pointfive.co/blog/finops-for-ai-economics-of-managed-llms-in-azure-open-ai)
