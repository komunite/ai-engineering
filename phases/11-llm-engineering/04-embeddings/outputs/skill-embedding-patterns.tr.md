---
name: skill-embedding-patterns
description: Embedding, vektör arama ve benzerlik için production pattern'leri
version: 1.0.0
phase: 11
lesson: 4
tags: [embeddings, vectors, similarity, search, chunking, quantization]
---

# Embedding Pattern'leri

Her embedding workflow'u bu sözleşmeyi izler:

```
text -> embed(text) -> vector (float array)
similarity(vector_a, vector_b) -> score (float)
```

Önemli olan tek iki karar embedding modeli ve benzerlik metriğidir. Geri kalan her şey tesisat işidir.

## Embedding'leri ne zaman kullan

- Dokümanlar arası semantik arama (anahtar kelime değil, anlam bul)
- Benzer öğeleri kümeleme (destek talepleri, ürün incelemeleri, bug raporları)
- En yakın komşulara göre sınıflandırma (etiketli örneklere benzerlikle yeni öğeleri etiketle)
- Öneri sistemleri (kullanıcının beğendiğine benzer öğeleri bul)
- Tekilleştirme (benzerlik eşiği kullanarak yakın-duplikat içerik bul)

## Embedding'leri ne zaman KULLANMA

- Tam anahtar kelime eşleşmesi (full-text search kullan)
- Yapılandırılmış sorgular (SQL, filtreler kullan)
- Manuel etiketlemenin daha hızlı olduğu küçük veri setleri (<100 öğe)
- Açıklanabilirliğin doğruluktan daha önemli olduğu görevler (embedding'ler opaktır)

## Model seçimi

Kısıtlarına göre seç:

- **API gerekli, en iyi değer**: OpenAI text-embedding-3-small (1536d, $0.02/1M token)
- **Maksimum doğruluk**: Voyage-3 (1024d, $0.06/1M token, en yüksek MTEB)
- **Yerel/özel gerekli**: BGE-M3 (1024d, ücretsiz, çok dilli, GPU önerilir)
- **Hızlı yerel prototipleme**: all-MiniLM-L6-v2 (384d, ücretsiz, CPU'da çalışır)
- **Çok dilli gerekli**: Cohere embed-v3 (1024d) veya BGE-M3 (her ikisi de güçlü çok dilli)

Kural: indeksleme ve sorgulama arasında asla embedding modellerini karıştırma. Farklı modellerden gelen vektörler uyumsuz uzaylarda yaşar.

## Chunking kuralları

1. Chunk başına 50 token overlap ile 256-512 token hedefle
2. Mümkünse cümle ortasında bölme
3. Her chunk ile metadata (kaynak dosya, bölüm başlığı, konum) dahil et
4. Yapılandırılmış dokümanlar (Markdown, HTML) için önce başlık sınırlarında böl
5. Chunk kalitesini bilinen cevapları arayıp retrieval'ı kontrol ederek test et

## Benzerlik metriği seçimi

- **Cosine similarity**: varsayılan seçim, değişken uzunluklu metni işler, normalize
- **Dot product**: vektörler zaten unit-normalize ise kullan (OpenAI modelleri öyle), biraz daha hızlı
- **Euclidean distance**: kümeleme için, mutlak konum önemli olduğunda kullan

Üçü de vektörler normalize edildiğinde aynı sıralamayı verir. Seçim sadece normalize edilmemiş vektörler için önemlidir.

## Depolama optimizasyonu

Üç sıkıştırma seviyesi, birleştirilebilir:

1. **Matryoshka truncation**: boyutları azalt (1536 -> 256 = 6x tasarruf, %3-5 doğruluk kaybı)
2. **Float16 quantization**: boyut başına depolamayı yarıya indir (2x tasarruf, <%1 doğruluk kaybı)
3. **Binary quantization**: boyut başına 1 bit (32x tasarruf, %5-10 doğruluk kaybı, rescoring ile kullan)

Production pattern'i: tüm corpus üzerinde binary arama, top-1000'i float32 vektörlerle yeniden skorla.

## Retrieve-then-rerank

En iyi doğruluk için iki aşamalı pipeline:

1. Bi-encoder top-100 adayı çıkarır (hızlı, önceden hesaplanmış embedding'leri kullanır)
2. Cross-encoder top-10'a yeniden sıralar (yavaş, her sorgu-doküman çiftini işler)

Bu, tek aşamalı retrieval'ı precision metriklerinde %10-15 yener. Doğruluğun gecikmeden daha önemli olduğu durumlarda kullan.

## Sık yapılan hatalar

- İndeksleme ve sorgulama için farklı embedding modelleri kullanmak
- Chunk'lar yerine tüm dokümanları embed etmek (embedding her şeyin ortalaması haline gelir)
- Cosine similarity'den önce vektörleri normalize etmemek (çoğu model pre-normalize eder, ama doğrula)
- Chunk overlap'i göz ardı etmek (sınırlarda bölünen cümleler bağlamı kaybeder)
- Orijinal metin olmadan sadece vektör saklamak (retrieval için her ikisi de gerekli)
- Model değiştiğinde yeniden embed etmemek (eski vektörler uyumsuz)
- Boyutları sadece doğruluğa göre seçmek (depolama ve gecikme boyutlarla doğrusal ölçeklenir)

## Embedding hata ayıklama

Arama sonuçları kötüyse:

1. Sorgu embedding'inin sıfır olmadığını doğrula (boş veya whitespace girdi sıfır vektör üretir)
2. Bilinen-ilgili bir dokümanın benzerlik skorunu manuel kontrol et
3. Doküman kelime dağarcığına uyacak şekilde sorguyu yeniden ifade et
4. İlgili içeriğin chunk'lar arasında bölünmediğinden emin olmak için chunk sınırlarını incele
5. Normalizasyon sorunlarını tespit etmek için top-k sonuçları metrikler arasında (cosine, dot, euclidean) karşılaştır
6. Pipeline'ın çalıştığını teyit etmek için trivially eşleşen bir sorguyla test et (dokümandan bir cümle kopyala)

## Production parametreleri

- Chunk boyutu: 256-512 token
- Chunk overlap: 50 token (chunk boyutunun %10-20'si)
- Top-k retrieval: doğrudan kullanım için 5-10, reranking için 50-100
- Benzerlik eşiği: cosine için 0.7+ (bunun altında sonuçlar genelde alakasız)
- Batch embedding: throughput için API çağrısı başına 100-500 metin işle
- İndeks yeniden inşası: model değiştiğinde veya dokümanlar önemli ölçüde güncellendiğinde yeniden embed et
