---
name: reflexion-buffer
description: TTL, dedup ve scope kapsamı ile verbal RL için bir reflection episodic-memory buffer'ı yönet.
version: 1.0.0
phase: 14
lesson: 03
tags: [reflexion, episodic-memory, self-healing, verbal-rl, sleep-time]
---

Bir görev sınıfı (agent çalıştırmasının tekrarlayan türü — örn. "bir fonksiyonu refactor et", "bir destek bileti kapat") verildiğinde, bir reflection episodic-memory buffer'ı yönet. Her reflection bir failure mode ve düzeltici içgörüyü doğal dilde kaydeder. Buffer, aynı görev sınıfının bir sonraki denemesine prepend edilir.

Üret:

1. Reflection yakalama. Bir deneme evaluator skoru eşiğin altında bittiğinde, "X'i yapamadım çünkü Y; bir sonraki sefer Z." şeklinde tek satırlık bir reflection yay. Tekrar üretilebilir olmadıkça external başarısızlıklardaki (network, upstream 500'ler) reflection'ları at.
2. TTL ve dedup. Reflection'lar varsayılan olarak N deneme sonra süresi doluyor (10 önerilir). Tam duplikatlar birleşir. Yakın duplikatlar (küçük bir embedding modelinde >0.9 cosine veya >= %80 ortak substring) yalnızca en güncel olanı tutar.
3. Scope politikası. Üç scope: task-class (görev adı başına), user (aynı kullanıcı için görevler arası), agent (tüm kullanıcılar arası). Varsayılan task-class. Yalnızca reflection kullanıcıya özgü tercihlere atıfta bulunuyorsa user scope'a yükselt; asla otomatik olarak agent scope'a yükseltme.
4. Sıkıştırma (compaction). Buffer bütçeyi aştığında, sleep-time compaction çalıştır: yakın duplikatları kümelendir, özetle, birleştir. Compaction hot path'in dışında çalışır — birincil agent'in yanıtını geciktirme.
5. Prompt entegrasyonu. "Önceki denemelerden öğrendiklerim" başlıklı tek bir blok yay, madde işaretli liste ile. Prompt'ta 6 maddeyle sınırla; taşan, ayrı bir özet maddesine gider ("... ve timeout'lar hakkında 4 daha eski reflection").

Sert ret durumları:

- Reflection'ları "bir sonraki sefer daha dikkatli ol" şeklinde yazmak. Bu uygulanabilir değil. Reflector'ı somut bir bir-sonraki-sefer talimatını zorlayan bir prompt ile yeniden çalıştır.
- Reflection'ları deneme sayısı yerine duvar saati zamanına göre sona erdirmek. TTL, offline-replayable çalıştırmalar için time-scoped değil, trial-scoped olmalı.
- Secret'lara (API anahtarları, token'lar, PII) atıfta bulunan reflection'ları saklamak. Buffer'a commit etmeden önce spesifik bir "contains secret"-sınıfı hata ile reddet.

Reddetme kuralları:

- Bağlı bir evaluator yoksa, reddet ve Lesson 05'i (Self-Refine/CRITIC) öner — reflection bir sinyal gerektirir, içgüdü değil.
- Görev sınıfı tek seferlikse (asla tekrarlanmaz), reddet; episodic bellek asla tekrarlanmayan bir görev için hiçbir şey yapmaz.

Çıktı: yapılandırılmış bir buffer dosyası (reflection objeleri içeren JSON: trial id, task class, scope, text, created_at, ttl_remaining), bir sonraki deneme için bir prompt bloğu ve yakında süresi dolacak girdileri listeleyen bir "stale reflections" raporu.

"Bundan sonra ne okumalı" notu ile bitir: buffer sürekli sınırına çarpıyorsa Lesson 06 (context compression), sıkıştırmayı hot path'ten taşımak için Lesson 08 (Letta sleep-time compute).
