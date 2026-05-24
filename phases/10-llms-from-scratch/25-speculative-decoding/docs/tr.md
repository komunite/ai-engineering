# Speculative Decoding ve EAGLE

> Bir frontier LLM'in bir token üretmesi milyarlarca parametre üzerinde tam bir forward pass gerektirir. Bu forward pass aşırı kaynak ayrılmıştır: çoğu zaman çok daha küçük bir model sonraki 3-5 token'ı doğru tahmin edebilir ve büyük model sadece tahmini *doğrulamak* zorundadır. Tahmin doğru olduğunda bir tokenin fiyatına 5 token aldın. Speculative decoding (Leviathan et al. 2023) bunu kesin yaptı ve EAGLE-3 (2025) acceptance rate'lerini doğrulama başına ~4.5 token'a itti — eşleşen output dağılımında 4-5x hızlanma.

**Tür:** Yapım
**Diller:** Python (numpy ile)
**Ön koşullar:** Faz 10 Ders 12 (Inference Optimization), Faz 10 Ders 04 (Mini-GPT Pretraining)
**Süre:** ~75 dakika

## Sorun

H100'de 70B-sınıfı model için decode throughput'u tipik olarak saniyede 40-80 token. Her token tüm model ağırlıklarını HBM'den okuyan tam bir forward pass gerektirir. Output'unu değiştirmeden modeli daha küçük yapamazsın. Memory ötesinde batch size'ı artıramazsın. Sıkıştın — modelin forward pass başına birden fazla token üretmesine izin veremezsen.

Autoregressive generation doğal olarak sıralı görünür: `x_{t+1} = sample(p(· | x_{1:t}))`. Ama bir concurrency fırsatı var. "Sonraki 4 token muhtemelen [a, b, c, d]" diyen ucuz bir tahminci olsaydı **büyük modelin tek bir forward pass'ında** 5 pozisyonu doğrulayabilir ve en uzun eşleşen prefix'i kabul edebilirdin.

Leviathan, Kalai, Matias (2023, "Fast Inference from Transformers via Speculative Decoding") bunu target modelin sampling dağılımını koruyan akıllı bir accept/reject kuralı yoluyla kesin yaptı. Aynı output dağılımı, 2-4× daha hızlı.

## Kavram

### İki-Model Kurulumu

- **Target model** `M_p`: gerçekten sample istediğin büyük, yavaş, yüksek-kaliteli model. Dağılım: `p(x)`.
- **Draft model** `M_q`: küçük, hızlı, daha düşük-kaliteli model. Dağılım: `q(x)`. 5-30× daha küçük.

Adım başına:

1. Draft model `K` token'ı autoregressive önerir: `x_1, x_2, ..., x_K ~ q`.
2. Target model `K+1` pozisyonun hepsi üzerinde TEK bir forward pass çalıştırır, paralel olarak, her önerilen token için `p(x_k)` üretir.
3. Aşağıdaki değiştirilmiş rejection-sampling kuralı yoluyla her token'ı soldan-sağa accept/reject. En uzun eşleşen prefix'i kabul et.
4. Herhangi bir token reject edilirse, düzeltilmiş dağılımdan değiştirme sample et ve dur. Aksi takdirde `p(· | x_1...x_K)`'dan bir bonus token sample et.

Draft target ile mükemmel eşleşirse, target-forward başına K+1 token alırsın. Draft pozisyon 1'de yanlışsa, sadece 1 token alırsın.

### Kesinlik Kuralı

Speculative decoding **dağılımda p'den sample etmeye kanıtlanabilir şekilde eşdeğer**. Rejection kuralı:

```
Her drafted token x_t için:
    r ~ Uniform(0, 1)
    if r < p(x_t) / q(x_t):
        x_t'i kabul et
    else:
        residual'dan değiştirme sample et: (p - q)+ / ||(p - q)+||_1
        dur
```

`(p - q)+` pointwise farkın pozitif kısmını gösterir. Draft ve target anlaştığında (`p ≈ q`) acceptance neredeyse 1. Anlaşmadıklarında, residual dağılım toplam sample'ın hala tam olarak `p` olacak şekilde inşa edilir.

**Greedy durum.** Temperature=0 sampling için sadece `argmax(p) == x_t` kontrol et. Evetse, kabul et; hayırsa, `argmax(p)` output et ve dur.

### Beklenen Hızlanma

Draft modelin token-seviyesi acceptance rate'i `α` ise, target-forward pass başına üretilen beklenen token:

```
E[tokens] = (1 - α^{K+1}) / (1 - α)        # K = draft uzunluğu, α [0, 1]'de
```

`α = 0.8, K = 4`'te: `(1 - 0.8^5)/(1 - 0.8) = 3.36` forward başına token. Tek bir target forward kabaca `cost_q * K + cost_p` (K draft adımı artı bir target doğrulama) maliyetlidir. `cost_p >> cost_q * K` ise hızlanma oranı throughput üzerinde `3.36× / 1 = 3.36×`'dir.

Tek gerçek parametre `α`'dır, tamamen draft-target uyumuna bağlıdır. İyi bir draft her şeydir.

### Draft Eğitimi: Distillation

Rastgele küçük bir model kötü bir draft yapar. Standart reçete target'tan distill etmektir:

1. Küçük bir mimari seç (70B target için ~1B, 7B target için ~500M).
2. Target modeli büyük bir metin corpus'unda çalıştır; sonraki-token dağılımlarını sakla.
3. Draft'ı target'ın dağılımına karşı (ground-truth token'lara karşı değil) KL divergence ile eğit.

Sonuç: `α` tipik olarak kodlamada 0.6-0.8, doğal-dil chat'te 0.7-0.85. Production'da 2-3× hızlanma.

### EAGLE: Tree Drafting + Feature Reuse

Li, Wei, Zhang, Zhang (2024, "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty") standart speculative decoding'de iki verimsizlik gözlemledi:

1. Draft her biri full-stack K seri adım yapar. Ama draft target'ın en son doğrulamadan feature'larını (hidden state'leri) yeniden kullanabilirdi — target zaten draft'ın sıfırdan yeniden türetmekte olduğu zengin temsiller hesapladı.
2. Draft lineer bir zincir output verir. Draft adayların bir *tree*'ini output verseydi (her node birden fazla tahmin), target'ın tek forward pass'ı tree attention mask yoluyla birden fazla aday yolu paralel doğrulayabilir ve en uzun kabul edilen dalı seçebilirdi.

EAGLE-1 değişiklikleri:
- Draft input = pozisyon t'de target'ın final hidden state'i, ham token'lar değil.
- Draft mimarisi = 1 transformer decoder katmanı (ayrı küçük model değil).
- Output = derinlik başına K = 4-8 adaylı tree, derinlik 4-6.

EAGLE-2 (2024) dinamik tree topolojisi ekler: tree draft belirsiz olduğu yerde daha geniş büyür ve emin olduğu yerde dar kalır. Doğrulama maliyetini artırmadan `α_effective`'i yükseltir.

EAGLE-3 (Li et al. 2025, "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test") sabit top-katman feature bağımlılığını kaldırır ve draft'ı yeni bir "test-time simulation" loss ile eğitir — draft teacher-forced eğitim dağılımı yerine target'ın test-time dağılımıyla eşleşen output'lar üzerinde eğitilir. Acceptance rate 0.75'ten (EAGLE-2) 0.82'ye (EAGLE-3) yükselir ve doğrulama başına ortalama token 3.0'dan 4.5'e.

### Tree Attention Doğrulama

Draft bir tree output verdiğinde, target model tek bir forward pass kullanarak bir **tree attention mask** ile onu doğrular — saf bir çizgi yerine tree topolojisini encode eden causal bir mask. Her token sadece tree'deki atalarına attention yapar. Doğrulama pass'ı hala bir forward, bir matmul; topolojik mask sadece birkaç ekstra KV girişi maliyetlidir.

```
        root
       /    \
      a      b
     / \    / \
    c  d   e   f
```

`a, b` rakip ilk-token adayları ve `c, d, e, f` ikinci-token adaylarıysa, altı pozisyonun hepsi tek bir forward pass'ta doğrulanır. Output kabul edilen herhangi bir yol boyunca en uzun prefix'tir.

### Ne Zaman Kazanır, Ne Zaman Kazanmaz

**Kazanır:**
- Tahmin edilebilir metinli chat / completion (kod, yaygın İngilizce, structured output). `α` yüksek.
- Decode sırasında kullanılmayan GPU compute'lu ayarlar (memory-bound faz). Tree drafting mevcut FLOP'ları kullanır.

**Kaybeder / kazanım yok:**
- Yüksek stokastik output'lar (yüksek temperature'de yaratıcı yazım). `α` `1/|vocab|`'a doğru çöker.
- Çok yüksek concurrency ile batch serving — batching zaten FLOP'ları doldurur, tree doğrulama için az yer.
- Draft'ın çok daha küçük olmadığı çok küçük target modeller.

Production atölyeleri tipik olarak chat'te 2-3× wall-clock hızlanma, kod üretiminde 3-5× ve yaratıcı yazımda sıfıra yakın raporlar.

## İnşa Et

`code/main.py`:

- Kesin rejection kuralını implement eden ve target'ın dağılımını koruduğunu doğrulayan referans bir `speculative_decode(target, draft, prompt, K, temperature)` (empirik KL < 0.01 vs plain target sampling).
- Top-p branching ile derinlik-K tree inşa eden EAGLE-tarzı bir tree drafter.
- Bir verifier için doğru causal deseni üreten tree attention mask builder.
- Minik bir LM üzerinde ikisini de çalıştıran bir acceptance-rate harness'ı (GPT-2-medium target'tan bir GPT-2-small distill et).

```python
def speculative_step(p_target, q_draft, K, temperature=1.0):
    """Bir speculative decoding turu. Kabul edilen token'ların listesini döner."""
    # 1. K token draft et
    draft_tokens = []
    q_probs = []
    state = draft_state_init()
    for _ in range(K):
        probs = softmax(q_draft(state) / temperature)
        t = np.random.choice(len(probs), p=probs)
        draft_tokens.append(t)
        q_probs.append(probs[t])
        state = draft_step(state, t)

    # 2. Target her drafted pozisyon + 1 ekstrada p hesaplar
    p_probs_all = target_forward_batched(p_target, draft_tokens, temperature)

    # 3. Soldan-sağa accept/reject
    accepted = []
    for k, tok in enumerate(draft_tokens):
        r = np.random.uniform()
        if r < p_probs_all[k][tok] / q_probs[k]:
            accepted.append(tok)
        else:
            residual = np.maximum(p_probs_all[k] - q_probs[k], 0)
            residual /= residual.sum()
            accepted.append(np.random.choice(len(residual), p=residual))
            return accepted
    # 4. Tüm K kabul edildi → target'tan bonus token sample et
    accepted.append(np.random.choice(len(p_probs_all[-1]), p=p_probs_all[-1]))
    return accepted
```

## Kullan

- **vLLM** ve **SGLang** birinci-sınıf speculative decoding yayınlar. Bayraklar: `--speculative_model`, `--num_speculative_tokens`. EAGLE-2/3 desteği `--spec_decoding_algorithm eagle` bayrağı yoluyla.
- **NVIDIA TensorRT-LLM** Medusa ve EAGLE tree'lerini native destekler.
- **Referans draft modeller**: `Qwen/Qwen3-0.6B-spec` (Qwen3-32B için draft eder), `meta-llama/Llama-3.2-1B-Instruct-spec` (70B için draft eder).
- **Medusa head'leri** (Cai et al. 2024, "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"): draft modeli yerine, target'ın kendisine K paralel prediction head ekle. Deploy etmesi daha basit, EAGLE'dan biraz daha düşük acceptance.

## Yayınla

Bu ders `outputs/skill-speculative-tuning.md` üretir — bir target modelin iş yükünü profil eden ve şunları seçen bir skill: draft model, K (draft uzunluğu), tree genişliği, temperature ve plain decode'a ne zaman geri düşülecek.

## Alıştırmalar

1. Kesin rejection kuralını implement et ve empirik olarak doğrula. `speculative_decode` üzerinden ve plain target sampling üzerinden 10K sample çalıştır; iki output dağılımı arasındaki TV mesafesini hesapla. < 0.01 olmalı.

2. Hızlanma formülünü hesapla. Sabit `α` ve `K` verildiğinde, target-forward başına beklenen token'ları çiz. α ∈ {0.5, 0.7, 0.9} için optimal K'yı bul.

3. Minik bir draft eğit. 124M GPT-2 target al ve KL loss ile 100M token üzerinde 30M GPT-2 draft distill et. Held-out metinde `α`'yı ölç. Beklenen: 0.6-0.7.

4. EAGLE-tarzı tree drafting implement et. Bir zincir yerine, draft'ın her derinlikte top-3 dal output etmesini sağla. Tree attention mask'ını inşa et. Target'ın en uzun doğru dalı kabul ettiğini doğrula.

5. Başarısızlık modlarını ölç. Temperature=1.5'te (yüksek stokastiklik) speculative decode çalıştır. α'nın çöktüğünü ve algoritmanın draft overhead'i nedeniyle plain decode'dan daha yavaş olduğunu göster.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Target model | "Büyük model" | Sample istediğin yavaş, yüksek-kaliteli model (p dağılımı) |
| Draft model | "Speculator" | Küçük, hızlı tahminci (q dağılımı); 5-30x daha küçük |
| K / draft length | "Look-ahead" | Doğrulama pass başına spekülasyon yapılan token sayısı |
| α / acceptance rate | "Hit rate" | Draft'ın önerisinin kabul edilme token başına olasılığı |
| Exact rejection rule | "Accept test" | target'ın dağılımını koruyan r < p/q karşılaştırması |
| Residual distribution | "Düzeltilmiş p-q" | Rejection'da sample edilecek dağılım (p - q)+ / ||(p - q)+||_1 |
| Tree drafting | "Branching spekülasyon" | Draft tek pass'ta tree-yapılı attention mask ile doğrulanan bir aday tree'si output verir |
| Tree attention mask | "Topolojik mask" | Her node'un sadece atalarına attention yapması için tree topolojisini encode eden causal mask |
| Medusa heads | "Paralel head'ler" | Target'ın kendisinde K ekstra prediction head; ayrı draft model yok |
| EAGLE feature reuse | "Hidden-state draft" | Draft input target'ın son hidden state'i, ham token'lar değil, draft'ı küçültür |
| Test-time simulation loss | "EAGLE-3 eğitimi" | Teacher forcing yerine target'ın test-time dağılımıyla eşleşen output'lar üzerinde draft eğit |

## İleri Okuma

- [Leviathan, Kalai, Matias, 2023 -- "Fast Inference from Transformers via Speculative Decoding"](https://arxiv.org/abs/2211.17192) -- kesin rejection kuralı ve teorik hızlanma analizi
- [Chen, Borgeaud, Irving et al., 2023 -- "Accelerating Large Language Model Decoding with Speculative Sampling"](https://arxiv.org/abs/2302.01318) -- DeepMind'da eşzamanlı speculative-sampling makalesi
- [Cai, Li, Geng, Wang, Wang, Zhu, Dao, 2024 -- "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"](https://arxiv.org/abs/2401.10774) -- draft modele paralel-head alternatifi
- [Li, Wei, Zhang, Zhang, 2024 -- "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty"](https://arxiv.org/abs/2401.15077) -- feature reuse ve tree drafting
- [Li et al., 2024 -- "EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees"](https://arxiv.org/abs/2406.16858) -- dinamik tree topolojisi
- [Li et al., 2025 -- "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test"](https://arxiv.org/abs/2503.01840) -- train-time test-time eşleşmesi
- [Fu, Haotian, Peng et al., 2024 -- "Break the Sequential Dependency of LLM Inference Using Lookahead Decoding"](https://arxiv.org/abs/2402.02057) -- Jacobi/lookahead decoding, speculator-free alternatif
