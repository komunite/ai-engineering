# Reward Modeling ve RLHF

> İnsanlar "iyi asistan cevabı" için bir ödül fonksiyonu yazamaz, ama iki cevabı karşılaştırıp daha iyi olanı seçebilir. Bu karşılaştırmalara bir reward model fit et, sonra dil modelini ona karşı RL et. Christiano 2017. InstructGPT 2022. GPT-3'ü ChatGPT'ye dönüştüren reçete. 2026'da çoğunlukla DPO ile değiştiriliyor — ama zihinsel model kalıyor.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 05 (Sentiment), Faz 9 · 08 (PPO)
**Süre:** ~45 dakika

## Sorun

Next-token-prediction hedefiyle bir dil modeli eğittin. Gramatik İngilizce yazıyor. Aynı zamanda yalan söylüyor, anlamsız konuşuyor ve reddetmesi gerektiği yerde reddetmiyor. Bunu daha fazla pretraining ile düzeltemezsin — web metni problem, çare değil.

"X instruction'ı için cevap A, cevap B'den daha iyi" diyen *skaler bir ödül* istiyorsun. Bu ödül fonksiyonunu elle yazmak imkânsız. "Yardımseverlik" token'lar üzerinde kapalı-formul bir ifade değildir. Ama insanlar iki çıktıyı karşılaştırıp bir tercih işaretleyebilir. Bu ölçekte ucuz toplanır.

RLHF (Christiano et al. 2017; Ouyang et al. 2022) tercihleri bir reward model'e dönüştürür, sonra LM'i bu ödüle karşı PPO ile optimize eder. Üç adımda: SFT → RM → PPO. ChatGPT, Claude, Gemini ve 2023-2025'teki diğer her hizalanmış-LLM'i gönderen reçete.

2026'da PPO adımı çoğunlukla DPO (Faz 10 · 08) ile değiştirildi çünkü hizalama ayarlaması için daha ucuz ve neredeyse aynı kadar iyi. Ama *reward model* parçası hâlâ her Best-of-N sampler'ın, her RL-from-verifiable-rewards pipeline'ının ve process reward model kullanan her reasoning modelinin temelinde yatıyor. RLHF'i anlarsan tüm hizalama stack'ini anlarsın.

## Kavram

![Üç-aşamalı RLHF: SFT, ikili tercihler üzerinde RM, KL cezalı PPO](../assets/rlhf.svg)

**Aşama 1: Supervised Fine-Tuning (SFT).** Pretrained bir base modelden başla. Hedef davranışın insan tarafından yazılmış gösterimleri (instruction-following cevaplar, yardımcı yanıtlar, vb.) üzerinde fine-tune et. Sonuç: *iyi davranışa eğimli* ama hâlâ sınırsız aksiyon uzayı olan bir `π_SFT` modeli.

**Aşama 2: Reward Model eğitimi.**

- `x` prompt'larına `(y_+, y_-)` cevap çiftleri topla, insanlar tarafından "y_+, y_-'a tercih ediliyor" olarak etiketli.
- `y_+`'a daha yüksek skorlar atayacak bir reward model `R_φ(x, y)` eğit.
- Loss: **Bradley-Terry ikili logistic**:

  `L(φ) = -E[ log σ(R_φ(x, y_+) - R_φ(x, y_-)) ]`

  σ sigmoid'dir. Ödül farkı bir tercih log-odds'ını ima eder. BT 1952'den beri (Bradley-Terry) standart olmuştur ve modern RLHF'te hâkim seçimdir.

- `R_φ` genelde SFT modelinden üzerine bir skaler başlıkla başlatılır. Aynı transformer omurgası; tek bir lineer katman ödülü üretir.

**Aşama 3: KL cezalı RM'e karşı PPO.**

- Eğitilebilir policy `π_θ`'yı `π_SFT`'ten başlat. Dondurulmuş bir *referans* `π_ref = π_SFT` tut.
- `y` cevabının sonundaki ödül:

  `r_total(x, y) = R_φ(x, y) - β · KL(π_θ(·|x) || π_ref(·|x))`

  KL cezası `π_θ`'nın `π_SFT`'ten keyfi olarak kaymasını önler — *regularizer*'dır, sert bir trust region değil. `β` tipik olarak `0.01`-`0.05`.
- Bu ödül ile PPO (Ders 08) koştur. Advantage'lar token seviyesindeki trajectory üzerinde hesaplanır, ama RM yalnızca tam cevabı skorlar.

**KL neden?** O olmadan, PPO mutlu bir şekilde reward-hacking stratejileri bulur — RM yalnızca dağıtım-içi tamamlamalar üzerinde eğitildi. Dağıtım-dışı bir cevap, herhangi bir insan yazımı cevaptan daha yüksek skor alabilir. KL `π_θ`'yı RM'in eğitildiği manifold'a yakın tutar. RLHF'teki en önemli tek kadrandır.

**2026 durumu:**

- **DPO** (Rafailov 2023): kapalı-formuldaki cebir, Aşama 2+3'ü tercih verisi üzerinde tek bir supervised loss'a indirgenir. RM yok, PPO yok. Hesaplamanın bir kısmı için hizalama benchmark'larında aynı kalite. Faz 10 · 08'de kapsanır.
- **GRPO** (DeepSeek 2024-2025): critic yerine grup-göreceli baseline'lı PPO, insan-eğitimli RM yerine bir *verifier*'dan (kod çalışıyor / matematik cevabı eşleşiyor) ödül. Reasoning modelleri için hâkim. Faz 9 · 12'de kapsanır.
- **Process reward modelleri (PRM'ler):** kısmi çözümleri (her reasoning adımını) skorlar, reasoning için hem RLHF hem GRPO varyantlarında kullanılır.
- **Constitutional AI / RLAIF:** insanlar yerine tercihleri üretmek için hizalanmış bir LLM kullanır. Tercih bütçesini ölçeklendirir.

## İnşa Et

Bu ders, string olarak temsil edilen minik sentetik "prompt"lar ve "cevap"lar kullanıyor. RM, bag-of-tokens temsili üzerinde lineer bir skorlayıcıdır. Gerçek LLM yok — pipeline'ın *şekli* önemli, ölçeği değil. `code/main.py`'a bak.

### Adım 1: sentetik tercih verisi

```python
PROMPTS = ["help me", "answer me", "explain this"]
GOOD_WORDS = {"clear", "specific", "kind", "thorough"}
BAD_WORDS = {"vague", "rude", "wrong", "short"}

def make_pair(rng):
    x = rng.choice(PROMPTS)
    y_good = rng.choice(list(GOOD_WORDS)) + " " + rng.choice(list(GOOD_WORDS))
    y_bad = rng.choice(list(BAD_WORDS)) + " " + rng.choice(list(BAD_WORDS))
    return (x, y_good, y_bad)
```

Gerçek RLHF'te bu, insan etiketçilerle değiştirilir. Şekil — `(prompt, preferred_response, rejected_response)` — birebir aynıdır.

### Adım 2: Bradley-Terry reward model

Lineer skor: `R(x, y) = w · bag(y)`. BT ikili log-loss'u minimize edecek şekilde eğit:

```python
def rm_train_step(w, x, y_pos, y_neg, lr):
    r_pos = dot(w, bag(y_pos))
    r_neg = dot(w, bag(y_neg))
    p = sigmoid(r_pos - r_neg)
    for tok, cnt in bag(y_pos).items():
        w[tok] += lr * (1 - p) * cnt
    for tok, cnt in bag(y_neg).items():
        w[tok] -= lr * (1 - p) * cnt
```

Birkaç yüz güncellemeden sonra, `w`, iyi-kelime token'larına pozitif ve kötülere negatif ağırlıklar atar.

### Adım 3: RM üzerinde PPO-benzeri policy

Oyuncak policy'miz bir vocabulary'den tek bir token üretir. Token'ı RM altında skorlarız, `log π_θ(token | prompt)`'u hesaplarız, KL-to-reference cezası ekleriz ve clip'lenmiş PPO surrogate'ini uygularız.

```python
def rlhf_step(theta, ref, w, prompt, rng, eps=0.2, beta=0.1, lr=0.05):
    logits_theta = policy_logits(theta, prompt)
    probs = softmax(logits_theta)
    token = sample(probs, rng)
    logits_ref = policy_logits(ref, prompt)
    probs_ref = softmax(logits_ref)
    reward = dot(w, bag([token])) - beta * kl(probs, probs_ref)
    # theta üzerinde ppo-stili güncelleme, ödülü return olarak ele al
    ...
```

### Adım 4: KL'yi izle

Her güncellemede ortalama `KL(π_θ || π_ref)`'i takip et. `~5-10`'a doğru yürürse policy `π_SFT`'ten uzağa kaymış — ya `β` çok düşük ya da reward hacking başlıyor. Bu gerçek RLHF'te en üst diagnostic'tir.

### Adım 5: TRL ile production reçetesi

Oyuncak pipeline'ı anladıktan sonra, gerçek bir kütüphane kullanıcısının yazdığı şekliyle aynı döngü. Hugging Face'in [TRL](https://huggingface.co/docs/trl)'i referans implementasyondur — Aşama 2 için `RewardTrainer` ve Aşama 3 için (yerleşik KL-to-reference'lı) `PPOTrainer`.

```python
# Aşama 2: ikili tercihlerden reward model
from trl import RewardTrainer, RewardConfig
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
rm = AutoModelForSequenceClassification.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct", num_labels=1
)

# dataset satırları: {"prompt", "chosen", "rejected"} — Bradley-Terry formatı
trainer = RewardTrainer(
    model=rm,
    tokenizer=tok,
    train_dataset=preference_data,
    args=RewardConfig(output_dir="./rm", num_train_epochs=1, learning_rate=1e-5),
)
trainer.train()
```

```python
# Aşama 3: SFT referansına KL cezalı RM'e karşı PPO
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

policy = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-checkpoint")
ref    = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-checkpoint")  # dondurulmuş

ppo = PPOTrainer(
    config=PPOConfig(learning_rate=1.41e-5, batch_size=64, init_kl_coef=0.05,
                     target_kl=6.0, adap_kl_ctrl=True),
    model=policy, ref_model=ref, tokenizer=tok,
)

for batch in dataloader:
    responses = ppo.generate(batch["query_ids"], max_new_tokens=128)
    rewards   = rm(torch.cat([batch["query_ids"], responses], dim=-1)).logits[:, 0]
    stats     = ppo.step(batch["query_ids"], responses, rewards)
    # stats şunları içerir: mean_kl, clip_frac, value_loss — üç PPO diagnostic'i
```

Kütüphanenin senin için yaptığı üç şey. `adap_kl_ctrl=True` uyarlanır-β schedule'unu uygular: gözlenen KL `target_kl`'yi aşarsa β iki katına çıkar; yarısının altındaysa β yarıya iner. Referans model konvansiyon gereği dondurulmuştur — `policy` ile yanlışlıkla parametreleri paylaşmaman gerekir. Value head policy ile aynı omurga üzerinde yaşar (`AutoModelForCausalLMWithValueHead` skaler bir MLP başlığı ekler), TRL'nin `policy/kl` ve `value/loss`'u ayrı raporlamasının sebebi budur.

## Tuzaklar

- **Aşırı-optimizasyon / reward hacking.** RM mükemmel değil; `π_θ` yüksek skor alan ama kötü olan rakip tamamlamalar bulur. Belirtiler: ödül sonsuza dek tırmanırken insan eval skoru plato yapar veya düşer. Düzeltme: erken dur, `β`'yı yükselt, RM eğitim verisini genişlet.
- **Length hacking.** Yardımcı cevaplar üzerinde eğitilmiş RM'ler genelde örtük olarak uzunluğu ödüllendirir. Policy cevapları doldurmayı öğrenir. Çözüm: uzunluk-normalize edilmiş ödül ya da uzunluk-bilinçli RM ile RLAIF.
- **Çok küçük RM.** RM en az policy kadar büyük olmalı. Minik bir RM policy'nin çıktılarını sadakatle skorlayamaz.
- **KL tuning.** Çok düşük β → kayma ve reward hacking. Çok yüksek β → policy zar zor değişir. Standart trick, adım başına sabit KL'yi hedefleyen *uyarlanır* bir β'dır.
- **Tercih-veri gürültüsü.** İnsan etiketlerinin ~%30'u gürültülü ya da belirsizdir. Uyum-filtrelenmiş veri üzerinde RM eğit ya da BT üzerinde bir sıcaklık kullanarak kalibre et.
- **Off-policy problemleri.** PPO verisi ilk epoch'tan sonra hafifçe off-policy'dir. Ders 08'deki gibi clip oranını izle.

## Kullan

2026'da RLHF katmanlıdır:

| Katman | Hedef | Yöntem |
|--------|-------|--------|
| Instruction-following, yardımseverlik, zararsızlık | Hizalama | DPO (Faz 10 · 08) RLHF-PPO'ya tercih edilir. |
| Reasoning doğruluğu (matematik, kod) | Yetenek | Verifier ödüllü GRPO (Faz 9 · 12). |
| Uzun-ufuklu çok-adımlı görevler | Agentic | Adımlar üzerinde process reward modelleriyle PPO / GRPO. |
| Güvenlik / reddetme davranışı | Güvenlik | Ayrı bir güvenlik RM'i ile RLHF-PPO ya da Constitutional AI. |
| Inference'ta Best-of-N | Hızlı hizalama | Decode zamanında RM'i kullan; policy eğitimi gerekmez. |
| Reward distillation | Inference compute'u | Dondurulmuş bir LM üzerinde küçük bir "reward head" eğit. |

RLHF 2022-2024'te *yöntemdi*. 2026'da production hizalama pipeline'ları DPO-öncelikli, RM-yoğun veya güvenlik-kritik adımlar için PPO-yalnız.

## Yayınla

`outputs/skill-rlhf-architect.md` olarak kaydet:

```markdown
---
name: rlhf-architect
description: Design an RLHF / DPO / GRPO alignment pipeline for a language model, including RM, KL, and data strategy.
version: 1.0.0
phase: 9
lesson: 9
tags: [rl, rlhf, alignment, llm]
---

Given a base LM, a target behavior (alignment / reasoning / refusal / agent), and a preference or verifier budget, output:

1. Stage. SFT? RM? DPO? GRPO? With justification.
2. Preference or verifier source. Humans, AI feedback, rule-based, unit-test-pass, or reward distillation.
3. KL strategy. Fixed β, adaptive β, or DPO (implicit KL).
4. Diagnostics. Mean KL, reward stability, over-optimization guard (holdout human eval).
5. Safety gate. Red-team set, refusal rate, safety RM separate from helpfulness RM.

Refuse to ship RLHF-PPO without a KL monitor. Refuse to use an RM smaller than the target policy. Refuse length-only rewards. Flag any pipeline that does not hold back a blind human-eval set as lacking over-optimization protection.
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki Bradley-Terry reward model'i 500 sentetik tercih çifti üzerinde eğit. Held-out 100 çift üzerinde ikili doğruluğu ölç. %90'ı geçmeli.
2. **Orta.** `β ∈ {0.0, 0.1, 1.0}` ile oyuncak PPO-RLHF döngüsünü koştur. Her biri için güncellemeler üzerinde RM skoru vs KL-to-reference çiz. Hangileri reward-hack ediyor?
3. **Zor.** DPO'yu (kapalı-formul preference-likelihood loss'u) aynı tercih verisi üzerinde uygula ve RLHF-PPO pipeline'ı ile harcanan compute ve ulaşılan son RM skoru bakımından karşılaştır.

## Anahtar Terimler

| Terim | İnsanların dediği | Aslında ne demek |
|-------|--------------------|--------------------|
| RLHF | "Hizalama RL'si" | Üç aşamalı SFT + RM + PPO pipeline'ı (Christiano 2017, Ouyang 2022). |
| Reward Model (RM) | "Skorlama ağı" | Bradley-Terry üzerinden ikili tercihlere fit edilmiş öğrenilmiş skaler fonksiyon. |
| Bradley-Terry | "İkili logistic loss" | `P(y_+ ≻ y_-) = σ(R(y_+) - R(y_-))`; standart RM hedefi. |
| KL cezası | "Referansa yakın kal" | Ödülde `β · KL(π_θ || π_ref)`; anti-reward-hacking regularizer. |
| Reward hacking | "Goodhart yasası" | Policy RM kusurlarını sömürür; belirtiler: ödül yukarı, insan eval düz. |
| RLAIF | "AI-etiketli tercihler" | Etiketlerin insanlar yerine başka bir LM'den geldiği RLHF. |
| PRM | "Process Reward Model" | Kısmi reasoning adımlarını skorlar; reasoning pipeline'larında kullanılır. |
| Constitutional AI | "Anthropic'in yöntemi" | Açık kurallarla yönlendirilen AI-üretimi tercihler. |

## İleri Okuma

- [Christiano et al. (2017). Deep Reinforcement Learning from Human Preferences](https://arxiv.org/abs/1706.03741) — RLHF'i başlatan makale.
- [Ouyang et al. (2022). InstructGPT — Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — ChatGPT'nin arkasındaki reçete.
- [Stiennon et al. (2020). Learning to summarize with human feedback](https://arxiv.org/abs/2009.01325) — özetleme için daha erken RLHF.
- [Rafailov et al. (2023). Direct Preference Optimization](https://arxiv.org/abs/2305.18290) — DPO; 2026'da RLHF-sonrası varsayılan.
- [Bai et al. (2022). Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073) — RLAIF ve self-critique döngüsü.
- [Anthropic RLHF makalesi (Bai et al. 2022). Training a Helpful and Harmless Assistant](https://arxiv.org/abs/2204.05862) — HH makalesi.
- [Hugging Face TRL kütüphanesi](https://huggingface.co/docs/trl) — production `RewardTrainer` ve `PPOTrainer`. Uyarlanır-KL ve value-head ayrıntıları için trainer kaynağını oku.
- [Hugging Face — Illustrating Reinforcement Learning from Human Feedback](https://huggingface.co/blog/rlhf) by Lambert, Castricato, von Werra, Havrilla — diyagramlarla üç aşamalı pipeline'ın kanonik gezintisi.
- [von Werra et al. (2020). TRL: Transformer Reinforcement Learning](https://github.com/huggingface/trl) — kütüphane; `examples/` Llama, Mistral ve Qwen için uçtan-uca RLHF script'leri içerir.
- [Sutton & Barto (2018). Ch. 17.4 — Designing Reward Signals](http://incompleteideas.net/book/RLbook2020.pdf) — ödül-hipotezi görüşü; reward hacking hakkında düşünmek için temel ön koşul.
