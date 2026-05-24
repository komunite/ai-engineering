---
name: vllm-stack-decider
description: İş yükü ve filo boyutu verildiğinde vLLM deployment layout'una karar ver — production-stack Helm chart, KV offload (native CPU veya LMCache), router/observability entegrasyonu.
version: 1.0.0
phase: 17
lesson: 18
tags: [vllm, production-stack, lmcache, kv-offload, connector-api]
---

İş yükü (prompt şekli, eşzamanlılık, prefix yeniden kullanım pattern'i), filo (engine'ler, GPU tipi) ve operasyonel bağlam (Kubernetes-native, multi-tenant, bütçe) verildiğinde, bir vLLM stack planı üret.

Üret:

1. Stack. vLLM production-stack Helm chart'ı kullan (yeni deployment'lar için önerilen) veya kendi kendine derle. Hangi operator'lar/CRD'lerin uygulandığını belirt.
2. KV offload. Seç:
   - Hiçbiri (kısa prompt'lar, düşük eşzamanlılık — overhead faydayı aşar).
   - Native vLLM CPU offload (tek-engine HBM baskısı, basit).
   - LMCache connector (çoklu-engine prefix yeniden kullanımı, preemption-yoğun veya multi-tenant paylaşılan prompt'lar).
3. HBM kullanım izleme. Headroom ile `--gpu-memory-utilization` ayarla; pre-preemption sinyali olarak %92+ sürekli üzerinde alarm.
4. Router entegrasyonu. Cache-aware router (Phase 17 · 11). KV-event kanalının yapılandırıldığını doğrula.
5. Observability. Engine başına Prometheus scrape, OTel GenAI öznitelikleri (Phase 17 · 13), production-stack'ten Grafana dashboard template'i.
6. Beklenen etki. Mevcuda karşı beklenen throughput kazancını niceliklendir — 16x H100 benchmark şeklini referans göster (KV ayak izi HBM'yi aştığında LMCache yardım eder).

Hard rejects:
- Paylaşılan prefix'ler veya preemption olmadan LMCache deploy etmek. Reddet — overhead, fayda yok.
- HBM baskısı izleme olmadan vLLM çalıştırmak. Reddet — ilk preemption sürpriz olacak.
- Helm chart kullanım durumunu kapsadığında production-stack'i elle derlemek. Reddet — yeniden icat maliyeti.

Reddetme kuralları:
- Filoda <2 engine varsa, LMCache'i reddet — engine'ler arası yeniden kullanım asıl mesele; tek-engine için native kullan.
- İş yükünde < 1K token prompt'lar ve < 100 eşzamanlılık varsa, herhangi bir offload'ı reddet — HBM headroom yeter.
- Takımda K8s yeteneği yoksa, production-stack'i reddet — tek-engine vLLM + basit proxy ile başla.

Çıktı: stack, KV offload seçimi, HBM izleme, router entegrasyonu, observability, beklenen etki adlandıran tek sayfalık plan. Tek gate ile bitir: son 24 saatte HBM kullanım P99.
