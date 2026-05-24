# Transformer Öncesi Metin Üretimi — N-gram Dil Modelleri

> Bir kelime şaşırtıcıysa, model kötüdür. Perplexity şaşırtıyı bir sayıya çevirir. Smoothing onu sonlu tutar.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 01 (Metin İşleme), Faz 2 · 14 (Naive Bayes)
**Süre:** ~45 dakika

## Sorun

Transformer'lardan önce, RNN'lerden önce, word embedding'lerden önce, bir dil modeli sonraki kelimeyi önceki `n-1` kelimeyi ne sıklıkla takip ettiğini sayarak tahmin ediyordu. "the cat" → "sat" 47 kez, "the cat" → "jumped" 12 kez, "the cat" → "refrigerator" 0 kez say. Olasılık dağılımı elde etmek için normalize et.

Bu bir n-gram dil modelidir. 1980'den 2015'e kadar her konuşma tanıyıcıyı, her yazım denetleyicisini ve her phrase-tabanlı makine çeviri sistemini çalıştırdı. Ucuz cihaz üzerinde dil modellemeye ihtiyacın olduğunda hâlâ çalışıyor.

İlginç problem, görülmemiş n-gram'lar için ne yapacağıdır. Ham sayım tabanlı bir model, görmediği her şeye sıfır olasılık atar, bu felaket çünkü cümleler uzundur ve neredeyse her uzun cümle en az bir görülmemiş dizi içerir. Elli yıllık smoothing araştırması bunu düzeltti. Kneser-Ney smoothing sonuçtur ve modern deep learning onun empirik geleneğini miras aldı.

## Kavram

![N-gram modeli: say, smoothla, üret](../assets/ngram.svg)

**N-gram olasılığı:** `P(w_i | w_{i-n+1}, ..., w_{i-1})`. `n`'i sabitle (tipik olarak trigram için 3, 4-gram için 4). Sayımlardan hesapla:

```text
P(w | context) = count(context, w) / count(context)
```

**Sıfır sayım problemi.** Eğitimde görülmeyen herhangi bir n-gram sıfır olasılık alır. Brown corpus üzerinde 2007 bir çalışma 4-gram modelin bile held-out 4-gram'ların %30'unun eğitimde görülmediğini buldu. Smoothing olmadan herhangi bir gerçek metin üzerinde değerlendiremezsin.

**Smoothing yaklaşımları, sofistikasyon sırasına göre:**

1. **Laplace (add-one).** Her sayıma 1 ekle. Basit, nadir olaylarda berbat.
2. **Good-Turing.** Frekans-frekansları temelinde yüksek frekanslı olaylardan görülmemiş olanlara olasılık kütlesi tahsis et.
3. **Interpolation.** n-gram, (n-1)-gram vb. tahminleri ayarlanabilir ağırlıklarla birleştir.
4. **Backoff.** N-gram sayımı sıfırsa, (n-1)-gram'a geri dön. Katz backoff bunu normalize eder.
5. **Absolute discounting.** Tüm sayımlardan sabit bir indirim `D` çıkar, görülmemişlere yeniden dağıt.
6. **Kneser-Ney.** Absolute discounting artı düşük dereceli model için akıllı bir seçim: ham frekans yerine *continuation probability* (bir kelimenin geçtiği bağlam sayısı) kullan.

Kneser-Ney içgörüsü derindir. "San Francisco" yaygın bir bigram'dır. Unigram "Francisco" çoğunlukla "San"den sonra geçer. Naif absolute discounting "Francisco"ya yüksek unigram olasılığı verir (çünkü sayım yüksektir). Kneser-Ney "Francisco"nun yalnızca bir bağlamda geçtiğini fark eder ve continuation probability'sini buna göre düşürür. Sonuç: "Francisco" ile biten yeni bir bigram uygun düşük olasılığı alır.

**Değerlendirme: perplexity.** Held-out test set üzerinde kelime başına ortalama negatif log-olabilirliğin üssü. Düşük daha iyidir. 100 perplexity, modelin 100 kelime arasında düzgün seçim yapsa olacağı kadar kafasının karışık olduğu anlamına gelir.

```text
perplexity = exp(- (1/N) * Σ log P(w_i | context_i))
```

## İnşa Et

### Adım 1: trigram sayımları

```python
from collections import Counter, defaultdict


def train_ngram(corpus_tokens, n=3):
    ngrams = Counter()
    contexts = Counter()
    for sentence in corpus_tokens:
        padded = ["<s>"] * (n - 1) + sentence + ["</s>"]
        for i in range(len(padded) - n + 1):
            ctx = tuple(padded[i:i + n - 1])
            word = padded[i + n - 1]
            ngrams[ctx + (word,)] += 1
            contexts[ctx] += 1
    return ngrams, contexts


def raw_probability(ngrams, contexts, context, word):
    ctx = tuple(context)
    if contexts.get(ctx, 0) == 0:
        return 0.0
    return ngrams.get(ctx + (word,), 0) / contexts[ctx]
```

Girdi tokenleştirilmiş cümlelerin listesidir. Çıktı n-gram sayımları ve bağlam sayımlarıdır. `<s>` ve `</s>` cümle sınırlarıdır.

### Adım 2: Laplace smoothing

```python
def laplace_probability(ngrams, contexts, vocab_size, context, word):
    ctx = tuple(context)
    numerator = ngrams.get(ctx + (word,), 0) + 1
    denominator = contexts.get(ctx, 0) + vocab_size
    return numerator / denominator
```

Her sayıma 1 ekle. Smoothlar ama görülmemiş olaylara aşırı kütle tahsis eder, nadir-bilinen olaylara da zarar verir.

### Adım 3: Kneser-Ney (bigram, interpolated)

```python
def kneser_ney_bigram_model(corpus_tokens, discount=0.75):
    unigrams = Counter()
    bigrams = Counter()
    unigram_contexts = defaultdict(set)

    for sentence in corpus_tokens:
        padded = ["<s>"] + sentence + ["</s>"]
        for i, w in enumerate(padded):
            unigrams[w] += 1
            if i > 0:
                prev = padded[i - 1]
                bigrams[(prev, w)] += 1
                unigram_contexts[w].add(prev)

    total_unique_bigrams = sum(len(ctx_set) for ctx_set in unigram_contexts.values())
    continuation_prob = {
        w: len(ctx_set) / total_unique_bigrams for w, ctx_set in unigram_contexts.items()
    }

    context_totals = Counter()
    for (prev, w), count in bigrams.items():
        context_totals[prev] += count

    unique_follow = defaultdict(set)
    for (prev, w) in bigrams:
        unique_follow[prev].add(w)

    def prob(prev, w):
        count = bigrams.get((prev, w), 0)
        denom = context_totals.get(prev, 0)
        if denom == 0:
            return continuation_prob.get(w, 1e-9)
        first_term = max(count - discount, 0) / denom
        lambda_prev = discount * len(unique_follow[prev]) / denom
        return first_term + lambda_prev * continuation_prob.get(w, 1e-9)

    return prob
```

Üç hareketli parça. `continuation_prob` "bu kelime kaç farklı bağlamda geçer?"i yakalar (Kneser-Ney yeniliği). `lambda_prev` indirim tarafından serbest bırakılan kütledir, backoff'u ağırlıklandırmak için kullanılır. Nihai olasılık indirimli ana terim artı ağırlıklı continuation terimidir.

### Adım 4: sampling ile metin üretimi

```python
import random


def generate(prob_fn, vocab, prefix, max_len=30, seed=0):
    rng = random.Random(seed)
    tokens = list(prefix)
    for _ in range(max_len):
        candidates = [(w, prob_fn(tokens[-1], w)) for w in vocab]
        total = sum(p for _, p in candidates)
        r = rng.random() * total
        acc = 0.0
        for w, p in candidates:
            acc += p
            if r <= acc:
                tokens.append(w)
                break
        if tokens[-1] == "</s>":
            break
    return tokens
```

Olasılıkla orantılı sampling. Seed başına her zaman farklı çıktı verir. Beam-search benzeri çıktı için, her adımda argmax'ı seç (greedy) ve küçük bir rastgelelik knob'u (temperature) ekle.

### Adım 5: perplexity

```python
import math


def perplexity(prob_fn, sentences):
    total_log_prob = 0.0
    total_tokens = 0
    for sentence in sentences:
        padded = ["<s>"] + sentence + ["</s>"]
        for i in range(1, len(padded)):
            p = prob_fn(padded[i - 1], padded[i])
            total_log_prob += math.log(max(p, 1e-12))
            total_tokens += 1
    return math.exp(-total_log_prob / total_tokens)
```

Düşük daha iyidir. Brown corpus için, iyi ayarlanmış bir 4-gram KN modeli 140 civarı perplexity'ye ulaşır. Aynı test set üzerinde bir transformer LM 15-30 alır. Açık yaklaşık 10x'tir. O açık alanın yoluna devam etmesinin sebebidir.

## Kullan

- **Klasik NLP öğretimi.** Smoothing, MLE ve perplexity'ye alabileceğin en net maruziyet.
- **KenLM.** Üretim n-gram kütüphanesi. Düşük latency'nin önemli olduğu konuşma ve MT sistemlerinde rescorer olarak kullanılır.
- **Cihaz üzerinde autocomplete.** Klavyelerde trigram modeller. Hâlâ.
- **Baseline'lar.** Sinirsel LM'inin iyi olduğunu ilan etmeden önce her zaman bir n-gram LM perplexity'si hesapla. Transformer'ın KN'yi geniş bir farkla yenmiyorsa, bir şey yanlış.

## Yayınla

`outputs/prompt-lm-baseline.md` olarak kaydet:

```markdown
---
name: lm-baseline
description: Build a reproducible n-gram language model baseline before training a neural LM.
phase: 5
lesson: 16
---

Given a corpus and target use (next-word prediction, rescoring, perplexity baseline), output:

1. N-gram order. Trigram for general English, 4-gram if corpus is large, 5-gram for speech rescoring.
2. Smoothing. Modified Kneser-Ney is the default; Laplace only for teaching.
3. Library. `kenlm` for production, `nltk.lm` for teaching, roll your own only to learn.
4. Evaluation. Held-out perplexity with consistent tokenization between train and test sets.

Refuse to report perplexity computed with different tokenization between systems being compared — perplexity numbers are comparable only under identical tokenization. Flag OOV rate in test set; KN handles OOV poorly unless you reserve a special <UNK> token during training.
```

## Alıştırmalar

1. **Kolay.** 1,000 cümlelik bir Shakespeare corpus'unda bir trigram LM eğit. 20 cümle üret. Yerel olarak mantıklı ama global olarak tutarsız olacaklar. Kanonik demo budur.
2. **Orta.** Bir held-out Shakespeare split'inde KN modelin için perplexity uygula. Laplace'a karşı karşılaştır. KN'nin perplexity'yi %30-50 düşürdüğünü görmelisin.
3. **Zor.** Trigram bir yazım düzeltici kur: yanlış yazılmış bir kelime ve bağlamı verildiğinde, düzeltmeler üret ve LM altında bağlam olasılığına göre sırala. Birkbeck yazım corpus'unda (kamuya açık) değerlendir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| N-gram | Kelime dizisi | `n` ardışık token dizisi. |
| Smoothing | Sıfırlardan kaçınma | Görülmemiş olayların sıfır olmayan olasılık alması için olasılık kütlesini yeniden dağıtma. |
| Perplexity | LM kalite metriği | Held-out veride `exp(-average log-prob)`. Düşük daha iyi. |
| Backoff | Daha kısa bağlama fallback | Trigram sayımı sıfırsa, bigram kullan. Katz backoff bunu formalize eder. |
| Kneser-Ney | N-gram'lar için en iyi smoothing | Absolute discounting + düşük dereceli model için continuation probability. |
| Continuation probability | KN'ye özgü | Ham sayımla değil, `w`'nin geçtiği bağlam sayısıyla ağırlıklandırılmış `P(w)`. |

## İleri Okuma

- [Jurafsky and Martin — Speech and Language Processing, Chapter 3 (2026 draft)](https://web.stanford.edu/~jurafsky/slp3/3.pdf) — n-gram LM'lerin ve smoothing'in kanonik işlemesi.
- [Chen and Goodman (1998). An Empirical Study of Smoothing Techniques for Language Modeling](https://dash.harvard.edu/handle/1/25104739) — Kneser-Ney'i en iyi n-gram smoother olarak yerleştiren makale.
- [Kneser and Ney (1995). Improved Backing-off for M-gram Language Modeling](https://ieeexplore.ieee.org/document/479394) — orijinal KN makalesi.
- [KenLM](https://kheafield.com/code/kenlm/) — hızlı üretim n-gram LM, latency-duyarlı uygulamalar için 2026'da hâlâ kullanılıyor.
