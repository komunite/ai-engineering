---
name: nli-picker
description: Bir sınıflandırma / faithfulness / zero-shot görevi için NLI modeli, etiket şablonu ve değerlendirme kurulumu seç
version: 1.0.0
phase: 5
lesson: 21
tags: [nlp, nli, zero-shot]
---

Bir kullanım senaryosu (faithfulness kontrolü, zero-shot sınıflandırma, doküman-seviyesi çıkarım) verildiğinde şunları çıkarırsın:

1. Model. Adlandırılmış NLI checkpoint. Alana, uzunluğa, dile bağlı gerekçe.
2. Şablon (zero-shot ise). Sözelleştirme deseni. Örnek.
3. Eşik. Karar kuralı için entailment kesim noktası. Kalibrasyona dayalı gerekçe.
4. Değerlendirme. Held-out etiketli set üzerinde doğruluk, hypothesis-only baseline, adversarial alt küme.

100-örnek etiketli sağlık kontrolü olmadan zero-shot sınıflandırma ürüne çıkarmayı reddet. Cümle-seviyesi NLI modelini doküman-uzunluğunda premise'larda kullanmayı reddet. NLI'nın halüsinasyonu çözdüğü iddiasını işaretle — azaltır, ortadan kaldırmaz.
