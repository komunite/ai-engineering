---
name: eval-suite
description: CI gate'leri ve evaluator-optimizer döngüsü ile üç katmanlı eval suite (static benchmark'lar, custom offline, online production) kur.
version: 1.0.0
phase: 14
lesson: 30
tags: [evaluation, ci, regression, benchmarks, llm-judge]
---

Bir agent ürünü verildiğinde, CI'ya bağlı üç katmanlı bir eval suite kur.

Üret:

1. **Static benchmark katmanı** — en az bir ilgili benchmark (kod için SWE-bench Verified, tool use için BFCL V4, web için WebArena, desktop için OSWorld, generalist için GAIA). Her zaman +-denetlenmiş skoru yanında raporla.
2. **Custom offline katmanı** — alana özgü boyutlarda skorlanan en az bir LLM-judge rubric'i (factual, ton, scope, ret kalitesi). Agent çalıştıktan sonra gerçek state'i sondalayan en az bir yürütme-tabanlı durum. Gold path ile en az bir trajectory-tabanlı durum.
3. **Online eval katmanı** — session replay'leri, guardrail-tetiklemeli alert'ler, OTel GenAI span'leri aracılığıyla adım başına cost/latency tracking (Lesson 23).
4. **Evaluator-optimizer runner** — agent'i propose / judge / refine içinde round cap ile sar.
5. **CI gate** — baseline'a göre >=%5 regresyonda build'i fail et. Baseline'ı zaman içinde takip et.
6. **Case haritalama** — Phase 14 derslerinden her guardrail ve her öğrenilmiş kuralın en az bir durumu var.

Sert ret durumları:

- Baseline'sız eval suite. Referans olmadan regresyonu tespit edemezsin.
- Factual görevlerde harici grounding olmadan LLM-judge. CRITIC pattern (Lesson 05) gerekli.
- Pin'lenmiş seed veya snapshot state olmadan flaky case'ler. Yanlış alarmlar takımın eval'lere güvenini erozyona uğratır.

Reddetme kuralları:

- Kullanıcı "yalnızca happy path" isterse, reddet. Her failure mode'un (Lesson 26) bir durumu olmalı.
- Kullanıcı "CI gate yok" isterse, ödeme yapan kullanıcılara dokunan ürünler için reddet. Aksi takdirde eval drift'i görünmezdir.
- Kullanıcı "tüm LLM-judge'lar" isterse, factual ve compliance görevlerinde reddet. Orada yürütme-tabanlı veya programatik evaluator'lar gerekli.

Çıktı: `cases/benchmarks/`, `cases/custom/`, `cases/online/`, `runner.py`, `ci_gate.py`, rubric'leri, baseline'ları ve Phase 14 haritalama tablosunu açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 24 (observability), Lesson 26 (failure mode'lar) veya substrat için Lesson 23 (OTel).
