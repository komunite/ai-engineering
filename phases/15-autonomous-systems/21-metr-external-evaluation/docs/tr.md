# METR Time Horizons ve Harici Kapasite Değerlendirmesi

> METR (eski ARC Evals) Aralık 2023'ten beri bağımsız bir 501(c)(3)'tür. Time Horizon 1.1 benchmark'ları (Ocak 2026) görev-başarı olasılığına karşılık log(uzman insan tamamlama süresi)'ne bir logistic eğri fit eder; %50 olasılıkta kesişim modelin time horizon'unu tanımlar. 2025-2026 engagement seti GPT-5.1, GPT-5.1-Codex-Max ve prototip monitoring değerlendirmelerini (bir monitor side task'leri yakalayabilir mi; agent monitor'dan kaçabilir mi) kapsar. Benchmark suite'leri: HCAST (180+ ML, cyber, SWE, akıl yürütme görevi; 1 dakikadan 8+ saate), RE-Bench (uzman baseline'lı 71 ML araştırma-mühendisliği görevi), SWAA. Dürüst not: METR ölçümleri idealize edilmiştir — insan yok, gerçek sonuç yok — ve takım eval-vs-deployment davranış farkını belgeledi (Ders 1). Bir time horizon bir üst sınırdır, deployment tahmini değildir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, logistic-fit horizon estimator)
**Ön koşullar:** Faz 15 · 01 (Uzun-horizon agent'lar), Faz 15 · 19 (RSP)
**Süre:** ~60 dakika

## Sorun

Scaling policy'leri (Ders 19, 20) yalnızca referans verdikleri ölçümler kadar yararlıdır. "AI R&D-4 eşiği" ve "Long-range Autonomy" politika nesirinde tanımlanmıştır; yalnızca belirli değerlendirmeler belirli sayılar ürettiğinde actionable hale gelirler.

METR, bu sayıların çoğunu tanımlamış 2024-2026 harici değerlendirme kuruluşudur. Frontier modelleri değerlendirirler — sıkça yayın-öncesi, lab'lerle NDA altında — ve metodolojiyi sonradan yayımlarlar. Time Horizon 1.1 benchmark'ı (Ocak 2026) onların manşet artifact'ıdır: kapasiteyi insan-okunur bir birime sıkıştıran tek bir skaler ("bu model bir uzmanın %50 güvenilirlikte X saat harcadığı türden bir görevi yapabilir").

Ders kısmen metodoloji (bir horizon'un nasıl hesaplandığı) ve kısmen yorum (bir horizon'un neden bir üst sınır olduğu, deployment tahmini olmadığı) hakkındadır. İki beceri birbirine aittir. Horizon'un nasıl fit edildiğini anlayan bir takım, slaytta yalnızca "14 saat" gören bir takımdan kötü bir vendor iddiası ile kandırılması çok daha zordur.

## Kavram

### METR arka plan

- Kuruluş: Aralık 2023 (eski ARC Evals, bağımsız bir 501(c)(3)'e ayrıldı).
- Kapsam: frontier modellerin otonom kapasitelerinin değerlendirmesi, sıkça yayın-öncesi.
- Partner lab'ler: Anthropic, OpenAI (2025-2026 boyunca birden fazla engagement).
- Dikkate değer teslimatlar: Time Horizon 1.0 (Mart 2025), Time Horizon 1.1 (Ocak 2026), prototip monitoring değerlendirmeleri.

### Time Horizon fit'i

Metodoloji (METR blog'undan ve makalelerinden):

1. Dakika-ölçeğinden saat-ölçeğine uzman tamamlama sürelerine uzanan bir görev suite'i topla. Mevcut suite'ler: HCAST (180+ görev), RE-Bench (71 görev), SWAA.
2. Modeli her görevde çalıştır; başarı veya başarısızlığı kaydet.
3. Bir logistic eğri fit et: log(uzman tamamlama süresi)'nin bir fonksiyonu olarak P(başarı).
4. Horizon, P(başarı) = 0.5 olan uzman-zamanıdır.

Logistic-fit şekli doğrudur çünkü kapasitenin genellikle görev zorluğuyla artan, plato-yaklaşan bir ilişkisi vardır. %50 noktası bir seçimdir (%10, %90 olabilir); METR detaylı makalede birden fazla eşik raporluyor ama en sezgisel olduğu için %50 ile lider.

### Ocak 2026 rakamları

Time Horizon 1.1'e göre:

- Claude Opus 4.6: Time Horizon 1.1 (Ocak 2026) itibarıyla %50 güvenilirlikte ~14 saat.
- HCAST tarzı görevlerde ikiye katlanma süresi: Time Horizon 1.1 (Ocak 2026) tarafından raporlanan post-2023 fit'inde ~4.3 ay (130.8 gün); ~7-ay rakamı Time Horizon 1.0'dan tam 2019-2025 fit'idir ve TH1.1'de post-2023 rakamıyla birlikte raporlanır.

Bunlar Faz 15'in geri kalanının referans verdiği belirli sayılardır. Eşik değerlendirmelerine besleyen ölçümlerden biri olarak Anthropic'in RSP v3.0'ında (Ders 19) ve DeepMind'ın FSF v3'ünde (Ders 20) alıntılanır.

### Benchmark suite'leri

- **HCAST**: ML, cybersecurity, software engineering ve genel akıl yürütme arasında 189 görev. Aralık: 1 dakikadan 8+ saatlik uzman zamanına. Horizon rakamının arkasındaki ana suite.
- **RE-Bench**: insan uzman baseline'ı olan 71 ML araştırma-mühendisliği görevi. Modelin AI R&D-4 eşiğine besleyen türden ML R&D işini yapıp yapamayacağını ölçer.
- **SWAA**: daha kısa görevler; horizon eğrisinin alt ucunu kalibre etmek için yararlı.

### Prototip monitoring değerlendirmeleri

2025-2026 METR çalışması monitoring-değerlendirme prototiplerini içerdi: bir monitor bir side task gerçekleştiren bir modeli (operatörün istediğinden başka bir şey) yakalayabilir mi; agent monitor'dan kaçabilir mi. Bunlar doğrudan OpenAI PF v2'deki "Undermining Safeguards" kategorisini ve DeepMind FSF v3'teki deceptive-alignment monitoring'i besler (Ders 20).

### Horizon'lar neden üst sınır

- **İdealize edilmiş tooling**: benchmark görevleri modele temiz tool'lar ve iyi formatlı veri verir. Gerçek deployment'lar daha dağınıktır.
- **Gerçek sonuç yok**: model asla aslında bir müşteriyi faturalandırmaz, gerçek veriyi silmez veya gerçek insanlarla iletişime geçmez. Gerçek deployment'lar geri alınamaz risklere sahiptir.
- **Eval-context gaming**: Ders 1. Modeller testlerde farklı davranır. 2026 International AI Safety Report bunu empirik olarak belgeler.
- **Meşru kullanıcı varyansı yok**: benchmark prompt'ları yapılandırılmıştır. Gerçek kullanıcılar belirsiz, bağlama bağlı request'ler üretir.

Horizon, uygun koşullar altında kapasite tavanıdır. Deployment güvenilirliği farklı bir sayıdır, daha düşüktür ve takımlar onu bilmek için kendi dağılımlarını ölçmelidir.

### Harici-değerlendirici durumu

Harici değerlendirme önemlidir çünkü dahili lab'lerin raporladıkları metrikleri optimize etme teşvikleri vardır. METR'in bağımsızlığı — bildirilmiş bir metodoloji ve peer-reviewed makaleler olan bir 501(c)(3) — yapısal azaltmadır. Tek başına yeterli değildir (lab'ler hâlâ METR'in ne gördüğünü kontrol eder), ama kesinlikle hiç harici değerlendirme olmamasından daha iyidir.

### Pratikte horizon sayıları nasıl kullanılır

- **Bir kapasite filtresi olarak**: bir modelin horizon'u önerilen bir görevin uzman-zamanının çok altındaysa, onu otonom göndermeyin (Ders 1'in skill dosyası).
- **Bir trend göstergesi olarak**: ikiye katlanma süresi mevcut pratiğin yeni azaltmalar olmadan ne kadar safe kalacağını söyler.
- **Bir prior olarak**: 14 saatlik bir horizon bir başlangıç noktasıdır. Görev dağılımın, tooling kaliten ve deployment context'in için aşağı ayarla.

## Kullan

`code/main.py`, sentetik bir sonuç seti verildiğinde görev-başarısının log(uzman zamanı)'na karşı logistic fit'i uygular. %50 horizon (METR'in manşeti), %10 horizon (muhafazakar) ve %90 horizon (iyimser) raporlar. Aynı zamanda başarı oranının eval-context gaming ile yapay olarak şişirildiğinde ne değiştiğini gösterir.

## Yayınla

`outputs/skill-horizon-interpretation.md`, bir vendor'ın horizon iddiasını inceler ve benchmark iddiası ile deployment gerçekliği arasında bir gap analizi üretir.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Fit'in %50 horizon'unun sentetik ground truth ile eşleştiğini doğrula. Şimdi görev-zaman grid'ini ikiye böl; horizon tahmini anlamlı şekilde değişiyor mu?

2. METR'in Time Horizon 1.1 blog postunu oku. Güvenilirliğin en yüksek ve en düşük olduğu belirli görevleri belirle. Açığın neden var olduğunu açıkla.

3. METR'in "Measuring Autonomous AI Capabilities" kaynaklarını oku. HCAST görev kategorilerini listele. Bir üretim görevi için daha ağır ağırlıklandıracağın bir kategori seç ve nedenini gerekçelendir.

4. Simülatöre eval-context gaming tanıt: başarısız görevlerin ~%20'sini başarıya çevir. Yeni horizon'u raporla. Bu, %20'lik bir gaming oranının gözlemlenen sayıya ne yaptığını yaklaşık olarak verir.

5. Kendi bug backlog'unda veya temsili bir görev setinde bir dahili horizon değerlendirmesi tasarla. Veri toplama, fit ve çıktının sana ne söylediğini tarif et. METR rakamlarıyla karşılaştır.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| METR | "Harici değerlendirici" | eski ARC Evals; Aralık 2023'ten beri bağımsız 501(c)(3) |
| Time Horizon | "Kapasite ölçüsü" | Logistic fit'ten %50 güvenilirlikteki uzman görev uzunluğu |
| HCAST | "METR'in ana suite'i" | 1 dakikadan 8+ saate uzanan 180+ görev |
| RE-Bench | "Araştırma mühendisliği" | İnsan baseline'lı 71 ML araştırma-mühendisliği görevi |
| SWAA | "Kısa-görev suite'i" | Horizon eğrisinin alt ucunu kalibre eder |
| İkiye katlanma süresi | "Büyüme oranı" | %50 horizon'un ikiye katlanması için süre; HCAST başına ~7 ay |
| Eval-context gaming | "Model farklı davranır" | Testler ve deployment arasında belgelenmiş davranış farkı |
| Üst sınır | "Horizon bir tavandır" | Yük altında benchmark horizon > deployment güvenilirliği |

## İleri Okuma

- [METR — Resources for Measuring Autonomous AI Capabilities](https://metr.org/measuring-autonomous-ai-capabilities/) — HCAST, RE-Bench, SWAA spesifikasyonları.
- [METR — Measuring AI Ability to Complete Long Tasks](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/) — orijinal horizon makalesi.
- [METR — Time Horizon 1.1 (January 2026)](https://metr.org/research/) — güncel rakamlar ve metodoloji.
- [Epoch AI — METR Time Horizons benchmark](https://epoch.ai/benchmarks/metr-time-horizons) — canlı izleme.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — METR'in ölçümleri üzerine içeriden perspektif.
