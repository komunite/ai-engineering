# Policy Gradient — Sıfırdan REINFORCE

> Value tahmin etmeyi bırak. Policy'yi doğrudan parametrize et, beklenen return'ün gradyanını hesapla, yukarı adımla. Williams (1992) bunu tek bir teoremde yazdı. PPO, GRPO ve her LLM RL döngüsünün var olma sebebi budur.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 · 03 (Backpropagation), Faz 9 · 03 (Monte Carlo), Faz 9 · 04 (TD Learning)
**Süre:** ~75 dakika

## Sorun

Q-learning ve DQN *value* fonksiyonunu parametrize eder. Aksiyonları `argmax Q` ile seçersin. Bu diskret aksiyonlar ve diskret state'ler için iyidir. Aksiyonlar sürekliyse (10 boyutlu bir tork üzerinde hangi `argmax`?) ya da stokastik bir policy istiyorsan (`argmax` yapı gereği deterministiktir) bozulur.

Policy gradient'lar bunun yerine *policy*'yi parametrize eder. `π_θ(a | s)`, aksiyonlar üzerinde bir dağılım üreten bir neural net'tir. Davranmak için ondan örnekle. Beklenen return'ün `θ`'ya göre gradyanını hesapla. Yukarı adımla. `argmax` yok. Bellman özyinelemesi yok. Sadece `J(θ) = E_{π_θ}[G]` üzerinde gradient ascent.

REINFORCE teoremi (Williams 1992) sana bu gradyanın hesaplanabilir olduğunu söyler: `∇J(θ) = E_π[ G · ∇_θ log π_θ(a | s) ]`. Bir episode koştur. Return'ü hesapla. Her adımda `∇ log π_θ(a | s)` ile çarp. Ortala. Gradient-ascent. Tamam.

2026'daki her LLM-RL algoritması — PPO, DPO, GRPO — REINFORCE'un bir rafinesidir. Parmaklarında onu anlamak bu fazın geri kalanının ve Faz 10 · 07 (RLHF implementasyonu) ile Faz 10 · 08 (DPO)'nın ön koşuludur.

## Kavram

![Policy gradient: softmax policy, log-π gradient, return-ağırlıklı güncelleme](../assets/policy-gradient.svg)

**Policy gradient teoremi.** `θ` ile parametrize edilmiş herhangi bir `π_θ` policy'si için:

`∇J(θ) = E_{τ ~ π_θ}[ Σ_{t=0}^{T} G_t · ∇_θ log π_θ(a_t | s_t) ]`

burada `G_t = Σ_{k=t}^{T} γ^{k-t} r_{k+1}` `t` adımından itibaren indirilmiş return'dür. Beklenti `π_θ`'dan örneklenen tam trajectory'ler `τ` üzerindedir.

**Kanıt kısadır.** Beklenti altında `J(θ) = Σ_τ P(τ; θ) G(τ)`'yu türetle. `∇P(τ; θ) = P(τ; θ) ∇ log P(τ; θ)` (log-türev trick'i) kullan. `log P(τ; θ) = Σ log π_θ(a_t | s_t) + θ'ya bağlı olmayan environment terimleri` olarak çarpanlara ayır. Environment terimleri kaybolur. İki satır cebir teoremi verir.

**Varyans azaltma trick'leri.** Düz REINFORCE'un öldürücü varyansı vardır — return'ler gürültülü, `∇ log π` gürültülü, çarpımları çok gürültülü. İki standart düzeltme:

1. **Baseline çıkarımı.** `G_t`'yi `a_t`'ye bağlı olmayan herhangi bir `b(s_t)` baseline'ı için `G_t - b(s_t)` ile değiştir. `E[b(s_t) · ∇ log π(a_t | s_t)] = 0` olduğundan yansızdır. Tipik seçim: bir critic tarafından öğrenilen `b(s_t) = V̂(s_t)` → actor-critic (Ders 07).
2. **Reward-to-go.** `Σ_t G_t · ∇ log π_θ(a_t | s_t)`'yi `Σ_t G_t^{from t} · ∇ log π_θ(a_t | s_t)` ile değiştir. Belirli bir aksiyon için yalnızca gelecek return'ler önemlidir — geçmiş ödüller sıfır-ortalama gürültü katar.

Birleştirildiğinde:

`∇J ≈ (1/N) Σ_{i=1}^{N} Σ_{t=0}^{T_i} [ G_t^{(i)} - V̂(s_t^{(i)}) ] · ∇_θ log π_θ(a_t^{(i)} | s_t^{(i)})`

ki bu da baseline'lı REINFORCE — A2C (Ders 07) ve PPO (Ders 08)'nun doğrudan atasıdır.

**Softmax policy parametrizasyonu.** Diskret aksiyonlar için standart seçim:

`π_θ(a | s) = exp(f_θ(s, a)) / Σ_{a'} exp(f_θ(s, a'))`

burada `f_θ` aksiyon başına bir skor üreten herhangi bir neural net'tir. Gradyanın temiz bir formu vardır:

`∇_θ log π_θ(a | s) = ∇_θ f_θ(s, a) - Σ_{a'} π_θ(a' | s) ∇_θ f_θ(s, a')`

yani alınan aksiyonun skoru eksi policy altındaki beklenen değeri.

**Sürekli aksiyonlar için Gauss policy.** `π_θ(a | s) = N(μ_θ(s), σ_θ(s))`. `∇ log N(a; μ, σ)` kapalı formuludur. Faz 9 · 07'nin SAC'sinin tek istediği budur.

## İnşa Et

### Adım 1: softmax policy network'ü

```python
def policy_logits(theta, state_features):
    return [dot(theta[a], state_features) for a in range(N_ACTIONS)]

def softmax(logits):
    m = max(logits)
    exps = [exp(l - m) for l in logits]
    Z = sum(exps)
    return [e / Z for e in exps]
```

Tablo formundaki bir env için lineer policy (aksiyon başına bir ağırlık vektörü) kullan. Atari için bir CNN tak ve softmax başlığını koru.

### Adım 2: örnekleme ve log-olasılık

```python
def sample_action(probs, rng):
    x = rng.random()
    cum = 0
    for a, p in enumerate(probs):
        cum += p
        if x <= cum:
            return a
    return len(probs) - 1

def log_prob(probs, a):
    return log(probs[a] + 1e-12)
```

### Adım 3: log-prob'lar yakalanmış rollout

```python
def rollout(theta, env, rng, gamma):
    trajectory = []
    s = env.reset()
    while not done:
        logits = policy_logits(theta, s)
        probs = softmax(logits)
        a = sample_action(probs, rng)
        s_next, r, done = env.step(s, a)
        trajectory.append((s, a, r, probs))
        s = s_next
    return trajectory
```

### Adım 4: REINFORCE güncellemesi

```python
def reinforce_step(theta, trajectory, gamma, lr, baseline=0.0):
    returns = compute_returns(trajectory, gamma)
    for (s, a, _, probs), G in zip(trajectory, returns):
        advantage = G - baseline
        grad_log_pi_a = [-p for p in probs]
        grad_log_pi_a[a] += 1.0
        for i in range(N_ACTIONS):
            for j in range(len(s)):
                theta[i][j] += lr * advantage * grad_log_pi_a[i] * s[j]
```

Gradient `∇ log π(a|s) = e_a - π(·|s)` (`a` onehot'u eksi olasılıklar) softmax policy gradient'ların kalbidir. Onu kas hafızasına yaz.

### Adım 5: baseline'lar

Son episode'lar üzerinde `G`'nin koşan ortalaması 4×4 GridWorld'ü çalıştırmak için yeterli varyans azaltımı; yakınsamak ~500 episode alır. Baseline'ı öğrenilmiş bir `V̂(s)`'ye yükselt, actor-critic'i elde edersin.

## Tuzaklar

- **Patlayan gradyanlar.** Return'ler devasa olabilir. `∇ log π` ile çarpmadan önce daima batch üzerinde `G`'yi `~N(0, 1)`'e normalize et.
- **Entropy çöküşü.** Policy çok erken neredeyse-deterministik bir aksiyona yakınsar, explore etmeyi bırakır, takılır. Düzeltme: hedefe entropy bonus `β · H(π(·|s))` ekle.
- **Yüksek varyans.** Düz REINFORCE binlerce episode ister. Bir critic baseline'ı (Ders 07) ya da TRPO/PPO'nun trust region'ı (Ders 08) standart düzeltmedir.
- **Örnek verimsizliği.** On-policy olmak, her geçişi bir güncellemeden sonra atmak demektir. Importance sampling üzerinden off-policy düzeltmeleri veriyi geri getirir, varyans pahasına (PPO'nun oranı clip'lenmiş bir IS ağırlığıdır).
- **Non-stationary gradyanlar.** 100 episode önce aldığın aynı gradyan eski `π`'yi kullanır. On-policy yöntemler bu yüzden birkaç rollout'ta bir günceller.
- **Credit assignment.** Reward-to-go olmadan, geçmiş ödüller gürültü katar. Daima reward-to-go kullan.

## Kullan

2026'da REINFORCE nadiren doğrudan koşulur ama gradyan formülü her yerdedir:

| Kullanım durumu | Türetilmiş yöntem |
|-----------------|-------------------|
| Sürekli kontrol | Gauss policy ile PPO / SAC |
| LLM RLHF | KL cezalı, token seviyesi policy üzerinde koşan PPO |
| LLM reasoning (DeepSeek) | GRPO — grup-göreceli baseline ile REINFORCE, critic yok |
| Multi-agent | Centralized-critic REINFORCE (MADDPG, COMA) |
| Diskret aksiyonlu robotik | A2C, A3C, PPO |
| Yalnızca preference ayarları | DPO — REINFORCE'un preference-likelihood loss'u olarak yeniden yazımı, örnekleme yok |

2026 eğitim script'inde `loss = -advantage * log_prob` okuduğunda, bu baseline'lı REINFORCE'tur. Tüm makaleler (DPO, GRPO, RLOO) bu tek satırın üstüne varyans azaltma trick'leridir.

## Yayınla

`outputs/skill-policy-gradient-trainer.md` olarak kaydet:

```markdown
---
name: policy-gradient-trainer
description: Produce a REINFORCE / actor-critic / PPO training config for a given task and diagnose variance issues.
version: 1.0.0
phase: 9
lesson: 6
tags: [rl, policy-gradient, reinforce]
---

Given an environment (discrete / continuous actions, horizon, reward stats), output:

1. Policy head. Softmax (discrete) or Gaussian (continuous) with parameter counts.
2. Baseline. None (vanilla), running mean, learned `V̂(s)`, or A2C critic.
3. Variance controls. Reward-to-go on by default, return normalization, gradient clip value.
4. Entropy bonus. Coefficient β and decay schedule.
5. Batch size. Episodes per update; on-policy data freshness contract.

Refuse REINFORCE-no-baseline on horizons > 500 steps. Refuse continuous-action control with a softmax head. Flag any run with `β = 0` and observed policy entropy < 0.1 as entropy-collapsed.
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld üzerinde lineer softmax policy ile REINFORCE uygula. Baseline'sız 1.000 episode eğit. Öğrenme eğrisini çiz; varyansı ölç (return std'si).
2. **Orta.** Koşan-ortalama bir baseline ekle. Tekrar eğit. Örnek verimliliğini ve varyansı düz koşuyla karşılaştır. Baseline yakınsamaya kadar olan adım sayısını ne kadar azaltıyor?
3. **Zor.** Entropy bonusu `β · H(π)` ekle. `β ∈ {0, 0.01, 0.1, 1.0}` üzerinde tara. Son return'ü ve policy entropy'sini çiz. Bu görevde sweet spot nerede?

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Policy gradient | "Policy'yi doğrudan eğit" | `∇J(θ) = E[G · ∇ log π_θ(a|s)]`; log-türev trick'inden türetilmiş. |
| REINFORCE | "Orijinal PG algoritması" | Williams (1992); log-policy gradient ile çarpılan Monte Carlo return'ler. |
| Log-türev trick'i | "Skor fonksiyonu tahmincisi" | `∇P(τ;θ) = P(τ;θ) · ∇ log P(τ;θ)`; beklentilerin gradyanlarını izlenebilir kılar. |
| Baseline | "Varyans azaltımı" | `G`'den çıkarılan herhangi bir `b(s)`; `E[b · ∇ log π] = 0` olduğundan yansız. |
| Reward-to-go | "Yalnızca gelecek return'ler sayılır" | Tam `G_0` yerine `G_t^{from t}`; doğru ve daha düşük varyanslı. |
| Entropy bonus | "Exploration'ı teşvik et" | `+β · H(π(·|s))` terimi policy'yi çökmekten korur. |
| On-policy | "Az önce gördüğün üzerinde eğit" | Gradyan beklentisi şu anki policy'ye göredir — eski veri doğrudan tekrar kullanılamaz. |
| Advantage | "Ortalamadan ne kadar daha iyi" | `A(s, a) = G(s, a) - V(s)`; baseline'lı REINFORCE'un çarptığı işaretli miktar. |

## İleri Okuma

- [Williams (1992). Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning](https://link.springer.com/article/10.1007/BF00992696) — orijinal REINFORCE makalesi.
- [Sutton et al. (2000). Policy Gradient Methods for Reinforcement Learning with Function Approximation](https://papers.nips.cc/paper_files/paper/1999/hash/464d828b85b0bed98e80ade0a5c43b0f-Abstract.html) — function approximation ile modern policy-gradient teoremi.
- [Sutton & Barto (2018). Ch. 13 — Policy Gradient Methods](http://incompleteideas.net/book/RLbook2020.pdf) — ders kitabı sunumu.
- [OpenAI Spinning Up — VPG / REINFORCE](https://spinningup.openai.com/en/latest/algorithms/vpg.html) — PyTorch kodlu temiz pedagojik sunum.
- [Peters & Schaal (2008). Reinforcement Learning of Motor Skills with Policy Gradients](https://homes.cs.washington.edu/~todorov/courses/amath579/reading/PolicyGradient.pdf) — varyans-azaltma ve REINFORCE'u trust-region ailesine (TRPO, PPO) bağlayan natural-gradient bakışı.
