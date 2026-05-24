# Multi-Head Attention

> Tek bir attention head bir seferde tek bir ilişki öğrenir. Sekiz head sekiz öğrenir. Head'ler bedava. Daha fazla al.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 02 (Sıfırdan Self-Attention)
**Süre:** ~75 dakika

## Sorun

Tek bir self-attention head, tek bir attention matrisi hesaplar. O matris tek tip ilişki yakalar — genelde eğitim sinyali ne olursa olsun loss'u minimize eden. Verinde özne-yüklem uyumu, co-reference, uzun-mesafe söylem ve syntactic chunking hep iç içe geçmişse, tek bir head bunları tek bir softmax dağılımına bulaştırır ve sinyalin yarısını kaybeder.

2017 Vaswani makalesindeki çözüm: her biri kendi Q, K, V projeksiyonlarına sahip birkaç attention fonksiyonunu paralel çalıştır ve çıktıları birleştir. Her head `d_model / n_heads` boyutunda daha küçük bir altuzayda çalışır. Toplam parametreler aynı kalır. Anlatım gücü artar.

Multi-head attention, 2026'daki her transformer'ın gönderdiği varsayılandır. Tek tartışma *kaç tane* head ve key'ler ile value'ların projeksiyonları paylaşıp paylaşmayacağı hakkında (Grouped-Query Attention, Multi-Query Attention, Multi-head Latent Attention).

## Kavram

![Multi-head attention böler, attention yapar, birleştirir](../assets/multi-head-attention.svg)

**Böl.** `(N, d_model)` şeklinde `X`'i al. Her biri `(N, d_model)` şeklinde Q, K, V'ye projeksiyona uğrat. `d_head = d_model / n_heads` olacak şekilde `(N, n_heads, d_head)`'a reshape et. `(n_heads, N, d_head)`'a transpoze et.

**Paralel attention yap.** Her head'in içinde scaled dot-product attention çalıştır. Her head `(N, d_head)` üretir. Head'ler embedding'in farklı altuzaylarında çalışır ve attention hesaplaması sırasında birbirleriyle konuşmaz.

**Birleştir ve projeksiyona uğrat.** Head'leri `(N, d_model)`'e geri yığ ve `(d_model, d_model)` şeklinde öğrenilmiş bir çıktı matrisi `W_o` ile çarp. Head'lerin karıştığı yer `W_o`.

**Neden işe yarar.** Her head, temsil bütçesi için diğerleriyle yarışmadan uzmanlaşabilir. 2019–2024 probing çalışmaları farklı head rolleri gösteriyor: pozisyonel head'ler, önceki token'a attention yapan head, copy head'ler, named-entity head'ler, induction head'ler (in-context learning'in altında yatan).

**2026 varyasyon soyağacı:**

| Varyant | Q head'leri | K/V head'leri | Kullanan |
|---------|---------|-----------|---------|
| Multi-head (MHA) | N | N | GPT-2, BERT, T5 |
| Multi-query (MQA) | N | 1 | PaLM, Falcon |
| Grouped-query (GQA) | N | G (örn. N/8) | Llama 2 70B, Llama 3+, Qwen 2+, Mistral |
| Multi-head latent (MLA) | N | low-rank'a sıkıştırılmış | DeepSeek-V2, V3 |

GQA modern varsayılandır çünkü KV cache belleğini `N/G` faktörü kadar kısar ve neredeyse tam kaliteyi korur. MLA daha da ileri gider: K/V'yi bir latent uzaya sıkıştırır, sonra hesaplama anında geri projeksiyona uğratır — FLOPs harcar, çok daha fazla bellek tasarrufu yapar.

## İnşa Et

### Adım 1: Zaten sahip olduğumuz tek-head'li attention'dan head'leri böl

Ders 02'deki `SelfAttention`'ı al ve bir split/concat çiftiyle sar. NumPy implementasyonu için `code/main.py`'a bak; mantık şu:

```python
def split_heads(X, n_heads):
    n, d = X.shape
    d_head = d // n_heads
    return X.reshape(n, n_heads, d_head).transpose(1, 0, 2)  # (heads, n, d_head)

def combine_heads(H):
    h, n, d_head = H.shape
    return H.transpose(1, 0, 2).reshape(n, h * d_head)
```

Bir reshape ve bir transpose. Loop yok. PyTorch'un `nn.MultiheadAttention` altında yaptığı tam olarak budur.

### Adım 2: head başına scaled-dot-product attention çalıştır

Her head, Q, K, V'nin kendi dilimini alır. Attention bir batched matmul olur:

```python
def mha_forward(X, W_q, W_k, W_v, W_o, n_heads):
    Q = X @ W_q
    K = X @ W_k
    V = X @ W_v
    Qh = split_heads(Q, n_heads)         # (heads, n, d_head)
    Kh = split_heads(K, n_heads)
    Vh = split_heads(V, n_heads)
    scores = Qh @ Kh.transpose(0, 2, 1) / np.sqrt(Qh.shape[-1])
    weights = softmax(scores, axis=-1)
    out = weights @ Vh                    # (heads, n, d_head)
    concat = combine_heads(out)
    return concat @ W_o, weights
```

Gerçek donanımda `Qh @ Kh.transpose(...)` tek bir `bmm`'dir. GPU, `(heads, N, d_head) × (heads, d_head, N) -> (heads, N, N)` şeklinde tek bir batched matmul görür. Head eklemek bedavadır.

### Adım 3: Grouped-Query Attention varyantı

Yalnızca key ve value projeksiyonları değişir. Q `n_heads` grup alır; K ve V `n_kv_heads < n_heads` grup alır ve eşleşmesi için tekrar edilir:

```python
def gqa_project(X, W, n_kv_heads, n_heads):
    kv = split_heads(X @ W, n_kv_heads)       # (kv_heads, n, d_head)
    repeat = n_heads // n_kv_heads
    return np.repeat(kv, repeat, axis=0)      # (n_heads, n, d_head)
```

Çıkarımda bu bellek tasarrufu sağlar çünkü KV cache'inde `n_heads` değil yalnızca `n_kv_heads` kopya yaşar. Llama 3 70B 8 KV head ile 64 query head kullanır — 8× cache küçülmesi.

### Adım 4: her head'in ne öğrendiğini incele

4 head'le kısa bir cümlede MHA çalıştır. Her head için `(N, N)` attention matrisini yazdır. Rastgele initialization ile bile farklı head'lerin farklı yapıyı seçtiğini göreceksin — bu kısmen sinyal, kısmen altuzaylardaki rotasyonel simetri.

## Kullan

PyTorch'ta tek satırlık versiyon:

```python
import torch.nn as nn

mha = nn.MultiheadAttention(embed_dim=512, num_heads=8, batch_first=True)
```

PyTorch 2.5+'tan itibaren GQA:

```python
from torch.nn.functional import scaled_dot_product_attention

# scaled_dot_product_attention CUDA'da otomatik olarak Flash Attention'a dispatch eder.
# GQA için Q'yu (B, n_heads, N, d_head) şeklinde ve K,V'yi (B, n_kv_heads, N, d_head)
# şeklinde geçir. PyTorch repeat işlemini halleder.
out = scaled_dot_product_attention(q, k, v, is_causal=True, enable_gqa=True)
```

**Kaç head?** 2026 production model'lerinden parmak hesabı:

| Model boyutu | d_model | n_heads | d_head |
|------------|---------|---------|--------|
| Small (~125M) | 768 | 12 | 64 |
| Base (~350M) | 1024 | 16 | 64 |
| Large (~1B) | 2048 | 16 | 128 |
| Frontier (~70B) | 8192 | 64 | 128 |

`d_head` neredeyse her zaman 64 veya 128'e iner. Tek bir head'in ne kadar "görebileceğinin" birimidir. 32'nin altına düş, head'ler ölçekleme faktörü `sqrt(d_head)` ile savaşmaya başlar; 256'nın üzerine çık, "çok sayıda küçük uzman" avantajını kaybedersin.

## Yayınla

`outputs/skill-mha-configurator.md`'ye bak. Skill, parametre bütçesi, sequence length ve dağıtım hedefi verilen yeni bir transformer için head sayısı, kv-head sayısı ve projeksiyon stratejisi önerir.

## Alıştırmalar

1. **Kolay.** `code/main.py`'daki MHA'yı al ve `d_model=64` sabitken `n_heads`'i 1'den 16'ya değiştir. Sentetik bir copy görevinde küçük tek-katmanlı bir modelin loss'unu çiz. Daha fazla head yardım eder mi, plato'ya mı ulaşır, zarar mı verir?
2. **Orta.** MQA (tüm query head'leri arasında paylaşılan tek bir KV head) implement et. Parametre sayısının tam MHA'ya göre ne kadar düştüğünü ölç. N=2048'de çıkarımda KV cache boyutunun ne kadar küçüldüğünü hesapla.
3. **Zor.** Multi-head Latent Attention'ın küçük bir versiyonunu implement et: K,V'yi rank-`r` bir latent'e sıkıştır, latent'i KV cache'de sakla, attention zamanında dekompres et. Hangi `r`'de cache belleği tam MHA'nın 1/8'inin altına geçer ve kalite validation ppl'sinin 1 bit'i içinde kalır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Head | "Tek bir attention devresi" | Kendi attention matrisine sahip `d_head = d_model / n_heads` boyutunda bir Q/K/V projeksiyonu. |
| d_head | "Head boyutu" | Head başına hidden genişlik; production'da neredeyse her zaman 64 veya 128. |
| Split / combine | "Reshape numaraları" | Attention etrafında `(N, d_model) ↔ (n_heads, N, d_head)` reshape+transpose. |
| W_o | "Çıktı projeksiyonu" | Head'leri birleştirdikten sonra uygulanan `(d_model, d_model)` matris; head'lerin karıştığı yer. |
| MQA | "Tek KV head" | Multi-Query Attention: tek paylaşılan K/V projeksiyonu. En küçük KV cache, biraz kalite kaybı. |
| GQA | "Llama 2'den beri varsayılan" | `n_kv_heads < n_heads` ile Grouped-Query Attention; Q'ya eşleşmek için tekrarlanır. |
| MLA | "DeepSeek'in numarası" | Multi-head Latent Attention: K,V low-rank latent'e sıkıştırılmış, attention zamanında dekompres edilmiş. |
| Induction head | "In-context learning'in arkasındaki devre" | Önceki oluşumları tespit eden ve onları takip edeni kopyalayan bir head çifti. |

## İleri Okuma

- [Vaswani et al. (2017). Attention Is All You Need §3.2.2](https://arxiv.org/abs/1706.03762) — orijinal multi-head spec.
- [Shazeer (2019). Fast Transformer Decoding: One Write-Head is All You Need](https://arxiv.org/abs/1911.02150) — MQA makalesi.
- [Ainslie et al. (2023). GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245) — eğitimden sonra MHA'yı GQA'ya nasıl dönüştürülür.
- [DeepSeek-AI (2024). DeepSeek-V2 Technical Report](https://arxiv.org/abs/2405.04434) — MLA ve cache belleğinde neden MHA/GQA'yı yendiği.
- [Olsson et al. (2022). In-context Learning and Induction Heads](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html) — head'lerin gerçekte ne yaptığına mekanistik bakış.
