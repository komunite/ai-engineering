# Soru-Cevap Sistemleri

> Modern QA'i üç sistem şekillendirdi. Extractive span'ları buldu. Retrieval-augmented onları belgelerde temellendirdi. Generative cevapları üretti. Her modern AI asistanı bu üçünün karışımıdır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 11 (Makine Çevirisi), Faz 5 · 10 (Attention Mekanizması)
**Süre:** ~75 dakika

## Sorun

Bir kullanıcı "When did the first iPhone launch?" yazıyor ve "June 29, 2007." bekliyor. "Apple's history is long and varied." değil. Hiçbir cümle olmadan tek başına oturan "2007" değil. Doğrudan, temellendirilmiş, doğru bir cevap.

Son on yılda üç mimari QA'a hâkim oldu.

- **Extractive QA.** Bir soru ve cevabı içerdiği bilinen bir pasaj verildiğinde, cevap span'ının pasajdaki başlangıç ve bitiş indekslerini bul. SQuAD kanonik benchmark'tır.
- **Open-domain QA.** Pasaj verilmiyor. Önce ilgili pasajı bul, sonra bir cevap çıkar ya da üret. Bu, bugün her RAG pipeline'ının temelidir.
- **Generative / Closed-book QA.** Büyük bir dil modeli parametric belleğinden cevaplar. Retrieval yok. Çıkarımda en hızlı, gerçeklerde en az güvenilir.

2026'da trend hibrit: en iyi birkaç pasajı getir, sonra bir generative modele o pasajlarda temellendirilmiş cevap vermesi için prompt yap. Bu RAG'dir ve ders 14 retrieval yarısını derinlemesine ele alır. Bu ders QA yarısını kurar.

## Kavram

![QA mimarileri: extractive, retrieval-augmented, generative](../assets/qa.svg)

**Extractive.** Soruyu ve pasajı birlikte bir transformer (BERT ailesi) ile encode et. Cevabın başlangıç ve bitiş token indekslerini tahmin eden iki head eğit. Loss, geçerli pozisyonlar üzerinde cross-entropy'dir. Çıktı pasajdan bir span'dır. Asla halüsinasyon etmez (tasarım gereği), pasajın cevaplayamayacağı soruları asla ele almaz (tasarım gereği).

**Retrieval-augmented (RAG).** İki aşama. Önce bir retriever bir corpus'tan top-`k` pasajı bulur. İkincisi, bir reader (extractive ya da generative) o pasajları kullanarak cevap üretir. Retriever-reader ayrımı her birinin bağımsız eğitilip değerlendirilmesini sağlar. Modern RAG sıklıkla aralarına bir reranker ekler.

**Generative.** Decoder-only bir LLM (GPT, Claude, Llama) öğrenilmiş ağırlıklardan cevaplar. Retrieval adımı yok. Yaygın bilgide mükemmel, nadir ya da yakın zamanlı gerçeklerde felaket. Halüsinasyon oranı, pretraining verisindeki fact frekansıyla ters orantılıdır.

## İnşa Et

### Adım 1: önceden eğitilmiş bir modelle extractive QA

```python
from transformers import pipeline

qa = pipeline("question-answering", model="deepset/roberta-base-squad2")

passage = (
    "Apple Inc. released the first iPhone on June 29, 2007. "
    "The device was announced by Steve Jobs at Macworld in January 2007."
)
question = "When was the first iPhone released?"

answer = qa(question=question, context=passage)
print(answer)
```

```python
{'score': 0.98, 'start': 57, 'end': 70, 'answer': 'June 29, 2007'}
```

`deepset/roberta-base-squad2`, cevaplanamayan soruları içeren SQuAD 2.0 üzerinde eğitilmiştir. Varsayılan olarak, `question-answering` pipeline'ı modelin null skoru kazansa bile en yüksek skorlu span'ı döndürür — otomatik olarak boş cevap *döndürmez*. Açık "cevap yok" davranışı için, pipeline çağrısına `handle_impossible_answer=True` ver: pipeline o zaman yalnızca null skor her span skorunu aştığında boş cevap döndürür. Her iki şekilde de her zaman `score` alanını kontrol et.

### Adım 2: retrieval-augmented bir pipeline (taslak)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

corpus = [
    "Apple Inc. released the first iPhone on June 29, 2007.",
    "Macworld 2007 featured the iPhone announcement by Steve Jobs.",
    "Android launched in 2008 as Google's mobile operating system.",
    "The first iPod was released in 2001.",
]
corpus_embeddings = encoder.encode(corpus, normalize_embeddings=True)


def retrieve(question, top_k=2):
    q_emb = encoder.encode([question], normalize_embeddings=True)
    sims = (corpus_embeddings @ q_emb.T).squeeze()
    order = np.argsort(-sims)[:top_k]
    return [corpus[i] for i in order]


def answer(question):
    passages = retrieve(question, top_k=2)
    combined = " ".join(passages)
    return qa(question=question, context=combined)


print(answer("When was the first iPhone released?"))
```

İki aşamalı pipeline. Dense retriever (Sentence-BERT) semantik benzerliğe göre ilgili pasajları bulur. Extractive reader (RoBERTa-SQuAD) birleştirilmiş top pasajlardan cevap span'ını çeker. Küçük corpus'larda çalışır. Bir milyon belgelik corpus için FAISS ya da bir vector database kullan.

### Adım 3: RAG ile generative

```python
def rag_generate(question, llm):
    passages = retrieve(question, top_k=3)
    prompt = f"""Context:
{chr(10).join('- ' + p for p in passages)}

Question: {question}

Answer using only the context above. If the context does not contain the answer, say "I don't know."
"""
    return llm(prompt)
```

Prompt deseni önemli. Modele bağlamda temellenmesini ve bağlam yetersizse "I don't know" döndürmesini açıkça söylemek, naif prompting'e kıyasla halüsinasyon oranlarını %40-60 düşürür. Daha ayrıntılı desenler alıntılar, güven skorları ve yapılı çıkarım ekler.

### Adım 4: gerçek dünyayı yansıtan değerlendirme

SQuAD **Exact Match (EM)** ve **token seviyesi F1** kullanır. EM, normalizasyondan sonra (küçük harf, noktalama kaldırma, makaleleri kaldırma) sıkı bir eşleşmedir — ya tahmin tam eşleşir ya da 0 puan alır. F1, tahmin ve referans arasındaki token örtüşmesi üzerinde hesaplanır ve kısmi kredi verir. İkisi de paraphrase'lere eksik kredi verir: "June 29, 2007" vs "June 29th, 2007" tipik olarak 0 EM alır (ordinal normalizasyonu bozar) ama yine de örtüşen token'lardan önemli F1 kazanır.

Üretim QA için:

- **Cevap doğruluğu** (LLM-judged ya da insan-judged, çünkü metrikler semantik denkliği yakalayamaz).
- **Citation doğruluğu.** Alıntılanan pasaj gerçekten cevabı destekliyor mu? Üretilen alıntılar ile getirilen pasajlar arasında string eşleşmesiyle otomatik olarak kontrolü tarivaldir.
- **Refusal kalibrasyonu.** Cevap getirilen pasajlarda yokken, sistem doğru biçimde "I don't know" diyor mu? False confidence oranını ölç.
- **Retrieval recall'u.** Reader'ı değerlendirmeden önce, retriever'ın doğru pasajı top-`k`'ya getirip getirmediğini ölç. Bir reader eksik pasajı düzeltemez.

### RAGAS: 2026 üretim eval framework'ü

`RAGAS`, RAG sistemleri için özel olarak kurulmuştur ve 2026'da gönderim varsayılanıdır. Gold referans gerektirmeden dört boyutu puanlar:

- **Faithfulness.** Cevaptaki her iddia getirilen bağlamdan mı geliyor? NLI tabanlı entailment ile ölçülür. Birincil halüsinasyon metriğindir.
- **Cevap relevance'ı.** Cevap soruyu adresliyor mu? Cevaptan hipotetik sorular üretilerek ve gerçek soruyla karşılaştırılarak ölçülür.
- **Context precision.** Getirilen chunk'ların yüzde kaçı gerçekten ilgiliydi? Düşük precision = prompt'ta gürültü.
- **Context recall.** Getirilen set gereken tüm bilgiyi içeriyor mu? Düşük recall = reader başarılı olamaz.

Referanssız puanlama, kurate edilmiş gold cevaplar olmadan canlı üretim trafiği üzerinde değerlendirme yapmana izin verir. Exact-match metriklerinin işe yaramaz olduğu açık uçlu sorular için üstüne LLM-as-judge katmanla.

`pip install ragas`. Retriever + reader'ını tak. Sorgu başına dört skaler al. Regresyonlarda uyarı ver.

## Kullan

2026 stack'i.

| Kullanım durumu | Önerilen |
|---------|-------------|
| Pasaj verildi, cevap span'ını bul | `deepset/roberta-base-squad2` |
| Sabit bir corpus üzerinde, closed-book kabul edilemez | RAG: dense retriever + LLM reader |
| Bir belge deposu üzerinde gerçek zamanlı | Hibrit (BM25 + dense) retriever + reranker (ders 14) ile RAG |
| Konuşmalı QA (takip soruları) | Konuşma geçmişiyle LLM + her tur RAG |
| Yüksek factual, regule edilmiş alanlar | Otoriter bir corpus üzerinde extractive; asla yalnız generative |

Extractive QA 2026'da modası geçmiş çünkü LLM'lerle RAG daha fazla durumu ele alıyor. Hâlâ literal alıntının gerekli olduğu bağlamlarda gönderiliyor: hukuki araştırma, regülatif compliance, audit araçları.

## Yayınla

`outputs/skill-qa-architect.md` olarak kaydet:

```markdown
---
name: qa-architect
description: Choose QA architecture, retrieval strategy, and evaluation plan.
version: 1.0.0
phase: 5
lesson: 13
tags: [nlp, qa, rag]
---

Given requirements (corpus size, question type, factuality constraint, latency budget), output:

1. Architecture. Extractive, RAG with extractive reader, RAG with generative reader, or closed-book LLM. One-sentence reason.
2. Retriever. None, BM25, dense (name the encoder), or hybrid.
3. Reader. SQuAD-tuned model, LLM by name, or "domain-fine-tuned DistilBERT."
4. Evaluation. EM + F1 for extractive benchmarks; answer accuracy + citation accuracy + refusal calibration for production. Name what you are measuring and how you are measuring it.

Refuse closed-book LLM answers for regulatory or compliance-sensitive questions. Refuse any QA system without a retrieval-recall baseline (you cannot evaluate the reader without knowing the retriever surfaced the right passage). Flag questions that require multi-hop reasoning as needing specialized multi-hop retrievers like HotpotQA-trained systems.
```

## Alıştırmalar

1. **Kolay.** Yukarıdaki SQuAD extractive pipeline'ı 10 Wikipedia pasajında kur. 10 soruyu elle hazırla. Cevabın ne sıklıkla doğru olduğunu ölç. Pasajlar ve sorular temizse 7-9 doğru görmelisin.
2. **Orta.** Bir refusal sınıflandırıcısı ekle. En üst retrieval skoru bir eşiğin (örneğin 0.3 cosine) altındayken, reader'ı çağırmak yerine "I don't know" döndür. Eşiği held-out sette ayarla.
3. **Zor.** Kendi seçtiğin 10,000 belgelik bir corpus üzerinde bir RAG pipeline'ı kur. RRF fusion ile hibrit retrieval (BM25 + dense) uygula (bkz. ders 14). Hibrit adımıyla ve onsuz cevap doğruluğunu ölç. Hangi soru türlerinin en çok fayda gördüğünü belgele.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Extractive QA | Cevap span'ını bul | Verilen bir pasajda cevabın başlangıç ve bitiş indekslerini tahmin et. |
| Open-domain QA | Corpus üzerinde QA | Verilen pasaj yok; önce bul sonra cevapla. |
| RAG | Getir sonra üret | Retrieval-augmented generation. Retriever + reader pipeline'ı. |
| SQuAD | Kanonik benchmark | Stanford Question Answering Dataset. EM + F1 metrikleri. |
| Hallucination | Uydurulmuş cevap | Getirilen bağlam tarafından desteklenmeyen reader çıktısı. |
| Refusal kalibrasyonu | Ne zaman susmasını bil | Cevap veremediğinde sistem doğru biçimde "I don't know" der. |

## İleri Okuma

- [Rajpurkar et al. (2016). SQuAD: 100,000+ Questions for Machine Comprehension of Text](https://arxiv.org/abs/1606.05250) — benchmark makalesi.
- [Karpukhin et al. (2020). Dense Passage Retrieval for Open-Domain QA](https://arxiv.org/abs/2004.04906) — DPR, QA için kanonik dense retriever.
- [Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) — RAG'i adlandıran makale.
- [Gao et al. (2023). Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) — kapsamlı RAG survey'i.
