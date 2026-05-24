# Capstone 04 — Multimodal Doküman QA (Görsel-Öncelikli PDF, Tablolar, Chart'lar)

> 2026 doküman-QA frontier'ı OCR-sonra-text'ten uzaklaştı ve görsel-öncelikli late interaction'a doğru hareket etti. ColPali, ColQwen2.5 ve ColQwen3-omni her PDF sayfasını bir görüntü olarak işler, multi-vector late interaction ile embed eder ve sorgunun patch'lere doğrudan attend etmesine izin verir. Finansal 10-K'larda, bilimsel makalelerde ve el yazısı notlarda bu pattern OCR-öncelikliyi büyük farkla yener. 10k sayfa üzerinde pipeline'ı uçtan uca inşa et ve OCR-sonra-text'e karşı yan yana karşılaştırmayı yayınla.

**Tür:** Bitirme
**Diller:** Python (pipeline), TypeScript (viewer UI)
**Ön koşullar:** Faz 4 (computer vision), Faz 5 (NLP), Faz 7 (transformer'lar), Faz 11 (LLM engineering), Faz 12 (multimodal), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P4 · P5 · P7 · P11 · P12 · P17
**Süre:** 30 saat

## Sorun

Kurumlar OCR pipeline'larının mahvettiği PDF'lerin üzerinde oturuyor: rotate edilmiş tablolarla taranmış 10-K'lar, denklemlerle yoğun bilimsel makaleler, sadece görüntü olarak anlamı olan chart'lar, el yazısı annotation'lar. Bunları text-öncelikli olarak işlemek sinyalin yarısını kaybetmek demek. 2026 cevabı ham sayfa görüntüleri üzerinde late-interaction multi-vector retrieval. ColPali (Illuin Tech) onu tanıttı; ColQwen2.5-v0.2 ve ColQwen3-omni doğruluğu itti. ViDoRe v3'te, görsel-öncelikli retrieval OCR-sonra-text'i anlamlı farklarla geçer — ve gap chart'larda, tablolarda ve el yazısında genişler.

Trade-off depolama ve gecikme. Bir ColQwen embedding'i sayfa başına ~2048 patch vektörü, tek bir 1024-dim vektör değil. Ham depolama balon yapar. DocPruner (2026) ölçülebilir doğruluk kaybı olmadan %50 pruning getiriyor. 10k sayfa index'leyeceksin, ViDoRe v3 nDCG@5 ölçeceksin, cevapları 2s altında sunacaksın ve doğrudan bir OCR-sonra-text baseline'ına karşı karşılaştıracaksın.

## Kavram

Late interaction her sorgu token'ının her patch token'ına karşı skor vermesi ve sorgu token'ı başına maksimum skorun toplanması demek. Tek bir pool'lanmış vektöre ihtiyaç duymadan ince-grenli matching elde edersin. Bir multi-vector index (Vespa, Qdrant multi-vector veya AstraDB) per-patch embedding'leri saklar ve retrieval zamanında MaxSim çalıştırır.

Cevaplayıcı, sorguyu artı top-k retrieve edilen sayfaları görüntü olarak alan ve evidence region'larıyla (bounding box'lar veya sayfa referansları) bir cevap yazan bir vision-language modeli. Qwen3-VL-30B, Gemini 2.5 Pro ve InternVL3 2026 frontier seçimleri. Denklemler ve bilimsel notasyon için bir OCR fallback (Nougat, dots.ocr) opsiyonel bir text kanalı olarak eklenir.

Değerlendirme iki boyutlu bir matris. Bir eksen: içerik tipi (düz text paragrafları, yoğun tablolar, bar/line chart'lar, el yazısı notlar, denklemler). Diğer eksen: retrieval yaklaşımı (görsel-öncelikli late interaction vs OCR-sonra-text vs hybrid). Her hücre nDCG@5 ve cevap doğruluğu alır. Rapor teslimattır.

## Mimari

```
PDF'ler -> sayfa renderer (PyMuPDF, 180 DPI)
           |
           v
  ColQwen2.5-v0.2 embed (sayfa başına multi-vector, ~2048 patch)
           |
           +------> DocPruner %50 sıkıştırma
           |
           v
   multi-vector index (Vespa veya Qdrant multi-vector)
           |
sorgu ----+----> top-k sayfa retrieve (MaxSim)
           |
           v
  VLM cevaplayıcı: Qwen3-VL-30B | Gemini 2.5 Pro | InternVL3
    input'lar: sorgu + top-k sayfa görüntüleri + opsiyonel OCR text
           |
           v
  cited page number'lar + evidence region'larla cevap
           |
           v
  Streamlit / Next.js viewer: kaynak sayfada highlight'lı box'lar
```

## Stack

- Sayfa rendering: PyMuPDF (fitz) 180 DPI'de, portrait-normalized
- Late-interaction modeli: ColQwen2.5-v0.2 veya ColQwen3-omni (Hugging Face'de vidore ekibi)
- Index: multi-vector field'lı Vespa veya Qdrant multi-vector veya MaxSim'li AstraDB
- Pruning: DocPruner 2026 politikası (yüksek-varyans patch'leri tut, < %0.5 doğruluk kaybında %50 sıkıştırma)
- OCR fallback (denklemler / yoğun tablolar): dots.ocr veya Nougat
- VLM cevaplayıcı: self-hosted Qwen3-VL-30B veya hosted Gemini 2.5 Pro; fallback olarak InternVL3
- Değerlendirme: ViDoRe v3 benchmark, multi-page reasoning için M3DocVQA
- Viewer UI: evidence region'lar için canvas overlay'li Next.js 15

## İnşa Et

1. **Ingest.** 10-K'lar, bilimsel makaleler ve taranmış dokümanlar boyunca 10k PDF sayfası korpusunu walk et. Her sayfayı 1536x2048 PNG'ye render et. `{doc_id, page_num, image_path}` persist et.

2. **Embed.** Her sayfa görüntüsünde ColQwen2.5-v0.2 çalıştır. Çıktı shape ~2048 patch embedding'i, dim 128. DocPruner uygula, en yüksek-sinyal yarısını tut. Vespa multi-vector field'a veya Qdrant multi-vector'a yaz.

3. **Sorgu.** Gelen her sorgu için, query tower (token-seviyesinde embedding'ler) ile embed et. Index'e karşı MaxSim çalıştır: her sorgu token'ı için, sayfa patch embedding'leri üzerinde max dot-product al, topla. Top-k sayfa döndür.

4. **Sentezle.** Qwen3-VL-30B'yi sorgu ve top-5 sayfa görüntüleriyle çağır. Prompt: "Sadece sağlanan sayfaları kullanarak cevap ver. Her iddiayı (doc_id, page) ile citation ver ve region'ı (figure, table, paragraph) isimlendir."

5. **Evidence region'lar.** Cited region'ları çıkarmak için cevabı post-process et. VLM bounding box'lar emit ederse (Qwen3-VL eder), viewer'da overlay olarak render et.

6. **OCR fallback.** Denklem-yoğun olarak tanımlanan sayfalar için (image variance üzerinde heuristic), Nougat veya dots.ocr çalıştır ve OCR text'i görüntünün yanında ekstra kanal olarak geçir.

7. **Eval.** ViDoRe v3 (retrieval nDCG@5) ve M3DocVQA (multi-page QA accuracy) çalıştır. Aynı korpusta aynı sentezleyici ile OCR-sonra-text pipeline'ı da çalıştır. Bir content-type × yaklaşım matrisi üret.

8. **UI.** Önce Streamlit prototip; sonra sayfa-başına evidence-region overlay'li Next.js 15 üretim viewer'ı.

## Kullan

```
$ doc-qa ask "EMEA segmenti için 2024 operating margin değişimi neydi?"
[retrieve]   320ms'de top-5 sayfa (ColQwen2.5, MaxSim, Vespa)
[synth]      qwen3-vl-30b, 1.4s, citation (form-10k-2024, p. 88) + (..., p. 92)
cevap:
  EMEA operating margin %18.2'den %16.8'e taşındı, 140bp düşüş.
  cited: 10-K-2024.pdf p.88 (Table 4, Segment Operating Margin)
         10-K-2024.pdf p.92 (MD&A, Operating Performance)
[viewer]     p.88 Table 4 üzerinde overlay'li highlight'lı bounding box'larla aç
```

## Yayınla

`outputs/skill-doc-qa.md` teslimat'ı açıklar: belirli bir korpusa tune edilmiş ve ViDoRe v3'te OCR-sonra-text baseline'ına karşı değerlendirilmiş görsel-öncelikli multimodal doküman QA sistemi.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | ViDoRe v3 / M3DocVQA doğruluğu | OCR-text baseline'ına ve yayınlanmış leaderboard'a karşı benchmark sayıları |
| 20 | Evidence-region grounding'i | Gerçekten cevap span'ini içeren cited region'ların oranı |
| 20 | Depolama ve gecikme mühendisliği | DocPruner sıkıştırma oranı, index p95, cevap p95 |
| 20 | Multi-page reasoning | El-etiketli 100-soruluk multi-page set'te doğruluk |
| 15 | Source-inspection UX'i | Viewer netliği, overlay sadakati, yan yana karşılaştırma araçları |
| **100** | | |

## Alıştırmalar

1. Aynı korpusta ColQwen2.5-v0.2 vs ColQwen3-omni ölç. Birinin doğru aldığı ve diğerinin kaçırdığı sayfaları belirle. Tipe göre route etmek için index'e bir "content class" tag ekle.

2. Embedding'leri agresif olarak prune et (%75, %90). Sıkıştırma cliff'ini bul: ViDoRe nDCG@5'in OCR baseline'ının altına düştüğü nokta.

3. Bir hybrid inşa et: OCR-sonra-text ve ColQwen'i paralel çalıştır, RRF ile fuse et, cross-encoder ile rerank yap. Hybrid ikisinden birini geçiyor mu? En çok nerede yardım ediyor?

4. Qwen3-VL-30B'yi daha küçük bir VLM (Qwen2.5-VL-7B) ile değiştir. Dolar başına accuracy eğrisini ölç.

5. El yazısı not desteği ekle. El yazısı korpusunu render et, ColQwen ile embed et, retrieval ölç. Bir el yazısı OCR pipeline'ına karşı karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Late interaction | "ColPali-tarzı retrieval" | Sorgu token'ları sayfa patch'lerine bağımsız skor verir; MaxSim aggregate eder |
| Multi-vector | "Per-patch embedding" | Her dokümanın tek bir pool'lanmış vektörü değil, çok sayıda vektörü var |
| MaxSim | "Late-interaction scoring" | Her sorgu token'ı için, doküman vektörleri üzerinde max similarity al; topla |
| DocPruner | "Patch sıkıştırma" | Patch'lerin %50'sini ihmal edilebilir doğruluk kaybıyla tutan 2026 pruning |
| ViDoRe v3 | "Doküman-retrieval benchmark'ı" | Visual-doküman retrieval ölçümü için 2026 standardı |
| Evidence region | "Cited bounding box" | Kaynak sayfada cevap span'ini lokalize eden bir bbox |
| OCR fallback | "Equation channel" | Denklem- veya tablo-yoğun sayfalar için vision ile birlikte kullanılan text pipeline |

## İleri Okuma

- [ColPali (Illuin Tech) repository'si](https://github.com/illuin-tech/colpali) — referans late-interaction doküman retrieval'ı
- [ColPali makalesi (arXiv:2407.01449)](https://arxiv.org/abs/2407.01449) — temel method makalesi
- [Hugging Face'de ColQwen ailesi](https://huggingface.co/vidore) — üretime hazır checkpoint'ler
- [M3DocRAG (Adobe)](https://arxiv.org/abs/2411.04952) — multi-page multimodal RAG baseline'ı
- [Vespa multi-vector tutorial](https://docs.vespa.ai/en/colpali.html) — referans serving stack'i
- [Qdrant multi-vector desteği](https://qdrant.tech/documentation/concepts/vectors/#multivectors) — alternatif index
- [AstraDB multi-vector](https://docs.datastax.com/en/astra-db-serverless/databases/vector-search.html) — alternatif managed index
- [Nougat OCR](https://github.com/facebookresearch/nougat) — denklem-yetenekli OCR fallback'i
