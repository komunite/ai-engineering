# Eval-Driven Agent Geliştirme

> Anthropic'in rehberi: "basit prompt'larla başla, onları kapsamlı değerlendirmeyle optimize et ve yalnızca gerektiğinde multi-step agentic sistemler ekle." Değerlendirme son adım değil. Faz 14'teki diğer her seçimi yönlendiren dış döngü.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14'ün tamamı.
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Üç değerlendirme katmanını — statik benchmark'lar, custom çevrimdışı, çevrimiçi üretim — ve her birinin ne için olduğunu adlandır.
- Evaluator-optimizer sıkı döngüsünü açıkla.
- 2026 best practice'ini açıkla: eval'ler kodun yanında yaşar, CI'da çalışır, PR'lere kapı koyar.
- Her Faz 14 dersini ürettiği eval case'ine bağla.

## Sorun

Agent'lar demo'ları geçer. Demo'ların tahmin edemediği şekillerde üretimde başarısız olurlar. Benchmark'lar "bu model geniş anlamda yetenekli mi?" sorusunu yanıtlar, "bu agent ürünüm için doğru patch'leri yayınlıyor mu?" sorusunu değil. Yanıt: üç katmanda değerlendirme, sürekli çalışıyor, her guardrail ve öğrenilmiş kural bir eval case'ine eşlenmiş.

## Kavram

### Üç değerlendirme katmanı

1. **Statik benchmark'lar** — kod için SWE-bench Verified (Ders 19), tarama / desktop için WebArena/OSWorld (Ders 20), generalist için GAIA (Ders 19), tool use için BFCL V4 (Ders 06). Cross-model karşılaştırma ve regresyon kapısı için kullan. Kontaminasyon gerçek: SWE-bench+ %32.67 çözüm sızıntısı buldu. Her zaman Verified / +-audited skorlarını raporla.

2. **Custom çevrimdışı eval'ler** — ürününün şekli:
   - LLM-as-judge (Langfuse, Phoenix, Opik — Ders 24).
   - Execution-tabanlı (patch'i çalıştır, testleri kontrol et).
   - Trajectory-tabanlı (aksiyon dizilerini gold'a karşı karşılaştır; OSWorld-Human en iyi agent'ları gold'un 1.4-2.7x üstünde gösteriyor).

3. **Çevrimiçi eval'ler** — üretim:
   - Session replay'leri (Langfuse).
   - Guardrail-tetiklemeli alarm'lar (Ders 16, 21).
   - Per-step maliyet / latency takip (Ders 23 OTel span'leri).

### Evaluator-optimizer (Anthropic)

Sıkı döngü:

1. Öneren çıktı üretir.
2. Evaluator yargılar.
3. Evaluator geçene kadar refine et.

Bu Self-Refine (Ders 05) genelleştirilmiş. Önemsediğin herhangi bir agent akışını güvenilirlik için evaluator-optimizer'a sarabilirsin.

### 2026 best practice

- Eval'ler kodun yanında yaşar.
- Her PR'de CI'da çalışır.
- Merge'u eval skorlarına kapı koy (örn. "main'e karşı > %5 regresyon yok").
- Her guardrail bir eval case'ine eşlenir.
- Her öğrenilmiş kural (Reflexion, pro-workflow learn-rule) bir başarısızlık case'ine eşlenir.

### Faz 14'ü bir araya getirmek

Faz 14'teki her ders eval case'leri üretir:

| Ders | Ürettiği eval case'i |
|--------|------------------------|
| 01 Agent Döngüsü | Budget-tükenmiş, infinite-loop guard |
| 02 ReWOO | Bir tool başarısız olduğunda planner doğru replan eder |
| 03 Reflexion | Öğrenilmiş self-reflection'lar retry'da uygulanır |
| 05 Self-Refine/CRITIC | Judge rafine edilmiş çıktıyı geçer |
| 06 Tool Use | Argüman coercion çalışır; bilinmeyen tool'lar reddedilir |
| 07-10 Bellek | Retrieval citation'ları kaynaklarla eşleşir; bayat olgular invalidate olur |
| 12 Workflow Desenleri | Her desen doğru çıktı üretir |
| 13 LangGraph | Resume state'i tam yeniden üretir |
| 14 AutoGen Actor'ları | DLQ çökmüş handler'ları yakalar |
| 16 OpenAI Agents SDK | Guardrail doğru input'larda tetiklenir |
| 17 Claude Agent SDK | Alt-agent sonuçları orchestrator'a döner |
| 19-20 Benchmark'lar | SWE-bench Verified skoru, WebArena başarı oranı, OSWorld verimliliği |
| 21 Computer Use | Per-step safety enjekte edilmiş DOM'u yakalar |
| 23 OTel | Span'ler gerekli attribute'ları yayar |
| 26 Başarısızlık Modları | Detector'lar bilinen başarısızlıkları etiketler |
| 27 Prompt Injection | PVE zehirli retrieval'leri reddeder |
| 28 Orkestrasyon | Supervisor doğru uzmana route eder |
| 29 Runtime Şekilleri | DLQ %N başarısızlığı işler |

Eval suite'inin her biri için case'leri varsa, Faz 14'ü kapsadın.

### Eval-driven geliştirme nerede başarısız olur

- **Baseline yok.** Last-known-good'sız eval'ler okunamaz. Baseline'ları sakla.
- **Topraklamasız LLM-judge.** Judge'lar da halüsine eder. CRITIC deseni (Ders 05) — judge dış tool'larda topraklanır.
- **Eval'lere overfit etmek.** Eval için optimize etmek üretim faydasından ayrılır. Case'leri rotate et.
- **Aksak eval'ler.** Non-deterministic case'ler false alarm'lara neden olur. Seed'leri sabitle, state snapshot al.

## İnşa Et

`code/main.py` bir stdlib eval harness:

- Kategorili case registry (benchmark, custom, online).
- Test altındaki scripted bir agent.
- Evaluator-optimizer döngüsü: öner, yargıla, geçene ya da maks tur'a kadar refine.
- CI kapısı: baseline'a karşı agregat geçiş oranı + regresyon.

Çalıştır:

```
python3 code/main.py
```

Çıktı: case başına pass/fail, regresyon flag, CI kapısı verdict.

## Kullan

- Eval case'lerini agent kodunla aynı repo'ya yaz.
- Her PR'de CI üzerinden çalıştır.
- Regresyonda build'i başarısız et.
- Geçiş oranını zaman üzerinde takip et.
- Her üretim başarısızlığını yeni bir case'e bağla.

## Yayınla

`outputs/skill-eval-suite.md` bir agent ürünü için CI kapıları ve regresyon takibi ile üç-katmanlı eval suite kurar.

## Alıştırmalar

1. Üretim başarısızlıklarından birini al. Onu yeniden üreten bir eval case yaz. Agent'ın şimdi geçiyor mu?
2. Domain'in için üç boyutlu (factual, ton, scope) bir LLM-judge rubric'i kur. 50 oturumu puanla.
3. Eval suite'ini CI'a kabloala. >=%5 regresyonda build'i başarısız et.
4. Bir trajectory-verimlilik metriği ekle: agent gold trajectory'ye karşı kaç adım attı?
5. Faz 14'teki her dersi suite'indeki bir eval case'ine eşle. Eksik var mı? Bu kapatılacak bir boşluk.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Statik benchmark | "Off-the-shelf eval" | SWE-bench, GAIA, AgentBench, WebArena, OSWorld |
| Custom çevrimdışı eval | "Domain eval" | Ürün şeklinde LLM-as-judge / exec / trajectory |
| Çevrimiçi eval | "Üretim eval" | Session replay, guardrail alarmları, maliyet/latency takip |
| Evaluator-optimizer | "Öner-yargıla-refine" | Judge geçene kadar iterate et |
| CI kapısı | "Merge blocker" | Eval regresyonunda build'i başarısız et |
| Baseline | "Last-known-good" | Regresyon tespit etmek için referans skor |
| Trajectory verimliliği | "Gold üzerinde adımlar" | Agent adım sayısı bölü insan uzman minimum |

## İleri Okuma

- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — "basit başla, eval'lerle optimize et"
- [OpenAI, SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) — küratörlü benchmark
- [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) — tool-use benchmark
- [Langfuse docs](https://langfuse.com/) — pratikte eval'ler + session replay
