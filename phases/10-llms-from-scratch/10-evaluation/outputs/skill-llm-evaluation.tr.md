---
name: skill-llm-evaluation
description: Görev türü, bütçe ve gereksinimlere dayalı olarak doğru LLM değerlendirme stratejisini seçmek için karar çerçevesi
version: 1.0.0
phase: 10
lesson: 10
tags: [evaluation, evals, benchmarks, llm-as-judge, elo, metrics]
---

# LLM Değerlendirme Stratejisi

Bir LLM sistemini değerlendirirken, doğru yaklaşımı seçmek için bu karar çerçevesini uygula.

## Her değerlendirme türü ne zaman kullanılır

**Benchmark'lar (MMLU, HumanEval, SWE-bench):** İlk model seçimi yapıyorsun. 10 aday modeli 3'e indirgemen gerekiyor. Benchmark'lar sıfır maliyetle kabaca sıralama verir. Son değerlendirme olarak benchmark kullanma.

**Özel değerlendirmeler:** Üretim için inşa ediyorsun. Spesifik başarısızlık modlarına sahip spesifik bir görevin var. Özel değerlendirmeler gerçek dünya performansını tahmin eden tek değerlendirmedir. Prototip için minimum 50 test case, üretim için 200+.

**LLM-as-judge:** Görevin açık uçlu (özetleme, yazım, sohbet). Exact match ve token overlap metrikleri çok katı. LLM-as-judge yargı başına ~$0.01 maliyet ve insanlarla ~%80 uzlaşır. Her zaman rubric kullan, belirsiz prompt değil.

**İnsan değerlendirmeleri:** Kazıklar yüksek ve otomatik metrikler uyuşmuyor. İnsan değerlendirmesi ground truth'tur ama yargı başına $0.10-$2.00 maliyetlidir. Belirsiz case'ler ve otomatik metriklerin periyodik kalibrasyonu için sakla.

**Pairwise karşılaştırmalardan ELO:** Aynı görevde birden çok modeli karşılaştırıyorsun. Pairwise mutlak puanlamadan daha güvenilirdir çünkü insanlar (ve LLM yargıçları) göreli yargılarda daha iyidir.

## Scoring fonksiyon seçimi

- **Exact match**: classification, entity extraction, bilinen cevaplı yapılandırılmış çıktılar
- **Token F1**: kısmi kredinin önemli olduğu extraction görevleri
- **ROUGE-L**: özetleme, çeviri
- **BLEU**: makine çevirisi
- **LLM-as-judge**: açık uçlu üretim, sohbet kalitesi, yardımseverlik
- **Execution-based**: kod üretimi (kodu çalıştır, testlerin geçip geçmediğini kontrol et)
- **Schema uyumu**: yapılandırılmış çıktılar (JSON şemayla eşleşiyor mu?)

## Değerlendirme tasarımında kırmızı bayraklar

- 50 case'ten küçük değerlendirme seti: sonuçlar istatistiksel olarak anlamsız
- Uç durum yok: happy-path performansı ölçüyorsun, her zaman gerçek dünyadan yüksektir
- Tek metrik: farklı metrikler farklı hikayeler anlatır, en az iki kullan
- Versiyonlama yok: versiyonlanmış değerlendirme setleri olmadan iyileşmeyi takip edemezsin
- Değerlendirme seti contamination: değerlendirme örneklerini asla fine-tuning verisi veya few-shot prompt'lara dahil etme
- Sadece bir modeli test etme: karşılaştırma için baseline (basit bir heuristic bile) lazım

## Değerlendirme pipeline kontrol listesi

1. Görevi kesin tanımla ("soruları cevapla" değil, "destek biletlerini 5 kategoriye sınıflandır")
2. Happy path, uç durumlar ve bilinen regresyonlar arasında test case'ler oluştur
3. Görev türü için uygun 2-3 scoring fonksiyonu seç
4. Üretim gereksinimlerine göre pass/fail eşikleri ayarla
5. Yürütmeyi otomatikleştir: tek komut tüm suite'i çalıştırır
6. Her şeyi versiyonla: test case'ler, scoring fonksiyonları, prompt'lar, model versiyonları
7. Her değişiklikte çalıştır: prompt güncellemeleri, model değişiklikleri, kod deployment'ları
8. Trendleri takip et: tek skor gürültü, trendline sinyaldir
9. Üç ayda bir insan yargısına karşı kalibre et
10. Üretim başarısızlığı keşfedildiğinde regresyon case'leri ekle
