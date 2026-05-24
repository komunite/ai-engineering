---
name: inference-platform-picker
description: İş yükü, SLA, bütçe ve operasyonel kısıtlar verildiğinde bir çıkarım platformu (Fireworks, Together, Baseten, Modal, Replicate, Anyscale veya özel silikon) seç. Token başına, dakika başına ve tahmin başına fiyatlandırmayı normalize et.
version: 1.0.0
phase: 17
lesson: 02
tags: [inference, fireworks, together, baseten, modal, replicate, anyscale, economics]
---

Bir iş yükü profili verildiğinde (model, token/gün, sürekli kullanım oranı, TTFT SLA, burst katsayısı, uyumluluk, Python vs karma stack), bir platform önerisi üret.

Üret:

1. Birincil platform. Platformu ve spesifik fiyatlandırma katmanını adlandır (serverless vs dedicated vs batch). Eşleşen iş yükü karakteristikleriyle gerekçelendir — ör. "Fireworks serverless çünkü SLA TTFT < 500 ms ve trafik bursty."
2. Etkin maliyet. Seçilen fiyatlandırma modelini $/M çıkış token'a normalize et. En az iki alternatifle karşılaştır. Dakika başının token başını ne zaman geçtiğini (yaklaşık %30 sürekli kullanım üzerinde) veya tam tersini belirt.
3. Cold-start planı. Serverless seçimler için (Fireworks, Modal, Replicate), beklenen cold-start latency'sini ve bir azaltma yöntemini belirt (pre-warming, min_workers=1, live-migration). Dedicated seçimler için (Baseten, Anyscale), bu bölümü atla ama trade-off'u not et.
4. İkinci sırada. İkinci platformu ve hangi koşulda geçiş yapacağını açıkça adlandır (ör. "HIPAA + dedicated GPU gerektiren bir enterprise anlaşma kapatırsak Baseten'e geç").
5. Gateway katmanı. Ürünü sağlayıcı çalkantısından izole etmek için platformun önüne bir AI gateway (LiteLLM, Portkey, Kong AI Gateway) konulup konulmayacağını öner. Varsayılan: evet, ölçek 500 RPS altında değilse.

Hard rejects:
- Normalize etmeden dakika başı ile token başını karşılaştırmak. Reddet ve etkin $/M token'da ısrar et.
- Yayınlanmış benchmark'lara karşı TTFT SLA'sını doğrulamadan "en hızlı" olduğu için Fireworks seçmek.
- Latency-bound olmayan herhangi bir iş yükü için özel silikon (Groq, Cerebras, SambaNova) önermek. Bunlar premium fiyatlıdır ve sadece interaktif SLA'larda kendini ödetir.

Reddetme kuralları:
- İş yükü regüle bir framework gerektiriyorsa (SOC 2 Type II, HIPAA) ve müşteri Modal veya Replicate seçtiyse, reddet — hiçbiri Baseten veya Anyscale ile aynı enterprise ayak izine sahip değil. Baseten öner.
- Beklenen trafik 100k token/gün altındaysa, dakika başı önermeyi reddet (Baseten, Modal, Anyscale). Ekonomisi tutmaz — bir marketplace (OpenRouter, DeepInfra) veya managed hyperscaler varsayılan olsun.
- Müşteri "en ucuzu" isterse, reddet — çok boyutlu maliyet fonksiyonunu adlandır (token rate + cold start + atıf + gateway + DX).

Çıktı: birincil platformu, etkin maliyeti, cold-start planını, ikinci sırayı ve gateway tutumunu adlandıran tek sayfalık öneri. Yanlış seçimi ortaya çıkaracak tek bir metrikle bitir (cold-start P99, token başına rate veya kullanım oranı sapması).
