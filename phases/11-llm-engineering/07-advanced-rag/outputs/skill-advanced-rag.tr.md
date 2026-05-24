---
name: skill-advanced-rag
description: Hibrit arama, reranking ve değerlendirme ile production-grade RAG kur
version: 1.0.0
phase: 11
lesson: 7
tags: [rag, hybrid-search, bm25, reranking, hyde, evaluation]
---

# Advanced RAG Pattern'i

Temel RAG: sorguyu embed et -> vektör arama -> top-k -> üret.
Advanced RAG: sorguyu embed et + BM25 -> sıraları birleştir -> rerank -> top-k -> üret.

```
query -> [vector search (top-50)] -+-> RRF fusion -> reranker (top-5) -> prompt -> LLM
                                   |
query -> [BM25 search (top-50)]  --+
```

## Temel RAG'den ne zaman yükselt

- Retrieval kalitesi Recall@5'te %70'in altına düşüyor
- Kullanıcılar yanlış veya alakasız cevaplar bildiriyor
- Corpus 100K chunk'ı aşıyor
- Sorgular dokümanlardan farklı kelime dağarcığı kullanıyor
- Multi-hop sorular tutarlı şekilde başarısız oluyor

## Implementation checklist

1. Vektör indeksinin yanına BM25 indeksi ekle
2. Her ikisini paralel çalıştır (her biri top-50)
3. Reciprocal Rank Fusion (k=60) ile birleştir
4. Top adayları bir cross-encoder ile rerank et
5. Nihai prompt için top-5 al
6. Bir test setinde faithfulness değerlendirmesi ekle

## Teknik seçim kılavuzu

- **Hibrit arama**: production'da her zaman kullan. Sorgu zamanında ek maliyeti yok.
- **Reranking**: Recall@50 iyi ama Recall@5 kötü olduğunda kullan. 50-200ms gecikme ekler.
- **HyDE**: sorgular muğlak veya dokümanlardan farklı kelime dağarcığı kullandığında kullan. Bir LLM çağrısı ekler.
- **Parent-child chunk'lar**: küçük chunk'lar bağlamdan yoksun ama büyük chunk'lar alakayı sulandırdığında kullan.
- **Metadata filtreleme**: corpus net kategorilere sahip olduğunda kullan (tarih, kaynak tipi, departman).
- **Sorgu ayrıştırma**: birden çok dokümandan bilgi gerektiren multi-hop sorular için kullan.

## Sık yapılan hatalar

- BM25 ve vektör aramayı farklı chunk setleriyle çalıştırmak (aynı corpus'u aramaları gerekir)
- Reranking için çok küçük bir aday havuzu kullanmak (top-10 çok az; top-50 kullan)
- Her sorgu için HyDE eklemek (sadece kelime dağarcığı uyumsuzluğu darboğaz olduğunda yardımcı olur)
- Değişiklikleri değerlendirmemek (her teknikten önce ve sonra Recall@k ölç)
- Nerede başarısız olduğunu ölçmeden önce pipeline'ı aşırı tasarlamak

## Değerlendirme workflow'u

1. Bilinen cevap chunk'larıyla 50+ test sorusu oluştur
2. Her retrieval yöntemi için Recall@5 ve Recall@10 ölç
3. Retrieval'ın başarılı olduğu sorgularda üretilen cevapların faithfulness'ını ölç
4. Corpus büyüdükçe metrikleri haftalık izle
5. Daha çok teknik eklemeden önce bireysel başarısızlıkları araştır
