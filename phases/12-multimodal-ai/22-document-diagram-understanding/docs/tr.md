# Belge ve Diyagram Anlama

> Belgeler fotoğraf değil. Bir PDF, bilimsel makale, fatura ya da el yazılı formun düz görsel anlamanın yakalayamayacağı yerleşim, tablolar, diyagramlar, footnote'lar, header'lar ve semantik yapısı var. VLM öncesi yığın bir pipeline'dı: Tesseract OCR + LayoutLMv3 + table-extraction sezgileri. VLM dalgası bunu OCR-free modellerle değiştirdi — Donut (2022), Nougat (2023), DocLLM (2023) — yapılandırılmış markup'ı doğrudan yayan. 2026'ya gelindiğinde frontier sadece "sayfa görselini 2576px native'de Claude Opus 4.7'ye besle" ve yapılandırılmış-markup çıktısı bedava gelir. Bu ders belge AI'nın üç-çağ yayını okur.

**Tür:** Yapım
**Diller:** Python (stdlib, layout-aware belge parser iskeleti)
**Ön koşullar:** Faz 12 · 05 (LLaVA), Faz 5 (NLP)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Belge AI'nın üç çağını açıkla: OCR pipeline, OCR-free, VLM-native.
- LayoutLMv3'ün üç input akışını betimle: metin, layout (bbox), görsel patch'leri, birleştirilmiş masking ile.
- Donut'u (OCR-free, görsel → markup), Nougat'ı (bilimsel makale → LaTeX), DocLLM'i (layout-aware generative), PaliGemma 2'yi (VLM-native) karşılaştır.
- Yeni bir görev için belge modeli seç (faturalar, bilimsel makaleler, el yazılı formlar, Çin fişleri).

## Sorun

"Bu PDF'i anla" aldatıcı şekilde zor. Bilgi şuralarda oturuyor:

- Metin içeriği (sinyalin %90'ı).
- Yerleşim (header'lar, footnote'lar, sidebar'lar, iki sütun format).
- Tablolar (satırlar, sütunlar, birleştirilmiş hücreler).
- Figürler ve diyagramlar.
- El yazısı annotation'lar.
- Font'lar ve typography (başlık vs gövde).

Ham OCR metni döker ve gerisini kaybeder. Faturalarla ilgilenen bir sistem "Toplam: 1.245$"ın bir footnote'tan değil, sağ alttan geldiğini bilmek zorunda.

## Kavram

### Çağ 1 — OCR pipeline (2021 öncesi)

Klasik yığın:

1. PDF → sayfa başına görsel.
2. Tesseract (ya da ticari OCR) per-kelime bounding box ile metin çıkarır.
3. Layout analyzer block'ları (header, table, paragraph) tanımlar.
4. Tablo yapı tanıyıcı tabloları ayrıştırır.
5. Domain kurallar + regex alanları çıkarır.

Temiz basılı metin için çalışır. El yazısı, çarpık tarama, karmaşık tablolar, İngilizce olmayan script'lerde kırılır. Her başarısızlık modu özel exception path gerektirir.

### TrOCR (2021)

TrOCR (Li et al., arXiv:2109.10282) Tesseract'in klasik CNN-CTC'sini sentetik + gerçek metin görsellerinde eğitilmiş transformer encoder-decoder ile değiştirdi. El yazısı ve çok dilli metinde temiz zafer. Hâlâ bir pipeline (detector sonra TrOCR sonra layout), ama OCR adımı dramatik olarak iyileşti.

### Çağ 2 — OCR-free (2022-2023)

İlk OCR-free modeller dediler: tespiti tamamen atla, görsel pikselleri yapılandırılmış çıktıya doğrudan eşle.

Donut (Kim et al., arXiv:2111.15664):
- Encoder-decoder transformer, encoder Swin-B.
- Çıktı form anlama için JSON, özetleme için markdown ya da herhangi bir göreve özel şema.
- OCR yok, layout yok, tespit yok.

Nougat (Blecher et al., arXiv:2308.13418):
- Spesifik olarak bilimsel makalelerde eğitildi.
- Çıktı LaTeX / markdown.
- Denklemler, çok sütunlu yerleşim, figürler ele alır.
- Her arXiv-parser'ının çağırdığı model.

Bunlar uzman, generalist değil. Bilimsel makalede Donut başarısız olur; faturada Nougat başarısız olur.

### LayoutLMv3 (2022)

Farklı bir parça. LayoutLMv3 (Huang et al., arXiv:2204.08387) OCR'yi tutar ama layout anlama ekler:

- Üç input akışı: OCR metin token'ları, token başına 2D bounding box, görsel patch'leri.
- Üç modalite boyunca masked eğitim objective'i (masked metin, masked patch'ler, masked layout).
- Aşağı akış: sınıflandırma, entity extraction, table QA.

LayoutLMv3 OCR tabanlı belge anlamanın zirvesi. Form ve faturalarda güçlü. Yukarı akış OCR gerektirir. Standardize edilmiş belge benchmark'larında VLM-öncesi en iyi doğruluk.

### DocLLM (2023)

DocLLM (Wang et al., arXiv:2401.00908) LayoutLM'in generative kardeşi. Layout token'larına koşullu serbest-form cevap üretir. Belgeler üzerinde QA için daha iyi; hâlâ OCR input'una bağımlı.

### Çağ 3 — VLM-native (2024+)

2024 VLM'leri pipeline'ı tamamen değiştirmek için yeterince iyi oldu. Yüksek çözünürlükte tam sayfa görselini VLM'e besle, soruyu sor, cevap al.

- LLaVA-NeXT 336-tile AnyRes küçük belgeler için çalışır.
- Qwen2.5-VL dinamik-çözünürlüğü 2048+ pikseli natively halleder.
- Claude Opus 4.7 2576px belgeleri destekler.
- PaliGemma 2 (Nisan 2025) spesifik olarak belgeler + el yazısı için eğitir.

VLM-native ile OCR-pipeline arasındaki fark hızla kapandı. 2026'ya gelindiğinde VLM-native şunlarda kazanır:

- Scene text (el yazılı + basılı, karışık script'ler).
- Birleştirilmiş hücreli karmaşık tablolar.
- Metin içine gömülü matematik denklemleri.
- Metin annotation'lı figürler.

OCR pipeline'lar hâlâ şunlarda kazanır:

- Sayfa başına latency'nin önemli olduğu büyük ölçekte saf-tarama iş yükleri.
- Pipeline güvenilirliği (VLM halüsinasyonlarına karşı deterministik başarısızlıklar).
- Auditable OCR çıktısı gerektiren düzenlenmiş ortamlar.

### Claude 4.7 / GPT-5 frontier'i

2576-piksel native input'ta, frontier VLM'ler belge anlamayı neredeyse insan doğruluğunda yapar. 2026 başlarından benchmark sayıları:

- DocVQA: Claude 4.7 ~95.1, PaliGemma 2 ~88.4, Nougat ~77.3, pipelined LayoutLMv3 ~83.
- ChartQA: Claude 4.7 ~92.2, GPT-4V ~78.
- VisualMRC: Claude 4.7 ~94.

Kapalı-model farkı çoğunlukla çözünürlük ve base-LLM ölçeği. 7B açık modeller birkaç puan geride ama yetişiyor.

### Matematik denklemleri ve LaTeX çıktısı

Bilimsel makaleler denklemler için tam LaTeX çıktısı gerektirir. Nougat bunda eğitildi. LaTeX hedefleriyle eğitilmiş VLM'ler (Qwen2.5-VL-Math, Nougat türevleri) kullanılabilir LaTeX üretir. Açık LaTeX eğitimi olmadan VLM'ler okunabilir ama net olmayan transcription üretir.

2026'da bilimsel-makale pipeline'ları için: PDF üzerinde Nougat zincirleyin, sonra zorlu sayfalarda VLM.

### El yazısı

Hâlâ en zor alt-görev. Karışık basılı + el yazılı (doktor notları, doldurulmuş formlar) OCR pipeline'larının maliyet için VLM'leri hâlâ yendiği yer. Yalnızca el yazısı VLM'leri iyileşiyor (Claude 4.7, PaliGemma 2).

### 2026 tarifi

Yeni bir belge-AI projesi için:

- Ölçekte saf-basılı faturalar: LayoutLMv3 + kurallar, maliyet-verimli.
- Karışık belgeler (bilimsel + el yazılı + form): VLM-native (PaliGemma 2 ya da Qwen2.5-VL).
- Tam arXiv ingestion: matematik için Nougat, figürler için VLM.
- Düzenleyici: çapraz-kontrol için OCR pipeline + VLM doğrulayıcı.

## Kullan

`code/main.py`:

- Oyuncak layout-aware tokenizer: (metin, bbox) çiftleri verildiğinde LayoutLMv3 tarzı input üretir.
- Donut tarzı görev şeması üretici: formlar için JSON şablonu.
- OCR-pipeline, Donut, Nougat ve VLM-native boyunca sayfa başına token bütçesi karşılaştırması.

## Yayınla

Bu ders `outputs/skill-document-ai-stack-picker.md` üretir. Bir belge-AI projesi (domain, ölçek, kalite, düzenleyici) verildiğinde, OCR pipeline, OCR-free uzman ve VLM-native arasından seçer.

## Alıştırmalar

1. Projen günde 10M fatura. Hangi yığın doğruluk kaybı olmadan sayfa başına maliyeti minimize eder?

2. LayoutLMv3 form QA'da neden saf-CLIP-VLM'leri yener ama scene-text'te underperform eder? Bbox akışı neyi feda eder?

3. Nougat LaTeX üretir. VLM-native çıktının LaTeX sadakatinde Nougat'ı yendiği bir test durumu ve Nougat'ın kazandığı bir durum öner.

4. PaliGemma 2 makalesini (Google, 2024) oku. PaliGemma 1'e karşı belge doğruluğunu yükselten anahtar eğitim-veri eklemesi neydi?

5. Düzenleyici-güvenli bir hibrit tasarla: birincil olarak OCR pipeline, ikincil çapraz-kontrol olarak VLM. Anlaşmazlığı nasıl çözüyorsun?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| OCR pipeline | "Tesseract tarzı" | Aşamalı yığın: tespit -> OCR -> layout -> kurallar; deterministik, kırılgan |
| OCR-free | "Donut tarzı" | Açık OCR'yi atlayan görsel-çıktı transformer'ı; tek model |
| Layout-aware | "LayoutLM" | Input token başına bbox koordinatları içerir; modaliteler boyunca birleştirilmiş masking |
| VLM-native | "Frontier VLM" | Sayfa görselini doğrudan yüksek çözünürlükte Claude/GPT/Qwen VLM'e besle; pipeline yok |
| DocVQA | "Doc benchmark" | Belge VQA standardı; en çok alıntılanan skor |
| Markup output | "LaTeX / MD" | Serbest-form metin yerine yapılandırılmış çıktı formatı; aşağı akış otomasyonu mümkün kılar |

## İleri Okuma

- [Li et al. — TrOCR (arXiv:2109.10282)](https://arxiv.org/abs/2109.10282)
- [Blecher et al. — Nougat (arXiv:2308.13418)](https://arxiv.org/abs/2308.13418)
- [Huang et al. — LayoutLMv3 (arXiv:2204.08387)](https://arxiv.org/abs/2204.08387)
- [Kim et al. — Donut (arXiv:2111.15664)](https://arxiv.org/abs/2111.15664)
- [Wang et al. — DocLLM (arXiv:2401.00908)](https://arxiv.org/abs/2401.00908)
