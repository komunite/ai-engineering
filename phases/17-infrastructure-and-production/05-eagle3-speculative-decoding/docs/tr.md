# Üretimde EAGLE-3 Speculative Decoding

> Speculative decoding hızlı bir draft modeli hedef modelle eşleştirir. Draft K token önerir; hedef tek bir forward'da doğrular; kabul edilen token'lar bedavadır. 2026'da EAGLE-3 üretim-sınıfı varyant — draft head'i ham token'lar yerine hedef modelin gizli durumları üzerinde eğitir, genel sohbette acceptance rate alpha'yı 0.6-0.8 bandına çıkarır. Doğru soru "draft ne kadar hızlı" değil, "trafiğimde alpha kaç?" sorusu. Alpha ~0.55'in altına düşerse, yüksek eşzamanlılıkta speculative decoding net negatiftir çünkü her reddedilen draft ikinci bir hedef forward pass'i maliyetler. Bu ders sana önce alpha'yı ölçmeyi, sonra flag'i çevirmeyi öğretir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak acceptance-rate simülatörü)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 10 · 18 (Multi-Token Prediction)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Speculative decoding'in üç jenerasyonunu adlandır ve EAGLE-3'ün EAGLE-2'den ve klasik bir draft modelinden neyi değiştirdiğini açıkla.
- Acceptance rate alpha'yı tanımla, alpha ve K (draft uzunluğu) üzerinden beklenen speedup'ı hesapla ve hedef eşzamanlılığın için break-even alpha'yı tanımla.
- 2026 vLLM'de speculative decoding'in neden opt-in (varsayılan değil) olduğunu ve alpha'yı ölçmeden açmanın neden üretim anti-pattern'i olduğunu açıkla.
- Bir ölçüm planı yaz: hangi benchmark, hangi prompt dağılımı, hangi eşzamanlılık noktası, hangi metriği gate olarak kullanacaksın.

## Sorun

Decode bellek-bağlı. Llama 3.3 70B FP8 çalıştıran bir H100'de, her decode edilen token ~140 GB/s ağırlık okur ve bir token yayar. Decode sırasında GPU compute neredeyse boşta — bottleneck matmul throughput'u değil, HBM bant genişliği.

Speculative decoding farkı sömürür. Ucuz bir draft modelle K aday token üret, sonra hedef modelden tüm K'yı tek bir forward pass'te doğrulamasını iste. Her doğrulanan token efektif olarak bedavadır (hedef yine de yapmak zorunda olduğu bir batch-of-K forward'a amortize edilir).

Klasik draft-model yaklaşımı aynı ailedeki daha küçük bir model kullanır (Llama 3.3 70B için draft eden Llama 3.2 1B). Çalışıyor ama acceptance rate orta — daha küçük modelin dağılımı hedeften sapıyor. EAGLE, sonra EAGLE-2, sonra EAGLE-3 hafif bir draft head'i doğrudan hedef modelin iç durumları üzerinde eğitir, böylece draft'ın dağılımı hedefi çok daha yakından izler. İşte bu yüzden alpha draft-model ile 0.4'ten EAGLE-3 ile 0.6-0.8'e çıkar.

Püf nokta: EAGLE-3 2026 vLLM'inde opt-in. `speculative_config` açıkça ayarlanmalı. Flag yok, hızlanma yok. Gerçek trafiğinde alpha'yı ölçmeden açan takımlar çoğu zaman kuyruk gecikmesinin daha iyiye değil, daha kötüye gittiğini görür.

## Kavram

### Speculative decoding gerçekte ne alır

Spec decode olmadan, token başına maliyet bir hedef forward'dır. K draft uzunluğunda ve alpha acceptance ile spec decode'da, hedef forward başına beklenen token `1 + K * alpha`'dır. Speedup `(1 + K * alpha) / (1 + epsilon)`'dur ve epsilon draft-artı-doğrulama overhead'i. K=5, alpha=0.7 için: `(1 + 5*0.7) / (1 + 0.1) = 4.5 / 1.1 = 4.1x`. Gerçek dünya sayıları 2-3x civarında kümeleniyor çünkü alpha üretim trafiğinde nadiren bu kadar yüksek ve epsilon yüksek batch boyutunda büyür.

### Neden alpha önemli olan tek metrik

Reddedilen token'lar yok olmaz — ilk reddedilen token için ikinci bir hedef forward'ı zorlar. Alpha'nın 0.4'e düştüğü bir iş yükünde, draft overhead artı doğrulama artı re-roll ödersin. Yüksek eşzamanlılıkta (örneğin 256 eşzamanlı), decode batch'i zaten yeterince büyük ki "tek başına hedef" ile "doğrulamalı hedef" arasındaki bellek-bant genişliği farkı küçülür. Çoğu 2026 donanımında alpha 0.55'in altında, spec decode net negatif.

Alpha iş yüküne göre değişir. ShareGPT-tarzı genel sohbette, ShareGPT üzerinde eğitilen EAGLE-3 0.6-0.8'e ulaşır. Alana-özel trafikte (kod, tıp, hukuk) genel veri üzerinde eğitilen draft head 0.4-0.6'ya düşer. Alana-özel bir draft head eğitmek alpha'yı geri kazanır — hedef finetuning ile karşılaştırıldığında hafif, hızlı bir eğitim job'u.

### Bir bakışta EAGLE jenerasyonları

- **Klasik draft modeli**: aynı ailenin küçük modeli. Alpha 0.3-0.5. Altyapı basit — iki model yüklü, draft hedef forward başına K forward çalıştırır.
- **EAGLE-1 (2024)**: hedef gizli durumları (son katman) üzerinde eğitilmiş tek draft head. Alpha ~0.5-0.6. Hedefin üstünde küçük param overhead.
- **EAGLE-2 (2025)**: adaptif draft uzunluğu ve ağaç-tabanlı draft'lar (tek hedef pass'te birden fazla dal doğrula). Alpha ~0.6-0.7. Daha karmaşık draft scheduler.
- **EAGLE-3 (2025-2026)**: birden fazla hedef katman üzerinde eğitilmiş draft head (yalnız son değil), daha iyi alignment. Genel sohbette alpha ~0.6-0.8.

### 2026 üretim tarifi

1. Hedef modeli sade yayınla. Hedef eşzamanlılıkta baseline TTFT, ITL, throughput'u ölç.
2. EAGLE-3 draft'ını vLLM `speculative_config` üzerinden etkinleştir. Benchmark'ı yeniden çalıştır.
3. Acceptance rate alpha'yı logla. vLLM V1 bunu `spec_decode_metrics.accepted_tokens_per_request` olarak raporlar. Alpha'yı almak için talep edilen draft uzunluğuna böl.
4. Üretim trafik dağılımında alpha < 0.55 ise, spec decode'u devre dışı bırak ya da alana-özel bir EAGLE-3 draft eğit.
5. Üretim eşzamanlılığında yeniden çalıştır. P99 ITL'in kötüleşmediğini doğrula.

### Üretim tuzağı: P99 kuyruk

Ortalama ITL spec decode ile düşer. Ayarlamazsan P99 kötüleşebilir. Reddedilen draft'lar iki-pass'lik bir sequence (draft + verify-fail + reroll) tetikler. Tam batch altında, o iki pass serileşir. P50'yi değil P99 ITL'i izle.

### EAGLE-3 nerede zaten deploy edildi

Google 2025'te AI Overviews'da speculative decoding deploy etti (aynı kalite, daha hızlı yanıt). vLLM V1 `speculative_config`'i belgelenmiş arayüz olarak yayınlar; V1'deki N-gram GPU speculative decoding chunked prefill ile uyumlu varyanttır. SGLang prefix-ağırlıklı iş yükleri için önerilen draft yolu olarak EAGLE-3'ü destekler.

### Tek satırda break-even matematiği

Beklenen speedup: `S(alpha, K) = (1 + K*alpha) / (1 + verify_overhead)`. `S = 1` koyarak alpha için çözersek: `alpha_breakeven = verify_overhead / K`. Tipik verify_overhead ~0.15 ve K=5 için: `alpha_breakeven = 0.03`. Ama bu ham decode matematiği. Yüksek eşzamanlılıkta verify overhead yükselir ve decode batch'i zaten sequence'ler arasında bellek okumalarını amortize eder, dolayısıyla pratikte etkin alpha_breakeven ~0.45-0.55'e tırmanır.

### Speculative decoding ne zaman kullanılmaz

- Gecikmenin önemli olmadığı batch-1 offline üretim. Düz hedef kullan.
- Çok kısa output'lar (50 token altı). Draft overhead ve doğrulama maliyeti domine eder.
- Alan-eğitimli draft head'i olmayan özel alanlar. Alpha çok düşük.
- vLLM v0.18.0 artı draft-model spec decode artı `--enable-chunked-prefill`. Bu kombinasyon compile etmez. Belgelenmiş istisna V1'deki N-gram GPU spec decode.

## Kullan

`code/main.py` bir aralık alpha değeri ve K draft uzunluğu üzerinde speculative decoding'li ve onsuz bir decode loop'u simüle eder. Break-even alpha'yı, ölçülen speedup'ı ve kuyruk davranışını yazdırır. Birkaç (alpha, K) kombinasyonunda çalıştır ve speculative decoding'in tam olarak nerede ödemeyi durdurduğunu gör.

## Yayınla

Bu ders `outputs/skill-eagle3-rollout.md` üretir. Bir hedef model, trafik dağılımı tanımı ve eşzamanlılık hedefi verildiğinde, kademeli bir EAGLE-3 rollout planı üretir — benchmark baseline, config etkinleştir, alpha'yı ölç, alpha >= 0.55'i gate olarak kullan, P99 ITL'i izle.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. K=5'te 2x speedup için hangi alpha gerek? 3x speedup için? Bu verify_overhead'e ne kadar hassas?
2. Üretim trafiğinin %70 genel sohbet, %30 kod olarak bölündüğünü hayal et. Genel sohbet ShareGPT üzerinde eğitilmiş EAGLE-3 ile alpha 0.7'ye ulaşıyor; kod 0.4'e ulaşıyor. Karışık alpha kaç ve spec decode net-pozitif mi?
3. vLLM `speculative_config` dokümantasyonunu oku. Üç modu adlandır (draft model, EAGLE, N-gram) ve hangisi chunked prefill ile uyumlu.
4. EAGLE-3'ü etkinleştirdikten sonra ortalama ITL'in %25 düştüğünü görüyorsun ama P99 ITL %15 yükselmiş. Teşhis et ve bir mitigasyon öner.
5. Llama 3.3 70B için EAGLE-3 draft head'inin bellek maliyetini hesapla. Klasik draft olarak Llama 3.2 1B çalıştırmakla nasıl karşılaştırır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Speculative decoding | "draft artı doğrula" | Ucuz bir modelle K token öner, hepsini tek hedef forward'da doğrula |
| Acceptance rate alpha | "spec accept oranı" | Hedef tarafından kabul edilen draft token'larının fraksiyonu; önemli olan tek metrik |
| Draft uzunluğu K | "spec k" | Draft'ın hedef forward başına önerdiği token sayısı; tipik 4-8 |
| Verify overhead epsilon | "spec overhead" | Düz hedef forward'a karşı doğrula-ve-reroll'ün ekstra maliyeti; batch ile büyür |
| EAGLE-3 | "en yeni EAGLE" | 2025-2026 varyantı; draft head'i birden fazla hedef katmanda eğitir; genel sohbette alpha 0.6-0.8 |
| `speculative_config` | "vLLM spec config" | vLLM V1'de açık opt-in; varsayılan yok demek hızlanma yok demek |
| N-gram spec decode | "N-gram draft" | Prompt'ta N-gram lookup'ları kullanan GPU-tarafı draft; chunked-prefill-uyumlu |
| Break-even alpha | "no-op alpha" | Spec decode'un sıfır speedup verdiği alpha; üretim eşzamanlılığında izle |
| Rejected-draft two-pass | "reroll maliyeti" | Draft'lar reddedildiğinde iki hedef forward; P99 kuyruğunu sürükler |

## İleri Okuma

- [vLLM — Speculative Decoding docs](https://docs.vllm.ai/en/latest/features/spec_decode/) — V1'de `speculative_config` ve chunked-prefill uyumluluğu üzerine yetkili kaynak.
- [vLLM Speculative Config API](https://docs.vllm.ai/en/latest/api/vllm/config/speculative/) — tam alan kümesi.
- [EAGLE paper (arXiv:2401.15077)](https://arxiv.org/abs/2401.15077) — orijinal EAGLE draft-head formülasyonu.
- [EAGLE-2 paper (arXiv:2406.16858)](https://arxiv.org/abs/2406.16858) — adaptif draft'lar ve ağaçlar.
- [UC Berkeley EECS-2025-224](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-224.html) — speculative decoding ile verimli LLM sistemi.
- [BentoML — Speculative Decoding](https://bentoml.com/llm/inference-optimization/speculative-decoding) — üretim rollout checklist'i.
