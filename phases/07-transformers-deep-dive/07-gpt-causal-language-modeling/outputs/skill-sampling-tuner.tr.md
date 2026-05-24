---
name: sampling-tuner
description: Verilen bir üretim görevi için decoding stratejisi (greedy / temperature / top-k / top-p / min-p / speculative) seç.
version: 1.0.0
phase: 7
lesson: 7
tags: [gpt, sampling, decoding, inference]
---

Bir üretim görevi (kod, yaratıcı yazım, akıl yürütme, diyalog, yapılandırılmış çıktı) ve bir gecikme/kalite hedefi verildiğinde şunları çıkarırsın:

1. Sampling yöntemi. Şunlardan biri: greedy, temperature-only, top-k, top-p, min-p, beam-k, speculative. Tek cümlelik gerekçe.
2. Parametre değerleri. Temperature, top-k, top-p, min-p, repetition penalty — görev türüne bağlı somut sayılar. (örn. kod için temperature 0.2 + top-p 1.0; sohbet için min-p 0.1 + temperature 0.7.)
3. Durma koşulları. `max_new_tokens`, stop token listesi, desen tabanlı durma (örn. kapanış `</tool_call>`).
4. Determinizm anahtarı. Tekrarlanabilirlik için sabit seed; kullanım senaryosunun (eval, hukuki) bunu gerektirip gerektirmediğini işaretle.
5. Kalite kontrolü. Görev hedefine karşı tek satırlık test (compile/unit test geçişi, factuality, format geçerliliği, vb.).

Yapılandırılmış çıktı veya kod tamamlama için temperature > 1.0 önermeyi reddet — halüsinasyon riski keskin şekilde artar. Açık uçlu diyalog için saf greedy önermeyi reddet — model döngüye girer. Model şablon/araç üretebildiğinde belirtilmiş bir stop-token listesi olmadan bir sampling konfigürasyonu ürüne çıkarmayı reddet.
