# Duygu Analizi

> Kanonik NLP görevi. Klasik metin sınıflandırması hakkında bilmen gereken çoğu şey burada ortaya çıkıyor.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 02 (BoW + TF-IDF), Faz 2 · 14 (Naive Bayes)
**Süre:** ~75 dakika

## Sorun

"The food was not great." Pozitif mi negatif mi?

Duygu analizi kulağa basit geliyor. Yorum yapan biri bir şeyi sevip sevmediğini söyledi. Cümleyi etiketle. Bunun kanonik NLP görevi haline gelmesinin sebebi, kolay görünen her vakanın altında zor bir vakanın saklanmasıdır. Olumsuzluk anlamı tersine çevirir. Alaycılık ters yüz eder. "Not bad at all" iki negatif kodlu kelimeye rağmen pozitiftir. Emojiler çevre metinden daha fazla sinyal taşır. Alan vocabulary'si önemlidir (müzik incelemesinde `tight` ile moda incelemesinde `tight`).

Duygu analizi, klasik NLP için çalışan bir laboratuvardır. Her naif baseline'ın neden belirli bir başarısızlık modu olduğunu anlarsan, her zengin modelin neden icat edildiğini anlarsın. Bu ders sıfırdan bir Naive Bayes baseline kurar, logistic regression ekler ve üretim duygu analizini compliance düzeyinde bir probleme dönüştüren tuzakları adlandırır.

## Kavram

Klasik duygu analizi iki adımlı bir tariftir.

1. **Temsil et.** Metni bir feature vektörüne çevir. BoW, TF-IDF ya da n-gram.
2. **Sınıflandır.** Etiketli örnekler üzerinde bir lineer model (Naive Bayes, logistic regression, SVM) uydur.

Naive Bayes işe yarayan en aptal modeldir. Etiket verildiğinde her feature'ın bağımsız olduğunu varsay. Sayımlardan `P(word | positive)` ve `P(word | negative)`'i tahmin et. Çıkarımda olasılıkları çarp. "Naive" bağımsızlık varsayımı gülünç biçimde yanlıştır ama sonuçlar şaşırtıcı derecede güçlüdür. Sebep: seyrek metin feature'ları ve orta düzey veri ile, sınıflandırıcı her kelimenin hangi tarafa ne kadar yaslandığından çok hangi tarafa yaslandığıyla ilgilenir.

Logistic regression bağımsızlık varsayımını düzeltir. Negatif ağırlıklar dahil her feature için bir ağırlık öğrenir. Bigram feature olarak `not good` negatif bir ağırlık alır. Naive Bayes hiç etiketlemediği bigram'lar için bunu yapamaz.

## İnşa Et

### Adım 1: gerçek bir mini veri seti

```python
POSITIVE = [
    "absolutely loved this movie",
    "beautiful cinematography and a great story",
    "one of the best films of the year",
    "brilliant acting from the lead",
    "heartwarming and funny",
]

NEGATIVE = [
    "boring and far too long",
    "not worth your time",
    "the plot made no sense",
    "terrible acting, awful script",
    "i want my two hours back",
]
```

Kasıtlı olarak küçük. Gerçek iş on binlerce örnek kullanır (IMDb, SST-2, Yelp polarity). Matematik özdeştir.

### Adım 2: sıfırdan multinomial Naive Bayes

```python
import math
from collections import Counter


def train_nb(docs_by_class, vocab, alpha=1.0):
    class_priors = {}
    class_word_probs = {}
    total_docs = sum(len(d) for d in docs_by_class.values())

    for cls, docs in docs_by_class.items():
        class_priors[cls] = len(docs) / total_docs
        counts = Counter()
        for doc in docs:
            for token in doc:
                counts[token] += 1
        total = sum(counts.values()) + alpha * len(vocab)
        class_word_probs[cls] = {
            w: (counts[w] + alpha) / total for w in vocab
        }
    return class_priors, class_word_probs


def predict_nb(doc, class_priors, class_word_probs):
    scores = {}
    for cls in class_priors:
        s = math.log(class_priors[cls])
        for token in doc:
            if token in class_word_probs[cls]:
                s += math.log(class_word_probs[cls][token])
        scores[cls] = s
    return max(scores, key=scores.get)
```

Toplamsal smoothing (alpha=1.0) Laplace smoothing'tir. O olmadan, bir sınıfta görülmemiş bir kelimenin olasılığı sıfırdır ve log patlar. Pratikte `alpha=0.01` yaygındır. `alpha=1.0` öğretim varsayılanıdır.

### Adım 3: sıfırdan logistic regression

```python
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def train_lr(X, y, epochs=500, lr=0.05, l2=0.01):
    n_features = X.shape[1]
    w = np.zeros(n_features)
    b = 0.0
    for _ in range(epochs):
        logits = X @ w + b
        preds = sigmoid(logits)
        err = preds - y
        grad_w = X.T @ err / len(y) + l2 * w
        grad_b = err.mean()
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


def predict_lr(X, w, b):
    return (sigmoid(X @ w + b) >= 0.5).astype(int)
```

L2 regularization burada önemli. Metin feature'ları seyrektir; L2 olmadan model eğitim örneklerini ezberler. `0.01`'den başla ve ayarla.

### Adım 4: olumsuzluğu ele alma (başarısızlık modu)

"not good" ve "not bad"i düşün. Bir BoW sınıflandırıcısı `{not, good}` ve `{not, bad}` görür ve eğitimde hangisi daha çok geçtiyse ondan öğrenir. Bir bigram sınıflandırıcısı `not_good` ve `not_bad`'i görür ve onları ayrı feature'lar olarak öğrenir. Bu genellikle yeterlidir.

Bigram'ların olmadığı durumlarda işe yarayan kaba bir düzeltme: **negation scoping**. Bir olumsuzluk kelimesini takip eden token'ların önüne sonraki noktalama işaretine kadar `NOT_` ekle.

```python
NEGATION_WORDS = {"not", "no", "never", "nor", "none", "nothing", "neither"}
NEGATION_TERMINATORS = {".", "!", "?", ",", ";"}


def apply_negation(tokens):
    out = []
    negate = False
    for token in tokens:
        if token in NEGATION_TERMINATORS:
            negate = False
            out.append(token)
            continue
        if token in NEGATION_WORDS:
            negate = True
            out.append(token)
            continue
        out.append(f"NOT_{token}" if negate else token)
    return out
```

```python
>>> apply_negation(["not", "good", "at", "all", ".", "but", "funny"])
['not', 'NOT_good', 'NOT_at', 'NOT_all', '.', 'but', 'funny']
```

Şimdi `good` ve `NOT_good` farklı feature'lar. Sınıflandırıcı bunları ters ağırlıklandırabilir. Üç satır ön işleme, duygu benchmark'larında ölçülebilir doğruluk sıçraması.

### Adım 5: önemli olan değerlendirme metrikleri

Sınıflar dengesizse tek başına accuracy yanıltıcıdır. Gerçek duygu corpus'ları genellikle %70-80 pozitif ya da %70-80 negatiftir; sabit-çoğunluk sınıflandırıcısı %80 accuracy alır ve değersizdir. Aşağıdakilerin hepsini raporla:

- **Sınıf başına precision ve recall.** Sınıf başına bir çift. Sınıf dengesine saygılı tek bir sayı elde etmek için macro-average yap.
- **Macro-F1 (dengesiz veri için birincil metrik).** Eşit ağırlıklı sınıf başına F1 skorlarının ortalaması. Sınıflar dengesiz olduğunda accuracy yerine bunu kullan.
- **Weighted-F1 (alternatif).** Macro ile aynı ama sınıf frekansına göre ağırlıklı. Dengesizliğin iş açısından anlamı varken macro-F1 ile birlikte raporla.
- **Confusion matrix.** Ham sayımlar. Herhangi bir skaler metriğe güvenmeden önce her zaman incele; modelin hangi sınıf çiftini karıştırdığını ortaya çıkarır.
- **Sınıf başına hata örnekleri.** Sınıf başına 5 yanlış tahmin çek. Onları oku. Gerçek hataları okumanın yerini hiçbir şey tutmaz.

Şiddetli dengesiz veri (> 95-5 oranı) için, accuracy yerine **AUROC** ve **AUPRC** raporla. AUPRC azınlık sınıfına daha duyarlıdır, genellikle önemsediğin de odur (spam, fraud, nadir duygu).

**Kaçınılması gereken yaygın bug.** Dengesiz veride macro-F1 yerine micro-F1 raporlamak, çoğunluk sınıfına hâkim olduğu için yüksek görünen bir sayı verir. Macro-F1 seni azınlık-sınıf performansını görmeye zorlar.

```python
def evaluate(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": precision, "recall": recall, "f1": f1}
```

## Kullan

scikit-learn bunu altı satırda, doğru şekilde yapar.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words=None)),
    ("clf", LogisticRegression(C=1.0, max_iter=1000)),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

Dikkat çekilecek üç şey. `stop_words=None` olumsuzlukları tutar. `ngram_range=(1, 2)` bigram'ları ekler, böylece `not_good` bir feature olur. `sublinear_tf=True` tekrar eden kelimeleri yumuşatır. Bu üç flag, SST-2'de %75 doğruluk baseline'ı ile %85 doğruluk baseline'ı arasındaki farktır.

### Ne zaman transformer'a uzanmalı

- Alaycılık tespiti. Klasik modeller burada başarısız olur. Nokta.
- Duygunun belge ortasında değiştiği uzun değerlendirmeler.
- Aspect-based sentiment. "Kamera harikaydı ama batarya berbattı." Duyguyu aspect'lere atamalısın. Sadece transformer'lar ya da yapılı çıktı modelleri.
- İngilizce olmayan, düşük kaynaklı diller. Multilingual BERT sana bedavadan bir zero-shot baseline verir.

Yukarıdakilerden herhangi birine ihtiyacın varsa, faz 7'ye (transformer'lar deep dive) atla. Aksi takdirde, TF-IDF artı bigram'lar artı olumsuzluk işleme üzerinde Naive Bayes ya da logistic regression senin 2026 üretim baseline'ındır.

### Tekrarlanabilirlik tuzağı (tekrar)

Duygu modellerini yeniden eğitmek rutindir. Onları yeniden değerlendirmek değildir. Makalelerde raporlanan doğruluk rakamları belirli split'leri, belirli ön işlemeyi, belirli tokenleştiricileri kullanır. Yeni modelini özdeş pipeline'ı kullanmadan bir baseline ile karşılaştırırsan yanıltıcı delta'lar alırsın. Her zaman baseline'ı kendi pipeline'ında yeniden oluştur, makalenin rakamını alma.

## Yayınla

`outputs/prompt-sentiment-baseline.md` olarak kaydet:

```markdown
---
name: sentiment-baseline
description: Design a sentiment analysis baseline for a new dataset.
phase: 5
lesson: 05
---

Given a dataset description (domain, language, size, label granularity, latency budget), you output:

1. Feature extraction recipe. Specify tokenizer, n-gram range, stopword policy (usually keep), negation handling (scoped prefix or bigrams).
2. Classifier. Naive Bayes for baseline, logistic regression for production, transformer only if the domain needs sarcasm / aspects / cross-lingual.
3. Evaluation plan. Report precision, recall, F1, confusion matrix, and per-class error samples (not just scalars).
4. One failure mode to monitor post-deployment. Domain drift and sarcasm are the top two.

Refuse to recommend dropping stopwords for sentiment tasks. Refuse to report accuracy as the sole metric when classes are imbalanced (e.g., 90% positive). Flag subword-rich languages as needing FastText or transformer embeddings over word-level TF-IDF.
```

## Alıştırmalar

1. **Kolay.** `apply_negation`'ı scikit-learn pipeline'ında bir ön işleme adımı olarak ekle ve küçük bir duygu veri setinde F1 delta'sını ölç.
2. **Orta.** Sınıf ağırlıklı logistic regression uygula (scikit-learn'a `class_weight="balanced"` ver ya da gradyanı kendin türet). Sentetik bir 90-10 sınıf dengesizliğine etkisini ölç.
3. **Zor.** Duygu modelinin residual'ları üzerinde ikinci bir sınıflandırıcı eğiterek bir alaycılık detektörü kur. Deney kurulumunu belgele. Doğruluğun şansın altına düştüğünde okuyucuyu uyar (2-sınıf alaycılıkta şans seviyesi ~%50'dir ve çoğu ilk girişim oraya iniyor).

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Polarity | Pozitif ya da negatif | Binary etiket; bazen nötr ya da ince-taneli (5 yıldız) olarak genişletilir. |
| Aspect-based sentiment | Aspect başına polarity | Duyguyu metinde bahsedilen belirli varlıklara ya da niteliklere ata. |
| Negation scoping | Yakındaki token'ları tersleme | "not"tan sonraki token'ların önüne noktalamaya kadar `NOT_` ekle. |
| Laplace smoothing | Sayımlara 1 ekleme | Naive Bayes'te sıfır olasılıklı feature'ları önler. |
| L2 regularization | Ağırlıkları küçültme | Loss'a `lambda * sum(w^2)` ekler. Seyrek metin feature'ları için temeldir. |

## İleri Okuma

- [Pang and Lee (2008). Opinion Mining and Sentiment Analysis](https://www.cs.cornell.edu/home/llee/opinion-mining-sentiment-analysis-survey.html) — temel survey. Uzun ama ilk dört bölüm klasik olan her şeyi kapsar.
- [Wang and Manning (2012). Baselines and Bigrams: Simple, Good Sentiment and Topic Classification](https://aclanthology.org/P12-2018/) — kısa metinlerde bigram'lar + Naive Bayes'in yenilmesinin zor olduğunu gösteren makale.
- [scikit-learn text feature extraction docs](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction) — `CountVectorizer`, `TfidfVectorizer` ve ayarlayacağın her knob için referans.
