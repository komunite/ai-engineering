# Generative Agent'lar ve Ortaya Çıkan Simülasyon

> Park ve diğ. 2023 (UIST '23, arXiv:2304.03442) 25 agent'lı bir kum havuzu olan **Smallville**'i üç-parçalı bir mimari ile doldurdu: **memory stream** (doğal-dil log'u), **reflection** (agent'ın kendi stream'i hakkında ürettiği daha yüksek-seviye sentezler) ve **plan** (gün-seviye davranış, sonra alt-planlar). Önemli sonuç Sevgililer Günü partisinin ortaya çıkışıydı: "Sevgililer Günü partisi düzenlemek istiyor" ile tohumlanmış bir agent, başka senaryo olmadan, popülasyona yayılan davetiyeler, koordine edilmiş randevular üretti ve parti gerçekleşti — onu bilgisi olmayan 24 agent'tan. Ablation'lar üç bileşenin de inanılabilirlik için gerekli olduğunu gösteriyor. Belgelenen başarısızlıklar mekansal-norm hataları (kapalı dükkanlara girme, tek-kişilik tuvaletleri paylaşma). Bu, 2026'da agent simülasyonları ve çoklu-agent sosyal değerlendirme için referans mimaridir.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 04 (Primitive Model), Faz 16 · 13 (Paylaşılan Bellek)
**Süre:** ~75 dakika

## Sorun

Çoğu çoklu-agent sistemi sıkıca-senaryolu takımlardır: planner planlar, coder kodlar, reviewer inceler. Bu iyi-tanımlanmış görevler için çalışır. Agent'lar bellek, öncelikler ve açık bir dünyaya sahip olduğunda ortaya çıkan, senaryosuz davranışı yakalamaz. Araştırma, toplum simülasyonu ve giderek artan oyun AI'sı bu ikinci türe ihtiyaç duyar.

Smallville mimarisi bunun benchmark'ıdır. Park 2023'e kadar en iyi agent simülasyonları sığ senaryo-takipçileriydi; ondan sonra desen açık dünyalardaki generative agent'lar için varsayılan oldu. 2026'da bir agent simülasyonu inşa edersen, ya Smallville'in üç bileşenini kullanıyorsundur ya da neden kullanmadığını açıkça gerekçelendiriyorsundur.

## Kavram

### Üç bileşen

**Memory stream.** Gözlemler, eylemler, reflection'lar ve planların append-only log'u. Her girdinin bir timestamp'i, bir tipi, bir tanımı (doğal dil) ve türetilmiş metadata'sı vardır: **recency**, **importance** (agent tarafından 1-10 kendi-puanlanmış) ve **relevance** (mevcut sorguya cosine benzerliği).

```
[2026-02-14 09:12:03] observation: Isabella Rodriguez bana jazz sevip sevmediğimi sordu
[2026-02-14 09:14:22] reflection:   Müzik hakkında uzun konuşmalardan keyif alıyorum
[2026-02-14 10:05:00] plan:         Bu gece Isabella'nın Sevgililer Günü partisine katıl
```

Bellek getirme üç skoru birleştirir: `score = w_recency * e^(-decay * age) + w_importance * importance + w_relevance * cos_sim`. Top-k girdiler mevcut prompt'a girer.

**Reflection.** Periyodik olarak (her N bellekte ya da önemli event'lerde), agent son bellekten daha yüksek-mertebe sentezler üretir. Reflection girdileri stream'e geri gider ve herhangi bir bellek gibi getirilebilir. Agent'ların "anlayışlar" oluşturmasının yolu budur — mimarinin uzun-vadeli inançlara eşdeğeri.

**Plan.** Yukarıdan aşağı parçalama. Önce gün-seviye plan geniş hatlarda ("işe git, Klaus ile akşam yemeği ye"). Sonra saat-seviye planlar. Sonra eylem-seviye planlar. Planlar revize edilebilir: bir gözlem bir planla çeliştiğinde, agent etkilenen segmenti yeniden planlar.

### Neden üçü de önemli (ablation)

Park ve diğ. observation, reflection ve plan'ın her birini düşüren ablation'lar çalıştırdı. Her ablation inanılabilirliği zedeler:

- **Observation** olmadan agent context'i kaçırır ve eski inançlar üzerinde hareket eder.
- **Reflection** olmadan agent daha yüksek-mertebe inançlar oluşturamaz; etkileşimler sığ kalır.
- **Plan** olmadan davranış tepkisel gürültüye dönüşür; hedefler dağılır.

İnsan rater'lardan inanılabilirlik skorları üçü de varken en yüksek; herhangi birini düşürmek ölçülebilir bir gerileme üretir.

### Sevgililer Günü ortaya çıkışı

Bir agent, Isabella Rodriguez, "14 Şubat saat 17:00'de Hobbs Cafe'de Sevgililer Günü partisi düzenlemek istiyor" hedefi ile tohumlandı. Diğer 24 agent böyle bir tohum almıyor. Simüle edilen günler boyunca:

1. Isabella'nın planı insanları davet etmeyi içerir.
2. Her davet bir komşunun memory stream'inde bir gözlem olur.
3. O komşunun reflection'ı inançlar üretir: "Isabella bir parti veriyor."
4. Komşunun planı "14 Şubat'ta partiye katıl"ı içerir.
5. Komşular diğer komşulara söyler. Davet merkezi koordinasyon olmadan yayılır.
6. 14 Şubat saat 17:00'de birkaç agent Hobbs Cafe'de birleşir.

Bu teknik anlamda ortaya çıkıştır: sistem-seviye davranış (bir parti) merkezi orchestrator olmadan yerel etkileşimlerden (iki-yönlü davetler + bireysel planlama) doğdu.

### Belgelenen başarısızlık modları

Park ve diğ. açıkça belgeliyor:

- **Mekansal norm hataları.** Agent'lar kapalı dükkanlara girer. Agent'lar aynı tek-kişilik tuvaleti kullanmaya çalışır. Agent'lar yemek için tasarlanmamış odalarda yemek yer. Model çevreden sosyal-fiziksel normları çıkarsamıyor.
- **Bellek taşması.** Derin simülasyon çalıştırmaları bellek-getirme maliyetinin büyümesine yol açar. Pratik çare: periyodik bellek sıkıştırması (özet-ve-buda) ve düşük-önemli girdilerde bozulma.
- **Reflection halüsinasyonu.** Reflection'lar memory stream'de var olmayan ilişkiler uydurabilir. Hafifletme: reflection prompt'larına kaynak bellek id'leri ekle ve getirme zamanında doğrula.

Bunlar üretim-ilgili başarısızlık modları: herhangi bir 2026 agent simülasyonu bunları miras alır.

### Üç-bileşen uygulama kuralları

1. **Bellek append-only'dir.** Bir bellek girdisini asla muta etme. Düzeltmeler yeni girdilerdir.
2. **Önemlilik skorları ucuzdur.** Yazma zamanında importance'ı 1-10 puanlamak için LLM'i çağır. Skoru cache'le.
3. **Getirme sıralıdır, filtreli değil.** Birleşik skorla top-k; sert filtreler kullanma (context'i kaybeder).
4. **Reflection periyodik çalışır.** İşlenmemiş belleğin önem toplamı bir eşiği aştığında tetikle (ör. 150).
5. **Planlar revize edilebilirdir.** Yeni bir gözlem bir planla çeliştiğinde, etkilenen segmenti yalnızca yeniden üret, tüm planı değil.

### Smallville'in ötesindeki generative agent'lar

2024-2026 takip literatürü mimariyi genişletir:

- **Politika / pazar araştırması için çoklu-agent sosyal simülasyon.** Smallville-benzeri popülasyonlar özelliklere yanıt olarak kullanıcı davranışını simüle eder. A/B testlerinden daha hızlı; doğruluk tartışmalıdır.
- **Oyunlar için NPC AI.** Smallville agent'larıyla RPG'ler senaryolu görevler yerine ortaya çıkan hikayeler üretir.
- **Generative-agent değerlendirme benchmark'ları.** Görev doğruluğu yerine, metrik uzun çalıştırmalar üzerinde inanılabilirlik + davranış tutarlılığı olur.

Mimari referanstır. Uzantılar bileşenleri değiştirir (bellek için vektör store, retrieval-augmented reflection, neurosymbolic plan) ama üç-parçalı yapıyı korur.

### Bu çoklu-agent mühendisliği için neden önemli

Smallville bileşenler doğru olduğunda çoklu-agent ortaya çıkışının ucuz olduğunun kanıtıdır. Mimari şimdi açık kaynak modellerde replike edildi (daha küçük LLM'ler inanılabilirliği keskin değil, kademeli olarak kaybeder). **Ortaya çıkan sosyal davranışa** ihtiyaç duyan herhangi bir üretim sistemi bu şekli kullanır. **Sıkı görev yürütmesine** ihtiyaç duyan herhangi bir sistem bu fazda daha önce supervisor / roller / primitive desenlerini kullanır.

## İnşa Et

`code/main.py` üç bileşeni senaryolu agent politikalarıyla stdlib Python'da uygular (gerçek LLM yok). Demo Sevgililer-günü partisinin ortaya çıkışını minyatür olarak yeniden üretir:

- `MemoryStream` — recency/importance/relevance getirme ile append-only log.
- `reflect(stream)` — son yüksek-önemli bellek üzerinde senaryolu reflection.
- `plan(agent_state)` — mevcut inançlara dayalı gün-seviye ve saat-seviye planlar.
- Senaryo: 5 agent. Agent 1 "17:00'de parti ver" ile başlar. Simüle edilen tick'lerde davet yayılır ve agent'lar birleşir.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: tick-tick izleme. Son tick'te 5 agent'tan en az 3'ü planlarında partiyi gösterir ve parti konumunda birleşirler. Tek tohum, herhangi bir orchestrator olmadan koordineli varışı üretti.

## Kullan

`outputs/skill-simulation-designer.md` bir generative-agent simülasyonu tasarlar: agent sayısı, bellek şeması, reflection sıklığı, plan ufku ve değerlendirme metriği.

## Yayınla

Üretim simülasyonları için kurallar:

- **Bellek veritabanıdır.** Ölçekte gerçek bir store seç (vektör DB, Postgres). In-memory stdlib prototipler için.
- **Getirme izini log'la.** Her eylem için onu yönlendiren top-k bellekleri log'la. Bu hata ayıklama yeteneğindir.
- **Agent başına token bütçesi.** Tick başına her agent'ın retrieve + reflect + plan'ı O(k) LLM çağrısıdır. N agent × T tick × tick başına çağrılar bütçeni cüceleştirebilir.
- **Belleği periyodik olarak sıkıştır.** Düşük-önemli girdileri özetle-ve-buda. Saklama politikası bir tasarım kararıdır, detay değil.
- **Mekansal / sosyal norm ihlallerini** açıkça tespit et. Mimari onları öğrenmiyor.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. 3+ agent'ın partide birleştiğini doğrula. Agent'ları 10'a artır — ortaya çıkış hâlâ oluyor mu?
2. Reflection adımını kaldır. Davranış nasıl görünür? Park 2023'teki ablation bulgusuna eşle.
3. Rekabet eden tohumlanmış bir hedef tanıt ("Klaus 17:00'de araştırma konuşması yapmak istiyor"). Agent'lar bölünüyor mu, yoksa bir hedef baskın mı? Onu ne belirler?
4. Mekansal kısıtlar ekle: Hobbs Cafe en fazla 4 agent tutar. Simülasyon taşmayı zarafetle ele alıyor mu yoksa "tek-kişilik tuvalet" başarısızlık desenine mi çarpıyor?
5. Park ve diğ.'i (arXiv:2304.03442) Bölüm 6 (ortaya çıkan davranış deneyleri)'ni oku. Minyatüründe yeniden üretilemeyen bir davranışı belirle. Mimarinin hangi bileşenini geliştirmen gerekir?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Memory stream | "Agent'ın günlüğü" | Gözlemler, eylemler, reflection'lar, planların append-only log'u. |
| Recency | "Bellek ne kadar yeni" | Yaşa göre üstel-bozulma skoru. |
| Importance | "Agent ne kadar önemsiyor" | Yazma zamanında kendi-puanlanmış 1-10. Cache'lenmiş. |
| Relevance | "Mevcut sorguyla ne kadar ilgili" | Cosine benzerliği (embedding-tabanlı). |
| Reflection | "Yüksek-mertebe inanç" | Son bellekten üretilmiş sentez, yeni bir bellek olarak yeniden alınır. |
| Plan | "Gün/saat/eylem parçalaması" | Yukarıdan aşağı plan ağacı. Gözlemler çeliştiğinde revize edilebilir. |
| Smallville | "Park 2023'ün kum havuzu" | Sevgililer Günü ortaya çıkışını üreten 25-agent simülasyon. |
| Believability | "Kalite metriği" | Davranışın makul bir agent gibi görünüp görünmediği için insan-rater skoru. |

## İleri Okuma

- [Park ve diğ. — Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442) — referans mimari
- [UIST '23 paper page](https://dl.acm.org/doi/10.1145/3586183.3606763) — yayın merkezi
- [Smallville code release](https://github.com/joonspk-research/generative_agents) — referans Python implementasyonu
- [Hayes-Roth 1985 — A Blackboard Architecture for Control](https://www.sciencedirect.com/science/article/abs/pii/0004370285900639) — yapılandırılmış-bellek agent'lar için önceki sanat
