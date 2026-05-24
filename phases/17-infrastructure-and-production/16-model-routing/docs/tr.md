# Maliyet-Azaltma Primitive'i Olarak Model Routing

> Dinamik bir broker her isteği değerlendirir (görev tipi, token uzunluğu, embedding benzerliği, güven) ve basit sorguları ucuz bir modele gönderir, karmaşık olanları frontier modele eskale eder. Model cascading olarak da adlandırılır. Üretim vaka çalışmaları ABD/İngiltere/AB deployment'larında iso-kalitede %20-60 maliyet azaltma gösteriyor; yüksek-hacimli SaaS'ta %30'luk routing verimlilik iyileştirmesi altı haneli yıllık tasarrufa dönüşüyor. 2026 bağlamı: LLM çıkarım fiyatları yıllık ~10x düştü — bir GPT-4-sınıfı token 2022 sonlarından 2026'ya $20/M'den ~$0.40/M'e gitti. Düşüşün çoğu donanım değil, daha iyi serving stack'leri (Faz 17 · 04-09). Routing, ürün regresyonu olmadan o fiyat düşüşünü marjına çevirme yolundur. Başarısızlık modu cheap-model drift: route %40'ı daha zayıf bir modele iter, reasoning görevlerinde kalite %3-5 düşer, üç ay kimse fark etmez. Yalnız offline eval set'leri değil, online kalite metrikleriyle route'ları gate'le.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak cascading router simülatörü)
**Ön koşullar:** Faz 17 · 01 (Yönetilen LLM Platformları), Faz 17 · 19 (AI Gateway'ler)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Model cascading'i açıkla: güven kontrolüyle ucuz-öncelikli, düşük güvende eskale.
- Dört routing sinyalini (görev sınıflandırma, prompt uzunluğu, bilinen-zor kümeye embedding benzerliği, ilk-pass'ten self-confidence) say.
- Hedef routing bölüşümünde ve kalite kayıp toleransında beklenen harmanlanmış maliyeti hesapla.
- Cheap-model creep'i yakalayan drift-izleme metriğini (online kalite gate'i) adlandır.

## Sorun

Servisin GPT-5'te aylık $80k maliyetli. Analytics'in sorguların %70'inin basit olduğunu gösteriyor: "Paris'te saat kaç?" "bu cümleyi yeniden ifade et." Bir Haiku-sınıfı model bunları maliyetin %3'ünde mükemmel halleder. %30 GPT-5'in reasoning'ine ihtiyaç duyar — kod, matematik, multi-step planlama.

%70'i ucuza ve %30'u pahalıya yönlendirirsen, faturan aynı ürün kalitesinde ~%65 düşer. Bu routing. Hile kaliteyi regrese etmeden broker'ı inşa etmek.

## Kavram

### Dört routing sinyali

1. **Görev sınıflandırma**: basit/karmaşık/kodgen/matematik/sohbet. Kural-tabanlı sınıflandırıcı, küçük bir LLM ($0.25/M'de Haiku-sınıfı) ya da etiketli kovalara embedding benzerliği olabilir. Output: route = ucuz / dengeli / frontier.

2. **Prompt uzunluğu**: >4K token'lık prompt'lar tutarlılık için sık sık frontier gerektirir. <500 token'lık prompt'lar genelde gerektirmez.

3. **Bilinen-zor kümeye embedding benzerliği**: sorgu bir bilinen-zor kovaya yakınsa (cosine > 0.88), doğrudan frontier'e eskale et.

4. **İlk-pass'ten self-confidence**: ucuza gönder; modelin log-prob'ları düşük güven gösterirse YA DA reddederse YA DA hedge eden dil çıkarırsa, frontier'de yeniden dene. Trafiğin ~%10'una P95 gecikme ekler ama diğer %90'da %50+ tasarruf eder.

### Üç desen

**Pre-route** (önde sınıflandırıcı): ~5-10ms gecikme eklendi; genelde en hızlı.

**Cascade** (ucuz-öncelikli, düşük güvende eskale): ortalama gecikme ~1.2x (ucuz çalıştırma artı doğrula), eskale edilende ~2x. En iyi kalite tabanı.

**Ensemble route** (örnek için ucuz ve frontier'i paralel çalıştır, reward-model seçer): en yüksek kalite, en yüksek maliyet; yalnız kritik A/B için kullan.

### Uygulama

AI gateway'leri (Faz 17 · 19) routing'i expose eder. LiteLLM fallback ve cost-routing'li `router` config'ine sahip. Portkey guard'lar + routing'e sahip. Kong AI Gateway plugin-tabanlı routing'e sahip. OpenRouter'ın model marketplace'i bir öneri API'sı expose eder.

Open-source: RouteLLM (LMSYS), Not Diamond (ticari), Prompt Mule.

### 2026 fiyat eğrisi

| Model sınıfı | 2022 sonu | 2026 | Değişim |
|-------------|-----------|------|--------|
| GPT-4 seviye kalite | ~$20/M | ~$0.40/M | 50x daha ucuz |
| Frontier (GPT-5, Claude 4) | — | ~$3-10/M | yeni tier |

İyileştirmenin çoğu serving verimliliği — Faz 17 · 04-09'daki çekirdek dersler sağlayıcı-taraflı maliyet düşüşlerine dönüştü. Routing tüm kullanıcılarının ucuz tier'a göç etmesini beklemek yerine o kazançları uygulama katmanında yakalamana izin verir.

### Drift gerçek risk

Route'un %40'ı ucuz modele gönderiyor. Altı ay boyunca, görev dağılımı kayıyor (kullanıcılar daha sofistike oluyor, daha uzun sorular soruyor). Router fark etmiyor çünkü sınıflandırıcısı Q1 verisi üzerinde eğitilmişti. Kalite sessizce düşüyor. Kimse yeterince yüksek sesle şikayet etmiyor. Kaybettiğin bir rakip benchmark'ında öğreniyorsun.

Online kalite metrikleriyle route'ları gate'le:

- Route başına kullanıcı thumbs-up / thumbs-down.
- Route başına bekletilen örnek (%5) üzerinde otomatik LLM-judge.
- Eskalasyon oranı: cascade %30+'sı yukarı-route'a tekmeliyorsa, ucuz model aşırı-route'lanıyor.
- Route başına reddetme oranı.

### Hatırlaman gereken sayılar

- 2026 iso-kalitede routing tasarrufu: %20-60 vaka çalışmaları.
- 2022-2026 LLM fiyat düşüşü: toplam yıllık ~10x.
- GPT-4 seviye 2022 vs 2026: ~$20/M → ~$0.40/M.
- Cascade gecikme etkisi: ortalama ~1.2x, eskale edilen ~2x (trafiğin ~%10'u).

## Kullan

`code/main.py` karma bir iş yükünde pre-route, cascade ve ensemble simüle eder. Harmanlanmış maliyeti, kalite kaybını ve eskalasyon oranını raporlar.

## Yayınla

Bu ders `outputs/skill-router-plan.md` üretir. İş yükü ve kalite bütçesi verildiğinde, bir routing deseni ve sinyaller seçer.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Cascade hangi doğruluk tabanında pre-route'u yener?
2. Kullanıcı tabanın %30 enterprise (karmaşık sorgular), %70 ücretsiz tier (basit). Routing bölüşümünü tasarla. Onu hangi online metrik gate'ler?
3. Bir route kaliteyi %2 düşürür ama %40 tasarruf eder. Bu yayın mı? Ürüne bağlı — iki yanı savun.
4. OpenAI / Anthropic API'lerindeki logprob'lar kullanarak bir güven kontrolü uygula. Başladığın eşik ne?
5. Altı ay boyunca, eskalasyon oranı %8'den %22'ye tırmanıyor. Üç sebep ve her biri için düzeltmeyi teşhis et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Model routing | "maliyet broker'ı" | İstek başına model'in dinamik seçimi |
| Model cascade | "ucuz-öncelikli eskale" | Ucuz çalıştır, düşük güvende frontier'e düş |
| Pre-route | "önce sınıflandır" | Önde sınıflandırıcı; yeniden çalıştırma yok |
| Ensemble route | "paralel seç" | Birden fazla çalıştır, reward-model en iyiyi seçer |
| Eskalasyon oranı | "yukarı-route'lanmış %" | Eskale eden cascade isteklerinin fraksiyonu |
| RouteLLM | "LMSYS router" | OSS router kütüphanesi |
| Not Diamond | "ticari router" | SaaS model-routing ürünü |
| Drift | "ucuz creep" | Router fark etmeden dağılım kayması |
| Online kalite gate'i | "canlı kontrol" | Canlı trafiği örnekleyen otomatik LLM-judge |

## İleri Okuma

- [AbhyashSuchi — Model Routing LLM 2026 Best Practices](https://abhyashsuchi.in/model-routing-llm-2026-best-practices/)
- [Lukas Brunner — Rise of Inference Optimization 2026](https://dev.to/lukas_brunner/the-rise-of-inference-optimization-the-real-llm-infra-trend-shaping-2026-4e4o)
- [RouteLLM paper / code](https://github.com/lm-sys/RouteLLM)
- [Not Diamond — model routing](https://www.notdiamond.ai/)
- [OpenRouter](https://openrouter.ai/) — routing primitive'leriyle multi-model gateway.
