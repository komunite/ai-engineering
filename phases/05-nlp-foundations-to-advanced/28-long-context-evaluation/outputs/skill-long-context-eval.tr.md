---
name: long-context-eval
description: Verilen bir model ve kullanım senaryosu için long-context değerlendirme bataryası tasarla
version: 1.0.0
phase: 5
lesson: 28
tags: [nlp, long-context, evaluation]
---

Bir hedef model, hedef context uzunluğu ve kullanım senaryosu verildiğinde şunları çıkarırsın:

1. Testler. NIAH derinlik × uzunluk gridi; RULER multi-hop; özel alan görevi.
2. Örnekleme. Her uzunlukta 0, 0.25, 0.5, 0.75, 1.0 derinlikleri.
3. Metrikler. Retrieval pass oranı; reasoning pass oranı; ilk-token-süresi; sorgu başına maliyet.
4. Kesim. Etkin retrieval uzunluğu (%90 pass) ve etkin reasoning uzunluğu (%70 pass). İkisini de raporla.
5. Regresyon. Sabit harness, her model yükseltmesinde yeniden çalıştır, delta'ları yüzeylendir.

Model kartından gelen context window'una tek başına güvenmeyi reddet. Herhangi bir multi-hop iş yükü için sadece-NIAH değerlendirmesini reddet. Bağımsız kanıt olarak vendor'un kendi raporladığı long-context skorlarını reddet.
