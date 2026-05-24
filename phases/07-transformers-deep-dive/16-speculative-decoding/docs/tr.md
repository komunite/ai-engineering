# Speculative Decoding — Draft, Doğrula, Tekrar Et

> Autoregressive decoding seridir. Her token bir öncekini bekler. Speculative decoding zinciri kırar: ucuz bir model N token draft eder, pahalı model N'in hepsini tek bir forward pass'te doğrular. Draft doğru olduğunda N üretim için bir büyük forward ödedin.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 07 (GPT Causal LM), Faz 7 · 12 (KV Cache & Flash Attention)
**Süre:** ~60 dakika

## Sorun

70B LLM tek bir token sample'lamak H100'de ~30 ms sürer. 3B draft model ~3 ms sürer. 3B'nin 5 token ileri draft etmesine izin verirsek, sonra 70B'yi 5'in hepsini doğrulamak için *bir kere* çalıştırırsak, toplam 5'e kadar kabul edilen token için `5×3 + 30 = 45 ms` — düz-hatlı üretim için `5×30 = 150 ms`'e karşı. Tam speculative-decoding pitch'i budur: 2–4× daha düşük decode latency için az miktarda ekstra GPU belleğini (draft model) takas et.

Numara dağılımı koruyor olmalı. Leviathan et al. (2023) ve eşzamanlı olarak Chen et al. tarafından tanıtılan speculative sampling, çıktı dizisinin büyük modelin kendi başına üretebileceği şeyle **aynı şekilde dağıtıldığını** garanti eder. Kalite ödünleşmesi yok. Sadece daha hızlı.

Dört draft-doğrulayıcı çifti ailesi 2026 çıkarımına hakimdir:

1. **Vanilla speculative (Leviathan 2023).** Ayrı draft model (örn., Llama 3 1B) + doğrulayıcı (örn., Llama 3 70B).
2. **Medusa (Cai 2024).** Doğrulayıcının üzerindeki çoklu decoding head'leri `t+1..t+k` pozisyonlarını paralel tahmin eder. Ayrı draft model yok.
3. **EAGLE ailesi (Li 2024, 2025).** Doğrulayıcının hidden state'lerini yeniden kullanan hafif draft; vanilla'dan daha yakın kabul oranı; tipik 3–4×.
4. **Lookahead decoding (Fu 2024).** Jacobi iterasyonu; draft modele hiç gerek yok. Self-speculation. Niş ama bağımlılıksız.

2026'daki her production çıkarım yığını varsayılan olarak speculative decoding gönderir. vLLM, TensorRT-LLM, SGLang ve llama.cpp en azından vanilla + EAGLE-2 destekler.

## Kavram

### Çekirdek algoritma

Bir doğrulayıcı `M_q` ve daha ucuz bir draft `M_p` verildiğinde:

1. `x_1..x_k`, zaten decode edilmiş prefix olsun.
2. **Draft**: `M_p`'yi kullanarak `d_{k+1}, d_{k+2}, ..., d_{k+N}`'i draft olasılıkları `p_1..p_N` ile autoregressive olarak öner.
3. **Paralel doğrula**: `x_1..x_k, d_{k+1}, ..., d_{k+N}` üzerinde `M_q`'yu bir kere çalıştır, `k+1..k+N+1` pozisyonları için doğrulayıcı olasılıkları `q_1..q_{N+1}`'i al.
4. **Her draft token'ı soldan sağa kabul et/reddet**: her `i` için, `min(1, q_i(d_i) / p_i(d_i))` olasılığıyla kabul et.
5. Pozisyon `j`'deki ilk redde: normalize edilmiş "residual" dağılım `(q_j - p_j)_+`'tan `t_j` sample al. `j`'den sonraki tüm draft'lar atılır.
6. `N`'in hepsini kabul edersek: `q_{N+1}`'den (bedava bonus token) bir ekstra token `t_{N+1}` sample al.

Residual dağılım numarası, çıktının `M_q` sıfırdan sample almışçasına tam aynı dağıtılmasını sağlayan matematiksel iç görüdür.

### Hızlanmayı belirleyen

`α` = draft token başına beklenen kabul oranı olsun. `c` = draft-to-doğrulayıcı maliyet oranı olsun. Adım başına:

- Naif üretim token başına 1 büyük-model çağrısı yapar.
- Speculative, `α` yüksekken `(1 - α^{N+1}) / (1 - α) ≈ 1/(1-α)` token başına 1 büyük-model çağrısı yapar.

`α = 0.75` ve `N = 5`'te tipik parmak hesabı: 3× daha az büyük-model çağrısı. Draft maliyeti 5× ucuz. Toplam duvar-saati ~2.5× düşer.

**α şuna bağlıdır:**

- Draft'ın doğrulayıcıyı ne kadar iyi yaklaşıkladığı. Aynı aile / aynı eğitim verisi α'yı önemli ölçüde arttırır.
- Decoding stratejisi. Greedy doğrulayıcıya karşı greedy draft: yüksek α. Temperature sampling: eşleştirmesi daha zor; kabul düşer.
- Görev tipi. Kod ve yapılandırılmış çıktı daha çok kabul eder (tahmin edilebilir); serbest-biçimli yaratıcı yazı daha az kabul eder.

### Medusa — draft model olmadan draft

Medusa draft modeli doğrulayıcıdaki ekstra çıktı head'leriyle değiştirir. Pozisyon `t`'de:

```
paylaşılan trunk → hidden h_t
    ├── head_0: t+1'deki token'ı tahmin et  (standart LM head)
    ├── head_1: t+2'deki token'ı tahmin et
    ├── head_2: t+3'teki token'ı tahmin et
    ├── head_3: t+4'teki token'ı tahmin et
```

Her head kendi logit'lerini çıkarır. Çıkarımda her head'den sample alarak bir aday dizi elde edersin, sonra tüm aday devamlarını aynı anda göz önüne alan bir tree-attention şeması kullanarak tek bir forward pass'le doğrularsın.

Artı: ikinci model yok. Eksi: eğitilebilir parametre ekler; supervised fine-tuning aşaması gerekir (~1B token); kabul oranı iyi bir draft'la vanilla speculative'den biraz daha düşüktür.

### EAGLE — hidden state'leri yeniden kullanarak daha iyi draft

EAGLE-1/2/3 (Li et al., 2024–2025) draft modeli, doğrulayıcının son-katman hidden state'lerini içine alan minik bir transformer (tipik olarak 1 katman) yapar. Draft, doğrulayıcının özellik temsilini gördüğü için, tahminleri doğrulayıcının çıktı dağılımıyla güçlü şekilde korelasyon yapar. Kabul oranları ~0.6'dan (vanilla) 0.85+'a tırmanır.

EAGLE-3 (2025), aday devamlarda tree search ekledi. vLLM ve SGLang, Llama 3/4 ve Qwen 3 için varsayılan spec yolu olarak EAGLE-2/3 gönderir.

### KV cache dansı

Doğrulama, `N` draft token'ı doğrulayıcıya tek bir forward pass'te besler. Bu, doğrulayıcının KV cache'ini `N` giriş kadar uzatır. Bazı draft'lar reddedilirse, cache'i kabul edilmiş prefix uzunluğuna geri sarmalısın.

Production implementasyonları (vLLM'in `--speculative-model`'i, TensorRT-LLM'in LookaheadDecoder'ı) bunu scratch KV buffer'larıyla halleder. Önce yaz, kabulde commit et. Kavramsal olarak zor değil ama detaycı.

## İnşa Et

`code/main.py`'a bak. Çekirdek speculative-sampling algoritmasını (rejection adımı + residual dağılım) şunlarla implement ediyoruz:

- Elle kodlanmış bir dağılım üzerinde deterministik-softmax olan bir "büyük model" (kabul matematiğini analitik olarak doğrulayabilelim diye).
- Büyük modelin bir perturbasyonu olan bir "draft model".
- Doğrudan örneklemeyle aynı marjinal dağılımı üreten bir kabul / red döngüsü.

### Adım 1: red adımı

```python
def accept_or_reject(q_prob, p_prob, draft_token, u):
    ratio = q_prob / p_prob if p_prob > 0 else float("inf")
    return u < min(1.0, ratio)
```

`u` uniform rastgele sayıdır. `q_prob`, draft edilen token için doğrulayıcının olasılığıdır. `p_prob`, draft modelinin olasılığıdır. Leviathan teoremi, bu Bernoulli kararının, redde residual'dan örnekleme ile takip edildiğinde, doğrulayıcının dağılımını tam olarak koruduğudur.

### Adım 2: residual dağılım

```python
def residual_dist(q, p):
    raw = [max(0.0, qi - pi) for qi, pi in zip(q, p)]
    s = sum(raw)
    return [r / s for r in raw]
```

`p`'yi `q`'dan eleman bazında çıkar, negatif değerleri sıfıra clamp et, yeniden normalize et. Herhangi bir redde bundan sample al.

### Adım 3: tek bir speculative adımı

```python
def spec_step(prefix, q_model, p_model, N, rng):
    drafts = []
    p_probs = []
    ctx = list(prefix)
    for _ in range(N):
        p_dist = p_model(ctx)
        d = sample(p_dist, rng)
        drafts.append(d)
        p_probs.append(p_dist[d])
        ctx.append(d)

    q_dists = [q_model(prefix + drafts[:i]) for i in range(N + 1)]

    for i, d in enumerate(drafts):
        u = rng.random()
        q_prob = q_dists[i][d]
        p_prob = p_probs[i]
        if u < min(1.0, q_prob / p_prob if p_prob > 0 else float("inf")):
            prefix = prefix + [d]
        else:
            res = residual_dist(q_dists[i], p_model(prefix))
            prefix = prefix + [sample(res, rng)]
            return prefix
    prefix = prefix + [sample(q_dists[N], rng)]
    return prefix
```

Beş kabul → bir bonus → tek doğrulayıcı pass'inde altı token üretildi.

### Adım 4: kabul oranını ölç

Değişen draft-kalite seviyelerinde 10.000 speculative adımı çalıştır. Draft ve doğrulayıcı dağılımları arasındaki KL ıraksamasına karşı kabul oranını çiz. Temiz bir monoton ilişki görmelisin.

### Adım 5: dağılım eşdeğerliğini doğrula

Ampirik olarak: speculative döngüsünün ürettiği token histogramı, doğrulayıcıdan doğrudan örnekleme ile üretilen histogramla eşleşmeli. Bu pratikte Leviathan teoremidir. Bir chi-square testi örnekleme hatası içinde doğrular.

## Kullan

Production:

```bash
# EAGLE ile vLLM
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-model /models/llama-3.1-eagle-70b \
    --speculative-draft-tensor-parallel-size 1 \
    --num-speculative-tokens 5

# Vanilla draft model ile vLLM
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-model meta-llama/Llama-3.2-1B-Instruct \
    --num-speculative-tokens 5
```

TensorRT-LLM, 2026 ortası itibarıyla en hızlı Medusa yoluna sahip. `faster-whisper`, küçük bir draft'la Whisper-large için speculative decoding sarar.

**Draft seçmek:**

| Strateji | Ne zaman seçilir | Hızlanma |
|----------|--------------|---------|
| Vanilla draft (1B/3B Llama ailesi) | Hızlı prototip, eğitim yok | 1.8–2.3× |
| Medusa head'leri | Doğrulayıcıyı fine-tune edebilirsin | 2–3× |
| EAGLE-2 / 3 | Production, maks hız | 3–4× |
| Lookahead | Draft yok, eğitim yok, ekstra param yok | 1.3–1.6× |

**Spec-decode NE ZAMAN YAPILMAMALI:**

- 1–5 token'lık tek dizi üretimi. Overhead hakimdir.
- Vahşi yaratıcı / yüksek-temperature örnekleme (α düşer).
- Bellek-kısıtlı dağıtımlar (draft model VRAM ekler).

## Yayınla

`outputs/skill-spec-decode-picker.md`'ye bak. Skill, yeni bir çıkarım workload'u için bir speculative decoding stratejisi (vanilla / Medusa / EAGLE / lookahead) ve tuning parametreleri (N, draft temperature) seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. 50.000 token üzerinde speculative token dağılımının doğrulayıcının doğrudan-sample dağılımıyla chi-square p > 0.05 içinde eşleştiğini doğrula.
2. **Orta.** `α = 0.5, 0.7, 0.85` için hızlanmayı (büyük-model forward başına token) `N`'nin bir fonksiyonu olarak çiz. Her α için optimal `N`'i tanımla. (İpucu: doğrulama çağrısı başına beklenen token = `(1 - α^{N+1}) / (1 - α)`.)
3. **Zor.** Minik bir Medusa implement et: Ders 14'teki bitirme GPT'sini al, t+2, t+3, t+4 pozisyonlarını tahmin eden 3 ekstra LM head ekle. Birleşik multi-head loss'la tinyshakespeare üzerinde eğit. Aynı modeli kısaltarak yapılan vanilla bir draft'a karşı kabul oranlarını karşılaştır.
4. **Zor.** Rollback implement et: 10 token'lık bir prefix KV cache ile başla, 5 draft token besle, pozisyon 3'te bir reddi simüle et. Bir sonraki iterasyonda cache okumalarının "prefix + ilk 2 kabul edilen draft" ile doğru eşleştiğini doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Draft model | "Ucuz olan" | Aday token'ları öneren daha küçük bir model; genelde doğrulayıcıdan 10–50× daha ucuz. |
| Doğrulayıcı | "Büyük olan" | Dağılımını koruduğumuz hedef model; speculative adım başına bir kere çalışır. |
| Kabul oranı (α) | "Draft ne kadar sıklıkla doğru" | Doğrulayıcının draft'ı kabul ettiği token başına olasılık. Tipik 0.7–0.9. |
| Residual dağılım | "Red fallback'i" | Normalize edilmiş `(q - p)_+`; redde bundan örnekleme doğrulayıcının dağılımını korur. |
| Bonus token | "Bedava olan" | N draft'ın hepsi kabul edildiğinde, doğrulayıcının sonraki-adım dağılımından bir tane daha sample al. |
| Medusa | "Draft'sız speculative" | Doğrulayıcı üzerinde t+1..t+k pozisyonlarını paralel tahmin eden birden fazla LM head'i. |
| EAGLE | "Hidden-state draft" | Doğrulayıcının son-katman hidden state'lerine koşullandırılmış minik transformer draft. |
| Lookahead decoding | "Jacobi iterasyonu" | Fixed-point iterasyon kullanan self-speculation; draft model yok. |
| Tree attention | "Birçok adayı bir kerede doğrula" | Birden fazla draft devamını aynı anda göz önüne alan dallanmalı doğrulama. |
| KV rollback | "Reddedilen draft'ları geri al" | Scratch KV buffer; kabulde commit et, redde at. |

## İleri Okuma

- [Leviathan, Kalman, Matias (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — çekirdek algoritma ve eşdeğerlik teoremi.
- [Chen et al. (2023). Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318) — eşzamanlı tanıtım; temiz Bernoulli-rejection kanıtı.
- [Cai et al. (2024). Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — Medusa makalesi; tree-attention doğrulama.
- [Li et al. (2024). EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — EAGLE-1; hidden-state-koşullu draft.
- [Li et al. (2024). EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees](https://arxiv.org/abs/2406.16858) — EAGLE-2; dinamik tree derinliği.
- [Li et al. (2025). EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](https://arxiv.org/abs/2503.01840) — EAGLE-3.
- [Fu et al. (2024). Break the Sequential Dependency of LLM Inference Using Lookahead Decoding](https://arxiv.org/abs/2402.02057) — lookahead, draft'sız yaklaşım.
- [vLLM docs — Speculative Decoding](https://docs.vllm.ai/en/latest/features/spec_decode.html) — dört stratejinin de bağlı olduğu kanonik production referansı.
- [SafeAILab / EAGLE reference implementation](https://github.com/SafeAILab/EAGLE) — EAGLE-1/2/3 için referans kod.
