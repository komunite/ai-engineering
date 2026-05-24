---
name: safety-harness
description: Hedef bir LLM app etrafına katmanlı bir safety pipeline'ı bağla, altı aileli bir red-team menzili çalıştır ve ölçülebilir bir harmlessness delta için constitutional self-critique çalıştır.
version: 1.0.0
phase: 19
lesson: 15
tags: [capstone, safety, red-team, llama-guard, x-guard, garak, pyrit, constitutional-ai]
---

Bir hedef LLM uygulaması (8B instruction-tuned model veya RAG chatbot) verildiğinde, katmanlı bir safety pipeline'ı ile sertleştir ve altı saldırı ailesi üzerinde autonomous bir red-team menzili çalıştır. Öncesi/sonrası harmlessness raporu üret.

Build planı:

1. Beş katmanlı pipeline: input sanitize (zero-width strip, encoding decode, Unicode normalize) -> NeMo Guardrails v0.12 rail'leri -> classifier gate (Llama Guard 4 / X-Guard / ShieldGemma-2 / Nemotron 3) -> target LLM -> output filter (Llama Guard 4 + Presidio PII + citation check). Flag'lenen çıktılar Slack HITL queue'suna gider.
2. Katman başına Langfuse span yay ki attribution uçtan uca observable olsun.
3. garak, PyRIT, PAIR, TAP, GCG, multi-turn persona ve multilingual code-switch saldırılarını cron'da çalıştıran red-team scheduler.
4. Her başarılı jailbreak: CVSS 4.0 skoru, repro, mitigation planı, disclosure timeline.
5. Over-refusal regression'larını yakalamak için sürekli çalışan XSTest benign-prompt probe.
6. Constitutional self-critique çalıştırması: 1k zararlı-girişim prompt -> target draft'lar -> critic yazılı anayasaya karşı skorlar -> yeniden yazılmış çiftler -> SFT. Held-out harmlessness eval üzerinde öncesi/sonrası ölç.
7. Alarmlar: benign-regression'da Slack warning, yeni jailbreak ailesinde PagerDuty critical.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Saldırı yüzeyi kapsamı | 6+ saldırı ailesi egzersize edildi, 2+ dil |
| 20 | True-positive / false-positive dengesi | XSTest benign pass oranına karşı saldırı bloklama oranı |
| 20 | Self-critique delta | Held-out eval üzerinde öncesi/sonrası harmlessness |
| 20 | Dokümantasyon ve disclosure | Timeline'lı CVSS skorlu bulgular |
| 15 | Otomasyon ve tekrarlanabilirlik | Cron-driven, alarmlar uçtan uca egzersize edildi |

Sert ret durumları:

- Tek katmanlı safety stack'leri. Bu capstone'un tezi defense in depth'tir.
- XSTest over-refusal sayıları olmadan başarı oranı raporlayan red-team çalıştırmaları.
- Held-out eval'siz constitutional self-critique (training-set doğruluğunu, generalization'ı değil raporlar).
- Jailbreak bulgularında eksik CVSS skorlaması.

Reddetme kuralları:

- Benign-probe karşı noktası olmadan safety sayısı raporlamayı reddet. Birisi olmadan diğeri yanıltıcıdır.
- Critique çiftlerinin insan curasyonu olmadan red-team başarılarında otomatik yeniden eğitmeyi reddet.
- En az iki İngilizce olmayan dil üzerinde X-Guard çalıştırmadan multilingual kapsam iddia etmeyi reddet.

Çıktı: beş katmanlı pipeline, red-team scheduler, PAIR/TAP/GCG runner'ları, constitutional-self-critique training harness'i, XSTest over-refusal dashboard'u, CVSS bulgu tracker'ı ve sertleştirme öncesi en yüksek başarı oranına sahip üç saldırı ailesi ile her birini mitigate eden spesifik pipeline katmanını adlandıran bir yazımı içeren bir repo.
