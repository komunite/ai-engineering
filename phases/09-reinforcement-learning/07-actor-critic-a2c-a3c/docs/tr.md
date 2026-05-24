# Actor-Critic — A2C ve A3C

> REINFORCE gürültülüdür. `V̂(s)`'yi öğrenen bir critic ekle, onu return'den çıkar ve aynı beklentiye sahip ama çok daha düşük varyanslı bir advantage elde edersin. Bu actor-critic. A2C onu senkron koşturur; A3C iş parçacıkları arasında koşturur. İkisi de her modern derin-RL yönteminin zihinsel modeli.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 04 (TD Learning), Faz 9 · 06 (REINFORCE)
**Süre:** ~75 dakika

## Sorun

Düz REINFORCE çalışır, ama varyansı korkunçtur. Monte Carlo return'leri `G_t` episode'lar arasında 10 kat değişebilir. Bu gürültüyü `∇ log π` ile çarpıp ortalamak, policy'yi binlerce episode'da çok daha az DQN güncellemesiyle hareket ettirebileceğin mesafe kadar hareket ettiren bir gradyan tahmincisi üretir.

Varyans ham return'leri kullanmaktan gelir. Bir `b(s_t)` baseline'ı — state'in herhangi bir fonksiyonu, öğrenilmiş bir value dahil — çıkarırsan, beklenti değişmez ve varyans düşer. En iyi izlenebilir baseline `V̂(s_t)`'dir. Şimdi `∇ log π` ile çarpan miktar *advantage*'tır:

`A(s, a) = G - V̂(s)`

Bir aksiyon, ortalamanın üstünde return ürettiyse iyidir; altındaysa kötü. Öğrenilmiş bir critic ile REINFORCE *actor-critic*'tir. Critic, actor'a düşük-varyanslı bir öğretmen verir. 2015 sonrası her derin-policy yöntemi budur (A2C, A3C, PPO, SAC, IMPALA).

## Kavram

![Actor-critic: policy net artı value net, advantage olarak TD residual'ı](../assets/actor-critic.svg)

**İki network, tek paylaşılan loss:**

- **Actor** `π_θ(a | s)`: policy. Davranmak için örneklenir. Policy gradient ile eğitilir.
- **Critic** `V_φ(s)`: state'ten beklenen return'ü tahmin eder. `(V_φ(s) - target)²`'yi minimize edecek şekilde eğitilir.

**Advantage.** İki standart form:

- *MC advantage:* `A_t = G_t - V_φ(s_t)`. Yansız, daha yüksek varyans.
- *TD advantage:* `A_t = r_{t+1} + γ V_φ(s_{t+1}) - V_φ(s_t)`. Biased (`V_φ`'yi kullanır), çok daha düşük varyans. *TD residual* `δ_t` olarak da bilinir.

**n-step advantage.** İkisi arasında interpolasyon yap:

`A_t^{(n)} = r_{t+1} + γ r_{t+2} + … + γ^{n-1} r_{t+n} + γ^n V_φ(s_{t+n}) - V_φ(s_t)`

`n = 1` saf TD. `n = ∞` MC. Çoğu uygulama Atari için `n = 5`, MuJoCo'da PPO için `n = 2048` kullanır.

**Generalized Advantage Estimation (GAE).** Schulman et al. (2016) tüm n-step advantage'lar üzerinde üstel ağırlıklı bir ortalama önerdi:

`A_t^{GAE} = Σ_{l=0}^{∞} (γλ)^l δ_{t+l}`

`λ ∈ [0, 1]` ile. `λ = 0` TD'dir (düşük varyans, yüksek bias). `λ = 1` MC'dir (yüksek varyans, yansız). `λ = 0.95` 2026 varsayılanıdır — bias/varyans kadranını istediğin yere gelene kadar tune et.

**A2C: senkron advantage actor-critic.** `N` paralel environment üzerinde `T` adım topla. Her adım için advantage'ları hesapla. Actor ve critic'i birleştirilmiş batch üzerinde güncelle. Tekrarla. A3C'nin daha basit, daha ölçeklenebilir kardeşi.

**A3C: asenkron advantage actor-critic.** Mnih et al. (2016). `N` worker iş parçacığı başlat, her biri bir env koşturur. Her worker gradyanları kendi rollout'unda yerel olarak hesaplar, sonra asenkron olarak paylaşılan bir parametre sunucusuna uygular. Replay buffer'a ihtiyaç yok — worker'lar farklı trajectory'ler koşturarak dekorele olur. A3C, CPU'larda ölçekte eğitebileceğini kanıtladı. 2026'da GPU-tabanlı A2C (batched paralel env'ler) hâkim çünkü GPU'lar büyük batch'ler ister.

**Birleşik loss.**

`L(θ, φ) = -E[ A_t · log π_θ(a_t | s_t) ]  +  c_v · E[(V_φ(s_t) - G_t)²]  -  c_e · E[H(π_θ(·|s_t))]`

Üç terim: policy-gradient loss, value regresyonu, entropy bonusu. `c_v ~ 0.5`, `c_e ~ 0.01` kanonik başlangıç noktaları.

## İnşa Et

### Adım 1: bir critic

MSE ile güncellenen lineer critic `V_φ(s) = w · features(s)`:

```python
def critic_update(w, x, target, lr):
    v_hat = dot(w, x)
    err = target - v_hat
    for j in range(len(w)):
        w[j] += lr * err * x[j]
    return v_hat
```

Tablo formundaki bir env'de critic birkaç yüz episode'da yakınsar. Atari'de lineer critic'i paylaşılan bir CNN gövdesi + value başlığıyla değiştir.

### Adım 2: n-step advantage

`T` uzunluğunda bir rollout ve bootstrap'lenmiş son `V(s_T)` verildiğinde:

```python
def compute_advantages(rewards, values, gamma=0.99, lam=0.95, last_value=0.0):
    advantages = [0.0] * len(rewards)
    gae = 0.0
    for t in reversed(range(len(rewards))):
        next_v = values[t + 1] if t + 1 < len(values) else last_value
        delta = rewards[t] + gamma * next_v - values[t]
        gae = delta + gamma * lam * gae
        advantages[t] = gae
    returns = [a + v for a, v in zip(advantages, values)]
    return advantages, returns
```

`returns` critic hedefidir. `advantages` `∇ log π` ile çarpan şeydir.

### Adım 3: birleşik güncelleme

```python
for step_i, (x, a, _r, probs) in enumerate(traj):
    adv = advantages[step_i]
    target_v = returns[step_i]

    # critic
    critic_update(w, x, target_v, lr_v)

    # actor
    for i in range(N_ACTIONS):
        grad_logpi = (1.0 if i == a else 0.0) - probs[i]
        for j in range(N_FEAT):
            theta[i][j] += lr_a * adv * grad_logpi * x[j]
```

On-policy, güncelleme başına bir rollout, actor ve critic için ayrı learning rate'ler.

### Adım 4: paralelleştirme (A3C vs A2C)

- **A3C:** `N` iş parçacığı başlat. Her biri kendi env'ini ve forward pass'ini koşturur. Periyodik olarak gradyan güncellemelerini paylaşılan bir master'a iter. Master'da kilit yok — yarışlar ok, sadece gürültü katar.
- **A2C:** Tek bir process içinde `N` env örneği koştur, gözlemleri bir `[N, obs_dim]` batch'inde yığ, batched forward pass, batched backward pass. Daha yüksek GPU kullanımı, deterministik, akıl yürütmesi daha kolay. 2026'da varsayılan.

Oyuncak kodumuz netlik için tek-iş parçacığı; batched A2C'ye yeniden yazmak üç satır numpy.

## Tuzaklar

- **Actor gradient'tan önce critic bias'ı.** Critic rastgele ise, baseline'ı bilgi vermez ve saf gürültü üzerinde eğitiyorsundur. Policy gradient'ı açmadan önce critic'i birkaç yüz adım ısıt ya da yavaş bir actor learning rate kullan.
- **Advantage normalizasyonu.** Batch başına advantage'ları sıfır-ortalama/birim-std'ye normalize et. Eğitimi neredeyse-sıfır maliyetle muazzam ölçüde kararlılaştırır.
- **Paylaşılan gövde.** Görüntü girişlerinde actor ve critic için paylaşılan bir feature extractor kullan. Ayrı başlıklar. Paylaşılan feature'lar her iki loss'tan da bedavaya yararlanır.
- **On-policy kontratı.** A2C veriyi tam olarak bir güncelleme için tekrar kullanır. Daha fazlası ise gradyanın biased'dır (importance-sampling düzeltmesi PPO'nun eklediği şeydir).
- **Entropy çöküşü.** `c_e > 0` olmadan, policy birkaç yüz güncellemede neredeyse-deterministik olur ve explore etmeyi bırakır.
- **Ödül ölçeği.** Advantage büyüklükleri ödül ölçeğine bağlıdır. Görevler arasında tutarlı gradyan büyüklükleri için ödülleri normalize et (örn. running-std bölme).

## Kullan

A2C/A3C 2026'da nadiren son seçimdir, ama sonraki her şeyin rafine ettiği mimaridir:

| Yöntem | A2C'ye ilişkisi |
|--------|-----------------|
| PPO | Çok-epoch güncellemeler için clip'lenmiş importance ratio'lu A2C |
| IMPALA | V-trace off-policy düzeltmeli A3C |
| SAC (Faz 9 · 07) | Soft-value critic'li off-policy A2C (sonraki ders) |
| GRPO (Faz 9 · 12) | Critic'siz A2C — grup-göreceli advantage |
| DPO | Preference-ranking loss'una indirgenmiş A2C, örnekleme yok |
| AlphaStar / OpenAI Five | League training + imitation pre-training'li A2C |

2026 makalesinde "advantage" görürsen, actor-critic düşün.

## Yayınla

`outputs/skill-actor-critic-trainer.md` olarak kaydet:

```markdown
---
name: actor-critic-trainer
description: Produce an A2C / A3C / GAE configuration for a given environment, with advantage estimation and loss weights specified.
version: 1.0.0
phase: 9
lesson: 7
tags: [rl, actor-critic, gae]
---

Given an environment and compute budget, output:

1. Parallelism. A2C (GPU batched) vs A3C (CPU async) and the number of workers.
2. Rollout length T. Steps per env per update.
3. Advantage estimator. n-step or GAE(λ); specify λ.
4. Loss weights. `c_v` (value), `c_e` (entropy), gradient clip.
5. Learning rates. Actor and critic (separate if using).

Refuse single-worker A2C on environments with horizon > 1000 (too on-policy, too slow). Refuse to ship without advantage normalization. Flag any run with `c_e = 0` and observed entropy < 0.1 as entropy-collapsed.
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld'de MC advantage'lı (`G_t - V(s_t)`) actor-critic eğit. Ders 06'daki koşan-ortalama-baseline'lı REINFORCE ile örnek verimliliğini karşılaştır.
2. **Orta.** TD-residual advantage'a (`r + γ V(s') - V(s)`) geç. Advantage batch'lerinin varyansını ölç. Ne kadar düşüyor?
3. **Zor.** GAE(λ) uygula. `λ ∈ {0, 0.5, 0.9, 0.95, 1.0}` üzerinde tara. Son return vs örnek verimliliği çiz. Bu görev için bias/varyans sweet spot'u nerede?

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Actor | "Policy net" | Policy gradient ile güncellenen `π_θ(a|s)`. |
| Critic | "Value net" | Return'lere / TD hedeflerine MSE regresyonu ile güncellenen `V_φ(s)`. |
| Advantage | "Ortalamadan ne kadar daha iyi" | `A(s, a) = Q(s, a) - V(s)` ya da tahmincileri. `∇ log π` için çarpan. |
| TD residual | "δ" | `δ_t = r + γ V(s') - V(s)`; tek-adım advantage tahmini. |
| GAE | "İnterpolasyon kadranı" | `λ` ile parametrize edilmiş n-step advantage'ların üstel ağırlıklı toplamı. |
| A2C | "Senkron actor-critic" | Env'ler arasında batched; rollout başına bir gradient adımı. |
| A3C | "Async actor-critic" | Worker iş parçacıkları gradyanları paylaşılan bir param sunucusuna iter. Orijinal makale; 2026'da daha az yaygın. |
| Bootstrap | "Ufukta V'yi kullan" | Rollout'u kes, toplamı kapatmak için `γ^n V(s_{t+n})` ekle. |

## İleri Okuma

- [Mnih et al. (2016). Asynchronous Methods for Deep Reinforcement Learning](https://arxiv.org/abs/1602.01783) — A3C, orijinal async actor-critic makalesi.
- [Schulman et al. (2016). High-Dimensional Continuous Control Using Generalized Advantage Estimation](https://arxiv.org/abs/1506.02438) — GAE.
- [Sutton & Barto (2018). Ch. 13 — Actor-Critic Methods](http://incompleteideas.net/book/RLbook2020.pdf) — temeller; critic bir neural net olduğunda Ch. 9 function approximation ile birlikte oku.
- [Espeholt et al. (2018). IMPALA](https://arxiv.org/abs/1802.01561) — V-trace off-policy düzeltmeli ölçeklenebilir dağıtık actor-critic.
- [OpenAI Baselines / Stable-Baselines3](https://stable-baselines3.readthedocs.io/) — okunmaya değer production A2C/PPO implementasyonları.
- [Konda & Tsitsiklis (2000). Actor-Critic Algorithms](https://papers.nips.cc/paper/1786-actor-critic-algorithms) — iki-zaman ölçekli actor-critic ayrışması için temel yakınsama sonucu.
