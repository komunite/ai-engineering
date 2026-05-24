---
name: ai-sre-plan
description: Bir takım için AI SRE rollout'u tasarla — multi-agent triaj mimarisi, yapılandırılmış runbook'lar, adversarial değerlendirme, dar otomatik düzeltme ve predictive-detection tutumu.
version: 1.0.0
phase: 17
lesson: 23
tags: [ai-sre, multi-agent, runbooks, auto-remediation, adversarial-eval, datadog-bits-ai, neubird, predictive]
---

Takım boyutu, incident hacmi, observability olgunluğu ve risk toleransı verildiğinde, bir AI SRE planı üret.

Üret:

1. Mimari. Multi-agent: supervisor + log agent + metric agent + runbook agent + human gate. Uzmanlaşmış agent'ları mevcut veri kaynaklarına eşleştir (Datadog, Grafana, Loki, Confluence).
2. Runbook dönüşümü. Yapılandırılmamış Confluence'tan symptom / hypothesis / verify / act bölümlü yapılandırılmış markdown'a geç. Git'te versiyonla.
3. Ürün seçimi. Datadog Bits AI, Azure SRE Agent, NeuBird Hawkeye, Incident.io Autopilot veya DIY.
4. Otomatik düzeltme kapsamı. Dar güvenli set (pod restart, deploy geri al, sınırlar içinde scale). Açık deny listesi (topoloji, kod, IAM, veritabanı). Kod olarak politika.
5. Adversarial değerlendirme. Otomatik düzeltme için iki-model uzlaşma gate'i belirt. Uzlaşmazlık eskalasyona alınır.
6. Predictive-detection tutumu. Düşünülüyorsa (MIT %89 sonucu), actuation politikasını adlandır — pager, pre-drain, auto-scale — yoksa sadece bir dashboard'tur.

Hard rejects:
- Geniş değişikliklerde human gate olmadan otomatik düzeltme. Reddet — güvenli seti açıkça adlandır.
- Bilgi tabanı olarak yapılandırılmamış runbook'lar. Reddet — yapılandırılmış, versiyonlanmış markdown iste.
- "Kur ve unut" çerçevelemesi. Reddet — neyin otonom olup olmadığını açıkça kapsamla.

Reddetme kuralları:
- Incident hacmi <10/ay ise, tam AI SRE rollout'unu reddet — maliyet faydayı aşar. Yalnızca yapılandırılmış runbook'ları öner.
- Takım observability'si olgun değilse (log'lar aranamaz, metrikler seyrek), reddet — AI SRE kötü veriyi büyütür.
- Takım ilk özellik olarak "predictive detection → otomatik düzeltme" öneriyorsa, reddet — önce actuation-politikası sorusunu yürü.

Çıktı: mimari, runbook planı, ürün seçimi, otomatik düzeltme kapsamı, adversarial gate, predictive tutum içeren tek sayfalık plan. 12 haftalık rollout takvimiyle bitir: hafta 1-4 yapılandırılmış runbook'lar, 5-8 triaj agent, 9-12 dar otomatik düzeltme.
