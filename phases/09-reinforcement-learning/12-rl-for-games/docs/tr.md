# Oyunlar için RL — AlphaZero, MuZero ve LLM-Reasoning Çağı

> 1992: TD-Gammon saf TD ile backgammon'da insan şampiyonları yendi. 2016: AlphaGo, Lee Sedol'u yendi. 2017: AlphaZero satranç, shogi ve Go'da sıfırdan hâkim oldu. 2024: DeepSeek-R1, PPO'nun yerini GRPO alarak aynı reçetenin reasoning üzerinde çalıştığını kanıtladı. Oyunlar, bu fazdaki her atılımı süren benchmark'tır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 05 (DQN), Faz 9 · 08 (PPO), Faz 9 · 09 (RLHF), Faz 9 · 10 (MARL)
**Süre:** ~120 dakika

## Sorun

Oyunlar RL'in istediği her şeye sahiptir. Temiz ödül (kazan/kaybet). Sonsuz episode'lar (self-play reset'leri). Mükemmel simülasyon (oyun *simülatörün kendisi*). Diskret ya da küçük sürekli aksiyon uzayları. Rekabetçi sağlamlığı zorlayan multi-agent yapı.

Ve her büyük RL atılımı oyunlarda test edildi. TD-Gammon (backgammon, 1992). Atari-DQN (2013). AlphaGo (2016). AlphaZero (2017). OpenAI Five (Dota 2, 2019). AlphaStar (StarCraft II, 2019). MuZero (öğrenilmiş model, 2019). AlphaTensor (matris çarpımı, 2022). AlphaDev (sıralama algoritmaları, 2023). DeepSeek-R1 (matematik reasoning, 2025) — game-RL tekniklerinin metin üzerinde çalıştığının en yeni gösterimi.

Bu bitirme dersi üç işaret-mimari'sini — AlphaZero, MuZero ve GRPO — tek bir birleştirici mercek üzerinden inceler: **self-play + search + policy improvement**. Her biri öncekini genelleştirir; GRPO özellikle AlphaZero'nun reçetesinin LLM reasoning'e uygulanmış halidir, token'lar aksiyon ve matematiksel doğrulama kazanma sinyali olarak.

## Kavram

![AlphaZero ↔ MuZero ↔ GRPO: aynı döngü, farklı environment'lar](../assets/rl-games.svg)

**Birleştirici döngü.**

```
while True:
    trajectory = self_play(current_policy, search)     # kendine karşı oyna
    policy_target = search.improved_policy(trajectory) # search ham policy'yi iyileştirir
    policy_net.update(policy_target, value_target)     # search çıktısı üzerinde supervised
```

**AlphaZero (2017).** Silver et al. Bilinen kuralları olan bir oyun (satranç, shogi, Go) verildiğinde:

- Policy-value network'ü: tek bir kule `f_θ(s) → (p, v)`. `p` geçerli hamleler üzerinde bir prior'dır. `v` beklenen oyun sonucudur.
- Monte Carlo Tree Search (MCTS): her hamlede, olası devamlarının bir ağacını genişlet. Prior + bootstrap olarak `(p, v)` kullan. Düğümleri UCB (PUCT) ile seç: `a* = argmax Q(s, a) + c · p(a|s) · √N(s) / (1 + N(s, a))`.
- Self-play: agent'a-karşı-agent oyunlar oyna. `t` hamlesinde, MCTS ziyaret dağılımı `π_t` policy eğitim hedefi olur.
- Loss: `L = (v - z)² - π · log p + c · ||θ||²`. `z` oyun sonucudur (+1 / 0 / -1).

Sıfır insan bilgisi. Sıfır el yapımı sezgisel. Her birinde onlarca milyon self-play oyunundan sonra satranç, shogi ve Go'ya hâkim olan tek bir reçete.

**MuZero (2019).** Schrittwieser et al. Kuralların bilindiği gereksinimini kaldırır.

- Sabit bir environment yerine, *latent dinamik modeli* `(h, g, f)` öğren:
  - `h(s)`: gözlemi latent state'e kodla.
  - `g(s_latent, a)`: sonraki latent state + ödülü tahmin et.
  - `f(s_latent)`: policy prior + value tahmin et.
- MCTS *öğrenilmiş latent uzayda* koşar. Aynı search, aynı eğitim döngüsü.
- Go, satranç, shogi *ve* Atari üzerinde çalışır — tek algoritma, kural bilgisi yok.

**Stochastic MuZero (2022).** Stokastik dinamikler ve şans düğümleri ekler; backgammon-sınıfı oyunlara genişler.

**Muesli, Gumbel MuZero (2022-2024).** Örnek verimliliği ve deterministik search üzerinde iyileştirmeler.

**GRPO (2024-2025).** DeepSeek-R1 reçetesi. Dil-modeli reasoning'e uygulanmış aynı AlphaZero-şekilli döngü:

- "Oyun": bir matematik / kodlama / reasoning problemini cevapla. "Kazanma" = verifier (test case'i geçti, sayısal cevap eşleşti) 1 döndürür.
- Policy: LLM. Aksiyonlar: token'lar. State: prompt + cevap-şimdiye kadar.
- Critic yok (PPO-stili V_φ). Bunun yerine, her prompt için, policy'den `G` tamamlama örnekle. Her biri için ödülü hesapla. REINFORCE-stili güncelleme için sinyal olarak **grup-göreceli advantage** `A_i = (r_i - mean_r) / std_r` kullan.
- Kaymayı önlemek için referans policy'ye KL cezası (RLHF gibi).
- Tam loss:

  `L_GRPO(θ) = -E_{q, {o_i}} [ (1/G) Σ_i A_i · log π_θ(o_i | q) ] + β · KL(π_θ || π_ref)`

Reward model yok, critic yok, MCTS yok. Grup-göreceli baseline üçünü de değiştirir. Hesaplamanın bir kısmıyla reasoning benchmark'larında PPO-RLHF kalitesini eşleştirir ya da aşar.

**R1 reçetesinin tamamı.** DeepSeek-R1 (DeepSeek 2025) tek bir makalede iki model:

- **R1-Zero.** DeepSeek-V3 base modelinden başla. SFT yok. İki ödül bileşeniyle doğrudan GRPO uygula: *doğruluk ödülü* (kural-tabanlı — son cevap doğru sayıya parse edildi mi / kod unit test'leri geçti mi) ve *format ödülü* (tamamlama chain-of-thought'unu `<think>…</think>` tag'leriyle sardı mı). Binlerce adımda, ortalama cevap uzunluğu ~100'den ~10.000 token'a büyür ve matematik benchmark skorları o1-preview'a yakın seviyelere tırmanır. Model sıfırdan akıl yürütmeyi öğrenir. Dezavantaj: chain-of-thought'ları çoğu zaman okunamaz, dilleri karıştırır ve stilistik cilaya sahip değildir.
- **R1.** R1-Zero'nun okunabilirlik problemlerini dört aşamalı bir pipeline ile düzelt:
  1. **Cold-start SFT.** Temiz formatlama ile birkaç bin uzun-CoT gösterimi topla. Base modeli onlar üzerinde supervised-finetune et. Bu okunabilir bir başlangıç noktası verir.
  2. **Reasoning-yönelimli GRPO.** Doğruluk+format ödülleri artı kod-değişimini önlemek için bir *dil-tutarlılığı* ödülü ile GRPO uygula.
  3. **Rejection sampling + SFT 2. tur.** RL checkpoint'inden ~600K reasoning trajectory'si örnekle, yalnızca doğru son cevaplı ve okunabilir CoT'lulara tut ve ~200K non-reasoning SFT örneğiyle (yazma, QA, self-cognition) birleştir. Base'i tekrar fine-tune et.
  4. **Full-spectrum GRPO.** Hem reasoning'i (kural-tabanlı ödüller) hem genel hizalamayı (yardımseverlik/zararsızlık preference-tabanlı ödüller) kapsayan bir RL turu daha.

Sonuç açık ağırlıklarla AIME ve MATH-500'de o1 ile eşleşir ve damıtılacak kadar küçüktür. Aynı makale ayrıca R1'in reasoning izleri üzerinde SFT'leyerek altı damıtılmış yoğun model (Qwen-1.5B'den Llama-70B'ye) yayınlar — student'ta RL yok. Güçlü bir RL teacher'ının damıtımı, student ölçeğinde sıfırdan RL'yi sürekli olarak yener.

**Reasoning için neden PPO yerine GRPO.** DeepSeekMath makalesinde (Şubat 2024) üç sebep: (1) eğitilecek value network yok, belleği yarıya indirir; (2) grup baseline'ı reasoning görevlerinin ürettiği seyrek son-trajectory ödülü doğal olarak halleder; (3) prompt başına normalizasyon, advantage'ları çılgınca farklı zorluktaki problemler arasında karşılaştırılabilir yapar, bunu PPO'nun tek critic'i yapamaz.

**Search-free vs search-based.** Oyunlar dallandı:

- *Uzun ufuklu mükemmel-bilgili oyunlar* (Go, satranç): hâlâ search-tabanlı. AlphaZero / MuZero hâkim.
- *LLM reasoning*: production'da henüz MCTS yok; tam rollout'lar üzerinde GRPO, inference compute'u için best-of-N. Process reward modelleri (PRM'ler) adım seviyesinde search'ün geri eklendiğine işaret ediyor.

## İnşa Et

`code/main.py`'daki kod **GRPO'yu miniatürde** uygular — birden fazla örnek grubuyla bir bandit. Algoritma bir LLM'dekiyle aynı; yalnızca policy ve environment daha basit. *Loss*'u ve 2025 yeniliği olan *grup-göreceli advantage*'ı öğretir.

### Adım 1: minik bir verifier environment'ı

```python
QUESTIONS = [
    {"prompt": "q1", "correct": 3},
    {"prompt": "q2", "correct": 1},
]

def verify(prompt_idx, answer_token):
    return 1.0 if answer_token == QUESTIONS[prompt_idx]["correct"] else 0.0
```

Gerçek GRPO'da verifier unit test'leri koşar ya da matematik eşitliği kontrol eder.

### Adım 2: policy: prompt başına K cevap token'ı üzerinde softmax

```python
def policy_probs(theta, p_idx):
    return softmax(theta[p_idx])
```

Bir prompt'la koşullanmış bir LLM'in son-katman çıktısına eşdeğer.

### Adım 3: grup örnekleme ve grup-göreceli advantage

```python
def grpo_step(theta, p_idx, G=8, beta=0.01, lr=0.1, rng=None):
    probs = policy_probs(theta, p_idx)
    samples = [sample(probs, rng) for _ in range(G)]
    rewards = [verify(p_idx, s) for s in samples]
    mean_r = sum(rewards) / G
    std_r = stddev(rewards) + 1e-8
    advs = [(r - mean_r) / std_r for r in rewards]

    for a, A in zip(samples, advs):
        grad = onehot(a) - probs
        for i in range(len(probs)):
            theta[p_idx][i] += lr * A * grad[i]
    # KL cezası: theta'yı referansa doğru çek
    for i in range(len(probs)):
        theta[p_idx][i] -= beta * (theta[p_idx][i] - reference[p_idx][i])
```

Grup-göreceli advantage 2024 DeepSeek trick'idir. Critic gerekmez. "Baseline" grup ortalaması, normalizasyon grup std'sini kullanır.

### Adım 4: REINFORCE baseline (value-free) ile karşılaştır

Aynı kurulum, aynı compute, düz REINFORCE. GRPO daha hızlı ve daha kararlı yakınsar.

### Adım 5: entropy ve KL'yi gözlemle

RLHF ile aynı diagnostics: referansa ortalama KL, policy entropy'si, zaman içinde ödül. Bunlar kararlılaştığında eğitim biter.

## Tuzaklar

- **Verifier gaming üzerinden reward hacking.** GRPO RLHF'in riskini miras alır: verifier yanlışsa ya da sömürülebilirse, LLM sömürüyü bulur. Sağlam verifier'lar (birden fazla test case, formel ispatlar) önemlidir.
- **Grup boyutu çok küçük.** Grup baseline'ının varyansı `1/√G` gibi gider. `G = 4`'ün altında, advantage sinyali gürültülüdür; standart seçim `G = 8` ile `64`.
- **Length bias.** Farklı uzunluklardaki LLM tamamlamalarının farklı log-olasılıkları vardır. Token sayısına göre normalize et ya da sekans-seviyesi log-prob kullan ya da max uzunluğa kes.
- **Saf self-play döngüleri.** AlphaZero-stili eğitim genel-toplamlı oyunlarda hâkimiyet döngülerinde takılabilir. Çeşitli rakip havuzlarıyla (league play, Ders 10) hafifletilir.
- **Search-policy uyumsuzluğu.** AlphaZero policy'yi search çıktısını taklit edecek şekilde eğitir. Policy net'i search dağılımını temsil etmek için çok küçükse, eğitim durur.
- **Compute tabanı.** MuZero / AlphaZero devasa compute ister. Tek bir ablation çoğu zaman yüzlerce GPU-saatidir. Öğrenme için minyatür demo'lar var (örn. Connect Four üzerinde AlphaZero).
- **Verifier kapsama.** Hatalı bir çözüm için geçen unit test'leri hatayı pekiştirir. Edge case'leri yakalayan verifier'lar tasarla.

## Kullan

2026 game-RL manzarası, alana göre:

| Alan | Hâkim yöntem |
|------|--------------|
| İki oyunculu sıfır-toplamlı tahta oyunları (Go, satranç, shogi) | AlphaZero / MuZero / KataGo |
| Eksik bilgili kart oyunları (poker) | CFR + deep learning (DeepStack, Libratus, Pluribus) |
| Atari / piksel oyunları | Muesli / MuZero / IMPALA-PPO |
| Büyük multiplayer strateji (Dota, StarCraft) | PPO + self-play + league (OpenAI Five, AlphaStar) |
| LLM matematik/kod reasoning | GRPO (DeepSeek-R1, Qwen-RL, açık replikasyonlar) |
| LLM hizalama | DPO / RLHF-PPO (GRPO değil; verifier preference, doğrulanabilir değil) |
| Robotik | PPO + DR (game-RL değil ama aynı policy-gradient araçlarını kullanır) |
| Kombinatoryal problemler | AlphaZero varyantları (AlphaTensor, AlphaDev) |

*Reçete* — self-play, search-augmented improvement, policy distillation — metin, piksel ve fiziksel kontrolü kapsar. GRPO en genç örnek; daha fazlası geliyor.

## Yayınla

`outputs/skill-game-rl-designer.md` olarak kaydet:

```markdown
---
name: game-rl-designer
description: Design a game-RL or reasoning-RL training pipeline (AlphaZero / MuZero / GRPO) for a given domain.
version: 1.0.0
phase: 9
lesson: 12
tags: [rl, alphazero, muzero, grpo, self-play]
---

Given a target (perfect-info game / imperfect-info / Atari / LLM reasoning / combinatorial), output:

1. Environment fit. Known rules? Markov? Stochastic? Multi-agent? Informs AlphaZero vs MuZero vs GRPO.
2. Search strategy. MCTS (PUCT with learned prior), Gumbel-sampled, best-of-N, or none.
3. Self-play plan. Symmetric self-play / league / offline data / verifier-generated.
4. Target signal. Game outcome / verifier reward / preference / learned model. Include robustness plan.
5. Diagnostics. Win rate vs baseline, ELO curve, verifier pass rate, KL to reference.

Refuse AlphaZero on imperfect-info games (route to CFR). Refuse GRPO without a trusted verifier. Refuse any game-RL pipeline without a fixed baseline opponent set (self-play ELO is uncalibrated otherwise).
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki GRPO bandit'ini uygula. 2 prompt × her biri 4 cevap token'ı üzerinde eğit. `G=8` ile < 1.000 güncellemede yakınsa.
2. **Orta.** PPO (clip'lenmiş) ve düz REINFORCE tak. Aynı bandit üzerinde GRPO ile örnek verimliliğini ve ödül varyansını karşılaştır.
3. **Zor.** Uzunluk-2 bir "reasoning zinciri"ne genişlet: agent iki token yayar ve verifier çifti ödüllendirir. GRPO'nun iki-adımlı sekanslar arasında credit assignment'ı nasıl ele aldığını ölç. (İpucu: grup advantage'ını *tam sekans* başına hesapla, ikisini de token konumlarına yay.)

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| MCTS | "Öğrenilmiş net ile ağaç araması" | Monte Carlo Tree Search; öğrenilmiş `(p, v)` prior'ları ile UCB1/PUCT seçimi. |
| AlphaZero | "Self-play + MCTS" | MCTS ziyaretlerini ve oyun sonucunu eşleştirmek için eğitilmiş policy-value net'i. |
| MuZero | "Öğrenilmiş-modelli AlphaZero" | Aynı döngü ama öğrenilmiş dinamikler üzerinden latent uzayda. |
| GRPO | "Critic-free PPO" | Group Relative Policy Optimization; grup-ortalama baseline + KL ile REINFORCE. |
| PUCT | "AlphaZero'nun UCB'si" | `Q + c · p · √N / (1 + N_a)` — value tahminini prior ile dengeler. |
| Self-play | "Agent vs geçmiş kendisi" | Sıfır-toplamlı için standart; simetrik eğitim sinyali. |
| League play | "Popülasyon-tabanlı self-play" | Geçmiş + şu anki + exploiter'lar rakip olarak örneklenir. |
| Verifier reward | "Doğrulanabilir RL" | Ödül deterministik bir checker'dan gelir (test'ler geçer, cevap eşleşir). |
| Process reward | "PRM" | Yalnızca son cevabı değil, her reasoning adımını skorlar. |

## İleri Okuma

- [Silver et al. (2017). Mastering the game of Go without human knowledge (AlphaGo Zero)](https://www.nature.com/articles/nature24270).
- [Silver et al. (2018). A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play (AlphaZero)](https://www.science.org/doi/10.1126/science.aar6404).
- [Schrittwieser et al. (2020). Mastering Atari, Go, chess and shogi by planning with a learned model (MuZero)](https://www.nature.com/articles/s41586-020-03051-4).
- [Vinyals et al. (2019). Grandmaster level in StarCraft II (AlphaStar)](https://www.nature.com/articles/s41586-019-1724-z).
- [DeepSeek-AI (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models (GRPO)](https://arxiv.org/abs/2402.03300) — GRPO'yu ve grup-göreceli baseline'ı tanıtan makale.
- [DeepSeek-AI (2025). DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) — tam dört aşamalı R1 reçetesi artı R1-Zero ablation'ı.
- [Brown et al. (2019). Superhuman AI for multiplayer poker (Pluribus)](https://www.science.org/doi/10.1126/science.aay2400) — ölçekte CFR + deep-learning.
- [Tesauro (1995). Temporal Difference Learning and TD-Gammon](https://dl.acm.org/doi/10.1145/203330.203343) — her şeyi başlatan makale.
- [Hugging Face TRL — GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer) — özel ödül fonksiyonlarıyla GRPO uygulamak için production referansı.
- [Qwen Team (2024). Qwen2.5-Math — GRPO replication](https://github.com/QwenLM/Qwen2.5-Math) — birden fazla ölçekte R1 reçetesinin açık replikasyonu.
- [Sutton & Barto (2018). Ch. 17 — Frontiers of Reinforcement Learning](http://incompleteideas.net/book/RLbook2020.pdf) — R1'in LLM ölçeğinde örneklediği self-play, search ve "tasarlanmış ödül" için ders kitabı çerçevelemesi.
