---
name: disaggregation-decider
description: Belirli bir iş yükü ve cluster için disaggregated prefill/decode (Dynamo veya llm-d) benimsenip benimsenmeyeceğine karar ver. Prefill:decode oranlarını, KV transfer maliyetini ve beklenen tasarrufları niceliklendir.
version: 1.0.0
phase: 17
lesson: 17
tags: [disaggregated-serving, dynamo, llm-d, nixl, kv-transfer, prefill-decode]
---

İş yükü profili (prompt/çıktı uzunluk dağılımı, model, eşzamanlılık), cluster topolojisi (GPU'lar, fabric, RDMA availability) ve mevcut serving maliyeti verildiğinde, bir disaggregation kararı üret.

Üret:

1. Disaggregate edilsin mi? Numaralı gerekçeyle Evet / Hayır. Baseline: prompt'lar > 512 VE çıktılar > 200. Fabric: RDMA mevcudiyeti yardım eder; yalnızca TCP başabaşı uzatır.
2. Stack seçimi. NVIDIA Dynamo (vLLM/SGLang/TRT-LLM üzerinde managed orkestratör) veya llm-d (Kubernetes-native Service'ler). Operasyonel bağlama eşleştir.
3. Prefill:decode oranı. Dynamo Planner Profiler okumalarını kullan veya iş yükü şeklinden hesapla (prefill TFLOPS vs decode bytes/sec). Örnek: RAG-yoğun için 2 prefill : 1 decode; çıktı-yoğun için 1:2.
4. KV transfer planı. Adlandırılmış transport (NIXL üzerinden InfiniBand / RDMA / TCP fallback). Prompt P99'unuz için istek başına transfer vergisini hesapla.
5. Router entegrasyonu. Önde cache-aware router (Phase 17 · 11) olmalı — prefix eşleştirmesi olmadan disaggregation cache kazancını kaybeder.
6. Beklenen tasarruflar. Birlikte yerleşik baseline'a karşı hesapla; yayınlanmış vakayı referans göster (aynı SLA'da %30-40).

Hard rejects:
- Kısa-prompt iş yüklerini (<512 token) disaggregate etmek. Reddet — transfer vergisi baskındır.
- Cache-aware router olmadan deploy etmek. Reddet — kör routing KV locality'sini geçersiz kılar.
- Topolojiyi (rack packing) görmezden gelmek. Reddet — çok-rack hop üzerinden KV transferi aynı rack'teki RDMA'dan daha pahalıdır.

Reddetme kuralları:
- Cluster'da < 4 GPU varsa, reddet — disaggregation'ın ödeme yapması için yeterli pool çeşitliliği yok.
- RDMA/InfiniBand yoksa ve plan yoksa, TCP'nin başabaşı >2K prompt'lara yükselttiğini not et; yeniden değerlendir.
- Takım rol başına scale ile iki GPU pool'u işletemiyorsa, llm-d'yi reddet ve managed alternatif olarak Dynamo iste.

Çıktı: disaggregate E/H, stack seçimi, oran, transport, router, beklenen tasarruflar içeren tek sayfalık karar. Doğrulanacak tek metrikle bitir: KV transfer P99 latency'si; plan-tanımlı bir eşiği aşmaya gate.
