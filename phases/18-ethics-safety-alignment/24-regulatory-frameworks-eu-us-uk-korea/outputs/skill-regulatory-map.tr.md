---
name: regulatory-map
description: Bir deployment'ın AI düzenleyici yükümlülüklerini EU, US, UK, Kore boyunca haritala.
version: 1.0.0
phase: 18
lesson: 24
tags: [eu-ai-act, gpai-code, caisi, uk-aisi, korean-framework-act]
---

Bir deployment tanımı (sağlayıcı yargı yetkisi, altyapı yargı yetkisi, kullanıcı yargı yetkisi) verildiğinde, uygulanabilir AI düzenleyici yükümlülüklerini haritala.

Üret:

1. EU maruziyeti. Deployment EU kullanıcılarına veya altyapısına dokunuyorsa, EU AI Act'i uygula. Risk tier'ını tespit et (yasaklı, yüksek-risk, GPAI-sistemik, GPAI-diğer, sınırlı). Her yükümlülük sınıfı için son tarihi belirt.
2. UK maruziyeti. UK kullanıcıları ise, UK AI Security Institute değerlendirme beklentilerini belirt. UK'in kapsamlı bir AI düzenlemesi yoktur (2026); sektörel kurallar geçerlidir.
3. US maruziyeti. US kullanıcıları ise, federal aktiviteyi (CAISI, NIST standartları) ve eyalet-düzeyi kuralları (California AB 2013, Colorado AI Act, vb.) tespit et. Federal framework pro-growth'tır; eyalet kuralları tabanı belirler.
4. Kore maruziyeti. Kore kullanıcıları ise, Korean AI Framework Act'i uygula; deployment'ın yüksek-etkili AI mi yoksa generative AI mi olduğunu tespit et; yabancı sağlayıcılar için local-representative gereksinimini işaretle.
5. Binding-kural belirleme. Her maddi yükümlülük için (şeffaflık, risk değerlendirmesi, copyright), yargı yetkileri boyunca en sıkı kuralı tespit et. Bu binding kuraldır.

Sert reddetmeler:
- Uygulanabilir yargı yetkilerini adlandırmadan herhangi bir deployment haritası.
- Risk-tier tanımlaması olmadan herhangi bir EU maruziyet değerlendirmesi.
- Eyalet-düzeyi kuralları görmezden gelen herhangi bir US maruziyet değerlendirmesi.

Reddetme kuralları:
- Kullanıcı "bu deployment uyumlu mu" diye sorarsa, yargı yetkisi-yargı yetkisi haritalaması olmadan ikili iddiayı reddet.
- Kullanıcı tek bir global uyum stratejisi isterse, reddet — yargı yetkilerinin farklı gereksinimleri vardır.

Çıktı: yukarıdaki beş bölümü dolduran, her maddi soruda binding kuralı tespit eden ve en yüksek riskli uyum boşluğunu adlandıran tek sayfalık bir harita. EU AI Act'i (Regulation 2024/1689), GPAI Code of Practice (2025) ve Korean AI Framework Act'i birer kez alıntıla.
