# İlişki Çıkarımı ve Knowledge Graph Yapımı

> NER entity'leri buldu. Entity linking onları sabitledi. İlişki çıkarımı aralarındaki kenarları bulur. Knowledge graph düğümlerin, kenarların ve provenance'larının toplamıdır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 06 (NER), Faz 5 · 25 (Entity Linking)
**Süre:** ~60 dakika

## Sorun

Bir analist okuyor: "Tim Cook became CEO of Apple in 2011." Dört gerçek:

- `(Tim Cook, role, CEO)`
- `(Tim Cook, employer, Apple)`
- `(Tim Cook, start_date, 2011)`
- `(Apple, type, Organization)`

İlişki çıkarımı (RE), serbest metni yapılı triple'lara `(subject, relation, object)` çevirir. Bir corpus üzerinde toplayınca knowledge graph elde edersin. Topla ve sorgula, RAG, analitik ya da compliance audit'leri için bir reasoning substrate'in olur.

2026 problemi: LLM'ler ilişkileri hevesle çıkarıyor. Çok hevesle. Kaynak metnin desteklemediği triple'ları halüsinasyon ediyorlar. Provenance olmadan, gerçek triple'ları makul kurgudan ayıramazsın. 2026 cevabı AEVS tarzı anchor-and-verify pipeline'larıdır.

## Kavram

![Metin → triple'lar → knowledge graph](../assets/relation-extraction.svg)

**Triple formu.** `(subject_entity, relation_type, object_entity)`. İlişkiler kapalı bir ontolojiden (Wikidata özellikleri, FIBO, UMLS) ya da açık bir setten (OpenIE tarzı, her şey gider) gelir.

**Üç çıkarım yaklaşımı.**

1. **Kural / pattern tabanlı.** Hearst pattern'leri: "X such as Y" → `(Y, isA, X)`. Artı elle hazırlanmış regex. Kırılgan, precise, açıklanabilir.
2. **Supervised sınıflandırıcı.** Bir cümlede iki entity mention'ı verildiğinde, sabit bir setten ilişkiyi tahmin et. TACRED, ACE, KBP üzerinde eğitilir. 2015–2022 standart.
3. **Generative LLM.** Triple'ları yayınlaması için modele prompt ver. Kutudan çıkar çıkmaz çalışır. Provenance gerekir, yoksa makul görünen çöp halüsinasyon eder.

**AEVS (Anchor-Extraction-Verification-Supplement, 2026).** Mevcut halüsinasyon-azaltma framework'ü:

- **Anchor.** Her entity span'ını ve ilişki-ifade span'ını tam pozisyonlarla tanımla.
- **Extract.** Anchor span'larına bağlı triple'lar üret.
- **Verify.** Her triple öğesini kaynak metne karşı eşleştir; desteklenmeyen her şeyi reddet.
- **Supplement.** Bir kapsama geçişi, anchor'lı hiçbir span'ın düşürülmediğinden emin olur.

Halüsinasyonlar keskin biçimde düşer. Daha fazla compute gerektirir ama denetlenebilir.

**Açık-vs-kapalı tradeoff'u.**

- **Kapalı ontoloji.** Sabit özellik listesi (örn. Wikidata'nın 11,000+ özelliği). Tahmin edilebilir. Sorgulanabilir. İcat etmesi zor.
- **Açık IE.** Herhangi bir sözel ifade bir ilişki olur. Yüksek recall. Düşük precision. Sorgulaması karışık.

Üretim KG'leri genellikle karıştırır: keşif için açık IE, sonra ana grafa birleştirmeden önce ilişkileri kapalı bir ontolojiye canonicalize et.

## İnşa Et

### Adım 1: pattern tabanlı çıkarım

```python
PATTERNS = [
    (r"(?P<s>[A-Z]\w+) (?:is|was) (?:a|an|the) (?P<o>[A-Z]?\w+)", "isA"),
    (r"(?P<s>[A-Z]\w+) (?:is|was) born in (?P<o>\w+)", "bornIn"),
    (r"(?P<s>[A-Z]\w+) works? (?:at|for) (?P<o>[A-Z]\w+)", "worksAt"),
    (r"(?P<s>[A-Z]\w+) founded (?P<o>[A-Z]\w+)", "founded"),
]
```

Tam oyuncak extractor için `code/main.py`'a bak. Hearst pattern'leri alana özgü pipeline'larda hâlâ gönderiliyor çünkü debug edilebilirler.

### Adım 2: supervised ilişki sınıflandırması

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tok = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSequenceClassification.from_pretrained("Babelscape/rebel-large")

text = "Tim Cook was born in Alabama. He later became CEO of Apple."
encoded = tok(text, return_tensors="pt", truncation=True)
output = model.generate(**encoded, max_length=200)
triples = tok.batch_decode(output, skip_special_tokens=False)
```

REBEL bir seq2seq ilişki çıkarıcıdır: metin girer, triple'lar çıkar, zaten Wikidata özellik id'lerinde. Distant-supervision verisi üzerinde fine-tune edilmiş. Standart açık-ağırlık baseline.

### Adım 3: anchoring ile LLM-prompted çıkarım

```python
prompt = f"""Extract (subject, relation, object) triples from the text.
For each triple, include the exact character span in the source text.

Text: {text}

Output JSON:
[{{"subject": {{"text": "...", "span": [start, end]}},
   "relation": "...",
   "object": {{"text": "...", "span": [start, end]}}}}, ...]

Only include triples fully supported by the text. No inference beyond what is stated.
"""
```

Her dönen span'ı kaynağa karşı doğrula. `text[start:end] != triple_entity` ise reddet. Bu en minimal formunda AEVS "verify" adımıdır.

### Adım 4: kapalı ontolojiye canonicalize et

```python
RELATION_MAP = {
    "is the CEO of": "P169",       # "chief executive officer"
    "was born in":   "P19",         # "place of birth"
    "founded":        "P112",       # "founded by" (özne/nesne tersine)
    "works at":       "P108",       # "employer"
}


def canonicalize(relation):
    rel_low = relation.lower().strip()
    if rel_low in RELATION_MAP:
        return RELATION_MAP[rel_low]
    return None   # eşlenmemiş açık ilişkileri at ya da manuel incelemeye yönlendir
```

Canonicalization sıklıkla mühendislik işinin %60-80'idir. Onun için bütçe ayır.

### Adım 5: küçük bir graf kur ve sorgula

```python
triples = extract(text)
graph = {}
for s, r, o in triples:
    graph.setdefault(s, []).append((r, o))


def neighbors(node, relation=None):
    return [(r, o) for r, o in graph.get(node, []) if relation is None or r == relation]


print(neighbors("Tim Cook", relation="P108"))    # -> [(P108, Apple)]
```

Bu her RAG-over-KG sisteminin atomudur. RDF triple store'larla (Blazegraph, Virtuoso), property graph'larla (Neo4j) ya da vektör-zenginleştirilmiş graf store'larla ölçeklendir.

## Tuzaklar

- **RE'den önce coreference.** "He founded Apple" — RE "he"nin kim olduğunu bilmek zorunda. Önce coref çalıştır (ders 24).
- **Entity canonicalization.** "Apple Inc" ve "Apple" aynı düğüme çözümlenmeli. Önce entity linking (ders 25).
- **Halüsinasyon triple'lar.** LLM'ler metnin desteklemediği triple'ları yayınlar. Span doğrulamayı zorla.
- **İlişki canonicalization kayması.** Açık IE ilişkileri tutarsızdır ("was born in," "came from," "is a native of"). Kanonik id'lere çök, yoksa graf sorgulanamaz.
- **Temporal hatalar.** "Tim Cook is CEO of Apple" — şimdi doğru, 2005'te yanlış. Birçok ilişki zaman sınırlıdır. Qualifier kullan (Wikidata'da `P580` başlangıç zamanı, `P582` bitiş zamanı).
- **Alan uyumsuzluğu.** REBEL Wikipedia'da eğitildi. Hukuki, tıbbi ve bilimsel metin sıklıkla alan-fine-tune edilmiş RE modelleri gerektirir.

## Kullan

2026 stack'i:

| Durum | Seç |
|-----------|------|
| Hızlı üretim, genel alan | Wikidata canonicalization'lı REBEL ya da LlamaPred |
| Alana özgü (biomed, hukuki) | SciREX tarzı alan fine-tune + özel ontoloji |
| LLM-prompted, denetlenmiş çıktı | AEVS pipeline'ı: anchor → extract → verify → supplement |
| Yüksek hacimli haber IE'si | Pattern tabanlı + supervised hibrit |
| Sıfırdan bir KG kurma | Açık IE + manuel canonicalization geçişi |
| Temporal KG | Qualifier'larla çıkar (başlangıç/bitiş zamanı, zaman noktası) |

Entegrasyon deseni: NER → coref → entity linking → ilişki çıkarımı → ontoloji eşleme → graf yükleme. Her aşama potansiyel bir kalite kapısıdır.

## Yayınla

`outputs/skill-re-designer.md` olarak kaydet:

```markdown
---
name: re-designer
description: Design a relation extraction pipeline with provenance and canonicalization.
version: 1.0.0
phase: 5
lesson: 26
tags: [nlp, relation-extraction, knowledge-graph]
---

Given a corpus (domain, language, volume) and downstream use (KG-RAG, analytics, compliance), output:

1. Extractor. Pattern-based / supervised / LLM / AEVS hybrid. Reason tied to precision vs recall target.
2. Ontology. Closed property list (Wikidata / domain) or open IE with canonicalization pass.
3. Provenance. Every triple carries source char-span + doc id. Non-negotiable for audit.
4. Merge strategy. Canonical entity id + relation id + temporal qualifiers; dedup policy.
5. Evaluation. Precision / recall on 200 hand-labelled triples + hallucination-rate on LLM-extracted sample.

Refuse any LLM-based RE pipeline without span verification (source provenance). Refuse open-IE output flowing into a production graph without canonicalization. Flag pipelines with no temporal qualifier on time-bounded relations (employer, spouse, position).
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki pattern extractor'ı 5 haber-makalesi cümlesinde çalıştır. Precision'ı elle kontrol et.
2. **Orta.** Aynı cümlelerde REBEL (ya da küçük bir LLM) kullan. Triple'ları karşılaştır. Hangi extractor daha yüksek precision'a sahip? Daha yüksek recall'a?
3. **Zor.** AEVS pipeline'ını kur: LLM ile çıkar + kaynağa karşı span'ları doğrula. 50 Wikipedia tarzı cümlede verify adımından önce ve sonra halüsinasyon oranını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Triple | Subject-relation-object | KG'in atomik birimi olan `(s, r, o)` tuple'ı. |
| Açık IE | Her şeyi çıkar | Açık vocabulary ilişki ifadeleri; yüksek recall, düşük precision. |
| Kapalı ontoloji | Sabit şema | Sınırlı ilişki türleri seti (Wikidata, UMLS, FIBO). |
| Canonicalization | Her şeyi normalize et | Yüzey adlarını / ilişkileri kanonik id'lere eşle. |
| AEVS | Temellendirilmiş çıkarım | Anchor-Extraction-Verification-Supplement pipeline'ı (2026). |
| Provenance | Kaynak-doğruluğu bağlantısı | Her triple kaynağına bir doc id + char-span taşır. |
| Distant supervision | Ucuz etiketler | Eğitim verisi oluşturmak için metni mevcut bir KG ile hizala. |

## İleri Okuma

- [Mintz et al. (2009). Distant supervision for relation extraction without labeled data](https://www.aclweb.org/anthology/P09-1113.pdf) — distant-supervision makalesi.
- [Huguet Cabot, Navigli (2021). REBEL: Relation Extraction By End-to-end Language generation](https://aclanthology.org/2021.findings-emnlp.204.pdf) — seq2seq RE iş atı.
- [Wadden et al. (2019). Entity, Relation, and Event Extraction with Contextualized Span Representations (DyGIE++)](https://arxiv.org/abs/1909.03546) — birleşik IE.
- [AEVS — Anchor-Extraction-Verification-Supplement framework](https://www.mdpi.com/2073-431X/15/3/178) — 2026 halüsinasyon-azaltma tasarımı.
- [Wikidata SPARQL tutorial](https://www.wikidata.org/wiki/Wikidata:SPARQL_tutorial) — kanonik graf sorguları.
