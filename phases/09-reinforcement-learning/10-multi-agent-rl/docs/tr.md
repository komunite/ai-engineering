# Multi-Agent RL

> Tek agent'lı RL environment'ın durağan olduğunu varsayar. Aynı dünyaya iki öğrenen agent koy ve bu varsayım kırılır: her agent diğerinin environment'ının bir parçası ve ikisi de değişiyor. Multi-agent RL, Markov varsayımı artık geçerli olmadığında öğrenmeyi yakınsatmak için trick'lerin bütünüdür.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 9 · 04 (Q-learning), Faz 9 · 06 (REINFORCE), Faz 9 · 07 (Actor-Critic)
**Süre:** ~45 dakika

## Sorun

Odada gezinmeyi öğrenen bir robot, tek-agent'lı bir RL problemidir. Bir futbol takımı değildir. AlphaStar vs StarCraft rakipleri değildir. Teklif veren agent'lardan oluşan bir pazaryeri değildir. Dört yollu durakta pazarlık eden iki araba değildir. Gerçek dünyadaki çok-üzerine-çok problemleri değildir.

Her multi-agent ayarında, herhangi bir agent'ın bakış açısından, diğer agent'lar environment'ın *bir parçasıdır*. Onlar öğrendikçe ve davranışlarını değiştirdikçe, environment non-stationary olur. Markov özelliği — "sonraki state yalnızca şu anki state'e ve benim aksiyonuma bağlı" — ihlal edilir çünkü sonraki state aynı zamanda *diğer* agent'ların ne seçtiğine de bağlıdır ve onların policy'leri hareketli hedeflerdir.

Bu tablo formundaki yakınsama kanıtlarını kırar (Q-learning'in garantisi durağan environment varsayar). Naif derin RL'i de kırar: agent'lar birbirini döngülerde kovalar, hiç kararlı bir policy'ye yakınsamaz. Multi-agent'a özgü tekniklere ihtiyacın var: centralized training / decentralized execution, counterfactual baseline'lar, league play, self-play.

2026 uygulamaları: robot sürüleri, trafik yönlendirme, otonom araç filoları, pazar simülatörleri, multi-agent LLM sistemleri (Faz 16) ve birden fazla akıllı oyuncuya sahip her oyun.

## Kavram

![Dört MARL rejimi: indep, centralized critic, self-play, league](../assets/marl.svg)

**Formalizm: Markov Game.** Bir MDP'in genelleştirmesi: state'ler `S`, joint aksiyon `a = (a_1, …, a_n)`, geçiş `P(s' | s, a)` ve agent başına ödüller `R_i(s, a, s')`. Her agent `i` kendi policy'si `π_i` altında kendi return'ünü maksimize eder. Ödüller aynıysa, **tamamen kooperatif**tir. Sıfır-toplamlıysa, **rekabetçi**dir. Karışıksa, **genel-toplamlı**dır.

**Temel zorluklar:**

- **Non-stationarity.** `i` agent'ının görüşünden `P(s' | s, a_i)`, değişmekte olan `π_{-i}`'ye bağlıdır.
- **Credit assignment.** Paylaşılan bir ödülle, ona hangi agent sebep oldu?
- **Exploration koordinasyonu.** Agent'lar tamamlayıcı stratejileri explore etmeli, aynı state'i fazlasıyla explore etmemeli.
- **Ölçeklenebilirlik.** Joint aksiyon uzayı `n`'de üstel olarak büyür.
- **Kısmi gözlemlenebilirlik.** Her agent yalnızca kendi gözlemini görür; küresel state gizlidir.

**Dört hâkim rejim:**

**1. Bağımsız Q-learning / bağımsız PPO (IQL, IPPO).** Her agent kendi Q veya policy'sini öğrenir, diğerlerini environment'ın parçası olarak ele alır. Basit, bazen çalışır (özellikle bir agent-modelleme yumuşatma trick'i gibi davranan experience replay ile). Teorik yakınsama: yok. Pratikte: gevşek-bağlı görevler için iyi, sıkı-bağlı olanlar için kötü.

**2. Centralized training, decentralized execution (CTDE).** En yaygın modern paradigma. Her agent'ın kendi *policy*'si `π_i` vardır, yerel gözlem `o_i` üzerinde koşullanır — deployment'ta standart decentralized execution. *Eğitim* sırasında, centralized bir critic `Q(s, a_1, …, a_n)` tam küresel state ve joint aksiyon üzerinde koşullanır. Örnekler:
- **MADDPG** (Lowe et al. 2017): agent başına centralized critic'li DDPG.
- **COMA** (Foerster et al. 2017): counterfactual baseline — "yerine `a'` aksiyonunu alsaydım ödülüm ne olurdu?" — benim katkımı izole eder.
- **MAPPO** / paylaşılan critic'li **IPPO** (Yu et al. 2022): centralized value function'lı PPO. 2026'da kooperatif MARL için hâkim.
- **QMIX** (Rashid et al. 2018): value decomposition — monotonik karıştırmalı `Q_tot(s, a) = f(Q_1(s, a_1), …, Q_n(s, a_n))`.

**3. Self-play.** Aynı agent'ın iki kopyası birbiriyle oynar. Rakibin policy'si geçmiş bir snapshot'tan benim policy'mdir. AlphaGo / AlphaZero / MuZero. OpenAI Five. Sıfır-toplamlı oyunlar için en iyi çalışır; eğitim sinyali simetriktir.

**4. League play.** Self-play'in genel-toplamlı / rekabetçi environment'lara genişlemesi: geçmiş ve şu anki policy'lerin bir popülasyonunu tut, league'den bir rakip örnekle, ona karşı eğit. Exploiter'ları (şu anki en iyiyi yenmekte uzmanlaşır) ve main exploiter'ları (exploiter'ları yenmekte uzmanlaşır) ekler. AlphaStar (StarCraft II). Oyun "taş-kâğıt-makas" strateji döngülerini kabul ettiğinde gerekli.

**İletişim.** Agent'ların birbirine öğrenilmiş mesajlar `m_i` gönderebilmesine izin ver. Kooperatif ayarlarda çalışır. Foerster et al. (2016) türevlenebilir agent-arası iletişimin uçtan-uca eğitilebileceğini gösterdi. Bugünün LLM-tabanlı multi-agent sistemleri (Faz 16) esasen doğal dilde iletişim kurar.

## İnşa Et

Bu ders iki kooperatif agent ile 6×6 bir GridWorld kullanıyor. Karşıt köşelerde başlarlar ve paylaşılan bir hedefe ulaşmaları gerekir. Paylaşılan ödül: ikisinden biri hâlâ hareket ederken adım başına `-1`, ikisi de vardığında `+10`. `code/main.py`'a bak.

### Adım 1: multi-agent env

```python
class CoopGridWorld:
    def __init__(self):
        self.size = 6
        self.goal = (5, 5)

    def reset(self):
        return ((0, 0), (5, 0))  # iki agent

    def step(self, state, actions):
        a1, a2 = state
        new1 = move(a1, actions[0])
        new2 = move(a2, actions[1])
        done = (new1 == self.goal) and (new2 == self.goal)
        reward = 10.0 if done else -1.0
        return (new1, new2), reward, done
```

*Joint* aksiyon uzayı `|A|² = 16`. Küresel state iki pozisyondur.

### Adım 2: bağımsız Q-learning

Her agent joint state üzerinde anahtarlanmış kendi Q-tablosunu koşturur. Her adımda: ikisi de ε-greedy aksiyon seçer, joint geçişi toplar, her biri paylaşılan ödülle kendi Q'sunu günceller.

```python
def independent_q(env, episodes, alpha, gamma, epsilon):
    Q1, Q2 = defaultdict(default_q), defaultdict(default_q)
    for _ in range(episodes):
        s = env.reset()
        while not done:
            a1 = epsilon_greedy(Q1, s, epsilon)
            a2 = epsilon_greedy(Q2, s, epsilon)
            s_next, r, done = env.step(s, (a1, a2))
            target1 = r + gamma * max(Q1[s_next].values())
            target2 = r + gamma * max(Q2[s_next].values())
            Q1[s][a1] += alpha * (target1 - Q1[s][a1])
            Q2[s][a2] += alpha * (target2 - Q2[s][a2])
            s = s_next
```

Ödüller yoğun ve hizalı olduğu için bu görevde çalışır. Sıkı-bağlı görevlerde başarısız olur (örn. bir agent'ın diğerini *beklemesi* gereken yerde).

### Adım 3: ayrıştırılmış-value güncellemeli centralized Q

Joint aksiyonlar üzerinde tek bir Q kullan `Q(s, a_1, a_2)`. Paylaşılan ödülden güncelle. Marginalize ederek execution'da decentralize et: `π_i(s) = argmax_{a_i} max_{a_{-i}} Q(s, a_1, a_2)`. Üstel joint aksiyon uzayını *doğru* küresel görüş için takas eder.

### Adım 4: basit self-play (rekabetçi 2-agent)

Aynı agent, iki rol. A agent'ını B agent'ına karşı eğit; `K` episode'dan sonra, A'nın ağırlıklarını B'ye kopyala. Simetrik eğitim, tutarlı ilerleme. AlphaZero reçetesi miniatürde.

## Tuzaklar

- **Non-stationary replay.** Bağımsız agent'larla experience replay tek-agent'tan daha kötüdür çünkü eski geçişler artık-eski rakipler tarafından üretildi. Düzeltme: yeniden etiketle ya da yenilikle ağırlıklandır.
- **Credit assignment belirsizliği.** Uzun bir episode'dan sonra paylaşılan ödül; hangi agent katkıda bulundu net değil. Düzeltme: counterfactual baseline'lar (COMA) ya da agent başına reward shaping.
- **Policy kayması / kovalama.** Her agent'ın en iyi cevabı diğerinin güncellemesiyle değişir. Düzeltme: centralized critic, yavaş learning rate'ler ya da freeze-one-at-a-time.
- **Koordinasyon üzerinden reward hacking.** Agent'lar tasarımcının öngörmediği koordineli sömürüler bulur. Açık artırma agent'ları sıfır teklife yakınsar. Düzeltme: dikkatli ödül tasarımı, davranışsal kısıtlamalar.
- **Exploration fazlalığı.** İki agent aynı state-aksiyon çiftlerini explore eder. Düzeltme: agent başına entropy bonus'ları ya da rol koşullaması.
- **League döngüleri.** Saf self-play bir hâkimiyet döngüsünde takılabilir. Düzeltme: çeşitli rakiplerle league play.
- **Örnek patlaması.** `n` agent × state uzayı × joint aksiyonlar. Function approximation ile yaklaşıkla; factored aksiyon uzayları (agent başına bir policy çıktı başlığı).

## Kullan

2026 MARL uygulama haritası:

| Alan | Yöntem | Notlar |
|------|--------|--------|
| Kooperatif navigasyon / manipülasyon | MAPPO / QMIX | CTDE; paylaşılan critic + decentralized actor'lar. |
| İki oyunculu oyunlar (satranç, Go, poker) | MCTS ile self-play (AlphaZero) | Sıfır-toplam; simetrik eğitim. |
| Kompleks multiplayer (Dota, StarCraft) | Imitation pretraining'li league play | OpenAI Five, AlphaStar. |
| Otonom araç filoları | Attention'lı CTDE MAPPO / PPO | Kısmi gözlem; değişken takım boyutları. |
| Açık artırma pazarları | Oyun-teorik denge + RL | `n` → ∞ olduğunda mean-field RL. |
| LLM multi-agent sistemleri (Faz 16) | Doğal-dil iletişim + rol koşullaması | Agent-planlama katmanında RL döngüsü. |

2026'da MARL'ın en büyük büyüme alanı LLM tabanlı: pazarlık eden, tartışan, yazılım inşa eden dil-modeli agent sürüleri. RL token seviyesinde değil *trajectory seviyesindeki* çıktılar üzerinde preference optimizasyonu olarak ortaya çıkar (Faz 16 · 03).

## Yayınla

`outputs/skill-marl-architect.md` olarak kaydet:

```markdown
---
name: marl-architect
description: Pick the right multi-agent RL regime (IPPO, CTDE, self-play, league) for a given task.
version: 1.0.0
phase: 9
lesson: 10
tags: [rl, multi-agent, marl, self-play]
---

Given a task with `n` agents, output:

1. Regime classification. Cooperative / adversarial / general-sum. Justify.
2. Algorithm. IPPO / MAPPO / QMIX / self-play / league. Reason tied to coupling tightness and reward structure.
3. Information access. Centralized training (what global info goes to the critic)? Decentralized execution?
4. Credit assignment. Counterfactual baseline, value decomposition, or reward shaping.
5. Exploration plan. Per-agent entropy, population-based training, or league.

Refuse independent Q-learning on tightly-coupled cooperative tasks. Refuse to recommend self-play for general-sum with cycle risks. Flag any MARL pipeline without a fixed-opponent eval (cherry-picked self-play numbers are common).
```

## Alıştırmalar

1. **Kolay.** 2-agent kooperatif GridWorld'de bağımsız Q-learning eğit. Ortalama return > 0 olana kadar kaç episode? Joint öğrenme eğrisini çiz.
2. **Orta.** Bir "koordinasyon" görevi ekle: hedef yalnızca her iki agent aynı turda üzerine adım attığında ulaşılır. Bağımsız Q hâlâ yakınsıyor mu? Ne bozuluyor?
3. **Zor.** MAPPO-stili eğitim için centralized bir critic uygula ve koordinasyon görevinde bağımsız PPO ile yakınsama hızını karşılaştır.

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| Markov game | "Multi-agent MDP" | `(S, A_1, …, A_n, P, R_1, …, R_n)`; her agent'ın kendi ödülü vardır. |
| CTDE | "Centralized training, decentralized execution" | Eğitim zamanında joint critic; her agent'ın policy'si yalnızca yerel gözlemi kullanır. |
| IPPO | "Bağımsız PPO" | Her agent PPO'yu ayrı koşturur. Basit baseline; çoğu zaman hafife alınır. |
| MAPPO | "Multi-agent PPO" | Küresel state üzerinde koşullanmış centralized value function'lı PPO. |
| QMIX | "Monotonik value decomposition" | `Q_tot = f_monotone(Q_1, …, Q_n)` decentralized argmax'a izin verir. |
| COMA | "Counterfactual multi-agent" | Advantage = benim Q'mum eksi benim aksiyonum üzerinde marjinalize edilen beklenen Q. |
| Self-play | "Agent vs geçmiş kendisi" | Tek agent, iki rol; sıfır-toplamlı oyunlar için standart. |
| League play | "Popülasyon eğitimi" | Geçmiş policy'leri önbelleğe al, havuzdan rakipler örnekle; strateji döngülerini halleder. |

## İleri Okuma

- [Lowe et al. (2017). Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments (MADDPG)](https://arxiv.org/abs/1706.02275) — centralized critic'li CTDE.
- [Foerster et al. (2017). Counterfactual Multi-Agent Policy Gradients (COMA)](https://arxiv.org/abs/1705.08926) — credit assignment için counterfactual baseline'lar.
- [Rashid et al. (2018). QMIX: Monotonic Value Function Factorisation](https://arxiv.org/abs/1803.11485) — monotoniklikle value decomposition.
- [Yu et al. (2022). The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games (MAPPO)](https://arxiv.org/abs/2103.01955) — PPO MARL için şaşırtıcı şekilde güçlüdür.
- [Vinyals et al. (2019). Grandmaster level in StarCraft II using multi-agent reinforcement learning (AlphaStar)](https://www.nature.com/articles/s41586-019-1724-z) — ölçekte league play.
- [Silver et al. (2017). Mastering the game of Go without human knowledge (AlphaGo Zero)](https://www.nature.com/articles/nature24270) — sıfır-toplamlı oyunlarda saf self-play.
- [Sutton & Barto (2018). Ch. 15 — Neuroscience & Ch. 17 — Frontiers](http://incompleteideas.net/book/RLbook2020.pdf) — ders kitabının multi-agent ayarlarına ve CTDE'nin çözmek için tasarlandığı non-stationarity problemine kısa ele alışını içerir.
- [Zhang, Yang & Başar (2021). Multi-Agent Reinforcement Learning: A Selective Overview](https://arxiv.org/abs/1911.10635) — yakınsama sonuçlarıyla kooperatif, rekabetçi ve karışık MARL'ı kapsayan survey.
