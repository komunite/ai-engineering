# Dinamik Programlama — Policy Iteration ve Value Iteration

> Dinamik programlama, hile yaparak RL'dir. Geçiş ve ödül fonksiyonlarını zaten biliyorsun; sadece `V` veya `π` hareket etmeyi bırakana kadar Bellman denklemini iterate edersin. Her sampling tabanlı yöntemin yaklaşmaya çalıştığı benchmark budur.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 01 (MDP'ler)
**Süre:** ~75 dakika

## Sorun

Bilinen modeli olan bir MDP'in var: herhangi bir state-aksiyon çifti için `P(s' | s, a)` ve `R(s, a, s')` sorgulayabilirsin. Bir envanter yöneticisi talep dağılımını bilir. Bir tahta oyununun deterministik geçişleri vardır. Bir gridworld dört satır Python'dur. Bir *modelin* var.

Model-free RL (Q-learning, PPO, REINFORCE) modelin olmadığı durum için icat edildi — sadece environment'tan örnekleyebildiğin durum için. Ama modelin olduğunda, daha hızlı, daha iyi yöntemler var: dinamik programlama. Bellman bunları 1957'de tasarladı. Hâlâ doğruluğu tanımlıyorlar: insanlar "bu MDP için optimal policy" dediklerinde, DP'nin döndüreceği policy'yi kastediyorlar.

2026'da bunlara üç sebepten ihtiyacın var. Birinci, RL araştırmasındaki her tablo formundaki environment (GridWorld, FrozenLake, CliffWalking) altın-standart policy'yi üretmek için DP ile çözülür. İkinci, kesin değerler sampling yöntemlerini *debug* etmene izin verir: Q-learning'in `V*(s_0)` tahmini DP cevabıyla %30 farklıysa, Q-learning'inde bir bug var demektir. Üçüncü, modern offline RL ve planlama yöntemleri (MCTS, AlphaZero'nun search'ü, Faz 9 · 10'daki model-based RL) hepsi öğrenilmiş ya da verilmiş bir model üzerinde bir Bellman backup'ı iterate eder.

## Kavram

![Policy iteration ve value iteration, yan yana](../assets/dp.svg)

**İki algoritma, ikisi de Bellman üzerinde sabit-nokta iterasyonu.**

**Policy iteration.** Policy değişmeyi bırakana kadar iki adımı sırayla yapar.

1. *Değerlendirme:* `π` policy'si verildiğinde, `V(s) ← Σ_a π(a|s) Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`'yi tekrar tekrar uygulayarak yakınsamaya kadar `V^π`'yi hesapla.
2. *İyileştirme:* `V^π` verildiğinde, `π`'yi `V^π`'ye göre greedy yap: `π(s) ← argmax_a Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`.

Yakınsama garantilidir çünkü (a) her iyileştirme adımı ya `π`'yi aynı tutar ya da bazı state'ler için `V^π`'yi kesinlikle artırır, (b) deterministik policy uzayı sonludur. Genelde büyük state uzayları için bile ~5–20 dış iterasyonda yakınsar.

**Value iteration.** Değerlendirme ve iyileştirmeyi tek bir sweep'te birleştirir. Bellman *optimality* denklemini uygula:

`V(s) ← max_a Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`

`max_s |V_{new}(s) - V(s)| < ε` olana kadar tekrarla. Sonunda greedy aksiyonu alarak policy'yi çıkar. İterasyon başına kesinlikle daha hızlı — iç değerlendirme döngüsü yok — ama tipik olarak yakınsamak için daha fazla iterasyon ister.

**Generalized policy iteration (GPI).** Birleştirici çerçeveleme. Value fonksiyonu ve policy iki yönlü bir iyileştirme döngüsünde kilitlidir; ikisini de karşılıklı tutarlılığa iten herhangi bir yöntem (async value iteration, modified policy iteration, Q-learning, actor-critic, PPO) bir GPI örneğidir.

**`γ < 1` neden önemli.** Bellman operatörü sup-norm'da bir `γ`-büzülmesidir: `||T V - T V'||_∞ ≤ γ ||V - V'||_∞`. Büzülme tek bir sabit nokta ve geometrik yakınsama anlamına gelir. `γ < 1`'i kaldır, garantiyi kaybedersin — sonlu bir ufka veya soğurucu bir terminal state'e ihtiyacın olur.

## İnşa Et

### Adım 1: GridWorld MDP modelini kur

Ders 01'deki aynı 4×4 GridWorld'ü kullan. Stokastik bir varyant ekliyoruz: `0.1` olasılıkla agent rastgele bir dik yöne kayar.

```python
SLIP = 0.1

def transitions(state, action):
    if state == TERMINAL:
        return [(state, 0.0, 1.0)]
    outcomes = []
    for direction, prob in action_probs(action):
        outcomes.append((apply_move(state, direction), -1.0, prob))
    return outcomes
```

`transitions(s, a)` bir `(s', r, p)` listesi döndürür. Modelin tamamı bu.

### Adım 2: policy evaluation

`π(s) = {action: prob}` policy'si verildiğinde, `V` hareket etmeyi bırakana kadar Bellman denklemini iterate et:

```python
def policy_evaluation(policy, gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in states()}
    while True:
        delta = 0.0
        for s in states():
            v = sum(pi_a * sum(p * (r + gamma * V[s_prime])
                              for s_prime, r, p in transitions(s, a))
                   for a, pi_a in policy(s).items())
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            return V
```

### Adım 3: policy improvement

`π`'yi `V`'ye göre greedy policy ile değiştir. `π` değişmediyse, dön — optimumdayız.

```python
def policy_improvement(V, gamma=0.99):
    new_policy = {}
    for s in states():
        best_a = max(
            ACTIONS,
            key=lambda a: sum(p * (r + gamma * V[s_prime])
                              for s_prime, r, p in transitions(s, a)),
        )
        new_policy[s] = best_a
    return new_policy
```

### Adım 4: birleştir

```python
def policy_iteration(gamma=0.99):
    policy = {s: "up" for s in states()}   # rastgele başlangıç
    for _ in range(100):
        V = policy_evaluation(lambda s: {policy[s]: 1.0}, gamma)
        new_policy = policy_improvement(V, gamma)
        if new_policy == policy:
            return V, policy
        policy = new_policy
```

4×4'te tipik yakınsama: 4–6 dış iterasyon. Çıktılar `V*(0,0) ≈ -6` ve adım sayısını kesinlikle azaltan bir policy.

### Adım 5: value iteration (tek-döngü versiyonu)

```python
def value_iteration(gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in states()}
    while True:
        delta = 0.0
        for s in states():
            v = max(sum(p * (r + gamma * V[s_prime])
                       for s_prime, r, p in transitions(s, a))
                   for a in ACTIONS)
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            break
    policy = policy_improvement(V, gamma)
    return V, policy
```

Aynı sabit nokta, daha az kod satırı.

## Tuzaklar

- **Terminal'leri ele almayı unutmak.** Bellman'ı soğurucu bir state'e uygularsan, hâlâ hiçbir şeyi değiştirmeyen bir "en iyi aksiyon" seçer. `if s == terminal: V[s] = 0` ile koru.
- **Sup-norm vs L2 yakınsama.** Ortalama değil, `max |V_new - V|` kullan. Teorik garanti sup-norm üzerinedir.
- **In-place vs senkron güncellemeler.** `V[s]`'yi in-place güncellemek (Gauss-Seidel) ayrı bir `V_new` dict'inden (Jacobi) daha hızlı yakınsar. Production kodu in-place kullanır.
- **Policy beraberlikleri.** İki aksiyon eşit Q-value'ya sahipse, `argmax` her iterasyonda beraberlikleri farklı kırabilir ve "policy stable" kontrolü salınır. Sabit bir beraberlik-kırma yöntemi kullan (sabit sırada ilk aksiyon).
- **State uzayı patlaması.** DP sweep başına `O(|S| · |A|)`. ~10⁷ state'e kadar çalışır. Ötesinde function approximation'a ihtiyacın var (Faz 9 · 05 ve sonrası).

## Kullan

2026'da DP, doğruluk baseline'ı ve planlayıcıların iç döngüsüdür:

| Kullanım durumu | Yöntem |
|-----------------|--------|
| Küçük tablo formundaki MDP'yi tam çöz | Value iteration (daha basit) ya da policy iteration (daha az dış adım) |
| Q-learning / PPO implementasyonunu doğrula | Bir oyuncak environment'ta DP-optimal V* ile karşılaştır |
| Model-based RL (Faz 9 · 10) | Öğrenilmiş geçiş modeli üzerinde Bellman backup |
| AlphaZero / MuZero'da planlama | Monte Carlo Tree Search = async Bellman backup |
| Offline RL (CQL, IQL) | Conservative Q-iteration — OOD aksiyonlarda cezalı DP |

Biri "optimal value function" dediğinde, "DP sabit noktası" demek istiyor. Bir makalede `V*` veya `Q*` gördüğünde, bu döngüyü hayal et.

## Yayınla

`outputs/skill-dp-solver.md` olarak kaydet:

```markdown
---
name: dp-solver
description: Solve a small tabular MDP exactly via policy iteration or value iteration. Report convergence behavior.
version: 1.0.0
phase: 9
lesson: 2
tags: [rl, dynamic-programming, bellman]
---

Given an MDP with a known model, output:

1. Choice. Policy iteration vs value iteration. Reason tied to |S|, |A|, γ.
2. Initialization. V_0, starting policy. Convergence sensitivity.
3. Stopping. Sup-norm tolerance ε. Expected number of sweeps.
4. Verification. V*(s_0) computed exactly. Greedy policy extracted.
5. Use. How this baseline will be used to debug/evaluate sampling-based methods.

Refuse to run DP on state spaces > 10⁷. Refuse to claim convergence without a sup-norm check. Flag any γ ≥ 1 on an infinite-horizon task as a guarantee violation.
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld üzerinde `γ ∈ {0.9, 0.99}` ile value iteration çalıştır. `max |ΔV| < 1e-6` olana kadar kaç sweep gerekiyor? `V*`'yi 4×4 grid olarak yazdır.
2. **Orta.** *Stokastik* GridWorld'de (slip olasılığı `0.1`) policy iteration ile value iteration'ı karşılaştır. Say: sweep'ler, duvar-saati zamanı, son `V*(0,0)`. Hangisi iterasyonda daha hızlı yakınsar? Duvar-saatinde?
3. **Zor.** Modified policy iteration kur: değerlendirme adımında yakınsamaya kadar değil, yalnızca `k` sweep koştur. `k ∈ {1, 2, 5, 10, 50}` için `V*(0,0)` hatası vs `k` grafiğini çiz. Eğri sana değerlendirme/iyileştirme dengesi hakkında ne söylüyor?

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Policy iteration | "DP algoritması" | Policy değişmeyi bırakana kadar dönüşümlü değerlendirme (`V^π`) ve iyileştirme (`V^π`'ye göre greedy `π`). |
| Value iteration | "Daha hızlı DP" | Tek bir sweep'te uygulanan Bellman optimality backup'ı; geometrik olarak `V*`'a yakınsar. |
| Bellman operatörü | "Özyineleme" | `(T V)(s) = max_a Σ P (r + γ V(s'))`; sup-norm'da bir `γ`-büzülmesi. |
| Büzülme | "DP neden yakınsar" | `||T x - T y|| ≤ γ ||x - y||` özelliğine sahip herhangi bir `T` operatörünün tek bir sabit noktası vardır. |
| GPI | "Her şey DP'dir" | Generalized Policy Iteration: `V` ve `π`'yi karşılıklı tutarlılığa iten herhangi bir yöntem. |
| Senkron güncelleme | "Jacobi-tarzı" | Bir sweep boyunca eski `V`'yi kullan; temiz analiz edilebilir ama daha yavaş. |
| In-place güncelleme | "Gauss-Seidel-tarzı" | `V`'yi güncellenirken kullan; pratikte daha hızlı yakınsar. |

## İleri Okuma

- [Sutton & Barto (2018). Ch. 4 — Dynamic Programming](http://incompleteideas.net/book/RLbook2020.pdf) — policy iteration ve value iteration'ın kanonik sunumu.
- [Bertsekas (2019). Reinforcement Learning and Optimal Control](http://www.athenasc.com/rlbook.html) — büzülme-eşleşmesi argümanlarının titiz bir ele alınışı.
- [Puterman (2005). Markov Decision Processes](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470316887) — modified policy iteration ve onun yakınsama analizi.
- [Howard (1960). Dynamic Programming and Markov Processes](https://mitpress.mit.edu/9780262582300/dynamic-programming-and-markov-processes/) — orijinal policy iteration makalesi.
- [Bertsekas & Tsitsiklis (1996). Neuro-Dynamic Programming](http://www.athenasc.com/ndpbook.html) — DP'den approximate-DP / deep RL'e köprü; sonraki her dersin kullandığı.
