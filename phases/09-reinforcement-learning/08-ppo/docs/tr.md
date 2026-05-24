# Proximal Policy Optimization (PPO)

> A2C her rollout'u bir güncellemeden sonra atar. PPO, policy gradient'ı clip'lenmiş bir importance ratio'ya sarar, böylece aynı veride policy patlamadan 10+ epoch yapabilirsin. Schulman et al. (2017). 2026'da hâlâ varsayılan policy-gradient algoritması.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 06 (REINFORCE), Faz 9 · 07 (Actor-Critic)
**Süre:** ~75 dakika

## Sorun

A2C (Ders 07) on-policy'dir: `E_{π_θ}[A · ∇ log π_θ]` gradyanı *şu anki* `π_θ`'dan örneklenmiş veri ister. Bir güncelleme al ve `π_θ` değişir; kullandığın veri artık off-policy'dir. Onu tekrar kullan, gradyanın biased olur.

Rollout'lar pahalıdır. Atari'de, 8 env × 128 adım = 1024 geçiş ve onlarca saniyelik environment zamanı. Bunu bir gradyan adımından sonra atmak israftır.

Trust Region Policy Optimization (TRPO, Schulman 2015) ilk düzeltmeydi: her güncellemeyi eski ve yeni policy arasındaki KL diverjansı `δ`'nın altında kalacak şekilde sınırla. Teorik olarak temiz, ama güncelleme başına conjugate-gradient çözümü ister. 2026'da kimse TRPO koşturmuyor.

PPO (Schulman et al. 2017) sert trust-region kısıtlamasını basit bir clip'lenmiş hedef ile değiştirir. Bir satır fazla kod. Rollout başına on epoch. Conjugate gradient yok. Yeterince-iyi teorik garantiler. Dokuz yıl sonra hâlâ MuJoCo'dan RLHF'e kadar her şey için varsayılan policy-gradient algoritması.

## Kavram

![PPO clip'lenmiş surrogate hedefi: 1 ± ε'da ratio clipping](../assets/ppo.svg)

**Importance ratio.**

`r_t(θ) = π_θ(a_t | s_t) / π_{θ_old}(a_t | s_t)`

Bu, yeni policy ile veriyi toplayan policy'nin likelihood oranıdır. `r_t = 1` değişiklik yok demektir. `r_t = 2` yeni policy'nin `a_t`'yi alma olasılığının eskisinin iki katı olması demektir.

**Clip'lenmiş surrogate.**

`L^{CLIP}(θ) = E_t [ min( r_t(θ) A_t, clip(r_t(θ), 1-ε, 1+ε) A_t ) ]`

İki terim:

- Advantage `A_t > 0` ise ve ratio `1 + ε`'nin ötesine geçmeye çalışırsa, clip gradyanı düzleştirir — iyi bir aksiyonu eski olasılığın `+ε` üzerine itme.
- Advantage `A_t < 0` ise ve ratio `1 - ε`'nin ötesine geçmeye çalışırsa (yani kötü bir aksiyonu clip'lenmiş azalmasına göre daha olası yapacaksak), clip gradyanı sınırlar — kötü bir aksiyonu `-ε`'nin altına itme.

`min` diğer yönü ele alır: ratio *yararlı* yönde hareket ettiyse, gradyanı hâlâ alırsın (sana zarar verecek tarafta clipping yok).

Tipik `ε = 0.2`. Hedefi `r_t`'nin fonksiyonu olarak çiz: "iyi tarafta" düz çatılı, "kötü tarafta" düz tabanlı parçalı-lineer bir fonksiyon.

**Tam PPO loss'u.**

`L(θ, φ) = L^{CLIP}(θ) - c_v · (V_φ(s_t) - V_t^{target})² + c_e · H(π_θ(·|s_t))`

A2C ile aynı actor-critic yapısı. Üç katsayı, genelde `c_v = 0.5`, `c_e = 0.01`, `ε = 0.2`.

**Training döngüsü.**

1. `N` paralel env üzerinde her biri için `T` adım, `N × T` geçiş topla.
2. Advantage'ları (GAE) hesapla, sabitler olarak dondur.
3. `π_{θ_old}`'i şu anki `π_θ`'nın bir snapshot'ı olarak dondur.
4. `K` epoch için, her `(s, a, A, V_target, log π_old(a|s))` minibatch'i için:
   - `r_t(θ) = exp(log π_θ(a|s) - log π_old(a|s))` hesapla.
   - `L^{CLIP}` + value loss + entropy uygula.
   - Gradient adımı.
5. Rollout'u at. 1. adıma dön.

`K = 10` ve 64 minibatch boyutu standart bir hiperparametre setidir. PPO sağlamdır: kesin sayılar genelde ±%50 içinde önemli değildir.

**KL-cezalı varyant.** Orijinal makale uyarlanır bir KL cezası kullanan alternatif önerdi: `L = L^{PG} - β · KL(π_θ || π_old)`, `β` gözlenen KL'e göre ayarlanır. Clipping versiyonu hâkim oldu; KL varyantı RLHF'te yaşıyor (orada referans policy'ye KL zaten istediğin ayrı bir kısıtlama).

## İnşa Et

### Adım 1: rollout sırasında `log π_old(a | s)`'i yakala

```python
for step in range(T):
    probs = softmax(logits(theta, state_features(s)))
    a = sample(probs, rng)
    s_next, r, done = env.step(s, a)
    buffer.append({
        "s": s, "a": a, "r": r, "done": done,
        "v_old": value(w, state_features(s)),
        "log_pi_old": log(probs[a] + 1e-12),
    })
    s = s_next
```

Snapshot bir kez, rollout sırasında alınır. Güncelleme epoch'ları sırasında değişmez.

### Adım 2: GAE advantage'larını hesapla (Ders 07)

A2C ile aynı. Batch üzerinde normalize et.

### Adım 3: clip'lenmiş surrogate güncellemesi

```python
for _ in range(K_EPOCHS):
    for mb in minibatches(buffer, size=64):
        for rec in mb:
            x = state_features(rec["s"])
            probs = softmax(logits(theta, x))
            logp = log(probs[rec["a"]] + 1e-12)
            ratio = exp(logp - rec["log_pi_old"])
            adv = rec["advantage"]
            surrogate = min(
                ratio * adv,
                clamp(ratio, 1 - EPS, 1 + EPS) * adv,
            )
            # backprop -surrogate, value loss ekle, entropy çıkar
            grad_logpi = onehot(rec["a"]) - probs
            if (adv > 0 and ratio >= 1 + EPS) or (adv < 0 and ratio <= 1 - EPS):
                pg_grad = 0.0  # clip'lenmiş
            else:
                pg_grad = ratio * adv
            for i in range(N_ACTIONS):
                for j in range(N_FEAT):
                    theta[i][j] += LR * pg_grad * grad_logpi[i] * x[j]
```

"Clip'lenmiş → sıfır gradyan" deseni PPO'nun kalbidir. Yeni policy yararlı yönde çok uzağa kaymışsa, güncelleme durur.

### Adım 4: value ve entropy

A2C ile aynı şekilde critic hedefine standart MSE ve actor üzerine entropy bonusu ekle.

### Adım 5: diagnostics

Her güncellemede izlenecek üç şey:

- **Ortalama KL** `E[log π_old - log π_θ]`. `[0, 0.02]`'de kalmalı. `0.1`'i geçerse, `K_EPOCHS` veya `LR`'yi azalt.
- **Clip oranı** — ratio'su `[1-ε, 1+ε]` dışında olan örneklerin oranı. `~0.1-0.3` olmalı. `~0` ise, clip hiç tetiklenmiyor → `LR` veya `K_EPOCHS`'u artır. `~0.5+` ise, rollout'u overfit ediyorsun → onları azalt.
- **Açıklanan varyans** `1 - Var(V_target - V_pred) / Var(V_target)`. Critic kalite metriği. Critic öğrendikçe 1'e doğru tırmanmalı.

## Tuzaklar

- **Clip katsayısı yanlış tune edilmiş.** `ε = 0.2` de-facto standart. `0.1`'e gitmek güncellemeleri çok ürkek yapar; `0.3+` instabiliteyi davet eder.
- **Çok fazla epoch.** `K > 20` rutin olarak instabilite üretir çünkü policy `π_old`'den uzaklaşır. Epoch'ları sınırla, özellikle büyük ağlar için.
- **Ödül normalizasyonu yok.** Büyük ödül ölçekleri clip aralığını yer. Advantage'ları hesaplamadan önce ödülleri normalize et (running std).
- **Advantage normalizasyonunu unutmak.** Batch başına sıfır-ortalama/birim-std normalizasyonu standarttır. Atlamak çoğu benchmark'ta PPO'yu mahveder.
- **Learning rate bozulmamış.** PPO sıfıra lineer LR bozulmasından faydalanır. Sabit LR genelde daha kötüdür.
- **Importance ratio matematik hataları.** Sayısal kararlılık için daima `exp(log_new - log_old)`, `new / old` değil.
- **Yanlış gradyan işareti.** Surrogate'i maksimize et = `-L^{CLIP}`'i *minimize* et. İşareti çevirmek en yaygın PPO bug'ıdır.

## Kullan

PPO 2026'nın varsayılan RL algoritmasıdır, şaşırtıcı sayıda alanda:

| Kullanım durumu | PPO varyantı |
|-----------------|--------------|
| MuJoCo / robotik kontrol | Gauss policy'li, GAE(0.95)'li PPO |
| Atari / diskret oyunlar | Categorical policy'li, kayan 128-adım rollout'lu PPO |
| LLM'ler için RLHF | Referans modeline KL cezalı PPO, cevap sonunda RM'den ödül |
| Büyük ölçekli oyun agent'ları | IMPALA + PPO (AlphaStar, OpenAI Five) |
| Reasoning LLM'leri | GRPO (Ders 12) — critic'siz PPO varyantı |
| Yalnızca preference verisi | DPO — PPO+KL'nin kapalı-formuluna indirgenmiş, online örnekleme yok |

PPO *loss şekli* — clip'lenmiş surrogate + value + entropy — DPO, GRPO ve neredeyse her RLHF pipeline'ının iskelesidir.

## Yayınla

`outputs/skill-ppo-trainer.md` olarak kaydet:

```markdown
---
name: ppo-trainer
description: Produce a PPO training config and a diagnostic plan for a given environment.
version: 1.0.0
phase: 9
lesson: 8
tags: [rl, ppo, policy-gradient]
---

Given an environment and training budget, output:

1. Rollout size. `N` envs × `T` steps.
2. Update schedule. `K` epochs, minibatch size, LR schedule.
3. Surrogate params. `ε` (clip), `c_v`, `c_e`, advantage normalization on.
4. Advantage. GAE(`λ`) with explicit `γ` and `λ`.
5. Diagnostics plan. KL, clip fraction, explained variance thresholds with alerts.

Refuse `K > 30` or `ε > 0.3` (unsafe trust region). Refuse any PPO run without advantage normalization or KL/clip monitoring. Flag clip fraction sustained above 0.4 as drift.
```

## Alıştırmalar

1. **Kolay.** 4×4 GridWorld'de `ε=0.2, K=4` ile PPO koştur. Eşleşen env adımlarında A2C'nin (rollout başına bir epoch) örnek verimliliğiyle karşılaştır.
2. **Orta.** `K ∈ {1, 4, 10, 30}` üzerinde tara. Return vs env adımları çiz ve güncelleme başına ortalama KL'yi takip et. Bu görevde `K` hangi değerde KL patlıyor?
3. **Zor.** Clip'lenmiş surrogate'i uyarlanır bir KL cezasıyla (`KL > 2·target` ise `β` iki katına, `KL < target/2` ise yarıya) değiştir. Son return, kararlılık ve clip-bağımsızlığı karşılaştır.

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Importance ratio | "r_t(θ)" | `π_θ(a|s) / π_old(a|s)`; veriyi toplayan policy'den sapma. |
| Clip'lenmiş surrogate | "PPO'nun ana trick'i" | `min(r·A, clip(r, 1-ε, 1+ε)·A)`; yararlı tarafta clip'in ötesinde düz gradyan. |
| Trust region | "TRPO / PPO niyeti" | Monotonik iyileşmeyi garanti etmek için her güncellemenin KL'sini sınırla. |
| KL cezası | "Yumuşak trust region" | Alternatif PPO: `L - β · KL(π_θ || π_old)`. Uyarlanır `β`. |
| Clip oranı | "Clipping ne sıklıkta tetikleniyor" | Diagnostic — 0.1-0.3 olmalı; dışı yanlış tune anlamına gelir. |
| Çok-epoch eğitim | "Veri tekrar kullanımı" | Her rollout üzerinde K epoch; varyans maliyetiyle örnek verimliliği için değiş tokuş. |
| On-policy-ish | "Çoğunlukla on-policy" | PPO nominal olarak on-policy'dir ama K>1 epoch hafifçe-off-policy veriyi güvenle kullanır. |
| PPO-KL | "Diğer PPO" | KL-cezalı varyant; KL-to-reference'in zaten bir kısıtlama olduğu RLHF'te kullanılır. |

## İleri Okuma

- [Schulman et al. (2017). Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347) — makale.
- [Schulman et al. (2015). Trust Region Policy Optimization](https://arxiv.org/abs/1502.05477) — TRPO, PPO'nun öncülü.
- [Andrychowicz et al. (2021). What Matters In On-Policy RL? A Large-Scale Empirical Study](https://arxiv.org/abs/2006.05990) — her PPO hiperparametresi ablation'lanmış.
- [Ouyang et al. (2022). Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — InstructGPT; RLHF içinde PPO reçetesi.
- [OpenAI Spinning Up — PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html) — PyTorch ile temiz modern sunum.
- [CleanRL PPO implementation](https://github.com/vwxyzjn/cleanrl) — birçok makalenin kullandığı referans tek-dosya PPO.
- [Hugging Face TRL — PPOTrainer](https://huggingface.co/docs/trl/main/en/ppo_trainer) — dil modelleri üzerinde PPO için production reçetesi; Ders 09 (RLHF) ile birlikte oku.
- [Engstrom et al. (2020). Implementation Matters in Deep Policy Gradients](https://arxiv.org/abs/2005.12729) — "37 kod-seviyesi optimizasyon" makalesi; hangi PPO trick'leri yük taşıyor, hangileri folklor.
