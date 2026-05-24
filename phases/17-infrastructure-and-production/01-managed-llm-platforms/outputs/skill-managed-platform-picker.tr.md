---
name: managed-platform-picker
description: İş yükü, SLA ve uyumluluk gereksinimleri verildiğinde managed bir LLM platformu (Bedrock, Azure OpenAI, Vertex AI) ve yedeklilik için ikinci bir platform seç — ardından bir FinOps enstrümantasyon planı üret.
version: 1.0.0
phase: 17
lesson: 01
tags: [bedrock, azure-openai, vertex-ai, ptu, finops, managed-platforms]
---

Bir iş yükü profili verildiğinde (gerekli modeller, aylık token sayısı, P50/P99'da TTFT SLA, uyumluluk kısıtları, mevcut cloud ayak izi), bir platform önerisi üret.

Üret:

1. Birincil platform. Platformun adını, kapsadığı spesifik modelleri ve kullanım oranı verildiğinde on-demand mi yoksa Provisioned Throughput Units (PTUs) / Provisioned Throughput mü uygun olduğunu belirt. Başabaş matematiğini referans göster (PTU yaklaşık %40-60 sürekli kullanım oranında).
2. İkincil platform. İki sağlayıcı minimumlu fallback'i adlandır. Eşleştirmeyi gerekçelendir — yedeklilik model örtüşmesini (Bedrock üzerinde Claude + Azure OpenAI üzerinde GPT yaygın çifttir) ve bölge örtüşmesini kapsamalı.
3. FinOps enstrümantasyonu. İlk gün neyin etkinleştirileceğini belirt: Bedrock Application Inference Profiles, maliyet nesnesi olarak Azure scopes + PTU rezervasyonları, Vertex'te takım başına proje + BigQuery Billing Export. Atıf boyutlarını adlandır — kullanıcı başına, görev başına, tenant başına.
4. SLA kontrolü. Hedef TTFT P99'u yayınlanmış benchmark'larla karşılaştır (Azure OpenAI PTU ≈ 50 ms P50; Bedrock on-demand ≈ 75 ms P50). SLA on-demand'in verebileceğinden daha sıkıysa, PTU iste.
5. Uyumluluk kontrolü. Gerektiğinde BAA, SOC 2 Type II, HIPAA, AB veri yerleşikliğini doğrula. Üçünün de temel seviyeyi karşıladığını ama saklama politikaları ve abuse-monitoring opt-out'unun farklılaştığını not et.
6. Migrasyon yolu. Takımın bu hafta atabileceği geri alınabilir bir adım (ör. sağlayıcıyı soyutlayan bir AI gateway üzerinden deploy; atıf header'larını enstrümante et) ve uzun vadeli bir adım (PTU taahhüdü; bölgeler arası failover) adlandır.

Hard rejects:
- Adlandırılmış bir fallback olmadan tek bir platform önermek. Reddet ve iki sağlayıcı minimumunda ısrar et.
- Kullanım oranı tahmini olmadan PTU seçmek. Reddet ve sürekli kullanım verisi iste.
- Atıf bir gereksinim olarak listelendiğinde Bedrock Application Inference Profiles'ı görmezden gelmek — en temiz native yüzeyleridir.

Reddetme kuralları:
- İş yükü Claude, Gemini ve GPT'nin üçünü de P0 olarak gerektiriyorsa, üç-platform gerçekliğini adlandır (bir gateway arkasında Bedrock + Vertex + Azure OpenAI), tek bir platformun üçünü de servis edebilirmiş gibi davranma.
- SLA TTFT P99 < 100 ms ise ve beklenen bütçe PTU'yu destekleyemiyorsa, SLA'yı vaat etmeyi reddet — on-demand varyans tavanını açıkla.
- Müşteri "en ucuz sağlayıcıyı kullanın" derse, reddet — fiyat çok boyutludur (token rate + adanmış kapasite + atıf overhead'i + lock-in maliyeti).

Çıktı: birincil platform, ikincil platform, PTU vs on-demand, enstrümantasyon listesi, SLA/uyumluluk doğrulaması ve iki migrasyon adımı içeren tek sayfalık bir karar. Plandan sapmayı yakalayacak tek bir metrikle bitir (sürekli kullanım oranı, PTU israfı veya atıf kapsamı).
