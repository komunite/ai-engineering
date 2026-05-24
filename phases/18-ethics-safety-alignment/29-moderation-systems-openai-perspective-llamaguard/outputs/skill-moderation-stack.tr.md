---
name: moderation-stack
description: Bir production deployment için bir moderasyon yığını konfigürasyonu öner.
version: 1.0.0
phase: 18
lesson: 29
tags: [openai-moderation, perspective, llama-guard, layered-moderation, azure-content-safety]
---

Bir production deployment verildiğinde, üç katman boyunca bir moderasyon yığını konfigürasyonu öner.

Üret:

1. Input classifier. OpenAI Moderation, Llama Guard 3/4 veya Perspective API'den birini seç. Politika taksonomisiyle eşleştir. Multimodal deployment'lar için Llama Guard 4 veya OpenAI omni-moderation.
2. Output classifier. Input classifier ile aynı veya farklı. Eşikleri downstream risk modeline eşleştir.
3. Custom domain kuralları. Genel classifier'ların yakalayamayacağı domain-spesifik kuralları sayımla: finansal-tavsiye disclaimer'ları, tıbbi-tavsiye reddetmeleri, yasal-disclaimer örüntüleri.
4. Edge case'ler için judge. İnsan-eskalasyon yolunu belirt. Hard refusal'lar nihai; belirsiz vakalar SLA içinde insan incelemesine gider.
5. Migrasyon planı. Azure Content Moderator yığında ise, Şubat 2027 retirement'tan önce Azure AI Content Safety'ye migrasyonu planla.

Sert reddetmeler:
- Output moderasyonu olmayan herhangi bir deployment (yalnız input yeterli değildir).
- Düzenlenen yüzeylerde (finans, sağlık, hukuk) custom domain kuralları olmayan herhangi bir deployment.
- Modern chat uygulamaları için yalnızca pre-LLM-dönemi classifier'lara (Perspective) dayanan herhangi bir deployment.

Reddetme kuralları:
- Kullanıcı tek bir en iyi classifier isterse, reddet — classifier seçimi politika-taksonomi-spesifiktir.
- Kullanıcı eşik değerleri isterse, tek sayıları reddet — eşikler risk toleransına ve downstream etkiye bağlıdır.

Çıktı: beş bölümü dolduran, her katmandaki classifier'ı adlandıran ve migrasyon yükümlülüklerini işaretleyen tek sayfalık bir öneri. OpenAI Moderation dokümanlarını ve Llama Guard 3/4 referanslarını birer kez alıntıla.
