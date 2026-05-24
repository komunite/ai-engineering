# RAG için Chunking Stratejileri

> Chunking konfigürasyonu retrieval kalitesini embedding modeli seçimi kadar etkiler (Vectara NAACL 2025). Chunking'i yanlış yap, hiçbir miktarda reranking seni kurtarmaz.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 14 (Bilgi Erişimi), Faz 5 · 22 (Embedding Modelleri)
**Süre:** ~60 dakika

## Sorun

Bir RAG sistemine 50 sayfalık bir sözleşme koyuyorsun. Kullanıcı soruyor: "What is the termination clause?" Retriever kapak sayfasını döndürüyor. Neden? Çünkü model 512-token chunk'lar üzerinde eğitildi ve termination clause 20 sayfa içeride, sayfa kırılımı boyunca bölünmüş, sorguyla bağlayan yerel anahtar kelime yok.

Düzeltme "daha iyi bir embedding modeli al" değil. Düzeltme chunking'tir. Ne kadar büyük? Overlap? Nereye böl? Çevre bağlam ile?

Şubat 2026 benchmark'ları şaşırtıcı sonuçlar gösteriyor:

- Vectara'nın 2026 çalışması: recursive 512-token chunking semantik chunking'i %69 → %54 doğrulukla yendi.
- Natural Questions üzerinde SPLADE + Mistral-8B: overlap ölçülebilir hiçbir fayda sağlamadı.
- Bağlam uçurumu: yanıt kalitesi ~2,500 token bağlam civarında keskin biçimde düşer.

"Açık" cevap (semantik chunking, %20 overlap, 1000 token) sıklıkla yanlıştır. Bu ders altı strateji için sezgi kurar ve sana hangisine ne zaman uzanacağını söyler.

## Kavram

![Tek pasajda görselleştirilmiş altı chunking stratejisi](../assets/chunking.svg)

**Fixed chunking.** Her N karakter ya da token'da böl. En basit baseline. Cümle ortasında böler. İyi sıkıştırma, kötü tutarlılık.

**Recursive.** LangChain'in `RecursiveCharacterTextSplitter`'ı. Önce `\n\n`'de bölmeyi dene, sonra `\n`, sonra `.`, sonra boşluk. Temiz geri düşer. 2026 varsayılanı.

**Semantik.** Her cümleyi embed et. Komşu cümleler arasındaki cosine similarity'yi hesapla. Similarity bir eşiğin altına düştüğü yerde böl. Konu tutarlılığını korur. Yavaş; bazen retrieval'a zarar veren minik 40-token parçalar üretir.

**Cümle.** Cümle sınırlarında böl. Chunk başına bir cümle ya da N cümlelik bir pencere. Maliyetin bir kısmında ~5k token'a kadar semantik chunking'le eşleşir.

**Parent-document.** Retrieval *için* küçük child chunk'lar ve bağlam için daha büyük parent chunk sakla. Child'a göre getir; parent'ı döndür. Zarif şekilde bozulur: kötü child chunk'lar hâlâ makul parent'lar döndürür.

**Late chunking (2024).** Önce tüm belgeyi token seviyesinde embed et, sonra token embedding'lerini chunk embedding'lerine havuzla. Chunk'lar arası bağlamı korur. Uzun bağlamlı embedder'larla (BGE-M3, Jina v3) çalışır. Daha yüksek compute.

**Contextual retrieval (Anthropic, 2024).** Her chunk'ın önüne belgedeki pozisyonunun LLM-üretimi bir özetini ekle ("This chunk is section 3.2 of the termination clauses..."). Anthropic'in kendi benchmark'ında %35-50 retrieval iyileştirmesi. İndekslemesi pahalı.

### Her varsayılanı yenen kural

Chunk boyutunu sorgu türüne eşle:

| Sorgu türü | Chunk boyutu |
|------------|-----------|
| Factoid ("what is the CEO's name?") | 256-512 token |
| Analitik / multi-hop | 512-1024 token |
| Tüm-bölüm anlama | 1024-2048 token |

NVIDIA'nın 2026 benchmark'ı. Chunk, cevabı artı yerel bağlamı içermek için yeterince büyük, retriever'ın top-K'sının bağlam gürültüsünden ziyade cevap üzerine odaklanması için yeterince küçük olmalı.

## İnşa Et

### Adım 1: fixed ve recursive chunking

```python
def chunk_fixed(text, size=512, overlap=0):
    step = size - overlap
    return [text[i:i + size] for i in range(0, len(text), step)]


def chunk_recursive(text, size=512, seps=("\n\n", "\n", ". ", " ")):
    if len(text) <= size:
        return [text]
    for sep in seps:
        if sep not in text:
            continue
        parts = text.split(sep)
        chunks = []
        buf = ""
        for p in parts:
            if len(p) > size:
                if buf:
                    chunks.append(buf)
                    buf = ""
                chunks.extend(chunk_recursive(p, size=size, seps=seps[1:] or (" ",)))
                continue
            candidate = buf + sep + p if buf else p
            if len(candidate) <= size:
                buf = candidate
            else:
                if buf:
                    chunks.append(buf)
                buf = p
        if buf:
            chunks.append(buf)
        return [c for c in chunks if c.strip()]
    return chunk_fixed(text, size)
```

### Adım 2: semantik chunking

```python
def chunk_semantic(text, encoder, threshold=0.6, min_chars=200, max_chars=2048):
    sentences = split_sentences(text)
    if not sentences:
        return []
    embs = encoder.encode(sentences, normalize_embeddings=True)
    chunks = [[sentences[0]]]
    for i in range(1, len(sentences)):
        sim = float(embs[i] @ embs[i - 1])
        current_len = sum(len(s) for s in chunks[-1])
        if sim < threshold and current_len >= min_chars:
            chunks.append([sentences[i]])
        else:
            chunks[-1].append(sentences[i])

    result = []
    for group in chunks:
        text_group = " ".join(group)
        if len(text_group) > max_chars:
            result.extend(chunk_recursive(text_group, size=max_chars))
        else:
            result.append(text_group)
    return result
```

`threshold`'u alanın için ayarla. Çok yüksek → parçalar. Çok düşük → tek dev chunk.

### Adım 3: parent-document

```python
def chunk_parent_child(text, parent_size=2048, child_size=256):
    parents = chunk_recursive(text, size=parent_size)
    mapping = []
    for p_idx, parent in enumerate(parents):
        children = chunk_recursive(parent, size=child_size)
        for child in children:
            mapping.append({"child": child, "parent_idx": p_idx, "parent": parent})
    return mapping


def retrieve_parent(child_query, mapping, encoder, top_k=3):
    child_embs = encoder.encode([m["child"] for m in mapping], normalize_embeddings=True)
    q_emb = encoder.encode([child_query], normalize_embeddings=True)[0]
    scores = child_embs @ q_emb
    top = np.argsort(-scores)[:top_k]
    seen, parents = set(), []
    for i in top:
        if mapping[i]["parent_idx"] not in seen:
            parents.append(mapping[i]["parent"])
            seen.add(mapping[i]["parent_idx"])
    return parents
```

Anahtar içgörü: parent'ları dedupe et. Birden çok child aynı parent'a eşlenebilir; hepsini döndürmek bağlamı boşa harcar.

### Adım 4: contextual retrieval (Anthropic deseni)

```python
def contextualize_chunks(document, chunks, llm):
    context_prompts = [
        f"""<document>{document}</document>
Here is the chunk to situate: <chunk>{c}</chunk>
Write 50-100 words placing this chunk in the document's context."""
        for c in chunks
    ]
    contexts = llm.batch(context_prompts)
    return [f"{ctx}\n\n{c}" for ctx, c in zip(contexts, chunks)]
```

Contextual chunk'ları indeksle. Sorgu zamanında retrieval, ekstra çevre sinyalinden fayda görür.

### Adım 5: değerlendir

```python
def recall_at_k(queries, corpus_chunks, encoder, k=5):
    chunk_embs = encoder.encode(corpus_chunks, normalize_embeddings=True)
    hits = 0
    for q_text, gold_idxs in queries:
        q_emb = encoder.encode([q_text], normalize_embeddings=True)[0]
        top = np.argsort(-(chunk_embs @ q_emb))[:k]
        if any(i in gold_idxs for i in top):
            hits += 1
    return hits / len(queries)
```

Her zaman benchmark et. Senin corpus'un için "en iyi" strateji hiçbir blog yazısıyla eşleşmeyebilir.

## Tuzaklar

- **Yalnızca factoid sorgularda değerlendirilen chunking.** Multi-hop sorgular çok farklı kazananları ortaya çıkarır. Sorgu-tipi katmanlı eval seti kullan.
- **Minimum boyut olmadan semantik chunking.** Retrieval'a zarar veren 40-token parçalar üretir. Her zaman `min_tokens` uygula.
- **Cargo cult olarak overlap.** 2026 çalışmaları overlap'in sıklıkla sıfır fayda sağladığını ve indeks maliyetini ikiye katladığını buluyor. Ölç, varsayma.
- **Min/max uygulaması yok.** 5 token'lık ya da 5000 token'lık chunk'lar ikisi de retrieval'ı bozar. Clamp et.
- **Cross-doc chunking.** Bir chunk'un iki belgeyi kapsamasına asla izin verme. Her zaman belge başına chunk yap, sonra birleştir.

## Kullan

2026 stack'i:

| Durum | Strateji |
|-----------|----------|
| İlk inşa, bilinmeyen corpus | Recursive, 512 token, overlap yok |
| Factoid QA | Recursive, 256-512 token |
| Analitik / multi-hop | Recursive, 512-1024 token + parent-document |
| Yoğun çapraz referans (sözleşmeler, makaleler) | Late chunking ya da contextual retrieval |
| Konuşmalı / diyalog corpus | Tur seviyesi chunk'lar + speaker metadata |
| Kısa söyleyişler (tweet'ler, değerlendirmeler) | Bir belge = bir chunk |

Recursive 512 ile başla. 50 sorgu eval setinde recall@5 ölç. Oradan ayarla.

## Yayınla

`outputs/skill-chunker.md` olarak kaydet:

```markdown
---
name: chunker
description: Pick a chunking strategy, size, and overlap for a given corpus and query distribution.
version: 1.0.0
phase: 5
lesson: 23
tags: [nlp, rag, chunking]
---

Given a corpus (document types, avg length, domain) and query distribution (factoid / analytical / multi-hop), output:

1. Strategy. Recursive / sentence / semantic / parent-document / late / contextual. Reason.
2. Chunk size. Token count. Reason tied to query type.
3. Overlap. Default 0; justify if >0.
4. Min/max enforcement. `min_tokens`, `max_tokens` guards.
5. Evaluation plan. Recall@5 on 50-query stratified eval set (factoid, analytical, multi-hop).

Refuse any chunking strategy without min/max chunk size enforcement. Refuse overlap above 20% without an ablation showing it helps. Flag semantic chunking recommendations without a min-token floor.
```

## Alıştırmalar

1. **Kolay.** Bir 20 sayfalık belgeyi fixed(512, 0), recursive(512, 0) ve recursive(512, 100) ile chunk'la. Chunk sayılarını ve sınır kalitesini karşılaştır.
2. **Orta.** 5 belge üzerinde 30 sorgu eval seti kur. Recursive, semantik ve parent-document için recall@5 ölç. Hangisi kazanır? Blog yazılarıyla eşleşiyor mu?
3. **Zor.** Contextual retrieval uygula. Baseline recursive'e karşı MRR iyileştirmesini ölç. Doğruluk kazancına karşı indeks maliyetini (LLM çağrıları) raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Chunk | Belgenin bir parçası | Embed edilen, indekslenen ve getirilen alt-belge birimi. |
| Overlap | Güvenlik marjı | Komşu chunk'lar arasında paylaşılan N token; 2026 benchmark'larında sıklıkla işe yaramaz. |
| Semantik chunking | Akıllı chunking | Komşu-cümle embedding similarity'sinin düştüğü yerde böl. |
| Parent-document | İki seviyeli retrieval | Küçük child'ları getir, daha büyük parent'ları döndür. |
| Late chunking | Embedding sonrası chunk | Tam belgeyi token seviyesinde embed et, chunk vektörlerine havuzla. |
| Contextual retrieval | Anthropic'in numarası | İndekslemeden önce her chunk'ın önüne eklenen LLM-üretimi özet. |
| Bağlam uçurumu | 2500-token duvarı | RAG'de ~2.5k bağlam token'ı civarında gözlemlenen kalite düşüşü (Ocak 2026). |

## İleri Okuma

- [Yepes et al. / LangChain — Recursive Character Splitting docs](https://python.langchain.com/docs/how_to/recursive_text_splitter/) — üretimdeki varsayılan.
- [Vectara (2024, NAACL 2025). Chunking configurations analysis](https://arxiv.org/abs/2410.13070) — chunking embedding seçimi kadar önemli.
- [Jina AI — Late Chunking in Long-Context Embedding Models (2024)](https://jina.ai/news/late-chunking-in-long-context-embedding-models/) — late chunking makalesi.
- [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) — LLM-üretimi bağlam prefix'leriyle %35-50 retrieval iyileştirmesi.
- [NVIDIA 2026 chunk-size benchmark — Premai summary](https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/) — sorgu türüne göre chunk boyutu.
