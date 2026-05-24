# Başarısızlık Modları — MAST, Groupthink, Monoculture, Cascading Errors

> 2026 için referans taksonomi **MAST** (Cemri ve diğ., NeurIPS 2025, arXiv:2503.13657)'dir, 7 state-of-the-art açık kaynak MAS'tan 1642 yürütme izinden türetilmiştir ve **%41-86.7 başarısızlık oranı** gösterir. Üç kök kategori: **Specification Problems** (%41.77) — rol belirsizliği, belirsiz görev tanımları; **Coordination Failures** (%36.94) — iletişim bozulmaları, state senkronizasyon kaybı; **Verification Gaps** (%21.30) — eksik doğrulama, kalite kontrolleri yok. **Groupthink** ailesi (arXiv:2508.05687) ekler: monoculture çöküşü (aynı baz model → korelasyonlu başarısızlıklar), conformity bias (agent'lar birbirinin hatalarını pekiştirir), eksik theory of mind, mixed-motive dinamikleri, cascading güvenilirlik başarısızlıkları. Cascading örneği: ödeme başarısızlığının sipariş retry'larını tetiklediği, onların envanter retry'larını tetiklediği, onların da envanter servisini bunalttığı retry storm'ları (saniyeler içinde 10× yük — circuit breaker'lara ihtiyaç). Bellek zehirlenmesi: bir agent'ın halüsinasyonu paylaşılan belleğe girer, downstream agent'lar onu gerçek olarak ele alır; doğruluk kademeli olarak bozulur, kök-neden teşhisini acılı kılar. **STRATUS** (NeurIPS 2025) uzmanlaşmış detection / diagnosis / validation agent'ları ile 1.5× mitigation-success iyileştirmesi rapor eder. Bu ders başarısızlık modlarını first-class mühendislik hedefleri olarak ele alır.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 13 (Paylaşılan Bellek), Faz 16 · 14 (Konsensüs ve BFT), Faz 16 · 15 (Voting ve Debate Topology)
**Süre:** ~75 dakika

## Sorun

Çoklu-agent sistemleri gerçek görevlerde %41-86.7 başarısız olur (Cemri ve diğ. 2025 bunu 7 açık kaynak MAS arasında ölçtü). Bu "sadece daha fazla agent ekle" ile hata ayıklanabilir değil. Başarısızlıkların yapısal nedenleri vardır. MAST taksonomisi sana kategorileri verir. Bu ders her kategoriyi somut bir tespit, teşhis ve hafifletme desenine eşler — böylece sayılar keyfi görünmemeye başlar.

2026 üretim pratiği başarısızlık modlarını tasarım girdileri olarak ele almaktır. Mimari her MAST kategorisine işaret edip dağıttığın hafifletmeyi isimlendirebilene kadar "yeterince iyi" değildir.

## Kavram

### MAST kategorileri

**Specification Problems (başarısızlıkların %41.77'si).** Agent'ın görevi yeterince sıkı tanımlanmamış. Örnekler:

- Rol belirsizliği: iki agent ikisi de reviewer olduğunu düşünür.
- Görev az-tanımlanmış: kullanıcı belirli bir açı istediğinde "bunu özetle".
- Başarı kriterleri örtük: agent başarılı olup olmadığını söyleyemez.

Hafifletmeler:
- Açık rol kontratları yaz. Her agent'ın prompt'u ne yaptığını *ve ne yapmadığını* belirtir.
- Görev başına kabul testleri. Agent başlamadan önce "tamam X gibi görünüyor" tanımla.
- Pre-flight spec kontrolü: ayrı bir agent dispatch'ten önce görev tanımını inceler.

**Coordination Failures (%36.94).** İletişim ya da state bozulmaları.

Örnekler:
- İki agent paylaşılan state'i senkronizasyon olmadan günceller.
- Agent'lar arası kayıp mesaj (kuyruk başarısızlığı, timeout).
- State drift: agent A görevin bittiğini düşünür; agent B hâlâ yürütüyor.

Hafifletmeler:
- İyimser eş zamanlılıkla sürümlü paylaşılan state.
- Kritik mesajlar için açık ack (ack'lenene kadar retry).
- Periyodik state-senk checkpoint'leri; drift'i erken tespit et.

**Verification Gaps (%21.30).** Çıktılarda bağımsız kontrol yok.

Örnekler:
- Bir agent başarı iddia eder; kimse doğrulamaz.
- Agent zinciri her biri öncekinin çıktısına güvenir.
- Ortaya çıkan bileşik davranış üzerinde test kapsamı eksik.

Hafifletmeler:
- Bağımsız verifier agent (Ders 13). Salt-okunur, bağımsız kaynak erişimi.
- Açık handoff kontratı: "A'nın çıktısı B başlamadan checker C'yi geçmeli."
- Post-hoc analiz için sonuç log'lama.

### Groupthink ailesi (arXiv:2508.05687)

Agent'lar homojenleştiğinde ya da birbirini taklit ettiğinde beş ilgili başarısızlık:

**Monoculture çöküşü.** Aynı baz model ya da eğitim verisi → korelasyonlu hatalar. Üç agent bir LLM paylaştığında, halüsinasyonlarını paylaşırlar.

**Conformity bias.** Agent'lar en yüksek sesle ya da en kendine güvenen peer'a doğru ayarlanır, yanlış olsa bile.

**Eksik ToM.** Agent'lar birbirlerinin inançlarını modellemez; koordinasyon dağılır (Ders 18).

**Mixed-motive dinamikleri.** Kısmen hizalı teşviklere sahip agent'lar uzlaşma-ortasına doğru kayar, hiç kimseyi tatmin etmez.

**Cascading güvenilirlik başarısızlıkları.** Bir bileşenin hata deseni bağımlı bileşenlerde hata desenleri tetikler.

### Cascading örneği — retry storm

Klasik bir 2026 olay deseni:

```
ödeme servisi istek %10'unda başarısız olur
   ↓
sipariş agent'ı ödemeyi retry eder (üstel backoff ama naif)
   ↓
her retry yeni bir sipariş-envanter kontrolüdür
   ↓
envanter servisi normal yükün 2×'ini görür
   ↓
envanter servisi timeout vermeye başlar
   ↓
her sipariş envanter kontrolünü retry eder
   ↓
envanter servisi normal yükün 10×'ini görür
   ↓
cluster düşer
```

Düzeltme klasiktir: **circuit breaker'lar**. Downstream hata oranı eşiği aştığında, cache'lenmiş ya da varsayılan sonuçlarla kısa devre yap. Artı istek başına sınırlı retry bütçeleri.

Circuit breaker'lar değişiklik olmadan dağıtık sistemlerden doğrudan ödünç aldığın az sayıda çoklu-agent başarısızlık hafifletmesinden biridir.

### Bellek zehirlenmesi (yeniden ziyaret)

Ders 13'ten: bir agent'ın halüsinasyonu paylaşılan-bellek gerçeği olur; downstream agent'lar zehirlenmiş gerçek üzerinde akıl yürütür. MAST terimleriyle, bu paylaşılan-bellek katmanında bir doğrulama boşluğudur.

Kademeli doğruluk bozulması belirtidir. Bir crash almazsın; kök-nedeni zor olan yavaş drift alırsın.

Hafifletme: append-only log, provenance, yazılamaz verifier. Zaten Ders 13'te kapsanmıştır.

### STRATUS — başarısızlık tespiti için uzmanlaşmış agent'lar

STRATUS (NeurIPS 2025) şunları dağıttığında 1.5× mitigation-success iyileştirmesi rapor eder:

- **Detection agent.** Belirti desenlerini (yüksek anlaşmazlık, retry artışları, doğruluk drift'i) izler.
- **Diagnosis agent.** Belirtiler verili, MAST taksonomisinden olası kök neden çıkarır.
- **Validation agent.** Bir hafifletme uygulandıktan sonra belirtilerin temizlendiğini kontrol eder.

Bu SRE-stili olay yanıtı, agent sistemlerine uygulanır. Üç rolün hepsi uzmanlaşmış prompt'lara sahip LLM agent'ları olabilir.

### Başarısızlık-modu denetimi

2026 en iyi uygulaması yıllık (ya da büyük sürüm başına) başarısızlık-modu denetimidir:

1. **İz örneklemi.** ~1000 gerçek yürütme izi topla.
2. **Kategorize et.** Her izin başarısızlıkları için MAST + Groupthink kategorilerine eşle.
3. **Kategori başına başarısızlık oranını hesapla.** Sisteminde hangi kategoriler baskın?
4. **Hafifletmeleri sırala.** Hangi düzeltme en çok başarısızlığı ortadan kaldırır?
5. **2-3 hafifletme seç.** Uygula; sonraki çeyrek yeniden denetle.

Disiplin belirli seçimlerden daha önemlidir. Denetimler olmadan başarısızlıklar gürültüye karışır ve asla sistematik olarak ele alınmaz.

### Sistemler sessizce başarısız olduğunda

En tehlikeli başarısızlık kategorisi sessiz doğruluk başarısızlığıdır. Yüksek sesle başarısız olan (crash, exception, alarm) bir sistem izlenebilir. Makul-ama-yanlış çıktılar üreten bir sistem exception log'ları ile tespit edilemez. Doğrulama boşlukları yalnızca sayıca %21.30 olmasına rağmen başarısızlık başına en pahalı kategori olmasının nedeni budur.

Yatırım yap:
- Örneklemeli insan incelemesi.
- Altın-veri seti regresyon testleri.
- Önemli çıktılar üzerinde agent-arası çapraz-kontrol.

### Başarısızlık vs yavaş başarısızlık

Bazı başarısızlıklar anlıktır; bazıları yavaştır. Anlık başarısızlıklar (timeout, schema uyuşmazlığı, auth hatası) tespit etmek ucuzdur. Yavaş başarısızlıklar (bellek zehirlenmesi, monokültür drift'i, rol belirsizliği) tespit etmek ve önlemek pahalıdır.

2026 mühendislik hamlesi: yavaş-başarısızlık proxy'lerini enstrümante et böylece görünür bir hata olmadan önce drift'i yakalayabilirsin. Anlaşma oranı, retry oranı, çıktı-uzunluğu dağılımı ve ardışık agent sürümleri arasındaki edit-distance hepsi yararlı proxy'lerdir.

## İnşa Et

`code/main.py` şunları uygular:

- `FailureTaxonomy` — simüle edilmiş olayları MAST + Groupthink kategorilerine kategorize eder.
- `CircuitBreaker` — klasik desen; hata oranı eşiği aştığında açılır.
- `RetryStormSimulator` — cascading başarısızlığı gösterir; circuit breaker'ı açar/kapatır.
- `DetectionAgent` — senaryolu STRATUS-stili belirti eşleştirici.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı:
- circuit breaker'sız retry storm: envanter hataları patlar (simüle edilmiş).
- circuit breaker ile: eşikte sınırla; degraded-mode yanıtlar sunulur.
- detection agent deseni işaretler ve MAST kategorisini isimlendirir.

## Kullan

`outputs/skill-mast-auditor.md` bir çoklu-agent sisteminde MAST-stili bir başarısızlık-modu denetimi çalıştırır. İzler → kategorizasyon → hafifletme sıralaması.

## Yayınla

Üretimde başarısızlık-modu disiplini:

- **Çeyrek başına MAST denetimi.** Yıllık değil. Kategoriler sistemin büyüdükçe kayar.
- **Her yere circuit breaker'lar.** Herhangi bir bağımlı servise her dışa çağrı. Varsayılan açık eşik %5-10 hata oranında.
- **Altın veri setleri.** Küçük, yüksek-kaliteli, elle denetlenmiş. Haftalık olarak onlara karşı regresyon-test.
- **STRATUS üçlüsü.** Üretimi izleyen Detection + Diagnosis + Validation agent'ları. Yalnızca detection agent ile başla; belirtiler gürültülü olduğunda diagnosis ekle.
- **Başarısızlık bütçesi.** Kategori başına başarısızlık oranı için açık SLO. Bütçeyi aşmak bir gönderim-durdurma konuşmasını tetikler.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Circuit breaker'ın retry storm'u sınırladığını doğrula. Başarısızlık eşiğini değiştir ve takası gözlemle.
2. Bir **yavaş-başarısızlık proxy'si** uygula: 3 paralel agent arasında anlaşma oranı. Keskin düştüğünde, bir alarm tetikle. Agent çıktılarını kademeli olarak korelasyonlandırarak bir monokültür drift'i simüle et.
3. Cemri ve diğ.'i (arXiv:2503.13657) oku. 7 MAS sisteminden birini seç ve onun en iyi 3 başarısızlık kategorisini eşle. Bunlar MAST'ın öngördüğüyle nasıl karşılaştırılıyor?
4. Groupthink makalesini (arXiv:2508.05687) oku. Beş desenden hangisinin üretimde tespit etmesi en zor olduğunu belirle. Bir proxy metriği öner.
5. Bildiğin belirli bir çoklu-agent sistemi için STRATUS-stili bir detection-diagnosis-validation üçlüsü tasarla. Detection hangi belirtileri izler? Diagnosis hangi hafifletmeleri önerir? Validation onların çalıştığını nasıl doğrular?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| MAST | "2026 taksonomi" | Cemri 2025; 3 kök kategori + 14 alt-tip başarısızlık. |
| Specification Problem | "Rol belirsizliği" | Görev ya da rol az-tanımlanmış; agent'lar ne yapacaklarını bilmez. |
| Coordination Failure | "State drift" | Agent'lar arası iletişim ya da senk bozulması. |
| Verification Gap | "Kimse kontrol etmedi" | Bağımsız doğrulama olmadan kabul edilen çıktılar. |
| Groupthink ailesi | "Homojenlik başarısızlıkları" | Monoculture, conformity, eksik ToM, mixed-motive, cascading. |
| Monoculture çöküşü | "Aynı model, aynı halüsinasyonlar" | Paylaşılan baz model ya da eğitim verisinden korelasyonlu hatalar. |
| Retry storm | "Cascading hata büyütmesi" | Bir başarısızlık downstream yükü büyüten retry'ları tetikler. |
| Circuit breaker | "Hata oranında hızlı başarısız ol" | Hata oranı eşiği aştığında aç; varsayılanla kısa devre yap. |
| STRATUS | "Olay yanıt üçlüsü" | Detection + diagnosis + validation agent'ları. 1.5× hafifletme başarısı. |
| Bellek zehirlenmesi | "Halüsinasyonlar yayılır" | Paylaşılan-bellek gerçeği kirlenmiş; downstream agent'lar zehir üzerinde akıl yürütür. |

## İleri Okuma

- [Cemri ve diğ. — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) — MAST taksonomisi, NeurIPS 2025
- [Groupthink failures in multi-agent LLMs](https://arxiv.org/abs/2508.05687) — monoculture, conformity ve beş-aile taksonomisi
- [STRATUS — specialized agents for MAS incident response](https://neurips.cc/) — NeurIPS 2025 proceedings girdisi (detection + diagnosis + validation)
- [Release It! — stability patterns (Nygard)](https://pragprog.com/titles/mnee2/release-it-second-edition/) — kanonik circuit-breaker referansı
- [Anthropic — Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — üretim başarısızlık-modu notları
