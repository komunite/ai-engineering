# Entity Linking ve Disambiguation

> NER "Paris"i buldu. Entity linking karar verir: Paris, Fransa? Paris Hilton? Paris, Texas? Paris (Truva prensi)? Linking olmadan, knowledge graph'in belirsiz kalır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 06 (NER), Faz 5 · 24 (Coreference Çözümleme)
**Süre:** ~60 dakika

## Sorun

Bir cümle "Jordan beat the press." diyor. NER'in "Jordan"ı PERSON olarak tag'liyor. İyi. Ama *hangi* Jordan?

- Michael Jordan (basketbol)?
- Michael B. Jordan (oyuncu)?
- Michael I. Jordan (Berkeley ML profesörü — evet, bu karışıklık ML makalelerinde gerçek)?
- Jordan (ülke)?
- Jordan (İbranice ilk isim)?

Entity linking (EL) her mention'ı bir knowledge base'deki benzersiz bir girdiye çözümler: Wikidata, Wikipedia, DBpedia ya da alan KB'in. İki alt görev:

1. **Aday üretimi.** "Jordan" verildiğinde, hangi KB girdileri makul?
2. **Disambiguation.** Bağlam verildiğinde, hangi aday doğru?

Her iki adım da öğrenilebilir. Her ikisi de benchmark edilebilir. Birleşik pipeline on yıldır stabil — değişen disambiguator'ın kalitesidir.

## Kavram

![Entity linking pipeline: mention → adaylar → disambiguate edilmiş entity](../assets/entity-linking.svg)

**Aday üretimi.** Mention yüzey formu ("Jordan") verildiğinde, bir alias indeksinde adayları ara. Wikipedia alias sözlükleri çoğu named entity'yi kapsar: "JFK" → John F. Kennedy, Jacqueline Kennedy, JFK havalimanı, JFK (film). Tipik indeks mention başına 10-30 aday döndürür.

**Disambiguation: üç yaklaşım.**

1. **Prior + context (Milne & Witten, 2008).** `P(entity | mention) × context-similarity(entity, text)`. İyi çalışır, hızlı, eğitim yok.
2. **Embedding tabanlı (ESS / REL / Blink).** Mention + bağlamı encode et. Her adayın açıklamasını encode et. Max cosine'u seç. 2020-2024 varsayılanı.
3. **Generative (GENRE, 2021; LLM tabanlı, 2023+).** Entity'nin kanonik adını token token decode et. Geçerli entity adlarının bir trie'ine kısıtlanmış, böylece çıktının geçerli bir KB id olması garanti.

**End-to-end vs pipeline.** Modern modeller (ELQ, BLINK, ExtEnD, GENRE) NER + aday üretimi + disambiguation'ı tek geçişte çalıştırır. Pipeline sistemleri üretimde hâlâ hâkim çünkü bileşenleri değiştirebilirsin.

### İki ölçüm

- **Mention recall (aday gen).** Doğru KB girdisinin aday listesinde göründüğü gold mention'ların oranı. Tüm pipeline için zemin.
- **Disambiguation accuracy / F1.** Doğru adaylar verildiğinde, top-1'in ne sıklıkla doğru olduğu.

Her zaman ikisini de raporla. %80 aday recall üzerinde %99 disambiguation'lı bir sistem %80 pipeline'dır.

## İnşa Et

### Adım 1: Wikipedia yönlendirmelerinden alias indeksi kur

```python
alias_to_entities = {
    "jordan": ["Q41421 (Michael Jordan)", "Q810 (Jordan, country)", "Q254110 (Michael B. Jordan)"],
    "paris":  ["Q90 (Paris, France)", "Q663094 (Paris, Texas)", "Q55411 (Paris Hilton)"],
    "apple":  ["Q312 (Apple Inc.)", "Q89 (apple, fruit)"],
}
```

Wikipedia alias verisi: ~18M (alias, entity) çifti. Wikidata dump'larından indir. Inverted index olarak sakla.

### Adım 2: bağlam tabanlı disambiguation

```python
def disambiguate(mention, context, alias_index, entity_desc):
    candidates = alias_index.get(mention.lower(), [])
    if not candidates:
        return None, 0.0
    context_words = set(tokenize(context))
    best, best_score = None, -1
    for entity_id in candidates:
        desc_words = set(tokenize(entity_desc[entity_id]))
        union = len(context_words | desc_words)
        score = len(context_words & desc_words) / union if union else 0.0
        if score > best_score:
            best, best_score = entity_id, score
    return best, best_score
```

Jaccard örtüşmesi bir oyuncak. Embedding'ler üzerinde cosine similarity ile değiştir (transformer sürümü için `code/main.py` step-2'ye bak).

### Adım 3: embedding tabanlı (BLINK tarzı)

```python
from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_mention(text, mention_span):
    start, end = mention_span
    marked = f"{text[:start]} [MENTION] {text[start:end]} [/MENTION] {text[end:]}"
    return encoder.encode([marked], normalize_embeddings=True)[0]

def embed_entity(entity_id, description):
    return encoder.encode([f"{entity_id}: {description}"], normalize_embeddings=True)[0]
```

İndeks zamanında, her KB entity'sini bir kez embed et. Sorgu zamanında, mention + bağlamı bir kez embed et, aday havuzuna karşı nokta çarpımı, max'ı seç.

### Adım 4: generative entity linking (kavram)

GENRE, entity'nin Wikipedia başlığını karakter karakter decode eder. Kısıtlı decoding (bkz ders 20) yalnızca geçerli başlıkların çıkarılabilmesini sağlar. KB destekli bir trie ile sıkı entegrasyon. Modern torunu REL-GEN ve yapılı çıktılı LLM-prompted EL'dir.

```python
prompt = f"""Text: {text}
Mention: {mention}
List the best Wikipedia title for this mention.
Respond with JSON: {{"title": "..."}}"""
```

Bir whitelist ile (Outlines `choice`) birleştirildiğinde, bu 2026'da gönderilecek en basit EL pipeline'ıdır.

### Adım 5: AIDA-CoNLL'da değerlendir

AIDA-CoNLL standart EL benchmark'ıdır: 1,393 Reuters makalesi, 34k mention, Wikipedia entity'leri. KB-içi doğruluğu (`P@1`) ve KB-dışı NIL-tespit oranını raporla.

## Tuzaklar

- **NIL ele alımı.** Bazı mention'lar KB'de değildir (gelişmekte olan entity'ler, ünlü olmayan kişiler). Sistemler yanlış entity tahmin etmek yerine NIL tahmin etmeli. Ayrıca ölçülür.
- **Mention sınır hataları.** Yukarı yöndeki NER kısmi span'ları kaçırır ("Bank of America" yalnızca "Bank" olarak tag'lenir). EL recall'u düşer.
- **Popülerlik bias'ı.** Eğitilmiş sistemler sık entity'leri aşırı tahmin eder. Bir ML makalesindeki "Michael I. Jordan" bahsi sıklıkla basketbol Jordan'ına link verilir.
- **Cross-lingual EL.** Çince metindeki mention'ları İngilizce Wikipedia entity'lerine eşleme. Çok dilli encoder ya da bir çeviri adımı gerektirir.
- **KB eskimesi.** Yeni şirketler, olaylar, kişiler geçen yılın Wikipedia dump'ında değil. Üretim pipeline'ları bir yenileme döngüsüne ihtiyaç duyar.

## Kullan

2026 stack'i:

| Durum | Seç |
|-----------|------|
| Genel amaçlı İngilizce + Wikipedia | BLINK ya da REL |
| Cross-lingual, KB = Wikipedia | mGENRE |
| LLM-dostu, günde az mention | Aday listesi + kısıtlı JSON ile Claude/GPT-4'e prompt |
| Alana özgü KB (tıbbi, hukuki) | KB-farkında retrieval'lı özel BERT + alan AIDA tarzı set üzerinde fine-tune |
| Aşırı düşük latency | Yalnızca tam-eşleşme prior (Milne-Witten baseline) |
| Araştırma SOTA | GENRE / ExtEnD / generative LLM-EL |

2026'da gönderilen üretim deseni: NER → coref → her mention'da EL → kümeleri küme başına tek bir kanonik entity'ye çök. Çıktı: belge başına entity başına bir KB id, mention başına bir değil.

## Yayınla

`outputs/skill-entity-linker.md` olarak kaydet:

```markdown
---
name: entity-linker
description: Design an entity linking pipeline — KB, candidate generator, disambiguator, evaluation.
version: 1.0.0
phase: 5
lesson: 25
tags: [nlp, entity-linking, knowledge-graph]
---

Given a use case (domain KB, language, volume, latency budget), output:

1. Knowledge base. Wikidata / Wikipedia / custom KB. Version date. Refresh cadence.
2. Candidate generator. Alias-index, embedding, or hybrid. Target mention recall @ K.
3. Disambiguator. Prior + context, embedding-based, generative, or LLM-prompted.
4. NIL strategy. Threshold on top score, classifier, or explicit NIL candidate.
5. Evaluation. Mention recall @ 30, top-1 accuracy, NIL-detection F1 on held-out set.

Refuse any EL pipeline without a mention-recall baseline (you cannot evaluate a disambiguator without knowing candidate gen surfaced the right entity). Refuse any pipeline using LLM-prompted EL without constrained output to valid KB ids. Flag systems where popularity bias affects minority entities (e.g. name-clashes) without domain fine-tuning.
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki prior+context disambiguator'ı 10 belirsiz mention (Paris, Jordan, Apple) üzerinde uygula. Doğru entity'yi elle etiketle. Doğruluğu ölç.
2. **Orta.** Bir sentence transformer ile 50 belirsiz mention'ı encode et. Her adayın açıklamasını embed et. Embedding tabanlı disambiguation'ı Jaccard bağlam örtüşmesine karşılaştır.
3. **Zor.** 1k-entity'lik bir alan KB'i kur (örn. şirketindeki çalışanlar + ürünler). NER + EL'i end-to-end uygula. 100 held-out cümlede precision ve recall ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Entity linking (EL) | Wikipedia'ya link | Bir mention'ı benzersiz bir KB girdisine eşle. |
| Aday üretimi | Kim olabilir? | Bir mention için makul KB girdilerinin kısa listesini döndür. |
| Disambiguation | Doğrusunu seç | Bağlam kullanarak adayları puanla, kazananı seç. |
| Alias indeksi | Lookup tablosu | Yüzey formdan → aday entity'lere eşleme. |
| NIL | KB'de değil | Hiçbir KB girdisinin eşleşmediğine dair açık tahmin. |
| KB | Knowledge base | Wikidata, Wikipedia, DBpedia ya da alan KB'in. |
| AIDA-CoNLL | Benchmark | Gold entity link'leri olan 1,393 Reuters makalesi. |

## İleri Okuma

- [Milne, Witten (2008). Learning to Link with Wikipedia](https://www.cs.waikato.ac.nz/~ihw/papers/08-DM-IHW-LearningToLinkWithWikipedia.pdf) — temel prior+context yaklaşımı.
- [Wu et al. (2020). Zero-shot Entity Linking with Dense Entity Retrieval (BLINK)](https://arxiv.org/abs/1911.03814) — embedding tabanlı iş atı.
- [De Cao et al. (2021). Autoregressive Entity Retrieval (GENRE)](https://arxiv.org/abs/2010.00904) — kısıtlı decoding'li generative EL.
- [Hoffart et al. (2011). Robust Disambiguation of Named Entities in Text (AIDA)](https://www.aclweb.org/anthology/D11-1072.pdf) — benchmark makalesi.
- [REL: An Entity Linker Standing on the Shoulders of Giants (2020)](https://arxiv.org/abs/2006.01969) — açık üretim stack'i.
