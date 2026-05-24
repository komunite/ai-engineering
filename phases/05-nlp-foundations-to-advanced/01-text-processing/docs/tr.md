# Metin İşleme — Tokenleştirme, Stemming, Lemmatization

> Dil süreklidir. Modeller ayrıktır. Ön işleme bu köprüdür.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 2 · 14 (Naive Bayes)
**Süre:** ~45 dakika

## Sorun

Bir model "The cats were running." cümlesini okuyamaz. Tam sayılar okur.

Her NLP sistemi aynı üç soruyla başlar. Bir kelime nerede başlar. Kelimenin kökü nedir. "run", "running", "ran" kelimelerini ne zaman aynı şey olarak ele alacağız (işimize geldiğinde) ne zaman farklı şeyler olarak ele alacağız (gelmediğinde).

Tokenleştirmeyi yanlış yap, model çöpten öğrenir. Tokenleştiricin `don't`'u tek token olarak ele alıyor ama `do n't`'u iki token olarak ele alıyorsa, eğitim dağılımı ikiye bölünür. Stemmer'ın `organization` ve `organ`'ı aynı stem'e indiriyorsa, topic modeling ölür. Lemmatizer'ın POS bağlamına ihtiyacı varsa ama sen vermiyorsan, fiiller isim olarak ele alınır.

Bu ders üç ön işleme primitif'ini sıfırdan inşa eder, sonra NLTK ve spaCy'nin aynı işi nasıl yaptığını gösterir; böylece tradeoff'ları görebilirsin.

## Kavram

Üç işlem. Her birinin bir görevi ve bir başarısızlık modu var.

**Tokenleştirme** bir string'i token'lara böler. "Token" kasten muğlaktır çünkü doğru granülerlik göreve bağlıdır. Klasik NLP için kelime seviyesinde. Transformer'lar için subword. Boşluksuz diller için karakter.

**Stemming** son ekleri kurallarla kesip atar. Hızlı, agresif, aptal. `running -> run`. `organization -> organ`. İkincisi başarısızlık modudur.

**Lemmatization** dilbilgisi bilgisini kullanarak bir kelimeyi sözlük formuna indirger. Daha yavaş, doğru, bir lookup tablosuna ya da morfolojik analizöre ihtiyaç duyar. `ran -> run` ("ran"in "run"un geçmiş zamanı olduğunu bilmek gerekir). `better -> good` (karşılaştırma formlarını bilmek gerekir).

Pratik kural. Hız önemliyse ve gürültüye tolerans gösterebiliyorsan stemleme (arama indeksleme, kaba sınıflandırma). Anlam önemliyse lemmatize et (soru-cevap, semantik arama, kullanıcının okuyacağı her şey).

## İnşa Et

### Adım 1: regex tabanlı kelime tokenleştirici

En basit kullanışlı tokenleştirici, alfasayısal olmayan karakterlerden böler ama noktalama işaretlerini kendi token'ları olarak tutar. Mükemmel değil, nihai değil, ama tek satırda çalışır.

```python
import re

def tokenize(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[0-9]+|[^\sA-Za-z0-9]", text)
```

Öncelik sırasına göre üç desen. Opsiyonel iç apostroflu kelimeler (`don't`, `it's`). Salt sayılar. Tek başına token olarak herhangi bir boşluksuz alfasayısal olmayan karakter (noktalama).

```python
>>> tokenize("The cats weren't running at 3pm.")
['The', 'cats', "weren't", 'running', 'at', '3', 'pm', '.']
```

Dikkat edilmesi gereken başarısızlık modları. `3pm`, `['3', 'pm']`'e bölünür çünkü harf dizileri ve rakam dizileri arasında geçiş yaptık. Çoğu görev için yeterince iyi. URL'ler, e-postalar, hashtag'ler hepsi bozulur. Üretim için, genel desenlerden önce ek desenler ekle.

### Adım 2: Porter stemmer (yalnızca adım 1a)

Tam Porter algoritmasının beş kural fazı vardır. Yalnızca adım 1a en sık İngilizce son ekleri kapsar ve deseni öğretir.

```python
def stem_step_1a(word):
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies"):
        return word[:-2]
    if word.endswith("ss"):
        return word
    if word.endswith("s") and len(word) > 1:
        return word[:-1]
    return word
```

```python
>>> [stem_step_1a(w) for w in ["caresses", "ponies", "caress", "cats"]]
['caress', 'poni', 'caress', 'cat']
```

Kuralları yukarıdan aşağıya oku. `ies -> i` kuralı, `ponies -> poni`'nin sebebidir, `pony` değil. Gerçek Porter'da bunu düzeltecek adım 1b vardır. Kurallar rekabet eder. Önceki kurallar kazanır. Sıra, herhangi bir tek kuraldan daha önemlidir.

### Adım 3: lookup tabanlı lemmatizer

Lemmatization'ın kendisi morfolojiye ihtiyaç duyar. Çözülebilir bir öğretim sürümü küçük bir lemma tablosu ve bir fallback kullanır.

```python
LEMMA_TABLE = {
    ("running", "VERB"): "run",
    ("ran", "VERB"): "run",
    ("runs", "VERB"): "run",
    ("better", "ADJ"): "good",
    ("best", "ADJ"): "good",
    ("cats", "NOUN"): "cat",
    ("cat", "NOUN"): "cat",
    ("were", "VERB"): "be",
    ("was", "VERB"): "be",
    ("is", "VERB"): "be",
}

def lemmatize(word, pos):
    key = (word.lower(), pos)
    if key in LEMMA_TABLE:
        return LEMMA_TABLE[key]
    if pos == "VERB" and word.endswith("ing"):
        return word[:-3]
    if pos == "NOUN" and word.endswith("s"):
        return word[:-1]
    return word.lower()
```

```python
>>> lemmatize("running", "VERB")
'run'
>>> lemmatize("cats", "NOUN")
'cat'
>>> lemmatize("better", "ADJ")
'good'
>>> lemmatize("watched", "VERB")
'watched'
```

Son vaka, kilit öğretim anıdır. `watched` tablomuzda yok ve fallback'imiz yalnızca `ing` ile başa çıkıyor. Gerçek lemmatization `ed`'i, düzensiz fiilleri, karşılaştırma sıfatlarını, ses değişimli çoğulları (`children -> child`) kapsar. Bu nedenle üretim sistemleri WordNet'i, spaCy'nin morfolojisini ya da tam bir morfolojik analizör kullanır.

### Adım 4: hepsini bir araya bağla

```python
def preprocess(text, pos_tagger=None):
    tokens = tokenize(text)
    stems = [stem_step_1a(t.lower()) for t in tokens]
    tags = pos_tagger(tokens) if pos_tagger else [(t, "NOUN") for t in tokens]
    lemmas = [lemmatize(word, pos) for word, pos in tags]
    return {"tokens": tokens, "stems": stems, "lemmas": lemmas}
```

Eksik parça bir POS tagger'ıdır. Faz 5 · 07 (POS Tagging) bir tane kuracak. Şimdilik, her şeyi `NOUN`'a varsay ve sınırlamayı kabul et.

## Kullan

NLTK ve spaCy üretim sürümlerini içerir. Her biri birkaç satır.

### NLTK

```python
import nltk
nltk.download("punkt_tab")
nltk.download("wordnet")
nltk.download("averaged_perceptron_tagger_eng")

from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk import pos_tag

text = "The cats were running."
tokens = word_tokenize(text)
stems = [PorterStemmer().stem(t) for t in tokens]
lemmatizer = WordNetLemmatizer()
tagged = pos_tag(tokens)


def nltk_pos_to_wordnet(tag):
    if tag.startswith("V"):
        return "v"
    if tag.startswith("J"):
        return "a"
    if tag.startswith("R"):
        return "r"
    return "n"


lemmas = [lemmatizer.lemmatize(t, nltk_pos_to_wordnet(tag)) for t, tag in tagged]
```

`word_tokenize` kısaltmaları, Unicode'u, regex'inin kaçırdığı kenar durumları halleder. `PorterStemmer` beş fazın hepsini çalıştırır. `WordNetLemmatizer`, NLTK'nın Penn Treebank şemasından WordNet'in kısaltma setine çevrilmiş POS tag'ine ihtiyaç duyar. Yukarıdaki çeviri bağlantısı, çoğu tutorial'ın atladığı kısımdır.

### spaCy

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("The cats were running.")

for token in doc:
    print(token.text, token.lemma_, token.pos_)
```

```
The      the     DET
cats     cat     NOUN
were     be      AUX
running  run     VERB
.        .       PUNCT
```

spaCy tüm pipeline'ı `nlp(text)`'in arkasına saklar. Tokenleştirme, POS tagging ve lemmatization hepsi çalışır. Ölçekte NLTK'den daha hızlı. Kutudan çıktığı haliyle daha doğru. Tradeoff, bireysel bileşenleri kolayca değiştiremeyecek olmandır.

### Hangisini seçmeli

| Durum | Seç |
|-----------|------|
| Öğretim, araştırma, bileşen değiştirme | NLTK |
| Üretim, çok dilli, hız önemli | spaCy |
| Transformer pipeline'ı (zaten modelin tokenleştiricisiyle tokenleştireceksin) | `tokenizers` / `transformers` kullan ve klasik ön işlemeyi atla |

### Kimsenin sana uyarmadığı iki başarısızlık modu

Çoğu tutorial algoritmaları öğretir ve durur. İki şey gerçek bir ön işleme pipeline'ını ısırır ve neredeyse hiç ele alınmaz.

**Tekrarlanabilirlik kayması.** NLTK ve spaCy, sürümler arasında tokenleştirme ve lemmatizer davranışını değiştirir. spaCy 2.x'te `['do', "n't"]` üretirken 3.x'te `["don't"]` üretebilir. Modelin bir dağılım üzerinde eğitildi. Çıkarım artık farklı bir dağılım üzerinde çalışıyor. Doğruluk sessizce bozulur ve kimse neden olduğunu bilmez. `requirements.txt`'te kütüphane sürümlerini sabitle. 20 örnek cümlenin beklenen tokenleştirmesini donduran bir ön işleme regresyon testi yaz. Her yükseltmede çalıştır.

**Eğitim / çıkarım uyumsuzluğu.** Agresif ön işleme (küçük harfe çevirme, stopword temizleme, stemming) ile eğit, ham kullanıcı girdisine deploy et, performansın çakılışını izle. Bu, üretimdeki en yaygın NLP başarısızlığıdır. Eğitim sırasında ön işleme yapıyorsan, çıkarım sırasında özdeş fonksiyonu çalıştırmalısın. Ön işlemeyi model paketinin içinde bir fonksiyon olarak gönder, serving ekibinin yeniden yazacağı bir notebook hücresi olarak değil.

## Yayınla

Mühendislerin üç ders kitabı okumadan bir ön işleme stratejisi seçmesine yardım eden yeniden kullanılabilir bir prompt.

`outputs/prompt-preprocessing-advisor.md` olarak kaydet:

```markdown
---
name: preprocessing-advisor
description: Recommends a tokenization, stemming, and lemmatization setup for an NLP task.
phase: 5
lesson: 01
---

You advise on classical NLP preprocessing. Given a task description, you output:

1. Tokenization choice (regex, NLTK word_tokenize, spaCy, or transformer tokenizer). Explain why.
2. Whether to stem, lemmatize, both, or neither. Explain why.
3. Specific library calls. Name the functions. Quote the POS-tag translation if NLTK is involved.
4. One failure mode the user should test for.

Refuse to recommend stemming for user-visible text. Refuse to recommend lemmatization without POS tags. Flag non-English input as needing a different pipeline.
```

## Alıştırmalar

1. **Kolay.** `tokenize`'ı URL'leri tek token olarak tutacak şekilde genişlet. Test: `tokenize("Visit https://example.com today.")` tek bir URL token'ı üretmeli.
2. **Orta.** Porter adım 1b'yi uygula. Bir kelime sesli harf içeriyor ve `ed` ya da `ing` ile bitiyorsa, onu kaldır. Çift ünsüz kuralını ele al (`hopping -> hop`, `hopp` değil).
3. **Zor.** WordNet'i lookup tablosu olarak kullanan ama WordNet'te girdi olmadığında Porter stemmer'ına geri dönen bir lemmatizer kur. Düz WordNet ve düz Porter'a karşı etiketli bir corpus üzerinde doğruluğu ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Token | Bir kelime | Modelin tükettiği her hangi bir birim. Kelime, subword, karakter ya da byte olabilir. |
| Stem | Kelimenin kökü | Kural tabanlı son ek soyma sonucu. Her zaman gerçek bir kelime değil. |
| Lemma | Sözlük formu | Arayacağın form. Doğru hesaplamak için dilbilgisel bağlam gerektirir. |
| POS tag | Söz dizimi türü | NOUN, VERB, ADJ gibi kategori. Doğru lemmatize etmek için gerekli. |
| Morfoloji | Kelime şekli kuralları | Bir kelimenin zamana, sayıya, duruma göre nasıl şekil değiştirdiği. Lemmatization buna bağlıdır. |

## İleri Okuma

- [Porter, M. F. (1980). An algorithm for suffix stripping](https://tartarus.org/martin/PorterStemmer/def.txt) — orijinal makale, beş sayfa, hâlâ en net açıklama.
- [spaCy 101 — linguistic features](https://spacy.io/usage/linguistic-features) — gerçek bir pipeline nasıl bağlanır.
- [NLTK book, chapter 3](https://www.nltk.org/book/ch03.html) — henüz düşünmediğin tokenleştirme kenar durumları.
