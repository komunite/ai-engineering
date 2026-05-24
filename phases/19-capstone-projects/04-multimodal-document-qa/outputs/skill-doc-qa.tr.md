---
name: doc-qa
description: 10k sayfa üzerinde late-interaction retrieval ve evidence-region citation'larıyla vision-first multimodal döküman QA sistemi kur.
version: 1.0.0
phase: 19
lesson: 04
tags: [capstone, multimodal, rag, colpali, colqwen, late-interaction, pdf]
---

Bir PDF corpus'u (10-K'lar, bilimsel makaleler, taranmış dökümanlar) verildiğinde, sayfaları ColPali tarzı late interaction ile image olarak index'leyen ve sayfa düzeyinde evidence region'larıyla soru yanıtlayan bir pipeline kur.

Build planı:

1. Her PDF sayfasını PyMuPDF ile 180 DPI'da 1536x2048 PNG'ye render et.
2. Her sayfayı ColQwen2.5-v0.2 veya ColQwen3-omni ile embed et. Multi-vector patch embedding'lerini Vespa, Qdrant multi-vector veya AstraDB'de sakla.
3. DocPruner tarzı %50 patch pruning uygula. Doğruluk düşüşünün ViDoRe v3 üzerinde %0.5 altında kaldığını doğrula.
4. Query zamanında: query token'larını embed et; her sayfanın patch'lerine karşı MaxSim hesapla; top-k sırala.
5. Query artı top-5 sayfa görüntüsünü geçen Qwen3-VL-30B veya Gemini 2.5 Pro ile sentezle. Atıflı `(doc_id, page, region)` anchor'ları zorunlu kıl.
6. Denklem veya tablo yoğun sayfalar için Nougat ya da dots.ocr'yi opsiyonel text kanalı olarak çalıştır ve görüntünün yanında besle.
7. Evidence region'ları kaynak sayfa üzerinde bounding box olarak overlay eden Next.js 15 viewer kur.
8. ViDoRe v3 ve M3DocVQA üzerinde değerlendir. Düz metin, tablo, grafik, el yazısı ve denklem üzerinde vision-first ile OCR-then-text'i karşılaştıran içerik sınıfı × yaklaşım matrisi üret.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | ViDoRe v3 / M3DocVQA doğruluğu | Eşleşen sayfalarda OCR-then-text baseline'ına karşı benchmark |
| 20 | Evidence-region grounding | Yanıt span'ini içeren atıflı region'ların oranı |
| 20 | Depolama ve latency mühendisliği | DocPruner sıkıştırma, index p95, yanıt p95 2s altı |
| 20 | Çok sayfalı muhakeme | Elle etiketlenmiş 100 soruluk multi-page sette doğruluk |
| 15 | Kaynak inceleme UX'i | Overlay sadakati, karşılaştırma araçları, sayfa sayfa explorer |

Sert ret durumları:

- OCR text'ini single-vector embed'e geri uydurarak "vision-first" diye pazarlanan OCR-first pipeline'lar.
- Patch düzeyinde bounding box'ları düşüren ve dolayısıyla evidence overlay render edemeyen herhangi bir sistem.
- DocPruner ayarlarını belgelemeden raporlanan depolama sayıları.

Reddetme kuralları:

- Dedicated redaction politikası olmadan taranmış legal sözleşmeleri index'lemeyi reddet. ColQwen embedding'leri içerik sızdırır.
- Kullanıcının açıklamadığı bir corpus'a karşı sorgu sunmayı reddet. Düzenlemeye tabi domain'lerde audit trail zorunludur.
- İki pipeline'ı aynı corpus üzerinde çalıştırmadan OCR-then-text ile karşılaştırmayı reddet.

Çıktı: ingestion pipeline'ı, Vespa (veya Qdrant multi-vector) config'i, 100 soruluk multi-page eval seti, viewer UI ve içerik sınıfı x yaklaşım matrisi ile 2026'da hangi içerik sınıflarının hâlâ OCR-then-text'i tercih ettiğine dair somut bir öneri içeren bir yazımı içeren bir repo.
