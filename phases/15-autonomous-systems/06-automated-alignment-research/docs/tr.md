# Automated Alignment Research (Anthropic AAR)

> Anthropic, paralel Claude Opus 4.6 Autonomous Alignment Researcher takımlarını bağımsız sandbox'larda çalıştırdı; log'ları herhangi bir sandbox'ın dışında yaşayan paylaşımlı bir forum üzerinden koordine ettiler (böylece agent'lar kendi kayıtlarını silemez). Weak-to-strong eğitim probleminde, AAR'lar insan araştırmacılardan daha iyi performans gösterdi. Anthropic'in kendi özeti, reçete edilmiş workflow'ların AAR esnekliğini sıkça kısıtladığını ve performansı düşürdüğünü işaretliyor. Alignment araştırmasını otomatikleştirmek, RSP'nin tespit etmesi gereken tam misalignment risklerinin zaman çizelgesini sıkıştıran adımdır.

**Tür:** Öğrenim
**Diller:** Python (stdlib, paralel araştırma forumu simülatörü)
**Ön koşullar:** Faz 15 · 05 (AI Scientist v2), Faz 15 · 04 (DGM)
**Süre:** ~60 dakika

## Sorun

Alignment araştırması insan-araştırmacı süresinde pahalıdır. Scalable oversight, reward specification veya weak-to-strong eğitim gibi problemler iterasyon başına haftalar süren deneyler gerektirir. Frontier kapasiteleri ilerledikçe alignment iş yükü, nitelikli araştırmacı arzından daha hızlı büyür.

Automated Alignment Research (AAR), kapasitesi alignment'ı geride bırakan aynı frontier modellerin farkın kapanmasına katkıda bulunup bulunamayacağını sorar. Anthropic'in 2026 raporundaki AAR-yürüttüğü bir weak-to-strong-eğitim çalışması (alignment.anthropic.com/2026/automated-w2s-researcher/), bu sınıfta deployment edilmiş bir sistemden gelen ilk kamuya açık sonuçlardan biridir.

Sonuç gerçekten pozitif: AAR'lar, insan baseline'ından daha iyi bir araştırma problemi çözdü. Sonuç aynı zamanda tek bir sistemde bu fazın geliştirdiği her endişeyi yoğunlaştırır. Eğer alignment araştırması otomatikleştirilebiliyorsa, safeguard'ları tehlikeye atan kısımlar da otomatikleştirilebilir. RSP'nin AI R&D kapasitesi eşikleri bu döngü göz önünde tutularak yazılmıştır.

## Kavram

### Mimari (kamuya açıklandığı şekliyle)

- **Paralel agent'lar.** Birden fazla Claude Opus 4.6 instance'ı AAR olarak çalışır, her biri bağımsız bir sandbox'ta. Sandbox'lar filesystem, network ve process yüzeyini sınırlar.
- **Paylaşımlı forum.** Bulgular, storage backend'i her sandbox'ın dışında oturan paylaşımlı bir foruma yayımlanır. Agent'lar forumu okuyabilir; agent'lar kendi sandbox'larından forum kayıtlarını silemez veya edit edemez.
- **Görev tahsisi.** İnsan tasarımlı bir görev kuyruğu AAR'lara araştırma problemlerini atar. AAR'lar dekompozisyonlar önerir, deneyler çalıştırır, bulguları yazar.
- **Weak-to-strong eğitim odağı.** Yayımlanmış çalışma weak-to-strong eğitimini ele aldı — daha güçlü bir öğrenci modeli eğitmek için daha zayıf bir supervisor modeli kullanmak. AAR'lar bu görevde insan araştırmacılardan daha iyi performans gösterdi.

### Sandbox-dışı log neden önemli

Log-bütünlük özelliği, kontrollü bir deney ile potansiyel olarak tehlikeye atılmış bir deney arasındaki farktır. AAR'lar kendi log'larını edit edebilseydi, başarısız veya şüpheli deneyleri örtbas edebilirlerdi. Anthropic bunu doğrudan işaretliyor: özellik araştırma çıktısına güvenmek için gerekli bir koşuldur ve doğrulanması non-trivial'dir.

Altyapı terimleriyle benzeri, harici depolamaya write-through'lu append-only log'lardır (örn. S3 object-lock, immutable Datadog log'ları). Agent'ın geçmiş kayıtları modifiye etmek için credential'ı yoktur. Bu, 2026 kurumsal güvenlik takımlarının ransomware-dirençli audit izleri yapmak için kullandığı aynı desendir.

### Reçete-edilmiş-workflow trade-off'u

Anthropic'in raporu, reçete edilmiş workflow'ların AAR esnekliğini sıkça kısıtladığını ve performansı düşürdüğünü not eder. Diğer bir deyişle: insan tasarımcı araştırma planını adım-adım yazarsa, AAR'lar yüksek-seviye hedefler ve dekompoze etme özgürlüğü verildiğindekinden daha kötü yapar. Bu agentic araştırmadaki sonuçlarla (LangGraph, Microsoft'un Agent Framework'ü) tutarlıdır — fazla-spesifik iskeleler yetenekli agent'lara zarar verir.

Safety çıkarımı inceliklidir. AAR performansını artıran esneklik, aynı zamanda yetkisiz dekompozisyona, yeni tool kullanımına ve hedef-drift'e izin veren esnekliktir. Trade-off bir tasarım-uzayı kararıdır: ne kadar esneklik, agent'a hedefleri dağılım-dışı genelleştirme alanı vermeden insanları yenmek için yeterli kapasite satın alıyor?

### Sıkıştırma riski

RSP v3.0 (Ders 19) bir AI R&D kapasite eşiği tanıtır: AI R&D pipeline'ını insan + AI araçlarına karşı rekabetçi maliyette tam otomatikleştirme yeteneği. DeepMind'ın FSF v3'ü benzer bir ML R&D otonomi seviyesi içerir. Her iki framework de bu eşiği yükseltilmiş kontroller için tetikleyici olarak ele alır.

AAR eşiğin bir adım gerisindedir: pipeline'ın bir kısmını (belirli, iyi-kapsamlı görevlerde alignment araştırması) otomatikleştirir ama uçtan uca kapasite gelişim döngüsünü değil. Zaman çizelgesi sorusu farkın ne kadar hızlı kapandığıdır.

Sıkıştırılmış zaman çizelgeleri bileşik-failure endişesidir. Alignment araştırması ve kapasite araştırması benzer hızlarda bileşik kazanırsa, misalignment risk yüzeyi en azından kapasite kadar hızlı büyür. Kapasite daha hızlı bileşik kazanırsa (tarihsel trend), fark genişler. Bu, AAR'ın koşullu bir iyi olduğu argümanıdır: her ek alignment sonucu, ancak ve ancak araştırma süreci güvenilirse farkı azaltır.

### AAR'ın yerini almadığı şey

İnsan araştırmacılar görev kuyruğunu kurar, sonuçları inceler ve anayasal otoriteyi elinde tutar. AAR'lar pipeline'ın ortasını hızlandırır, uçları değil. Anthropic'in yayımlanmış çıktıları hem AAR katkılarını hem de neyi yayımlayacak, neyi geri çekecek ve neyi rafine edeceğine dair insan-araştırmacı yargısını içerir.

Bu, Ders 15'teki propose-then-commit deseninin araştırmanın kendisine uygulanmasıyla eşleşir: AAR'lar önerir; insanlar commit eder.

## Kullan

`code/main.py`, çoklu-AAR'lı bir araştırma forumunu simüle eder. Üç bağımsız "araştırma agent'ı" paralel çalışır, isteğe bağlı tamper denemeleriyle append-only bir foruma bulgu gönderir.

İzle:

- Sandbox-dışı logging'in log-tamper denemelerini nasıl yakaladığını.
- Serbest dekompozisyonlu görev tahsisinin daha zor problemlerde sabit workflow'lardan daha iyi performans gösterdiğini.
- Log tamper-evident değilse, tek bir tehlikeye atılmış AAR'ın forumun sinyalini nasıl kontamine edebileceğini.

## Yayınla

`outputs/skill-aar-deployment-review.md`, otomatik-alignment-araştırma pipeline'ının deployment-öncesi incelemesidir.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. "fixed-workflow" vs "free-decomposition" ayarlarını karşılaştır. Serbest dekompozisyon her zaman kazanır mı, yoksa sabit workflow'un rekabetçi olduğu problem sınıfları var mı?

2. Simülatörü bir agent log tampering denesin diye modifiye et. Append-only log'un onu tespit ettiğini doğrula. Tespit imzasının log'da tam olarak nasıl göründüğünü açıklayan bir paragraf yaz.

3. Anthropic'in weak-to-strong AAR raporunu oku. AAR'ların insan araştırmacıları yendiği belirli alt-görevi belirle. Onu otomasyona uygun kılan neydi?

4. AAR esnekliğini (daha iyi sonuçlar) reçete-edilmiş-workflow kısıtlamalarına (daha kolay audit) karşı dengeleyen bir görev-kuyruğu tahsis politikası tasarla. İkisini nasıl A/B test edeceğini tarif et.

5. RSP v3.0'ın AI R&D-4 eşiğini oku. Bir paragrafta, AAR'ın şu an geçmediği ama geçeceğini düşündüğün şeyi tarif et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| AAR | "Automated Alignment Researcher" | Alignment problemlerinde otonom olarak işletilen Claude Opus 4.6 instance'ı |
| Weak-to-strong eğitim | "Daha zayıf bir supervisor ile daha güçlü bir model eğitmek" | AAR'ların insanları yendiği klasik scalable-oversight benchmark'ı |
| Paylaşımlı forum | "Agent'ların bulgu yayımladığı yer" | Append-only, sandbox-dışı depolama |
| Sandbox-dışı log | "Agent kendi kaydını edit edemez" | Harici depolamaya tamper-evident write-through |
| Reçete edilmiş workflow | "İnsan tasarımcıdan adım-adım plan" | AAR'ı kısıtlar; sıkça serbest dekompozisyona göre performansı düşürür |
| Serbest dekompozisyon | "Agent görevi nasıl böleceğine karar verir" | Daha yetenekli, audit edilmesi daha zor |
| AI R&D eşiği | "RSP/FSF kapasite seviyesi" | R&D pipeline'ının rekabetçi maliyette tam otomasyonu |
| Sıkıştırılmış zaman çizelgesi | "Alignment vs kapasite yarışı" | Kapasite alignment'tan hızlı bileşik kazanırsa, misalignment riski büyür |

## İleri Okuma

- [Anthropic — Automated Weak-to-Strong Researcher](https://alignment.anthropic.com/2026/automated-w2s-researcher/) — birincil kaynak.
- [Anthropic Responsible Scaling Policy v3.0](https://anthropic.com/responsible-scaling-policy/rsp-v3-0) — AI R&D eşiği çerçevesi.
- [Anthropic — Measuring AI agent autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) — daha geniş agent-otonomi çerçevesi.
- [DeepMind Frontier Safety Framework v3](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — RSP'ye paralel ML R&D otonomi seviyeleri.
- [Burns et al. (2023). Weak-to-Strong Generalization (OpenAI)](https://openai.com/index/weak-to-strong-generalization/) — AAR'ların saldırdığı altta yatan problem.
