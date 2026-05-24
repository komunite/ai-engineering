# Yönetilen LLM Platformları — Bedrock, Vertex AI, Azure OpenAI

> Üç hyperscaler, üç farklı strateji. AWS Bedrock bir model marketplace'i — Claude, Llama, Titan, Stability, Cohere tek bir API'nin arkasında. Azure OpenAI özel OpenAI ortaklığı artı dedicated kapasite için Provisioned Throughput Units (PTU'lar). Vertex AI Gemini-öncelikli; en iyi long-context ve multimodal hikayesi onda. 2026'da Artificial Analysis Llama 3.1 405B eşdeğerlerinde Azure OpenAI'ı ~50 ms medyan, Bedrock'u ~75 ms ölçüyor — farkı PTU'lar açıklıyor çünkü dedicated kapasite shared on-demand'i yener. Karar kuralı "hangisi en hızlı" değil, "hangi model kataloğu ve FinOps yüzeyi ürünüme uyuyor" sorusu. Bu ders, tradeoff'ları yazılı şekilde — sezgilerle değil — seçmeyi öğretir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak maliyet-ve-gecikme karşılaştırıcı)
**Ön koşullar:** Faz 11 (LLM Engineering), Faz 13 (Tools & Protocols)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Üç platform stratejisini (marketplace vs özel vs Gemini-öncelikli) adlandır ve her birini bir ürün kullanım senaryosuyla eşleştir.
- Azure OpenAI'da Provisioned Throughput Units'in (PTU) sana ne aldığını ve 405B ölçeğinde on-demand Bedrock'un neden tipik olarak ~25 ms daha yavaş okunduğunu açıkla.
- Her platform için FinOps atıf yüzeyini diyagramla (Bedrock Application Inference Profile vs Vertex project-per-team vs Azure scope'lar + PTU rezervasyonları).
- Bir "iki-sağlayıcı minimum" politikası yaz ve 2026'da tek-vendor lock-in'in neden pahalı bir hata olduğunu açıkla.

## Sorun

Ürünün için Claude 3.7 Sonnet'i seçtin. Şimdi onu serve etmen gerek. Anthropic API'ını doğrudan çağırabilirsin, ya da AWS Bedrock üzerinden çağırabilirsin, ya da bir gateway üzerinden gidebilirsin. Direkt API en basiti; Bedrock BAA'ları, VPC endpoint'leri, IAM ve CloudWatch atıfını ekler. Gateway failover, birleşik faturalama ve sağlayıcılar arası rate limit'leri ekler.

Daha derin soru katalog. Eğer aynı üründe Claude ve Llama ve Gemini'ye ihtiyacın varsa, hepsini tek bir yerden satın alamazsın — eğer o yer aynı anda Bedrock artı Vertex artı Azure OpenAI değilse. Hyperscaler'lar değiştirilebilir değil — her biri model katmanına kimin sahip olduğu konusunda farklı bir bahis yaptı.

Bu ders üç bahsi, gecikme farkını, FinOps farkını ve lock-in riskini haritalandırır.

## Kavram

### Üç strateji

**AWS Bedrock** — marketplace. Claude (Anthropic), Llama (Meta), Titan (AWS first-party), Stability (görüntü), Cohere (embeddings), Mistral, ayrıca görüntü ve embedding alt-katalogları. Tek API, tek IAM yüzeyi, tek CloudWatch export'u. Bedrock'un bahsi, müşterilerin tek bir modelden çok opsiyonelliği istediği yönünde.

**Azure OpenAI** — özel ortaklık. Azure datacenter'larında GPT-4 / 4o / 5 / o-serisi, DALL·E, Whisper ve OpenAI modellerinin fine-tuning'i. "Azure OpenAI Service" kataloğunda OpenAI-dışı model yok — onlar Azure AI Foundry'ye (ayrı ürün) gidiyor. Azure'un bahsi, OpenAI'ın frontier olarak kalacağı ve müşterilerin o spesifik ilişkide enterprise kontroller isteyeceği yönünde.

**Vertex AI** — önce Gemini, geri kalan her şey ikinci. Gemini 1.5 / 2.0 / 2.5 Flash ve Pro, ayrıca Model Garden (üçüncü-taraf). Vertex'in bahsi multimodal long-context — 1M-token'lık Gemini context'i farklılaştırıcı.

### Ölçekte gecikme farkı

Artificial Analysis sürekli benchmark çalıştırır. Eşdeğer Llama 3.1 405B deployment'larında (shared on-demand), Azure OpenAI medyan first-token gecikmesi yaklaşık 50 ms; Bedrock yaklaşık 75 ms. Fark bir AWS başarısızlığı değil — bir kapasite modeli farkı. Azure PTU'ları (Provisioned Throughput Units) satar; bunlar tenant'ın için GPU kapasitesini rezerve eder. Bedrock'un eşdeğeri (Provisioned Throughput) var, ama birim başına saatte ~$21'dan başlar ve çoğu müşteri shared on-demand'de kalır.

On-demand shared kapasite diğer tüm müşterilerin trafiğiyle yarışır. Dedicated kapasite yarışmaz. Eğer ürün SLA'in P99'da TTFT < 100 ms ise, ya Azure'da PTU satın alırsın, ya Bedrock Provisioned Throughput satın alırsın, ya da varsayılan varyansı kabul edersin.

### Provisioned Throughput ekonomisi

Azure PTU'lar: rezerve edilmiş bir inference compute bloğu. Öngörülebilir iş yükleri için on-demand'e karşı %70'e varan tasarruf. Trafiğe bakılmaksızın saat başına sabit maliyetlenir — boşta olsa bile rezervasyon için ödersin. Break-even genelde %40-60 sürdürülen utilization civarında.

Bedrock Provisioned Throughput: model ve bölgeye bağlı olarak saatte $21-$50. Benzer matematik — break-even tepe utilization'ın yarısı civarında. Aylık taahhüt gerekli.

Vertex provisioned kapasite Gemini SKU başına satılır; fiyatlandırma model ve bölgeye göre değişir ve daha az kamuya duyurulur.

### FinOps yüzeyi — gerçek farklılaştırıcı

**Bedrock Application Inference Profile'lar** marketplace'teki en temiz atıf. Bir profili `team`, `product`, `feature` ile etiketle; tüm model çağrılarını üzerinden yönlendir; CloudWatch profil başına maliyeti post-processing olmadan parçalar. 2025'te eklendi, hâlâ en granüler hyperscaler-native çözüm.

**Vertex** atıfı project-per-team artı her-yerde-label. Her takımı bir GCP projesi olarak modellersin, her kaynağa label koyar, rollup'lar için BigQuery Billing Export + DataStudio kullanırsın. Daha fazla iş, ama BigQuery sana maliyet verisi üzerinde arbitrary SQL verir.

**Azure** subscription/resource-group scope'larına artı tag'lere dayanır, PTU rezervasyonları first-class maliyet objesi olarak. Tag'ler isteklerden değil resource group'larından miras alınır, dolayısıyla istek-başı atıf Application Insights custom metrics ya da header damgalayan bir gateway gerektirir.

Desen: Bedrock native olarak en temiz, Vertex BigQuery üzerinden en esnek, Azure enstrümante etmedikçe en opak.

### Lock-in 2026 riski

Tek bir model baskınken tek-hyperscaler taahhüdü tamamdı. 2026'da frontier aylık değişiyor — bir çeyrek Claude 3.7, sonraki Gemini 2.5, sonraki GPT-5. Tek bir platforma kilitlenmek seni frontier'ın üçte ikisinden dışarı kilitler.

Çalışan takımların benimsediği desen: herhangi bir ürün-kritik LLM çağrısı için iki-sağlayıcı minimum. Bedrock artı Azure OpenAI yaygın çift — biri Claude, diğeri GPT, aralarında failover, aynı gateway. Maliyet artışı ihmal edilebilir çünkü gateway optimal yönlendirir; kesintilerde (Ocak 2025 Azure OpenAI olayı, AWS us-east-1 kesintisi gibi) erişilebilirlik artışı belirleyici.

### Veri ikametgâhı, BAA'lar ve regüle edilmiş endüstriler

Bedrock: çoğu bölgede BAA; VPC endpoint'ler; guardrail'ler. Yaygın fintech varsayılanı.
Azure OpenAI: HIPAA, SOC 2, ISO 27001; AB veri ikametgâhı; enterprise-regüle varsayılanı.
Vertex: HIPAA, GDPR, bölge başına veri ikametgâhı; Google Cloud'un compliance stack'i.

Üçü de temel checkbox'ları karşılar. Farklar veri saklama politikalarında, log'ların nasıl ele alındığında ve abuse-monitoring'in trafiğini okuyup okumadığında (çoğunda varsayılan opt-in; enterprise için opt-out mevcut).

### Hatırlaman gereken sayılar

- Llama 3.1 405B eşdeğerlerinde Azure OpenAI medyan TTFT: ~50 ms (PTU'larla).
- On-demand Bedrock medyan TTFT: ~75 ms.
- Bedrock Provisioned Throughput: birim başına saatte $21-$50.
- Azure PTU break-even: ~%40-60 sürdürülen utilization.
- Yüksek utilization'da on-demand'e karşı PTU tasarrufu: %70'e kadar.

## Kullan

`code/main.py` üç platformu sentetik bir iş yükünde karşılaştırır — on-demand vs PTU ekonomisini, TTFT varyansını ve maliyet atıf fidelity'sini modeller. Çalıştır, PTU'ların nerede ödediğini ve marketplace'in model çeşitliliğinin nerede TTFT farkından ağır bastığını gör.

## Yayınla

Bu ders `outputs/skill-managed-platform-picker.md` üretir. Bir iş yükü profili verildiğinde (gereken modeller, TTFT SLA, günlük hacim, compliance gereklilikleri), birincil platform, yedek ve FinOps enstrümantasyon planı önerir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. 70B sınıfı bir model için Azure PTU on-demand'i hangi sürdürülen utilization'da yener? Break-even'ı hesapla ve duyurulan %40-60 bandıyla karşılaştır.
2. Ürünün Claude 3.7 Sonnet ve GPT-4o gerektiriyor. İki-sağlayıcı deployment'ı tasarla — hangisi hangi hyperscaler'a, önünde hangi gateway, failover politikası ne?
3. Regüle edilmiş bir sağlık müşterisi BAA, US-East veri ikametgâhı ve P99'da 100ms-altı TTFT gerektiriyor. Bir platform seç ve üç spesifik özellikle gerekçelendir.
4. Bedrock faturanın bu ay trafik değişikliği olmadan 4 kat arttığını keşfettin. Application Inference Profile'lar olmadan suçluyu nasıl bulurdun? Profile'larla ne kadar sürer?
5. Azure OpenAI ve Bedrock fiyatlandırma sayfalarını oku. Aylık 100M-token'lık bir Claude iş yükü için hangisi daha ucuz — direkt Anthropic API, Bedrock on-demand, ya da Bedrock Provisioned Throughput?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Bedrock | "AWS LLM servisi" | Claude, Llama, Titan, Mistral, Cohere'i kapsayan model marketplace'i |
| Azure OpenAI | "Azure'un ChatGPT'si" | Azure datacenter'larında özel OpenAI modelleri, enterprise kontrollerle |
| Vertex AI | "Google'ın LLM'i" | Üçüncü-taraf modeller için Model Garden'lı Gemini-öncelikli platform |
| PTU | "dedicated kapasite" | Provisioned Throughput Unit — rezerve edilmiş inference GPU'ları, saat başına fiyatlandırılır |
| Application Inference Profile | "Bedrock tag'leme" | Tag'lerle ürün başına maliyet/kullanım profili, CloudWatch-native |
| Model Garden | "Vertex kataloğu" | Vertex AI'ın üçüncü-taraf model bölümü, Gemini'den ayrı |
| Two-provider minimum | "LLM redundancy" | Her kritik LLM yolunu ≥2 hyperscaler üzerinde çalıştırma politikası |
| BAA | "HIPAA evrakı" | Business Associate Agreement; PHI için gerekli; üçü de sağlar |
| Abuse monitoring | "log gözcüsü" | Prompt'lar/çıktılar üzerinde sağlayıcı-taraflı güvenlik taraması; enterprise'da opt-out |

## İleri Okuma

- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) — yetkili rate card'ı ve Provisioned Throughput fiyatlandırması.
- [Azure OpenAI Service Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/) — PTU ekonomisi ve rate card'lar.
- [Vertex AI Generative AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) — Gemini tier'ları ve Model Garden ek ücretleri.
- [Artificial Analysis LLM Leaderboard](https://artificialanalysis.ai/) — sağlayıcılar arasında sürekli gecikme ve throughput benchmark'ları.
- [The AI Journal — AWS Bedrock vs Azure OpenAI CTO Guide 2026](https://theaijournal.co/2026/03/aws-bedrock-vs-azure-openai/) — enterprise karar framework'ü.
- [Finout — Bedrock vs Vertex vs Azure FinOps](https://www.finout.io/blog/bedrock-vs.-vertex-vs.-azure-cognitive-a-finops-comparison-for-ai-spend) — atıf mekaniğini yan yana.
