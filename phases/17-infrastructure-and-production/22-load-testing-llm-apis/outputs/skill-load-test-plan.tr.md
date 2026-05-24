---
name: load-test-plan
description: Gerçekçi bir LLM load testi tasarla — tool seç (LLMPerf, k6, GenAI-Perf, guidellm), dört pattern kur (sabit, ramp, spike, soak) ve CI'da gate'le.
version: 1.0.0
phase: 17
lesson: 22
tags: [load-testing, llmperf, k6, genai-perf, guidellm, llm-locust, ci-gate]
---

İş yükü (endpoint, TTFT/TPOT/hata için SLA), hedef ölçek (eşzamanlılık, RPS) ve CI tutumu (PR gate veya yalnızca release) verildiğinde, bir load test planı üret.

Üret:

1. Tool. Baseline koşular için LLMPerf; CI gate'leri için k6 + streaming uzantısı; NVIDIA-referans koşular için GenAI-Perf; büyük sentetik için guidellm. LLM-Locust yalnızca zaten Locust üzerindeyse.
2. Prompt dağılımı. Gerçek trafikten ortalama + standart sapma girdi token'ları (mevcutsa) veya yayınlanmış dağılım (ShareGPT / HumanEval). Tek-prompt-döngüsünü yasakla.
3. Dört pattern. Sabit, ramp, spike, soak. Her biri için: hedef RPS, süre, beklenen failure mode.
4. CI gate. Spesifik eşikler: TTFT P95 < X, 5xx < %5, TPOT < Y. PR başına runtime: 3-5 dk.
5. Metrik hizalaması. Raporlama tool'unun GenAI-Perf-tarzı (ITL TTFT'yi hariç tutar) mı yoksa LLMPerf-tarzı (ITL TTFT'yi içerir) mı olduğunu not et. Birini seç ve tutarlı kal.
6. Çıktı. Repo'ya commit edilmiş bir script dosyası (k6 JS, LLMPerf CLI).

Hard rejects:
- Tekdüze prompt'larla load testi. Reddet — sayılar yalan söyler.
- Streaming desteği olmadan load testi. Reddet — LLM endpoint'leri varsayılan olarak streaming'tir.
- Metrik-tanımı farklılıklarını kabul etmeden tool'lar arası sayıları karşılaştırmak. Reddet.

Reddetme kuralları:
- Takım LLM-Locust uzantısı olmadan stock Locust üzerinde çalıştırmayı düşünüyorsa, reddet — GIL tuzağı.
- CI gate bütçesi PR başına < 60s ise, tam soak'u reddet — hızlı sabit-durum artı ayrı gece soak öner.
- Prompt dağılım verisi mevcut değilse, belgelenmiş yayınlanmış dağılım (ShareGPT) iste ve varsayımı not et.

Çıktı: tool, prompt dağılımı, hedefli dört pattern, CI gate eşikleri, metrik hizalaması içeren tek sayfalık plan. Tek CI çıktısıyla bitir: yalnızca tüm eşikler karşılanırsa, 3-koşu stabilitesinde PR yeşil.
