# LLM'ler için Shadow Trafiği, Canary Rollout ve Progressive Deployment

> LLM rollout'ları yazılım deployment'ının en zor kısımlarını birleştirir: unit test yok, dağınık başarısızlık modları, gecikmiş sinyaller. Sıra (1) shadow modu — prod isteklerini aday modele duplike et, logla, sıfır kullanıcı etkisiyle karşılaştır; bariz dağılım sorunlarını yakalar ama kalite garantisi değildir; (2) canary rollout — her adımda gate'lerle %10 → %25 → %50 → %75 → %100 progresif trafik kayması; gecikme percentile'larını, istek başına maliyeti, hata/reddetme oranını, output uzunluk dağılımını, kullanıcı-geri bildirim oranını izle; (3) stabilite onaylandıktan sonra farklı alternatifler için A/B testing. Non-determinizm indirgenemez — GPU FP non-associativity artı batch-boyutu varyansı nedeniyle özdeş input'larla çalıştırmalar arası %15'e varan doğruluk varyasyonu. Maliyet bir değişken, sabit değil — %20 daha iyi bir model çağrı başına 3x daha pahalı olabilir. Rollback hızı belirleyici: rollback redeploy gerektiriyorsa, çok yavaşsın. Politika config/flag'lerde yaşar; model pinli digest'lerle registry'de yaşar; rollback = politika çevir + eşiği geri al + eski modeli saniyeler içinde pin'le.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak canary-progresyon simülatörü)
**Ön koşullar:** Faz 17 · 13 (Observability), Faz 17 · 21 (A/B Testing)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Shadow modunu (sıfır-etki karşılaştırma), canary'yi (canlı trafik progresif) ve A/B'yi (stabilite-onaylı karşılaştırma) ayır.
- Beş LLM-spesifik canary metriğini (gecikme, istek başına maliyet, hata/reddetme, output-uzunluk dağılımı, kullanıcı geri bildirimi) say.
- LLM non-determinizminin (%15'e kadar) bir rollout'ta "stabil"in anlamını nasıl değiştirdiğini açıkla.
- Saniyeler (politika çevir) süren bir rollback yolu tasarla — saatler (redeploy) değil.

## Sorun

Yeni bir model yayınlıyorsun. Offline eval'ler %3 doğruluk kazancı gösteriyor. Üretimde açıyorsun. 24 saat içinde, maliyet %40 yukarıda, kullanıcı thumbs-down %8 yukarıda, üç müşteri ticket'ı "garip cevaplar" rapor ediyor. Geri alıyorsun. Redeploy 3 saat alıyor. Hafta sonun mahvoluyor.

Bunun her parçası önlenebilirdi. Shadow modu %40 maliyet sıçramasını herhangi bir kullanıcı görmeden önce yakalardı. Canary thumbs-down hareket ettiğinde %10'da dururdu. Policy-flag rollback 30 saniye alırdı. Disiplin "offline eval'ler iyi görünüyor" ile "gerçek kullanıcılar mutlu" arasındaki boşluğu dolduran şey.

## Kavram

### Shadow modu

Aday üretimle aynı istekleri alır; output'lar log'lanır, kullanıcılara döndürülmez. Sıfır kullanıcı etkisi. Log:

- Output içeriği (üretime karşı diff).
- Token sayıları (maliyet delta'sı).
- Gecikme.
- Reddetme ve hata.

Yakalar: maliyet patlamaları, uzunluk regresyonları, bariz reddetme değişiklikleri, sert hatalar. YAKALAMAZ: kullanıcının algılayacağı kalite delta'sı. Shadow bir smoke test, kalite testi değil.

### Canary rollout

Gate'lerle progresif trafik kayması. Tipik progresyon: %1 → %10 → %25 → %50 → %75 → %100. Her adımda 5 metrik üzerinde gate:

1. **Gecikme percentile'ları** — P50, P95, P99. İhlal: canary P99 > baseline'ın 1.5x'i.
2. **İstek başına maliyet** — harmanlanmış $. İhlal: baseline'ın %20+'sı.
3. **Hata / reddetme oranı** — 5xx artı açık reddetmeler. İhlal: baseline'ın 2x'i.
4. **Output uzunluk dağılımı** — ortalama + P99. İhlal: dağılımsal kayma.
5. **Kullanıcı-geri bildirim oranı** — thumbs-down / ticket girişleri. İhlal: baseline'ın 1.5x'i.

### Non-determinizm yeni varyans

Özdeş input'lar özdeş olmayan output'lar üretir. Sebepler:

- GPU FP non-associativity (floating-point reduction sırası batch'e göre değişir).
- Batch-boyutu varyansı (128'lik batch'te vs 16'lık batch'te aynı prompt).
- Sampling (temperature > 0).

Ölçülen: özdeş eval set'lerinde çalıştırmalar arası %15'e varan doğruluk varyasyonu. Bir rollout'ta "stabil" demek metriklerin beklenen varyans içinde olması, baseline ile özdeş olması değil. Gate'leri gürültü tabanının üstüne ayarla.

### Maliyet bir değişken

%20 daha iyi bir model çağrı başına 3x daha pahalı olabilir. İstek başına maliyet beş gate'ten biri. Unit economics'i bozan "daha iyi" bir model yayınlamak bir rollback vakası.

### Rollback silah

- Policy flag (feature flag sistemi): config'te yüzdeyi çevir; saniyeler alır.
- Model pin'leme (registry digest'i): pinli model otomatik-yükseltilmez.
- Rollback = flag'i geri al + pinli digest'i öncekine ayarla. Saniyeler, saatler değil.

Stack'in rollback için redeploy gerektiriyorsa, yayınlamadan önce bunu düzelt.

### Tooling

**Argo Rollouts** / **Flagger** — Kubernetes progressive delivery controller'ları. Istio/Linkerd weighted routing ile entegre olur.

**Istio weighted routing** — service-mesh-seviyesi trafik bölme.

**KServe / Seldon Core** — yerleşik canary'li model serving.

**Feature flag'ler** — LaunchDarkly, Flagsmith, Unleash. Policy-seviyesi çevir, redeploy yok.

### Metrik kadansı

Canary gate'leri trafik hacmine bağlı olarak her 5-15 dakikada kontrol eder. Dakikada 10 istekli %1 trafik pencere başına 50-150 veri noktası verir — gecikme için yeterli ama kullanıcı geri bildirimi için gürültülü. %10 ~10x daha fazlasını verir. Progresyonlar her adımda yeterli örnek biriktirmek için yeterince duraklamalı.

### A/B adımı opsiyonel

Yeni model belirgin şekilde farklıysa (farklı davranış, farklı maliyet eğrisi, farklı ton), canary geçtikten sonra %50'de A/B test et. Yalnızca geliştirilmiş bir sürümse, canary gate'leri geçince %100'e atla.

### Hatırlaman gereken sayılar

- Canary progresyonu: %1 → %10 → %25 → %50 → %75 → %100.
- Non-determinizm tavanı: özdeş input'larda çalıştırmalar arası %15'e varan varyans.
- Beş canary metriği: gecikme, maliyet, hata/reddetme, output uzunluğu, kullanıcı geri bildirimi.
- Maliyet gate'i: baseline'ın %20+'sı ihlal.
- Rollback: saniyeler, saatler değil.

## Kullan

`code/main.py` enjekte edilmiş regresyon'larla bir canary rollout simüle eder. Rollout'un hangi aşamada durduğunu ve hangi gate'in tetiklendiğini raporlar.

## Yayınla

Bu ders `outputs/skill-rollout-runbook.md` üretir. Aday model, baseline ve risk toleransı verildiğinde, shadow→canary→%100 planı tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. %25 maliyet regresyonu enjekte et. Canary hangi aşamada durur?
2. Yeni modelin offline %3 doğruluk kazancı var ama istek başına maliyet +%18. Yayınlanır mı? Politikaya bağlı — iki yolu da yaz.
3. End-to-end 60 saniye altında alan bir rollback tasarla. Gereken altyapıyı listele.
4. Non-determinizm eval'inde ±%7 gösteriyor. False-alarm yapmamak için canary gate'lerini ayarla. Hangi çarpanları kullanırsın?
5. Shadow modu canary'den önce %40 maliyet sıçramasını yakalıyor. Shadow'da ateşlenen alert kuralını yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Shadow modu | "yeniye duplike" | Logging için sıfır-etki aday'a-gönder |
| Canary | "progresif trafik" | Gate'lerle kademeli kullanıcı-açık rollout |
| Gate'ler | "rollout kontrolleri" | Progresyonu blokeleyen metrik eşikleri |
| Non-determinizm | "LLM varyansı" | İndirgenemez çalıştırmalar-arası farklar |
| Policy flag | "flag-çevir rollback" | Config-seviyesi rollback, saniyeler değil saatler |
| Model pin | "registry digest'i" | Bir model sürümüne değişmez referans |
| Argo Rollouts | "K8s progresif" | Kubernetes-native canary/rollback controller'ı |
| KServe | "çıkarım K8s" | Canary primitive'leriyle model serving |
| Istio weighted | "mesh bölme" | Service-mesh trafik ayırıcı |

## İleri Okuma

- [TianPan — Releasing AI Features Without Breaking Production](https://tianpan.co/blog/2026-04-09-llm-gradual-rollout-shadow-canary-ab-testing)
- [MarkTechPost — Safely Deploying ML Models](https://www.marktechpost.com/2026/03/21/safely-deploying-ml-models-to-production-four-controlled-strategies-a-b-canary-interleaved-shadow-testing/)
- [APXML — Advanced LLM Deployment Patterns](https://apxml.com/courses/mlops-for-large-models-llmops/chapter-4-llm-deployment-serving-optimization/advanced-llm-deployment-patterns)
- [Argo Rollouts docs](https://argo-rollouts.readthedocs.io/)
- [Flagger docs](https://docs.flagger.app/)
