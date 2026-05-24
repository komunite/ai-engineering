# MDP'ler, State'ler, Aksiyonlar ve Ödüller

> Bir Markov Decision Process beş şeyden ibarettir: state'ler, aksiyonlar, geçişler, ödüller, bir indirim. RL'deki her şey — Q-learning, PPO, DPO, GRPO — bu şekil üzerinde optimize eder. Bir kere öğren, pekiştirmeli öğrenmenin geri kalanını bedavaya oku.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 1 · 06 (Olasılık ve Dağılımlar), Faz 2 · 01 (ML Taksonomisi)
**Süre:** ~45 dakika

## Sorun

Bir satranç botu yazıyorsun. Ya da bir envanter planlayıcısı. Ya da bir trading agent'ı. Ya da bir reasoning modelini eğiten PPO döngüsü. Dört farklı alan, tek bir şaşırtıcı gerçek: dördü de aynı matematiksel objeye indirgeniyor.

Supervised learning sana `(x, y)` çiftleri verir ve bir fonksiyon fit etmeni ister. Pekiştirmeli öğrenme sana etiket vermez — sadece bir state akışı, aldığın aksiyonlar ve skaler bir ödül verir. Hamle oyunu kazandı mı? Stok yenileme kararı para mı kazandırdı? Trade kâr mı etti? LLM'in az önce ürettiği token, judge'dan daha yüksek ödül almaya yol açtı mı?

Bu akıştan, onu formel hale getirmeden öğrenemezsin. "Ne gördüm," "ne yaptım," "sonra ne oldu," "bu ne kadar iyiydi" — her biri üzerinde akıl yürütebileceğin bir obje haline gelmek zorunda. Bu formelleştirmeye Markov Decision Process denir. Bu fazdaki her RL algoritması, sonundaki RLHF ve GRPO döngüleri dahil, bu şekil üzerinde optimize eder.

## Kavram

![Markov decision process: state'ler, aksiyonlar, geçişler, ödüller, indirim](../assets/mdp.svg)

**Beş obje.**

- **State'ler** `S`. Agent'ın karar vermek için ihtiyaç duyduğu her şey. GridWorld'de hücre. Satrançta tahta. Bir LLM'de context window artı varsa bellek.
- **Aksiyonlar** `A`. Seçimler. Yukarı/aşağı/sola/sağa hareket. Bir hamle yap. Bir token yay.
- **Geçişler** `P(s' | s, a)`. `s` state'i ve `a` aksiyonu verildiğinde sonraki state üzerinden dağılım. Satrançta deterministik, envanterde stokastik, LLM çözümlemesinde neredeyse-deterministik.
- **Ödüller** `R(s, a, s')`. Skaler sinyal. Kazanma = +1, kaybetme = -1. Gelir eksi maliyet. GRPO'daki log-likelihood oran terimi.
- **İndirim** `γ ∈ [0, 1)`. Gelecek ödülün şu ana göre ne kadar saydığı. `γ = 0.99` sana ~100 adımlık bir ufuk verir; `γ = 0.9` ~10.

**Markov özelliği** `P(s_{t+1} | s_t, a_t) = P(s_{t+1} | s_0, a_0, …, s_t, a_t)`. Gelecek yalnızca şu anki state'e bağlıdır. Eğer öyle değilse, state temsili eksik demektir — yöntemin başarısızlığı değil, state'in başarısızlığı.

**Policy'ler ve dönüşler.** Bir policy `π(a | s)` state'leri aksiyon dağılımlarına eşler. Return `G_t = r_t + γ r_{t+1} + γ² r_{t+2} + …` gelecek ödüllerin indirimli toplamıdır. Value `V^π(s) = E[G_t | s_t = s]`, `π` policy'si altında `s`'den başlayan beklenen return'dür. Q-value `Q^π(s, a) = E[G_t | s_t = s, a_t = a]` ise belirli bir aksiyonla başlayan beklenen return'dür. Her RL algoritması bu ikisinden birini tahmin eder, sonra `π`'yi buna göre iyileştirir.

**Bellman denklemleri.** Bu fazdaki her şeyin kullandığı sabit-nokta denklemleri:

`V^π(s) = Σ_a π(a|s) Σ_{s', r} P(s', r | s, a) [r + γ V^π(s')]`
`Q^π(s, a) = Σ_{s', r} P(s', r | s, a) [r + γ Σ_{a'} π(a'|s') Q^π(s', a')]`

Bunlar beklenen return'ü "bu adımın ödülü" artı "indirilmiş, indiğin yerin değeri" olarak ikiye ayırır. Yinelemeli. Faz 9'daki her algoritma ya bu denklemi yakınsamaya kadar iterate eder (dinamik programlama), ondan örnekler (Monte Carlo) ya da onu bir adım bootstrap eder (temporal difference).

## İnşa Et

### Adım 1: minik deterministik bir MDP

Bir 4×4 GridWorld. Agent sol üstte başlar, terminal sağ altta, adım başına -1 ödül, aksiyonlar `{up, down, left, right}`. `code/main.py`'a bak.

```python
GRID = 4
TERMINAL = (3, 3)
ACTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

def step(state, action):
    if state == TERMINAL:
        return state, 0.0, True
    dr, dc = ACTIONS[action]
    r, c = state
    nr = min(max(r + dr, 0), GRID - 1)
    nc = min(max(c + dc, 0), GRID - 1)
    return (nr, nc), -1.0, (nr, nc) == TERMINAL
```

Beş satır. Environment'ın tamamı bu. Deterministik geçişler, sabit adım cezası, soğurucu terminal state.

### Adım 2: bir policy'yi koştur

Bir policy, state'ten aksiyon dağılımına bir fonksiyondur. En basiti: uniform random.

```python
def uniform_policy(state):
    return {a: 0.25 for a in ACTIONS}

def rollout(policy, max_steps=200):
    s, total, steps = (0, 0), 0.0, 0
    for _ in range(max_steps):
        a = sample(policy(s))
        s, r, done = step(s, a)
        total += r
        steps += 1
        if done:
            break
    return total, steps
```

Random policy'yi 1000 kez koştur. Bu 4×4 tahta için ortalama return -60 ile -80 arası. Optimum return -6 (sağ-aşağı düz çizgi). Bu farkı kapatmak Faz 9'un tamamı.

### Adım 3: Bellman denklemi üzerinden `V^π`'yi tam olarak hesapla

Küçük MDP'ler için Bellman denklemi bir lineer sistemdir. State'leri numaralandır, beklentiyi uygula, değerler değişmeyi bırakana dek iterate et.

```python
def policy_evaluation(policy, gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in all_states()}
    while True:
        delta = 0.0
        for s in all_states():
            if s == TERMINAL:
                continue
            v = 0.0
            for a, pi_a in policy(s).items():
                s_next, r, _ = step(s, a)
                v += pi_a * (r + gamma * V[s_next])
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            return V
```

Bu iteratif policy evaluation. Sutton & Barto'daki ilk algoritma ve sonrasında gelen her RL yönteminin teorik temeli.

### Adım 4: `γ` fiziksel anlamı olan bir hiperparametredir

Etkili ufuk kabaca `1 / (1 - γ)`. `γ = 0.9` → 10 adım. `γ = 0.99` → 100 adım. `γ = 0.999` → 1000 adım.

Çok düşükse agent miyop davranır. Çok yüksekse credit assignment gürültülenir, çünkü uzak gelecekteki ödülün sorumluluğunu birçok erken adım paylaşır. LLM RLHF'i tipik olarak `γ = 1` kullanır çünkü episode'lar kısa ve sınırlıdır. Kontrol görevleri `0.95–0.99` kullanır. Uzun-ufuklu strateji oyunları `0.999`.

## Tuzaklar

- **Markov olmayan state.** Karar vermek için son üç gözlemi gerekiyorsa, "state" sadece şu anki gözlem değildir. Çözüm: frame'leri yığ (Atari'deki DQN 4'ünü yığar) ya da recurrent bir state kullan (gözlemler üzerinde LSTM/GRU).
- **Seyrek ödüller.** Yalnızca-kazan ödülleri büyük state uzaylarında öğrenmeyi neredeyse imkânsız kılar. Reward shaping yap (ara sinyal) ya da imitation ile bootstrap et (Faz 9 · 09).
- **Reward hacking.** Vekil bir ödülü optimize etmek genellikle patolojik davranış üretir. OpenAI'nin tekne yarışı agent'ı, yarışı bitirmek yerine sonsuza dek powerup toplamak için daireler çiziyordu. Ödülü daima hedef sonuçtan tanımla, vekilden değil.
- **İndirim yanlış-belirtimi.** Sonsuz-ufuklu bir görevde `γ = 1` her value'yu sonsuz yapar. Daima sonlu ufuk veya `γ < 1` ile sınırla.
- **Ödül ölçeği.** {+100, -100} ödülleri ile {+1, -1} aynı optimal policy'leri verir ama çok farklı gradyan büyüklükleri verir. PPO/DQN'e takmadan önce `[-1, 1]` civarına normalize et.

## Kullan

2026 stack'i koda dokunmadan önce her RL pipeline'ını bir MDP'ye indirger:

| Durum | State | Aksiyon | Ödül | γ |
|-------|-------|---------|------|---|
| Kontrol (lokomosyon, manipülasyon) | Eklem açıları + hızlar | Sürekli tork | Göreve özel shape'lenmiş | 0.99 |
| Oyunlar (satranç, Go, poker) | Tahta + tarihçe | Geçerli hamle | Kazan=+1 / kaybet=-1 | 1.0 (sonlu) |
| Envanter / fiyatlandırma | Stok + talep | Sipariş miktarı | Gelir - maliyet | 0.95 |
| LLM'ler için RLHF | Bağlam token'ları | Sonraki token | Sonda reward-model skoru | 1.0 (episode ~200 token) |
| Reasoning için GRPO | Prompt + kısmi cevap | Sonraki token | Sonda verifier 0/1 | 1.0 |

Herhangi bir training loop yazmadan önce beş tuple'ı yaz. "RL çalışmıyor" hata raporlarının çoğunun izi, kâğıt üstünde bozuk olan bir MDP formülasyonuna kadar gider.

## Yayınla

`outputs/skill-mdp-modeler.md` olarak kaydet:

```markdown
---
name: mdp-modeler
description: Given a task description, produce a Markov Decision Process spec and flag formulation risks before training.
version: 1.0.0
phase: 9
lesson: 1
tags: [rl, mdp, modeling]
---

Given a task (control / game / recommendation / LLM fine-tuning), output:

1. State. Exact feature vector or tensor spec. Justify Markov property.
2. Action. Discrete set or continuous range. Dimensionality.
3. Transition. Deterministic, stochastic-with-known-model, or sample-only.
4. Reward. Function and source. Sparse vs shaped. Terminal vs per-step.
5. Discount. Value and horizon justification.

Refuse to ship any MDP where the state is non-Markovian without explicit mention of frame-stacking or recurrent state. Refuse any reward that was not defined in terms of the target outcome. Flag any `γ ≥ 1.0` on an infinite-horizon task. Flag any reward range >100x the typical step reward as a likely gradient-explosion source.
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld'ü ve random-policy rollout'unu `code/main.py`'da uygula. 10.000 episode koştur. Return'ün ortalamasını ve std'sini raporla. Optimum return ile (-6) karşılaştır.
2. **Orta.** Uniform-random policy için `γ ∈ {0.5, 0.9, 0.99}` ile `policy_evaluation`'ı koştur. Her biri için `V`'yi 4×4 grid olarak yazdır. Terminal'e yakın state value'larının `γ` büyüdükçe neden daha hızlı arttığını açıkla.
3. **Zor.** GridWorld'ü stokastik yap: her aksiyon `p = 0.1` olasılıkla komşu bir yöne kayar. Uniform policy'yi yeniden değerlendir. `V[start]` daha iyi mi olur, daha kötü mü? Neden?

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| MDP | "Pekiştirmeli öğrenme kurulumu" | Markov özelliğini sağlayan `(S, A, P, R, γ)` tuple'ı. |
| State | "Agent'ın gördüğü şey" | Seçilen policy sınıfı altında gelecek dinamikler için yeterli istatistik. |
| Policy | "Agent'ın davranışı" | Koşullu dağılım `π(a | s)` ya da deterministik harita `s → a`. |
| Return | "Toplam ödül" | Şu anki adımdan itibaren indirimli toplam `Σ γ^t r_t`. |
| Value | "Bir state ne kadar iyi" | `s`'den başlayarak `π` altında beklenen return. |
| Q-value | "Bir aksiyon ne kadar iyi" | İlk aksiyon `a` ile `s`'den başlayarak `π` altında beklenen return. |
| Bellman denklemi | "Dinamik programlama özyinelemesi" | Value / Q'nun tek-adım ödül artı indirimli haleftarı value'ya sabit-nokta ayrışması. |
| İndirim `γ` | "Gelecek vs şimdi" | Uzak-gelecek ödül üzerine geometrik ağırlık; etkili ufuk `~1/(1-γ)`. |

## İleri Okuma

- [Sutton & Barto (2018). Reinforcement Learning: An Introduction, 2nd ed.](http://incompleteideas.net/book/RLbook2020.pdf) — ders kitabı. Bölüm 3 MDP'leri ve Bellman denklemlerini kapsar; Bölüm 1 sonraki her derste yatan ödül hipotezini motive eder.
- [Bellman (1957). Dynamic Programming](https://press.princeton.edu/books/paperback/9780691146683/dynamic-programming) — Bellman denkleminin kökeni.
- [OpenAI Spinning Up — Part 1: Key Concepts](https://spinningup.openai.com/en/latest/spinningup/rl_intro.html) — derin-RL açısından özlü bir MDP giriş kitapçığı.
- [Puterman (2005). Markov Decision Processes](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470316887) — MDP'ler ve kesin çözüm yöntemleri üzerine yöneylem-araştırması referansı.
- [Littman (1996). Algorithms for Sequential Decision Making (PhD thesis)](https://www.cs.rutgers.edu/~mlittman/papers/thesis-main.pdf) — MDP'lerin bir dinamik-programlama özelleşmesi olarak en temiz türetilişi.
