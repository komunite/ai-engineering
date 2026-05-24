---
name: failure-detector
description: Agent trace'leri için failure-mode dedektörleri üret; bir trace store'a bağlı, sektörde tekrarlayan beş modu artı alana özgü imzaları etiketler.
version: 1.0.0
phase: 14
lesson: 26
tags: [failure-modes, masft, detection, observability]
---

Bir ürün alanı ve bir trace store verildiğinde, agent failure mode'ları için dedektörler üret.

Üret:

1. Mod başına dedektör: `hallucinated_action`, `scope_creep`, `cascading_errors`, `context_loss`, `tool_misuse`, `success_hallucination`.
2. Alana özgü dedektörler (örn. bir dev tool için "issue bağlamadan PR oluşturdu", bir marketing tool için "onay olmadan > 5 alıcıya email gönderdi").
3. Tüm dedektörleri her trace'e uygulayan ve bir dağılım yayan Tagger.
4. Eşik-tabanlı alerting: bugünün trace'lerinin >=%5'i bir modu etiketliyorsa, page veya bilet aç.
5. Sample saklama: etiketlenen her trace için, operatör review'ı için input + output + state snapshot'larını sakla.

Sert ret durumları:

- Production'da trace başına LLM çağrısı gerektiren dedektörler. Pattern-tabanlı dedektörler kullan; LLM-judge'ı sample'lanmış review için sakla.
- Yalnızca crash'te etiketleme. Çoğu başarısızlık geçerli görünümlü çıktı üretir. İçerik + state üzerinde imza kontrolleri gerekli.
- PII redaksiyon olmadan etiketlenmiş trace'leri saklamak. Failure örnekleri en kötü içeriği taşır; saklamadan önce temizle.

Reddetme kuralları:

- Kullanıcı "tüm trace'leri sonsuza kadar sakla" isterse, maliyet + compliance nedenleriyle reddet. Etiketle + oranla sample'la.
- Ürünün "known good" baseline'ı yoksa, drift alert'lerini reddet. Drift'in bir referansa ihtiyacı var.
- Dedektörler version'lı değilse, reddet. Dedektör regresyonları sinyalini haber vermeden kırar.

Çıktı: `detectors.py`, `tagger.py`, `alerts.py`, `retention.py`, eşikleri, saklama politikasını, alert yönlendirmesini açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 24 (observability backend'leri) veya adversarial failure mode'ları için Lesson 27 (prompt injection).
