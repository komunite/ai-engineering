# Attention Varyantları — Sliding Window, Sparse, Differential

> Tam attention bir çemberdir. Her token her token'ı görür ve bedeli bellek öder. Dört varyant çemberin şeklini büker ve maliyetin yarısını kurtarır.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 02 (Self-Attention), Faz 7 · 03 (Multi-Head), Faz 7 · 12 (KV Cache / Flash Attention)
**Süre:** ~60 dakika

## Sorun

Tam attention, sequence length'te `O(N²)` bellek ve `O(N²)` compute eder. 128K-context Llama 3 70B için bu katman başına 16 milyar attention girişi, 80 katmanla çarpılı. Flash Attention (Ders 12) `O(N²)` aktivasyon belleğini gizler ama aritmetik maliyeti değiştirmez — her token hâlâ diğer her token'a attention yapar.

Üç sınıf varyant attention matrisinin topolojisini kendisini değiştirir:

1. **Sliding window attention (SWA).** Her token tam prefix'e değil, sabit bir komşu penceresine attention yapar. Bellek ve compute, `W` pencere olmak üzere `O(N · W)`'ye düşer. Gemma 2/3, Mistral 7B'nin ilk katmanları, Phi-3-Long.
2. **Sparse / block attention.** Yalnızca seçili `(i, j)` çiftleri skor alır; geri kalanlar sıfır ağırlığa zorlanır. Longformer, BigBird, OpenAI sparse transformer.
3. **Differential attention.** Ayrı Q/K projeksiyonlarıyla iki attention haritası hesapla, birini diğerinden çıkar. Ağırlığı ilk birkaç token'a sızdıran "attention sink"i öldürür. Microsoft'un DIFF Transformer'ı (2024).

Bunlar bir arada var olur. 2026 frontier model genelde bunları karıştırır: çoğu katman SWA-1024, her beşinci global tam attention ve bir avuç retrieval'ı temizleyen differential head. Gemma 3'ün 5:1 SWA-to-global oranı şu anki textbook varsayılanıdır.

## Kavram

### Sliding Window Attention (SWA)

Pozisyon `i`'deki her query yalnızca `[i - W, i]` (causal SWA) veya `[i - W/2, i + W/2]` (çift yönlü) pozisyonlarına attention yapar. Pencere dışındaki token'lar skor matrisinde `-inf` alır.

```
tam causal:            sliding window (W=4):
pozisyonlar 0-7        pozisyonlar 0-7, W=4
    0 1 2 3 4 5 6 7        0 1 2 3 4 5 6 7
0 | x                0 |  x
1 | x x              1 |  x x
2 | x x x            2 |  x x x
3 | x x x x          3 |  x x x x
4 | x x x x x        4 |    x x x x
5 | x x x x x x      5 |      x x x x
6 | x x x x x x x    6 |        x x x x
7 | x x x x x x x x  7 |          x x x x
```

`N = 8192` ve `W = 1024` için, skor matrisi beklenti olarak 1024 × 8192 sıfır olmayan satıra sahip — 8× azalma.

**KV cache SWA ile küçülür.** Katman başına yalnızca K ve V'nin son `W` token'ı tutulmalı. Gemma-3-vari bir konfigürasyon için (1024 pencere, 128K context), KV cache 128× düşer.

**Kalite maliyeti.** Yalnız-SWA transformer'lar uzun-mesafe retrieval'da zorlanır. Çözüm: SWA katmanlarını tam-attention katmanlarıyla iç içe geçir. Gemma 3, 5:1 SWA:global kullanır. Mistral 7B, bilginin örtüşen pencereler üzerinden "ileri aktığı" bir causal-SWA yığını kullandı — her katman efektif alıcı alanı `W` kadar uzatır ve `L` katmandan sonra model `L × W` token geriye attention yapabilir.

### Sparse / Block Attention

Önceden bir `N × N` sparsity pattern'i seç. Üç kanonik şekil:

- **Local + strided (OpenAI sparse transformer).** Son `W` token'a artı ondan önceki her `stride`-inci token'a attention yap. Hem local hem long-range'i `O(N · sqrt(N))` compute'ta yakalar.
- **Longformer / BigBird.** Local pencere + herkese attention yapan ve herkes tarafından attention yapılan küçük bir global token kümesi (örn. `[CLS]`) + random-sparse bağlantılar. Eşleşen kalitede ampirik 2× context.
- **Native Sparse Attention (DeepSeek, 2025).** Hangi `(Q, K)` bloklarının önemli olduğunu öğren; kernel seviyesinde sıfır blokları atla. FlashAttention-uyumlu.

Sparse attention bir kernel-mühendisliği hikayesidir. Matematik basittir (skor matrisini mask'le); kazanç sıfır girdileri SRAM'e hiç yüklememekten gelir. FlashAttention-3 ve 2026 FlexAttention API'si PyTorch'ta özel sparse pattern'leri birinci sınıf yapar.

### Differential Attention (DIFF Transformer, 2024)

Normal attention'ın bir "attention sink" sorunu vardır: softmax her satırın toplamının 1 olmasını zorlar, bu yüzden özellikle bir şeye attention yapmak istemeyen token'lar ağırlığı ilk token'a (veya ilk birkaçına) döker. Bu, gerçek içeriğe gitmesi gereken kapasiteyi çalar.

Differential attention bunu **iki** attention haritası hesaplayıp çıkararak düzeltir:

```
A1 = softmax(Q1 K1^T / √d)
A2 = softmax(Q2 K2^T / √d)
DiffAttn = (A1 - λ · A2) V
```

burada `λ` öğrenilmiş bir skalerdir (tipik olarak 0.5–0.8). A1 gerçek içerik ağırlıklarını yakalar; A2 sink'i yakalar. Çıkarma sink'i iptal eder, ağırlığı alakalı token'lara yeniden dağıtır.

Raporlanan sonuçlar (Microsoft 2024): %5–10 daha düşük perplexity, aynı eğitilmiş uzunlukta 1.5–2× daha uzun efektif context, daha keskin needle-in-haystack retrieval.

### Varyant Karşılaştırması

| Varyant | Compute | KV cache | Tam'a karşı kalite | Production kullanımı |
|---------|---------|----------|-----------------|----------------|
| Tam attention | O(N²) | katman başına O(N) | baseline | her modelin varsayılan katmanı |
| SWA (pencere 1024) | O(N·W) | katman başına O(W) | -0.1 ppl, global katmanlarla iyi | Gemma 2/3, Phi-3-Long |
| Local + strided sparse | O(N·√N) | karışık | SWA'ya benzer | OpenAI sparse transformer, Longformer |
| BigBird (local + global + random) | yaklaşık O(N) | karışık | 2× context'te tam'ı eşleştirir | erken long-context BERT |
| Native Sparse (DeepSeek-V3.2) | O(N · aktif kesir) | O(N) | 0.05 ppl içinde | DeepSeek-V3.2, 2025 |
| Differential | O(2·N²) | O(2N) | -%5 ila -%10 ppl | DIFF Transformer, erken 2026 modelleri |

## İnşa Et

`code/main.py`'a bak. Oyuncak bir dizide yan yana full, SWA, local+strided ve differential attention'ı gösteren bir causal mask karşılaştırıcısı implement ediyoruz.

### Adım 1: tam causal mask (baseline)

```python
def causal_mask(n):
    return [[0.0 if j <= i else float("-inf") for j in range(n)] for i in range(n)]
```

Ders 07'den baseline. Alt üçgensel; diyagonal üzerinde sıfır ağırlık.

### Adım 2: sliding window causal mask

```python
def swa_mask(n, window):
    M = [[float("-inf")] * n for _ in range(n)]
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(lo, i + 1):
            M[i][j] = 0.0
    return M
```

Tek parametre — `window`. `window >= n` için tam causal attention'a kavuşursun. `window = 1` için, her token yalnızca kendisine attention yapar.

### Adım 3: local + strided sparse mask

```python
def strided_mask(n, window, stride):
    M = [[float("-inf")] * n for _ in range(n)]
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(lo, i + 1):
            M[i][j] = 0.0
        for j in range(0, i + 1, stride):
            M[i][j] = 0.0
    return M
```

Yoğun local pencere artı dizinin başına kadar her `stride`-inci token. Alıcı alan ek katmanlarla log adımlarda büyür.

### Adım 4: differential attention

```python
def diff_attention(Q1, K1, Q2, K2, V, lam):
    A1 = softmax_causal(Q1 @ K1.T / sqrt_d)
    A2 = softmax_causal(Q2 @ K2.T / sqrt_d)
    return (A1 - lam * A2) @ V
```

İki attention pass'i, öğrenilmiş karışım katsayısıyla çıkar. Kodda single vs differential'ın attention-sink heatmap'ini karşılaştırıyoruz ve sink'in çöktüğünü izliyoruz.

### Adım 5: KV cache boyutları

`N = 131072`'de her varyant için katman başına cache boyutunu yazdır. SWA ve sparse varyantlar 10–100× düşer. Differential ikiye katlar. Bellek faturanı bilinçli öde.

## Kullan

2026 production pattern'leri:

```python
from transformers import AutoModelForCausalLM
# Gemma 3, SWA'yı (window=1024) ve global katmanları 5:1'de karıştırır.
model = AutoModelForCausalLM.from_pretrained("google/gemma-3-27b-it")
# print(model.config.sliding_window, model.config.layer_types)
```

PyTorch 2.5+'taki FlexAttention bir mask fonksiyonu kabul eder:

```python
from torch.nn.attention.flex_attention import flex_attention, create_block_mask

def swa_pattern(b, h, q_idx, kv_idx):
    return (q_idx - kv_idx < 1024) & (q_idx >= kv_idx)

mask = create_block_mask(swa_pattern, B=batch, H=heads, Q_LEN=n, KV_LEN=n)
out = flex_attention(q, k, v, block_mask=mask)
```

Bu özel bir Triton kernel'e derlenir. Yaygın pattern'ler için FlashAttention-3 hızının %10 içinde ve mask fonksiyonu Python callable'ı.

**Her birini ne zaman seçmeli:**

- **Saf tam attention** — ~16K context'e kadar her katman veya retrieval kalitesinin en önemli olduğu yer.
- **SWA + global karışımı** — uzun context (>32K), eğitim ve çıkarım bellek-bağımlı. 32K üstünde 2026 varsayılanı.
- **Sparse block attention** — özel kernel, özel pattern. Özelleşmiş workload'lar için ayrılmış (retrieval, ses).
- **Differential attention** — attention-sink kontaminasyonunun zarar verdiği herhangi bir workload (uzun-context RAG, needle-in-haystack).

## Yayınla

`outputs/skill-attention-variant-picker.md`'ye bak. Skill, hedef context length, retrieval talepleri ve eğitim/çıkarım compute profili verilen yeni bir model için bir attention topolojisi seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. `window=4`'te SWA'nın satır başına son 4 token dışındaki her şeyi sıfırladığını doğrula. `window=n`'nin tam causal attention'ı bit-aynı ürettiğini doğrula.
2. **Orta.** Ders 07 bitirme projesinin üstünde `window=1024` ile causal SWA implement et. tinyshakespeare'de 1.000 adım eğit. Val loss tam attention'a göre ne kadar geriler? Tepe bellek ne kadar düşer?
3. **Zor.** Bitirme modelinde Gemma-3 tarzı 5:1 katman karışımı (5 SWA, 1 global) implement et. Eşleşen parametrelerde saf-SWA ve saf-global baseline'lara karşı loss, bellek ve üretim kalitesini karşılaştır.
4. **Zor.** Head başına öğrenilmiş `λ` ile differential attention implement et. Sentetik bir retrieval görevinde eğit (bir iğne, 2.000 distraktör). Eşleşen parametrelerde tek-attention baseline'a karşı retrieval doğruluğunu ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Sliding window attention (SWA) | "Local attention" | Her query son `W` token'ına attention yapar; KV cache `O(W)`'ye küçülür. |
| Efektif alıcı alan | "Modelin ne kadar geriye gördüğü" | Pencere `W` olan `L`-katmanlı SWA yığınında, `L × W` token'a kadar. |
| Longformer / BigBird | "Local + global + random" | Birkaç her-zaman-attention yapan global token'lı sparse pattern'ler; erken long-context yaklaşımı. |
| Native Sparse Attention | "DeepSeek'in kernel numarası" | Blok-seviyesi sparsity'yi öğren; kaliteyi korurken kernel seviyesinde sıfır blokları atla. |
| Differential attention | "İki harita, biri çıkarır" | DIFF Transformer: attention sink'leri iptal etmek için ikinciden öğrenilmiş `λ` katı bir attention haritasını birinciden çıkar. |
| Attention sink | "Ağırlık token 0'a sızar" | Softmax normalizasyonu satırların toplamının 1 olmasını zorlar; bilgilendirici olmayan query'ler ağırlığı pozisyon 0'a döker. |
| FlexAttention | "Python-olarak-mask" | PyTorch 2.5+ API'si, keyfi mask fonksiyonlarını FlashAttention-biçimli kernel'lere derler. |
| Katman tipi karışımı | "5:1 SWA-to-global" | Daha düşük bellekte kaliteyi korumak için bir yığında sparse ve full attention katmanlarını iç içe geçir. |

## İleri Okuma

- [Beltagy, Peters, Cohan (2020). Longformer: The Long-Document Transformer](https://arxiv.org/abs/2004.05150) — kanonik sliding-window + global-token makalesi.
- [Zaheer et al. (2020). Big Bird: Transformers for Longer Sequences](https://arxiv.org/abs/2007.14062) — local + global + random.
- [Child et al. (2019). Generating Long Sequences with Sparse Transformers](https://arxiv.org/abs/1904.10509) — OpenAI'ın local+strided pattern'i.
- [Gemma Team (2024). Gemma 2: Improving Open Language Models at a Practical Size](https://arxiv.org/abs/2408.00118) — 1:1 SWA:global karışımı.
- [Gemma Team (2025). Gemma 3 technical report](https://arxiv.org/abs/2503.19786) — şimdi textbook varsayılanı olan window=1024 ile 5:1 karışım.
- [Ye et al. (2024). Differential Transformer](https://arxiv.org/abs/2410.05258) — DIFF Transformer makalesi.
- [Yuan et al. (2025). Native Sparse Attention](https://arxiv.org/abs/2502.11089) — DeepSeek-V3.2'nin öğrenilmiş-sparsity attention'ı.
- [PyTorch — FlexAttention blog and docs](https://pytorch.org/blog/flexattention/) — Kullan'daki mask-as-callable pattern'i için API referansı.
