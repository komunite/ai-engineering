# Özetleme

> Extractive sistemler sana belgenin ne söylediğini söyler. Abstractive sistemler yazarın ne demek istediğini söyler. Farklı görevler, farklı tuzaklar.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 02 (BoW + TF-IDF), Faz 5 · 11 (Makine Çevirisi)
**Süre:** ~75 dakika

## Sorun

Feed'ine 2,000 kelimelik bir haber makalesi düşüyor. Onu yakalayan 120 kelimeye ihtiyacın var. Ya makaleden en önemli üç cümleyi seçebilirsin (extractive) ya da içeriği kendi kelimelerinle yeniden yazabilirsin (abstractive). İkisine de özetleme deniyor. Tamamen farklı problemler.

Extractive özetleme bir ranking problemidir. Her cümleyi puanla, top-`k`'yı döndür. Çıktı her zaman gramerlidir çünkü kelimesi kelimesine alınır. Risk, makale boyunca dağılmış içeriği kaçırmaktır.

Abstractive özetleme bir üretim problemidir. Bir transformer girdi koşuluna bağlı yeni metin üretir. Çıktı akıcı ve sıkıştırılmıştır ama kaynakta olmayan gerçekleri halüsinasyon edebilir. Risk, özgüvenli uydurmadır.

Bu ders ikisini de, her birinin sahip olduğu başarısızlık moduyla birlikte kurar.

## Kavram

![Extractive TextRank vs abstractive transformer](../assets/summarization.svg)

**Extractive.** Makaleyi, düğümlerin cümleler ve kenarların benzerlikler olduğu bir graf olarak ele al. Cümleleri her şeye ne kadar bağlı olduklarına göre puanlamak için graf üzerinde PageRank (ya da benzer bir şey) çalıştır. En yüksek puanlı cümleler özettir. Kanonik implementasyon **TextRank**'tir (Mihalcea ve Tarau, 2004).

**Abstractive.** Belge-özet çiftleri üzerinde bir transformer encoder-decoder (BART, T5, Pegasus) fine-tune et. Çıkarımda model belgeyi okur ve özeti cross-attention yoluyla token token üretir. Özellikle Pegasus, fazla fine-tuning olmadan özetlemede mükemmel olmasını sağlayan bir gap-sentence pretraining hedefi kullanır.

**ROUGE** (Recall-Oriented Understudy for Gisting Evaluation) ile değerlendirme. ROUGE-1 ve ROUGE-2 unigram ve bigram örtüşmesini puanlar. ROUGE-L en uzun ortak alt diziyi puanlar. Yüksek daha iyidir ama 40 ROUGE-L "iyi" ve 50 "olağanüstü"dür. Her makale üçünü de raporlar. `rouge-score` paketini kullan.

## İnşa Et

### Adım 1: TextRank (extractive)

```python
import math
import re
from collections import Counter


def sentence_split(text):
    return re.split(r"(?<=[.!?])\s+", text.strip())


def similarity(s1, s2):
    w1 = Counter(s1.lower().split())
    w2 = Counter(s2.lower().split())
    intersection = sum((w1 & w2).values())
    denom = math.log(len(w1) + 1) + math.log(len(w2) + 1)
    if denom == 0:
        return 0.0
    return intersection / denom


def textrank(text, top_k=3, damping=0.85, iterations=50, epsilon=1e-4):
    sentences = sentence_split(text)
    n = len(sentences)
    if n <= top_k:
        return sentences

    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                sim[i][j] = similarity(sentences[i], sentences[j])

    scores = [1.0] * n
    for _ in range(iterations):
        new_scores = [1 - damping] * n
        for i in range(n):
            total_out = sum(sim[i]) or 1e-9
            for j in range(n):
                if sim[i][j] > 0:
                    new_scores[j] += damping * sim[i][j] / total_out * scores[i]
        if max(abs(s - ns) for s, ns in zip(scores, new_scores)) < epsilon:
            scores = new_scores
            break
        scores = new_scores

    ranked = sorted(range(n), key=lambda k: scores[k], reverse=True)[:top_k]
    ranked.sort()
    return [sentences[i] for i in ranked]
```

Adı anılmaya değer iki şey. Benzerlik fonksiyonu orijinal TextRank varyantı olan log-normalize edilmiş kelime örtüşmesini kullanır. TF-IDF vektörlerinin cosine'ı da çalışır. Damping faktörü 0.85 ve yineleme sayısı PageRank varsayılanlarıdır.

### Adım 2: BART ile abstractive

```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

article = """(uzun haber makalesi metni)"""

summary = summarizer(article, max_length=120, min_length=60, do_sample=False)
print(summary[0]["summary_text"])
```

BART-large-CNN, CNN/DailyMail corpus'unda fine-tune edilmiştir. Kutudan çıkar çıkmaz haber tarzı özetler üretir. Diğer alanlar için (bilimsel makaleler, diyalog, hukuki) ilgili Pegasus checkpoint'i kullan ya da hedef veride fine-tune et.

### Adım 3: ROUGE değerlendirmesi

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
scores = scorer.score(reference_summary, generated_summary)
print({k: round(v.fmeasure, 3) for k, v in scores.items()})
```

Her zaman stemming kullan. O olmadan, "running" ve "run" farklı kelimeler olarak sayılır ve ROUGE eksik sayar.

### ROUGE'un ötesinde (2026 özetleme değerlendirmesi)

ROUGE yirmi yıldır baskın özetleme metriği oldu ve 2026'da tek başına yetersiz. NLG makalelerinin geniş ölçekli bir meta-analizi şunu gösterdi:

- **BERTScore** (contextual embedding benzerliği) 2023 boyunca yer kazandı ve şimdi çoğu özetleme makalesinde ROUGE'un yanında raporlanıyor.
- **BARTScore** değerlendirmeyi üretim olarak ele alır: özeti, önceden eğitilmiş bir BART'ın kaynağı verildiğinde ona ne kadar olası atadığına göre puanlar.
- **MoverScore** (contextual embedding'ler üzerinde Earth Mover's Distance) 2025 özetleme benchmark'larında en üst sıraya ulaştı çünkü semantik örtüşmeyi ROUGE'dan daha iyi yakalıyor.
- **FactCC** ve **QA tabanlı faithfulness** 2021-2023'te yaygındı, şimdi sıklıkla **G-Eval** (coherence, consistency, fluency, relevance'ı chain-of-thought reasoning ile puanlayan bir GPT-4 prompt zinciri) ile değiştiriliyor.
- **G-Eval** ve benzeri LLM-judge yaklaşımları, rubric'ler iyi tasarlandığında insan yargısıyla ~%80 oranında eşleşiyor.

Üretim önerisi: eski karşılaştırma için ROUGE-L, semantik örtüşme için BERTScore, coherence ve factuality için G-Eval raporla. 50-100 insan etiketli özete karşı kalibre et.

### Adım 4: factuality problemi

Abstractive özetler halüsinasyona yatkındır. Extractive özetler çok daha düşük halüsinasyon riski taşır çünkü çıktı kaynaktan kelimesi kelimesine alınır, ancak kaynak cümleleri bağlamlarından çıkarılmış, eskimiş ya da sıra dışı alıntılanmışsa hâlâ yanıltıcı olabilir. Bu, üretim sistemlerinin compliance-bitişik içerik için hâlâ extractive yöntemleri tercih etmesinin tek başına en büyük nedenidir.

Adı verilecek halüsinasyon türleri:

- **Entity takası.** Kaynak "John Smith" diyor. Özet "John Brown" diyor.
- **Sayı kayması.** Kaynak "25,000" diyor. Özet "25 milyon" diyor.
- **Polarity flip.** Kaynak "rejected the offer" diyor. Özet "accepted the offer" diyor.
- **Fact icadı.** Kaynak CEO'dan bahsetmiyor. Özet CEO'nun onayladığını söylüyor.

İşe yarayan değerlendirme yaklaşımları:

- **FactCC.** Kaynak cümlesi ile özet cümlesi arasında entailment üzerinde eğitilmiş binary sınıflandırıcı. Factual/not-factual tahmin eder.
- **QA tabanlı factuality.** Bir QA modeline cevapları kaynakta olan sorular sor. Özet farklı cevapları destekliyorsa, işaretle.
- **Entity seviyesi F1.** Kaynak vs özet named entity'leri karşılaştır. Yalnızca özette mevcut olan entity'ler şüphelidir.

Factuality'nin önemli olduğu (haber, tıbbi, hukuki, finansal) kullanıcı-yönelimli her şey için, extractive daha güvenli varsayılandır. Abstractive, döngüde bir factuality kontrolüne ihtiyaç duyar.

## Kullan

2026 stack'i:

| Kullanım durumu | Önerilen |
|---------|-------------|
| Haber, 3-5 cümlelik özet, İngilizce | `facebook/bart-large-cnn` |
| Bilimsel makaleler | `google/pegasus-pubmed` ya da ayarlanmış T5 |
| Çok belgeli, uzun-form | 32k+ bağlamlı herhangi bir LLM, prompt'lanmış |
| Diyalog özetleme | `philschmid/bart-large-cnn-samsum` |
| Tasarım gereği düşük halüsinasyon riskli extractive | TextRank ya da `sumy`'nin LSA / LexRank'i |

Uzun bağlamlı LLM'ler, compute kısıtlama olmadığında 2026'da özelleşmiş modelleri sıklıkla geçer. Tradeoff maliyet ve tekrarlanabilirliktir; özelleşmiş modeller daha tutarlı çıktılar verir.

## Yayınla

`outputs/skill-summary-picker.md` olarak kaydet:

```markdown
---
name: summary-picker
description: Pick extractive or abstractive, named library, factuality check.
version: 1.0.0
phase: 5
lesson: 12
tags: [nlp, summarization]
---

Given a task (document type, compliance requirement, length, compute budget), output:

1. Approach. Extractive or abstractive. Explain in one sentence why.
2. Starting model / library. Name it. `sumy.TextRankSummarizer`, `facebook/bart-large-cnn`, `google/pegasus-pubmed`, or an LLM prompt.
3. Evaluation plan. ROUGE-1, ROUGE-2, ROUGE-L (use rouge-score with stemming). Plus factuality check if abstractive.
4. One failure mode to probe. Entity swap is the most common in abstractive news summarization; flag samples where source entities do not appear in summary.

Refuse abstractive summarization for medical, legal, financial, or regulated content without a factuality gate. Flag input over the model's context window as needing chunked map-reduce summarization (not just truncation).
```

## Alıştırmalar

1. **Kolay.** TextRank'i 5 haber makalesinde çalıştır. En üst 3 cümleyi bir referans özetle karşılaştır. ROUGE-L ölç. CNN/DailyMail tarzı makalelerde 30-45 ROUGE-L görmelisin.
2. **Orta.** Entity seviyesi factuality uygula: kaynak ve özetten named entity'leri çıkar (spaCy), özetteki kaynak entity'lerinin recall'unu ve özet entity'lerinin kaynağa karşı precision'unu hesapla. Yüksek precision ve düşük recall güvenli ama tutuk; düşük precision halüsinasyon entity'leri demektir.
3. **Zor.** 50 CNN/DailyMail makalesinde BART-large-CNN'i bir LLM (Claude ya da GPT-4) ile karşılaştır. ROUGE-L, factuality (entity F1 ile) ve özet başına maliyet raporla. Her birinin nerede kazandığını belgele.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Extractive | Cümle seç | Kaynaktan cümleleri kelimesi kelimesine döndür. Asla halüsinasyon etmez. |
| Abstractive | Yeniden yaz | Kaynak koşullu yeni metin üret. Halüsinasyon edebilir. |
| ROUGE | Özet metriği | Sistem çıktısı ile referans arasında N-gram / LCS örtüşmesi. |
| TextRank | Graf tabanlı extractive | Cümle benzerlik grafı üzerinde PageRank. |
| Factuality | Doğru mu | Özet iddialarının kaynak tarafından desteklenip desteklenmediği. |
| Hallucination | Uydurulmuş içerik | Kaynağın desteklemediği özetteki içerik. |

## İleri Okuma

- [Mihalcea and Tarau (2004). TextRank: Bringing Order into Texts](https://aclanthology.org/W04-3252/) — extractive kanonik makale.
- [Lewis et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training](https://arxiv.org/abs/1910.13461) — BART makalesi.
- [Zhang et al. (2019). PEGASUS: Pre-training with Extracted Gap-sentences](https://arxiv.org/abs/1912.08777) — Pegasus ve gap-sentence hedefi.
- [Lin (2004). ROUGE: A Package for Automatic Evaluation of Summaries](https://aclanthology.org/W04-1013/) — ROUGE makalesi.
- [Maynez et al. (2020). On Faithfulness and Factuality in Abstractive Summarization](https://arxiv.org/abs/2005.00661) — factuality manzarası makalesi.
