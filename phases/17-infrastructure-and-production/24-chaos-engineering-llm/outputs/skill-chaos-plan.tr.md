---
name: chaos-plan
description: Bir LLM chaos engineering planı tasarla — ön koşulları doğrula, dört düzlem kur, tool seç, üç güvenli deneyle başla, safety-plane gate'lerini zorla.
version: 1.0.0
phase: 17
lesson: 24
tags: [chaos-engineering, litmuschaos, chaosmesh, harness, llm-chaos, game-day]
---

Stack (Kubernetes / VM'ler / managed), SLI/SLO olgunluğu, observability kalitesi ve takım on-call olgunluğu verildiğinde, bir chaos planı üret.

Üret:

1. Ön koşul kontrolü. SLI/SLO tanımlı, observability bağlı, rollback otomatik, runbook'lar yapılandırılmış, on-call rotasyonu olduğunu doğrula. Herhangi biri eksikse, üretim chaos'unu çalıştırmayı reddet.
2. Dört düzlem. Her düzlem için tool'ları adlandır (control, target, safety, observability). Observability için Phase 17 · 13'e yönlendir.
3. Üç başlangıç deneyi. Pod kill ile başla. Sonra sağlayıcı 429. Sonra bellek aşırı yüklemesi. Her biri blast-radius sınırı, süre, başarı kriteriyle.
4. Safety gate'leri. Burn-rate (>2x beklenen), blast-radius (filonun < %30'u), trace-ID etiketleme, suppression pencereleri.
5. Cadans. Haftalık küçük canary. Aylık game day (takımlar arası). Çeyreklik resilience denetimi.
6. Tooling. LitmusChaos (OSS, CNCF mezunu), Chaos Mesh (OSS, CNCF sandbox), Harness Chaos (ticari AI-asistanlı), AWS FIS / Azure Chaos Studio (managed cloud-native).

Hard rejects:
- Beş ön koşul olmadan üretimde chaos çalıştırmak. Reddet — gerçek incident'e dönüşür.
- Blast-radius sınırları olmadan deneyler. Reddet.
- Trace-ID etiketleme olmadan deneyler. Reddet — alarmları dedupe etmek imkansız.

Reddetme kuralları:
- Takım staging'de hiç başarılı bir deney çalıştırmadıysa, staging'de bir yeşil olana kadar üretim chaos'unu reddet.
- Incident hacmi zaten yüksekse (>2/hafta), eklenen chaos'u reddet — önce stabilize et.
- Takımda SLO yoksa, herhangi bir deneyden önce SLO iste.

Çıktı: ön koşul kontrolü, dört-düzlem tool'ları, üç başlangıç deneyi, safety gate'leri, cadans içeren tek sayfalık plan. Çeyreklik bağımlılık-haritası güncelleme taahhüdüyle bitir.
