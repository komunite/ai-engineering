---
name: skill-context-engineering
description: Görev tipi, window boyutu ve gecikme bütçesine göre context assembly pipeline'ları tasarlamak için karar çerçevesi
version: 1.0.0
phase: 11
lesson: 05
tags: [context-engineering, context-window, rag, memory, tool-selection, lost-in-the-middle]
---

# Context Engineering

Bir LLM uygulaması kurarken, context assembly pipeline'ını tasarlamak için bu çerçeveyi uygula.

## Temel ilkeler

1. **Context kıttır.** 128K window kulağa büyük gelir ama hızla dolar. Her bileşeni açıkça bütçele.
2. **Dikkat dengesizdir.** Modeller başa ve sona daha çok dikkat eder. Kritik bilgiyi oraya koy. Orta ölü bölgedir.
3. **Dinamik statiği yener.** Farklı sorgular farklı context'e ihtiyaç duyar. Bir kerede değil sorgu başına birleştir.
4. **Az daha çoktur.** Küratörlü bir 10K context dökme bir 100K context'i yener. Toplam bilgiden çok signal-to-noise oranı önemlidir.
5. **Her şeyi ölç.** Ölçemediğini optimize edemezsin. Her istekte bileşen başına token say.

## Context bütçesi kılavuzu

| Bileşen | Tipik Aralık | Öncelik | Sıkıştırma Stratejisi |
|-----------|-------------|----------|---------------------|
| System prompt | 200-1.000 token | Sabit, yüksek | Sıkı yaz, tekrarı sil |
| Tool tanımları | 500-3.000 token | Dinamik, orta | Sorgu niyetine göre buda |
| Retrieved context | 1.000-5.000 token | Dinamik, yüksek | Rerank + eşik + tekille |
| Konuşma geçmişi | 500-5.000 token | Dinamik, orta | Eski turları özetle |
| Few-shot örnekleri | 500-2.000 token | Dinamik, yüksek | Görev benzerliğine göre seç |
| User sorgusu | 50-500 token | Sabit, en yüksek | N/A |
| Generation rezervi | 2.000-8.000 token | Sabit | Beklenen çıktı uzunluğuna göre ayarla |

## Her bellek tipini ne zaman kullan

**Kısa-vadeli (konuşma geçmişi):** Mevcut oturum. Özetleme ile yönetilir. 5-10 mübadeleden eski turları sıkıştır. Son 3-4 turu birebir tut.

**Uzun-vadeli (gerçekler veritabanı):** Oturumlar arasında devam eden tercihler ve proje gerçekleri. Oturum başında retrieve et. Örnekler: "kullanıcı Python tercih ediyor", "proje PostgreSQL kullanıyor", "ekip trunk-based development izliyor". CLAUDE.md, bir veritabanı veya yapılandırılmış bir memory sisteminde sakla.

**Episodik (geçmiş etkileşimler):** Mevcut görevle alakalı belirli geçmiş konuşmalar. Embedding olarak sakla, benzerliğe göre retrieve et. "Geçen hafta benzer bir auth sorununu debug ettik" episodik memory'dir.

## Tool seçim stratejisi

Her istekte tüm tool'ları dahil etme. Bu token israfıdır ve modeli karıştırır.

1. Sorgu niyetini sınıflandır (kod, e-posta, takvim, araştırma, veri)
2. Niyetleri tool kategorilerine eşle
3. Sadece eşleşen tool'ları dahil et
4. Niyet muğlaksa, ilk 2 kategorideki tool'ları dahil et
5. Her zaman fallback olarak bir "genel" tool (web arama gibi) ekle

Beklenen tasarruf: net niyetli sorgularda tool tanımı token'larının %60-80'i.

## Retrieval best practice'leri

- **Retrieval sonrası rerank et.** Vektör benzerliği kaba bir filtredir. Bir reranker (cross-encoder veya LLM-bazlı) precision'ı önemli ölçüde artırır.
- **Alaka eşiği ayarla.** 0.3 cosine benzerliğinin altındaki chunk'ları dahil etme. Gürültü eklerler.
- **Tekille.** İki chunk içeriklerinin %80+'ını paylaşıyorsa, sadece daha yüksek skorluyu tut.
- **Lost-in-the-middle sıralaması uygula.** En alakalı chunk'ları başa ve sona yerleştir.
- **Toplam retrieval token'larını sınırla.** 3-5 yüksek alakalı chunk, 15 vasat chunk'ı yener.

## Geçmiş yönetimi

- Son 3-4 turu birebir tut (model son context'e ihtiyaç duyar)
- Eski turları bir özete sıkıştır ("X tartıştık, Y'ye karar verdik ve Z'de tıkandık")
- Bilgi eklemeyen sistem üretilen turları düşür (kullanıcıya görünür içeriği olmayan tool çağrıları)
- Geçmiş mevcut bütçenin %30'unu aşınca sıkıştırmayı tetikle

## Kırmızı bayraklar

- System prompt 2.000 token'ı aşıyor: muhtemelen dinamik olması gereken bilgi içeriyor
- Her istekte tüm tool'lar dahil: intent-bazlı seçim uygula
- Retrieval'da alaka filtresi yok: window'a gürültü döküyorsun
- Geçmiş sınırsız büyüyor: özetleme uygulanmamış
- Generation rezervi yok: model yanıtlarını kesiyor
- Aynı bilgi 3 yerde (system prompt, retrieved doc, geçmiş): tekille
- Context kullanımı %60'ın üzerinde: modelin "düşünmesi" için çok az alan bırakıyorsun
