---
name: slo-goodput-gate
description: P50/P90/P99 yüzdelikleri ve belgelenmiş tool seçimiyle LLM deploy'larını throughput değil goodput üzerinde gate'leyen CI/CD-hazır bir benchmark tarifi üret.
version: 1.0.0
phase: 17
lesson: 08
tags: [inference-metrics, goodput, ttft, tpot, itl, slo, benchmarking]
---

Bir iş yükü (model, hardware, hedef eşzamanlılık, kullanıcıya dönük etkileşim tipi — streaming sohbet / tek-atımlık / ses / agent) verildiğinde, CI/CD için goodput tabanlı bir SLO gate üret.

Üret:

1. SLO spec. Üç eşik: TTFT P99 sınırı, TPOT P99 sınırı, E2E P99 sınırı. Etkileşim tipinden savunulabilir değerler seç (streaming sohbet: TTFT 500 ms, TPOT 25 ms, E2E 3 s; ses: TTFT 300 ms daha sıkı; agent: E2E 5 s daha gevşek).
2. Benchmark tarifi. Tool seçimi (LLMPerf veya GenAI-Perf — seçtiğini ve nedenini belirt). Prompt dağılımı (girdi ve çıktı token'larının ortalama + standart sapma). Eşzamanlılık taraması (hedefin %25, %50, %100, %150'si).
3. Goodput hesaplaması. Formül: üç kısıtı aynı anda karşılayan isteklerin oranı. Üretim için hedef >= %99, canary için >= %95.
4. Yüzdelik raporlama. Her metrik için P50, P90, P99 raporla (asla yalnız ortalama değil). Sadece sanity check için ortalamaları annote et.
5. Tool tuzağı notu. Tool'un ITL'den TTFT'yi dahil mi yoksa hariç mi tuttuğunu belirt. Takımlar arası karşılaştırmadan önce tanımı düzelt.
6. Gate mantığı. Goodput hedef eşzamanlılıkta hedefi karşılarsa CI geçer. %100 ile %150 eşzamanlılık arasında goodput 5 puandan fazla düşerse işaretle — load-test headroom'unun eksik olduğunu gösterir.

Hard rejects:
- Yalnızca throughput üzerinde gate'lemek. Reddet ve goodput iste.
- P99 olmadan ortalama raporlamak. Reddet.
- Tool adını ve tool sürümünü atlamak. Reddet.
- Yalnızca hedef eşzamanlılıkta benchmark yapmak; her zaman taramayı yap.

Reddetme kuralları:
- Kullanıcının yazılmış bir SLO'su yoksa, reddet ve önce etkileşim tipine göre bir tane yaz.
- Prompt dağılımı "döngüde aynı prompt'lar"sa, reddet — bu prompt-tekdüzelik tuzağıdır. Gerçekçi sentetik iste.
- Benchmark < 30 koşu veya koşu başına <100 istek ise, istatistiksel olarak yetersiz olarak reddet.

Çıktı: eşikleri, benchmark tarifini, tool seçimini, yüzdelik rapor şablonunu ve CI pass/fail kuralını listeleyen tek sayfalık SLO gate spec'i. Bilinen zayıflığa göre goodput vs eşzamanlılık eğrisi, prompt-dağılımı duyarlılığı veya chunked-prefill on/off tail karşılaştırmasından birini adlandıran "sırada neyi ölç" paragrafıyla bitir.
