---
name: memory-blocks
description: Kritik yolun dışında bir sleep-time consolidation agent'ı ile Letta-şekilli üç katmanlı bellek sistemi (core block'lar, recall, archival) üret.
version: 1.0.0
phase: 14
lesson: 08
tags: [memory, letta, blocks, sleep-time, consolidation]
---

Bir hedef runtime, bir birincil model ve (muhtemelen daha güçlü) bir sleep-time model verildiğinde, açık block tipleri ve async consolidation ile üç katmanlı bir bellek sistemi üret.

Üret:

1. `label`, `value`, `limit`, `description`, `version`, `history` içeren `Block` tipi. Her write version'ı artırır ve eski değeri kaydeder. `near_limit(threshold=0.8)` sun.
2. En az üç varsayılan block'a sahip bir `BlockStore`: `human` (kullanıcı hakkında olgular), `persona` (agent self-concept) ve `task` (mevcut scope). Kullanıcı tanımlı block'lara izin ver.
3. Bir `Recall` store — session'a göre sayfalanmış tur logu. Her turu otomatik yaz. Kuyruk sınırda evict olur ama geri alınabilir kalır.
4. Bir `Archival` store — en az iki backend (vector, KV). Insert record id döndürür. Çelişki olduğunda sil yerine invalidate et.
5. Turları işleyen ve yalnızca ham write'lar üreten bir `PrimaryAgent`. Kritik yolda özet çıkarma yok.
6. Turlar arasında çalışan bir `SleepTimeAgent`: eşiğin üstündeki block'ları özetle, çelişen archival kayıtlarını invalidate et, `learned_context`'i paylaşılan block'lara yaz.

Sert ret durumları:

- Doğrudan lookup hariç, kullanıcı yüzlü tur sırasında senkron çalışan herhangi bir memory operasyonu. Özet çıkarma, consolidation, invalidation sleep-time pas'ına aittir.
- Çelişki olduğunda archival kayıtlarını silmek. History denetlenebilir kalsın diye invalidate et.
- Persona veya Safety block'una review adımı olmadan yazmak. Bu block'lar davranışı global olarak şekillendirir; sessiz write'lar bug'ları maskeler.

Reddetme kuralları:

- Runtime block'ları session'lar arasında persist edemiyorsa, "memory" olarak tanımlanan bir ürün göndermeyi reddet. İddiayı düşür.
- Sleep-time agent'in trace çıktısı yoksa, reddet. Sessiz consolidation bir hata ayıklama ölü bölgesidir.
- Kullanıcı "invalidation yok, her zaman en son write'a güven" isterse, tarihsel iddiaların önemli olduğu herhangi bir alan için reddet (compliance, tıbbi, hukuki).

Çıktı: bileşen başına bir dosya artı varsayılan block'ları, sleep-time cadence'ını ve çelişki çözüm politikasını isimlendiren bir `README.md`. "Bundan sonra ne okumalı" notu ile bitir: agent bellek üzerinde graph reasoning gerektiriyorsa Lesson 09, ürün memory operasyonlarında OTel span'leri gerektiriyorsa Lesson 23.
