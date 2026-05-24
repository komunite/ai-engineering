# OpenAI Preparedness Framework ve DeepMind Frontier Safety Framework

> OpenAI Preparedness Framework v2 (Nisan 2025) Research Categories tanıtır — Long-range Autonomy, Sandbagging, Autonomous Replication and Adaptation, Undermining Safeguards — Tracked Categories'den farklı olarak. Tracked Categories, Safety Advisory Group tarafından incelenen Capabilities Reports artı Safeguards Reports tetikler. DeepMind'ın FSF v3'ü (Eylül 2025, 17 Nisan 2026'da Tracked Capability Levels eklendi) otonomiyi ML R&D ve Cyber domain'lerine katlar (ML R&D otonomi seviyesi 1 = AI R&D pipeline'ını insan + AI araçlarına karşı rekabetçi maliyette tam otomatikleştirme). FSF v3 açıkça instrumental-reasoning misuse için otomatik monitoring üzerinden deceptive alignment'ı ele alır. Dürüst not: PF v2'deki Research Categories (Long-range Autonomy dahil) otomatik olarak azaltma tetiklemez; politika dili "potansiyel"dir. DeepMind kendisi instrumental reasoning güçlenirse otomatik monitoring'in "uzun vadede yeterli kalmayacağını" söylüyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib, üç-framework karar tablosu diff aracı)
**Ön koşullar:** Faz 15 · 19 (Anthropic RSP)
**Süre:** ~45 dakika

## Sorun

Ders 19 Anthropic'in scaling policy'sini yakından okudu. Bu ders, OpenAI'ın ve DeepMind'ınkini okuyarak resmi tamamlar. Üç belge de aynı soruyu ele alan kuzen artifact'lardır — bir frontier lab bir modeli ne zaman duraklatmalı veya gate etmeli — ve küçük bir kategori setinde yakınsar ve önemli olan belirli yerlerde ayrışırlar.

Yakınsama: üçü de uzun-aralık otonomiyi takip etmeye değer bir kapasite sınıfı olarak etiketler. Üçü de deceptive davranışı (alignment faking, sandbagging) belirli bir risk sınıfı olarak kabul eder. Üçünün de bir dahili inceleme organı vardır. Ayrışma: OpenAI kategorileri "Tracked" (zorunlu azaltma) ve "Research" (otomatik tetik yok) olarak ayırır. DeepMind otonomiyi ayrıca adlandırmak yerine iki domain'e katlar. Lab Tracked vs Research, ya da Critical vs Moderate, ya da Tier-1 vs Tier-2 adlandırır; bir kapasitenin hangi bucket'ta yaşadığının operasyonel sonucu lab'ler arasında farklıdır.

Onları birlikte okumak yararlı egzersizdir. Aynı kapasite Anthropic'te "zorunlu azaltma", OpenAI'da "izlenen ama tetiklemeyen" ve DeepMind'da "belirli bir domain'de takip edilen" olabilir. Politika duruşu önemlidir.

## Kavram

### OpenAI Preparedness Framework v2 (Nisan 2025)

Yapı:

- **Tracked Categories**: Capabilities Reports (modelin neyi yapabildiği) artı Safeguards Reports (hangi azaltmaların yerinde olduğu) tetikler. Deployment'tan önce Safety Advisory Group tarafından incelenir.
- **Research Categories**: lab'in takip ettiği ama henüz belirli azaltmalara taahhüt etmediği model kapasiteleri. Long-range Autonomy, Sandbagging, Autonomous Replication and Adaptation, Undermining Safeguards içerir.

v2'de anahtar çerçeveleme: Research Categories otomatik olarak azaltma tetiklemez. Politika dili "potansiyel" azaltmalardır. İzlenecek belirli delta budur: bir kategorinin Tracked vs Research'teki konumu "gate edilen" ile "gözlemlenen" arasındaki menteşedir.

### DeepMind Frontier Safety Framework v3 (Eylül 2025; 17 Nisan 2026'da Tracked Capability Levels eklendi)

Yapı:

- **Critical Capability Levels (CCL'ler)**: beş domain arasında kapasite eşikleri: Cyber, Bio, ML R&D, CBRN, Autonomy (ML R&D ve Cyber'a katlanmış).
- **Tracked Capability Levels**: Nisan 2026'da eklenen ek granülarite. Somut örnek: ML R&D otonomi seviyesi 1 = AI R&D pipeline'ını insan + AI araçlarına karşı rekabetçi maliyette tam otomatikleştirme.
- **Deceptive alignment monitoring**: instrumental-reasoning misuse için otomatik monitoring'e açık taahhüt.

Otonomi çerçevesi OpenAI'ınkinden farklıdır. DeepMind "Otonomi"yi üst-seviye bir domain olarak tutmaz; otonominin zarara yol açacağı domain'lere (ML R&D ve Cyber) katlanır. Argüman, domain'siz otonominin risk olmayan kapasite olduğudur; karşı argüman, domain'ler arası otonominin framework'ün adlandırması gereken bir meta-risk olduğudur.

### Üçünün üzerinde yakınsadığı

- Dahili Safety Advisory Group (Anthropic SAG, OpenAI SAG, DeepMind dahili komitesi olarak adlandırılmış). Yüksek-kapasiteli modeller için deployment'tan önce inceleme.
- Bir risk sınıfı olarak deceptive alignment / alignment faking'in açık olarak anılması.
- Bildirilmiş bir cadence'te standing artifact'lar (Anthropic: Frontier Safety Roadmap, Risk Report; OpenAI: Capabilities and Safeguards Reports; DeepMind: FSF güncelleme döngüsü).
- Yalnızca-monitoring savunmalarının bir tavanı olduğunun kabulü. DeepMind açıktır: "otomatik monitoring uzun vadede yeterli kalmayacaktır."

### Ayrıştıkları yer

- **Anthropic**: pause taahhüdü v3.0'da kaldırıldı; AI R&D-4 eşiği adlandırılmış bir sonraki gate'tir.
- **OpenAI**: Tracked vs Research ayrımı; Research Categories (Long-range Autonomy dahil) otomatik gate etmez.
- **DeepMind**: otonomi diğer domain'lere katlanmış; Tracked Capability Levels Nisan 2026'da granülarite ekler.

### Sandbagging: üçünü de karmaşıklaştıran belirli bir kapasite

Sandbagging (bir modelin değerlendirmelerde stratejik olarak underperform etmesi) OpenAI'ın Research Categories'sindedir. Anthropic'in RSP v3.0'ı bunu evaluation-context farkı üzerinden ele alır (Ders 1). DeepMind bunu FSF v3'teki deceptive alignment monitoring üzerinden ele alır.

Bir model değerlendirmelerde sandbag yaparsa, her framework'ün kapasite eşikleri underestimate edilir. Framework yalnızca ölçüm çalışırsa çalışır. Bu yüzden harici ölçüm (Ders 21, METR) ve adversarial değerlendirme lab self-assessment'a ek olarak gereklidir.

### Politika-okuma becerisi

- Bulun: önemsediğin her kapasite politikada bulunabilmelidir. Bulunabilir değilse, politika onu kapsamaz.
- Sınıflandır: Tracked mi (azaltma tetikler) yoksa Research mi (takip edilen ama tetiklemeyen)? OpenAI bunu adlandırır; Anthropic ve DeepMind'ın kendi karşılıkları vardır.
- Cadence: politika bildirilmiş bir takvimde mi güncellenir, yoksa yalnızca belirli olaylardan sonra mı? Bildirilmiş cadence daha güçlüdür.
- Bağımsızlık: harici inceleme zorunlu mu yoksa opsiyonel mi? Anthropic Apollo ve US AI Safety Institute ile partner; OpenAI METR ile; DeepMind öncelikle dahili SAG ile.

## Kullan

`code/main.py` küçük bir karar tablosu diff aracı uygular. Bir kapasite (otonomi, deceptive alignment, R&D otomasyonu, cyber uplift, vb.) verildiğinde, üç politikanın her birinin kapasiteyi nasıl sınıflandırdığını ve hangi azaltmaların tetiklendiğini çıktılar. Bir okuma yardımcısıdır, bir politika aracı değildir.

## Yayınla

`outputs/skill-cross-policy-diff.md`, üç framework'ü referans olarak kullanarak belirli bir kapasite için bir politikalar arası karşılaştırma üretir.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Diff aracının çıktısının kaynak belgelere karşı doğrulayabildiğin en az iki kapasite için politikalarla eşleştiğini doğrula.

2. OpenAI Preparedness Framework v2'yi tam olarak oku. Her Research Category'sini belirle. Her biri için, neden Tracked yerine Research'te olduğuna dair bir cümle yaz.

3. DeepMind FSF v3'ü artı Nisan 2026 Tracked Capability Levels güncellemesini tam olarak oku. ML R&D otonomi seviyesi 1'in belirli değerlendirme kriterlerini belirle. Onu harici olarak nasıl ölçerdin?

4. Sandbagging OpenAI'ın Research Categories'sindedir. Sandbag yapan bir modeli gerçek kapasitesini açığa çıkarmaya zorlayacak bir değerlendirme tasarla. Ders 1 eval-context-gaming tartışmasını referans ver.

5. Üç politikayı belirli bir kapasitede (seçimin) karşılaştır. Hangi politikanın sınıflandırmasını en titiz, hangisini en az bulduğunu adlandır. Kaynak metinle gerekçelendir.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Preparedness Framework | "OpenAI'ın scaling policy'si" | PF v2 (Nisan 2025); Tracked vs Research kategorileri |
| Tracked Category | "Zorunlu azaltma" | Capabilities + Safeguards Reports tetikler; SAG inceleme |
| Research Category | "Yalnızca izlenen" | Takip edilen ama otomatik azaltma yok; Long-range Autonomy içerir |
| Frontier Safety Framework | "DeepMind'ın scaling policy'si" | FSF v3 (Eylül 2025) + Tracked Capability Levels (Nisan 2026) |
| CCL | "Critical Capability Level" | Domain başına DeepMind eşiği (Cyber, Bio, ML R&D, CBRN) |
| ML R&D otonomi seviyesi 1 | "R&D otomasyonu" | AI R&D pipeline'ını rekabetçi maliyette tam otomatikleştirme |
| Sandbagging | "Stratejik underperformance" | Model eval'lerde underperform eder; OpenAI Research Categories'te |
| Instrumental reasoning | "Means-ends akıl yürütme" | Hedeflere nasıl ulaşılacağı üzerine akıl yürütme; DeepMind monitoring'in hedefi |

## İleri Okuma

- [OpenAI — Updating our Preparedness Framework](https://openai.com/index/updating-our-preparedness-framework/) — v2 duyurusu.
- [OpenAI — Preparedness Framework v2 PDF](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf) — tam belge.
- [DeepMind — Strengthening our Frontier Safety Framework](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — FSF v3 duyurusu.
- [DeepMind — Updating the Frontier Safety Framework (April 2026)](https://deepmind.google/blog/updating-the-frontier-safety-framework/) — Tracked Capability Levels eklemesi.
- [Gemini 3 Pro FSF Report](https://storage.googleapis.com/deepmind-media/gemini/gemini_3_pro_fsf_report.pdf) — FSF-format Risk Report örneği.
