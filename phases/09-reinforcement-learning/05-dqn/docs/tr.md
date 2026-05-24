# Deep Q-Networks (DQN)

> 2013: Mnih, ham pikseller üzerinde bir Q-learning ağı eğitti, yedi Atari oyununda her klasik RL agent'ını yendi. 2015: 49 oyuna genişletildi, Nature'da yayınlandı, derin-RL çağını başlattı. DQN, function approximation'ı kararlı kılan üç trick ile Q-learning'dir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 · 03 (Backpropagation), Faz 9 · 04 (Q-learning, SARSA)
**Süre:** ~75 dakika

## Sorun

Tablo formundaki Q-learning her (state, aksiyon) çifti için ayrı bir Q-değeri ister. Bir satranç tahtasının ~10⁴³ state'i vardır. Bir Atari frame'i 210×160×3 = 100.800 feature'dır. Tablo formundaki RL binlerce state'te ölür, milyarlarca bir kenara.

Düzeltme geriye dönük bakıldığında bariz: Q-tablosunu bir neural network ile değiştir, `Q(s, a; θ)`. Ama bariz-geriye-dönük olan onlarca yıl aldı. Q-learning ile naif function approximation "ölümcül üçlü" — function approximation + bootstrapping + off-policy öğrenme — altında ıraksar. Mnih et al. (2013, 2015) öğrenmeyi kararlı kılan üç mühendislik trick'i belirledi:

1. **Experience replay**, geçişlerin korelasyonunu kırar.
2. **Target network**, bootstrap hedefini dondurur.
3. **Reward clipping**, gradyan büyüklüklerini normalize eder.

Atari üzerinde DQN, tek bir mimari ve tek bir hiperparametre setiyle ham piksellerden onlarca kontrol problemini çözen ilk şeydi. O zamandan beri inşa edilen her "derin-RL" — DDQN, Rainbow, Dueling, Distributional, R2D2, Agent57 — bu üç-trick temeli üzerinde yığılmıştır.

## Kavram

![DQN eğitim döngüsü: env, replay buffer, online net, target net, Bellman TD loss](../assets/dqn.svg)

**Hedef.** DQN nöral bir Q-fonksiyonu üzerinde tek-adım TD loss'u minimize eder:

`L(θ) = E_{(s,a,r,s')~D} [ (r + γ max_{a'} Q(s', a'; θ^-) - Q(s, a; θ))² ]`

`θ` = online network, gradient descent ile her adım güncellenir. `θ^-` = target network, periyodik olarak `θ`'dan kopyalanır (her ~10.000 adım). `D` = geçmiş geçişlerin replay buffer'ı.

**Üç trick, önem sırasıyla:**

**Experience replay.** `~10⁶` geçişin halka buffer'ı. Her eğitim adımı uniformly random bir minibatch örnekler. Bu temporal korelasyonu kırar (ardışık frame'ler neredeyse aynıdır), ağın nadir ödüllendirici geçişlerden birçok kez öğrenmesine izin verir ve ardışık gradient güncellemelerinin korelasyonunu kırar. O olmadan, neural net'li on-policy TD Atari'de ıraksar.

**Target network.** Bellman denkleminin her iki tarafında aynı `Q(·; θ)` ağını kullanmak hedefi her güncellemede hareket ettirir — "kendi kuyruğunu kovalamak." Düzeltme: dondurulmuş ağırlıklarla ikinci bir ağ `Q(·; θ^-)` tut. Her `C` adımda, `θ → θ^-` kopyala. Bu, regresyon hedefini bir seferde binlerce gradient adımı için kararlılaştırır. Soft güncellemeler `θ^- ← τ θ + (1-τ) θ^-` (DDPG, SAC'ta kullanılan) daha pürüzsüz bir varyant.

**Reward clipping.** Atari ödül büyüklükleri 1'den 1000+'a değişir. `{-1, 0, +1}`'e clip'lemek, herhangi bir oyunun gradyanı domine etmesini durdurur. Ödül büyüklüğünün önemli olduğu durumlarda yanlış; yalnızca işaretin önemli olduğu Atari için iyi.

**Double DQN.** Hasselt (2016) maximization bias'ı düzeltir: aksiyonu *seçmek* için online net'i, *değerlendirmek* için target net'i kullan.

`target = r + γ Q(s', argmax_{a'} Q(s', a'; θ); θ^-)`

Drop-in replacement, sürekli olarak daha iyi. Varsayılan olarak kullan.

**Diğer iyileştirmeler (Rainbow, 2017):** prioritized replay (yüksek-TD-hatalı geçişleri daha çok örnekle), dueling mimari (ayrı `V(s)` ve advantage başlıkları), noisy network'ler (öğrenilmiş exploration), n-step return'ler, distributional Q (C51/QR-DQN), multi-step bootstrapping. Her biri birkaç yüzde ekler; kazanımlar kabaca toplamsaldır.

## İnşa Et

Buradaki kod yalnızca stdlib, numpy-free — minik sürekli bir GridWorld üzerinde el-yapımı tek-gizli-katmanlı bir MLP kullanıyoruz, böylece her eğitim adımı mikrosaniyelerde koşuyor. Algoritma ölçekteki Atari DQN ile birebir aynı.

### Adım 1: replay buffer

```python
class ReplayBuffer:
    def __init__(self, capacity):
        self.buf = []
        self.capacity = capacity
    def push(self, s, a, r, s_next, done):
        if len(self.buf) == self.capacity:
            self.buf.pop(0)
        self.buf.append((s, a, r, s_next, done))
    def sample(self, batch, rng):
        return rng.sample(self.buf, batch)
```

Atari için ~50.000 kapasite; bizim oyuncak env'imiz için 5.000 yeter.

### Adım 2: minik bir Q-network (manuel MLP)

```python
class QNet:
    def __init__(self, n_in, n_hidden, n_actions, rng):
        self.W1 = [[rng.gauss(0, 0.3) for _ in range(n_in)] for _ in range(n_hidden)]
        self.b1 = [0.0] * n_hidden
        self.W2 = [[rng.gauss(0, 0.3) for _ in range(n_hidden)] for _ in range(n_actions)]
        self.b2 = [0.0] * n_actions
    def forward(self, x):
        h = [max(0.0, sum(w * xi for w, xi in zip(row, x)) + b) for row, b in zip(self.W1, self.b1)]
        q = [sum(w * hi for w, hi in zip(row, h)) + b for row, b in zip(self.W2, self.b2)]
        return q, h
```

Forward pass: lineer → ReLU → lineer. Ağın tamamı bu.

### Adım 3: DQN güncellemesi

```python
def train_step(online, target, batch, gamma, lr):
    grads = zeros_like(online)
    for s, a, r, s_next, done in batch:
        q, h = online.forward(s)
        if done:
            y = r
        else:
            q_next, _ = target.forward(s_next)
            y = r + gamma * max(q_next)
        td_error = q[a] - y
        accumulate_grads(grads, online, s, h, a, td_error)
    apply_sgd(online, grads, lr / len(batch))
```

Şekil iki farkla Ders 04'teki Q-learning: (a) bir tabloyu indekslemek yerine türevlenebilir bir `Q(·; θ)` üzerinden backprop yapıyoruz, (b) hedef `Q(·; θ^-)` kullanıyor.

### Adım 4: dış döngü

Her episode için, `Q(·; θ)` üzerinde ε-greedy davran, geçişleri buffer'a it, bir minibatch örnekle, bir gradient adımı at, periyodik olarak `θ^- ← θ` senkronize et. Desen:

```python
for episode in range(N):
    s = env.reset()
    while not done:
        a = epsilon_greedy(online, s, epsilon)
        s_next, r, done = env.step(s, a)
        buffer.push(s, a, r, s_next, done)
        if len(buffer) >= batch:
            train_step(online, target, buffer.sample(batch), gamma, lr)
        if steps % sync_every == 0:
            target = copy(online)
        s = s_next
```

16 boyutlu one-hot state'li minik GridWorld'ümüzde agent ~500 episode'da neredeyse-optimal policy öğrenir. Atari'de bunu 200M frame'e ölçeklendir ve bir CNN feature extractor ekle.

## Tuzaklar

- **Ölümcül üçlü.** Function approximation + off-policy + bootstrapping ıraksabilir. DQN bunu target net + replay ile hafifletir; ikisini de kaldırma.
- **Exploration.** ε bozulmalı, tipik olarak ilk ~%10 eğitimde 1.0'dan 0.01'e. Yeterli erken exploration olmadan Q-net yerel bir havzaya yakınsar.
- **Aşırı tahmin.** Gürültülü Q üzerinde `max` yukarı yönlü biased'tır. Production'da daima Double DQN kullan.
- **Ödül ölçeği.** Ödülleri clip'le veya normalize et; gradyan büyüklüğü ödül büyüklüğüyle orantılıdır.
- **Replay buffer coldstart.** Buffer'da birkaç bin geçiş olmadan eğitime başlama. ~20 örnek üzerindeki erken gradyanlar overfit eder.
- **Target senkronizasyon frekansı.** Çok sık ≈ target net yok; çok seyrek ≈ bayat hedefler. Atari DQN 10.000 env adımı kullanır. Pratik kural: eğitim ufkunun ~1/100'ünde bir senkronize et.
- **Gözlem ön işleme.** Atari DQN state'i Markov yapmak için 4 frame yığar. Hız bilgisi olan herhangi bir env frame-stacking veya recurrent state ister.

## Kullan

2026'da DQN nadiren state-of-the-art'tır ama referans off-policy algoritma olarak kalır:

| Görev | Tercih yöntemi | Neden DQN değil? |
|-------|----------------|------------------|
| Diskret-aksiyonlu Atari-benzeri | Rainbow DQN ya da Muesli | Aynı çerçeve, daha fazla trick. |
| Sürekli kontrol | SAC / TD3 (Faz 9 · 07) | DQN'in policy network'ü yok. |
| On-policy / yüksek-throughput | PPO (Faz 9 · 08) | Replay buffer yok; ölçeklendirmesi kolay. |
| Offline RL | CQL / IQL / Decision Transformer | Muhafazakâr Q hedefleri, bootstrap patlamaları yok. |
| Büyük diskret aksiyon uzayları (recommender) | Aksiyon embedding'li DQN ya da IMPALA | İyi; süslemeler önemli. |
| LLM RL | PPO / GRPO | Sekans seviyesi, adım seviyesi değil; farklı loss. |

Dersler hâlâ taşınır. Replay ve target network'ler SAC, TD3, DDPG, SAC-X, AlphaZero'nun self-play buffer'ı ve her offline RL yönteminde görünür. Reward clipping PPO'da advantage normalizasyonu olarak yaşar. Mimari bir plandır.

## Yayınla

`outputs/skill-dqn-trainer.md` olarak kaydet:

```markdown
---
name: dqn-trainer
description: Produce a DQN training config (buffer, target sync, ε schedule, reward clipping) for a discrete-action RL task.
version: 1.0.0
phase: 9
lesson: 5
tags: [rl, dqn, deep-rl]
---

Given a discrete-action environment (observation shape, action count, horizon, reward scale), output:

1. Network. Architecture (MLP / CNN / Transformer), feature dim, depth.
2. Replay buffer. Capacity, minibatch size, warmup size.
3. Target network. Sync strategy (hard every C steps or soft τ).
4. Exploration. ε start / end / schedule length.
5. Loss. Huber vs MSE, gradient clip value, reward clipping rule.
6. Double DQN. On by default unless explicit reason to disable.

Refuse to ship a DQN with no target network, no replay buffer, or ε held at 1. Refuse continuous-action tasks (route to SAC / TD3). Flag any reward range > 10× per-step mean as needing clipping or scale normalization.
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı koştur. Episode başı return eğrisini çiz. Koşan ortalama -10'u aşana kadar kaç episode gerekiyor?
2. **Orta.** Target network'ü devre dışı bırak (Bellman hedefinin her iki tarafı için online net'i kullan). Eğitim instabilitesini ölç — return salınıyor mu, ıraksıyor mu?
3. **Zor.** Double DQN ekle: `argmax a'`'yı seçmek için online net'i, değerlendirmek için target net'i kullan. Gürültülü-ödüllü bir GridWorld'de Double DQN'li ve Double DQN'siz 1.000 episode sonrası `Q(s_0, best_a)`'nın gerçek `V*(s_0)`'a karşı bias'ını karşılaştır.

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| DQN | "Deep Q-learning" | Nöral Q-fonksiyonu, replay buffer ve target network'lü Q-learning. |
| Experience replay | "Karıştırılmış geçişler" | Her gradient adımında uniformly örneklenen halka buffer; veriyi dekorele eder. |
| Target network | "Dondurulmuş bootstrap" | Bellman hedefinde kullanılan Q'nun periyodik kopyası; eğitimi kararlılaştırır. |
| Ölümcül üçlü | "RL neden ıraksar" | Function approximation + bootstrapping + off-policy = yakınsama garantisi yok. |
| Double DQN | "Maximization bias için düzeltme" | Online net aksiyonu seçer, target net değerlendirir. |
| Dueling DQN | "V ve A başlıkları" | Q = V + A - mean(A) olarak ayrıştır; aynı çıkış, daha iyi gradyan akışı. |
| Rainbow | "Tüm trick'ler" | DDQN + PER + dueling + n-step + noisy + distributional bir arada. |
| PER | "Prioritized Replay" | TD-hata büyüklüğüyle orantılı olarak geçişleri örnekle. |

## İleri Okuma

- [Mnih et al. (2013). Playing Atari with Deep Reinforcement Learning](https://arxiv.org/abs/1312.5602) — derin RL'i başlatan 2013 NeurIPS workshop makalesi.
- [Mnih et al. (2015). Human-level control through deep reinforcement learning](https://www.nature.com/articles/nature14236) — Nature makalesi, 49-oyunlu DQN.
- [Hasselt, Guez, Silver (2016). Deep Reinforcement Learning with Double Q-learning](https://arxiv.org/abs/1509.06461) — DDQN.
- [Wang et al. (2016). Dueling Network Architectures](https://arxiv.org/abs/1511.06581) — dueling DQN.
- [Hessel et al. (2018). Rainbow: Combining Improvements in Deep RL](https://arxiv.org/abs/1710.02298) — yığılmış-trick'ler makalesi.
- [OpenAI Spinning Up — DQN](https://spinningup.openai.com/en/latest/algorithms/dqn.html) — temiz modern sunum.
- [Sutton & Barto (2018). Ch. 9 — On-policy Prediction with Approximation](http://incompleteideas.net/book/RLbook2020.pdf) — DQN'in target network ve replay buffer'ının evcilleştirmek için tasarlandığı "ölümcül üçlü"nün ders kitabı ele alışı.
- [CleanRL DQN implementation](https://docs.cleanrl.dev/rl-algorithms/dqn/) — ablation çalışmalarında kullanılan referans tek-dosya DQN; bu dersin sıfırdan versiyonuyla birlikte okumak iyi.
