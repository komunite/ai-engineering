# Alignment Araştırma Ekosistemi — MATS, Redwood, Apollo, METR

> Beş organizasyon 2026 non-lab alignment araştırma katmanını tanımlar. MATS (ML Alignment & Theory Scholars): 2021 sonundan beri 527+ araştırmacı, 180+ makale, 10K+ atıf, h-index 47; 2024 yaz cohort'u ~90 scholar ve 40 mentor ile 501(c)(3) olarak inkorporate edildi; 2025-öncesi mezunların %80'i Anthropic, DeepMind, OpenAI, UK AISI, RAND, Redwood, METR, Apollo'da 200+ ile safety/security üzerinde çalışıyor. Redwood Research: Buck Shlegeris tarafından kurulan applied alignment lab'ı; AI Control tanıttı (Ders 10); control safety case'leri üzerine UK AISI ile işbirliği yapar. Apollo Research: frontier lab'lar için pre-deployment scheming değerlendirmeleri; In-Context Scheming (Ders 8) ve Towards Safety Cases for AI Scheming'in yazarı. METR (Model Evaluation and Threat Research): görev-tabanlı capability değerlendirmeleri, otonom-görev zaman-horizon çalışmaları; "Common Elements of Frontier AI Safety Policies" lab framework'lerini karşılaştırır. Eleos AI Research: model-welfare pre-deployment değerlendirmeleri (Ders 19); Claude Opus 4 welfare değerlendirmesi gerçekleştirdi.

**Tür:** Öğrenim
**Diller:** yok
**Ön koşullar:** Faz 18 · 01-27 (önceki Faz 18 dersleri)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Non-lab alignment araştırma ekosisteminin beş organizasyonunu ve temel çıktılarını tanımla.
- MATS'in ölçeğini (scholar'lar, makaleler, h-index) ve yetenek pipeline'ı olarak rolünü tarif et.
- Redwood'un AI Control gündemini ve UK AISI ile partnerliğini tarif et.
- METR'in görev-tabanlı değerlendirme metodolojisini tarif et.

## Sorun

Frontier lab'lar (Ders 18) safety değerlendirmelerini dahili olarak üretir ve seçili sonuçları yayınlar. Lab'lar dışındaki ekosistem değerlendirmelerin doğrulandığı, novel failure mode'ların ilk keşfedildiği ve yeteneğin eğitildiği yerdir. Ekosistemi anlamak hangi araştırma bulgularının kim tarafından güvenildiğini yorumlamaya yardımcı olur.

## Kavram

### MATS (ML Alignment & Theory Scholars)

2021 sonunda başladı. Araştırma mentorluk programı; scholar'lar spesifik bir alignment problemi üzerinde bir kıdemli araştırmacıyla 10-12 hafta geçirir.

Ölçek (2026):
- Başlangıçtan beri 527+ araştırmacı.
- 180+ yayınlanmış makale.
- 10K+ atıf.
- h-index 47.
- 2024 yaz: 90 scholar + 40 mentor; 501(c)(3) olarak inkorporate edildi.

Kariyer sonuçları: 2025-öncesi mezunların ~%80'i safety/security üzerinde çalışıyor. Anthropic, DeepMind, OpenAI, UK AISI, RAND, Redwood, METR, Apollo'da 200+.

### Redwood Research

Applied alignment lab. Buck Shlegeris tarafından kuruldu. AI Control gündemini (Ders 10) tanıttı. Control safety case'leri üzerine UK AISI ile işbirliği yapar. Değerlendirme tasarımı üzerinde DeepMind ve Anthropic'e danışmanlık eder.

Kanonik makaleler: Greenblatt, Shlegeris vd., "AI Control" (arXiv:2312.06942, ICML 2024); Alignment Faking (Greenblatt, Denison, Wright vd., arXiv:2412.14093, Anthropic ile ortak).

Tarz: spesifik tehdit modelleri, worst-case adversary'ler, stress-test edilebilen somut protokoller.

### Apollo Research

Frontier lab'lar için pre-deployment scheming değerlendirmeleri. In-Context Scheming'in yazarı (Ders 8, arXiv:2412.04984). 2025 OpenAI anti-scheming eğitim işbirliği partneri. Towards Safety Cases for AI Scheming (2024) üretir.

Tarz: aldatmanın ortaya çıkabileceği agentic-setting değerlendirmeleri; üç sütun ayrıştırması (misalignment, goal-directedness, situational awareness).

### METR (Model Evaluation and Threat Research)

Görev-tabanlı capability değerlendirmeleri. Otonom-görev tamamlama zaman-horizon çalışmaları. "Common Elements of Frontier AI Safety Policies" (metr.org/common-elements, 2025) lab framework'lerini karşılaştırır.

Apollo ile AI Scheming safety-case sketch'inin ortak yazarı.

Tarz: uzun-horizon görev değerlendirmeleri, ampirik capability ölçümü, framework sentezi.

### Eleos AI Research

Model-welfare pre-deployment değerlendirmeleri. System card'ın 5.3 bölümünde belgelenen Claude Opus 4 welfare değerlendirmesini gerçekleştirdi. Ders 19'un welfare-ilgili iddiaları için dış metodoloji kontrolü sağlar.

### Akış

MATS araştırmacıları eğitir. Mezunlar Anthropic, DeepMind, OpenAI'ya (lab safety ekipleri) veya Redwood, Apollo, METR, Eleos'a (dış değerlendirme) gider. Dış değerlendiriciler lab'larla ve UK AISI / CAISI ile ortaklık kurar. Yayınlar ekosistemi sonraki cohort için MATS'e geri besler.

### Bu katman neden önemli

Tek-kaynak değerlendirmeleri güvenilmezdir: kendi modellerini değerlendiren lab'lar yapısal bir çıkar çatışmasına sahiptir. Dış değerlendiriciler lab'ın az raporlayabileceği failure mode'ları gündeme getirebilir ve doğrulayabilir. 2024 Sleeper Agents makalesi (Ders 7) Anthropic + Redwood'du; Alignment Faking Anthropic + Redwood'du; In-Context Scheming Apollo'ydu; Anti-Scheming Apollo + OpenAI'ydı. Multi-org yapısı kalite kontrolüdür.

### Bu Faz 18'de nereye uyuyor

Dersler 7-11 Redwood ve Apollo çalışmalarına referans verir; Ders 18 METR'in framework karşılaştırmasına referans verir; Ders 19 Eleos'a referans verir. Ders 28 fazın geri kalanının dayandığı ekosistem için açık organizasyonel haritadır.

## Kullan

Kod yok. Dış sentezin lab-dahili policy çalışmasına nasıl değer kattığının bir örneği olarak METR'in "Common Elements of Frontier AI Safety Policies"ini oku.

## Yayınla

Bu ders `outputs/skill-ecosystem-map.md` üretir. Bir alignment iddiası veya değerlendirmesi verildiğinde, organizasyonu, yayın mecrasını ve metodolojik tarzı tanımlar ve bilinen-karşılık organizasyonlara karşı çapraz kontrol eder.

## Alıştırmalar

1. Dersler 7-15'ten bir makale seç ve dahil olan organizasyonları tanımla. Yazarları MATS mezunları ve mevcut ekosistem üyelikleriyle çapraz kontrol et.

2. METR'in "Common Elements of Frontier AI Safety Policies"ini oku. Vurguladıkları üç cross-lab yakınsamayı ve en büyük iki ayrışmayı tanımla.

3. MATS kariyer sonuçları ~%80 safety/security'dir. Bu seçim baskısının uyumlu (alanı eğitir) mi yoksa yanlı (heterodox pozisyonları filtreler) mi olduğunu argümante et.

4. Redwood ve Apollo ikisi de control/scheming çalışması yapar ama farklı tarzlarda. Bir failure mode seç ve her birinin onu nasıl araştıracağını tarif et.

5. Eleos AI tek saf model-welfare organizasyonudur. Farklı bir welfare-bitişik soruya (cognitive liberty, robotic embodiment, vb.) odaklanan hipotetik bir ikinci organizasyon tasarla ve metodolojisini ifade et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| MATS | "mentorluk programı" | ML Alignment & Theory Scholars; 2021'den beri 527+ araştırmacı |
| Redwood Research | "control lab'ı" | Applied alignment; AI Control yazarları; UK AISI partneri |
| Apollo Research | "scheming eval'ları" | Frontier lab'lar için pre-deployment scheming değerlendirmeleri |
| METR | "görev-horizon eval'ları" | Görev-tabanlı capability değerlendirmeleri; framework sentezi |
| Eleos AI | "welfare lab'ı" | Model-welfare pre-deployment değerlendirmeleri |
| Yetenek pipeline'ı | "MATS -> lab'lar" | MATS mezunları Anthropic, DM, OpenAI, Redwood, Apollo, METR'a akar |
| Dış değerlendirme | "non-lab kontrol" | Modelin üreticisi tarafından yapılmayan değerlendirme; güvenilirlik katar |

## İleri Okuma

- [MATS (ML Alignment & Theory Scholars)](https://www.matsprogram.org/) — mentorluk programı
- [Redwood Research](https://www.redwoodresearch.org/) — AI Control makaleleri
- [Apollo Research](https://www.apolloresearch.ai/) — scheming değerlendirmeleri
- [METR — Common Elements of Frontier AI Safety Policies](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — framework karşılaştırması
- [Eleos AI Research](https://www.eleosai.org/research) — model welfare metodolojisi
