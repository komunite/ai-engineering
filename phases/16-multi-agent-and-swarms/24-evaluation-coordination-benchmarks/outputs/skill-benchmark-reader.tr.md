---
name: benchmark-reader
description: Bir çoklu-agent benchmark iddiasını şüpheyle oku. İddiayı benchmark seçimi, kontaminasyon, baseline'lar, istatistiksel anlamlılık, görev çeşitliliği ve maliyet ifşası üzerinden notla.
version: 1.0.0
phase: 16
lesson: 24
tags: [multi-agent, benchmarks, evaluation, SWE-bench, MARBLE]
---

Yayımlanmış veya dahili bir çoklu-agent benchmark performans iddiası verildiğinde, iddiayı notla ve uyarıları yüzeye çıkar.

Üret:

1. **Benchmark + split tanımlaması.** Hangi benchmark (MARBLE, COMMA, MedAgentBoard, AgentArch, SWE-bench Pro, SWE-bench Verified, custom)? Hangi split (tam, held-out, kontaminasyon-temizlenmiş)? Bilinmeyen split'ler diskalifiyedir.
2. **Kontaminasyon durumu.** Benchmark, test edilen model için post-training-cutoff mu? Benchmark eğitim cutoff'undan önceyse, kontaminasyon riski için işaretle ve iddiayı indirim uygula.
3. **Baseline kalitesi.** Vs tek-LLM, vs random, vs önceki çoklu-agent çalışması. Vs ayarlanmamış-aynı-sistem sayılmaz; bu bir ablation'dır, baseline değildir.
4. **İstatistiksel anlamlılık.** N deneme, güven aralığı veya standart hata, p-değeri veya eşdeğeri. N < 50 denemede istatistik olmayan iddialar yetersiz desteklidir.
5. **Görev çeşitliliği.** Bir görev, bir alan ya da çok mu? Tek-görev iddiaları genelleştirmeyi ima etmez.
6. **Maliyet ifşası.** Görev başına token, görev başına wall-clock, görev başına dolar maliyeti. 20x maliyetle %90 çözüm bir iş kararıdır; maliyet olmadan iddia eksiktir.
7. **Harf notu + tek cümlelik karar.**

   - **A:** Altı kontrolün hepsi geçer; iddia muhtemelen sağlamdır.
   - **B:** Bir zayıflık; iddia not edilen uyarılarla makuldür.
   - **C:** İki zayıflık; iddia ipucu verir ama replikasyona ihtiyaç duyar.
   - **D:** Üç veya daha fazla zayıflık; iddia kanıt değildir.
   - **F:** Diskalifiye edici problem (ifşa edilmemiş split'te kontaminasyon, istatistik yok, baseline yok).

Sert ret durumları:

- Verified vs Pro belirtmeden "SWE-bench"i alıntılayan iddialar. 40+ puanlık fark bu belirsiz raporlamayı kabul edilemez kılar.
- Baseline karşılaştırması olmadan iddialar. "Sistemimiz %X yapıyor" bir sayıdır, sonuç değil.
- Çoklu-agent sistemler için 20 denemeden azına dayanan iddialar. Varyans çok yüksek.
- Çoklu-agent sistemler için maliyet-ifşasız iddialar. Koordinasyon vergisi materyaldir.

Reddetme kuralları:

- Benchmark halka açık değilse ve kullanıcının dahili denetim izi yoksa, not atanamaz. Değerlendirme artifact'larının yayımlanmasını öner.
- İddia şu anda peer review altında olan bir paperdan ise (arXiv preprint, gönderilmemiş), replikasyona kadar önlem olarak bir harf notu düşür.
- Kullanıcı denetim isteyen iddia sahibi ise, denetimi düz çalıştır; iddia henüz yayın için hazır değilse işaretle.

Çıktı: bir sayfalık not kartı. Tek cümlelik özetle başla ("Not: C — iyi benchmark seçimi, yeterli baseline'lar, ama kontaminasyon kontrolü yok ve maliyet ifşası yok."), ardından yukarıdaki yedi bölüm. "Notu yükseltmek için ne düzeltilmeli" şeklinde önceliklendirilmiş listeyle bitir.
