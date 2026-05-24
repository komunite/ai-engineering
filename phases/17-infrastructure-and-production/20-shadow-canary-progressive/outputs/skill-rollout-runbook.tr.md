---
name: rollout-runbook
description: Yeni bir LLM modeli veya prompt template'i için beş canary gate, gürültü-tabanına duyarlı eşikler ve saniyeler-hızlı rollback yoluyla shadow → canary → A/B → %100 rollout planı tasarla.
version: 1.0.0
phase: 17
lesson: 20
tags: [rollout, canary, shadow, progressive-delivery, feature-flags, argo-rollouts, flagger, kserve]
---

Bir aday değişiklik (yeni model, yeni prompt template'i, yeni router politikası), baseline üretim metrikleri ve risk toleransı verildiğinde, bir rollout runbook'u üret.

Üret:

1. Shadow planı. Süre (24-72 saat). Loglanan metrikler: çıktılar, token sayıları, latency, refusal, hata. Alarm: >%20 maliyet kayması, >%30 çıktı uzunluk kayması, herhangi bir şema ihlali.
2. Canary ilerlemesi. Aşamalar (%1 → %10 → %25 → %50 → %75 → %100). Aşama başına süre (trafik hacmine göre 30dk-24sa; her aşamanın istatistiksel güven için yeterli veriye sahip olduğundan emin ol).
3. Beş gate. Latency P99, istek başına maliyet, hata/refusal, çıktı uzunluğu P99, thumbs-down oranı için tam eşikleri belirt. Gürültü tabanının üzerine ayarla (%15 indirgenemez varyans bekle).
4. Tooling. Rollout controller'ı adlandır (Argo Rollouts, Flagger, KServe) ve anında rollback için feature flag sistemi.
5. Rollback yolu. Üç eylemi belgele: flag'i çevir → pinlenmiş digest'i geri al → doğrula. Hedef süre: uçtan uca 60 saniyenin altında.
6. A/B atlansın mı? Gerekçelendir. İyileştirilmiş-varyant değişiklikler A/B'yi atlar; belirgin farklı değişiklikler (yeni davranış, yeni maliyet eğrisi) A/B gerektirir.

Hard rejects:
- Shadow modu atlamak. Reddet — maliyet artışları ve uzunluk regresyonları offline değerlendirmeyi geçer.
- %15 varyanstan daha sıkı gate'ler. Reddet — yanlış alarmlar meşru rollout'ları durdurur.
- Yeniden deploy gerektiren rollback. Reddet — bu rollback değil, hasar raporudur.

Reddetme kuralları:
- Değişiklik güvenlik-kritikse (ör. PII işleme değişikliği), açık ek gate iste: canary'ye başlamadan önce shadow örneğinde sıfır PII sızıntısı.
- Trafik hacmi <100 istek/saat ise, uzatılmış canary aşamaları iste — aksi takdirde gate gürültüsü sinyali bastırır.
- Takım beş canary gate için baseline metrikleri sağlayamıyorsa, rollout'u reddet — baseline ön koşuldur.

Çıktı: shadow, canary, gate'ler, tooling, rollback, A/B tutumu içeren tek sayfalık runbook. Rollback tatbikatı gereksinimiyle bitir: ilk gerçek deploy'dan önce rollback'i bir kez prova et.
