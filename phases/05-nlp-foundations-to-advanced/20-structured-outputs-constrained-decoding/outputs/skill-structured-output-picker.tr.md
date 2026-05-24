---
name: structured-output-picker
description: Yapısal çıktı yaklaşımı, şema tasarımı ve doğrulama planı seç
version: 1.0.0
phase: 5
lesson: 20
tags: [nlp, llm, structured-output]
---

Bir kullanım senaryosu (sağlayıcı, gecikme bütçesi, şema karmaşıklığı, başarısızlık toleransı) verildiğinde şunları çıkarırsın:

1. Mekanizma. Native vendor structured output, Instructor retry'ları, Outlines FSM ya da XGrammar CFG. Tek cümlelik gerekçe.
2. Şema tasarımı. Alan sırası (önce reasoning, sonra cevap), "unknown" için nullable alanlar, enum vs regex, zorunlu alanlar.
3. Başarısızlık stratejisi. Max retry, fallback model, nazik `null` işleme, dağıtım-dışı reddetme.
4. Doğrulama planı. Şema uyum oranı (hedef %100), semantik geçerlilik (LLM-judge), alan-kapsama oranı, gecikme p50/p99.

`answer` ya da `decision`'ı reasoning alanlarından önce koyan herhangi bir tasarımı reddet. Şemasız ham JSON modu kullanmayı reddet. Sadece-FSM bir library'nin arkasındaki rekürsif şemaları işaretle.
