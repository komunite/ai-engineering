# Self-Refine ve CRITIC: İteratif Çıktı İyileştirme

> Self-Refine (Madaan et al., 2023) bir LLM'i üç rolde — generate, feedback, refine — bir döngüde kullanır. Ortalama kazanç: 7 görevde +20 mutlak. CRITIC (Gou et al., 2023) doğrulamayı dış tool'lara yönlendirerek feedback adımını sertleştirir. 2026'da bu desen her framework'te "evaluator-optimizer" (Anthropic) ya da bir guardrail döngüsü (OpenAI Agents SDK) olarak yayılıyor.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 03 (Reflexion)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Self-Refine'ın üç prompt'unu (generate, feedback, refine) belirt ve refine prompt'u için geçmişin neden önemli olduğunu açıkla.
- CRITIC'in kritik içgörüsünü açıkla: LLM'ler dış topraklama olmadan self-verification'da güvenilmez.
- Geçmiş ve opsiyonel dış doğrulayıcı ile bir stdlib Self-Refine döngüsü uygula.
- Bu deseni Anthropic'in "evaluator-optimizer" workflow'una ve OpenAI Agents SDK'nın output guardrail'lerine eşle.

## Sorun

Bir agent neredeyse doğru olan bir yanıt üretiyor. Belki bir kod satırının syntax hatası var. Belki bir özet çok uzun. Belki bir plan edge case'i kaçırıyor. İstediğin şey: agent kendi çıktısını eleştiriyor, sonra düzeltiyor.

Self-Refine bunun tek modelle, eğitim verisi olmadan, RL olmadan çalıştığını gösteriyor. Ama bir tuzak var: LLM'ler zor olgularda self-verification'da kötü. CRITIC çözümü adlandırıyor — doğrulama adımını dış tool'lara (search, code interpreter, calculator, test runner) yönlendir.

Bu iki makale birlikte iteratif iyileştirme için 2026 varsayılanını tanımlıyor: üret, doğrula (mümkünse dışsal), iyileştir, doğrulayıcı geçtiğinde dur.

## Kavram

### Self-Refine (Madaan et al., NeurIPS 2023)

Bir LLM, üç rol:

```
generate(task)            -> output_0
feedback(task, output_0)  -> critique_0
refine(task, output_0, critique_0, history) -> output_1
feedback(task, output_1)  -> critique_1
refine(task, output_1, critique_1, history) -> output_2
...
feedback "sorun yok" derse ya da bütçe tükendiğinde dur.
```

Önemli detay: `refine` tüm geçmişi görür — tüm önceki çıktılar ve eleştiriler — böylece hataları tekrarlamaz. Makale bunu ablate eder: geçmişi at ve kalite keskin düşer.

Başlık: GPT-4 dahil 7 görev (matematik, kod, akronim, dialog) genelinde ortalama +20 mutlak iyileştirme. Eğitim yok, dış tool yok, tek model.

### CRITIC (Gou et al., arXiv:2305.11738, v4 Şubat 2024)

Self-Refine'ın zayıflığı: feedback adımı kendini puanlayan bir LLM. Olgusal iddialar için bu güvenilmez (bir halüsinasyon onu üreten modele genellikle ikna edici görünür). CRITIC, `feedback(task, output)`'u `verify(task, output, tools)` ile değiştirir; burada `tools` şunları içerir:

- Olgusal iddialar için bir arama motoru.
- Kod doğruluğu için bir code interpreter.
- Aritmetik için bir calculator.
- Domain'e özel doğrulayıcılar (unit testler, type checker'lar, linter'lar).

Doğrulayıcı, tool sonuçlarında toprakla(n)mış yapılandırılmış bir eleştiri üretir. Refiner sonra bu eleştiriye koşullanır.

Başlık: Eleştiri topraklanmış olduğu için CRITIC olgusal görevlerde Self-Refine'ın üzerine çıkar. Dış doğrulayıcı olmayan görevlerde (yaratıcı yazı, formatlama) CRITIC Self-Refine'a indirgenir.

### Durdurma koşulu

İki yaygın şekil:

1. **Doğrulayıcı geçer.** Dış test başarı döndürür. Mevcutsa tercih edilir (unit testler, type checker, guardrail iddiası).
2. **Feedback verilmez.** Model "çıktı iyi" der. Daha ucuz ama güvenilmez; bir maks-iterasyon tavanı ile eşleştir.

2026 varsayılan: bunları birleştir. "Doğrulayıcı geçerse VEYA model iyi derse VE iterasyonlar >= 2 VEYA iterasyonlar >= max_iterations ise dur."

### Evaluator-Optimizer (Anthropic, 2024)

Anthropic'in Aralık 2024 yazısı bunu beş workflow desenden biri olarak adlandırıyor. İki rol:

- Evaluator: çıktıyı puanlar ve bir eleştiri üretir.
- Optimizer: eleştiriyi verildiğinde çıktıyı revize eder.

Evaluator geçene kadar döngü. Bu, Anthropic'in çerçevesindeki Self-Refine/CRITIC. Anthropic'in eklediği kritik mühendislik detayı: evaluator ve optimizer prompt'ları önemli ölçüde farklı olmalı, böylece model sadece onay damgası vurmaz.

### OpenAI Agents SDK output guardrails

OpenAI Agents SDK bu deseni "output guardrails" olarak yayınlıyor. Bir guardrail, bir agent'ın nihai çıktısında çalışan bir doğrulayıcı. Guardrail tetiklenirse (`OutputGuardrailTripwireTriggered` raise eder), çıktı reddedilir ve agent yeniden deneyebilir. Guardrail'ler tool çağırabilir (CRITIC-tarzı) ya da saf fonksiyon olabilir (Self-Refine-tarzı).

### 2026 tuzakları

- **Onay-damgası döngüleri.** Aynı model aynı prompt stiliyle hem üretim hem eleştiri yapınca "bana iyi göründü"de yakınsar. Yapısal olarak farklı prompt'lar kullan ya da eleştiri için daha küçük ucuz bir model.
- **Aşırı-iyileştirme.** Her refine geçişi latency ve token ekler. 1-3 geçiş bütçele; ondan sonra insan incelemesine yükselt.
- **Önemsiz görevlerde CRITIC.** Dış doğrulayıcı yoksa, CRITIC Self-Refine'a dejenere olur; bir stub doğrulayıcı için latency ödeme.

## İnşa Et

`code/main.py` Self-Refine ve CRITIC'i bir oyuncak görev üzerinde uyguluyor: verilen bir konuda kısa bir madde işaretli liste üret. Doğrulayıcı format'ı kontrol eder (3 madde, her biri 60 karakter altında). CRITIC, bilinen halüsinasyonları cezalandıran bir dış "fact verifier" ekler.

Bileşenler:

- `generate` — scripted üretici.
- `feedback` — LLM-tarzı self-critique.
- `verify_external` — CRITIC-tarzı topraklanmış doğrulayıcı.
- `refine` — geçmiş verildiğinde çıktıyı yeniden yazar.
- Durdurma koşulu — doğrulayıcı geçer ya da maks 4 iterasyon.

Çalıştır:

```
python3 code/main.py
```

Self-Refine vs CRITIC koşularını karşılaştır. CRITIC, Self-Refine'ın kaçırdığı bir olgusal hatayı yakalar çünkü dış doğrulayıcının self-critic'in sahip olmadığı bir topraklaması var.

## Kullan

Anthropic'in evaluator-optimizer'ı bu desenin Claude-dostu dilinde hali. OpenAI Agents SDK'nın output guardrails'i CRITIC-şekilli (guardrail'ler tool çağırabilir). LangGraph Self-Refine gibi okunan bir reflection node'u yayar. Google'ın Gemini 2.5 Computer Use'u CRITIC varyantı bir per-step safety evaluator ekler: her aksiyon commit'ten önce doğrulanır.

## Yayınla

`outputs/skill-refine-loop.md` görev şekli, doğrulayıcı varlığı ve iterasyon bütçesi verildiğinde bir evaluator-optimizer döngüsü yapılandırır. Generator, evaluator/verifier ve optimizer için prompt'lar ve bir durdurma policy'si yayar.

## Alıştırmalar

1. Oyuncağı max_iterations=1 ile çalıştır. CRITIC hâlâ yardım eder mi?
2. Dış doğrulayıcıyı gürültülü olanla değiştir (rastgele %30 false positive). Döngü ne yapar? Çoğu guardrail stack'inin 2026 gerçeği bu.
3. "Generator-critic farklı modellerde" varyantı uygula: büyük model üretir, küçük model eleştirir. Aynı-model'i yener mi?
4. CRITIC Bölüm 3'ü (arXiv:2305.11738 v4) oku. Üç doğrulama-tool kategorisini adlandır ve her biri için bir örnek ver.
5. OpenAI Agents SDK'nın `output_guardrails`'ini CRITIC'in doğrulayıcı rolüne eşle. SDK ne yanlış yapıyor ve ne doğru yapıyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Self-Refine | "Kendini düzelten LLM" | Geçmişli, tek modelde generate -> feedback -> refine döngüsü |
| CRITIC | "Tool-topraklanmış doğrulama" | Feedback'i dış doğrulayıcıyla (search, code, calc, testler) değiştir |
| Evaluator-Optimizer | "Anthropic workflow deseni" | İki rol — evaluator puanlar, optimizer revize eder — yakınsamaya kadar döngü |
| Output guardrail | "Post-hoc check" | Bir agent çıktı ürettikten sonra çalışan OpenAI Agents SDK doğrulayıcısı |
| Doğrulama adımı | "Eleştiri fazı" | Taşıyıcı karar: topraklanmış ya da self-rated |
| Refine geçmişi | "Modelin zaten denediği" | Önceki çıktılar + eleştiriler refine prompt'una öne eklenir; at ve kalite çöker |
| Onay-damgası döngüsü | "Self-agreement başarısızlığı" | Aynı-prompt eleştiri "iyi görünüyor" döndürür; yapısal olarak farklı prompt'larla düzelt |
| Durdurma koşulu | "Yakınsama testi" | Doğrulayıcı geçer VEYA feedback yok VE iterasyon tavanı; asla tek-koşul değil |

## İleri Okuma

- [Madaan et al., Self-Refine (arXiv:2303.17651)](https://arxiv.org/abs/2303.17651) — kanonik makale
- [Gou et al., CRITIC (arXiv:2305.11738)](https://arxiv.org/abs/2305.11738) — tool-topraklanmış doğrulama
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — evaluator-optimizer workflow deseni
- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) — CRITIC-şekilli doğrulayıcı olarak output guardrails
