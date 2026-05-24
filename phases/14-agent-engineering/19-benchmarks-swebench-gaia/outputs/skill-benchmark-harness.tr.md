---
name: benchmark-harness
description: FAIL_TO_PASS / PASS_TO_PASS gate'leri, kontaminasyon kontrolleri ve step-count metrikleri ile bir kod tabanı için SWE-bench tarzı bir harness kur.
version: 1.0.0
phase: 14
lesson: 19
tags: [swe-bench, gaia, agentbench, harness, evaluation]
---

Bir kod tabanı ve (bug, fix) çiftleri listesi verildiğinde, gerçek unit test'ler üzerinde gate olan ve operasyonel metrikleri kaydeden bir benchmark harness'ı kur.

Üret:

1. Görev başına tanım: `(tid, description, state_before, fail_to_pass_tests, pass_to_pass_tests, solution)`.
2. Agent'in patch'ini uygulayan, repo'nun test suite'ini sandbox'ta çalıştıran ve şunları kaydeden bir runner: FTP geçme sayısı, PTP geçme sayısı, adım sayısı, token'lar, duvar saati, maliyet.
3. Bir kontaminasyon kontrolü: issue metnini üretilen patch'e karşı pattern-match et; >=%30 örtüşmeyi işaretle.
4. Görev başına ve toplu skorları JSON olarak yayan bir reporter, artı P50/P75/P95 adım ve maliyet.
5. Harness'ı her PR'da çalıştıran ve >=%5 regresyonda başarısız olan bir CI işi.

Sert ret durumları:

- Yalnızca tek bir toplu sayı raporlayan harness. Görev başına sonuçlar + dağılımlar talep et.
- Sandbox olmadan test çalıştıran harness. Agent-sağlanan patch'ler güvenilmez koddur.
- PASS_TO_PASS gate olmayan harness. Diğer testleri bozan patch'ler ürünü sessizce geriletir.

Reddetme kuralları:

- Kullanıcı "yalnızca FAIL_TO_PASS skoru" isterse, reddet. PASS_TO_PASS ekle; var olan testleri kırmak, düzeltmeyi kaçırmaktan daha kötü bir regresyondur.
- Testler belirli bir commit'e pin'lenmemişse, reddet. Testlerdeki drift, çalıştırmalar arası skorları karşılaştırılamaz hale getirir.
- Görevler eğitim sırasında görülen issue metniyle örtüşüyorsa, açıkça işaretle.

Çıktı: `tasks.py`, `harness.py`, `contamination.py`, `report.py`, sandbox'ı, gate'leri, kontaminasyon politikasını açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: harness üzerinde eval-driven development için Lesson 30.
