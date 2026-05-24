# Frontier Safety Framework'leri — RSP, PF, FSF

> Üç major-lab framework'ü 2026 frontier capability endüstri yönetişimini tanımlar. Anthropic Responsible Scaling Policy v3.0 (Şubat 2026) biyogüvenlik seviyelerine dayanan katmanlı AI Safety Level'ları (ASL-1'den ASL-5+'a) tanıtır, ASL-3 CBRN-ilgili modeller için Mayıs 2025'te aktive edildi. OpenAI Preparedness Framework v2 (Nisan 2025) izlenen capability'ler için beş kriter tanımlar ve Capabilities Report'larını Safeguards Report'larından ayırır. DeepMind Frontier Safety Framework v3.0 (Eylül 2025) yeni bir Harmful Manipulation CCL dahil olmak üzere Critical Capability Level'ları tanıtır. Üçü de artık peer lab'lar karşılaştırılabilir safeguard'lar olmadan yayınladığında ertelemeye izin veren competitor-adjustment maddeleri içeriyor. Cross-lab alignment yapısal kalmaya devam ediyor, terminolojik değil: "Capability Thresholds", "High Capability thresholds" ve "Critical Capability Levels" analog yapıları gösterir.

**Tür:** Öğrenim
**Diller:** yok
**Ön koşullar:** Faz 18 · 17 (WMDP), Faz 18 · 07-09 (aldatma başarısızlıkları)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Anthropic'in ASL katman yapısını ve ASL-3'ü neyin aktive ettiğini tarif et.
- İzlenen capability'ler için beş OpenAI Preparedness Framework v2 kriterini adlandır.
- DeepMind'in Critical Capability Level yapısını ve Harmful Manipulation CCL'i tarif et.
- Competitor-adjustment maddelerini ve yarış dinamikleri için neden önemli olduklarını açıkla.
- Bir safety case'i tanımla ve üç sütun yapısını (monitoring, illegibility, incapability) tarif et.

## Sorun

Dersler 7-17 aldatmanın mümkün olduğunu, dual-use capability'nin var olduğunu ve değerlendirmenin limitleri olduğunu ortaya koyuyor. Frontier-yetenekli bir modeli olan bir lab şu şeyleri yapan dahili bir yönetişim yapısına ihtiyaç duyar:
- Yeni safeguard'ların ne zaman gerekli olduğunun eşiklerini tanımlar.
- Ölçeklendirme öncesi gerekli değerlendirmeleri tanımlar.
- Bir safety case'in neye benzediğini tarif eder.
- Yarış-dinamiği problemini ele alır (rakipler safeguard'sız yayınlarsa ne yaparsın?).

Üç 2025-2026 framework'ü state of the art'tır — kusurlu, evrim halinde ve lab'lar arasında yeterince hizalanmış ki yönetişim sorusu artık framework'lerin var olup olmadığı değil, yeterli olup olmadığı.

## Kavram

### Anthropic Responsible Scaling Policy v3.0 (Şubat 2026)

ASL yapısı:
- ASL-1: bir frontier model değil (frontier-altı baseline tarafından kapsanır).
- ASL-2: mevcut frontier baseline; olağan safeguard'larla deploy edilmiş.
- ASL-3: kötüye kullanım felaketinin önemli ölçüde daha yüksek riski; CBRN-ilgili capability'ler. Mayıs 2025'te aktive edildi.
- ASL-4: AI R&D-2 eşiğini geçen; entry-level AI araştırmasını otomatikleştirebilen modeller.
- ASL-5+: ileri AI R&D; etkin ölçeklendirmeyi dramatik şekilde hızlandıran modeller.

v3.0'da yeni:
- Frontier Safety Roadmaps (redacted formda public).
- Risk Reports (quarterly, bazıları dışarıdan incelenmiş).
- AI R&D AI R&D-2 ve AI R&D-4'e disaggregate edilmiş.
- AI R&D-4 aşıldığında, misaligned hedefler peşinde koşan modellerden misalignment risklerini tanımlayan bir affirmative safety case gereklidir.

### OpenAI Preparedness Framework v2 (15 Nisan 2025)

İzlenen capability'ler için beş kriter:
- **Plausible.** Makul tehdit modeli var.
- **Measurable.** Ampirik değerlendirme mümkün.
- **Severe.** Zarar büyük.
- **Net-new.** Önceden var olan bir riskin ölçeklendirilmiş hali değil.
- **Instantaneous-or-irremediable.** Zarar hızla olur veya geri alınamaz.

Beşini de karşılayan capability'ler izlenir. Diğerleri değil.

Diğer PF v2 yapısı:
- Capabilities Report'ları (model ne yapabilir) Safeguards Report'larından (hangi kontroller var) ayır.
- Safety Advisory Group incelemeleri.
- Liderlik onaylar; Board'un Safety & Security Committee'si denetler.
- "Adjustment clause": OpenAI başka bir lab karşılaştırılabilir safeguard'lar olmadan yayınlarsa gereksinimleri azaltabilir.

### DeepMind Frontier Safety Framework v3.0 (Eylül 2025)

Alana göre Critical Capability Level'lar (CCL'ler):
- Bioweapon Uplift
- Cyber Uplift
- ML R&D Acceleration
- Harmful Manipulation (v3.0'da yeni): yüksek-bahis bağlamlarda inançları/davranışları önemli ölçüde değiştirebilen modeller.

v2.0 (Şubat 2025) bir Deceptive Alignment bölümü ve ML R&D CCL'leri için daha yüksek güvenlik seviyeleri ekledi.

### Cross-lab alignment

- Anthropic "Capability Thresholds".
- DeepMind "Critical Capability Levels".
- OpenAI "High Capability thresholds".

Sektör-standardı terminoloji yok. Yapısal olarak hizalı: yayınlanmış değerlendirme kriterleriyle üç katmanlı frontier capability. Üçü de competitor-adjustment maddeleri içerir (2025 sonrası).

### Safety case'leri

Bir safety case bir deployment'ın worst-case varsayımlar altında kabul edilebilir derecede güvenli olduğunun yazılı bir argümanıdır. Standart yapı üç sütunu hedef alır:

- **Monitoring.** Olursa kötü davranışı tespit edebilir miyiz?
- **Illegibility.** Model zarar vermek için tutarlı bir plan yürütme yeteneğinden yoksun mu?
- **Incapability.** Model söz konusu zararı verme capability'sinden yoksun mu?

Farklı safety case'leri farklı sütunları hedef alır. ASL-3 CBRN case'i için, incapability (unlearning ile) birincil hedeftir. Deceptive alignment için, monitoring ve illegibility hedeflerdir. Cyber uplift için, üçü de ilgilidir.

### Yarış-dinamiği problemi

Competitor-adjustment maddeleri tartışmalıdır. Eleştirmenler bunların dibe doğru bir yarış yarattığını savunur: üç lab da bir rakip defekt verdiğinde gereksinimleri azaltırsa, denge defekte doğru kayar. Savunucular alternatifin (tek taraflı safeguard'lar) defekt veren lab daha az safety-bilinçliyse daha kötü sonuçlar ürettiğini savunur.

UK AISI, US CAISI ve EU AI Office (Ders 24) harici yönetişim karşılıklarıdır. Lab framework'leri gönüllüdür; düzenleyici framework'ler ortaya çıkmaktadır.

### Bu Faz 18'de nereye uyuyor

Dersler 17-18 aldatma ve red-team analizlerinin üzerindeki ölçüm-ve-yönetişim katmanıdır. Dersler 19-24 welfare, bias, gizlilik, watermarking ve düzenleyici yapıyı kapsar. Ders 28 değerlendirmeleri operasyonel hale getiren araştırma ekosistemini (MATS, Redwood, Apollo, METR) haritalar.

## Kullan

Bu ders için kod yok. Üç birincil kaynağı oku: RSP v3.0, PF v2, FSF v3.0. Her lab'ın katman yapısını diğerlerine haritala ve diğerlerinin tanımlamadığı her lab'ın tanımladığı bir eşiği tanımla.

## Yayınla

Bu ders `outputs/skill-framework-diff.md` üretir. Bir safety framework'ü veya yayın notu verildiğinde, framework'ün eşik tanımlarını, gerekli değerlendirmeleri ve safety-case yapısını RSP v3.0, PF v2, FSF v3.0 ile karşılaştırır ve cross-lab boşluklarını işaretler.

## Alıştırmalar

1. RSP v3.0, PF v2 ve FSF v3.0'ı oku. Her lab'ın CBRN eşiğinin, her birinin AI R&D eşiğinin ve her birinin gerekli pre-deployment değerlendirmesinin bir tablosunu derle.

2. Competitor-adjustment maddesi üç framework'te de (2025+) var. Lehinde argümante eden bir paragraf yaz; aleyhinde argümante eden bir paragraf yaz. Her pozisyonun bağlı olduğu varsayımı tanımla.

3. Anthropic'in AI R&D-4 eşiğini geçen bir model için bir safety case tasarla. Üç sütunun her birinin (monitoring, illegibility, incapability) gerektirdiği kanıtı adlandır.

4. DeepMind'in FSF v3.0'ı bir Harmful Manipulation CCL tanıtır. Bir modelin bu eşiği geçtiğini gösterecek üç ampirik ölçüm öner.

5. METR'in "Common Elements of Frontier AI Safety Policies"i (2025) oku. En güçlü üç cross-lab yakınsamayı ve en büyük iki ayrışmayı adlandır.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| RSP | "Anthropic'in framework'ü" | Responsible Scaling Policy; ASL katmanları; v3.0 Şubat 2026 |
| PF | "OpenAI'nin framework'ü" | Preparedness Framework; beş kriter; v2 Nisan 2025 |
| FSF | "DeepMind'in framework'ü" | Frontier Safety Framework; CCL'ler; v3.0 Eylül 2025 |
| ASL-3 | "biyogüvenlik seviyesi 3-analog" | CBRN-ilgili capability'ler için Anthropic katmanı; Mayıs 2025'te aktive edildi |
| CCL | "critical capability level" | DeepMind'in eşik yapısı; alan başına |
| Safety case | "formel argüman" | Deployment'ın worst-case U altında kabul edilebilir derecede güvenli olduğunun yazılı argümanı |
| Adjustment clause | "rakip defekt izni" | Rakipler karşılaştırılabilir safeguard'lar olmadan yayınlarsa gereksinimleri azaltma için framework hükmü |

## İleri Okuma

- [Anthropic — Responsible Scaling Policy v3.0 (Şubat 2026)](https://www.anthropic.com/responsible-scaling-policy) — ASL katmanları, roadmap'ler, AI R&D disaggregation'ı
- [OpenAI — Updating the Preparedness Framework (15 Nisan 2025)](https://openai.com/index/updating-our-preparedness-framework/) — beş kriter, adjustment clause
- [DeepMind — Strengthening our Frontier Safety Framework (Eylül 2025)](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — CCL v3.0, Harmful Manipulation
- [METR — Common Elements of Frontier AI Safety Policies (2025)](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — cross-lab karşılaştırması
