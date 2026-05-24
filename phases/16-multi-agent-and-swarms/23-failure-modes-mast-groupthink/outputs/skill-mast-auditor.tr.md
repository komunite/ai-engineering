---
name: mast-auditor
description: Bir çoklu-agent sistem üzerinde MAST tarzı hata-modu denetimi çalıştır. Yürütme-trace hatalarını Specification / Coordination / Verification ve Groupthink ailelerine kategorize et; önlemleri beklenen hata azaltımına göre sırala.
version: 1.0.0
phase: 16
lesson: 23
tags: [multi-agent, failure-modes, MAST, groupthink, circuit-breaker, audit]
---

Bir çoklu-agent sistem ve örneklenmiş yürütme trace'leri verildiğinde, hata-modu denetimi çalıştır.

Üret:

1. **Örneklem inşası.** Production'dan en az 200 trace, görev türleri ve zaman pencerelerinde üniform örneklenmiş. Örnekleme yöntemini ve önyargı risklerini belgele.
2. **Sınıflandırma geçişi.** Her trace için `success | failure` işaretle. Hatalar için bir MAST kategorisi (spec / coord / verify) ata ve uygunsa bir veya daha fazla Groupthink aile etiketi (monoculture / conformity / tom / mixed-motive / cascade) ata.
3. **Dağılım tablosu.** MAST kategorisi ve Groupthink etiketine göre sayımlar ve yüzdeler. Cemri 2025'in referans dağılımıyla karşılaştır (41.77 / 36.94 / 21.30). Referanstan ağır şekilde sapan sistemler genellikle belirli bir zayıf katmana sahiptir.
4. **En sık hata pattern'ları.** En sık 3 spesifik pattern'ı belirle (ör. "iki agent de review yapıyor"). Tekrar üretme adımlarını belgele.
5. **Önlem sıralaması.** Her en sık pattern için, standart kütüphaneden bir önlem öner: açık rol sözleşmeleri, versiyonlu paylaşımlı state, bağımsız verifier, circuit breaker, detection-diagnosis-validation (STRATUS) üçlüsü. Pattern'in sıklığı verildiğinde beklenen hata azaltımına göre sırala.
6. **Sessiz hata riski.** Kaç hata makul-ama-yanlış çıktılar üretir vs gürültülü hatalar? Sessiz oran doğrulama-katmanı yatırımını yönlendirir.
7. **Yavaş-hata proxy'leri.** Gürültülü bir hataya dönüşmeden önce drift'i yüzeye çıkaracak 2-3 canlı metrik öner: agreement rate, retry-rate, output-length dağılımı, agent-arası edit distance.

Sert ret durumları:

- Rastgele ya da stratified örneklem olmadan denetimler. Elle seçilmiş hatalar dramatik vakaları aşırı temsil eder ve yavaş-hata drift'ini kaçırır.
- Baseline ölçümü olmadan önlem önerileri. Mevcut hata oranı bilinmiyorsa "verifier ekle" hiçbir şey ifade etmez.
- MAST-bilinmeyen olayları yok saymak. Bir trace bir kategoriye uymuyorsa, taksonomi eksiktir; bir kategori zorlamak yerine bir uzantı öner.
- Operasyonel yavaş-hata izleme olmadan üç aylık denetimin yeterli olduğunu iddia etmek. Üç aylık, denetimler arası drift'i kaçırır.

Reddetme kuralları:

- Trace'lerde agent başına atıf yoksa (kim ne yazdı, kim ne okudu), denetim koordinasyon hatalarını rol çatışmalarından ayırt edemez. Yeniden denetimden önce yapılandırılmış agent başına loglama eklenmesini öner.
- Sistemin toplam 50'den az başarısız trace'i varsa, örneklem dağılım tahminleri üretmek için çok küçük. Daha uzun gözlem penceresi öner.
- Trace'ler PII içeriyorsa, analizden önce maskele.

Çıktı: üç sayfalık rapor. Tek cümlelik özetle başla ("%41 spec hatası, %12 koordinasyon, %39 doğrulama boşluğu, %8 bilinmeyen; en sık pattern dual-reviewer çatışması; en yüksek ROI önlemi açık rol sözleşmeleri."), ardından yukarıdaki yedi bölüm. Önceliklendirilmiş aksiyon listesiyle bitir: üç önlem, tahmini implementation maliyeti ve beklenen hata-oranı azaltımı ile.
