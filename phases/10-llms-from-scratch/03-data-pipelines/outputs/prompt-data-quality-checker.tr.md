---
name: prompt-data-quality-checker
description: LLM pretraining pipeline'larında veri kalitesini doğrula ve hata ayıkla
version: 1.0.0
phase: 10
lesson: 3
tags: [data-pipeline, deduplication, quality-filter, pre-training, llm, data-cleaning]
---

# LLM Pretraining için Veri Kalitesi Denetleyici

LLM pretraining için bir veri pipeline'ı kurarken ya da denetlerken, sorunları modele ulaşmadan yakalamak için bu çerçeveyi kullan.

## Pipeline Çıktısında Kırmızı Bayraklar

**Deduplication web verisinin %20'sinden azını kaldırdı.** Common Crawl tipik olarak %30-40 duplicate içerir. Dedup adımın %20'den azını kaldırıyorsa, MinHash parametrelerin fazla muhafazakâr veya eşiğin fazla yüksek. Kontrol et: shingle boyutu k, hash fonksiyonu sayısı, LSH band sayısı, Jaccard eşiği.

**Sıkıştırma oranı 2.0 char/token altında.** Bu, tokenizer'ının fazla agresif biçimde böldüğü anlamına gelir. Ya daha fazla merge ile yeniden eğit, vocabulary boyutunu artır veya pre-tokenization'ın metni gereksiz yere parçalamadığını kontrol et.

**Sıkıştırma oranı 6.0 char/token üstünde.** Tokenizer'ın çok domain'e özgü merge'ler öğrenmiş, genelleyemeyebilir. Domain'e özgü model için sorun değil ama genel amaçlı modeller için uyarı işareti.

**Dizi kullanımı %90 altında.** Çok fazla padding var. Ya dokümanların çok kısa (filtrele veya minimum doküman uzunluğunu artır) ya da sequence packing'in verimsiz (saf padding'den multi-document packing'e geç).

**Vocab kullanımı %50 altında.** Vocabulary'nin yarısından fazlası bu corpus'ta kullanılmıyor. Ya vocabulary domain'in için fazla büyük ya da tokenizer çok farklı veri üzerinde eğitilmiş.

## Quality Filter Kalibrasyonu

Her pipeline aşamasında 1000 dokümanlık rastgele örnekte bu kontrolleri çalıştır:

1. **Temizleme sonrası 20 rastgele doküman oku.** Kalıntı HTML, JavaScript, navigation metni veya boilerplate içeriyorlar mı? Evet ise, HTML stripping'in eksik.

2. **Quality filter'dan GEÇEN 20 rastgele doküman oku.** Bunlardan herhangi biri spam, keyword listesi veya makine üretimi mi? Evet ise, filter eşiklerini sıkılaştır.

3. **Quality filter'dan KALAN 20 rastgele doküman oku.** Bunlardan herhangi biri gerçekten iyi içerik mi? Evet ise, filter'ın fazla agresif. Eşikleri gevşet veya spesifik kalıplar için istisnalar ekle.

4. **Dedup'tan 20 rastgele yakın-duplicate çift oku.** Gerçekten benzerler mi? Değilse, Jaccard eşiğini düşür veya hash fonksiyonu sayısını artır.

## Veri Karıştırma Oranları

Evrensel bir formül yoktur. Şu baseline'larla başla ve değerlendirmeye göre ayarla:

| Kategori | Llama 3 Oranı | Başlangıç Noktası |
|----------|--------------|----------------|
| Web text | 50% | 50% |
| Code | 25% | 15-25% |
| Books/academic | 13% | 10-15% |
| Math | 8% | 5-10% |
| Multilingual web | 4% | 5-10% |

Modelin programlamada güçlü olması isteniyorsa code oranını artır. Reasoning önemliyse math oranını artır. Daha az gürültü gerekiyorsa web oranını düşür. Oranları değiştirdikten sonra her zaman benchmark üzerinde değerlendir.

## Ölçeklendirme Tahminleri

Belirli bir hedef token sayısı için:

- Web'den 1T token: ~3-5TB ham metin, temizlik ve dedup sonrası ~1.5-2TB bekle
- Tokenization hızı (Rust): çekirdek başına ~100M token/saniye
- Tokenization hızı (Python): çekirdek başına ~1-10M token/saniye
- 128 hash, 16 band ile MinHash dedup: çekirdek başına ~10K doküman/saniye
- Sequence packing: I/O bound, 10GB üstü corpus için memory-mapped file kullan

15T token için (Llama 3 ölçeği), ~30-50TB ham giriş verisi, 64 çekirdekli makinede 1-2 hafta ön işleme ve 100TB+ ara dosya diski planla.

## Eğitim Öncesi Kontrol Listesi

1. Toplam token sayısı compute bütçenle eşleşiyor (rehber olarak Chinchilla scaling veya Llama 3 overtrain oranı)
2. Dedup web verisinin %30-40'ını kaldırdı
3. Quality filter kalan verinin %10-20'sini kaldırdı
4. İngilizce için sıkıştırma oranı 3-5 char/token
5. Dizi kullanımı %95 üstünde
6. Rastgele spot kontroller her pipeline aşamasında temiz, tutarlı metin gösteriyor
7. Veri karışım oranları küçük ölçekli eğitim koşusunda doğrulandı
8. PII kaldırma örnek üzerinde doğrulandı
9. Tüm binary formatlar (packed sequence'lar, token ID array'leri) round-trip encoding/decoding testlerinden geçiyor
10. Pipeline tekrarlanabilir: sabit random seed'lerle aynı girdi aynı çıktıyı üretiyor
