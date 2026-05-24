# MARL — MADDPG, QMIX, MAPPO

> Çoklu-agent koordinasyonunun reinforcement-learning mirası, 2026'da hâlâ LLM-agent sistemlerini bilgilendirir. **MADDPG** (Lowe ve diğ., NeurIPS 2017, arXiv:1706.02275) Centralized Training, Decentralized Execution (CTDE)'i tanıttı: her critic eğitim sırasında tüm agent'ların state ve action'larını görür; test zamanında yalnızca yerel actor'lar çalışır. İş birlikçi, rekabetçi ve karışık ayarlar için çalışır. **QMIX** (Rashid ve diğ., ICML 2018, arXiv:1803.11485) monoton karıştırma ağıyla value-decomposition'dır; agent başına Q'lar joint Q'ya birleşir, böylece `argmax` temiz dağılır — StarCraft Multi-Agent Challenge (SMAC)'de baskın. **MAPPO** (Yu ve diğ., NeurIPS 2022, arXiv:2103.01955) merkezi value fonksiyonlu PPO'dur; minimal tuning ile particle-world, SMAC, Google Research Football, Hanabi'de "şaşırtıcı derecede etkili". Bunlar merkeziyetsizce hareket etmesi gereken agent takımları için politikaları eğitmenin altındaki şeyleri sağlar. MAPPO **varsayılan 2026 iş birlikçi-MARL baseline'ıdır**. Bu ders her birini küçük bir grid-world oyuncağından inşa eder ve LLM-agent eğitimine dokunmadan önce üç fikri kas hafızasına yerleştirir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, küçük NumPy-free implementasyonlar)
**Ön koşullar:** Faz 09 (Reinforcement Learning), Faz 16 · 09 (Parallel Swarm Networks)
**Süre:** ~90 dakika

## Sorun

LLM-agent sistemleri giderek artan oranda agent'lar arası koordinasyon için politikalar eğitir: ne zaman ertelenir, ne zaman hareket edilir, hangi peer çağrılır. Bu tür politikaları nasıl eğiteceğini söyleyen literatür Multi-Agent Reinforcement Learning (MARL)'dir, LLM dalgasından önce gelir ve küçük bir baskın algoritma setine sahiptir.

Desen kelime dağarcığı olmadan MARL makalelerini okumak acı verici. Centralized training with decentralized execution (CTDE), value decomposition ve centralized critic'ler trend kelimeler değil — belirli sorunların belirli yanıtları:

- Independent RL (her agent tek başına öğrenir) her agent'ın perspektifinden non-stationary'dir. Kötü.
- Centralized RL (bir agent hepsini kontrol eder) ölçeklenmez ve yürütme kısıtlarını ihlal eder.
- CTDE ikisinin en iyisini alır: global bilgiyle eğit, yerel politikalarla dağıt.

## Kavram

### Makalelerin kullandığı üç ortam

- **Particle World (multi-agent particle env).** İş birlikçi/rekabetçi görevlerle basit 2D fizik. MADDPG'nin orijinal test alanı.
- **StarCraft Multi-Agent Challenge (SMAC).** İş birlikçi mikro-yönetim, kısmi gözlem. QMIX'in test alanı. Ayrık eylemler, sürekli state'ler.
- **Google Research Football, Hanabi, MPE.** MAPPO baseline'ları.

Farklı env'ler farklı eylem/gözlem tipleri vardır. Algoritmalar buna göre seçer.

### MADDPG (2017) — CTDE deseni

Her agent `i`'nin kendi gözlemini eyleme eşleyen bir actor `mu_i(o_i)`'si vardır. Her agent ayrıca eğitim sırasında tüm gözlemleri ve tüm eylemleri gören bir critic `Q_i(x, a_1, ..., a_n)`'a sahiptir. Actor critic'in değerlendirmesine karşı policy gradient ile güncellenir.

```
actor update:    grad_theta_i J = E[grad_theta mu_i(o_i) * grad_a_i Q_i(x, a_1..n) at a_i=mu_i(o_i)]
critic update:   bir-sonraki-state joint tahminine verili Q_i(x, a_1..n) üzerinde TD
```

CTDE neden: eğitim zamanında herkesin eylemlerini biliriz; bunu her critic'te varyansı azaltmak için kullanırız. Dağıtım zamanında her agent yalnızca `o_i`'yi görür ve `mu_i(o_i)`'yi çağırır.

Başarısızlık modu: critic'ler N agent ile büyür (girdi tüm eylemleri içerir). Yaklaşımlar olmadan ~10 agent'ın ötesine ölçeklenmez.

### QMIX (2018) — value decomposition

Yalnızca iş birlikçi. Global ödül, agent başına Q-değerlerinin monoton bir fonksiyonunun toplamıdır:

```
Q_tot(tau, a) = f(Q_1(tau_1, a_1), ..., Q_n(tau_n, a_n)),   df/dQ_i >= 0
```

Monotonluk, her agent'ın bağımsız olarak `argmax_{a_i} Q_i`'yi seçerek `argmax_a Q_tot`'un hesaplanabileceğini garanti eder. Bu **ihtiyaç duyduğun tam olarak merkeziyetsiz yürütme özelliğidir**. Eğitim zamanında bir mixing network agent başına Q'lardan `Q_tot`'u üretir.

QMIX'in SMAC'ta neden kazandığı: iş birlikçi StarCraft mikro-yönetim homojen agent'lara, yerel gözleme, global ödüle sahiptir — value decomposition için mükemmel uyum.

Başarısızlık modu: monotonluk kısıtı sınırlayıcıdır; bazı görevler monoton-ayrıştırılamayan ödül yapılarına sahiptir (bir agent takım için fedakarlık yapar). Uzantılar (QTRAN, QPLEX) bunu gevşetir.

### MAPPO (2022) — gözden kaçan varsayılan

Multi-Agent PPO: merkezi value fonksiyonlu PPO. Her agent'ın kendi politikası vardır; tüm agent'lar tam state'i gören (ya da agent başına) value fonksiyonlarını paylaşır. Yu ve diğ. 2022 MAPPO'yu MADDPG, QMIX ve uzantılarına karşı beş benchmark'ta benchmark'ladı ve buldu ki:

- MAPPO particle-world, SMAC, Google Research Football, Hanabi, MPE'de off-policy MARL yöntemlerini eşler ya da yener.
- Minimal hyperparameter tuning gerekli.
- Stabil eğitim; seed'ler arası tekrarlanabilir.

Topluluk bu makaleye kadar on-policy MARL'ı küçümsedi. 2026'da MAPPO iş birlikçi MARL için varsayılan baseline; herhangi bir yeni yöntem onu yenmeli.

### LLM-agent mühendisleri neden umursamalı

Üç doğrudan kullanım:

1. **Router eğitimi.** Bir meta-agent hangi sub-agent'ın bir görevi ele alacağını seçer. Bu N merkeziyetsiz sub-agent ve bir merkezi router'lı bir MARL problemidir. MAPPO uyar.
2. **Rol ortaya çıkışı.** Generative-agent simülasyonlarında, agent'ları zaman içinde tamamlayıcı roller benimsemeye eğitmek gizlenmiş bir MARL problemidir. QMIX-stili value decomposition tamamlayıcılığı yapı gereği zorlar.
3. **Çoklu-agent tool kullanımı.** Agent'lar tool'ları paylaştığında ve bütçe için rekabet ettiğinde, onları CTDE ile eğitmek kaynak kısıtlarına saygı duyan dağıtılabilir yerel politikalar üretir.

Pratik uyarı: 2026'da çoğu üretim LLM-agent sistemi politikalarını eğitmek yerine prompt'lar. MARL (a) çok fazla etkileşim verisi, (b) net bir ödül sinyali ve (c) eğitim altyapısına yatırım yapma isteği olduğunda devreye girer.

### RL'in ötesinde tasarım deseni olarak CTDE

Eğitim olmadan bile CTDE yararlı bir mimari desendir:

- *Tasarım* sırasında, tam takım görünürlüğü varsay.
- *Runtime'da*, merkeziyetsiz yürütmeyi zorla: her agent yalnızca `o_i`'yi görür.

Desen agent başına state'i açık tutmaya ve önceden kısmi gözlemlenebilirlik üzerine düşünmeye zorlar. Çoğu üretim çoklu-agent sistemi sessizce paylaşılan state'i her yerde varsayar — CTDE disiplini bunu önler.

### Non-stationarity problemi

Birden çok agent eş zamanlı öğrendiğinde, her agent'ın ortamı (başkalarının politikalarını içerir) non-stationary'dir. Klasik tek-agent RL kanıtları kırılır. Bu derste MARL algoritmalarının hepsi bunu adresler:

- MADDPG: global critic tüm eylemleri görür, dolayısıyla değer tahmini stationary'dir.
- QMIX: value decomposition öğrenmeyi optimallik iyi tanımlandığı bir joint-Q uzayına taşır.
- MAPPO: merkezi value fonksiyonu başkalarının politika değişimlerinden gelen varyansı söndürür.

LLM-agent sistemlerinde non-stationarity "agent'ım geçen ay çalıştı, şimdi upstream'deki o başka agent değişti, benimki yanlış davranıyor" olarak tezahür eder. CTDE ile MARL eğitmek ilkesel düzeltmedir; prompt-seviye düzeltmeler daha hızlı ama daha az dayanıklıdır.

### Bu dersin KAPSAMADIĞI

Gerçek ağları eğitmek bir Faz 09 konusudur. Bu ders gradient güncellemeleri olmadan CTDE, value-decomposition ve centralized-value desenlerini gösteren senaryolu-politika versiyonlarını inşa eder. Hedef tam bir MARL kütüphanesi (PyMARL, MARLlib, RLlib multi-agent) eline almadan önce desenleri içselleştirmektir.

## İnşa Et

`code/main.py` üç desen demonstrasyonunu uygular, hepsi küçük bir 2-agent iş birlikçi grid-world üzerinde:

- Ortam: 4x4 grid üzerinde 2 agent, bir ödül peletinin biri. Ödül = herhangi bir agent pellete ulaşırsa 1; görev biter.
- `IndependentAgents` — her agent başkalarını ortam olarak ele alır. Baseline.
- `MADDPGStyle` — merkezi critic bir joint değer hesaplar; actor politikaları ondan günceller. Senaryolu politika iyileştirmesi.
- `QMIXStyle` — monoton mixer'lı value decomposition.
- `MAPPOStyle` — merkezi value fonksiyonu; politikalar paylaşılan baseline'a karşı günceller.

Dördü de aynı episode'ları çalıştırır ve ortalama hedef-adımı rapor eder. CTDE varyantları bağımsız baseline'dan daha kısa yollara yakınsar.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: bağımsız agent'lar ortalama ~6 adım alır; CTDE varyantları ~3.5 adıma yakınsar (4x4 grid için optimal 3'tür). Senaryolu politikalara rağmen desen farkı ortaya çıkar.

## Kullan

`outputs/skill-marl-picker.md` belirli bir çoklu-agent görevi için bir MARL algoritması seçen bir skill'dir: iş birlikçi vs rekabetçi, homojen vs heterojen, eylem-uzayı tipi, ölçek, ödül sinyali.

## Yayınla

Üretimde MARL nadirdir. Kullandığında:

- **MAPPO ile başla.** 2022 makalesi bunu baseline olarak kurdu; önce onu yeniden üretmek daha gösterişli yöntemleri kovalamak için haftalar tasarruf eder.
- **Her agent'ın gözlem ve eylem stream'ini log'la.** Agent başına izler olmadan MARL hata ayıklama umutsuzdur.
- **Eğitim kodunu yürütme kodundan ayır.** CTDE bir disiplindir; yürütme yolunun yalnızca `o_i`'yi görmesine izin ver.
- **Ödül şekillendirme uyarısı.** MARL ödül tasarımına son derece duyarlıdır. Şekillendirmede bir koordinasyon bug'ı ve agent'lar onu sömürmeyi öğrenir. Adversarial testler çalıştır.
- **LLM agent'lar için**, önce prompt-seviye politikaları düşün. MARL eğitimine yalnızca etkileşim verisi + ödül sinyali + altyapı hepsi mevcutken yatırım yap.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Bağımsız ve MAPPO-stili agent'lar arasındaki hedef-adımı boşluğunu ölç. Boşluk 6x6 grid'de büyür mü, küçülür mü?
2. Bir rekabetçi varyant uygula: iki agent, bir pellet, yalnızca ilk ulaşan ödül alır. Hangi desen rekabeti temiz şekilde ele alır? Tarihsel olarak MADDPG.
3. MADDPG'i (arXiv:1706.02275) Bölüm 3'ü oku. Tam critic güncelleme kuralını kendi kelimelerinle pseudocode'da sembolik olarak uygula.
4. MAPPO'yu (arXiv:2103.01955) oku. Yazarlar benchmark'larında merkezi value + PPO'nun off-policy MARL'ı neden yendiğini neden savunuyor? Üç en güçlü iddiayı listele.
5. CTDE'yi varsayımsal bir LLM-agent sistemine (ör. research agent + summarizer + coder) tasarım deseni olarak uygula. Tasarım zamanında mevcut ama runtime'da mevcut olmayan joint bilgi nedir?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| MARL | "Multi-Agent RL" | Çoklu-agent sistemleri için reinforcement learning. |
| CTDE | "Centralized Training, Decentralized Execution" | Global bilgiyle eğit; yerel politikalarla dağıt. |
| MADDPG | "Multi-Agent DDPG" | Tüm gözlemleri + eylemleri gören agent başına critic'li CTDE. |
| QMIX | "Value decomposition" | Agent başına Q'ların monoton karışımı. İş birlikçi. |
| MAPPO | "Multi-Agent PPO" | Merkezi value fonksiyonlu PPO. 2026 varsayılan baseline. |
| Value decomposition | "Bireysel Q'ların toplamı" | Agent başına Q'ların monoton fonksiyonu olarak temsil edilen joint Q. |
| Non-stationarity | "Hareketli hedefler" | Başkaları öğrendikçe her agent'ın ortamı değişir. Çekirdek MARL problemi. |
| On-policy / off-policy | "Mevcut / replay'den öğren" | PPO on-policy (MAPPO); DDPG ve Q-learning off-policy'dir. |
| SMAC | "StarCraft Multi-Agent Challenge" | İş birlikçi mikromanagement benchmark'ı; QMIX'in kendi yetiştirdiği zemin. |

## İleri Okuma

- [Lowe ve diğ. — Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments](https://arxiv.org/abs/1706.02275) — MADDPG; NeurIPS 2017
- [Rashid ve diğ. — QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent Reinforcement Learning](https://arxiv.org/abs/1803.11485) — QMIX; ICML 2018
- [Yu ve diğ. — The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games](https://arxiv.org/abs/2103.01955) — MAPPO; NeurIPS 2022
- [BAIR blog post on MAPPO](https://bair.berkeley.edu/blog/2021/07/14/mappo/) — MAPPO sonucunun okunabilir çerçevesi
- [SMAC repository](https://github.com/oxwhirl/smac) — StarCraft Multi-Agent Challenge
