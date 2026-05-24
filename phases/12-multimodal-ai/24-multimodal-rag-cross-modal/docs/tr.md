# Multimodal RAG ve Cross-Modal Retrieval

> Vision-native belge RAG bir dilim. Üretim multimodal RAG daha geniş gidiyor — gezi planlaması ("doğal ışıklı sessiz vegan brunch bul"), tıbbi triyaj ("bu fotoğraf + bu notlara hangi yaralanma uyuyor"), e-ticaret ("bu selfie'me benzer, bedenimde kıyafetler"), saha servis ("bu motor sesini artı parçanın fotoğrafını teşhis et") gibi iş akışları için metin, görsel, ses ve video boyunca retrieval. Üç 2025 surveyi — Abootorabi et al., Mei et al., Zhao et al. — alt-problemleri kodladı: cross-modal retrieval, retrieval fusion, generation grounding, multimodal değerlendirme. Bu ders survey'leri okur ve bir üretim pipeline'ı tasarlar.

**Tür:** Yapım
**Diller:** Python (stdlib, fusion + grounded generator ile cross-modal retriever)
**Ön koşullar:** Faz 12 · 23 (ColPali), Faz 11 (RAG temelleri)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Cross-modal retrieval tasarla: metin → görsel, görsel → metin, ses → video, vb.
- Üç fusion stratejisini karşılaştır: score fusion, attention-based fusion, MoE fusion.
- Generation grounding'i açıkla: kaynakların modaliteler karışımı olduğunda "kaynağını alıntıla" neye benzer.
- 2025'in üç canonical multimodal RAG survey'ini ve alt-problem taksonomisini söyle.

## Sorun

Tek modaliteli RAG çözülmüş bir kalıp: sorgu embed et, chunk'ları embed et, retrieve et, LLM'e doldur. Multimodal RAG şunu gerektirir:

1. Çoklu retrieval head (her modalitenin uyumlu uzayda embedding'lere ihtiyacı var).
2. Modaliteler arası retrieval sonuçlarının fusion'ı.
3. Modaliteler arası kaynakları alıntılayan generation grounding.
4. Cross-modal sinyali kapsayan değerlendirme metrikleri.

2025 survey'leri hepsi aynı taksonomiye varıyor.

## Kavram

### Cross-modal retrieval

A modalitesindeki sorgu verildiğinde B modalitesindeki belgeleri al. Üç kalıp:

1. Paylaşılan embedding uzayı. CLIP ve CLAP paylaşılan uzayda metin + görsel / metin + ses embedding'leri üretir. Modaliteler arası cosine similarity doğrudan çalışır. CLIP-eğitilmiş çiftlerle sınırlı.

2. Modalite başına encoder + çeviri. Metin encoder + görsel encoder + uzaylar arası eşleyen küçük çevirici modül. Gupta et al.'ın Sen2Sen'i ve diğer 2024 tasarımları. Esnek ama karmaşıklık ekler.

3. Encoder olarak VLM. Retrieval temsili olarak VLM'in hidden state'lerini kullan. VLM'in desteklediği herhangi modalite çalışır. Daha yüksek kalite, daha pahalı.

Seçim: metin+görsel için CLIP / SigLIP 2; metin+ses için CLAP; frontier kalitesinde cross-modal için VLM-hidden-state'leri.

### Fusion stratejileri

10 sonuç aldın: 5 görsel, 3 metin pasajı, 2 ses klibi. Nasıl birleştiriyorsun?

Score fusion (en ucuz). Her modalitenin kendi retriever'ı var, her biri skor döndürür. Modalite içinde skorları normalize et sonra topla. Basit, sıklıkla çalışır.

Attention-based fusion. Tüm alınan öğeleri birleştir, küçük bir attention network'ünün onları ağırlıklandırmasına izin ver. Eğitim ister.

MoE fusion. Gating network modalite-spesifik expert'lere yönlendirir. Farklı sorgu türleri farklı yönlendirilir — görsel soru görselleri daha yüksek ağırlıklandırır.

Üretim varsayılan: sorgunun baskın modalitesine hafif bias'lı score fusion. A/B domain'inde net kazanım gösteriyorsa MoE'ye yükselt.

### Generation grounding

LLM hangi alınan öğenin her iddiayı yönlendirdiğini alıntılamalı. Multi-modal için:

- Metin kaynak: standart alıntı `[1]`.
- Görsel kaynak: kısa caption ile `[img 3]`.
- Ses: `[audio 2 at 0:34]`.

Generator'ı grounding-aware veriyle eğit: eğitim hedefindeki her iddia kaynak indeksiyle etiketlenmiş. Çıkarımda model doğal olarak alıntı yayar.

### 2025 survey'leri

Abootorabi et al. (arXiv:2502.08826, "Ask in Any Modality"): multimodal RAG için taksonomi. Retrieval, fusion, generation kapsar. En geniş kapsama.

Mei et al. (arXiv:2504.08748, "A Survey of Multimodal RAG"): alt-görev benchmark'larına ve başarısızlık modlarına odaklanır. Değerlendirme tasarımı için kullanışlı.

Zhao et al. (arXiv:2503.18016): vision-odaklı survey. ColPali-family çalışmasında güçlü.

Üçünü okumak sana 2025 bahar itibariyle state of the art verir. Alt-problemlerin çoğu hâlâ açık.

### MuRAG — temelli makale

MuRAG (Chen et al., 2022) ilk multimodal RAG'dı. Multimodal KB'den görsel + metin aldı, cevaplar üretti. VLM dalgasından önce yapılabilirliği gösterdi. Modern sistemler (REACT, VisRAG, M3DocRAG) buna inşa eder.

### Bir üretim gezi-planlayıcı örneği

Sorgu: "doğal ışıklı sessiz vegan brunch bul."

Pipeline:

1. Sorguyu ayrıştır. "sessiz" → ses/yorum anahtar kelime; "vegan brunch" → menü öğesi; "doğal ışık" → görsel feature.
2. Modalite başına retrieve et:
   - Yorumlarda metin retrieval: "vegan brunch, sessiz atmosfer."
   - Restoran fotoğraflarında görsel retrieval: "doğal ışık, ferah."
   - Ambient-ses kliplerinde ses retrieval: "düşük desibel, müzik yok."
3. Skorları birleştir. Her restoran kompozit skor alır.
4. Top-k restoran → VLM generator'a tüm kanıtla → alıntılarla cevap.

Bu metin-RAG'ın çok ötesinde. Her modalite yalnızca metnin kaçırdığı sinyali ekler.

### Agentic multimodal RAG

Çok-hop: ilk retrieval yüksek-güven cevaplar döndürmezse, LLM yeniden formüle eder ve tekrar retrieve eder. Faz 14'ten agentic RAG kalıpları buraya uygulanır. Örnekler:

- İlk top-10 al → LLM "çok gürültülü, <40 dB için filtrele" sorar → yeniden retrieve et.
- Görselleri al → LLM birinin menü olduğunu görür → menü metnini al → cevapla.

Karmaşıklık ekler ama tek-atış retrieval'ın halledemediği sorguları halleder.

### Değerlendirme

Cross-modal değerlendirme hâlâ olgunlaşmamış. Yaygın proxy'ler:

- Modalite başına Recall@k.
- Birleştirilmiş top-k doğruluğu.
- İnsan-değerlendirme uçtan uca memnuniyet.
- Göreve özel (tamamlanan rezervasyonlar, yapılan alışverişler).

Tüm modaliteleri kapsayan standart benchmark yok. Çoğu makale domain-spesifik görevlerde değerlendirir.

## Kullan

`code/main.py`:

- Paylaşılan restoran corpus'unda çalışan üç mock retriever (metin, görsel, ses).
- Konfigüre edilebilir ağırlıklarla modalite skorlarını birleştiren score fusion.
- Alıntılarla son cevap yayan generator stub.
- Güven düşükse sorguyu yeniden formüle eden basit agentic döngü.

## Yayınla

Bu ders `outputs/skill-multimodal-rag-designer.md` üretir. Multimodal sorgu akışı olan bir ürün spec'i verildiğinde, retriever'ları, fusion'ı, generator'ı ve değerlendirmeyi tasarlar.

## Alıştırmalar

1. Tıbbi triyaj multimodal RAG öner: sorgu = yaralanma fotoğrafı + metin semptomlar. Hangi modaliteler hangi KB'den retrieve eder?

2. Score fusion basit bir ağırlıklı toplam. MoE fusion'ın kaçındığı hangi başarısızlık moduna sahip?

3. Abootorabi et al.'ın taksonomisini (Bölüm 3) oku. Üç canonical alt-problem ne ve seçtiğin ürüne nasıl haritalanır?

4. Bir gezi-planlayıcı multimodal RAG için bir eval spec tasarla. Hangi metrikler görsel recall'ı, ses recall'ı ve compozite doğruluğu kapsar?

5. Agentic multi-hop RAG'ın round-trip başına latency vergisi var. Hangi sorgu zorluğunda doğruluk kazanımı latency'yi haklı çıkarır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Cross-modal retrieval | "Bir modalitede sorgula, diğerini al" | Metin sorgu görselleri alır; görsel sorgu metni alır; paylaşılan uzay ya da çevirici gerektirir |
| Score fusion | "Skorları birleştir" | Modalite başına retrieval skorlarının ağırlıklı toplamı; en basit fusion |
| MoE fusion | "Modalite-yönlendirilmiş expert'ler" | Gating network sorgu başına hangi modalitenin skorlarına güvenileceğini seçer |
| Grounded generation | "Kaynaklarını alıntıla" | Cevaptaki her iddia kaynak indeksiyle etiketlenmiş |
| MuRAG | "İlk multimodal RAG" | Multimodal RAG kalıbını kuran 2022 makalesi |
| Agentic multi-hop | "Yeniden formüle et ve tekrar dene" | İlk-geçiş güveni düşük olduğunda LLM retriever'ları tekrar sorgular |

## İleri Okuma

- [Abootorabi et al. — Ask in Any Modality (arXiv:2502.08826)](https://arxiv.org/abs/2502.08826)
- [Mei et al. — A Survey of Multimodal RAG (arXiv:2504.08748)](https://arxiv.org/abs/2504.08748)
- [Zhao et al. — Vision RAG Survey (arXiv:2503.18016)](https://arxiv.org/abs/2503.18016)
- [Chen et al. — MuRAG (arXiv:2210.02928)](https://arxiv.org/abs/2210.02928)
- [Liu et al. — REACT (arXiv:2301.10382)](https://arxiv.org/abs/2301.10382)
