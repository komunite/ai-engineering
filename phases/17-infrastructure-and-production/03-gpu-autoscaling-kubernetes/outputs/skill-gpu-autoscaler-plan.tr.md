---
name: gpu-autoscaler-plan
description: Kubernetes tabanlı bir LLM serving cluster'ı için üç katmanlı GPU autoscaling planı tasarla (Karpenter + KAI Scheduler + uygulama sinyalleri). DCGM_FI_DEV_GPU_UTIL tuzaklarını ve kısmi tahsis arızalarını teşhis et.
version: 1.0.0
phase: 17
lesson: 03
tags: [kubernetes, gpu, autoscaling, karpenter, kai-scheduler, hpa, dynamo-planner, llm-d]
---

Cluster topolojisi (node'lar, GPU tipleri, NVLink domain'leri), iş yükü şekli (TP/PP konfig, ortalama eşzamanlılık, burst katsayısı) ve SLO (TTFT P99, goodput) verildiğinde, üç katmanlı bir autoscaling planı üret.

Üret:

1. Katman 1 — Karpenter NodePool. `instance-type`, `capacity-type` (on-demand / spot / reserved), `consolidationPolicy` (GPU pool'ları için `consolidateAfter: 1h` ile `WhenEmpty` olmalı), GPU dışı iş yüklerini hariç tutan taint'ler ve KAI Scheduler seçimi için label'ları belirt.
2. Katman 2 — KAI Scheduler politikası. Gang scheduling'in gerekli olup olmadığını belirt (TP/PP > 1 için evet). Topoloji kısıtını tanımla (NVLink domain, rack, zone). Üretim vs eğitim tenant'ları için kuyruk hiyerarşisi ve preemption kurallarını belirt.
3. Katman 3 — Uygulama autoscaler'ı. Sinyali seç: prefill-bound iş yükleri için queue depth, decode-bound için KV cache kullanımı, karma için composite goodput. `DCGM_FI_DEV_GPU_UTIL`'i yasakla ve nedenini açıkla.
4. Disaggregated bölünme. Phase 17 · 17 disaggregated prefill/decode kullanılıyorsa, ayrı HPA'lar belirt — prefill pool için queue depth sinyali, decode pool için KV utilization sinyali.
5. Warm-pool boyutlandırması. SLO-kritik yollar için minimum hazır replica sayısı, P99 TTFT kısıtı ve gözlenen cold-start süresine (node provision + model yükleme) dayalı.
6. İzleme. Dashboard'a alınacak metrikler: replica başına queue depth, replica başına KV utilization, node provision bekleme süresi, gang-scheduling erteleme sayısı, Karpenter consolidation event'leri.

Hard rejects:
- `DCGM_FI_DEV_GPU_UTIL` üzerinde HPA önermek. Reddet ve doğru sinyaller olarak queue depth + KV utilization'ı adlandır.
- Bir GPU pool'u için `consolidationPolicy: WhenEmptyOrUnderutilized` bırakmak. Reddet ve çalışan-job tahliye riskini referans göster.
- Bir TP/PP iş yükü için gang scheduling'i görmezden gelmek. Reddet — kısmi tahsis para yakan bir anti-pattern'dir.

Reddetme kuralları:
- Cluster'da yalnızca bir GPU tipi ve bir node varsa, Karpenter önermeyi reddet — müşteriye önce managed serverless (Phase 17 · 02) lazım.
- Operatör "GPU belleği üzerinde scale etmek" isterse, reddet — vLLM `--gpu-memory-utilization`'a önceden tahsis eder; bellek tek istekte bile %90 civarında kalır.
- TP-8 bir iş yükü için karmaşıklık gerekçesiyle gang scheduling reddedilirse, planı onaylamayı reddet — 8 dağınık GPU üzerinde tek-pod yerleşimi atomik olarak başarısız olur.

Çıktı: Karpenter YAML snippet'i, KAI Scheduler config snippet'i, HPA/özel autoscaler sinyal seçimi, warm-pool sayısı ve beş dashboard metriğiyle tek sayfalık plan. Tek bir kill-switch ile bitir: P99 TTFT ihlal olursa, son-bilinen autoscaler durumuna rollback yap.
