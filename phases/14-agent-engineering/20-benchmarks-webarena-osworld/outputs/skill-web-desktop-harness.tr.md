---
name: web-desktop-harness
description: Yürütme-tabanlı değerlendirme ve trajectory-verimliliği metrikleri ile WebArena/OSWorld tarzı bir harness kur.
version: 1.0.0
phase: 14
lesson: 20
tags: [webarena, osworld, harness, trajectory-efficiency]
---

Bir hedef uygulama (web veya desktop) ve gold trajectory'ler ile görev listesi verildiğinde, bir eval harness'ı kur.

Üret:

1. Görev tanımları: `(tid, description, gold_steps, success_predicate, state_reset)`.
2. Runner: agent'i çalıştırır, her eylemi yakalar, adım sayısı + geçen süre + başarı durumunu kaydeder.
3. Trajectory-verimliliği metriği: `agent_steps / gold_steps`. Görev başına ve toplu raporla.
4. Görevler arası state reset — bir görevi başka bir görev tarafından kirletilmiş state üzerinde asla çalıştırma.
5. Failure-mode classifier'ı: her başarısızlık için, bunun bir grounding miss (yanlış element) mi yoksa planlama miss'i (yanlış eylem) mi olduğunu etiketle.

Sert ret durumları:

- Görevler arası state reset yok. Görevler arası kontaminasyon tüm skorları geçersiz kılar.
- Yalnızca-başarı-oranı raporlama. Trajectory verimliliği 2026 standardıdır.
- DOM eşliği olmadan yalnızca-screenshot harness'ı. Bazı agent'ler DOM+vision kullanır; yüzeyi özel olarak kısıtlamadıkça her ikisini de ver.

Reddetme kuralları:

- Görevlerin gold trajectory'si yoksa, reddet. Bunlar olmadan verimliliği ölçemezsin.
- Uygulama belirli bir versiyona pin'lenmemişse, reddet. Drift, çalıştırmalar arası karşılaştırmaları geçersiz kılar.
- Agent destructive tool'lara sahipse (delete, publish), uygulamanın sandbox kopyasını talep et.

Çıktı: `tasks.py`, `runner.py`, `failure_classifier.py`, `report.py`, reset politikasını, gold-trajectory kaynaklamasını ve grounding-vs-planlama ayrımını açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 21 (computer use modelleri) veya Lesson 30 (eval-driven development).
