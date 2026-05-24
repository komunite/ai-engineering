---
name: parallel-inference-router
description: Bir reasoning iş yükünü voting, tree-of-thought, multi-agent, Hogwild! ve speculative decoding stratejileri arasında yönlendir.
version: 1.0.0
phase: 10
lesson: 22
tags: [parallel-inference, hogwild, speculative-decoding, tree-of-thought, multi-agent, reasoning]
---

Bir reasoning iş yükü profili (görev başına token bütçesi, görev paralellik özellikleri, model ailesi, deployment hedefi, latency bütçesi) verildiğinde, bir paralel-inference stratejisi veya kombinasyonu öner.

Şunları üret:

1. Görev sınıflandırması. Uzun reasoning (5k+ token), orta chain-of-thought (1k-5k), kısa chat (1k altı) veya classification. İlk-pass kararını yönlendirir.
2. Paralellik ekseni. Dizi-içi (speculative decoding) vs diziler-arası (voting, Hogwild!, multi-agent). Çoğu iş yükü önce dizi-içi ekseninden faydalanır.
3. Strateji önerisi. Şunlar arasından seç: yalnızca speculative decoding (100 token üstündeki herhangi bir iş yükü için güvenli varsayılan), speculative + Hogwild! (paralelleştirilebilir yapılı uzun reasoning), tree-of-thought (açık branch-and-prune problemleri), multi-agent (rol-özelleşmesi problemleri), voting ensemble (yüksek-bahisli classification).
4. Parametre ayarları. Speculative decoding için: draft ailesi (EAGLE-3 varsayılan) ve `N` (Faz 10 · 15 skill). Hogwild! için: worker sayısı N (2 ila 4, nadiren daha fazla), koordinasyon prompt template'i, tek-node deployment doğrulaması.
5. Birleşik speedup tahmini. Speculative decoding'i Hogwild! ile birleştiriyorsan, multiplicative speedup'ı raporla (tipik aralık: 3x spec * 1.5-2x Hogwild! = 4.5-6x).

Sert redler:
- 2000 token altındaki herhangi bir iş yükü için Hogwild!. Koordinasyon yükü baskın olur.
- Reasoning olmayan modellerde Hogwild! (emergent koordinasyon yok).
- Doğal rol ayrışması olmayan problemler için multi-agent framework.
- Açık branch-and-prune mantığı olmadan tree-of-thought (strateji aksi takdirde lineer CoT'ye indirgenir).
- Node'lar arası Hogwild! çalıştırmak (cross-node cache senkronizasyonu çok yavaş).

Reddetme kuralları:
- İş yükü deneysel araştırmaysa, üretim bahsi yerine deney olarak Hogwild! öner. Speedup'lar göreve bağlı ve Nisan 2026 itibarıyla gerçek dünya deployment'ı nadir.
- Kullanıcı garantili speedup isterse, reddet ve yalnızca speculative decoding'in güçlü-garanti özelliğine sahip olduğunu (çıktı dağılımı korunur) açıkla. Hogwild! ampirik.
- Kullanıcının sınırlı VRAM'i varsa, Hogwild! N>2'yi reddet — her worker cache paylaşılsa bile kendi aktivasyon belleğine ihtiyaç duyar.

Çıktı: görev sınıflandırması, paralellik ekseni, strateji, parametreler ve birleşik speedup tahminini listeleyen bir sayfalık öneri. Hogwild! ilk 100 üretim isteğinde karşılığını vermezse yalnızca speculative decoding'e geri dönmeyi haklı çıkaracak spesifik latency veya doğruluk metriğini adlandıran "rollback tetikleyici" paragrafıyla bitir.
