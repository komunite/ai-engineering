# LLM'ler için Sürü Optimizasyonu (PSO, ACO)

> Biyolojiden ilham alan optimizasyon LLM geri dönüşü yapıyor. **LMPSO** (arXiv:2504.09247) her particle'ın velocity'sinin bir prompt olduğu ve LLM'in sıradaki adayı ürettiği PSO kullanır; yapılandırılmış-sıra çıktılarında iyi çalışır (matematik ifadeleri, programlar). **Model Swarms** (arXiv:2410.11163) her LLM uzmanını bir model-ağırlık manifoldu üzerinde PSO particle'ı olarak ele alır ve yalnızca 200 örnekle 9 veri setinde 12 baseline üzerine **%13.3 ortalama kazanım** raporlar. **SwarmPrompt** (ICAART 2025) prompt optimizasyonu için PSO + Grey Wolf'u hibridleştirir. **AMRO-S** (arXiv:2603.12933) çoklu-agent LLM yönlendirmesi için ACO-ilhamlı pheromone uzmanlarıdır — **4.7× hızlanma**, yorumlanabilir yönlendirme kanıtı, kaliteli-gateli asenkron güncelleme çıkarımı öğrenmeden ayrılır. Bu ders prompt parametre uzayında PSO'yu ve agent yönlendirmesinde ACO'yu uygular, bu klasik algoritmaların LLM dönemine neden uyduğunu ve ne zaman uymadığını ölçer.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 09 (Parallel Swarm Networks), Faz 16 · 14 (Konsensüs ve BFT)
**Süre:** ~75 dakika

## Sorun

Görev eval'inde %62 puan alan bir prompt'un var. İyileştirmek istiyorsun. Naif hamle gradient'siz manuel ayarlamadır, kötü ölçeklenir. Reinforcement learning ödül sinyalleri ve eğitmek için yeterli rollout ihtiyacı duyar. Prompt'lar üzerinde backprop gerçekten mümkün değil — prompt diferansiyellenebilir bir parametre değil, ayrık bir string'dir.

Klasik biyolojiden ilham alan optimizasyon — sürekli arama uzayları için PSO, yol seçimi için ACO — tam olarak bu rejim için tasarlandı: gradient'siz, popülasyon-tabanlı, değerlendirme başına ucuz. Onları LLM'lerle gradient'siz arama adımı için eşleştir ve şaşırtıcı derecede pratik bir optimizer elde edersin.

Aynı desenler çoklu-agent sistemlerinde agent *yönlendirmesi* için geçerlidir. ACO-stili bir pheromone trail hangi agent'ın hangi görev-tipinde en iyi çalıştığını kaydeder, router'ın trail'i sömürmesine izin verir ve rotaların yeniden keşfedilebilmesi için pheromone'ları çürütür.

## Kavram

### PSO hatırlatması (Kennedy & Eberhart 1995)

Particle Swarm Optimization: sürekli bir arama uzayında particle'lar popülasyonu. Her particle'ın `x_i` pozisyonu ve `v_i` velocity'si vardır. Her iterasyon:

```
v_i <- w * v_i + c1 * r1 * (p_best_i - x_i) + c2 * r2 * (g_best - x_i)
x_i <- x_i + v_i
fitness(x_i) değerlendir
iyileştiyse p_best_i'yi güncelle
global en iyi ise g_best'i güncelle
```

Burada `p_best` particle'ın kendi en iyisi, `g_best` sürünün en iyisi, `w, c1, c2` inertia + cognitive + social ağırlıkları, `r1, r2` rastgele faktörler.

### LLM çıktıları üzerinde PSO — LMPSO

arXiv:2504.09247 PSO'yu LLM-üretilen yapılandırılmış çıktılar (matematik ifadeleri, programlar) için uyarlar. Her particle bir aday çıktıdır. Velocity, mevcut çıktıyı kişisel/global en iyiye doğru nasıl değiştireceğini tanımlayan bir *prompt*'tur. LLM yeni çıktıyı velocity prompt'undan üretir. Velocity'nin "inertia"sı "küçük artımlı değişiklikler yap" gibi bir prompt'tur.

Bu şu durumlarda iyi çalışır:
- Çıktı yapılandırılmıştır (parse edilebilir, değerlendirilebilir).
- Fitness otomatiktir (test çalıştırmaları, aritmetik değerlendirme).
- Popülasyon küçüktür (~10-30 particle), böylece toplam LLM çağrıları yönetilebilir kalır.

Fitness insan incelemesi gerektirdiğinde iyi çalışmaz — iterasyon başına maliyet yasaklayıcı olur.

### Model Swarms

arXiv:2410.11163 PSO'yu çıktı katmanından *model* katmanına alır. Her "particle" bir uzman LLM'dir (parametreler). Sürü parametreleri gradient'siz bir güncelleme yoluyla kolektif en iyiye doğru hareket ettirir. Raporlanan: 9 veri setinde 12 baseline üzerine iterasyon başına yalnızca 200 örnekle %13.3 ortalama kazanım.

Temel içgörü LLM uzman modellerinin paylaşılan bir parametre manifoldunda (adapter ağırlıkları, LoRA delta'ları) zaten yakın olmasıdır. Bu düşük-boyutlu alt uzayda PSO ucuz ve etkilidir.

### ACO hatırlatması (Dorigo 1992)

Ant Colony Optimization: karıncalar bir grafı dolaşır; her yolun bir pheromone trail'i vardır. Karınca hareket olasılıkları pheromone gücüyle ağırlıklandırılır. Görevi tamamlayan karıncalar çözüm kalitesiyle orantılı pheromone bırakır. Pheromone zamanla çürür.

### AMRO-S — agent yönlendirmesi için ACO

arXiv:2603.12933 çoklu-agent yönlendirmesi için ACO kullanır. Her görev-tipi bir "destinasyon"; her agent olası bir rotadır. Pheromone iyi çıktılar üreten rotaları güçlendirir. Temel katkılar:

- **Yorumlanabilir yönlendirme kanıtı.** Pheromone gücü insan-okunabilir bir sinyaldir.
- **Kalite-gateli asenkron güncelleme.** Pheromone yalnızca kalite kontrolleri geçtikten sonra güncellenir, çıkarımı öğrenmeden ayırır.
- **4.7× hızlanma** çoklu-agent yönlendirme benchmark'ında.

Kalite gate'i önemli: olmadan, hızlı-ama-yanlış agent'lar pheromone biriktirir ve sistem kötü rotalara kilitlenir.

### LLM'ler için PSO / ACO ne zaman kullanılır

**PSO'yu şu durumlarda kullan:**
- Arama uzayı süreklidir ya da sürekli parametrelere eşlenir (prompt embedding'leri, LoRA ağırlıkları, sayısal üretim parametreleri).
- Fitness ucuz ve otomatiktir.
- Popülasyon küçük olabilir (10-30).

**ACO'yu şu durumlarda kullan:**
- Bir yönlendirme ya da yol-seçimi problemin var.
- Kararlar zamanla pekişir (aynı görev tipleri geri gelir).
- Yönlendirme kararları için yorumlanabilir kanıta ihtiyacın var.

**Şu durumlarda hiçbirini kullanma:**
- Fitness insan incelemesi gerektirir (iterasyon başına çok pahalı).
- Arama uzayı PSO'nun kapsamadığı şekilde ayrık ve kombinatoriktir (genetik algoritmalar kullan).
- Gerçek zamanlı kararlar katı gecikme gerektirir (PSO/ACO tek-geçiş sezgisellere göre yavaş yakınsar).

### Biyolojiden ilham almanın neden hâlâ kazandığı

Gradient-tabanlı yöntemler diferansiyellenebilir sinyallere ihtiyaç duyar. LLM çıktıları ve yönlendirme kararları kolaylıkla diferansiyellenebilir değildir. Sahte-gradient yöntemleri (reinforcement-öğrenilmiş router'lar, DPO-stili prompt tuner'lar) çalışır ama pahalı eğitime ihtiyaç duyar.

PSO ve ACO yalnızca bir *değerlendirici* fonksiyonuna ihtiyaç duyar. Bir aday çıktıyı ya da bir yönlendirme kararını puanlayabiliyorsan, o uzayda optimize edebilirsin. Bu, uygulanabilirlik çıtasını çok daha aşağı çeker.

### Pratik sınırlar

- **Popülasyon bütçesi.** N particle × T iterasyon × değerlendirme başına maliyet. ~$0.02/çağrı LLM eval'ler için 50 iterasyon çalıştıran 20-particle PSO ~$20 mal olur. Buna göre planla.
- **Keşif vs sömürü.** Pheromone çürüme oranı ve PSO inertia takas eder; çok hızlı çürüme → çözümleri unut; çok yavaş → erken yerel optimum'lara takıl.
- **Felaket kayması.** Fitness manzarası değişirse (yeni veri dağılımı), her iki algoritma da yakınsayıp sonra ayrışabilir. En-iyi-fitness stabilitesini izle.

## İnşa Et

`code/main.py` şunları uygular:

- `LMPSO` — sayısal prompt parametreleri (sıcaklık, top_k ağırlıkları) üzerinde PSO. Her particle'ın "LLM üretimi" senaryolu bir fitness fonksiyonu olarak simüle edilir. Algoritmayı 30 iterasyon çalıştırır ve g_best yakınsamasını gösterir.
- `AMRO_S` — ACO-stili yönlendirme. 3 agent, 4 görev tipi, pheromone matrisi, 100 yönlendirilmiş görev. Trail oluşumunu göstermek için zaman içinde (görev_tipi → agent seçimleri) dağılımını yazar.
- Karşılaştırma: aynı görev akışında rastgele yönlendirme vs ACO yönlendirme. Kalite ve gecikmeyi ölçer.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı:
- LMPSO: 30 iterasyon üzerinde g_best fitness rastgeleden optimal'e yakına iyileşir.
- AMRO-S: pheromone tablosu görev-tipi başına doğru agent'ta stabilize olur; ACO yönlendirme kalitede rastgeleyi ~%30-40 yener ve ayrıca gecikmeyi azaltır (daha az retry).

## Kullan

`outputs/skill-swarm-optimizer.md` LLM / agent optimizasyon problemleri için PSO, ACO, genetik algoritmalar ve gradient-tabanlı optimizer'lar arasında seçim yapmaya yardım eder.

## Yayınla

- **Küçük başla.** 10-20 particle, 20-50 iterasyon. Yalnızca yakınsama eğrisi net kazanım gösteriyorsa ölçeklendir.
- **İterasyon başına pheromone ya da g_best'i log'la.** Trail olmadan sürü optimizer'ı hata ayıklamak acı verici.
- **Kalite-gate güncellemeler.** Özellikle ACO yönlendirme için: hızlı-ve-yanlış agent'lar pheromone biriktirmemeli.
- **Dağılım kaymasında çürümeyi sıfırla.** Eval dağılımın değiştiğinde, yaşlı pheromone'lar bayattır; sıfırla ya da çürüme oranını geçici olarak iki katına çıkar.
- **İterasyon başına maliyeti sınırla.** İterasyon başına maliyet metriği yay. İterasyon başına $500 mal olan ve %0.5 kazanım sağlayan PSO gönderilebilir değil.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. LMPSO yakınsamasını gözlemle. Popülasyon boyutunu 5, 10, 20, 50 değiştir. Hangi boyutta yakınsama-zamanı doyar?
2. Bir "felaket kayması" deneyi uygula: iterasyon 30'dan sonra fitness fonksiyonunu değiştir. PSO ne kadar hızlı uyum sağlar? `p_best`'i sıfırlamak yardım ediyor mu?
3. AMRO-S'ye bir kalite gate'i ekle: yalnızca eval skoru > 0.7 olan çalıştırmalarda pheromone biriktirme. Bu, gatesiz versiyona karşı yakınsamayı nasıl değiştiriyor?
4. LMPSO'yu (arXiv:2504.09247) oku. Makaledeki "velocity as a prompt"u sayısal velocity'ne geri eşle. Simülasyonda ne kaybedildi ve ne korundu?
5. AMRO-S'yi (arXiv:2603.12933) oku. Asenkron pheromone güncellemesiyle ayrık "inference fast-path"i uygula. Bu sürekli yük altında sistem gecikmesini nasıl değiştirir?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| PSO | "Particle Swarm Optimization" | Kennedy-Eberhart 1995. Popülasyon-tabanlı gradient'siz optimizer. |
| ACO | "Ant Colony Optimization" | Dorigo 1992. Pheromone trail'leri yoluyla yol/rota optimizasyonu. |
| LMPSO | "LLM üretimli PSO" | arXiv:2504.09247. Velocity bir prompt; LLM adaylar üretir. |
| Model Swarms | "Uzman ağırlıkları üzerinde PSO" | arXiv:2410.11163. Model parametre alt uzayında gradient'siz güncelleme. |
| AMRO-S | "Agent yönlendirmesi için ACO" | arXiv:2603.12933. Görev-tipi × agent üzerinde pheromone matrisi. |
| p_best / g_best | "Kişisel / global en iyi" | Şimdiye kadar bulunan particle başına ve sürü çapında en iyi çözümler. |
| Pheromone | "Yönlendirme belleği" | Bir kenar üzerinde güç; zamanla çürür; kalitede birikir. |
| Kalite-gateli güncelleme | "Yalnızca iyi çalıştırmalardan öğren" | Kalite kontrolüne koşullu pheromone birikimi. |
| Felaket kayması | "Dağılım kayması" | Fitness manzarası değişir; eski p_best ve pheromone'lar bayat olur. |

## İleri Okuma

- [Kennedy & Eberhart — Particle Swarm Optimization](https://ieeexplore.ieee.org/document/488968) — 1995 PSO makalesi
- [Dorigo — Ant Colony Optimization](https://www.aco-metaheuristic.org/about.html) — 1992 ACO temelleri
- [LMPSO — Language Model Particle Swarm Optimization](https://arxiv.org/abs/2504.09247) — yapılandırılmış LLM çıktıları için PSO
- [Model Swarms — gradient-free LLM expert optimization](https://arxiv.org/abs/2410.11163) — model-ağırlık alt uzayında PSO
- [AMRO-S — ant-colony multi-agent routing](https://arxiv.org/abs/2603.12933) — kalite gate'li pheromone-yönlendirmeli yönlendirme
