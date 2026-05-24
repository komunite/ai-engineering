# Veri Provenance ve Training-Data Yönetişimi

> EU AI Act GPAI için Ağustos 2025'e kadar makine-okunabilir opt-out standartlarını gerektirir (EU Copyright Directive TDM exception üzerinden). California AB 2013 (2024'te imzalandı) — Generative AI training-data transparency geliştiricilerin 12 zorunlu alanla veri kümelerinin bir özetini yayınlamasını gerektirir. 2025 DPA legitimate interest hizalanması: Irish DPC (21 Mayıs 2025) EDPB görüşünden sonra safeguard'larla Meta'nın first-party kamu EU/EEA yetişkin içeriği üzerinde LLM eğitimini kabul eder; Cologne Higher Regional Court (23 Mayıs 2025) ihtiyati tedbir kararını reddeder; Hamburg DPA aciliyeti düşürür; UK ICO (23 Eylül 2025) LinkedIn'in AI-eğitim safeguard'larına (transparency, basitleştirilmiş opt-out, genişletilmiş itiraz pencereleri) pozitif düzenleyici yanıt verir ve izlemeye devam eder — formel bir clearance değil. Brezilya ANPD (2 Temmuz 2024) yetersiz bilgi transparency'si üzerine Meta'nın işlemesini askıya aldı; preventive measure Meta bir uyum planı sunduktan sonra 30 Ağustos 2024'te kaldırıldı. Anahtar geri dönüşsüzlük problemi: cookie-consent framework'leri gerçek zamanlı, geri döndürülebilir tracking için tasarlanmıştır; veri model ağırlıklarına girdiğinde, cerrahi silme imkansızdır — eğitilmiş neural network'ler için pratik GDPR right-to-erasure yok. Uyum penceresi toplama zamanındadır. Data Provenance Initiative (dataprovenance.org, Longpre, Mahari, Lee vd., "Consent in Crisis", Temmuz 2024): büyük ölçekli audit yayıncıların robots.txt kısıtlamaları eklediği oranda AI veri commons'ının hızlı düşüşünü gösterir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, 12-alan California AB 2013 scaffold üretici)
**Ön koşullar:** Faz 18 · 24 (düzenleyici), Faz 18 · 26 (card'lar)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- California AB 2013'ün Generative AI training-data transparency için 12 zorunlu alanını tarif et.
- Legitimate-interest LLM eğitimi üzerine 2025 DPA pozisyonunu ifade et (Irish DPC, UK ICO, Hamburg, Cologne).
- Geri dönüşsüzlük problemini tarif et: GDPR right-to-erasure'nin eğitilmiş neural network'ler için neden pratik bir eşdeğeri olmadığı.
- Data Provenance Initiative'in "Consent in Crisis" bulgusunu ifade et.

## Sorun

Training-data yönetişimi her model card'ın (Ders 26) ve düzenleyici yükümlülüğün (Ders 24) upstream'idir. 2024-2025'te, düzenleyici manzara üç ilkede konsolide oldu: opt-out altyapısı, veri-kümesi-başına ifşa ve kamuya açık veri için legitimate-interest uyumlamaları. Toplama zamanında uymayan sağlayıcılar downstream'de remediation yapamaz.

## Kavram

### California AB 2013

2024'te imzalandı. 1 Ocak 2022 veya sonrasında yayınlanan sistemler için belgelendirme 1 Ocak 2026'ya veya öncesinde yayınlanmalıdır. Bölüm 3111(a) geliştiricilerin 12 yasal madde ile eğitimde kullanılan veri kümelerinin yüksek düzey özetini yayınlamasını gerektirir:
1. Veri kümelerinin kaynakları veya sahipleri.
2. Veri kümelerinin AI sisteminin amaçlanan amacını nasıl ilerlettiğinin açıklaması.
3. Veri kümelerindeki veri noktalarının sayısı (genel aralıklar kabul edilebilir; dinamik veri kümeleri için tahminler).
4. Veri noktalarının türlerinin açıklaması (etiketli veri kümeleri için etiket türleri; etiketsiz için genel karakteristikler).
5. Veri kümelerinin telif hakkı, marka veya patentle korunan herhangi bir veri içerip içermediği veya tamamen public domain'de olup olmadığı.
6. Veri kümelerinin satın alınıp alınmadığı veya lisanslanıp lisanslanmadığı.
7. Veri kümelerinin kişisel bilgi içerip içermediği (Cal. Civ. Code §1798.140(v) uyarınca).
8. Veri kümelerinin aggregate consumer information içerip içermediği (Cal. Civ. Code §1798.140(b) uyarınca).
9. Geliştirici tarafından temizleme, işleme veya diğer modifikasyon, amaçlanan amaçla.
10. Verinin toplandığı zaman dilimi, toplama devam ediyorsa bildirimle.
11. Veri kümelerinin geliştirme sırasında ilk kullanıldığı tarihler.
12. Sistemin sentetik veri üretimi kullanıp kullanmadığı veya sürekli kullanıp kullanmadığı.

Madde 12 (sentetik veri) Gebru vd. 2018 datasheet'lere göre yenidir. Madde 7 (kişisel bilgi) Privacy Rights Act (CPRA) yükümlülüklerini tetikler. Yasa güvenlik/bütünlük, uçak-operasyonu ve federal-yalnızca ulusal güvenlik sistemlerini muaf tutar (Bölüm 3111(b)).

### EU AI Act (Ders 24) ve TDM opt-out

EU Copyright Directive text-and-data-mining exception, rightholder opt-out etmedikçe kamuya açık içerik üzerinde eğitime izin verir. EU AI Act GPAI Code of Practice Copyright bölümü GPAI sağlayıcılarının makine-okunabilir opt-out sinyallerine (robots.txt, C2PA "No AI Training" iddiası, vb.) saygı duymasını gerektirir.

### 2025 DPA legitimate interest yakınsaması

Irish DPC (21 Mayıs 2025): Meta'nın first-party kamu EU/EEA yetişkin-kullanıcı içeriği üzerinde eğitim planı EDPB görüşünden sonra safeguard'larla kabul edildi. Cologne Higher Regional Court (23 Mayıs 2025) Meta'ya karşı ihtiyati tedbir kararını reddeder: opt-out yeterlidir. Hamburg DPA EU-genelinde tutarlılık için aciliyet prosedürünü düşürür. UK ICO (23 Eylül 2025) LinkedIn'in benzer safeguard'larla AI eğitimine devam etmesine ve devam eden izlemeye pozitif düzenleyici yanıt verdi — formel bir clearance değil.

Yakınsak ilke: legitimate interest kamuya açık first-party içerik üzerinde opt-out ile eğitimi gerekçelendirebilir. Consent gerekli değil.

### Brezilya ANPD (Haziran 2024)

Yetersiz bilgi transparency'si üzerine Meta'nın AI eğitimi için Brezilyalı kullanıcı verisini işlemesini askıya aldı. EU DPA'lardan farklı sonuç — ANPD legitimate-interest kabul edilebilirliği üzerinde transparency'yi önceliklendirdi.

### Geri dönüşsüzlük problemi

Cookie-consent gerçek zamanlı, geri döndürülebilir tracking için tasarlandı. Training data farklıdır: veri model ağırlıklarına girdiğinde cerrahi silme mümkün değildir. Sıfırdan yeniden eğitim tek tam remediation'dır ve yasaklayıcı şekilde pahalıdır.

Kısmi remediation'lar:
- **Unlearning.** Yaklaşık kaldırma; MIA ile ölçülür (Ders 22).
- **Influence function-tabanlı lokalizasyon.** Veri tarafından en çok etkilenen ağırlıkları tanımla; seçici olarak güncelle.
- **Fine-tune bastırma.** Modeli veriden türetilen çıktıları reddetmek için eğit.

Hiçbiri problemi tamamen çözmez. Uyum penceresi toplama zamanındadır.

### Data Provenance Initiative

dataprovenance.org. Longpre, Mahari, Lee vd. "Consent in Crisis" (Temmuz 2024): AI training data commons'ının büyük ölçekli audit'i. Bulgu: yayıncılar artan oranda robots.txt kısıtlamaları ekliyor. Açıkça-eğitilebilir-üzerinde-commons hızla daralıyor. 2023 -> 2024 üst eğitim kaynaklarının yaklaşık %25'inin bazı kısıtlama eklediğini gördü. İma: gelecekteki training-data kullanılabilirliği yeni acquisition paradigmalarına bağlıdır (lisanslama, sentetik üretim, teşvikli katılım).

### Bu Faz 18'de nereye uyuyor

Ders 26 model-seviyesi belgelendirmedir. Ders 27 veri-kümesi-seviyesi yönetişimidir. Birlikte transparency katmanını tanımlarlar. Ders 28 bu sorular üzerinde çalışan araştırma ekosistemini haritalar.

## Kullan

`code/main.py` bir oyuncak veri kümesi için California AB 2013-uyumlu 12-alan veri kümesi özet scaffold'u üretir. Alanları doldurabilir ve hangilerinin gizlilik veya telif hakkı follow-on yükümlülükleri tetiklediğini gözlemleyebilirsin.

## Yayınla

Bu ders `outputs/skill-provenance-check.md` üretir. Eğitimde kullanılan bir veri kümesi verildiğinde, AB 2013 12-alan kapsamını, opt-out altyapısı uyumunu, DPA hizalanmasını ve geri dönüşsüzlük-risk değerlendirmesini kontrol eder.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Bir oyuncak veri kümesi için 12-alan özet üret ve hangi alanların yetersiz-belirtildiğini tanımla.

2. EU Copyright Directive TDM opt-out makine-okunabilirdir. Opt-out sinyali için standart bir format öner ve onu robots.txt ve C2PA "No AI Training" ile karşılaştır.

3. Data Provenance Initiative'in "Consent in Crisis"ini (Temmuz 2024) oku. En hızlı kısıtlayan üç içerik kategorisini tarif et ve bir ekonomik sonuç savun.

4. 2025 DPA hizalanması kamu-içerik eğitimi için legitimate interest'i kabul eder. Legitimate interest'in yetersiz olacağı bir senaryo kur ve bir sağlayıcının onun yerine ihtiyaç duyacağı hukuki temeli tanımla.

5. AB 2013 alanlarıyla compose olan ve her veri kümesi için C2PA-imzalı bir provenance zinciri ile training-data-provenance manifest'i çiz. Bir teknik ve bir hukuki engel tanımla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| AB 2013 | "California yasası" | Generative AI training-data transparency; 12 zorunlu alan |
| TDM exception | "text-and-data-mining" | Opt-out ile EU Copyright Directive training-data exception |
| Legitimate interest | "EU temeli" | Kamu içerik üzerinde eğitimi gerekçelendirebilecek GDPR Madde 6 temeli |
| Opt-out sinyali | "makine-okunabilir no-train" | robots.txt, C2PA "No AI Training", TDM.Reservation |
| Geri dönüşsüzlük | "un-train yapılamaz" | Model ağırlıklarındaki veri cerrahi olarak kaldırılamaz |
| Unlearning | "yaklaşık kaldırma" | Modelin spesifik veriye bağımlılığını azaltmak için post-training müdahaleler |
| Consent in Crisis | "DPI audit'i" | Hızlanan robots.txt kısıtlamalarının Temmuz 2024 bulgusu |

## İleri Okuma

- [California AB 2013](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240AB2013) — Generative AI training-data transparency yasası
- [EU AI Act + GPAI Code of Practice (Ders 24)](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) — Copyright bölümü
- [Longpre, Mahari, Lee et al. — Consent in Crisis (dataprovenance.org, Temmuz 2024)](https://www.dataprovenance.org/consent-in-crisis-paper) — DPI audit'i
- [IAPP — EU Digital Omnibus GDPR amendments (2025)](https://iapp.org/news/a/eu-digital-omnibus-amendments-to-gdpr-to-facilitate-ai-training-miss-the-mark) — düzenleyici bağlam
