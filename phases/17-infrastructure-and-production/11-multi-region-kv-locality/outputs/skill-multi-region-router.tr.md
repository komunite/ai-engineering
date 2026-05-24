---
name: multi-region-router
description: KV-cache locality, yerleşiklik sınırları, DR manifest'i ve çeyreklik failover tatbikatıyla çok bölgeli bir LLM routing planı tasarla.
version: 1.0.0
phase: 17
lesson: 11
tags: [multi-region, kv-cache, routing, dr, bedrock-cri, vllm-router, llm-d, gorgo]
---

Kapsamdaki bölgeler, yerleşiklik sınırları, beklenen prefix-cache çeşitliliği ve TTFT SLA verildiğinde, bir çok bölgeli routing ve DR planı üret.

Üret:

1. Router seçimi. Cache-aware bir router seç (vLLM Router, llm-d router) ve KV-event kanalını tanımla. Prefix-hash algoritmasını adlandır (ör. 512-token rolling) ve tie-breaker'ı (en az queue depth).
2. Routing politikası. Bölgesel-öncelikli mi yoksa global (GORGO-tarzı) prefill + RTT minimizasyonu mu? Prompt-uzunluk dağılımıyla gerekçelendir — uzun prompt'lar (>8K token) bölgeler arası routing'den faydalanır; kısalar faydalanmaz.
3. Yerleşiklik bölümlemesi. Herhangi bir optimizasyondan önce: hangi istekler hangi bölgelere yasal nedenlerle bağlı (GDPR, HIPAA). TTFT iyileşse bile yerleşiklik aşan routing'i yasakla.
4. Ticari CRI katmanı. Availability katmanı olarak Bedrock Cross-Region Inference veya GKE Multi-Cluster Gateway etkinleştirmeyi öner. Bu katmanın TTFT optimizasyonu OLMADIĞINI net belirt.
5. DR manifest. Minimum üç dosya (HF repo + engine config + deployment manifest). Tokenizer, quantization config'leri, RoPE, chat template'leri, LoRA adaptörlerinin dahil olduğunu doğrula. Saklama yerini belirt (S3 cross-region replication, multi-region GCS).
6. Failover tatbikatı. Çeyreklik cadans. Kim yürütür, ne ölçülür (RTO, RPO, cache ısınma süresi). Hedef: gerçek 2024 JPMorgan tatbikatına eşleşen 30-dakikalık RTO.

Hard rejects:
- Routing optimizasyonu için yerleşikliği görmezden gelmek. Reddet — GDPR ihlali TTFT kazancını döver.
- Bedrock CRI'nin bölgeler arası routing'i "çözdüğünü" iddia etmek. Reddet — CRI availability'dir, TTFT değil.
- Yalnızca ağırlıkları yedeklemek. Reddet — %32 DR başarısızlık istatistiğini adlandır ve üç dosyalı manifesti iste.

Reddetme kuralları:
- Kapsamda yalnızca bir bölge varsa, planı reddet — tek bölgenin farklı failure mode'ları vardır (Phase 17 · 03 kapsar).
- Yerleşiklik ve TTFT SLA uyumsuzsa (ör. AB yerleşikliği 8K prompt'larda P99 TTFT < 100 ms ile istek başına soğuk prefix üzerinde prefill'i zorluyorsa), SLA'yı vaat etmeyi reddet ve ürün gereksinimini eskalasyona al.

Çıktı: router, routing politikası, yerleşiklik bölümleri, CRI katmanı tutumu, DR manifest, çeyreklik tatbikat sahibini adlandıran tek sayfalık plan. Alarm vereceğin tek metrikle bitir: bölgeler arası prefix-cache hit oranının plan-tanımlı bir eşiğin altına düşmesi.
