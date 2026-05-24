# Coreference Çözümleme

> "She called him. He did not answer. The doctor was at lunch." İki kişiye üç referans ve kimsenin adı yok. Coreference çözümleme kimin kim olduğunu çözer.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 06 (NER), Faz 5 · 07 (POS & Ayrıştırma)
**Süre:** ~60 dakika

## Sorun

300 kelimelik bir makaleden Apple Inc.'in her bahsini çıkar. Makale "Apple" dediğinde kolay. "the company", "they", "Cupertino's technology giant" ya da "Jobs's firm" dediğinde zor. Bu mention'ları aynı entity'ye çözümlemeden, NER pipeline'ın mention'ların %60-80'ini kaçırır.

Coreference çözümleme, aynı gerçek dünya entity'sine referans veren her ifadeyi tek bir kümeye bağlar. Yüzey seviyesi NLP (NER, ayrıştırma) ile downstream semantik (IE, QA, özetleme, KG) arasındaki yapıştırıcıdır.

2026'da neden önemli:

- Özetleme: "The CEO announced..." vs "Tim Cook announced..." — özet CEO'yu adlandırmalı.
- Soru cevaplama: "Who did she call?" "she"yi çözümlemeyi gerektirir.
- Bilgi çıkarımı: "PER1 founded Apple" ve "Jobs founded Apple" ayrı girdiler olan bir knowledge graph yanlıştır.
- Çok belgeli IE: aynı olay hakkındaki makalelerde mention'ları birleştirmek cross-document coreference'tır.

## Kavram

![Coreference kümeleme: mention'lar → entity'ler](../assets/coref.svg)

**Görev.** Girdi: bir belge. Çıktı: her kümenin bir entity'ye referans verdiği mention'lar (span'lar) kümelemesi.

**Mention türleri.**

- **Named entity.** "Tim Cook"
- **Nominal.** "the CEO", "the company"
- **Pronominal.** "he", "she", "they", "it"
- **Appositive.** "Tim Cook, Apple's CEO,"

**Mimariler.**

1. **Kural tabanlı (Hobbs, 1978).** Gramer kuralları kullanan sentaktik-ağaç tabanlı pronoun çözümleme. İyi baseline. Pronoun'larda yenmesi şaşırtıcı derecede zor.
2. **Mention-pair sınıflandırıcı.** Her mention çifti (m_i, m_j) için corefer olup olmadıklarını tahmin et. Transitive closure ile kümele. 2016 öncesi standart.
3. **Mention-ranking.** Her mention için aday antecedent'ları ("antecedent yok" dahil) sırala. En üstü seç.
4. **Span tabanlı end-to-end (Lee et al., 2017).** Transformer encoder. Bir uzunluk sınırına kadar tüm aday span'ları sırala. Mention skorlarını tahmin et. Her span için antecedent-olasılığı tahmin et. Greedy kümele. Modern varsayılan.
5. **Generative (2024+).** Bir LLM'e prompt: "Bu metindeki her pronoun'u ve antecedent'ini listele." Kolay durumlarda iyi çalışır, uzun belgelerde ve nadir referent'larda zorlanır.

**Değerlendirme metrikleri.** Beş standart metrik (MUC, B³, CEAF, BLANC, LEA) çünkü hiçbir tek metrik kümeleme kalitesini yakalamaz. İlk üçünün ortalamasını CoNLL F1 olarak raporla. CoNLL-2012'de 2026'da state-of-the-art: ~83 F1.

**Bilinen zor durumlar.**

- Sayfalar önce tanıtılmış entity'lere referans veren belirli betimlemeler.
- Bridging anaphora ("the wheels" → önceden bahsedilmiş bir araba).
- Çince ve Japonca gibi dillerde sıfır anaphora.
- Cataphora (referent'ten önce pronoun): "When **she** walked in, Mary smiled."

## İnşa Et

### Adım 1: önceden eğitilmiş nöral coreference (AllenNLP / spaCy-experimental)

```python
import spacy
nlp = spacy.load("en_coreference_web_trf")   # deneysel model
doc = nlp("Apple announced new products. The company said they would ship soon.")
for cluster in doc._.coref_clusters:
    print(cluster, "->", [m.text for m in cluster])
```

Daha uzun bir belgede, şuna benzer bir şey alırsın:
- Cluster 1: [Apple, The company, they]
- Cluster 2: [new products]

### Adım 2: kural tabanlı pronoun çözümleyici (öğretim)

Yalnızca stdlib implementasyon için `code/main.py`'a bak:

1. Mention'ları çıkar: named entity'ler (büyük harfli span'lar), pronoun'lar (sözlük lookup), belirli betimlemeler ("the X").
2. Her pronoun için, önceki K mention'a bak ve onları şuna göre puanla:
   - cinsiyet/sayı uyumu (heuristic)
   - recency (yakın olan kazanır)
   - sentaktik rol (özneler tercih edilir)
3. En yüksek skorlu antecedent'a bağla.

Nöral modellerle rekabetçi değil. Ama arama uzayını ve end-to-end bir modelin yapması gereken kararları gösterir.

### Adım 3: coreference için LLM'leri kullanma

```python
prompt = f"""Text: {text}

List every pronoun and noun phrase that refers to a person or company.
Cluster them by what they refer to. Output JSON:
[{{"entity": "Apple", "mentions": ["Apple", "the company", "it"]}}, ...]
"""
```

İzlenecek iki başarısızlık modu. Birincisi, LLM'ler aşırı birleştirir ("him" ve "her" iki farklı kişiye referans veriyor olabilir). İkincisi, LLM'ler uzun belgelerde sessizce mention'ları düşürür. Her zaman span-offset kontrolleriyle doğrula.

### Adım 4: değerlendirme

Standart conll-2012 script'i MUC, B³, CEAF-φ4'ü hesaplar ve ortalamayı raporlar. Şirket içi eval için, anote test setinde span seviyesi precision ve recall ile başla, sonra mention-linking F1 ekle.

## Tuzaklar

- **Singleton patlaması.** Bazı sistemler her mention'ı kendi kümesi olarak raporlar. B³ hoşgörülüdür. MUC bunu cezalandırır. Her zaman üç metriği de kontrol et.
- **Uzun bağlamda pronoun'lar.** 2,000 token üzerindeki belgelerde performans ~15 F1 düşer. Dikkatli chunk'la.
- **Cinsiyet varsayımları.** Sabit kodlu cinsiyet kuralları non-binary referent'larda, organizasyonlarda, hayvanlarda bozulur. Öğrenilmiş modeller ya da nötr puanlama kullan.
- **Uzun belgelerde LLM drift'i.** Tek bir API çağrısı 50+ paragraf boyunca mention'ları güvenilir biçimde kümeleyemez. Sliding-window + merge kullan.

## Kullan

2026 stack'i:

| Durum | Seç |
|-----------|------|
| İngilizce, tek belge | `en_coreference_web_trf` (spaCy-experimental) ya da AllenNLP nöral coref |
| Çok dilli | OntoNotes ya da Multilingual CoNLL üzerinde eğitilmiş SpanBERT / XLM-R |
| Cross-document event coref | Özelleşmiş end-to-end modeller (2025–26 SOTA) |
| Hızlı LLM baseline'ı | Yapılı çıktı coref prompt'uyla GPT-4o / Claude |
| Üretim diyalog sistemleri | Kural tabanlı fallback + nöral birincil + kritik slot'lar için manuel inceleme |

2026'da gönderilen entegrasyon deseni: önce NER çalıştır, coref çalıştır, coref kümelerini NER entity'lerine birleştir. Downstream görevler mention başına bir entity değil, küme başına bir entity görür.

## Yayınla

`outputs/skill-coref-picker.md` olarak kaydet:

```markdown
---
name: coref-picker
description: Pick a coreference approach, evaluation plan, and integration strategy.
version: 1.0.0
phase: 5
lesson: 24
tags: [nlp, coref, information-extraction]
---

Given a use case (single-doc / multi-doc, domain, language), output:

1. Approach. Rule-based / neural span-based / LLM-prompted / hybrid. One-sentence reason.
2. Model. Named checkpoint if neural.
3. Integration. Order of operations: tokenize → NER → coref → downstream task.
4. Evaluation. CoNLL F1 (MUC + B³ + CEAF-φ4 average) on held-out set + manual cluster review on 20 documents.

Refuse LLM-only coref for documents over 2,000 tokens without sliding-window merge. Refuse any pipeline that runs coref without a mention-level precision-recall report. Flag gender-heuristic systems deployed in demographically diverse text.
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki kural tabanlı çözümleyiciyi elle hazırlanmış 5 paragrafta çalıştır. Ground truth'a karşı mention-link doğruluğunu ölç.
2. **Orta.** Bir haber makalesinde önceden eğitilmiş nöral coref modeli kullan. Kümeleri kendi manuel anotasyonuna karşı karşılaştır. Nerede başarısız oldu?
3. **Zor.** Coref-zenginleştirilmiş NER pipeline'ı kur: önce NER, sonra coref kümeleri yoluyla birleştir. 100 makalede yalnızca-NER'a karşı entity-kapsama iyileştirmesini ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Mention | Bir referans | Bir entity'ye referans veren metnin bir span'ı (isim, pronoun, isim öbeği). |
| Antecedent | "it"in referans verdiği | Daha sonraki bir mention'ın corefer ettiği daha önceki mention. |
| Cluster | Entity'nin mention'ları | Aynı gerçek dünya entity'sine referans veren mention'lar kümesi. |
| Anaphora | Geriye referans | Sonraki mention öncekine referans verir ("he" → "John"). |
| Cataphora | İleriye referans | Önceki mention sonrakine referans verir ("When he arrived, John..."). |
| Bridging | Örtük referans | "I bought a car. The wheels were bad." (O arabanın tekerlekleri.) |
| CoNLL F1 | Leaderboard'lardaki sayı | MUC, B³, CEAF-φ4 F1 skorlarının ortalaması. |

## İleri Okuma

- [Jurafsky & Martin, SLP3 Ch. 26 — Coreference Resolution and Entity Linking](https://web.stanford.edu/~jurafsky/slp3/26.pdf) — kanonik ders kitabı bölümü.
- [Lee et al. (2017). End-to-end Neural Coreference Resolution](https://arxiv.org/abs/1707.07045) — span tabanlı end-to-end.
- [Joshi et al. (2020). SpanBERT](https://arxiv.org/abs/1907.10529) — coref'i iyileştiren pretraining.
- [Pradhan et al. (2012). CoNLL-2012 Shared Task](https://aclanthology.org/W12-4501/) — benchmark.
- [Hobbs (1978). Resolving Pronoun References](https://www.sciencedirect.com/science/article/pii/0024384178900064) — kural tabanlı klasik.
