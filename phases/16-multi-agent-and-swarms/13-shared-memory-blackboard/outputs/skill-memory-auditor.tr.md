---
name: memory-auditor
description: Bir çoklu-agent sistemin paylaşımlı memory tasarımını provenance, versioning, verifier ayrımı ve projection şeması açısından denetle. Production öncesinde memory-poisoning maruziyetini işaretle.
version: 1.0.0
phase: 16
lesson: 13
tags: [multi-agent, shared-state, blackboard, memory-poisoning, provenance]
---

Bir çoklu-agent codebase ya da mimari dokümanı verildiğinde, paylaşımlı memory tasarımını denetle ve memory poisoning'e maruziyeti işaretle.

Üret:

1. **Topoloji.** Tam mesaj havuzu, topic-bölümlenmiş blackboard, agent başına yansıtılmış görünüm ya da hibrit mi? Veri yapısını adlandır (list, dict, pandas frame, vector store, SQL tablo). Steady state'te yazıcıların ve okuyucuların kabaca üst sınırını say.
2. **Provenance alanları.** Her yazımda, girdi şunları kaydediyor mu: writer id, timestamp, prompt hash veya prompt metni, tool-call trace, kaynak URI veya tool adı? Mevcut alanları ve eksik alanları listele.
3. **Update modeli.** Log append-only mi yoksa yazıcılar yerinde mi değiştiriyor? Mutation varsa, eşzamanlılık kontrol mekanizması nedir (lock, optimistic versioning, hiçbiri)? Düzeltmeler yerinde edit değil, supersession girdileri olmalı — bunu yapmayan tasarımı işaretle.
4. **Verifier ayrımı.** Bağımsız kaynak erişimine sahip read-only bir agent var mı? Ana havuza yazabiliyor mu (yazmamalı)? Çıktısı nereye gidiyor?
5. **Projection şeması.** Tasarım projeksiyonlar kullanıyorsa (LangGraph reducer'ları, blackboard topic'leri, rol-scoped görünümler), şema belgelenmiş mi? Yeni agent'lar tükettikleri projeksiyonu nasıl bildirir?
6. **Poisoning risk skoru.** Her eksende 1-5 arası skorla: [provenance bütünlüğü], [mutation yerine supersession], [verifier bağımsızlığı], [projection şeması netliği]. Herhangi bir eksende 3'ün altında skor alan sistem işaretlenir.

Sert ret durumları:

- Eksik bir verifier'ı işaretlemeyen herhangi bir denetim. Bağımsız kaynak erişimine sahip yazılamayan bir verifier, yük taşıyan önlemdir; bu olmadan diğer her önlem dekoratiftir.
- "Daha fazla test ekle" öneren denetimler. Testler memory poisoning'i yakalayamaz çünkü poisoning testleri geçen makul çıktılar üretir.
- Sadece içeriği hash'lemeyi tek provenance olarak öneren denetimler. Hash sana *ne* yazıldığını söyler, *kim* veya *nereden* yazdığını söylemez.

Reddetme kuralları:

- Codebase paylaşımlı state'i harici bir servise (Redis, Postgres, vector DB) inceleme tool'u olmadan gizliyorsa, production okuma erişimi olmadan denetimin tamamlanamayacağını belirt.
- Sistem 3'ten az agent içeriyorsa, memory poisoning riskinin düşük olduğunu ama provenance'ın hala ucuz bir sigorta olduğunu not düş.
- Sistem yerleşik state yönetimine sahip bir framework kullanıyorsa (LangGraph checkpointer, AutoGen havuzu), bunları yeniden türetmek yerine framework'ün garantilerini denetle.

Çıktı: iki sayfalık rapor. Tek cümlelik özetle başla ("Paylaşımlı state provenance ve verifier'sız tam mesaj havuzu — yüksek poisoning riski."), ardından yukarıdaki altı bölüm. Önceliklendirilmiş aksiyon listesiyle bitir: üç değişiklik, her biri [critical] [should] ya da [nice-to-have] etiketli, tahmini implementation süresiyle.
