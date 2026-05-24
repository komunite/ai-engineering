# Uzun Bağlam Değerlendirmesi — NIAH, RULER, LongBench, MRCR

> Gemini 3 Pro 10M token bağlam reklam ediyor. 1M token'da, 8-needle MRCR %26.3'e düşüyor. Reklam edilen ≠ kullanılabilir. Uzun bağlam değerlendirmesi sana üzerine gönderdiğin modelin gerçek kapasitesini söyler.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 13 (Soru-Cevap), Faz 5 · 23 (Chunking Stratejileri)
**Süre:** ~60 dakika

## Sorun

200 sayfalık bir sözleşmen var. Model 1M token bağlam iddia ediyor. Sözleşmeyi yapıştırıyorsun ve soruyorsun: "What is the termination clause?" Model cevaplıyor — ama kapak sayfasından cevaplıyor çünkü termination clause 120k token derinde, modelin gerçekten dikkat ettiği yerin ötesinde oturuyor.

Bu 2026 bağlam-kapasite açığıdır. Spec sheet'leri 1M ya da 10M diyor. Gerçeklik bunun %60-70'inin kullanılabilir olduğunu ve "kullanılabilir"in göreve bağlı olduğunu söylüyor.

- **Retrieval (haystack'te tek needle):** sınır modellerde reklam edilen max'a kadar neredeyse mükemmel.
- **Multi-hop / aggregation:** çoğu modelde ~128k'nın ötesinde keskin biçimde bozulur.
- **Dağınık gerçekler üzerinde reasoning:** başarısız olan ilk görev.

Uzun bağlam değerlendirmesi bu eksenleri ölçer. Bu ders benchmark'ları, her birinin gerçekten ne ölçtüğünü ve alanın için nasıl özel bir needle testi kuracağını adlandırır.

## Kavram

![NIAH baseline'ı, RULER çok görevli, LongBench bütünsel](../assets/long-context-eval.svg)

**Needle-in-a-Haystack (NIAH, 2023).** Uzun bir bağlamda kontrollü bir derinlikte bir gerçek ("the magic word is pineapple") yerleştir. Modelden onu getirmesini iste. Derinlik × uzunluğu süpür. Orijinal uzun-bağlam benchmark'ı. Sınır modeller şimdi bunu doyura ulaşmış; gerekli ama yeterli olmayan bir baseline.

**RULER (Nvidia, 2024).** 4 kategoride 13 görev türü: retrieval (single / multi-key / multi-value), multi-hop tracing (değişken takibi), aggregation (yaygın kelime frekansı), QA. Konfigüre edilebilir bağlam uzunluğu (4k'dan 128k+'a). NIAH'yi doyura ulaşan ama multi-hop'ta başarısız olan modelleri ortaya çıkarır. 2024 yayınında, 32k+ bağlam iddia eden 17 modelden yalnızca yarısı 32k'da kalite korudu.

**LongBench v2 (2024).** 503 çoktan seçmeli soru, 8k-2M kelime bağlamı, altı görev kategorisi: single-doc QA, multi-doc QA, long in-context learning, long dialogue, code repo, long structured data. Gerçek dünya uzun bağlam davranışı için üretim benchmark'ı.

**MRCR (Multi-Round Coreference Resolution).** Ölçekte multi-turn coreference. 8-needle, 24-needle, 100-needle varyantları. Attention bozulmadan önce bir modelin kaç gerçeği juggle edebileceğini ortaya çıkarır.

**NoLiMa.** "Non-lexical needle." Needle ve sorgu literal örtüşme paylaşmaz; retrieval bir adım semantik reasoning gerektirir. NIAH'dan zor.

**HELMET.** Birçok belgeyi birleştirir, herhangi birinden bir soru sorar. Seçici attention'ı test eder.

**BABILong.** İlgisiz haystack'lerin içine bAbI reasoning zincirleri gömer. Yalnızca retrieval değil, haystack'te reasoning'i test eder.

### Gerçekten ne raporlamalı

- **Reklam edilen bağlam penceresi.** Spec sheet sayısı.
- **Etkili retrieval uzunluğu.** Bir eşikte (örn. %90) NIAH geçişi.
- **Etkili reasoning uzunluğu.** O eşikte multi-hop ya da aggregation geçişi.
- **Bozulma eğrisi.** Görev türü başına çizilen doğruluk vs bağlam uzunluğu.

Spec sheet'in için iki sayı: retrieval-etkili ve reasoning-etkili. Genellikle reasoning-etkili reklam edilen pencerenin %25-50'sidir.

## İnşa Et

### Adım 1: alanın için özel bir NIAH

`code/main.py`'a bak. İskelet:

```python
def build_haystack(filler_text, needle, depth_ratio, total_tokens):
    if not (0.0 <= depth_ratio <= 1.0):
        raise ValueError(f"depth_ratio must be in [0, 1], got {depth_ratio}")
    if total_tokens <= 0:
        raise ValueError(f"total_tokens must be positive, got {total_tokens}")

    filler_tokens = tokenize(filler_text)
    needle_tokens = tokenize(needle)
    if not filler_tokens:
        raise ValueError("filler_text produced no tokens")

    # Haystack gövdesini doldurmaya yetecek kadar filler tekrarla.
    body_len = max(total_tokens - len(needle_tokens), 0)
    while len(filler_tokens) < body_len:
        filler_tokens = filler_tokens + filler_tokens
    filler_tokens = filler_tokens[:body_len]

    insert_at = min(int(body_len * depth_ratio), body_len)
    haystack = filler_tokens[:insert_at] + needle_tokens + filler_tokens[insert_at:]
    return " ".join(haystack)


def score_niah(model, haystack, question, expected):
    answer = model.complete(f"Context: {haystack}\nQ: {question}\nA:", max_tokens=50)
    return 1 if expected.lower() in answer.lower() else 0
```

`depth_ratio` ∈ {0, 0.25, 0.5, 0.75, 1.0} × `total_tokens` ∈ {1k, 4k, 16k, 64k}'i süpür. Heatmap'i çiz. Bu hedef modelin için NIAH kartıdır.

### Adım 2: multi-needle varyantı

```python
def build_multi_needle(filler, needles, total_tokens):
    depths = [0.1, 0.4, 0.7]
    chunks = [filler[:int(total_tokens * 0.1)]]
    for depth, needle in zip(depths, needles):
        chunks.append(needle)
        next_chunk = filler[int(total_tokens * depth): int(total_tokens * (depth + 0.3))]
        chunks.append(next_chunk)
    return " ".join(chunks)
```

"What are the three magic words?" gibi sorular üçünü de getirmeyi gerektirir. Single-needle başarısı multi-needle başarısını öngörmez.

### Adım 3: multi-hop değişken takibi (RULER tarzı)

```python
haystack = """X1 = 42. ... (filler) ... X2 = X1 + 10. ... (filler) ... X3 = X2 * 2."""
question = "What is X3?"
```

Cevap üç atamayı zincirlemeyi gerektirir. 128k'da sınır modeller burada sıklıkla %50-70 doğruluğa düşer.

### Adım 4: stack'inde LongBench v2

```python
from datasets import load_dataset
longbench = load_dataset("THUDM/LongBench-v2")

def eval_model_on_longbench(model, subset="single-doc-qa"):
    tasks = [x for x in longbench["test"] if x["task"] == subset]
    correct = 0
    for x in tasks:
        answer = model.complete(x["context"] + "\n\nQ: " + x["question"], max_tokens=20)
        if normalize(answer) == normalize(x["answer"]):
            correct += 1
    return correct / len(tasks)
```

Kategori başına doğruluk raporla. Toplam skorlar büyük görev seviyesi farklarını saklar.

## Tuzaklar

- **Yalnızca-NIAH değerlendirmesi.** 1M token'da NIAH geçmek multi-hop hakkında hiçbir şey söylemez. Her zaman RULER ya da özel multi-hop testi çalıştır.
- **Düzgün derinlik sampling.** Birçok implementasyon yalnızca depth=0.5'i test eder. depth=0, 0.25, 0.5, 0.75, 1.0 test et — "lost in the middle" etkisi gerçektir.
- **Filler ile lexical örtüşme.** Needle filler ile anahtar kelime paylaşıyorsa, retrieval önemsizleşir. NoLiMa tarzı örtüşmeyen needle'lar kullan.
- **Latency'yi yok sayma.** 1M token'lık prompt'ların prefill'i 30-120 saniye sürer. Doğrulukla birlikte time-to-first-token'ı ölç.
- **Vendor-self-reported sayılar.** OpenAI, Google, Anthropic kendi skorlarını yayınlar. Her zaman kullanım durumunda bağımsız olarak yeniden çalıştır.

## Kullan

2026 stack'i:

| Durum | Benchmark |
|-----------|-----------|
| Hızlı sanity kontrolü | 3 derinlik × 3 uzunlukta özel NIAH |
| Üretim için model seçimi | Hedef uzunluğunda RULER (13 görev) |
| Gerçek dünya QA kalitesi | LongBench v2 single-doc-QA alt seti |
| Multi-hop reasoning | BABILong ya da özel değişken takibi |
| Konuşmalı / dialog | Hedef uzunluğunda MRCR 8-needle |
| Model yükseltme regresyonu | Sabit şirket içi NIAH + RULER harness'i, her yeni modelde çalıştır |

Üretim için pratik kural: amaçladığın uzunlukta NIAH + 1 reasoning görevin olmadan bir bağlam penceresine asla güvenme.

## Yayınla

`outputs/skill-long-context-eval.md` olarak kaydet:

```markdown
---
name: long-context-eval
description: Design a long-context evaluation battery for a given model and use case.
version: 1.0.0
phase: 5
lesson: 28
tags: [nlp, long-context, evaluation]
---

Given a target model, target context length, and use case, output:

1. Tests. NIAH depth × length grid; RULER multi-hop; custom domain task.
2. Sampling. Depths 0, 0.25, 0.5, 0.75, 1.0 at each length.
3. Metrics. Retrieval pass rate; reasoning pass rate; time-to-first-token; cost-per-query.
4. Cutoff. Effective retrieval length (90% pass) and effective reasoning length (70% pass). Report both.
5. Regression. Fixed harness, rerun on every model upgrade, surface deltas.

Refuse to trust a context window from the model card alone. Refuse NIAH-only evaluation for any multi-hop workload. Refuse vendor self-reported long-context scores as independent evidence.
```

## Alıştırmalar

1. **Kolay.** 3 derinlik (0.25, 0.5, 0.75) × 3 uzunlukta (1k, 4k, 16k) bir NIAH kur. Herhangi bir modelde çalıştır. Pass rate'i 3×3 heatmap olarak çiz.
2. **Orta.** 3-needle varyantı ekle. Her uzunlukta 3'ünün de retrieval'ını ölç. Aynı uzunlukta single-needle pass rate'i ile karşılaştır.
3. **Zor.** 64k filler'a gömülmüş bir değişken takibi görevi (X1 → X2 → X3, 3 hop) kur. 3 sınır model arasında doğruluğu ölç. Model başına etkili reasoning uzunluğunu raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| NIAH | Saman yığınında iğne | Filler'a bir gerçek dik, modelden onu getirmesini iste. |
| RULER | Steroidli NIAH | Retrieval / multi-hop / aggregation / QA arasında 13 görev türü. |
| Etkili bağlam | Gerçek kapasite | Doğruluğun bir eşik üstünde tutulduğu uzunluk. |
| Lost in the middle | Derinlik bias'ı | Modeller uzun girdilerin ortasındaki içeriğe daha az dikkat eder. |
| Multi-needle | Aynı anda birçok gerçek | Çoklu dikim; yalnızca retrieval değil, attention juggle etmeyi test eder. |
| MRCR | Multi-round coref | 8, 24 ya da 100-needle coreference; attention doygunluğunu ortaya çıkarır. |
| NoLiMa | Non-lexical needle | Needle ve sorgu literal token paylaşmaz; reasoning gerektirir. |

## İleri Okuma

- [Kamradt (2023). Needle in a Haystack analysis](https://github.com/gkamradt/LLMTest_NeedleInAHaystack) — orijinal NIAH repo'su.
- [Hsieh et al. (2024). RULER: What's the Real Context Size of Your Long-Context LMs?](https://arxiv.org/abs/2404.06654) — çok görevli benchmark.
- [Bai et al. (2024). LongBench v2](https://arxiv.org/abs/2412.15204) — gerçek dünya uzun bağlam eval'i.
- [Modarressi et al. (2024). NoLiMa: Non-lexical needles](https://arxiv.org/abs/2404.06666) — daha zor needle'lar.
- [Kuratov et al. (2024). BABILong](https://arxiv.org/abs/2406.10149) — saman yığınında reasoning.
- [Liu et al. (2024). Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — derinlik bias'ı makalesi.
