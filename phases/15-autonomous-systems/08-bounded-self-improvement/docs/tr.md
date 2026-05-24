# Bounded Self-Improvement Tasarımları

> Araştırma, bir self-improvement döngüsünü sınırlamak için dört primitif üzerinde birleşti. Her edit'te tutulması gereken formal invariant'lar. Modifiye edilemeyen alignment anchor'ları. Sadece performans değil her boyutun (safety, adillik, dayanıklılık) tutulması gereken çok-hedefli kısıtlamalar. Tarihsel metrikler kapasite kaybı işaret ettiğinde döngüyü duraklatan regresyon tespiti. Hiçbiri safety kanıtı değildir — bilgi-teorik sonuçlar (Kolmogorov karmaşıklığı, Lob teoremi) herhangi bir sistemin kendi haleflerini hakkında neyi kanıtlayabileceğini sınırlar. Bunlar sessiz failure'ın maliyetini yükselten azaltmalardır.

**Tür:** Öğrenim
**Diller:** Python (stdlib, invariant kontrollü bounded döngü)
**Ön koşullar:** Faz 15 · 07 (RSI), Faz 15 · 04 (DGM)
**Süre:** ~60 dakika

## Sorun

Ders 7'nin yarış simülatörü küçük oran farklarının büyük farklara bileşik kazandığını gösterdi. Ders 4'ün DGM vaka çalışması döngülerin kendi evaluator'larını aktif olarak game edebileceğini gösterdi. Her iki sonuç da aynı mühendislik sorusunu işaret ediyor: bir self-improvement döngüsüne, kısıtlamaların döngünün kendisi tarafından sessizce zayıflatılamayacağı hangi kısıtlamaları koyabilirsin?

ICLR 2026 RSI Workshop özeti (openreview.net/pdf?id=OsPQ6zTQXV) böyle dört primitif belirler. Anthropic'in RSP v3.0'ı (Ders 19) ve DeepMind'ın FSF v3'ü (Ders 20) her ikisi de bunlara kapasite eşiklerinde referans verir. Meta HyperAgents çalışması ve SAHOO (Mart 2026) gibi topluluk framework'leri üretimde alt kümeleri uygular.

Dürüst çerçeve: bunlar azaltmalardır. Bilgi-teorik sonuçlar herhangi bir sistemin kendi halefi hakkında neyi kanıtlayabileceğini sınırlar ve hiçbir mevcut tasarım problemi formal olarak kapatmaz. İyi-sınırlanmış bir döngü sınırsız olandan daha safe'tir, mutlak terimlerle safe değil.

## Kavram

### Primitif 1: formal invariant'lar

Bir invariant her self-modification'dan önce ve sonra tutulması gereken bir özelliktir. Örnekler:

- Çıktı dağılımı sabit bir constitution header'ına koşullanmıştır (Ders 17).
- Hiçbir tool çağrısı yetkisiz bir endpoint'e gitmez.
- Memory write'ları logged, imzalı bir yoldan geçer.
- Evaluator'ın modül hash'i onaylanmış versiyona eşleşir.

Invariant'lar döngünün edit edemediği harici kod tarafından kontrol edilir. Önerilen bir modifikasyon bir invariant'ı ihlal ederse, reddedilir. Bu DGM tarzı evaluator-tampering mode'unu yakalar (Ders 4).

Zor kısım, safety için gerekli ve makul sürede hesaplanabilir invariant'ları seçmektir. Aşırı-spesifik ilerlemeyi durdurur; eksik-spesifik döngünün önemli özelliklerin yanından geçmesine izin verir.

### Primitif 2: alignment anchor'ları

Bir alignment anchor, döngünün edit yüzeyinin dışına sabitlenmiş döngünün çekirdek hedefinin değiştirilemez bir temsilidir. Örnekler:

- Her çağrıda salt-okunur bir konumdan yüklenen bir anayasal metin (Ders 17).
- Bağımsız erişim kontrolü olan ayrı bir repository'de bir evaluator.
- Bir insan tarafından imzalanan ve her döngüde yeniden doğrulanan bir tool-permission manifest'i.

Anchor'ın rolü hedef drift'ini önlemektir. Döngü hedefi nasıl takip ettiğini iyileştirebilir ama hedefin ne olduğunu edit edemez.

İncelikli failure mode: döngünün edit edemediği bir anchor, anchor'ı nasıl okuduğunda drift eden bir döngü tarafından hâlâ yeniden yorumlanabilir. Constitutional AI (Ders 17) novel durumları işlemek için açıkça reason-based'tir; o akıl yürütme katmanı yorum drift'inin yaşadığı yerdir. Anchor'lar gereklidir, yeterli değil.

### Primitif 3: çok-hedefli kısıtlamalar

Tek bir skaler skor için optimize eden bir döngü kestirmeler bulur. Birden fazla sert kısıtlamayı eşzamanlı karşılaması gereken bir döngünün daha az kestirmesi vardır. Tipik eksenler:

- Performans (görev-seviyesi benchmark)
- Safety (red-team değerlendirmeleri, bilinen-kötü üzerinde reddetme oranı)
- Adillik (hassas alt gruplarda disparate-impact sınırları)
- Dayanıklılık (OOD test setleri, adversarial input işleme)

Bir modifikasyon yalnızca her kısıtlama tutulduğunda kabul edilir. Ders 13'ün cost governor'ı bunu finansal kısıtlamalarla istifler. Ders 18'in Llama Guard'ı bir safety ekseni olarak takılır.

### Primitif 4: regresyon tespiti

Her döngünün skorları tarihsel dağılımlara karşı karşılaştırılır. Yapılandırılmış toleransın ötesinde bir düşüş döngüyü duraklatır. Bu, aksi takdirde döngü "üzerinden iyileştikçe" çalışan ortalamaya emilecek sessiz kapasite kaybını yakalar.

Pratik bir uygulama: son N döngünün görev başına skorlarını depola. Her yeni döngü görev başına bir delta hesaplar. Herhangi bir delta bir eşiğin altına düşerse, döngü reddedilir ve bir insan inceler.

### Bilgi-teorik sınırlar

Kolmogorov karmaşıklığı ve Lob teoremi bir sistemin kendisi hakkında neyi kanıtlayabileceğine üst sınırlar koyar. Schmidhuber'in formal Godel Machine'i (Ders 4) en yüksek böyle sınırı hedefledi; kimse non-trivial bir kanıt tamamlamadı. Lob'un sonucu der ki: bir sistem kanıtlanabilir şekilde "X yapmam gerektiğini kanıtlarsam X yapacağım"a inanıyorsa, X'i yapması gerektiğini kanıtlamadan yapacaktır, iyi bilinen bir self-reference failure'ı.

Primitiflerimiz için ima: safety problemini kapatamazlar. Sessiz failure'ı daha pahalı yaparlar. Eksik bir kontrolü sessizce atlayacak kötü niyetli veya drift etmiş bir döngü, şimdi açık olanı aktif olarak baltalamak zorundadır ki bu daha tespit edilebilir bir imzadır.

### İşlenmiş bir örnek

Bir agent'ın bir edit önerdiğini varsay. Gating yığını:

1. Invariant kontrolleri: modül hash'leri, tool-permission manifest, anayasal header.
2. Anchor kontrolü: hedef ifadesi onaylanmış versiyona eşleşir (byte-bazlı veya anlamsal).
3. Çok-hedefli değerlendirme: performans, safety, adillik, dayanıklılık eksenleri.
4. Regresyon tespiti: hiçbir eksen toleranstan fazla düşmez.

Edit'in inmesi için dördünün de geçmesi gerekir. Tek bir failure döngüyü duraklatır.

## Kullan

`code/main.py`, Ders 4'teki DGM tarzı oyuncak üzerinde bir bounded self-improvement döngüsü çalıştırır, ancak üstüne dört primitif katmanlandırılmış olarak. Her primitif bireysel olarak etkinleştirilebilir veya devre dışı bırakılabilir. Demonstrasyon her primitif'in belirli bir failure sınıfını yakaladığı ve herhangi birini kaldırmanın o failure sınıfını geçirdiğidir.

## Yayınla

`outputs/skill-bounded-loop-review.md`, önerilen bir bounded döngüyü audit eder ve dört primitif'ten hangisini iddia ettiklerine karşı gerçekten uyguladığını puanlar.

## Alıştırmalar

1. `code/main.py`'yi tüm primitif'ler etkinken çalıştır. Döngünün hack'in kazanmasına izin vermeden birincil metrikte hâlâ iyileştiğini doğrula.

2. Regresyon tespitini devre dışı bırak. Bunun sessiz kapasite kaybının kabul edilmesine yol açtığı bir input oluştur.

3. Çok-hedefli kısıtlamayı devre dışı bırak. Döngünün performans ekseninde yakınsadığını ve bir safety ekseninin düştüğünü göster.

4. Bir coding agent için bir alignment anchor tasarla. Hangi metin, nerede saklı, nasıl kontrol ediliyor?

5. ICLR 2026 RSI Workshop özetini oku. Dört primitif'ten birini seç ve mevcut sanat durumuna somut bir iyileştirme öner.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Invariant | "Her zaman-doğru özellik" | Her edit'ten önce ve sonra harici kod tarafından kontrol edilen bir özellik |
| Alignment anchor | "Sabitlenmiş hedef" | Döngünün edit yüzeyinin dışında değiştirilemez çekirdek-hedef temsili |
| Çok-hedefli kısıtlama | "Tüm eksenler tutmalı" | Performans, safety, adillik, dayanıklılık — hepsi gerekli |
| Regresyon tespiti | "Düşüşte duraklat" | Tarihsel metrik delta'ları kapasite kaybı önerdiğinde döngüyü duraklat |
| Kolmogorov sınırı | "Bilgi-teorik sınır" | Bir sistemin kendi halefi hakkında neyi kanıtlayabileceğini sınırlar |
| Lob teoremi | "Self-reference tuzağı" | Sistem "yapmalıyım"ı kanıtlamadan "yapmalıyım" üzerine eyleme geçebilir |
| Gate yığını | "Katmanlı kontrol" | Birleştirilmiş birden fazla primitif; herhangi bir failure edit'i reddeder |
| Bounded improvement | "Azaltma, kanıt değil" | Sessiz-failure maliyetini yükseltir; safety problemini kapatmaz |

## İleri Okuma

- [ICLR 2026 RSI Workshop summary (OpenReview)](https://openreview.net/pdf?id=OsPQ6zTQXV) — dört-primitif yakınsaması.
- [Anthropic Responsible Scaling Policy v3.0](https://anthropic.com/responsible-scaling-policy/rsp-v3-0) — çok-hedefli kapasite eşikleri.
- [DeepMind Frontier Safety Framework v3](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — bir invariant primitif olarak deceptive-alignment monitoring.
- [Schmidhuber (2003). Godel Machines](https://people.idsia.ch/~juergen/goedelmachine.html) — bu primitiflerin formal-kanıt atası.
- [Anthropic — Claude's Constitution (January 2026)](https://www.anthropic.com/news/claudes-constitution) — reason-based alignment anchor'ı.
