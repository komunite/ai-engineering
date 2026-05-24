# Yapılı Çıktılar ve Kısıtlı Decoding

> Bir LLM'den JSON iste. Çoğu zaman JSON al. Üretimde "çoğu" problemdir. Kısıtlı decoding, sampling'den önce logit'leri düzenleyerek "çoğu"yu "her zaman"a çevirir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 17 (Chatbot'lar), Faz 5 · 19 (Subword Tokenleştirme)
**Süre:** ~60 dakika

## Sorun

Bir sınıflandırıcı bir LLM'e prompt veriyor: "Return one of {positive, negative, neutral}." Model "The sentiment is positive — this review is overwhelmingly favorable because the customer explicitly states that they ..." döndürüyor. Parser'ın çöküyor. Sınıflandırıcının F1'i 0.0.

Serbest formlu üretim bir kontrat değildir. Bir öneridir. Üretim sistemi bir kontrata ihtiyaç duyar.

2026'da üç katman var.

1. **Prompting.** Nazikçe sor. "Return only the JSON object." Sınır modellerde ~%80 çalışır, küçüklerde daha az.
2. **Yerel yapılı çıktı API'leri.** OpenAI `response_format`, Anthropic tool use, Gemini JSON mode. Desteklenen şemalarda güvenilir. Vendor-locked.
3. **Kısıtlı decoding.** Logit'leri her üretim adımında, modelin geçersiz token'ları yayınlama*ması* için modifiye et. İnşa yoluyla %100 geçerli. Herhangi bir yerel modelde çalışır.

Bu ders üçü için de sezgi kurar ve hangisine ne zaman uzanacağını adlandırır.

## Kavram

![Her adımda geçersiz token'ları mask'leyen kısıtlı decoding](../assets/constrained-decoding.svg)

**Kısıtlı decoding nasıl çalışır.** Her üretim adımında, LLM tüm vocabulary üzerinde bir logit vektörü (~100k token) üretir. Bir *logit processor*, model ile sampler arasında oturur. Mevcut hedef gramerdeki — JSON Schema, regex, context-free grammar — pozisyon verildiğinde hangi token'ların geçerli olduğunu hesaplar ve tüm geçersiz token'ların logit'lerini negatif sonsuza ayarlar. Kalan logit'ler üzerindeki softmax, olasılık kütlesini yalnızca geçerli devamlara koyar.

2026'da implementasyonlar:

- **Outlines.** JSON Schema ya da regex'i bir finite-state machine'e derler. Her token O(1) geçerli-sonraki-token lookup alır. FSM tabanlı, dolayısıyla recursive şemalar düzleştirme gerektirir.
- **XGrammar / llguidance.** Context-free grammar motorları. Recursive JSON Schema'yı ele alır. Sıfıra yakın decoding overhead'i. OpenAI 2025 yapılı çıktı implementasyonunda llguidance'a kredi verdi.
- **vLLM guided decoding.** Outlines, XGrammar ya da lm-format-enforcer arka uçlarıyla yerleşik `guided_json`, `guided_regex`, `guided_choice`, `guided_grammar`.
- **Instructor.** Herhangi bir LLM üzerinde Pydantic tabanlı wrapper. Doğrulama başarısızlığında retry yapar. Cross-provider, ama logit'leri modifiye etmez — retry'lara + yapılı-çıktı-farkında prompt'lara dayanır.

### Sezgi karşıtı sonuç

Kısıtlı decoding sıklıkla unconstrained üretimden *daha hızlıdır*. İki sebep. Birincisi, sonraki-token arama uzayını küçültür. İkincisi, akıllı implementasyonlar zorla token'lar için token üretimini tamamen atlar (`{"name": "` gibi scaffolding — her byte belirlenmiştir).

### Sana pahalıya patlayan tuzak

Alan sırası önemlidir. `answer`'ı `reasoning`'den önce koy, model düşünmeden önce bir cevaba bağlanır. JSON geçerli. Cevap yanlış. Hiçbir doğrulama yakalamaz.

```json
// KÖTÜ
{"answer": "yes", "reasoning": "because ..."}

// İYİ
{"reasoning": "... therefore ...", "answer": "yes"}
```

Şema alan sırası mantıktır, formatlama değil.

## İnşa Et

### Adım 1: sıfırdan regex kısıtlı üretim

Bağımsız FSM implementasyonu için `code/main.py`'a bak. 30 satırda çekirdek fikir:

```python
def mask_logits(logits, valid_token_ids):
    mask = [float("-inf")] * len(logits)
    for tid in valid_token_ids:
        mask[tid] = logits[tid]
    return mask


def generate_constrained(model, tokenizer, prompt, fsm):
    ids = tokenizer.encode(prompt)
    state = fsm.initial_state
    while not fsm.is_accept(state):
        logits = model.next_token_logits(ids)
        valid = fsm.valid_tokens(state, tokenizer)
        logits = mask_logits(logits, valid)
        tok = sample(logits)
        ids.append(tok)
        state = fsm.transition(state, tok)
    return tokenizer.decode(ids)
```

FSM şu ana kadar tatmin ettiğimiz gramer parçalarını takip eder. `valid_tokens(state, tokenizer)`, hangi vocabulary token'larının FSM'i kabul edici bir yolu terk etmeden ilerletebileceğini hesaplar.

### Adım 2: JSON Schema için Outlines

```python
from pydantic import BaseModel
from typing import Literal
import outlines


class Review(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float
    evidence_span: str


model = outlines.models.transformers("meta-llama/Llama-3.2-3B-Instruct")
generator = outlines.generate.json(model, Review)

result = generator("Classify: 'The wait staff was attentive and the food arrived hot.'")
print(result)
# Review(sentiment='positive', confidence=0.93, evidence_span='attentive ... hot')
```

Sıfır doğrulama hatası. Asla. FSM, geçersiz çıktıyı ulaşılamaz kılar.

### Adım 3: provider-agnostik Pydantic için Instructor

```python
import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field


class Invoice(BaseModel):
    vendor: str
    total_usd: float = Field(ge=0)
    line_items: list[str]


client = instructor.from_anthropic(Anthropic())
invoice = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    response_model=Invoice,
    messages=[{"role": "user", "content": "Extract from: 'Acme Corp $420. Widget, Gizmo.'"}],
)
```

Farklı mekanizma. Instructor logit'lere dokunmaz. Şemayı prompt'a formatlar, çıktıyı parse eder ve doğrulama başarısızlığında retry yapar (varsayılan 3 kez). Herhangi bir provider ile çalışır. Retry'lar latency ve maliyet ekler. Cross-provider taşınabilirlik satış noktasıdır.

### Adım 4: yerel vendor API'leri

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-5",
    input=[{"role": "user", "content": "Classify: 'The food was cold.'"}],
    text={"format": {"type": "json_schema", "name": "sentiment",
          "schema": {"type": "object", "required": ["sentiment"],
                     "properties": {"sentiment": {"type": "string",
                                                  "enum": ["positive", "negative", "neutral"]}}}}},
)
print(response.output_parsed)
```

Sunucu tarafı kısıtlı decoding. Desteklenen şemalar için Outlines ile güvenilirlik eşitliği. Yerel model yönetimi yok. Seni vendor'a kilitler.

## Tuzaklar

- **Recursive şemalar.** Outlines, recursion'ı sabit derinliğe düzleştirir. Ağaç yapılı çıktılar (iç içe yorumlar, AST) XGrammar ya da llguidance (CFG tabanlı) gerektirir.
- **Devasa enum'lar.** 10,000 seçenekli enum yavaş derlenir ya da timeout olur. Bir retriever'a geç: önce top-k adayları tahmin et, onlara kısıtla.
- **Çok katı gramer.** `date: "YYYY-MM-DD"` regex'i zorla ve model eksik tarihler için `"unknown"` çıkaramaz. Model bir tarih icat ederek telafi eder. `null` ya da bir sentinel'e izin ver.
- **Erken bağlanma.** Yukarıdaki alan sırası tuzağına bak. Her zaman önce reasoning koy.
- **Şemasız vendor JSON modu.** Saf JSON modu yalnızca geçerli JSON garantilemez, *kullanım durumun için* geçerli değil. Her zaman tam bir şema sağla.

## Kullan

2026 stack'i:

| Durum | Seç |
|-----------|------|
| OpenAI/Anthropic/Google modeli, basit şema | Yerel vendor yapılı çıktı |
| Herhangi bir provider, Pydantic workflow, retry'lara tolerans | Instructor |
| Yerel model, %100 geçerlilik gerekli, düz şema | Outlines (FSM) |
| Yerel model, recursive şema | XGrammar ya da llguidance |
| Self-hosted çıkarım sunucusu | vLLM guided decoding |
| Retry kabul edilebilir batch işleme | Instructor + en ucuz model |

## Yayınla

`outputs/skill-structured-output-picker.md` olarak kaydet:

```markdown
---
name: structured-output-picker
description: Choose a structured output approach, schema design, and validation plan.
version: 1.0.0
phase: 5
lesson: 20
tags: [nlp, llm, structured-output]
---

Given a use case (provider, latency budget, schema complexity, failure tolerance), output:

1. Mechanism. Native vendor structured output, Instructor retries, Outlines FSM, or XGrammar CFG. One-sentence reason.
2. Schema design. Field order (reasoning first, answer last), nullable fields for "unknown", enum vs regex, required fields.
3. Failure strategy. Max retries, fallback model, graceful `null` handling, out-of-distribution refusal.
4. Validation plan. Schema compliance rate (target 100%), semantic validity (LLM-judge), field-coverage rate, latency p50/p99.

Refuse any design that puts `answer` or `decision` before reasoning fields. Refuse to use bare JSON mode without a schema. Flag recursive schemas behind an FSM-only library.
```

## Alıştırmalar

1. **Kolay.** Küçük açık-ağırlık bir modele (örn. Llama-3.2-3B) kısıtlı decoding olmadan `Review(sentiment, confidence, evidence_span)` için prompt ver. 100 değerlendirmede geçerli JSON olarak parse olanların oranını ölç.
2. **Orta.** Aynı corpus Outlines JSON modu ile. Uyumluluk oranını, latency'yi ve semantik doğruluğu karşılaştır.
3. **Zor.** Telefon numaraları için (`\d{3}-\d{3}-\d{4}`) sıfırdan bir regex kısıtlı decoder uygula. 1000 örnekte 0 geçersiz çıktı doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Kısıtlı decoding | Geçerli çıktıyı zorla | Her üretim adımında geçersiz-token logit'lerini mask'le. |
| Logit processor | Kısıtlayan şey | Fonksiyon: `(logits, state) -> masked_logits`. |
| FSM | Finite-state machine | Derlenmiş gramer temsili; O(1) geçerli-sonraki-token lookup. |
| CFG | Context-free grammar | Recursion'ı ele alan gramer; FSM'den yavaş ama daha ifadeli. |
| Şema alan sırası | Önemli mi? | Evet — ilk alan bağlanır; reasoning'i her zaman cevaptan önce koy. |
| Guided decoding | vLLM'in adı | Aynı kavram, çıkarım sunucusuna entegre. |
| JSON modu | OpenAI'nin erken sürümü | JSON syntax'ını garantiler; şema eşleşmesini garantiLEMEZ. |

## İleri Okuma

- [Willard, Louf (2023). Efficient Guided Generation for LLMs](https://arxiv.org/abs/2307.09702) — Outlines makalesi.
- [XGrammar paper (2024)](https://arxiv.org/abs/2411.15100) — hızlı CFG tabanlı kısıtlı decoding.
- [vLLM — Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html) — çıkarım sunucusu entegrasyonu.
- [OpenAI — Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs) — API referansı + gotcha'lar.
- [Instructor library](https://python.useinstructor.com/) — provider'lar arası Pydantic + retry'lar.
- [JSONSchemaBench (2025)](https://arxiv.org/abs/2501.10868) — 6 kısıtlı decoding framework'ünü benchmark.
