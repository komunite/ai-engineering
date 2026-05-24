# Temporal Difference — Q-Learning ve SARSA

> Monte Carlo episode'un bitmesini bekler. TD bir sonraki value tahminini bootstrap'leyerek her adımdan sonra günceller. Q-learning off-policy ve iyimserdir; SARSA on-policy ve temkinlidir. İkisi de tek satır kod. İkisi de bu fazdaki her derin-RL yönteminin temelini oluşturur.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 01 (MDP'ler), Faz 9 · 02 (Dinamik Programlama), Faz 9 · 03 (Monte Carlo)
**Süre:** ~75 dakika

## Sorun

Monte Carlo çalışır ama iki pahalı talebi vardır. Sonlanan episode'lara ihtiyaç duyar ve yalnızca son return geldikten sonra günceller. Episode'un 1.000 adımsa, MC herhangi bir şeyi güncellemek için 1.000 adım bekler. Yüksek-varyanslı, düşük-biaslı ve pratikte yavaştır.

Dinamik programlamanın tersi profil var — sıfır-varyans bootstrap'li backup'lar — ama bilinen bir model ister.

Temporal difference (TD) öğrenmesi farkı böler. Tek bir geçişten `(s, a, r, s')`, tek-adım bir hedef `r + γ V(s')` oluştur ve `V(s)`'yi ona doğru ittir. Model yok. Tam episode yok. RHS'de yaklaşık bir `V` kullanmaktan gelen bias, ama MC'den çarpıcı şekilde daha düşük varyans ve birinci adımdan online güncellemeler.

Modern RL'in döndüğü eksen budur — DQN, A2C, PPO, SAC. Faz 9'un geri kalanı, bu derste yazacağın tek-adım TD güncellemesinin üstüne kurulu function approximation ve tricks katmanları.

## Kavram

![Q-learning vs SARSA: off-policy max vs on-policy Q(s', a')](../assets/td.svg)

**V için TD(0) güncellemesi:**

`V(s) ← V(s) + α [r + γ V(s') - V(s)]`

Köşeli parantez içindeki ifade TD hatasıdır `δ = r + γ V(s') - V(s)`. MC'deki `G_t - V(s_t)`'nin online analoğudur. Yakınsama `α`'nın Robbins-Monro'yu sağlamasını (`Σ α = ∞`, `Σ α² < ∞`) ve tüm state'lerin sonsuz sıklıkta ziyaret edilmesini gerektirir.

**Q-learning.** Control için off-policy bir TD yöntemi:

`Q(s, a) ← Q(s, a) + α [r + γ max_{a'} Q(s', a') - Q(s, a)]`

`max`, agent gerçekte hangi aksiyonu alırsa alsın, `s'`'den itibaren *greedy* policy'nin izleneceğini varsayar. Bu ayrıştırma Q-learning'in agent ε-greedy ile explore ederken `Q*`'ı öğrenmesini sağlar. Mnih et al. (2015) bunu Atari üzerinde derin Q-learning'e dönüştürdü (Ders 05).

**SARSA.** On-policy bir TD yöntemi:

`Q(s, a) ← Q(s, a) + α [r + γ Q(s', a') - Q(s, a)]`

İsim `(s, a, r, s', a')` tuple'ından geliyor. SARSA, agent'ın bir sonraki gerçekten *aldığı* `a'` aksiyonunu kullanır, greedy `argmax`'i değil. Hangi ε-greedy `π` koşuyorsa `Q^π`'a yakınsar, ki bu da `ε → 0` limitinde `Q*` olur.

**Cliff-walking farkı.** Klasik cliff-walking görevinde (uçurumdan düş = ödül -100), Q-learning uçurum kenarı boyunca optimal yolu öğrenir ama exploration sırasında zaman zaman cezayı alır. SARSA, exploration gürültüsünü Q-value'sunda hesaba kattığı için uçurumdan bir adım uzakta daha güvenli bir yol öğrenir. Eğitimle, `ε → 0`'da ikisi de optimuma ulaşır. Pratikte önemli: deployment'ta gerçekten exploration oluyorsa, SARSA'nın davranışı daha muhafazakârdır.

**Expected SARSA.** `Q(s', a')`'yı `π` altındaki beklenen değeriyle değiştir:

`Q(s, a) ← Q(s, a) + α [r + γ Σ_{a'} π(a'|s') Q(s', a') - Q(s, a)]`

SARSA'dan daha düşük varyans (`a'`'nın örneklemesi yok), aynı on-policy hedef. Modern ders kitaplarında genelde varsayılan.

**n-step TD ve TD(λ).** Bootstrap'lemeden önce `n` adım bekleyerek TD(0) ile MC arasında interpolasyon yap. `n=1` TD'dir, `n=∞` MC'dir. TD(λ), tüm `n`'ler üzerinde `(1-λ)λ^{n-1}` geometrik ağırlıklarla ortalama alır. Çoğu derin-RL `n`'yi 3 ile 20 arasında kullanır.

## İnşa Et

### Adım 1: ε-greedy policy üzerinde SARSA

```python
def sarsa(env, episodes, alpha=0.1, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})

    def choose(s):
        if random() < epsilon:
            return choice(ACTIONS)
        return max(Q[s], key=Q[s].get)

    for _ in range(episodes):
        s = env.reset()
        a = choose(s)
        while True:
            s_next, r, done = env.step(s, a)
            a_next = choose(s_next) if not done else None
            target = r + (gamma * Q[s_next][a_next] if not done else 0.0)
            Q[s][a] += alpha * (target - Q[s][a])
            if done:
                break
            s, a = s_next, a_next
    return Q
```

Sekiz satır. Q-learning'den *tek* fark hedef satırı.

### Adım 2: Q-learning

```python
def q_learning(env, episodes, alpha=0.1, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
    for _ in range(episodes):
        s = env.reset()
        while True:
            a = choose(s, Q, epsilon)
            s_next, r, done = env.step(s, a)
            target = r + (gamma * max(Q[s_next].values()) if not done else 0.0)
            Q[s][a] += alpha * (target - Q[s][a])
            if done:
                break
            s = s_next
    return Q
```

`max`, hedefi davranıştan ayrıştırır. O tek sembol, on-policy ile off-policy arasındaki farktır.

### Adım 3: öğrenme eğrileri

100 episode başına ortalama return'ü takip et. Q-learning basit deterministik GridWorld'de daha hızlı yakınsar; SARSA cliff-walking'te daha muhafazakârdır. `code/main.py`'daki 4×4 GridWorld'de ikisi de `α=0.1, ε=0.1` ile ~2.000 episode sonrası neredeyse-optimal.

### Adım 4: DP gerçeğiyle karşılaştır

`Q*`'ı almak için value iteration'ı (Ders 02) koştur. `max_{s,a} |Q_learned(s,a) - Q*(s,a)|`'yı kontrol et. Sağlıklı bir tablo formundaki TD agent'ı 4×4 GridWorld'de 10.000 episode sonrası `~0.5` içine girer.

## Tuzaklar

- **Başlangıç Q değerleri önemli.** İyimser başlatma (negatif-ödüllü bir görev için `Q = 0`) exploration'ı teşvik eder. Kötümser başlatma greedy policy'yi sonsuza dek hapsedebilir.
- **α scheduling.** Sabit `α` non-stationary problemler için iyidir. Bozulan `α_n = 1/n` teoride yakınsama verir ama pratikte çok yavaştır — `α`'yı `[0.05, 0.3]`'e sabitle ve öğrenme eğrisini takip et.
- **ε scheduling.** Yüksek başla (`ε=1.0`), `ε=0.05`'e bozul. "GLIE" (Greedy in the Limit with Infinite Exploration) yakınsama koşuludur.
- **Q-learning'de max bias.** `max` operatörü `Q` gürültülü olduğunda yukarı yönlü biased'tır. Aşırı-tahmine yol açar — Hasselt'in Double Q-learning'i (Ders 05'teki DDQN'de kullanılır) bunu iki Q tablosuyla düzeltir.
- **Sonlanmayan episode'lar.** TD terminal'siz öğrenebilir, ama ya adımları sınırlamak ya da sınırda bootstrap'i doğru ele almak gerekir. Standart: sınırı non-terminal say, bootstrap'lemeye devam et.
- **State hash'leme.** State'ler tuple/tensor ise, hashable bir anahtar kullan (list değil tuple; ham float değil yuvarlanmış float tuple'ı).

## Kullan

2026 TD manzarası:

| Görev | Yöntem | Sebep |
|-------|--------|-------|
| Küçük tablo formundaki environment'lar | Q-learning | Optimal policy'yi doğrudan öğrenir. |
| On-policy güvenlik-kritik | SARSA / Expected SARSA | Exploration sırasında muhafazakâr. |
| Yüksek boyutlu state | DQN (Faz 9 · 05) | Replay ve target net ile neural-net Q-fonksiyonu. |
| Sürekli aksiyonlar | SAC / TD3 (Faz 9 · 07) | Bir Q-network üzerinde TD güncellemesi; policy net aksiyonları üretir. |
| LLM RL (reward-model-tabanlı) | PPO / GRPO (Faz 9 · 08, 12) | GAE üzerinden TD-tarzı advantage'lı actor-critic. |
| Offline RL | CQL / IQL (Faz 9 · 08) | Muhafazakâr regularizasyonlu Q-learning. |

2026 makalelerinde okuduğun "RL"in yüzde doksanı Q-learning veya SARSA'nın bir varyasyonudur. Daha derinine girmeden önce tablo formundaki güncellemeyi parmaklarında anla.

## Yayınla

`outputs/skill-td-agent.md` olarak kaydet:

```markdown
---
name: td-agent
description: Pick between Q-learning, SARSA, Expected SARSA for a tabular or small-feature RL task.
version: 1.0.0
phase: 9
lesson: 4
tags: [rl, td-learning, q-learning, sarsa]
---

Given a tabular or small-feature environment, output:

1. Algorithm. Q-learning / SARSA / Expected SARSA / n-step variant. One-sentence reason tied to on-policy vs off-policy and variance.
2. Hyperparameters. α, γ, ε, decay schedule.
3. Initialization. Q_0 value (optimistic vs zero) and justification.
4. Convergence diagnostic. Target learning curve, `|Q - Q*|` check if DP is possible.
5. Deployment caveat. How will exploration behave at inference? Is SARSA's conservatism needed?

Refuse to apply tabular TD to state spaces > 10⁶. Refuse to ship a Q-learning agent without a max-bias caveat. Flag any agent trained with ε held at 1.0 throughout (no exploitation phase).
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld üzerinde Q-learning ve SARSA uygula. 2.000 episode için öğrenme eğrilerini (100 episode başına ortalama return) çiz. Hangisi daha hızlı yakınsıyor?
2. **Orta.** Bir cliff-walking environment'ı kur (4×12, son satır -100 ödüllü ve başlangıca reset olan uçurum). Q-learning ve SARSA'nın son policy'lerini karşılaştır. Aldıkları yolların ekran görüntüsünü al. Hangisi uçuruma daha yakın?
3. **Zor.** Double Q-learning uygula. Gürültülü-ödüllü bir GridWorld'de (adım ödülüne eklenen Gauss gürültüsü σ=5), Q-learning'in `V*(0,0)`'ı anlamlı bir miktarda aşırı-tahmin ederken Double Q-learning'in etmediğini göster.

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| TD hatası | "Güncelleme sinyali" | `δ = r + γ V(s') - V(s)`, bootstrap'lenmiş artık. |
| TD(0) | "Tek-adım TD" | Yalnızca bir sonraki state tahminini kullanarak her geçişten sonra güncelle. |
| Q-learning | "Off-policy RL 101" | Sonraki state aksiyonları üzerinde `max`'li TD güncellemesi; davranış policy'sinden bağımsız `Q*`'ı öğrenir. |
| SARSA | "On-policy Q-learning" | Gerçek sonraki aksiyonu kullanan TD güncellemesi; şu anki ε-greedy π için `Q^π`'yi öğrenir. |
| Expected SARSA | "Düşük-varyans SARSA" | Örneklenen `a'`'yı π altındaki beklentisiyle değiştir. |
| GLIE | "Doğru exploration scheduling" | Greedy in the Limit with Infinite Exploration; Q-learning yakınsaması için gerekli. |
| Bootstrapping | "Hedefte şu anki tahmini kullanmak" | TD'yi MC'den ayıran şey. Bias kaynağı ama devasa varyans azaltımı. |
| Maximization bias | "Q-learning aşırı tahmin ediyor" | Gürültülü tahminler üzerinde `max` yukarı yönlü biased'tır; Double Q-learning ile düzeltilir. |

## İleri Okuma

- [Watkins & Dayan (1992). Q-learning](https://link.springer.com/article/10.1007/BF00992698) — orijinal makale ve yakınsama kanıtı.
- [Sutton & Barto (2018). Ch. 6 — Temporal-Difference Learning](http://incompleteideas.net/book/RLbook2020.pdf) — TD(0), SARSA, Q-learning, Expected SARSA.
- [Hasselt (2010). Double Q-learning](https://papers.nips.cc/paper_files/paper/2010/hash/091d584fced301b442654dd8c23b3fc9-Abstract.html) — maximization bias için düzeltme.
- [Seijen, Hasselt, Whiteson, Wiering (2009). A Theoretical and Empirical Analysis of Expected SARSA](https://ieeexplore.ieee.org/document/4927542) — expected SARSA motivasyonu.
- [Rummery & Niranjan (1994). On-line Q-learning using connectionist systems](https://www.researchgate.net/publication/2500611_On-Line_Q-Learning_Using_Connectionist_Systems) — SARSA terimini ortaya atan makale (o zaman "modified connectionist Q-learning" deniyordu).
- [Sutton & Barto (2018). Ch. 7 — n-step Bootstrapping](http://incompleteideas.net/book/RLbook2020.pdf) — TD(0)'ı TD(n)'e genelleştirir, Q-learning'den eligibility trace'lere ve sonra PPO'daki GAE'ye giden yol.
