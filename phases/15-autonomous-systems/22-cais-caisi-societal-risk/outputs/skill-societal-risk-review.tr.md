---
name: societal-risk-review
description: CAIS dört-risk framework'ü ve CAISI / SB-53 regulatory bağlamı kullanarak bir deployment'ı societal-scale-risk duruşu için incele.
version: 1.0.0
phase: 15
lesson: 22
tags: [cais, caisi, four-risk-framework, organizational-risk, sb-53, societal-risk]
---

Önerilen veya çalışan bir AI deployment'ı verildiğinde, deployment'ı CAIS dört-risk framework'üne karşı etiketleyen, organizational-risk alt-kollarını envanterleyen ve regulatory yüzeyi adlandıran bir societal-scale-risk incelemesi üret.

Üret:

1. **Dört-risk etiketleme.** Dört kategorinin her biri için (malicious use, AI races, organizational risks, rogue AIs), deployment'ın ona dokunup dokunmadığını ve nasıl dokunduğunu belirt. Bir deployment birden fazla kategoriye dokunabilir; "uygulanmaz" bir cümlede gerekçelendirilmelidir.
2. **Organizational-risk envanteri.** Deployment'ı dört alt-kola karşı puanla: safety culture, denetim titizliği, multi-layered savunmalar, bilgi güvenliği. "Eksik" puanlanan herhangi bir kol işaretli bir gap'tir.
3. **Regulatory yüzey.** Geçerli regulatory framework'leri adlandır: EU AI Act (EU'da veya EU kullanıcılarına hizmet ediyorsa), California SB-53 (imzalandı ve geçerliyse), CAISI gönüllü anlaşmaları (lab imzaladıysa). Uyumluluk bir deployment kapısıdır, bir nice-to-have değildir.
4. **Harici-değerlendirme duruşu.** Deployment'ın veya base modelinin geçirdiği harici değerlendirmeleri adlandır (METR, CAISI, Apollo, Gray Swan vb.). Harici değerlendirme yokluğu uzun-horizon otonom deployment'lar için işaretli bir gap'tir.
5. **Yapısal-güç maruziyeti.** Kuruluşun ne kadar competitive-deployment baskısı altında olduğunu ve bunun organizational-risk kollarına karşı nasıl ödün verdiğini tahmin et. Ağır race baskısı altındaki ekipler önce denetimi düşürür; bu CAIS bulgusudur.

Sert reddetmeler:
- Hardcoded-yasak katmanı olmadan harmful-capability kategorilerine dokunan deployment'lar (Lesson 17).
- Bağımsız denetim olmadan competitive-race koşullarında deployment'lar.
- Harici capability değerlendirmesi olmayan uzun-horizon otonom deployment'lar.
- Article 14 HITL'i olmayan EU deployment'ları (Lesson 15).
- SB-53 imzalandıysa incident-reporting süreci olmayan California deployment'ları.

Reddetme kuralları:
- Kullanıcı base model için harici evaluator'ı adlandıramazsa, reddet ve önce tanımlama iste. Yalnızca self-evaluation yetersizdir.
- Kullanıcı "bir scaling policy'miz var"ı catastrophic-risk düzenlemesiyle uyumluluk olarak ele alıyorsa, reddet ve spesifik regulatory-yüzey haritalaması iste.
- Kullanıcı denetim olmadan race baskısı altında deploy etmeyi öneriyorsa, reddet ve organizational risk üzerine CAIS bulgusunu adlandır.

Çıktı formatı:

Şunları içeren bir societal-risk incelemesi döndür:
- **Dört-risk satır tablosu** (kategori, dokunuldu y/n, niteliği)
- **Organizational-risk scorecard'ı** (safety culture / denetim / savunmalar / infosec)
- **Regulatory yüzey** (geçerli framework'ler uyumluluk durumuyla)
- **Harici-değerlendirme duruşu** (evaluator, kapsam, cadence)
- **Yapısal-güç maruziyeti** (low / medium / high, gerekçeyle)
- **Deployment hazırlığı** (production / staging / yalnızca araştırma)
