# LLM Değerlendirme — RAGAS, DeepEval, G-Eval

> Exact-match ve F1 semantik denkliği kaçırır. İnsan incelemesi ölçeklenmez. LLM-as-judge üretim cevabıdır — sayıya güvenmek için yeterli kalibrasyonla.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 13 (Soru-Cevap), Faz 5 · 14 (Bilgi Erişimi)
**Süre:** ~75 dakika

## Sorun

RAG sistemin cevap veriyor: "June 29th, 2007."
Gold referans: "June 29, 2007."
Exact Match 0 alır. F1 ~%75 alır. Bir insan 100 verirdi.

Şimdi 10,000 test vakasıyla çarp. Retriever, chunking, prompt ya da modeldeki her değişiklikle tekrar çarp. Anlamı anlayan, ölçekte ucuz çalışan, regresyonlar hakkında yalan söylemeyen ve doğru başarısızlık modlarını öne çıkaran bir evaluator'a ihtiyacın var.

2026'nın bu sorunu sahiplenen üç framework'ü var.

- **RAGAS.** Retrieval-Augmented Generation ASsessment. NLI + LLM-judge arka uçlarıyla dört RAG metriği (faithfulness, answer-relevance, context-precision, context-recall). Araştırma destekli, hafif.
- **DeepEval.** LLM'ler için pytest. G-Eval, task-completion, hallucination, bias metrikleri. CI/CD-native.
- **G-Eval.** Bir yöntem (ve bir DeepEval metriği): chain-of-thought, özel kriter, 0-1 skor ile LLM-as-judge.

Üçü de LLM-as-judge'a yaslanıyor. Bu ders yöntem ve onun etrafındaki güven katmanı için sezgi kurar.

## Kavram

![Dört değerlendirme boyutu, LLM-as-judge mimarisi](../assets/llm-evaluation.svg)

**LLM-as-judge.** Statik bir metriği bir rubric verildiğinde çıktıları puanlayan bir LLM ile değiştir. `(query, context, answer)` verildiğinde, bir judge LLM'e prompt: "Faithfulness'ta 0-1 puanla." Skoru döndür.

Neden işe yarar: LLM'ler maliyetin küçük bir kısmında insan yargısına yaklaşır. GPT-4o-mini puanlanmış vaka başına ~$0.003'te 1000-örnek regresyon eval koşmasını $5 altında mümkün kılar.

Neden sessizce başarısız olur:

1. **Judge bias'ı.** Judge'lar daha uzun cevapları, kendi model ailelerinden cevapları, prompt stiline uyan cevapları tercih eder.
2. **JSON parse başarısızlıkları.** Kötü JSON → NaN skor → toplamdan sessizce dışlanır. RAGAS kullanıcıları bu acıyı bilir. try/except + açık başarısızlık modu ile kapı koy.
3. **Model sürümleri arası drift.** Judge'ı yükseltmek her metriği değiştirir. Judge modelini + sürümünü dondur.

**RAG dörtlüsü.**

| Metrik | Soru | Arka uç |
|--------|----------|---------|
| Faithfulness | Cevaptaki her iddia getirilen bağlamdan mı geliyor? | NLI tabanlı entailment |
| Answer relevance | Cevap soruyu adresliyor mu? | Cevaptan hipotetik sorular üret; gerçek soruyla karşılaştır |
| Context precision | Getirilen chunk'lardan hangisi ilgiliydi? | LLM-judge |
| Context recall | Retrieval ihtiyaç duyulan her şeyi getirdi mi? | Gold cevaba karşı LLM-judge |

**G-Eval.** Özel bir kriter tanımla: "Cevap doğru kaynağı alıntıladı mı?" Framework otomatik olarak chain-of-thought değerlendirme adımlarına genişler, sonra 0-1 puanlar. RAGAS'ın kapsamadığı alana özgü kalite boyutları için iyi.

**Kalibrasyon.** İnsan etiketlerine karşı korelasyonun olmadan ham judge skoruna asla güvenme. 100 elle etiketlenmiş örnek koş. Judge'ı insana karşı çiz. Spearman rho hesapla. rho < 0.7 ise, judge rubric'in çalışma gerektiriyor.

## İnşa Et

### Adım 1: NLI ile faithfulness (RAGAS tarzı)

```python
from typing import Callable
from transformers import pipeline

nli = pipeline("text-classification",
               model="MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
               top_k=None)

# `llm` herhangi bir callable: prompt str -> üretilmiş str.
# Örnek: llm = lambda p: client.messages.create(model="claude-haiku-4-5", ...).content[0].text
LLM = Callable[[str], str]


def atomic_claims(answer: str, llm: LLM) -> list[str]:
    prompt = f"""Break this answer into simple factual claims (one per line):
{answer}
"""
    return llm(prompt).splitlines()


def faithfulness(answer: str, context: str, llm: LLM) -> float:
    claims = atomic_claims(answer, llm)
    if not claims:
        return 0.0
    supported = 0
    for claim in claims:
        result = nli({"text": context, "text_pair": claim})[0]
        entail = next((s for s in result if s["label"] == "entailment"), None)
        if entail and entail["score"] > 0.5:
            supported += 1
    return supported / len(claims)
```

Cevabı atomik iddialara ayrıştır. Her iddiayı getirilen bağlama karşı NLI ile kontrol et. Faithfulness = desteklenen oran.

### Adım 2: answer relevance

```python
import numpy as np
from sentence_transformers import SentenceTransformer

# encoder: .encode(texts, normalize_embeddings=True) -> ndarray uygulayan herhangi bir model
# örn., encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")

def answer_relevance(question: str, answer: str, encoder, llm: LLM, n: int = 3) -> float:
    prompt = f"Write {n} questions this answer could be the answer to:\n{answer}"
    generated = [line for line in llm(prompt).splitlines() if line.strip()][:n]
    if not generated:
        return 0.0
    q_emb = np.asarray(encoder.encode([question], normalize_embeddings=True)[0])
    g_embs = np.asarray(encoder.encode(generated, normalize_embeddings=True))
    sims = [float(q_emb @ g_emb) for g_emb in g_embs]
    return sum(sims) / len(sims)
```

Cevap sorulan sorudan farklı sorular ima ediyorsa, relevance düşer.

### Adım 3: G-Eval özel metriği

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase

metric = GEval(
    name="Correctness",
    criteria="The answer should be factually accurate and match the expected output.",
    evaluation_steps=[
        "Read the expected output.",
        "Read the actual output.",
        "List factual claims in the actual output.",
        "For each claim, mark supported or unsupported by the expected output.",
        "Return score = fraction supported.",
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
)

test = LLMTestCase(input="When was the first iPhone released?",
                   actual_output="June 29th, 2007.",
                   expected_output="June 29, 2007.")
metric.measure(test)
print(metric.score, metric.reason)
```

Evaluation step'leri rubric'tir. Açık adımlar örtük "score 0-1" prompt'larından daha stabildir.

### Adım 4: CI gate

```python
import deepeval
from deepeval.metrics import FaithfulnessMetric, ContextualRelevancyMetric


def test_rag_system():
    cases = load_regression_cases()
    faith = FaithfulnessMetric(threshold=0.85)
    rel = ContextualRelevancyMetric(threshold=0.7)
    for case in cases:
        faith.measure(case)
        assert faith.score >= 0.85, f"faithfulness regression on {case.id}"
        rel.measure(case)
        assert rel.score >= 0.7, f"relevancy regression on {case.id}"
```

Bir pytest dosyası olarak gönder. Her PR'da çalıştır. Regresyonlarda merge'leri engelle.

### Adım 5: sıfırdan oyuncak eval

`code/main.py`'a bak. Faithfulness'ın (cevap iddialarının bağlamla örtüşmesi) ve relevance'ın (cevap token'larının soru token'larıyla örtüşmesi) yalnızca stdlib yaklaşıkları. Üretim değil. Şekli gösterir.

## Tuzaklar

- **Kalibrasyon yok.** İnsan etiketleriyle 0.3 korelasyonlu bir judge gürültüdür. Göndermeden önce bir kalibrasyon koşusu iste.
- **Self-evaluation.** Aynı LLM'i üretmek ve yargılamak için kullanmak skorları %10-20 şişirir. Judge için farklı bir model ailesi kullan.
- **Pairwise yargıda pozisyon bias'ı.** Judge'lar sunulan ilk seçeneği tercih eder. Her zaman sırayı rastgele yap ve ikisini de çalıştır.
- **Ham toplam başarısızlıkları saklar.** Ortalama skor 0.85 sıklıkla %5 felaket başarısızlıkları saklar. Her zaman alt quantile'ı incele.
- **Golden dataset bozulması.** Zaman içinde drift eden versionlanmamış eval setleri uzunlamasına karşılaştırmayı bozar. Her değişiklikle veri setini etiketle.
- **LLM maliyeti.** Ölçekte, judge çağrıları maliyete hâkim olur. Kalibrasyon eşiğini karşılayan en ucuz modeli kullan. GPT-4o-mini, Claude Haiku, Mistral-small.

## Kullan

2026 stack'i:

| Kullanım durumu | Framework |
|---------|-----------|
| RAG kalite izleme | RAGAS (4 metrik) |
| CI/CD regresyon kapıları | DeepEval + pytest |
| Özel alan kriterleri | DeepEval içinde G-Eval |
| Online canlı-trafik izleme | Referanssız modda RAGAS |
| Insan döngülü spot kontroller | Anotasyon UI ile LangSmith ya da Phoenix |
| Red-teaming / güvenlik eval | Promptfoo + DeepEval |

Tipik stack: izleme için RAGAS, CI için DeepEval, yeni boyutlar için G-Eval. Üçünü de çalıştır; faydalı biçimde anlaşmazlığa düşerler.

## Yayınla

`outputs/skill-eval-architect.md` olarak kaydet:

```markdown
---
name: eval-architect
description: Design an LLM evaluation plan with calibrated judge and CI gates.
version: 1.0.0
phase: 5
lesson: 27
tags: [nlp, evaluation, rag]
---

Given a use case (RAG / agent / generative task), output:

1. Metrics. Faithfulness / relevance / context-precision / context-recall + any custom G-Eval metrics with criteria.
2. Judge model. Named model + version, rationale for cost vs accuracy.
3. Calibration. Hand-labeled set size, target Spearman rho vs human > 0.7.
4. Dataset versioning. Tag strategy, change log, stratification.
5. CI gate. Thresholds per metric, regression-window logic, bottom-quantile alert.

Refuse to rely on a judge untested against ≥50 human-labeled examples. Refuse self-evaluation (same model generates + judges). Refuse aggregate-only reporting without bottom-10% surfacing. Flag any pipeline where judge upgrade lands without parallel baseline eval.
```

## Alıştırmalar

1. **Kolay.** Bilinen halüsinasyonları olan 10 RAG örneğinde RAGAS kullan. Faithfulness metriğinin her birini yakaladığını doğrula.
2. **Orta.** 50 QA cevabını doğruluk için 0-1 elle etiketle. G-Eval ile puanla. Judge ve insan arasında Spearman rho ölç.
3. **Zor.** DeepEval ile bir pytest CI kapısı kur. Retriever'ı kasıtlı olarak gerilet. Kapının başarısız olduğunu doğrula. En düşük %10'da eşik kontrolüyle alt-quantile alerting ekle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| LLM-as-judge | Bir LLM ile puanlama | Bir rubric verildiğinde çıktıları 0-1 puanlaması için bir judge modele prompt. |
| RAGAS | RAG metrik kütüphanesi | 4 referanssız RAG metrikli açık kaynak eval framework'ü. |
| Faithfulness | Cevap temellendirilmiş mi? | Getirilen bağlam tarafından entail edilen cevap iddialarının oranı. |
| Context precision | Getirilen chunk'lar ilgiliydi mi? | Gerçekten önemli olan top-K chunk'ların oranı. |
| Context recall | Retrieval her şeyi buldu mu? | Getirilen chunk'lar tarafından desteklenen gold-cevap iddialarının oranı. |
| G-Eval | Özel LLM judge | Rubric + chain-of-thought eval adımları + 0-1 skor. |
| Kalibrasyon | Güven ama doğrula | Judge skoru ve insan skoru arasındaki Spearman korelasyonu. |

## İleri Okuma

- [Es et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) — RAGAS makalesi.
- [Liu et al. (2023). G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment](https://arxiv.org/abs/2303.16634) — G-Eval makalesi.
- [DeepEval docs](https://deepeval.com/docs/metrics-introduction) — açık üretim stack'i.
- [Zheng et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) — bias'lar, kalibrasyon, sınırlar.
- [MLflow GenAI Scorer](https://mlflow.org/blog/third-party-scorers) — RAGAS, DeepEval, Phoenix'i entegre eden birleştirici framework.
