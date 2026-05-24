# Sim-to-Real Transfer

> Simülatörde eğitilip donanımda başarısız olan bir policy, simülatörü ezberlemiş bir policy'dir. Domain randomization, domain adaptation ve system identification, öğrenilmiş kontrolörleri reality gap'i geçirten üç araçtır.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 9 · 08 (PPO), Faz 2 · 10 (Bias/Variance)
**Süre:** ~45 dakika

## Sorun

Gerçek bir robotu eğitmek yavaş, tehlikeli ve pahalıdır. Bir biped yürümeyi öğrenmek için milyonlarca eğitim episode'u alır; bir kez bile düşen gerçek bir biped donanımı kırar. Simülasyon sana sınırsız reset, deterministik tekrarlanabilirlik, paralel environment'lar ve fiziksel hasar olmaması sunar.

Ama simülatörler yanlıştır. Rulmanlar MuJoCo modellerinden daha çok sürtünmeye sahiptir. Kameralar simülatörün içermediği lens distorsiyonuna sahiptir. Motorların sim modellerinin %99'unun atladığı gecikme, backlash ve doygunluğu vardır. Rüzgâr, toz ve değişken aydınlatma steril rendering'te eğitilmiş bir policy'yi sabote eder. **Reality gap** — sim dağılımı ile gerçek dağılımı arasındaki sistematik fark — robotik için deployed RL'in merkezi problemidir.

*Sim-to-real dağılım kaymasına karşı sağlam* bir policy'ye ihtiyacın var. Üç tarihsel yaklaşım: simülatörü randomize et (domain randomization), policy'yi az miktarda gerçek veriyle adapte et (domain adaptation / fine-tuning) ya da gerçek sistemin parametrelerini tanımla ve onları eşleştir (system identification). 2026'da hâkim reçete üçünü de devasa paralel simülasyonla (Isaac Sim, Isaac Lab, GPU'da Mujoco MJX) birleştirir.

## Kavram

![Üç sim-to-real rejimi: domain randomization, adaptation, system identification](../assets/sim-to-real.svg)

**Domain Randomization (DR).** Tobin et al. 2017, Peng et al. 2018. Eğitim sırasında, gerçek robotta farklı olabilecek her sim parametresini randomize et: kütleler, sürtünme katsayıları, motor PD kazançları, sensör gürültüsü, kamera konumu, aydınlatma, dokular, temas modelleri. Policy "bugün hangi sim'deyim" üzerinden koşullu bir dağılım öğrenir ve tam aralık üzerinde genelleşir. Gerçek robot eğitim zarfı içine düşerse, policy çalışır.

- **Avantaj:** gerçek veri gerekmiyor. Bir reçete, birçok robot.
- **Dezavantaj:** aşırı-randomize edilmiş eğitim "evrensel" ama aşırı temkinli bir policy üretir. Çok gürültü ≈ çok regularizasyon.

**System Identification (SI).** Eğitimden önce simülatörün parametrelerini gerçek dünya verilerine fit et. Gerçek robotta kol-eklem sürtünmesini ölçebiliyorsan, onu sim'e tak. Sonra bu değerleri bekleyen bir policy eğit. Gerçek sisteme erişim ister ama reality gap'i doğrudan azaltır.

- **Avantaj:** kesin, düşük-gürültülü eğitim hedefi.
- **Dezavantaj:** kalıntı model hatası policy için görünmezdir; küçük tanımlanmamış etkiler (örn. motor deadband) hâlâ deployment'ı bozar.

**Domain Adaptation.** Sim'de eğit, az miktarda gerçek veri ile fine-tune et. İki tat:

- **Real2Sim2Real:** gerçek rollout'ları kullanarak `f(s, a, z) - f_sim(s, a)` artık simülatörünü öğren, düzeltilmiş sim'de eğit. Az gerçek veriyle gap'i kapatır.
- **Observation adaptation:** öğrenilmiş bir feature extractor (örn. GAN pixel-to-pixel) üzerinden gerçek obs → sim-benzeri obs eşleyen bir policy eğit. Kontrolör sim'de kalır.

**Privileged learning / teacher-student.** Miki et al. 2022 (ANYmal quadruped). Privileged bilgiye (ground truth sürtünme, arazi yüksekliği, IMU drift) erişimi olan bir *teacher*'ı simülasyonda eğit. Yalnızca gerçek-sensör gözlemlerini gören bir *student*'a damıt. Student privileged feature'ları geçmişten çıkarmayı öğrenir, fiziksel parametrelere karşı sağlamdır.

**Devasa paralel simülasyon.** 2024-2026. Isaac Lab, Mujoco MJX, Brax hepsi tek bir GPU'da binlerce paralel robotu koşturur. 4.096 paralel humanoid'le PPO saatler içinde yıllarca deneyim toplar. "Reality gap" eğitim dağılımı genişledikçe küçülür; bu 4.096 env'in her birinde farklı randomize parametreler olduğunda DR neredeyse bedava olur.

**Gerçek-dünya 2026 reçetesi (quadruped yürüme örneği):**

1. Domain-randomize yerçekimi, sürtünme, motor kazançları, yükle devasa paralel sim.
2. Privileged bilgi (arazi haritası, vücut hızı ground truth) ile teacher policy eğitildi.
3. Yalnızca proprioception (bacak eklem encoder'ları) kullanan teacher'dan damıtılmış student policy.
4. Opsiyonel olarak gerçek IMU üzerinde autoencoder ile observation adaptation.
5. Deploy et. 10+ environment üzerinde zero-shot. Başarısız olursa, güvenlik-kısıtlı PPO ile dakikalarca gerçek-dünya fine-tuning'i yap.

## İnşa Et

Bu dersin kodu, *gürültülü* geçişli bir GridWorld üzerinde domain randomization'ın minik bir gösterimidir. "Sim"de randomize edilmiş slip olasılıklarını deneyimleyen bir policy eğitiyor ve "gerçek"te eğitim sırasında hiç görmediği bir slip seviyesinde değerlendiriyoruz. Şekil doğrudan MuJoCo-to-hardware transferine eşlenir.

### Adım 1: parametrize sim

```python
def step(state, action, slip):
    if rng.random() < slip:
        action = random_perpendicular(action)
    ...
```

`slip` simülatörün açığa çıkardığı bir parametredir. Gerçek robotikte bu sürtünme, kütle, motor kazancı olabilir — sim ile gerçek arasında değişen herhangi bir şey.

### Adım 2: DR ile eğit

Her episode başında, `slip ~ Uniform[0.0, 0.4]` örnekle. PPO / Q-learning / herhangi bir şey eğit. Bunu birçok episode için yap.

### Adım 3: "gerçek" slip'lerde zero-shot değerlendir

`slip ∈ {0.0, 0.1, 0.2, 0.3, 0.5, 0.7}` üzerinde değerlendir. İlk dördü eğitim desteğinin içinde; `0.5` ve `0.7` dışında. DR-eğitilmiş bir policy destek içinde optimuma yakın kalmalı ve dışında zarif şekilde bozulmalı. Sabit-slip-eğitilmiş bir policy eğitim slip'inin dışında kırılgan olacak.

### Adım 4: dar eğitim ile karşılaştır

Yalnızca `slip = 0.0` ile ikinci bir policy eğit. Aynı `slip` taraması üzerinde değerlendir. Gerçek slip > 0 olur olmaz felaketsel bir düşüş görmelisin.

## Tuzaklar

- **Çok fazla randomizasyon.** `slip ∈ [0, 0.9]` üzerinde eğit ve policy'in o kadar risk kaçınan olur ki optimal yolu hiç denemez. *Beklenen* gerçek-dünya dağılımıyla eşleştir, "her şey olabilir" ile değil.
- **Çok az randomizasyon.** İnce bir dilim üzerinde eğit ve policy hiç genelleştiremez. Policy iyileştikçe dağılımı genişleten uyarlanır curriculum kullan (Automatic Domain Randomization).
- **Yanlış-tanımlanmış parametre uzayı.** Yanlış şeyi randomize et (gerçek gap motor gecikmesiyken kamera tonu) ve DR yardımcı olmaz. Önce gerçek robotu profilliendir.
- **Privileged info sızıntısı.** Aksiyonlar için yalnızca gözlemleri değil küresel state'i kullanan bir teacher, yetişemeyen bir student üretebilir. Teacher policy'sinin gözlem geçmişi verildiğinde student tarafından gerçeklenebilir olduğundan emin ol.
- **Sim-to-sim transfer başarısızlığı.** Policy'in daha zor bir sim varyantına sağlam değilse, gerçek dünyaya da sağlam olmayacak. Deploy etmeden önce daima bir held-out sim varyantında test et.
- **Gerçek-dünya güvenlik zarfı yok.** Sim'de çalışan ve düşük seviyeli bir güvenlik kalkanı olmadan "gerçekte çalışan" bir policy hâlâ donanımı bozabilir. Öğrenilmemiş bir kontrolörde rate limit'ler, tork limitleri, eklem limitleri ekle.

## Kullan

2026 sim-to-real stack'i:

| Alan | Stack |
|------|-------|
| Bacaklı lokomosyon (ANYmal, Spot, humanoid) | Isaac Lab + DR + privileged teacher / student |
| Manipülasyon (becerikli eller, pick-and-place) | Isaac Lab + DR + görü için DR-GAN |
| Otonom sürüş | CARLA / NVIDIA DRIVE Sim + DR + gerçek fine-tune |
| Drone yarışı | RotorS / Flightmare + DR + online adaptation |
| Parmak/elde manipülasyon | OpenAI Dactyl (görülmemiş ölçekte DR) |
| Endüstriyel kollar | MuJoCo-Warp + SI + küçük gerçek fine-tune |

Her ölçekteki kontrol için iş akışı tutarlıdır: sim'i mümkün olduğunca iyi fit et, fit edemediğini randomize et, devasa policy'ler eğit, damıt, güvenlik kalkanıyla deploy et.

## Yayınla

`outputs/skill-sim2real-planner.md` olarak kaydet:

```markdown
---
name: sim2real-planner
description: Plan a sim-to-real transfer pipeline for a given robot + task, covering DR, SI, and safety.
version: 1.0.0
phase: 9
lesson: 11
tags: [rl, sim2real, robotics, domain-randomization]
---

Given a robot platform, a task, and access to real hardware time, output:

1. Reality gap inventory. Suspected sources ranked by expected impact (contact, sensing, actuation delay, vision).
2. DR parameters. Exact list, ranges, distribution. Justify each range against real measurements.
3. SI steps. Which parameters to measure; measurement method.
4. Teacher/student split. What privileged info the teacher uses; what obs the student uses.
5. Safety envelope. Low-level limits, emergency stops, backup controller.

Refuse to deploy without (a) a zero-shot sim-variant test, (b) a safety shield, (c) a rollback plan. Flag any DR range wider than 3× measured real variability as likely over-randomized.
```

## Alıştırmalar

1. **Kolay.** Sabit-slip GridWorld'de (slip=0.0) bir Q-learning agent'ı eğit. slip ∈ {0.0, 0.1, 0.3, 0.5} üzerinde değerlendir. Return vs slip çiz.
2. **Orta.** `slip ~ Uniform[0, 0.3]` örnekleyen bir DR Q-learning agent'ı eğit. Aynı taramayı değerlendir. DR slip=0.5'te (dağılım-dışı) ne kadar kazanç sağlıyor?
3. **Zor.** Bir curriculum uygula: slip=0.0 ile başla, policy optimumun %90'ına her ulaştığında DR aralığını genişlet. Sabit DR baseline'ına karşı slip=0.3'e zero-shot ulaşmak için toplam environment adımlarını ölç.

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Reality gap | "Sim-to-real farkı" | Eğitim ve deployment fizik/duyumlama arasındaki dağılım kayması. |
| Domain randomization (DR) | "Rastgele sim'ler üzerinde eğit" | Eğitim sırasında sim parametrelerini randomize et, böylece policy genelleşir. |
| System identification (SI) | "Gerçeği ölç ve sim'i fit et" | Gerçek fiziksel parametreleri tahmin et; sim'i eşleşmesi için ayarla. |
| Domain adaptation | "Gerçek veri üzerinde fine-tune" | Sim eğitiminden sonra küçük gerçek-dünya fine-tune; obs ya da dinamikleri adapte edebilir. |
| Privileged info | "Teacher için ground truth" | Yalnızca sim'in sahip olduğu bilgi; student bunu gözlem geçmişinden çıkarmalı. |
| Teacher/student | "Privileged'i damıt -> gözlemlenebilir" | Kısayollarla eğitilmiş teacher; student onlar olmadan taklit etmeyi öğrenir. |
| ADR | "Automatic Domain Randomization" | Policy iyileştikçe DR aralıklarını genişleten curriculum. |
| Real2Sim | "Gerçek veriyle gap'i kapat" | Sim'in gerçek rollout'ları taklit etmesi için artık öğren. |

## İleri Okuma

- [Tobin et al. (2017). Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World](https://arxiv.org/abs/1703.06907) — orijinal DR makalesi (robotik için görü).
- [Peng et al. (2018). Sim-to-Real Transfer of Robotic Control with Dynamics Randomization](https://arxiv.org/abs/1710.06537) — dinamikler için DR, quadruped lokomosyon.
- [OpenAI et al. (2019). Solving Rubik's Cube with a Robot Hand](https://arxiv.org/abs/1910.07113) — Dactyl, ölçekte ADR.
- [Miki et al. (2022). Learning robust perceptive locomotion for quadrupedal robots in the wild](https://www.science.org/doi/10.1126/scirobotics.abk2822) — ANYmal için teacher-student.
- [Makoviychuk et al. (2021). Isaac Gym: High Performance GPU Based Physics Simulation for Robot Learning](https://arxiv.org/abs/2108.10470) — 2025-2026 deployment'larını süren devasa paralel sim.
- [Akkaya et al. (2019). Automatic Domain Randomization](https://arxiv.org/abs/1910.07113) — ADR curriculum yöntemi.
- [Sutton & Barto (2018). Ch. 8 — Planning and Learning with Tabular Methods](http://incompleteideas.net/book/RLbook2020.pdf) — modern sim-to-real pipeline'larının altında yatan Dyna çerçevelemesi (planlama + rollout'lar için bir model kullan).
- [Zhao, Queralta & Westerlund (2020). Sim-to-Real Transfer in Deep Reinforcement Learning for Robotics: a Survey](https://arxiv.org/abs/2009.13303) — benchmark sonuçlarıyla sim-to-real yöntemlerinin taksonomisi.
