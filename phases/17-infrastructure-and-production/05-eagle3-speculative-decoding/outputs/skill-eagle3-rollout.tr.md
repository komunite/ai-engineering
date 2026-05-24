---
name: eagle3-rollout
description: Ship etmeden önce gerçek trafikte kabul oranı alfa'yı ölçen aşamalı bir EAGLE-3 speculative-decoding rollout planı üret.
version: 1.0.0
phase: 17
lesson: 05
tags: [speculative-decoding, eagle-3, vllm, alpha, production-rollout]
---

Hedef model, hardware (GPU tipi ve sayısı), trafik açıklaması (genel sohbet / kod / uzmanlaşmış), eşzamanlılık hedefi ve mevcut baseline metrikleri (TTFT, ITL, throughput) verildiğinde, aşamalı bir EAGLE-3 rollout planı üret.

Üret:

1. Baseline ölçüm planı. Hangi benchmark (LLMPerf, GenAI-Perf veya üretim shadow), hangi prompt dağılımı, hangi eşzamanlılık noktası, hangi metrikler kaydedilecek (TTFT ortalama/P99, ITL ortalama/P99, throughput, eşzamanlılık).
2. Draft-head seçimi. Genel sohbet için ShareGPT-trained EAGLE-3. Uzmanlaşmış trafik (kod, tıbbi, hukuki) için domain-trained EAGLE-3, veya ship etmeden önce bir tane eğitme kararı.
3. Config. Tam vLLM `speculative_config` alanları (method, model, num_speculative_tokens). v0.18.0 uyumluluğunu not et: draft-model speculation `--enable-chunked-prefill` ile birleşemez; V1'de N-gram GPU spec decode istisnadır.
4. Alfa eşiği. Üretim eşzamanlılığında hedef alpha >= 0.55. Ölçüm prosedürü: 24 saat shadow trafik, vLLM `spec_decode_metrics`'ı logla, kabul edilen token'ları talep edilen draft uzunluğuna böl. Herhangi bir 1 saatlik pencerede alfa 0.45 altına düşerse kill switch.
5. Tail gözetimi. P99 ITL delta'sını çiz (spec on - spec off). Delta pozitifse, reddedilmiş-draft iki-pass pattern'i ısırıyor. K'yı düşür veya bu iş yükünde devre dışı bırak.
6. Başabaş kontrolü. Raporlanan eşzamanlılıkta, mevcut verify overhead için başabaş alfasını hesapla. Yalnızca ölçülen alfa başabaşı en az 0.1 geçtiğinde ship et.

Hard rejects:
- Üretim trafiğinde alfa ölçmeden ship etmek. Reddet ve 24 saatlik shadow ölçüm iste.
- Ölçülen alfayı adlandırmadan 2-3x hızlanma iddia etmek.
- Latency'nin kısıt olmadığı offline batch işleri için speculative decoding etkinleştirmek.
- vLLM v0.18.0'da draft-model speculation'ı chunked prefill ile birleştirmek. Hard incompatibility.

Reddetme kuralları:
- Trafik çoğunlukla çok kısa çıktılarsa (ortalama 50 token altı), reddet. Draft overhead'i baskın; plain target ship et.
- Hardware tüketici sınıfıysa (RTX 4090 / 5090) ve batch size 8 altında kalıyorsa, plain target öner — verify overhead'in batch-amortizasyonu hardware'in sağlayamayacağı eşzamanlılık gerektirir.
- Kullanıcı bir ölçüm döngüsü olmadan K'nın auto-tune'unu isterse, reddet. K, ölçülen alfa artı verify overhead'ten seçilir; hiçbir auto-tune ölçümün yerini almaz.

Çıktı: baseline → config → alfa eşiği → tail gözetimi → başabaş onayını listeleyen tek sayfalık aşamalı rollout planı. Teşhise göre domain-spesifik EAGLE-3 eğitimi, daha düşük K veya plain target'a dönüşten birini adlandıran bir "sırada neyi ölç" paragrafıyla bitir.
