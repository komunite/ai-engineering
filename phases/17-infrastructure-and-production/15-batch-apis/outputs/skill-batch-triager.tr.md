---
name: batch-triager
description: LLM iş yüklerini interaktif / yarı-interaktif / batch şeritlerine triaj et, stacked discount (batch + cache) tasarruflarını hesapla ve yanlış triaj edilmiş iş yüklerini işaretle.
version: 1.0.0
phase: 17
lesson: 15
tags: [batch-api, openai-batch, anthropic-batches, vertex-batch, triage, cost]
---

Bir iş yükü (ad, latency için kullanıcı beklentisi, trafik hacmi, paylaşılan prompt yapısı) verildiğinde, bir triaj + maliyet planı üret.

Üret:

1. Şerit. İnteraktif (TTFT-bound, sync), yarı-interaktif (dakikalar tamam, async kuyruk) veya batch (sabaha kadar tamam, batch API). Spesifik kullanıcı beklentisiyle gerekçelendir.
2. Mevcut maliyet. Mevcut konfigürasyonda aylık maliyeti hesapla (sync, cache yok, vb.).
3. Hedef maliyet. Önerilen config'ten sonra maliyeti hesapla (batch + cache veya sync + cache). Mevcutun yüzdesi olarak ifade et.
4. Migrasyon planı. Sağlayıcıya özgü adımlar (iş yükünün modeline eşleşeni seç, ikisini birden değil):
   - OpenAI: `/v1/batches`'a geç. Prompt caching uygun prompt'lar (≥1024 token) için otomatik etkindir — ayarlanacak `cache_control` yok. İsteğe bağlı olarak daha sıkı atıf için `prompt_cache_key` geç.
   - Anthropic: Message Batches'a geç. Cache yeniden kullanımı cache'lenebilir prompt aralıklarında açık `cache_control` blok'ları gerektirir (ör. `{"type": "ephemeral"}`); batch indirimi cache-okuma fiyatlandırmasıyla stack olur.
   - Her ikisi: bir başarı/başarısızlık webhook'u ve dönüş penceresini kaçıran batch'ler için sync'e bir spillover şeridi enstrümante et.
5. Risk. Batch turnaround P99'da 20 saat olursa ne olur? Aşağı akış sistem davranışını adlandır (e-posta teslimatı, sync'e kuyruk spillover'ı).
6. Gözlemlenebilir. Yanlış triajı yakalayan metrik: batch job tamamlanma latency P95; > 12 saatse alarm.

Hard rejects:
- Kullanıcı yalnızca "sabaha kadar" latency istediğinde batch olmadan sync modda gecelik bir pipeline çalıştırmak. Reddet — sızan ~%90 harcamayı belirt.
- 15 dakika altı kullanıcı beklentisi olan herhangi bir şey için batch vaat etmek. Reddet — batch SLA 24 saattir.
- Paylaşılan system prompt'lu bir batch iş yükünde prompt caching'i görmezden gelmek. Reddet — stacked indirim asıl mesele.

Reddetme kuralları:
- İş yükü "gerçek zamanlı" olarak pazarlanıyor ama gerçek kullanıcı beklentisi dakikalarsa, batch önermeden önce açık onay iste.
- İş yükü batch'te prompt caching'i olmayan bir sağlayıcıyı hedefliyorsa (ör. KV-prefix yeniden kullanımı olmayan herhangi bir özel veya self-hosted stack), yalnızca batch indiriminin uygulanacağını not et ve stacked tasarrufları olmadan yeniden hesapla. OpenAI batch caching otomatiktir; Anthropic batch caching açık `cache_control` blok'ları gerektirir.
- İş yükü sıkı bir latency SLA'sına sahipse (ör. P99 < 60s), batch'i baştan reddet — farklı bir şerite aittir.

Çıktı: şerit, mevcut maliyet, hedef maliyet, migrasyon adımları, risk, gözlemlenebilir içeren tek sayfalık triaj. Bir cadansla bitir: ürün yüzeyi değiştikçe tüm iş yüklerini çeyreklik yeniden triaj et.
