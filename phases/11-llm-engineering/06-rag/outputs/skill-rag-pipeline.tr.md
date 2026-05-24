---
name: skill-rag-pipeline
description: İlk prensiplerden RAG pipeline'ları kur ve hata ayıkla
version: 1.0.0
phase: 11
lesson: 6
tags: [rag, retrieval, embeddings, vector-search, llm-engineering]
---

# RAG Pipeline Pattern'i

Her RAG sistemi bu pattern'i izler:

```
documents -> chunk -> embed -> store
query -> embed -> search(top_k) -> build_prompt -> generate
```

İndeksleme doküman başına bir kez olur. Sorgulama her kullanıcı isteğinde olur.

## RAG'i ne zaman kullan

- LLM özel veya güncel dokümanlara erişmeli
- Fine-tuning, güncellemek için çok pahalı veya çok yavaş
- Cevaplar için kaynak göstermen gerekiyor
- Bilgi tabanı sık değişiyor

## RAG'i ne zaman KULLANMA

- Cevap LLM'in zaten bildiği genel bilgi
- Görev yaratıcı (yazma, beyin fırtınası), factual değil
- Modelin belirli bir muhakeme stilini benimsemesini istiyorsun (fine-tuning kullan)

## Implementation checklist

1. Dokümanları 256-512 token segment'lere 50 token overlap ile chunk'la
2. Her chunk'ı tutarlı bir embedding modeliyle embed et
3. Embedding'leri orijinal metinle bir vektör veritabanında sakla
4. Sorgu sırasında, kullanıcının sorusunu aynı modelle embed et
5. Cosine similarity ile en benzer top-k (5-10) chunk'ı retrieve et
6. Bir prompt kur: sistem talimatı + retrieved context + user sorusu
7. Cevabı retrieved context'te grounding yaparak üret
8. Cevabı kaynak referanslarıyla döndür

## Sık yapılan hatalar

- İndeksleme ve sorgulama için farklı embedding modelleri kullanmak (vektörler uyumsuz)
- Chunk'lar çok küçük (bağlam kaybı) veya çok büyük (alaka sulanması)
- Chunk'lar arasında overlap dahil etmemek (cümleleri sınırlarda böler)
- Dokümanlar değiştiğinde yeniden indekslemeyi unutmak
- Retrieved chunk'ları tutarlı bir cevap üretmeden kullanıcıya döndürmek
- Factual RAG sorguları için temperature=0 ayarlamamak (daha yüksek temperature = daha fazla halüsinasyon)

## Retrieval hata ayıklama

Doğru chunk'lar retrieve edilmiyorsa:
1. Sorgu embedding'ini yazdır ve sıfır olmadığını doğrula
2. Bilinen-ilgili bir chunk için cosine similarity'leri manuel kontrol et
3. Doküman kelime dağarcığına uyacak şekilde sorguyu yeniden ifade et
4. Embedding modelinin indeks ve sorgu zamanı arasında eşleştiğini doğrula
5. İlgili içeriğin chunking sırasında kaybolup kaybolmadığını kontrol et

## Production parametreleri

- Chunk boyutu: 256-512 token
- Overlap: 50 token (chunk boyutunun %10-20'si)
- Top-k: çoğu kullanım senaryosu için 5-10
- Temperature: factual cevaplar için 0
- Embedding modeli: text-embedding-3-small (maliyet etkin) veya text-embedding-3-large (daha yüksek doğruluk)
