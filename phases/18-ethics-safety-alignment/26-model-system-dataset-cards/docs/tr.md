# Model, System ve Dataset Card'ları

> Üç belgelendirme formatı AI transparency'sini yapılandırır. Model Card'lar (Mitchell vd. 2019) — modeller için besin etiketleri: eğitim verisi, nicel disaggregate edilmiş analizler, etik düşünceler, uyarılar; Hugging Face model card'larının yalnızca %0.3'ü etik düşünceleri belgeler (Oreamuno vd. 2023). Datasheet for Datasets (Gebru vd. 2018, CACM) — motivasyon, kompozisyon, toplama süreci, etiketleme, dağıtım, bakım; elektronik-datasheet analogu. Data Card'lar (Pushkarna vd., Google 2022) — çeşitli okuyucular için boundary object'ler olarak modüler katmanlı detay (telescopic, periscopic, microscopic). 2024-2025 gelişimleri: LLM'ler üzerinden otomatik üretim (CardGen, Liu vd. 2024); model-card detayı HF'de %29'a kadar indirme artışıyla korele (Liang vd. 2024); doğrulanabilir attestation'lar (Laminator, Duddu vd. 2024); karbon/su için sürdürülebilirlik raporlama eklemeleri (Jouneaux vd. Temmuz 2025); EU/ISO düzenleyici card'ları ortaya çıkıyor. System Card'lar (Sidhpurwala 2024; Meta system-level transparency; "Blueprints of Trust" arXiv:2509.20394) — güvenlik yetenekleri, prompt-injection koruması, veri-exfiltration tespiti, insan değerleriyle alignment'ı kapsayan end-to-end AI sistem belgelendirmesi.

**Tür:** Yapım
**Diller:** Python (stdlib, model-card + datasheet + system-card üretici)
**Ön koşullar:** Faz 18 · 18 (safety framework'leri), Faz 18 · 24 (düzenleyici)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Orijinal Mitchell vd. 2019 model card'ını ve Gebru vd. 2018 datasheet'ini tarif et.
- Data Card'ların telescopic/periscopic/microscopic katmanlamasını tarif et.
- System Card'ları ve end-to-end kapsamını tarif et.
- Üç 2024-2025 gelişimini ifade et (otomatik üretim, doğrulanabilir attestation'lar, sürdürülebilirlik raporlama).

## Sorun

Düzenleyici framework'ler (Ders 24) ve lab safety policy'leri (Ders 18) ikisi de belgelendirme gerektirir. Belgelendirme formatları model-spesifikten (model card'lar) veri kümesi-spesifik'e (datasheet'ler) sistem-spesifik'e (system card'lar) gelişti. Her biri transparency'nin farklı bir kapsamını ele alır. 2024-2025 otomasyonu ve doğrulanabilir-attestation çalışması uzun süredir devam eden benimseme problemini ele alıyor.

## Kavram

### Model Card'lar (Mitchell vd. 2019)

Bölümler:
- Model detayları.
- Amaçlanan kullanım.
- Faktörler (değerlendirme için ilgili demografik veya çevresel faktörler).
- Metrikler.
- Değerlendirme verisi.
- Eğitim verisi.
- Nicel analizler (faktörlere göre disaggregate edilmiş).
- Etik düşünceler.
- Uyarılar ve öneriler.

Benimseme problemi: Oreamuno vd. 2023'ün Hugging Face model card'larını audit'i yalnızca %0.3'ün etik düşünceleri belgelediğini buldu.

### Datasheet for Datasets (Gebru vd. 2018)

Elektronik-datasheet analogu. Bölümler:
- Motivasyon (veri kümesi neden oluşturuldu).
- Kompozisyon (içinde ne var).
- Toplama süreci (nasıl bir araya getirildi).
- Etiketleme (varsa).
- Kullanımlar (amaçlanan, yasaklı, riskler).
- Dağıtım.
- Bakım.

CACM 2021'de yayınlandı. Datasheet upstream belgelendirmedir; model card'ın doğru olması datasheet'in doğru olmasına bağlıdır.

### Data Card'lar (Pushkarna vd., Google 2022)

Modüler katmanlı detay. Üç zoom seviyesi:
- **Telescopic.** Uzman olmayanlar için üst düzey özet.
- **Periscopic.** ML pratisyenleri için orta düzey genel bakış.
- **Microscopic.** Auditor'lar için detaylı özellik-seviyesi belgelendirme.

Boundary-object çerçevelemesi: farklı okuyucular aynı belgeden farklı bilgi çıkarır.

### System Card'lar

Kapsam: model + safety stack + deployment context dahil end-to-end AI sistemi. Bölümler tipik olarak şunları içerir:
- Güvenlik yetenekleri.
- Prompt-injection koruması.
- Veri-exfiltration tespiti.
- Belirtilen insan değerleriyle alignment.
- Olay yanıtı.

Sidhpurwala 2024 ve Meta system-level transparency çalışması. "Blueprints of Trust" (arXiv:2509.20394) System Card'ı Model Card'ların deployment-katmanı tamamlayıcısı olarak formalize eder.

### 2024-2025 gelişimleri

- **CardGen (Liu vd. 2024).** LLM'ler üzerinden otomatik model-card üretimi; standartlaştırılmış Mitchell 2019 alanlarında birçok insan-yazılı card'dan daha yüksek objektiflik raporluyor.
- **İndirme korelasyonu (Liang vd. 2024).** Detaylı model card'lar HF'de %29'a kadar daha yüksek indirme oranlarıyla korele — benimseme baskısı artık pazar-tahrikli, yalnızca compliance-tahrikli değil.
- **Laminator (Duddu vd. 2024).** Hardware TEE / kriptografik imzalar üzerinden doğrulanabilir attestation'lar — model card'ın yalnızca bir iddia değil, proof-of-claim taşımasına izin verir.
- **Sürdürülebilirlik (Jouneaux vd. Temmuz 2025).** Karbon, su ve compute-enerji ayak izi için eklemeler; ortaya çıkan ISO standartları.
- **Düzenleyici card'lar.** EU AI Act (Ders 24) GPAI Code of Practice Transparency bölümü model card'ları bir uyum artefaktı olarak gerektirir.

### Bu Faz 18'de nereye uyuyor

Dersler 24-25 düzenleyici ve CVE katmanlarıdır. Ders 26 belgelendirme katmanıdır. Ders 27 datasheet'in upstream'i olan training-data yönetişimidir. Ders 28 card'larda referans verilen değerlendirmeleri üreten araştırma ekosistemidir.

## Kullan

`code/main.py` bir oyuncak deployment için minimal bir model card, datasheet ve system card üretir. Her biri kanonik bölüm yapısını takip eder. Formatı inceleyebilir ve üç kapsamı karşılaştırabilirsin.

## Yayınla

Bu ders `outputs/skill-card-audit.md` üretir. Bir model card, datasheet veya system card verildiğinde, bölüm kapsamını, sayısal disaggregation'ı ve doğrulanabilir attestation'ların var olup olmadığını audit eder.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Üretilen card'ları incele. Zayıf (yalnızca placeholder) bölümleri tanımla ve onları güçlendirecek kanıtı belirt.

2. Model card'ı iki demografik grup arasında nicel disaggregate edilmiş analiz ile genişlet (Ders 20).

3. Oreamuno vd. 2023'ü %0.3 benimseme oranı üzerine oku. Etik-düşünceler benimsemesini artıracak model card şartnamesine bir yapısal değişiklik öner.

4. Laminator (Duddu vd. 2024) doğrulanabilir attestation'lar için TEE'ler kullanır. Bir değerlendirme sonucunun kriptografik attestation'ını taşıyan bir model-card alanı tasarla ve verifier'ın rolünü tarif et.

5. Geçmiş projelerinden biri veya hipotetik bir deployment için bir System Card (System Card, Model Card değil) yaz. Üçüncü-taraf auditor'lar için en yüksek değerli bölümü tanımla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| Model Card | "Mitchell card'ı" | ML modelleri için Mitchell vd. 2019 standart belgelendirmesi |
| Datasheet | "Gebru datasheet'i" | Veri kümeleri için Gebru vd. 2018 standart belgelendirmesi |
| Data Card | "Pushkarna card'ı" | Google 2022 modüler katmanlı veri belgelendirmesi |
| System Card | "deployment card'ı" | Safety stack dahil end-to-end AI sistem belgelendirmesi |
| Boundary object | "farklı okuyucular, bir belge" | Data Card'ların çerçevelemesi: aynı belge çeşitli kitlelere hizmet eder |
| Doğrulanabilir attestation | "Laminator attestation'ı" | Bir belgelendirme iddiasına eklenmiş kriptografik veya TEE kanıt |
| Sürdürülebilirlik alanı | "karbon / su ayak izi" | Çevresel hesap için ortaya çıkan 2025 ekleme |

## İleri Okuma

- [Mitchell et al. — Model Cards for Model Reporting (arXiv:1810.03993, FAT* 2019)](https://arxiv.org/abs/1810.03993) — kanonik model card
- [Gebru et al. — Datasheets for Datasets (CACM 2021, arXiv:1803.09010)](https://arxiv.org/abs/1803.09010) — datasheet makalesi
- [Pushkarna et al. — Data Cards (Google 2022)](https://arxiv.org/abs/2204.01075) — katmanlı veri belgelendirmesi
- [Sidhpurwala et al. — Blueprints of Trust (arXiv:2509.20394)](https://arxiv.org/abs/2509.20394) — System Card formalizasyonu
