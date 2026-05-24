# POS Tagging ve Sentaktik Ayrıştırma

> Dilbilgisi bir süre modası geçmişti. Sonra her LLM pipeline'ı yapılı çıkarımı doğrulamak zorunda kaldı ve geri döndü.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 01 (Metin İşleme), Faz 2 · 14 (Naive Bayes)
**Süre:** ~45 dakika

## Sorun

Ders 01, lemmatization'ın bir POS tag'ine ihtiyacı olduğunu vaat etti. `running`'in fiil olduğunu bilmeden, bir lemmatizer onu `run`'a indirgeyemez. `better`'ın sıfat olduğunu bilmeden, `good`'a indirgeyemez.

O vaat bütün bir alt alanı sakladı. POS tagging dilbilgisel kategoriler atar. Sentaktik ayrıştırma cümlenin ağaç yapısını kurtarır: hangi kelimenin hangisini değiştirdiği, hangi fiilin hangi argümanları yönettiği. Klasik NLP, ikisini de yirmi yıl boyunca rafine etti. Sonra deep learning, ikisini önceden eğitilmiş bir transformer'ın üstünde token-classification görevine çöktürdü ve araştırma topluluğu yoluna devam etti.

Uygulama topluluğu değil. Her yapılı-çıkarım pipeline'ı arka planda hâlâ POS ve bağımlılık ağaçları kullanıyor. LLM üretimi JSON dilbilgisel kısıtlamalara karşı doğrulanıyor. Soru-cevap sistemleri sorguları bağımlılık ayrıştırmalarını kullanarak ayrıştırıyor. Makine çeviri kalitesi değerlendiricileri ayrıştırma ağaçlarının hizalanmasını kontrol ediyor.

Bilinmeye değer. Bu ders tag setlerini, baseline'ları ve sıfırdan uygulamayı bırakıp spaCy'yi çağırdığın noktayı tanıtır.

## Kavram

**POS tagging** her token'ı bir dilbilgisel kategoriyle etiketler. **Penn Treebank (PTB)** tag set'i İngilizce varsayılanıdır. Gündelik okuyucunun gereksiz bulduğu ayrımlarla 36 tag: `NN` tekil isim, `NNS` çoğul isim, `NNP` özel isim tekil, `VBD` fiil geçmiş zaman, `VBZ` fiil 3. tekil şahıs şimdiki zaman, vb. **Universal Dependencies (UD)** tag set'i daha kabadır (17 tag) ve dilden bağımsızdır; cross-lingual çalışmalar için varsayılan oldu.

```
The/DET cats/NOUN were/AUX running/VERB at/ADP 3pm/NOUN ./PUNCT
```

**Sentaktik ayrıştırma** bir ağaç üretir. İki ana stil:

- **Constituency ayrıştırma.** İsim öbekleri, fiil öbekleri, edat öbekleri birbirinin içine yuvalanır. Çıktı, kelimelerin yapraklar olduğu non-terminal kategorilerin (NP, VP, PP) bir ağacıdır.
- **Dependency ayrıştırma.** Her kelimenin bağlı olduğu tek bir head kelimesi vardır, bir dilbilgisel ilişkiyle etiketlenmiş. Çıktı, her kenarın bir (head, dependent, relation) üçlüsü olduğu bir ağaçtır.

Dependency ayrıştırma 2010'larda kazandı çünkü diller arasında, özellikle serbest kelime sıralı olanlar arasında, temiz biçimde genelleşir.

```
running ROOT
cats, running'in nsubj'i
were, running'in aux'u
at, running'in prep'i
3pm, at'in pobj'i
```

## İnşa Et

### Adım 1: en sık tag baseline'ı

İşe yarayan en aptal POS tagger. Her kelime için, eğitimde en çok sahip olduğu tag'i tahmin et.

```python
from collections import Counter, defaultdict


def train_mft(train_examples):
    word_tag_counts = defaultdict(Counter)
    all_tags = Counter()
    for tokens, tags in train_examples:
        for token, tag in zip(tokens, tags):
            word_tag_counts[token.lower()][tag] += 1
            all_tags[tag] += 1
    word_best = {w: c.most_common(1)[0][0] for w, c in word_tag_counts.items()}
    default_tag = all_tags.most_common(1)[0][0]
    return word_best, default_tag


def predict_mft(tokens, word_best, default_tag):
    return [word_best.get(t.lower(), default_tag) for t in tokens]
```

Brown corpus'ta bu baseline ~%85 doğruluğa ulaşır. İyi değil ama ciddi bir modelin altına düşmemesi gereken zemin.

### Adım 2: bigram HMM tagger

Dizinin ortak olasılığını modelle:

```
P(tags, words) = prod P(tag_i | tag_{i-1}) * P(word_i | tag_i)
```

İki tablo: geçiş olasılıkları (önceki tag verildiğinde tag), emisyon olasılıkları (tag verildiğinde kelime). İkisini de sayımlardan Laplace smoothing ile tahmin et. Viterbi (tag lattice'i üzerinde dinamik programlama) ile decode et.

```python
import math


def train_hmm(train_examples, alpha=0.01):
    transitions = defaultdict(Counter)
    emissions = defaultdict(Counter)
    tags = set()
    vocab = set()

    for tokens, ts in train_examples:
        prev = "<BOS>"
        for token, tag in zip(tokens, ts):
            transitions[prev][tag] += 1
            emissions[tag][token.lower()] += 1
            tags.add(tag)
            vocab.add(token.lower())
            prev = tag
        transitions[prev]["<EOS>"] += 1

    return transitions, emissions, tags, vocab


def log_prob(table, given, key, smooth_denom, alpha):
    return math.log((table[given].get(key, 0) + alpha) / smooth_denom)


def viterbi(tokens, transitions, emissions, tags, vocab, alpha=0.01):
    tags_list = list(tags)
    n = len(tokens)
    V = [[0.0] * len(tags_list) for _ in range(n)]
    back = [[0] * len(tags_list) for _ in range(n)]

    for j, tag in enumerate(tags_list):
        em_denom = sum(emissions[tag].values()) + alpha * (len(vocab) + 1)
        tr_denom = sum(transitions["<BOS>"].values()) + alpha * (len(tags_list) + 1)
        tr = log_prob(transitions, "<BOS>", tag, tr_denom, alpha)
        em = log_prob(emissions, tag, tokens[0].lower(), em_denom, alpha)
        V[0][j] = tr + em
        back[0][j] = 0

    for i in range(1, n):
        for j, tag in enumerate(tags_list):
            em_denom = sum(emissions[tag].values()) + alpha * (len(vocab) + 1)
            em = log_prob(emissions, tag, tokens[i].lower(), em_denom, alpha)
            best_prev = 0
            best_score = -1e30
            for k, prev_tag in enumerate(tags_list):
                tr_denom = sum(transitions[prev_tag].values()) + alpha * (len(tags_list) + 1)
                tr = log_prob(transitions, prev_tag, tag, tr_denom, alpha)
                score = V[i - 1][k] + tr + em
                if score > best_score:
                    best_score = score
                    best_prev = k
            V[i][j] = best_score
            back[i][j] = best_prev

    last_best = max(range(len(tags_list)), key=lambda j: V[n - 1][j])
    path = [last_best]
    for i in range(n - 1, 0, -1):
        path.append(back[i][path[-1]])
    return [tags_list[j] for j in reversed(path)]
```

Brown üzerinde bigram HMM ~%93 doğruluğa ulaşır. %85'ten %93'e sıçrama çoğunlukla geçiş olasılıklarıdır — model `DET NOUN`'un yaygın ve `NOUN DET`'in nadir olduğunu öğrenir.

### Adım 3: modern tagger'lar bunu neden yener

Geçiş + emisyon olasılıkları yereldir. "I bought a saw"da `saw`'un isim ama "I saw the movie"da fiil olduğunu yakalayamazlar. Rastgele feature'lı (son ek, kelime şekli, önce ve sonraki kelime, kelimenin kendisi) bir CRF ~%97'ye ulaşır. Bir BiLSTM-CRF ya da transformer ~%98+'a ulaşır.

Bu görev üzerindeki tavan annotator anlaşmazlığıyla belirlenir. İnsan annotator'ları Penn Treebank'ta yaklaşık %97 oranında anlaşırlar. %98'i geçen modeller muhtemelen test set'ine overfit ediyor.

### Adım 4: dependency ayrıştırma taslağı

Sıfırdan tam dependency ayrıştırma kapsam dışı; kanonik ders kitabı işlemesi Jurafsky ve Martin'dedir. Bilmen gereken iki klasik aile:

- **Transition tabanlı** ayrıştırıcılar (arc-eager, arc-standard) bir shift-reduce ayrıştırıcı gibi davranır: token'ları okur, bir stack'e iter ve arc'lar oluşturan reduce eylemleri uygular. Greedy decoding hızlıdır. Klasik implementasyon MaltParser'dır. Modern sinirsel sürüm: Chen ve Manning'in transition tabanlı ayrıştırıcısı.
- **Graph tabanlı** ayrıştırıcılar (Eisner'in algoritması, Dozat-Manning biaffine) olası her head-dependent kenarını puanlar ve maksimum spanning ağacı seçer. Daha yavaş ama daha doğru.

Çoğu uygulamalı iş için, spaCy'yi çağır:

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("The cats were running at 3pm.")
for token in doc:
    print(f"{token.text:10s} tag={token.tag_:5s} pos={token.pos_:6s} dep={token.dep_:10s} head={token.head.text}")
```

```
The        tag=DT    pos=DET    dep=det        head=cats
cats       tag=NNS   pos=NOUN   dep=nsubj      head=running
were       tag=VBD   pos=AUX    dep=aux        head=running
running    tag=VBG   pos=VERB   dep=ROOT       head=running
at         tag=IN    pos=ADP    dep=prep       head=running
3pm        tag=NN    pos=NOUN   dep=pobj       head=at
.          tag=.     pos=PUNCT  dep=punct      head=running
```

`dep` sütununu aşağıdan yukarı oku, cümlenin dilbilgisel yapısı ortaya çıkar.

## Kullan

Her üretim NLP kütüphanesi standart pipeline'ın parçası olarak POS ve dependency parser'ları içerir.

- **spaCy** (`en_core_web_sm` / `md` / `lg` / `trf`). Hızlı, doğru, tokenleştirme + NER + lemmatization ile entegre. `token.tag_` (Penn), `token.pos_` (UD), `token.dep_` (dependency ilişkisi).
- **Stanford NLP (stanza)**. Stanford'un CoreNLP halefi. 60+ dilde state-of-the-art.
- **trankit**. Transformer tabanlı, iyi UD doğruluğu.
- **NLTK**. `pos_tag`. Kullanılabilir, yavaş, eski. Öğretim için yeterli.

### 2026'da bu hâlâ nerede önemli

- **Lemmatization.** Ders 01 doğru lemmatize etmek için POS'a ihtiyaç duyar. Her zaman.
- **LLM çıktılarından yapılı çıkarım.** Üretilen bir cümlenin dilbilgisel kısıtlamalara saygı duyduğunu doğrula (örneğin özne-fiil uyumu, gerekli niteleyiciler).
- **Aspect-based sentiment.** Dependency ayrıştırmaları sana hangi sıfatın hangi ismi değiştirdiğini söyler.
- **Sorgu anlama.** "Wes Anderson tarafından yönetilen Bill Murray oynayan filmler" ayrıştırma yoluyla yapılı kısıtlamalara ayrışır.
- **Cross-lingual transfer.** UD tag'leri ve dependency ilişkileri dilden bağımsızdır, yeni dillerin zero-shot yapılı analizini mümkün kılar.
- **Düşük-compute pipeline'ları.** Bir transformer gönderemiyorsan, POS + dependency parse + gazetteer seni şaşırtıcı derecede ileri götürür.

## Yayınla

`outputs/skill-grammar-pipeline.md` olarak kaydet:

```markdown
---
name: grammar-pipeline
description: Design a classical POS + dependency pipeline for a downstream NLP task.
version: 1.0.0
phase: 5
lesson: 07
tags: [nlp, pos, parsing]
---

Given a downstream task (information extraction, rewrite validation, query decomposition, lemmatization), you output:

1. Tagset to use. Penn Treebank for English-only legacy pipelines, Universal Dependencies for multilingual or cross-lingual.
2. Library. spaCy for most production, stanza for academic-grade multilingual, trankit for highest UD accuracy. Name the specific model ID.
3. Integration pattern. Show the 3-5 lines that call the library and consume the needed attributes (`.pos_`, `.dep_`, `.head`).
4. Failure mode to test. Noun-verb ambiguity (`saw`, `book`, `can`) and PP-attachment ambiguity are the classical traps. Sample 20 outputs and eyeball.

Refuse to recommend rolling your own parser. Building parsers from scratch is a research project, not an application task. Flag any pipeline that consumes POS tags without handling lowercase/uppercase variants as fragile.
```

## Alıştırmalar

1. **Kolay.** Küçük bir tag'lenmiş corpus üzerinde (örneğin NLTK'nın Brown alt seti) en sık tag baseline'ını kullanarak held-out cümlelerde doğruluğu ölç. ~%85 sonucunu doğrula.
2. **Orta.** Yukarıdaki bigram HMM'i eğit ve tag başına precision/recall raporla. HMM en çok hangi tag'leri karıştırıyor?
3. **Zor.** spaCy'nin dependency ayrıştırmasını kullanarak 1000 cümlelik bir örnekten özne-fiil-nesne üçlüleri çıkar. Elle etiketlenmiş 50 üçlü üzerinde değerlendir. Çıkarımın nerede başarısız olduğunu belgele (genellikle edilgenler, koordinasyonlar ve eklenmiş özneler).

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| POS tag | Kelimenin tipi | Dilbilgisel kategori. PTB'nin 36'sı var; UD'nin 17'si. |
| Penn Treebank | Standart tag seti | İngilizceye özgü. İnce-taneli fiil zamanları ve isim sayısı. |
| Universal Dependencies | Çok dilli tag seti | PTB'den daha kaba; dilden bağımsız; cross-lingual çalışma için varsayılan. |
| Dependency parse | Cümle ağacı | Her kelimenin bir head'i var, her kenarın bir dilbilgisel ilişkisi var. |
| Viterbi | Dinamik programlama | Verilen emisyonlar ve geçişler için en yüksek olasılıklı tag dizisini bulur. |

## İleri Okuma

- [Jurafsky and Martin — Speech and Language Processing, chapters 8 and 18](https://web.stanford.edu/~jurafsky/slp3/) — POS ve ayrıştırmanın kanonik ders kitabı işlemesi.
- [Universal Dependencies project](https://universaldependencies.org/) — her çok dilli ayrıştırıcı tarafından kullanılan cross-lingual tag set'i ve treebank koleksiyonu.
- [spaCy linguistic features guide](https://spacy.io/usage/linguistic-features) — `Token` üzerinde sunulan her attribute için pratik referans.
- [Chen and Manning (2014). A Fast and Accurate Dependency Parser using Neural Networks](https://nlp.stanford.edu/pubs/emnlp2014-depparser.pdf) — sinirsel ayrıştırıcıları ana akıma sokan makale.
