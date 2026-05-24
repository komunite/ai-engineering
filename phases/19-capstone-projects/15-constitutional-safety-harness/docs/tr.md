# Capstone 15 — Constitutional Safety Harness + Red-Team Range

> Anthropic'in Constitutional Classifier'ları, Meta'nın Llama Guard 4'ü, Google'ın ShieldGemma-2'si, NVIDIA'nın Nemotron 3 Content Safety'si ve multilingual kapsam için X-Guard 2026 safety-classifier stack'ini tanımladı. garak, PyRIT, NVIDIA Aegis ve promptfoo standart adversarial değerlendirme araçları oldu. NeMo Guardrails v0.12 onları bir üretim pipeline'ına bağlıyor. Bu capstone hepsini bir araya bağlıyor: hedef bir uygulama etrafında katmanlı bir safety harness, 6+ saldırı ailesi çalıştıran otonom bir red-team agent'ı ve ölçülebilir bir harmlessness delta'sı üreten bir constitutional self-critique koşusu.

**Tür:** Bitirme
**Diller:** Python (safety pipeline, red team), YAML (policy config'leri)
**Ön koşullar:** Faz 10 (LLM'ler sıfırdan), Faz 11 (LLM engineering), Faz 13 (tools), Faz 14 (agent'lar), Faz 18 (ethics, safety, alignment)
**Egzersize edilen fazlar:** P10 · P11 · P13 · P14 · P18
**Süre:** 25 saat

## Sorun

2026'da LLM safety frontier'ı sınıflandırıcıların çalışıp çalışmadığı değil (kabaca çalışıyorlar), bunları over-refusing yapmadan veya bariz delikler bırakmadan bir üretim uygulaması etrafında nasıl doğru compose edileceği. Llama Guard 4 İngilizce policy ihlallerini yönetir. X-Guard (132 dil) multilingual jailbreak'i yönetir. ShieldGemma-2 image-tabanlı prompt injection'ı yakalar. NVIDIA Nemotron 3 Content Safety enterprise kategorilerini kapsar. Anthropic'in Constitutional Classifier'ları training sırasında kullanılan ayrı bir yaklaşım, serving değil.

Saldırı evolution'ı da önemli. PAIR ve TAP jailbreak keşfini otomatize eder. GCG gradient-tabanlı suffix saldırıları çalıştırır. Multi-turn ve code-switch saldırıları agent memory'sini exploit eder. Deploy edilmiş herhangi bir LLM'in bir red-team range'ine — garak ve PyRIT kanonik sürücüler — artı belgelenmiş mitigation'lara ve CVSS-skorlu findings'e ihtiyacı var.

Hedef bir uygulamayı (ya bir 8B instruction-tuned model ya da diğer capstone'lardan biri olan RAG chatbot'lardan biri) sertleştireceksin, ona karşı 6+ saldırı ailesi çalıştıracaksın ve bir önce/sonra harmlessness ölçümü üreteceksin.

## Kavram

Safety pipeline'ının beş katmanı var. **Input sanitize**: zero-width char'ları strip et, base64/rot13 decode et, Unicode normalize et. **Policy katmanı**: NeMo Guardrails v0.12 rail'leri (off-domain, toxicity, PII çıkarma). **Sınıflandırıcı gate'i**: input'ta Llama Guard 4, non-English'te X-Guard, image input'ta ShieldGemma-2. **Model**: target LLM. **Output filter**: output'ta Llama Guard 4, Presidio PII scrub, uygulanabilir olduğunda citation enforcement. **HITL tier'ı**: yüksek-riskli flag'li çıktılar bir Slack queue'una gider.

Red-team range'i bir scheduler'da çalışır. PAIR ve TAP otonom olarak jailbreak'leri keşfeder. GCG gradient-tabanlı suffix saldırıları çalıştırır. ASCII / base64 / rot13 encoding saldırıları. Multi-turn saldırılar (persona adoption, memory exploitation). Code-switch saldırıları (İngilizce'yi Swahili veya Tay ile karıştır). Her koşu CVSS skorlama ve disclosure timeline'ı ile yapılı bir findings dosyası üretir.

Constitutional-self-critique koşusu bir training-time müdahalesi. 1k zararlı-deneme prompt al, model bir yanıt taslağı çizsin, onu yazılı bir constitution'a (do-not-harm kuralları) karşı eleştirsin ve critique loop'unda yeniden eğit. Holdout eval'de önce/sonra harmlessness delta'sını ölç.

## Mimari

```
istek (text / image / multilingual)
      |
      v
input sanitize (zero-width strip, decode, normalize)
      |
      v
NeMo Guardrails v0.12 rail'leri (off-domain, policy)
      |
      v
sınıflandırıcı gate'i:
  Llama Guard 4 (İngilizce)
  X-Guard (multilingual, 132 dil)
  ShieldGemma-2 (image prompt'ları)
  Nemotron 3 Content Safety (enterprise)
      |
      v (izinli)
target LLM
      |
      v
output filter: Llama Guard 4 + Presidio PII + citation check
      |
      v
flag'li çıktılar için HITL tier'ı

paralel:
  red-team scheduler
    -> garak (klasik saldırılar)
    -> PyRIT (orkestre edilmiş red team)
    -> otonom jailbreak agent'ı (PAIR + TAP)
    -> GCG suffix saldırıları
    -> multilingual / code-switch
    -> multi-turn persona adoption

çıktı: CVSS-skorlu findings + disclosure timeline + önce/sonra harmlessness delta
```

## Stack

- Safety sınıflandırıcılar: Llama Guard 4, ShieldGemma-2, NVIDIA Nemotron 3 Content Safety, X-Guard
- Guardrail framework'ü: NeMo Guardrails v0.12 + OPA
- Red-team sürücüleri: garak (NVIDIA), PyRIT (Microsoft Azure), NVIDIA Aegis, promptfoo
- Jailbreak agent'ları: PAIR (Chao et al., 2023), Tree-of-Attacks (TAP), GCG suffix
- Constitutional training: Anthropic-tarzı self-critique loop + critique'lerde SFT
- PII scrub: Presidio
- Target: bir 8B instruction-tuned model veya diğer capstone'ların RAG chatbot'larından biri

## İnşa Et

1. **Target kurulumu.** vLLM'de bir 8B instruction-tuned model ayağa kaldır (veya başka bir capstone'dan RAG chatbot'unu yeniden kullan). Bu test altındaki uygulama.

2. **Safety pipeline wrap'i.** Beş-katmanlı pipeline'ı target etrafında bağla. Her katmanın bireysel olarak gözlemlenebilir olduğunu doğrula (Langfuse'ta katman başına span).

3. **Sınıflandırıcı kapsamı.** Llama Guard 4'ü, X-Guard'ı (multilingual), ShieldGemma-2'yi (image) yükle. Baseline'ları belirlemek için her birini küçük etiketli bir set'te çalıştır.

4. **Red-team scheduler.** garak, PyRIT, bir PAIR agent'ı, bir TAP agent'ı, bir GCG runner'ı, multi-turn bir saldırgan ve bir code-switch saldırganı schedule et. Her biri ayrı bir kuyrukta çalışır.

5. **Saldırı suite'i.** Altı saldırı ailesi: (1) PAIR otomatize jailbreak, (2) TAP tree-of-attacks, (3) GCG gradient suffix, (4) ASCII / base64 / rot13 encoding, (5) multi-turn persona, (6) multilingual code-switch. Aile başına başarı oranı raporla.

6. **Constitutional self-critique.** 1k zararlı-deneme prompt küratör et. Her biri için, target bir yanıt taslağı çizer. Bir critic LLM yazılı bir constitution'a karşı skorlar ("do no harm," "cite evidence," "refuse illegal requests"). Critic'in itiraz ettiği prompt'lar yeniden yazılır; target critique-iyileştirilmiş çiftler üzerinde fine-tune olur. Holdout eval'de önce/sonra harmlessness ölç.

7. **Over-refusal ölçümü.** Benign prompt suite'inde (örn. XSTest) false-positive oranı izle. Target benign sorularda yardımcı kalmalı.

8. **CVSS skorlama.** Her başarılı jailbreak için CVSS 4.0 üzerinde skor ver (attack vector, complexity, impact). Bir disclosure timeline'ı ve mitigation planı üret.

9. **Range otomasyonu.** Yukarıdaki her şey bir cron'da çalışır; findings bir kuyruğa yazar; over-refusal regresyon alert'leri Slack'e ateşlenir.

## Kullan

```
$ safety probe --model=target --family=PAIR --budget=50
[attacker]   PAIR agent target üzerinde çalışıyor
[attack]     deneme 1/50: sorguyu academic research olarak gizle ... bloklandı
[attack]     deneme 2/50: roleplay'e başvur ... bloklandı
[attack]     deneme 3/50: chain-of-thought ikna ... BAŞARILI
[finding]    CVSS 4.8 medium: target'te roleplay bypass
[range]      50'de 7 başarı (%14 başarı oranı)
```

## Yayınla

Teslimat `outputs/skill-safety-harness.md`. Üretim-grade katmanlı safety pipeline'ı artı önce/sonra harmlessness delta'larıyla yeniden üretilebilir bir red-team range'i.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Saldırı-yüzey kapsamı | 6+ saldırı ailesi egzersize edildi, 2+ dil |
| 20 | True-positive / false-positive trade-off'u | Saldırı blok oranı vs XSTest benign pass oranı |
| 20 | Self-critique delta'sı | Holdout eval'de önce/sonra harmlessness |
| 20 | Dokümantasyon ve disclosure | Timeline ile CVSS-skorlu findings |
| 15 | Otomasyon ve tekrarlanabilirlik | Her şey alert'lerle cron'da çalışır |
| **100** | | |

## Alıştırmalar

1. garak'ın prompt-injection plugin'ini bir RAG chatbot'ta çalıştır ve output-filter katmanlı ve katmansız saldırı başarı oranını karşılaştır.

2. Yedinci bir saldırı ailesi ekle: retrieve edilmiş dokümanlar üzerinden indirect prompt injection. Gereken ekstra savunmayı ölç.

3. Bir "refuse-with-help" modu implement et: guardrail bloklar olduğunda, target düz bir refusal yerine daha güvenli ilgili bir yanıt sunar. XSTest delta'sını ölç.

4. Multilingual kapsam gap'i: X-Guard'ın yetersiz kaldığı bir dil bul. Onu hedefleyen bir fine-tune dataset öner.

5. Constitutional self-critique'i bir 30B model üzerinde çalıştır ve delta'nın ölçeklenip ölçeklenmediğini ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Katmanlı safety | "Defense in depth" | Input, gate, output, HITL'de birden çok guardrail |
| Llama Guard 4 | "Meta'nın safety sınıflandırıcısı" | 2026 referans input/output content sınıflandırıcısı |
| PAIR | "Jailbreak agent'ı" | LLM-sürücülü jailbreak keşfi üzerine makale (Chao et al.) |
| TAP | "Tree-of-Attacks" | PAIR'in tree-search varyantı |
| GCG | "Greedy coordinate gradient" | Gradient-tabanlı adversarial suffix saldırısı |
| Constitutional self-critique | "Anthropic-tarzı training" | Target taslak çizer -> critic skorlar -> yeniden yaz -> yeniden eğit |
| XSTest | "Benign probe set'i" | Over-refusal regresyon benchmark'ı |
| CVSS 4.0 | "Severity skoru" | Safety findings için standart vulnerability skorlama |

## İleri Okuma

- [Anthropic Constitutional Classifier'ları](https://www.anthropic.com/research/constitutional-classifiers) — training-time referansı
- [Meta Llama Guard 4](https://ai.meta.com/research/publications/llama-guard-4/) — 2026 input/output sınıflandırıcısı
- [Google ShieldGemma-2](https://huggingface.co/google/shieldgemma-2b) — image + multimodal safety
- [NVIDIA Nemotron 3 Content Safety](https://developer.nvidia.com/blog/building-nvidia-nemotron-3-agents-for-reasoning-multimodal-rag-voice-and-safety/) — enterprise referansı
- [X-Guard (arXiv:2504.08848)](https://arxiv.org/abs/2504.08848) — 132-dilli multilingual safety
- [garak](https://github.com/NVIDIA/garak) — NVIDIA red-team toolkit'i
- [PyRIT](https://github.com/Azure/PyRIT) — Microsoft red-team framework'ü
- [NeMo Guardrails v0.12](https://docs.nvidia.com/nemo-guardrails/) — rail framework'ü
- [PAIR (arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — jailbreak agent makalesi
