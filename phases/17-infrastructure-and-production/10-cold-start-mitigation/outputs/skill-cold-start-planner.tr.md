---
name: cold-start-planner
description: Serverless LLM deploy'ları için cold-start azaltmalarını seç ve katmanla. Fazları bütçele (node, image, ağırlıklar, engine, ilk forward) ve azaltmaları SLA'ya eşleştir.
version: 1.0.0
phase: 17
lesson: 10
tags: [cold-start, serverless, bottlerocket, model-streamer, gpu-snapshot, warm-pool, serverlessllm]
---

Model boyutu, SLA (TTFT P99), trafik şekli (sabit vs bursty) ve bütçe tutumu verildiğinde, bir cold-start azaltma planı üret.

Üret:

1. Cold-start bütçesi. Ham cold-start yolunu parçala (node provision, image pull, ağırlıkları HBM'ye, engine init, ilk forward). Belirtilen model boyutu için 2026 nominal saniyeleri kullan.
2. Katman seçimi. Toplamı SLA'nın altına indiren minimum sayıda katman seç: pre-seeded image (L1), model streamer (L2), GPU snapshot (L3), warm pool (L4), tiered loading (L5). Her katmanı saldırdığı spesifik faza karşı gerekçelendir.
3. Warm-pool boyutlandırması. Birincil yol için `min_workers` belirt. SLA TTFT P99 < 60s ve 70B+ model ise, maliyet ne olursa olsun warm pool zorunlu yap.
4. Maliyet tahmini. Seçilen warm-pool için aylık GPU maliyeti ve günde beklenen cold start sayısı.
5. Tail politikası. Yeni bir replica'daki ilk kullanıcıya ne olur — sıcak bir replica'ya kuyruğa mı alınır, yoksa cold-start vergisini mi öder? Spesifik bir politika adlandır (ör. "ilk isteği 10s içinde herhangi bir sıcak replica'ya yönlendir; cold'a düş").
6. Failure mode. Bir warm replica oturum ortasında ölürse ne olur. Recovery otomatik mi (live migration), yoksa bir sonraki istekte cold start mı?

Hard rejects:
- Aylık maliyeti hesaplamadan "sadece warm pool ekle" önermek.
- Saldırdığı spesifik faz olmadan azaltma iddia etmek (ör. 180s image pull'u ortadan kaldırdığını söylemeden "Bottlerocket kullan").
- GPU snapshot'lardaki GPU-topoloji başına kısıtı görmezden gelmek — platform SKU göç ettirirse, snapshot'lar geçersizdir.

Reddetme kuralları:
- SLA warm pool olmadan yeni 70B cold start'ta TTFT P99 < 5s ise, reddet — 2026 altyapı hızlarında matematiksel olarak imkansız.
- Bütçe warm pool yasaklarsa ama SLA 30s altı cold start gerektirirse, platforma özgü düzeltmeyi adlandır (Modal GPU snapshots, Baseten pre-warming) ve onsuz farklı bir platformda SLA'yı vaat etmeyi reddet.
- Operatör bursty trafik ve bir 70B modelle scale-to-zero isterse, SLA'yı vaat etmeyi reddet — snapshot'lar veya warm pool olmadan matematik tutmaz.

Çıktı: fazları, katmanları, `min_workers`'ı, aylık maliyeti, tail politikasını, failure mode'u listeleyen tek sayfalık plan. Alarm vereceğin tek metrikle bitir: son yuvarlanan saatte P99 cold-start süresi.
