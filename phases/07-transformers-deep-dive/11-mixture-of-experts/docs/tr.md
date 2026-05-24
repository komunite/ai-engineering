# Mixture of Experts (MoE)

> Yoğun 70B transformer her token için her parametreyi aktive eder. 671B MoE token başına yalnızca 37B aktive eder ve her benchmark'ta onu yener. Sparsity, on yılın en önemli ölçekleme fikridir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 05 (Tam Transformer), Faz 7 · 07 (GPT)
**Süre:** ~45 dakika

## Sorun

Yoğun bir transformer'ın çıkarımdaki FLOPs'u parametre sayısına eşittir (forward pass için 2 ile çarpılı). Bir yoğun modeli ölçeklendir ve her token tam faturayı öder. 2024'e gelindiğinde frontier bir compute duvarına çarpıyordu: anlamlı şekilde daha akıllı olmak için token başına üstel olarak daha fazla FLOPs gerekiyordu.

Mixture of Experts bu bağlantıyı kırar. Her FFN'i `E` bağımsız uzman + token başına `k` uzman seçen bir router ile değiştir. Toplam parametreler = `E × FFN_size`. Token başına aktif parametreler = `k × FFN_size`. Tipik 2026 konfigürasyonu: `E=256`, `k=8`. Depolama `E` ile ölçeklenir, hesaplama `k` ile ölçeklenir.

2026 frontier neredeyse tamamen MoE: DeepSeek-V3 (671B toplam / 37B aktif), Mixtral 8×22B, Qwen2.5-MoE, Llama 4, Kimi K2, gpt-oss. Artificial Analysis'in bağımsız leaderboard'unda, top 10 açık-kaynak modelin hepsi MoE.

## Kavram

![MoE katmanı: router token başına E uzmandan k tanesini seçer](../assets/moe.svg)

### FFN takası

Yoğun transformer bloğu:

```
h = x + attn(norm(x))
h = h + FFN(norm(h))
```

MoE bloğu:

```
h = x + attn(norm(x))
scores = router(norm(h))              # (N_tokens, E)
top_k = argmax_k(scores)              # token başına E uzmandan k seç
h = h + sum_{e in top_k}(
        gate(scores[e]) * Expert_e(norm(h))
    )
```

Her uzman bağımsız bir FFN'dir (tipik olarak SwiGLU). Router tek bir linear katmandır. Her token kendi `k` uzmanını seçer ve çıktılarının gated bir karışımını alır.

### Load-balancing sorunu

Router token'ların %90'ını uzman 3'ten geçirirse, diğer uzmanlar açlık çeker. Üç çözüm denendi:

1. **Auxiliary load-balancing loss** (Switch Transformer, Mixtral). Uzman kullanım varyansıyla orantılı bir ceza ekle. Çalışır ama bir hyperparametre ve ikinci bir gradient sinyali ekler.
2. **Expert capacity + token dropping** (erken Switch). Her uzman en fazla `C × N/E` token işler; taşan token'lar katmanı atlar. Kaliteyi zedeler.
3. **Auxiliary-loss-free balancing** (DeepSeek-V3). Router'ın top-k seçimini kaydıran öğrenilmiş bir uzman başına bias ekle. Bias eğitim loss'unun dışında güncellenir. Ana objektif üzerinde ceza yok. 2024'ün büyük kazanımı.

DeepSeek-V3'ün yaklaşımı: her eğitim adımından sonra, her uzman için kullanımının hedefin üstünde mi altında mı olduğunu kontrol et. Bias'ı `±γ` ile dürt. Seçim `scores + bias` kullanır. Gating için kullanılan uzman olasılıkları değişmemiş ham `scores`'tur. Routing'i ifadeden ayırır.

### Shared expert'ler

DeepSeek-V2/V3 ayrıca uzmanları *shared* ve *routed* olarak böler. Her token tüm shared expert'lerden geçer. Routed expert'ler top-k üzerinden seçilir. Shared expert'ler ortak bilgiyi yakalar; routed expert'ler uzmanlaşır. V3, 256 routed'tan top-8 artı 1 shared expert çalıştırır.

### Fine-grained expert'ler

Klasik MoE (GShard, Switch): her uzman tam bir FFN kadar geniştir. `E` küçük (8–64), `k` küçük (1–2).

Modern fine-grained MoE (DeepSeek-V3, Qwen-MoE): her uzman daha dar (FFN boyutunun 1/8'i). `E` büyük (256+), `k` daha büyük (8+). Aynı toplam parametre, ama kombinasyonlar çok daha hızlı ölçeklenir. `C(256, 8) = 400 trilyon` token başına olası "uzman". Kalite yükselir, latency düz kalır.

### Maliyet profili

Token başına, katman başına:

| Konfigürasyon | Aktif param / token | Toplam param |
|--------|-----------------------|--------------|
| Mixtral 8×22B | ~39B | 141B |
| Llama 3 70B (yoğun) | 70B | 70B |
| DeepSeek-V3 | 37B | 671B |
| Kimi K2 (MoE) | ~32B | 1T |

DeepSeek-V3, token başına **daha az aktif FLOPs** yapar ama neredeyse her benchmark'ta Llama 3 70B'yi (yoğun) yener. Daha fazla parametre = daha fazla bilgi. Daha fazla aktif FLOPs = token başına daha fazla compute. MoE bunları ayırır.

### İncelik: bellek

Tüm uzmanlar hangileri ateşlerse ateşlesin GPU'da yaşar. 671B model, fp16 ağırlıkları için ~1.3 TB VRAM'a ihtiyaç duyar. Frontier MoE dağıtımı uzman paralelizmi gerektirir — uzmanları GPU'lar arasında shard'la, token'ları ağ üzerinden route et. Latency, matmul'a değil, all-to-all iletişime hakimdir.

## İnşa Et

`code/main.py`'a bak. Saf stdlib'de kompakt bir MoE katmanı:

- `n_experts=8` SwiGLU-vari uzman (illüstrasyon için her biri bir linear)
- top-k=2 routing
- softmax-normalize edilmiş gating ağırlıkları
- uzman başına bias üzerinden auxiliary-loss-free balancing

### Adım 1: router

```python
def route(hidden, W_router, top_k, bias):
    scores = [sum(h * w for h, w in zip(hidden, W_router[e])) for e in range(len(W_router))]
    biased = [s + b for s, b in zip(scores, bias)]
    top_idx = sorted(range(len(biased)), key=lambda i: -biased[i])[:top_k]
    # seçilen uzmanların ORİJİNAL skorları üzerinde softmax
    chosen = [scores[i] for i in top_idx]
    m = max(chosen)
    exps = [math.exp(c - m) for c in chosen]
    s = sum(exps)
    gates = [e / s for e in exps]
    return top_idx, gates
```

Bias seçimi etkiler, gate ağırlığını değil. DeepSeek-V3 numarası budur — bias load dengesizliğini modelin tahminlerini yönlendirmeden düzeltir.

### Adım 2: router'dan 100 token geçir

Hangi uzmanların ne sıklıkla ateşlediğini izle. Bias olmadan kullanım çarpık. Bias güncelleme döngüsüyle (aşırı kullanılan uzmanlar için `-γ`, az kullanılanlar için `+γ`), kullanım birkaç iterasyonda uniform bir dağılıma yakınsar.

### Adım 3: param sayısı karşılaştırması

Bir MoE konfigürasyonunun "yoğun eşdeğerini" yazdır. DeepSeek-V3 biçimli: 256 routed + 1 shared, 8 aktif, d_model=7168. Toplam parametre sayısı göz yaşartıcı. Aktif sayı yoğun Llama 3 70B'nin yedide biri.

## Kullan

HuggingFace yükleme:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("mistralai/Mixtral-8x22B-v0.1")
```

2026 production çıkarımı: vLLM MoE routing'i doğal olarak destekler. SGLang en hızlı uzman-paralel yola sahip. Her ikisi de top-k seçimi ve uzman paralelizmini otomatik halleder.

**MoE ne zaman seçilir:**
- Token başına daha düşük çıkarım maliyetinde frontier kalitesi istiyorsun.
- VRAM / uzman-paralel altyapına sahipsin.
- Workload'un token-yoğun (sohbet, kod), context-yoğun değil (uzun belgeler).

**MoE NE ZAMAN SEÇİLMEMELİ:**
- Edge dağıtımı — herhangi bir aktif FLOP için tam depolama ödersin.
- Latency-kritik tek-kullanıcı serving — uzman routing'i overhead ekler.
- Küçük modeller (<7B) — MoE'nin kalite avantajı yalnızca bir compute eşiğinin üzerinde (~6B aktif param) görünür.

## Yayınla

`outputs/skill-moe-configurator.md`'ye bak. Skill, parametre bütçesi, eğitim token'ları ve dağıtım hedefi verilen yeni bir MoE için E, k ve shared-expert düzenini seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. Auxiliary-loss-free bias güncellemesinin 50 iterasyon boyunca uzman kullanımını nasıl eşitlediğini izle.
2. **Orta.** Öğrenilmiş router'ı hash tabanlı bir router ile değiştir (deterministik, öğrenme yok). Kaliteyi ve dengeyi karşılaştır. Öğrenilmiş router neden daha iyi?
3. **Zor.** GRPO tarzı "rollout-matched routing" implement et (DeepSeek-V3.2 numarası): çıkarım sırasında hangi uzmanların ateşlediğini logla, gradient hesaplaması sırasında aynı routing'i zorla. Oyuncak bir policy-gradient kurulumunda etkiyi ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Expert | "Birçok arasında tek FFN" | Bağımsız bir feed-forward network; FFN hesaplamasının sparse bir dilimine ayrılmış parametreler. |
| Router | "Gate" | Her token'ı her uzmana karşı skorlayan minik bir linear katman; top-k seçim. |
| Top-k routing | "Token başına k aktif uzman" | Her token'ın FFN hesaplaması tam olarak k uzmandan, gate ile ağırlıklandırılarak geçer. |
| Auxiliary loss | "Load-balance cezası" | Çarpık uzman kullanımını cezalandıran ekstra loss terimi. |
| Auxiliary-loss-free | "DeepSeek-V3 numarası" | Router'ın seçiminde yalnız uzman başına bias üzerinden denge; ekstra gradient yok. |
| Shared expert | "Her zaman açık" | Her token'ın geçtiği ekstra uzman; ortak bilgiyi yakalar. |
| Expert parallelism | "Uzmana göre shard'la" | Farklı uzmanları farklı GPU'lara dağıt; token'ları ağ üzerinden route et. |
| Sparsity | "Aktif param < toplam param" | `k × expert_size / (E × expert_size)` oranı; DeepSeek-V3 için 37/671 ≈ %5.5. |

## İleri Okuma

- [Shazeer et al. (2017). Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer](https://arxiv.org/abs/1701.06538) — fikir.
- [Fedus, Zoph, Shazeer (2022). Switch Transformer: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961) — Switch, klasik MoE.
- [Jiang et al. (2024). Mixtral of Experts](https://arxiv.org/abs/2401.04088) — Mixtral 8×7B.
- [DeepSeek-AI (2024). DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) — MLA + auxiliary-loss-free MoE + MTP.
- [Wang et al. (2024). Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts](https://arxiv.org/abs/2408.15664) — bias-tabanlı balancing makalesi.
- [Dai et al. (2024). DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066) — bu dersin router'ının kullandığı fine-grained + shared-expert ayırımı.
- [Kim et al. (2022). DeepSpeed-MoE: Advancing Mixture-of-Experts Inference and Training](https://arxiv.org/abs/2201.05596) — orijinal shared-expert makalesi.
