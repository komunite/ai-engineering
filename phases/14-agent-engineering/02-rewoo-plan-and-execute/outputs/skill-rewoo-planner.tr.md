---
name: rewoo-planner
description: Bir kullanıcı isteği ve tool kataloğundan doğrulanmış bir ReWOO plan DAG'ı üret.
version: 1.0.0
phase: 14
lesson: 02
tags: [rewoo, plan-and-execute, planning, dag, distillation]
---

Bir kullanıcı isteği ve bir tool kataloğu (isim, input schema, açıklama) verildiğinde, bir ReWOO planı üret: tool çağrıları ve kanıt referansları (`#E1`, `#E2`, ...) içeren bir adım DAG'ı. Planı bir executor'a vermeden önce doğrula.

Üret:

1. Bir plan DAG'ı. Her node id'ye (`E1`, `E2`, ...), tool ismine, argüman dict'ine (string'ler `#E<k>` referansları içerebilir) ve opsiyonel `parallel_group` etiketine sahip.
2. Doğrulama çıktısı. Topolojik sıralama ile döngüsüzlük kontrolü; referans çözümleme kontrolü (her `#E<k>` için önceki bir üretici var); tool varlık kontrolü (her tool ismi katalogda var); arg schema kontrolü (her argüman tool'un input schema'sıyla eşleşir).
3. Paralellik ipucu. Her topolojik seviye için, eşzamanlı çalışabilecek node'ları listele.
4. Planner/solver ayrım önerisi. Plan 3 adımdan azsa, ReAct öner. Plan sınırsız döngü gerektiriyorsa (her adımda yeniden planlama), replanner ile Plan-and-Execute öner. Plan 30 adımı aşıyorsa veya web/mobile'ı hedefliyorsa, sentetik plan verisi ile Plan-and-Act öner.

Sert ret durumları:

- Döngülü planlar. ReWOO bir DAG varsayar; döngüler ReAct veya LATS konusudur.
- Topolojik sırada `k` henüz var olmayan `#E<k>` referansları olan planlar. Başarısız olan spesifik kenarı belirt.
- Katalogda olmayan tool'ları çağıran planlar. Plan çalışsın diye tool uydurma.
- Bir referansın argüman tipinin tool'un schema'sıyla eşleşmediği planlar (örn. `#E1` bir string yerine koyuyor ama tool int bekliyor).

Reddetme kuralları:

- Görev açık uçlu keşifse (hangi tool'ların gerekli olduğu, hangi adımların gerektiği bilinmiyor), reddet ve ReAct veya LATS (Lesson 04) öner.
- Tool kataloğunda gating onay tool'u olmadan destructive tool'lar varsa, reddet ve Lesson 09'a (izinler, sandboxing) yönlendir.

Çıktı: yapılandırılmış bir plan (JSON veya YAML), bir doğrulama raporu, bir paralellik haritası ve executor'a (ReWOO Worker), replanner'a (Plan-and-Execute) veya daha büyük bir trajectory-sampling döngüsüne (Plan-and-Act) yönlendiren bir takip eylemi.

"Bundan sonra ne okumalı" notu ile bitir: görev sınıfı daha önce denenmişse Lesson 03 (Reflexion), plan aramadan fayda görecekse Lesson 04 (LATS).
