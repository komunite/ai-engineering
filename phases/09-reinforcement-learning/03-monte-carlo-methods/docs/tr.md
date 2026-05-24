# Monte Carlo Yöntemleri — Tam Episode'lardan Öğrenme

> Dinamik programlama bir model ister. Monte Carlo episode'lardan başka hiçbir şey istemez. Policy'yi koştur, return'leri izle, ortalamasını al. RL'deki en basit fikir — ve sonrasındaki her şeyi açan o.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 01 (MDP'ler), Faz 9 · 02 (Dinamik Programlama)
**Süre:** ~75 dakika

## Sorun

Dinamik programlama zariftir, ama her state ve aksiyon için `P(s' | s, a)`'yı sorgulayabildiğini varsayar. Gerçek dünyada neredeyse hiçbir şey böyle çalışmaz. Bir robot, bir eklem torkunun ardından kamera pikselleri üzerindeki dağılımı analitik olarak hesaplayamaz. Bir fiyatlandırma algoritması, her olası müşteri reaksiyonu üzerinde integral alamaz. Bir LLM, bir token'dan sonraki tüm olası devamları sıralayamaz.

Sadece environment'tan *örnekleme* yeteneğine ihtiyaç duyan bir yönteme ihtiyacın var. Policy'yi koştur. Bir trajectory al `s_0, a_0, r_1, s_1, a_1, r_2, …, s_T`. Value'ları tahmin etmek için kullan. Bu Monte Carlo.

DP'den MC'ye geçiş felsefi olarak önemlidir: *bilinen model + tam backup*'tan *örneklenmiş rollout'lar + ortalanmış return*'e geçiyoruz. Varyans atlar, ama uygulanabilirlik patlar. Bu dersten sonraki her RL algoritması — TD, Q-learning, REINFORCE, PPO, GRPO — özünde bir Monte Carlo tahmincisidir, bazen üzerine bootstrapping katmanlanmış.

## Kavram

![Monte Carlo: rollout, return'leri hesapla, ortala; first-visit vs every-visit](../assets/monte-carlo.svg)

**Temel fikir, tek satırda:** `V^π(s) = E_π[G_t | s_t = s] ≈ (1/N) Σ_i G^{(i)}(s)`, burada `G^{(i)}(s)`, `π` policy'si altında `s` ziyaretlerinin ardından gözlenen return'lerdir.

**First-visit vs every-visit MC.** `s` state'ini birden çok kez ziyaret eden bir episode verildiğinde, first-visit MC yalnızca ilk ziyaretten gelen return'ü sayar; every-visit MC tüm ziyaretleri sayar. İkisi de limitte yansızdır (unbiased). First-visit analiz etmesi daha basittir (iid örnekler). Every-visit episode başına daha çok veri kullanır ve pratikte tipik olarak daha hızlı yakınsar.

**Inkremental ortalama.** Tüm return'leri saklamak yerine, koşan ortalamayı güncelle:

`V_n(s) = V_{n-1}(s) + (1/n) [G_n - V_{n-1}(s)]`

Yeniden organize et: `V_new = V_old + α · (target - V_old)`, `α = 1/n`. `1/n`'i sabit step-size `α ∈ (0, 1)` ile değiştir ve `π`'deki değişiklikleri takip eden non-stationary bir MC tahmincisi elde edersin. O hamle MC'den TD'ye ve her modern RL algoritmasına geçişin tamamıdır.

**Exploration artık bir sorun.** DP sıralama ile her state'e dokundu. MC yalnızca policy'nin ziyaret ettiği state'leri görür. `π` deterministikse, state uzayının tüm bölgeleri asla örneklenmez ve value tahminleri sonsuza dek sıfırda kalır. Tarihsel sırayla üç çözüm:

1. **Exploring starts.** Her episode'u rastgele bir (s, a) çiftinden başlat. Kapsamayı garanti eder; pratikte gerçekçi değildir (bir robotu rastgele bir state'e "reset" edemezsin).
2. **ε-greedy.** Şu anki Q'ya göre greedy davran, ama `ε` olasılıkla rastgele bir aksiyon seç. Asimptotik olarak tüm state-aksiyon çiftleri örneklenir.
3. **Off-policy MC.** Bir davranış policy'si `μ` altında veri topla, importance sampling ile target policy `π` hakkında öğren. Yüksek varyans, ama DQN gibi replay-buffer yöntemlerine giden köprü.

**Monte Carlo Control.** Değerlendir → iyileştir → değerlendir, tıpkı policy iteration gibi, ama değerlendirme sampling tabanlı:

1. `π`'yi koştur, bir episode al.
2. Gözlenen return'lerden `Q(s, a)`'yı güncelle.
3. `π`'yi `Q`'ya göre ε-greedy yap.
4. Tekrarla.

Hafif koşullar altında olasılık 1 ile `Q*` ve `π*`'a yakınsar (her çift sonsuz sıklıkta ziyaret edilir, `α` Robbins-Monro'yu sağlar).

## İnşa Et

### Adım 1: rollout → (s, a, r) listesi

```python
def rollout(env, policy, max_steps=200):
    trajectory = []
    s = env.reset()
    for _ in range(max_steps):
        a = policy(s)
        s_next, r, done = env.step(s, a)
        trajectory.append((s, a, r))
        s = s_next
        if done:
            break
    return trajectory
```

Model yok, yalnızca `env.reset()` ve `env.step(s, a)`. Gym environment ile aynı arayüz ama soyulmuş.

### Adım 2: return'leri hesapla (ters sweep)

```python
def returns_from(trajectory, gamma):
    returns = []
    G = 0.0
    for _, _, r in reversed(trajectory):
        G = r + gamma * G
        returns.append(G)
    return list(reversed(returns))
```

Tek pass, `O(T)`. `G_t = r_{t+1} + γ G_{t+1}` geri özyinelemesi yeniden-toplamayı önler.

### Adım 3: first-visit MC değerlendirmesi

```python
def mc_policy_evaluation(env, policy, episodes, gamma=0.99):
    V = defaultdict(float)
    counts = defaultdict(int)
    for _ in range(episodes):
        trajectory = rollout(env, policy)
        returns = returns_from(trajectory, gamma)
        seen = set()
        for t, ((s, _, _), G) in enumerate(zip(trajectory, returns)):
            if s in seen:
                continue
            seen.add(s)
            counts[s] += 1
            V[s] += (G - V[s]) / counts[s]
    return V
```

Üç satır işi yapar: state'i ilk ziyarette görüldü olarak işaretle, sayacı artır, koşan ortalamayı güncelle.

### Adım 4: ε-greedy MC control (on-policy)

```python
def mc_control(env, episodes, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
    counts = defaultdict(lambda: {a: 0 for a in ACTIONS})

    def policy(s):
        if random() < epsilon:
            return choice(ACTIONS)
        return max(Q[s], key=Q[s].get)

    for _ in range(episodes):
        trajectory = rollout(env, policy)
        returns = returns_from(trajectory, gamma)
        seen = set()
        for (s, a, _), G in zip(trajectory, returns):
            if (s, a) in seen:
                continue
            seen.add((s, a))
            counts[s][a] += 1
            Q[s][a] += (G - Q[s][a]) / counts[s][a]
    return Q, policy
```

### Adım 5: DP altın standardı ile karşılaştır

`V^π`'nin MC tahmini, episode → ∞ olurken Ders 02'deki DP sonucuyla uyuşmalı. Pratikte: 4×4 GridWorld'de 50.000 episode seni DP cevabının `~0.1` içine sokar.

## Tuzaklar

- **Sonsuz episode'lar.** MC episode'ların *sonlanmasını* gerektirir. Policy'n sonsuza dek döngüye girebiliyorsa, `max_steps`'i sınırla ve sınırı zımni başarısızlık olarak ele al. Random policy ile GridWorld rutin olarak zaman aşımına uğrar — bu normal, sadece doğru saydığından emin ol.
- **Varyans.** MC tam return kullanır. Uzun episode'larda, varyans devasadır — sondaki tek bir şanssız ödül `V(s_0)`'ı aynı miktarda kaydırır. TD yöntemleri (Ders 04) bunu bootstrapping ile keser.
- **State kapsama.** Beraberlikli taze bir Q üzerinde greedy MC yalnızca bir aksiyonu denecektir. *Mutlaka* explore etmelisin (ε-greedy, exploring starts, UCB).
- **Non-stationary policy'ler.** `π` değişiyorsa (MC control'deki gibi), eski return'ler farklı bir policy'dendir. Sabit-α MC bunu halleder; sample-average MC halletmez.
- **Off-policy importance sampling.** `π(a|s)/μ(a|s)` ağırlıkları bir trajectory boyunca çarpılır. Varyans ufukla patlar. Per-decision weighted IS ile sınırla ya da TD'ye geç.

## Kullan

Monte Carlo yöntemlerinin 2026'daki rolü:

| Kullanım durumu | Neden MC |
|-----------------|----------|
| Kısa-ufuklu oyunlar (blackjack, poker) | Episode'lar doğal olarak sonlanır; return'ler temizdir. |
| Loglanmış bir policy'nin offline değerlendirmesi | Saklanmış trajectory'ler üzerinde ortalama indirilmiş return'ler. |
| Monte Carlo Tree Search (AlphaZero) | Ağaç yapraklarından MC rollout'ları seçimi yönlendirir. |
| LLM RL değerlendirmesi | Belirli bir policy için örneklenmiş tamamlamalar üzerinde ortalama ödülü hesapla. |
| PPO'da baseline tahmini | `A_t = G_t - V(s_t)` advantage hedefi bir MC `G_t` kullanır. |
| RL öğretmek | Gerçekten çalışan en basit algoritma — özü görmek için bootstrapping'i çıkar. |

Modern derin-RL algoritmaları (PPO, SAC) saf MC (tam return) ile saf TD (tek-adım bootstrap) arasında `n`-step return'ler veya GAE üzerinden interpolasyon yapar. Her iki uç da aynı tahmincinin örnekleridir.

## Yayınla

`outputs/skill-mc-evaluator.md` olarak kaydet:

```markdown
---
name: mc-evaluator
description: Evaluate a policy via Monte Carlo rollouts and produce a convergence report with DP-comparison if available.
version: 1.0.0
phase: 9
lesson: 3
tags: [rl, monte-carlo, evaluation]
---

Given an environment (episodic, with reset+step API) and a policy, output:

1. Method. First-visit vs every-visit MC. Reason.
2. Episode budget. Target number, variance diagnostic, expected standard error.
3. Exploration plan. ε schedule (if needed) or exploring starts.
4. Gold-standard comparison. DP-optimal V* if tabular; otherwise a bound from a Q-learning / PPO baseline.
5. Termination check. Max-step cap, timeouts, handling of non-terminating trajectories.

Refuse to run MC on non-episodic tasks without a finite horizon cap. Refuse to report V^π estimates from fewer than 100 episodes per state for tabular tasks. Flag any policy with zero-variance actions as an exploration risk.
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld'de uniform-random policy'nin first-visit MC değerlendirmesini uygula. 10.000 episode koştur. `V(0,0)`'ı episode sayısının fonksiyonu olarak DP cevabına karşı çiz.
2. **Orta.** `ε ∈ {0.01, 0.1, 0.3}` ile ε-greedy MC control uygula. 20.000 episode sonrası ortalama return'ü karşılaştır. Eğri neye benziyor? Bias-variance dengesi nerede yaşıyor?
3. **Zor.** Importance sampling ile *off-policy* MC uygula: uniform-random policy `μ` altında veri topla, deterministik optimal policy `π` için `V^π`'yi tahmin et. Plain IS vs per-decision IS vs weighted IS'yi karşılaştır. Hangisinin en düşük varyansı var?

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Monte Carlo | "Rastgele örnekleme" | Beklentileri dağılımdan iid örnekler üzerinde ortalama alarak tahmin et. |
| Return `G_t` | "Gelecek ödül" | `t` adımından episode sonuna kadar indirilmiş ödüllerin toplamı: `Σ_{k≥0} γ^k r_{t+k+1}`. |
| First-visit MC | "Her state'i bir kez say" | Bir episode'da yalnızca ilk ziyaret value tahminine katkıda bulunur. |
| Every-visit MC | "Tüm ziyaretleri kullan" | Her ziyaret katkıda bulunur; biraz biased ama daha sample-efficient. |
| ε-greedy | "Exploration gürültüsü" | `1-ε` olasılıkla greedy aksiyon seç; `ε` olasılıkla rastgele aksiyon. |
| Importance sampling | "Yanlış dağılımdan örneklemeyi düzeltme" | `μ` verisinden `V^π`'yi tahmin etmek için return'leri `π(a|s)/μ(a|s)` çarpımlarıyla yeniden ağırlıklandır. |
| On-policy | "Kendi verimden öğren" | Target policy = davranış policy'si. Düz MC, PPO, SARSA. |
| Off-policy | "Başkasının verisinden öğren" | Target policy ≠ davranış policy'si. Importance-sampled MC, Q-learning, DQN. |

## İleri Okuma

- [Sutton & Barto (2018). Ch. 5 — Monte Carlo Methods](http://incompleteideas.net/book/RLbook2020.pdf) — kanonik ele alış.
- [Singh & Sutton (1996). Reinforcement Learning with Replacing Eligibility Traces](https://link.springer.com/article/10.1007/BF00114726) — first-visit vs every-visit analizi.
- [Precup, Sutton, Singh (2000). Eligibility Traces for Off-Policy Policy Evaluation](http://incompleteideas.net/papers/PSS-00.pdf) — off-policy MC ve varyans kontrolü.
- [Mahmood et al. (2014). Weighted Importance Sampling for Off-Policy Learning](https://arxiv.org/abs/1404.6362) — modern düşük-varyans IS tahmincileri.
- [Tesauro (1995). TD-Gammon, A Self-Teaching Backgammon Program](https://dl.acm.org/doi/10.1145/203330.203343) — MC/TD self-play'in süperinsan oyununa yakınsadığının ilk büyük-ölçekli ampirik gösterimi; bu fazın ikinci yarısındaki her dersin kavramsal öncüsü.
