# Anthropic Responsible Scaling Policy v3.0

> RSP v3.0, 2023 politikasının yerini alarak 24 Şubat 2026'da yürürlüğe girdi. İki-katmanlı azaltma: Anthropic'in tek taraflı yapacağı şey ile endüstri çapında bir öneri olarak çerçevelenen şey (RAND SL-4 güvenlik standartları dahil). Frontier Safety Roadmap'lerini ve Risk Report'larını tek-seferlik teslimatlar yerine standing belgeler olarak ekler. 2023 pause taahhüdünü bırakır. AI R&D-4 eşiğini tanıtır: bir kez geçildiğinde, Anthropic misalignment risklerini ve azaltmaları tanımlayan bir affirmative case yayımlamak zorundadır. Claude Opus 4.6 bunu geçmez. Anthropic v3.0 duyurusunda "bunu güvenle ekarte etmenin zorlaştığını" belirtir. SaferAI 2023 RSP'sini 2.2 olarak derecelendirdi; v3.0'ı 1.9'a düşürerek Anthropic'i OpenAI ve DeepMind ile birlikte "zayıf" RSP kategorisine koydu. Kalitatif eşikler 2023 niceliksel taahhütlerin yerini aldı; pause clause'unu kaldırmak en keskin regresyondur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, RSP eşik karar motoru)
**Ön koşullar:** Faz 15 · 06 (AAR), Faz 15 · 07 (RSI)
**Süre:** ~45 dakika

## Sorun

Frontier lab'ler kısmen teknik belgeler, kısmen governance belgeleri ve kısmen regülatörlere sinyaller olan scaling policy'leri yayımlar. RSP v3.0 mevcut Anthropic belgesidir. Onu yakından okumak önemlidir, ona uyumun bağlayıcı olduğu için değil (değil), çerçevenin bir lab'in catastrophic risk'i nasıl tasarladığını ve trade-off'ları halka nasıl ilettiğini şekillendirdiği için.

v3.0 vs v2.0 diff'i yararlı birimdir. Eklenen ne: Frontier Safety Roadmaps, Risk Reports, AI R&D-4 eşiği. Kaldırılan ne: 2023 pause taahhüdü. Yeniden çerçevelenen ne: Anthropic-tek taraflı ve endüstri-önerisi arasında ayrılmış iki-katmanlı bir azaltma programı. Harici inceleme — SaferAI — skoru 2.2'den (v2) 1.9'a (v3.0) düşürdü. Bu, bir scaling policy'nin daha cilalı görünürken nasıl daha az titiz olabileceğidir.

## Kavram

### İki-katmanlı azaltma programı

- **Anthropic tek taraflı aksiyonlar**: Anthropic diğer lab'lerin ne yaptığına bakılmaksızın yapacağı şey. Bir eşiğin üstünde eğitim durur, belirli güvenlik önlemleri, belirli deployment gate'leri.
- **Endüstri-çapında öneriler**: Anthropic'in endüstrinin toplu olarak yapması gerektiğini düşündüğü şey. RAND SL-4 güvenlik standartlarını içerir. Bunlar Anthropic tarafındaki taahhütler değildir; politika savunuculuğudur.

İki-katmanlı yapı v2'de yoktu. Bu, bir okuyucunun her taahhüdün hangi sütunda yaşadığına bakması gerektiği anlamına gelir. "Endüstri çapında öneri" sütunundaki bir güvenlik önlemi Anthropic'in vaadi değil; Anthropic'in umududur.

### AI R&D-4 eşiği

Bu, RSP v3.0'ın önemli bir sonraki eşik olarak adlandırdığı kapasite seviyesidir. Özellikle: AI araştırmasının önemli bir kısmını rekabetçi maliyette otomatikleştirebilen bir model. Anthropic bir modelin onu geçtiğine inandığında, devam eden scaling'den önce misalignment risklerini ve azaltmaları tanımlayan bir affirmative case yayımlamak zorundadır.

Claude Opus 4.6 v3.0 duyurusuna göre bunu geçmez. Belge ekler: "bunu güvenle ekarte etmek zorlaşıyor." Bu ifade önemlidir; eşiğin spekülatif bir limit değil, canlı bir endişe olacak kadar yakın olduğunu kabul eder.

Ders 6 (Automated Alignment Research) ve Ders 7 (Recursive Self-Improvement) doğrudan bu eşiğe besler. Araştırma-kalite çıtalarını geçen automated alignment researcher'lar AI R&D-4 eşiğinin yaklaştığına dair kanıttır.

### Frontier Safety Roadmaps ve Risk Reports

v3.0 iki artifact tipini standing belgelere yükseltir:

- **Frontier Safety Roadmap**: planlanan safety çalışmasını, kapasite beklentilerini ve azaltma araştırmasını tarif eden ileriye dönük belge.
- **Risk Report**: yayından sonra belirli modeller üzerinde gözlemlenen kapasite ve artık riski tarif eden retrospektif belge.

Her ikisi de halka açıktır. Her ikisi de bildirilmiş bir cadence'te güncellenir. Yarar: okuyucu Anthropic'in bir Roadmap'te yapacağını söylediği şeyin bir Risk Report'ta raporladığıyla nasıl karşılaştırıldığını takip edebilir.

### Pause clause'unu kaldırma

2023 RSP açık bir pause taahhüdü içeriyordu: bir model belirli kapasite eşiklerini geçerse, azaltmalar yerinde olana kadar eğitim duraklardı. v3.0 açık pause'u daha yumuşak bir formülasyonla değiştirir (bir affirmative case yayımla, azaltmalar yeterliyse devam et). SaferAI ve diğer analistler bunu yeni belgedeki en güçlü regresyon olarak doğrudan dile getirdi.

Değişiklik için politika argümanı: 2023'teki niceliksel eşikler 2026 dönemi kapasite benchmark'ları tarafından ulaşılamaz oldu çünkü benchmark'lar kendisi yeniden ölçeklendi. Karşı argüman: bir scaling policy'deki pause clause'u bir taahhüt aracıdır; onu kaldırmak politikanın güvenilirliğini kaldırır.

### SaferAI'ın derecesi düşürmesi

SaferAI RSP-stili belgeleri derecelendiren bağımsız bir kuruluştur. Halka açık derecelendirmeleri: 2023 Anthropic RSP 2.2 puan aldı (4.0'ın en iyi mevcut RSP ve 1.0'ın nominal olduğu bir ölçekte). v3.0 1.9 puan aldı. Bu Anthropic'i "ılımlı"dan "zayıf"a taşıdı, OpenAI ve DeepMind'a zayıf kategoride katılarak.

SaferAI'ya göre derece düşürme faktörleri:
- Niceliksel eşiklerin yerini kalitatif olanlar aldı.
- Pause taahhüdü kaldırıldı.
- AI R&D-4 eşik azaltmaları belirli önlemler yerine "affirmative case" olarak tarif edilir.
- İnceleme mekanizmaları sınırlı bağımsız oversight ile Anthropic'in Safety Advisory Group'una bağlıdır.

### Bu ders ne değil

Bu bir uyum dersi değildir. RSP v3.0 bir regülasyon değildir; hiçbir şey Anthropic'i onu takip etmeye zorlamaz. Ders, belgeyi hak ettiği spesifiklik ve şüphecilikle okumakta. Scaling policy'ler frontier lab'lerin catastrophic-risk duruşu hakkında yaydığı birincil halka açık sinyaldir. Onları iyi okumak, işi frontier kapasitelerine bağlı olan herkes için pratik bir beceridir.

## Kullan

`code/main.py` RSP eşik-değerlendirme şeklini yansıtan küçük bir karar motoru uygular: bir aday model ve bir kapasite ölçümleri seti verildiğinde, AI R&D-4 eşiğinin geçilip geçilmediğini, gerekli affirmative-case bölümlerini ve deployment'ın devam edip edemeyeceğini döner. Kasıtlı olarak basittir; amaç belgenin mantığını açık hale getirmektir.

## Yayınla

`outputs/skill-scaling-policy-review.md`, v3.0 referansına karşı bir scaling policy'yi (Anthropic, OpenAI, DeepMind veya dahili) inceler: iki-katmanlı yapı, eşikler, pause taahhütleri, bağımsız inceleme.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Farklı kapasite seviyelerinde üç sentetik model besle. Eşik değerlendiricinin beklenen şekilde davrandığını ve doğru affirmative-case template'i ürettiğini doğrula.

2. RSP v3.0'ı tam olarak oku (32 sayfa). "Endüstri çapında öneri" katmanında yaşayan her taahhüdü belirle. Bu taahhütlerin hangisi v2'de "Anthropic tek taraflı" olurdu?

3. SaferAI'ın RSP derecelendirme metodolojisini oku. Rubric'lerini belgeye uygulayarak v3.0 için 1.9 skorlarını yeniden üret. Derece düşürmeyi en çok hangi rubric satırı sürdü?

4. 2023 pause taahhüdü kaldırıldı. 2026 benchmark-yeniden ölçekleme problemini kabul ederken politikanın güvenilirliğini koruyan bir yedek taahhüt öner.

5. RSP v3.0'ı OpenAI Preparedness Framework v2 ile (Ders 20) karşılaştır. v3.0'ın daha güçlü olduğu bir alan seç. Preparedness Framework'ün daha güçlü olduğu bir alan seç.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| RSP | "Anthropic'in scaling policy'si" | Responsible Scaling Policy; v3.0, 24 Şubat 2026'da yürürlükte |
| AI R&D-4 | "Araştırma-otomasyon eşiği" | Önemli AI araştırmasını rekabetçi maliyette otomatikleştirme kapasitesi |
| Affirmative case | "Safety gerekçesi" | Risklerin tanımlandığı ve azaltmaların yeterli olduğu yayımlanmış argüman |
| Frontier Safety Roadmap | "İleriye dönük plan" | Planlanan safety çalışması ve beklenen kapasiteler üzerine standing belge |
| Risk Report | "Bir model üzerine retrospektif" | Yayın sonrası gözlemlenen kapasite ve artık risk üzerine standing belge |
| İki-katmanlı azaltma | "Tek taraflı vs endüstri" | Anthropic taahhütleri vs endüstri önerileri, ayrılmış |
| Pause taahhüdü | "2023 clause" | Eğitimi duraklatma açık vaadi; v3.0'da kaldırıldı |
| SaferAI derecesi | "Bağımsız RSP notu" | Üçüncü-taraf rubric'i; v3.0 1.9 puan aldı (v2 2.2 idi) |

## İleri Okuma

- [Anthropic — Responsible Scaling Policy v3.0](https://anthropic.com/responsible-scaling-policy/rsp-v3-0) — tam 32-sayfalık politika.
- [Anthropic — RSP v3.0 announcement](https://www.anthropic.com/news/responsible-scaling-policy-v3) — v2'den değişikliklerin özeti.
- [Anthropic — Frontier Safety Roadmap](https://www.anthropic.com/research/frontier-safety) — RSP v3.0'tan link verilen standing belge.
- [Anthropic — Risk Report: Claude Opus 4.6](https://www.anthropic.com/research/risk-report-claude-opus-4-6) — mevcut frontier model üzerine retrospektif.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — AI R&D-4'ü ölçülen otonomiye bağlar.
