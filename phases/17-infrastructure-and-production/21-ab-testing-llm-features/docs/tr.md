# LLM Özelliklerini A/B Test Etmek — GrowthBook, Statsig ve Vibes Sorunu

> Geleneksel A/B testing non-deterministik LLM'ler için inşa edilmedi. Kritik ayrım: eval'ler "model işi yapabilir mi?" sorusunu yanıtlar; A/B testleri "kullanıcılar umursar mı?" sorusunu yanıtlar. İkisi de gerekli; vibe check'lere yayınlamak bitti. 2026'da test edilecekler: prompt mühendisliği (sözcükler), model seçimi (GPT-4 vs GPT-3.5 vs OSS; doğruluk vs maliyet vs gecikme), generation parametreleri (temperature, top-p). Gerçek vakalar: bir chatbot reward-model varyantı +%70 sohbet uzunluğu ve +%30 retention sağladı; Nextdoor AI subject-line deneyleri reward-fonksiyon iyileştirmesinden sonra +%1 CTR sağladı; Khan Academy Khanmigo gecikme-vs-matematik-doğruluk ekseninde iterasyon yaptı. Platform bölünmesi: **Statsig** (Eylül 2025'te OpenAI tarafından $1.1B'a satın alındı) — sequential testing, CUPED, hepsi-bir-arada. **GrowthBook** — open-source, warehouse-native, Bayesian + Frequentist + Sequential motorları, CUPED, SRM kontrolleri, Benjamini-Hochberg + Bonferroni düzeltmeleri. Warehouse-SQL tercihine ve organizasyonuna "OpenAI tarafından satın alındı"nın önemli olup olmadığına göre seçersin.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak sequential test simülatörü)
**Ön koşullar:** Faz 17 · 13 (Observability), Faz 17 · 20 (Progressive Deployment)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Eval'leri ("model işi yapabilir mi") A/B testlerinden ("kullanıcılar umursar mı") ayır.
- Üç test edilebilir ekseni (prompt, model, parametreler) say ve her biri için metriği seç.
- CUPED'i, sequential testing'i ve Benjamini-Hochberg çoklu-karşılaştırma düzeltmelerini açıkla.
- Warehouse-SQL duruşu ve kurumsal satın alma tutumuna göre Statsig ya da GrowthBook'u seç.

## Sorun

Bir system prompt'u elle ayarladın. Daha iyi hissettiriyor. Yayınlıyorsun. Conversion gürültüyle değişiyor. Metriği suçluyorsun. Ya da yeni bir model yayınladın ve conversion hareket etmedi — model bozuldu mu yoksa değişiklik tespit edilemeyecek kadar küçük müydü? Bilmiyorsun çünkü A/B olmadan yayınladın.

Eval'ler modelin etiketli bir kümede görevi yapıp yapamayacağını yanıtlar. Kullanıcıların output'u tercih edip etmediğini yanıtlamazlar. Yalnız kontrollü bir online deney bunu yanıtlar ve yalnızca deneyin yeterli gücü varsa, non-determinizmi kontrol ediyorsa ve çoklu karşılaştırmalar için düzeltme yapıyorsa.

## Kavram

### Eval'ler vs A/B testleri

**Eval'ler** — offline, etiketli küme, judge (rubric ya da LLM-as-judge ya da insan). Cevap: "Output bu sabit dağılımda doğru / faydalı / güvenli mi?"

**A/B test** — online, canlı kullanıcılar, randomize. Cevap: "Yeni varyant önemli olan kullanıcı-seviyesi metriği hareket ettiriyor mu?"

İkisi de gerekli. Eval'ler maruziyetten önce regresyon'ları yakalar; A/B sonrasında ürün etkisini doğrular.

### Ne test edilir

1. **Prompt mühendisliği** — sözcükler, system-prompt yapısı, örnekler. Metrik: görev başarısı, kullanıcı retention'ı, istek başına maliyet.
2. **Model seçimi** — GPT-4 vs GPT-3.5-Turbo vs Llama-OSS. Metrik: doğruluk (görev) + istek başına maliyet + gecikme P99. Çok-amaçlı.
3. **Generation parametreleri** — temperature, top-p, max_tokens. Metrik: göreve-özgü (output çeşitliliği vs determinizm).

### CUPED — varyans azaltma

Controlled-experiments Using Pre-Experiment Data. Post-period karşılaştırmasından önce pre-period varyansını regresyon'la çıkar. Tipik varyans azaltma: %30-70. Etkin örneklem boyutu bedavaya yükselir.

Uygulama: hem Statsig hem GrowthBook uygular.

### Sequential testing

Klasik A/B sabit örneklem boyutu varsayar. Sequential testler ("peek-and-decide") tekrarlanan bakışlar altında false-positive oranını kontrol eder. Always-valid sequential prosedürler (mSPRT, Howard'ın confidence sequence'ları) net kazananlarda erken durmana izin verir.

### Çoklu-karşılaştırma düzeltmeleri

%95 güvende 20 A/B test çalıştırmak şansla bir false positive üretir. Bonferroni düzeltmesi test başına α'yı sıkar; Benjamini-Hochberg false-discovery oranını kontrol eder. GrowthBook ikisini de uygular.

### SRM — sample ratio mismatch

Atama hash'i kullanıcıları varyantlara randomize eder. 50/50 bölme 47/53 sağlarsa, bir şey bozuk — SRM kontrolü bunu işaretler. İki platform da uygular.

### Statsig vs GrowthBook

**Statsig**:
- OpenAI tarafından $1.1B'a satın alındı (Eylül 2025). Hosted, SaaS.
- Sequential testing, CUPED, bekletilen popülasyonlar.
- Hepsi-bir-arada: feature flag'leri + experimentation + observability.
- En iyi uyum: takım zaten paketlenmiş bir ürün istiyor, OpenAI sahipliğini umursamıyor.

**GrowthBook**:
- Open-source (MIT); warehouse-native (Snowflake/BigQuery/Redshift'ten doğrudan okur).
- Birden fazla motor: Bayesian, Frequentist, Sequential.
- CUPED, SRM, Bonferroni, BH düzeltmeleri.
- Self-host ya da managed cloud.
- En iyi uyum: warehouse-SQL mağazası, veri takımı metrik katmanını kontrol eder, OSS ister.

### Non-determinizm gücü karmaşıklaştırır

Aynı prompt değişen output'lar üretir. Geleneksel güç hesaplamaları IID gözlemleri varsayar. LLM non-determinizmi ile, etkin örneklem boyutu nominal'den düşüktür. Güvenlik payı olarak gereken örneklem boyutunu ~1.3-1.5x ile çarp.

### Gerçek vaka çıktıları

- Chatbot reward model varyantı: +%70 sohbet uzunluğu, +%30 retention.
- Nextdoor subject line'lar: reward-fonksiyon iyileştirmesinden sonra +%1 CTR.
- Khan Academy Khanmigo: iteratif gecikme-vs-matematik-doğruluk takası.

### Anti-pattern: vibe'lara yayınlamak

Her kıdemli mühendis A/B olmadan "daha iyi hissettiriyor" diye yayınlanan bir özellik adlandırabilir. Çoğu takımın aylarca fark etmediği ürün metriklerini regrese etti. A/B zorlayıcı fonksiyon.

### Hatırlaman gereken sayılar

- Statsig OpenAI tarafından satın alındı: $1.1B, Eylül 2025.
- GrowthBook: open-source MIT; Bayesian + Frequentist + Sequential.
- CUPED varyans azaltma: %30-70.
- LLM non-determinizmi → +%30-50 örneklem-boyutu tamponu.

## Kullan

`code/main.py` sabit ve sequential sınırlarla bir sequential A/B test simüle eder. Sequential'ın erken durmana nasıl izin verdiğini gösterir.

## Yayınla

Bu ders `outputs/skill-ab-plan.md` üretir. Özellik değişikliği, iş yükü, baseline verildiğinde, platform, gate'ler, örneklem boyutu seçer.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. %3 baseline conversion ile beklenen %5 lift için, %80 güç için örneklem boyutu ne?
2. Sağlık-regüle on-prem bir müşteri için Statsig ya da GrowthBook seç.
3. Çözülen-ticket başına maliyette GPT-4 vs GPT-3.5'i test eden bir A/B tasarla. Birincil metrik, guardrail metrik, ikincil ne?
4. Canary'n geçiyor ama A/B -%1.2 conversion gösteriyor. Yayınlar mısın? Eskalasyon kriterlerini yaz.
5. Post'un %60 varyansı olan bir pre-period'a CUPED uygula. Etkin-örneklem-boyutu artışını hesapla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Eval | "offline test" | Model yetkinliğinin etiketli-küme değerlendirmesi |
| A/B test | "deney" | Kullanıcılar üzerinde canlı randomize karşılaştırma |
| CUPED | "varyans azaltma" | Varyansı azaltmak için pre-period regresyon |
| Sequential test | "peek-ok test" | Erken durmaya izin veren always-valid prosedür |
| Çoklu karşılaştırma | "aile hatası" | Birçok test çalıştırmak false positive'leri şişirir |
| Bonferroni | "sıkı düzeltme" | α'yı test sayısına böl |
| Benjamini-Hochberg | "BH FDR" | False-discovery-rate kontrolü, daha az muhafazakâr |
| SRM | "kötü bölme" | Sample ratio mismatch; atama bug'ı |
| Statsig | "OpenAI sahibi" | Ticari hepsi-bir-arada, 2025'te satın alındı |
| GrowthBook | "OSS olan" | MIT warehouse-native platform |
| mSPRT | "sequential probability ratio test" | Klasik sequential prosedür |

## İleri Okuma

- [GrowthBook — How to A/B Test AI](https://blog.growthbook.io/how-to-a-b-test-ai-a-practical-guide/)
- [Statsig — Beyond Prompts: Data-Driven LLM Optimization](https://www.statsig.com/blog/llm-optimization-online-experimentation)
- [Statsig vs GrowthBook comparison](https://www.statsig.com/perspectives/ab-testing-feature-flags-comparison-tools)
- [Deng et al. — CUPED](https://www.exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf)
- [Howard — Confidence Sequences](https://arxiv.org/abs/1810.08240)
