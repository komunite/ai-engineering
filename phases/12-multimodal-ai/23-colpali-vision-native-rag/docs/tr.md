# ColPali ve Vision-Native Belge RAG

> Geleneksel RAG PDF'leri metne ayrıştırır, parçalara böler, parçaları embed eder, vektörleri depolar. Her adım sinyal kaybeder: OCR chart verisini düşürür, chunking tablo satırlarını kırar, metin embedding'leri figürleri görmezden gelir. ColPali (Faysse et al., Temmuz 2024) daha basit soruyu sordu: metni hiç çıkarmak neden? Sayfa görselini PaliGemma üzerinden doğrudan embed et, retrieval için ColBERT tarzı late interaction kullan ve belgenin taşıdığı tüm yerleşim, figür, font ve formatlama sinyalini tut. Yayınlanan benchmark'lar: görsel-zengin belgelerde metin-RAG'dan uçtan uca %20-40 daha iyi doğruluk. ColQwen2, ColSmol ve VisRAG kalıbı genişletti. Bu ders vision-native RAG tezini okur ve küçük bir ColPali benzeri indexer inşa eder.

**Tür:** Yapım
**Diller:** Python (stdlib, multi-vector indexer + MaxSim scorer)
**Ön koşullar:** Faz 11 (LLM Mühendisliği — RAG temelleri), Faz 12 · 05 (LLaVA)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Bi-encoder retrieval (belge başına bir vektör) ile late-interaction retrieval (belge başına birçok vektör) arasındaki farkı açıkla.
- ColBERT'in MaxSim operasyonunu ve ColPali'nin onu metin token'larından görsel patch'lere nasıl genelleştirdiğini betimle.
- Küçük bir ColPali benzeri indexer inşa et: sayfa → patch embedding → sorgu-terim embedding üzerinde MaxSim → top-k sayfa.
- Faturalar / finansal raporlar kullanım durumunda ColPali + Qwen2.5-VL generator'ı text-RAG + GPT-4 ile karşılaştır.

## Sorun

PDF'lerde metin-RAG belgenin çoğunu çöpe atar. Bir finansal raporun Q3 gelir büyümesi genelde bir chart'tadır; tıbbi raporun bulguları annote edilmiş görsellerdedir; legal sözleşmenin imza block'u layout gerçeği, metin gerçeği değil.

Metin-RAG pipeline:

1. PDF → OCR / pdftotext üzerinden metin.
2. Metin → 300-500 token chunk.
3. Chunk → bi-encoder embedding (tek vektör).
4. User sorgusu → embedding → cosine similarity → top-k chunk.
5. Chunk'lar + sorgu → LLM.

Beş kayıplı adım. Chart'lar yakalanmadı. Tablolar chunk'lara kırıldı. Çok sütun yerleşim düzleşti. Figür annotation'ları kayboldu.

ColPali çözümü: OCR'yi atla, sayfa görselini doğrudan embed et. Modelin sorgu zamanında ince taneli patch'lere attend edebilmesi için retrieval'da ColBERT tarzı late interaction kullan.

## Kavram

### ColBERT (2020)

ColBERT (Khattab & Zaharia, arXiv:2004.12832) bir metin retrieval yöntemi. Belge başına bir vektör yerine, token başına bir vektör üretir. Sorgu zamanında:

- Sorgu token'ları kendi embedding'lerini alır (N_q vektör).
- Belge token'ları embedding alır (N_d vektör, tipik olarak cache'lenir).
- Skor = sorgu token'ları üzerinde, belge token'ları üzerinde max cosine similarity toplamı: Σ_i max_j cos(q_i, d_j).

Bu MaxSim operasyonu. Her sorgu token'ı en iyi eşleşen belge token'ını "seçer". Son skor toplamdır.

Artılar: güçlü recall, terim-seviye semantik ele alır. Eksiler: belge başına N_d vektör, depolama pahalı.

### ColPali

ColPali (Faysse et al., arXiv:2407.01449) ColBERT kalıbını görsellere uygular.

- Her sayfa PaliGemma (ViT + dil) tarafından patch embedding'lere kodlanır: sayfa başına N_p vektör.
- Her user sorgusu (metin) sorgu-token embedding'lere kodlanır: N_q vektör.
- Skor = Σ_i max_j cos(q_i, p_j), yani sorgu-metin-token'ları ve sayfa-görsel-patch'leri üzerinde MaxSim.
- Top-k sayfaları toplam skor ile al.

Belge-ingestion zamanında: her sayfayı PaliGemma ile embed et, tüm patch embedding'leri sakla. Sorgu zamanında: sorgu token'larını embed et, tüm saklanan sayfa embedding'lerine karşı MaxSim hesapla, top-k sayfa döndür.

Artılar: uçtan uca görsel-zengin belgelerde metin-RAG'ı %20-40 yener. Her patch-vektör yerel yerleşim ve içeriği yakalar.

Eksiler: N_p patch × 4-byte float × D-boyutlu vektör sayfa başına = depolama hızla büyür. PQ / OPQ quantization ile hafifletilir.

### ColQwen2 ve ColSmol

ColQwen2 (illuin-tech, 2024-2025) PaliGemma'yı Qwen2-VL ile değiştirir. Daha iyi base encoder, daha iyi retrieval.

ColSmol yerel / edge kullanım için daha küçük ölçek varyantı. ~1B param'da ColSmol retriever tüketici GPU'da koşar.

### VisRAG

VisRAG (Yu et al., arXiv:2410.10594) farklı bir varyant: patch'lerde MaxSim yerine, her sayfayı VLM ile tek vektöre pool'la, sonra bi-encoder retrieve et. Daha hızlı indexing + daha küçük depolama, daha zayıf recall.

Kalite-vs-maliyet trade-off'u: kalite için ColPali, ölçek için VisRAG.

### M3DocRAG

M3DocRAG (Cho et al., arXiv:2411.04952) multi-modal retrieval'ı çok-sayfa çok-belge akıl yürütmeye genişletir. Belgeler arası sayfalar alır, VLM için çok-sayfa context oluşturur.

### ViDoRe — benchmark

ColPali'nin companion benchmark'ı. Visual Document Retrieval Evaluation. Görevler finansal raporları, bilimsel makaleleri, yönetim belgelerini, tıbbi kayıtları, manuel'leri içerir. Metrik: nDCG@5.

ColPali-v1 ViDoRe'de ~%80 nDCG@5 puanlıyor; aynı belgelerde metin-RAG ~%50-60 puanlıyor.

### Uçtan uca RAG pipeline

Vision-native RAG için:

1. Ingest: PDF → sayfa görselleri → PaliGemma kodlaması → tüm patch embedding'leri sakla.
2. Sorgu: user metni → sorgu-token embedding → tüm indexlenmiş sayfalara karşı MaxSim → top-k sayfa.
3. Üret: top-k sayfa görselleri + sorgu → VLM (Qwen2.5-VL ya da Claude) → cevap.

Hiçbir yerde OCR yok. Figürler, chart'lar, font'lar, yerleşim hepsi cevaba akar.

### Depolama matematiği

Sayfa başına 729 patch ve 128 boyutlu embedding ile 50 sayfalık finansal rapor:

- ColPali: 50 * 729 * 128 * 4 byte = ~18 MB ham, PQ sonrası ~4 MB.
- Text-RAG: 50 chunk * 768-boyut * 4 byte = ~150 kB.

ColPali belge başına ~30x daha çok depolama. Ölçekte OPQ / PQ onu ~5-10x'e indirir, genelde tolere edilebilir.

### Metin-RAG'ın hâlâ kazandığı yer

- Yerleşim sinyali olmayan saf-metin belgeler (wiki makaleleri, chat log'ları). Metin-RAG daha basit ve depolama-ucuz.
- Depolamanın maliyete hakim olduğu çok milyon-sayfa arşivler.
- Retrieval yanında çıkarılabilir OCR metni gerektiren katı düzenleyici gereksinimler.

2026'da diğer her şey için — finansal raporlar, bilimsel makaleler, legal sözleşmeler, tıbbi kayıtlar, UX dokümantasyonu — vision-native RAG kazanır.

## Kullan

`code/main.py`:

- Oyuncak patch encoder: bir "sayfayı" (küçük feature vektör grid'i) bir patch embedding dizisine eşler.
- MaxSim scorer: bir sorgu token embedding seti ile sayfa patch seti arasında ColBERT tarzı skor hesaplar.
- 5 oyuncak sayfayı index'ler, 3 sorgu çalıştırır, skorlarla top-k döndürür.

## Yayınla

Bu ders `outputs/skill-vision-rag-designer.md` üretir. Bir belge-RAG projesi verildiğinde, ColPali / ColQwen2 / VisRAG / text-RAG seçer ve depolamayı boyutlandırır.

## Alıştırmalar

1. Sayfa başına 729 patch, 128-boyut emb, 4-byte float ile 200 sayfalık yıllık rapor. Ham depolama ve PQ-sıkıştırılmış (8x) depolama hesapla.

2. MaxSim Σ_i max_j cos(q_i, p_j). Bu toplam basit mean similarity'nin yakalamadığı neyi yakalar?

3. ColPali sayfaları patch setleri olarak index'liyor. Onun yerine kelime seviyesinde (ColBERT yaptığı gibi) index'lersek ne değişir? Trade-off'lar?

4. Sorgu başına 500ms latency bütçeli 1M-sayfa corpus için uçtan uca pipeline tasarla. ColQwen2 / VisRAG seç ve haklı çıkar.

5. M3DocRAG'ı (arXiv:2411.04952) oku. Çok-sayfa attention kalıbını ve tek-sayfa ColPali retrieval'dan nasıl farklı olduğunu betimle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Late interaction | "ColBERT tarzı" | Tek belge vektörü değil, token başına ya da patch başına embedding'ler + MaxSim kullanarak retrieval |
| MaxSim | "Patch'ler üzerinde max" | Her sorgu token'ı için en yüksek-similarity belge token'ını seç; sorgu boyunca topla |
| Bi-encoder | "Tek-vektör" | Belge başına bir vektör; daha hızlı ama granularity kaybeder |
| Multi-vector | "Belge başına çok-vektör" | Belge / sayfa başına N_p vektör sakla; depolama maliyeti büyür ama recall iyileşir |
| Patch embedding | "Sayfa feature'ı" | VLM encoder'dan görsel patch başına bir vektör, sayfa başına cache'lenir |
| ViDoRe | "Vision doc bench" | ColPali'nin visual document retrieval için benchmark suite'i |
| PQ quantization | "Product quantization" | Vektör similarity'sini korurken depolamayı ~8x küçülten sıkıştırma |

## İleri Okuma

- [Faysse et al. — ColPali (arXiv:2407.01449)](https://arxiv.org/abs/2407.01449)
- [Khattab & Zaharia — ColBERT (arXiv:2004.12832)](https://arxiv.org/abs/2004.12832)
- [Yu et al. — VisRAG (arXiv:2410.10594)](https://arxiv.org/abs/2410.10594)
- [Cho et al. — M3DocRAG (arXiv:2411.04952)](https://arxiv.org/abs/2411.04952)
- [illuin-tech/colpali GitHub](https://github.com/illuin-tech/colpali)
