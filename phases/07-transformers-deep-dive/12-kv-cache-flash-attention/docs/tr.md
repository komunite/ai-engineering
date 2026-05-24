# KV Cache, Flash Attention ve Çıkarım Optimizasyonu

> Eğitim paralel ve FLOP-bağımlıdır. Çıkarım seri ve bellek-bağımlıdır. Farklı darboğaz, farklı numaralar.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 02 (Self-Attention), Faz 7 · 05 (Tam Transformer), Faz 7 · 07 (GPT)
**Süre:** ~75 dakika

## Sorun

Naif autoregressive bir decoder, `N` token üretmek için `O(N²)` iş yapar: her adımda tam prefix üzerinde attention'ı yeniden hesaplar. 4K token'lık bir yanıt için bu 16M attention işlemi, çoğu gereksiz. Bir prefix token'ının her hidden state'i hesaplandıktan sonra deterministiktir — yalnızca yeni token'ın query'sini önceki her şeyin cache'lenmiş key ve value'larına karşı çalıştırman gerekir.

Bunun üstüne, attention'ın kendisi çok veri taşır. Standart attention N×N skor matrisini, N×d softmax çıktısını, N×d son çıktıyı materyalize eder — HBM'ye çok fazla okuma ve yazma. N≥2K için, attention FLOP-bağımlı olmadan önce bellek-bağımlı olur. Klasik attention kernel'leri modern GPU'ları 4–10× az kullanır.

İki optimizasyon, ikisi de Dao et al.'dan, frontier çıkarımı "yavaş"tan "hızlı"ya itti:

1. **KV cache.** Her prefix token'ının K ve V vektörlerini sakla. Her yeni token'ın attention'ı cache'lenmiş key'lere karşı bir query'dir. Çıkarım üretim adımı başına `O(N²)`'den `O(N)`'e iner.
2. **Flash Attention.** Tam N×N matris HBM'ye hiç çarpmayacak şekilde attention hesaplamasını tile'la. Tüm softmax + matmul SRAM'de olur. A100'de 2–4× duvar-saati hızlanması; FP8 ile H100'de 5–10×.

2026'ya gelindiğinde ikisi de evrenseldir. Her production çıkarım yığını (vLLM, TensorRT-LLM, SGLang, llama.cpp) onları varsayar. Her frontier model Flash Attention etkin gönderilir.

## Kavram

![KV cache büyümesi ve Flash Attention tiling'i](../assets/kv-cache-flash-attn.svg)

### KV cache matematiği

Decoder katmanı başına, token başına, head başına:

```
bytes_per_token_per_layer = 2 * d_head * dtype_size
                          ^
                          K ve V
```

32 katmanlı, 32 head'li, d_head=128, fp16 olan 7B model için:

```
katman başına token başına = 2 * 128 * 2 = 512 bayt
token başına (32 katman) = 16 KB
32K context başına = 512 MB
```

Llama 3 70B için (80 katman, d_head=128, 8 KV head ile GQA):

```
katman başına token başına = 2 * 8 * 128 * 2 = 4096 bayt (4 KB)
32K context başına = 10.4 GB
```

Bu 10 GB, Llama 3 70B'nin 128K context'te batch size 1'de yalnızca KV cache için bir 40 GB A100'ün çoğuna ihtiyaç duymasının nedenidir.

**KV cache kazancı GQA.** 64 head'li MHA 32 GB olurdu. MLA daha da fazla sıkıştırır.

### Flash Attention — tiling numarası

Standart attention:

```
S = Q @ K^T          (HBM okuma, N×N, HBM yazma)
P = softmax(S)       (HBM okuma, HBM yazma)
O = P @ V            (HBM okuma, HBM yazma)
```

Üç HBM gidiş-dönüşü. H100'de HBM bant genişliği 3 TB/s; SRAM 30 TB/s. Her HBM gezisi, her şeyi chip üzerinde tutmaya kıyasla on kat yavaşlamadır.

Flash Attention:

```
Q'nun her bloğu için (tile boyutu ~128 × 128):
    Q_tile'ı SRAM'e yükle
    K, V'nin her bloğu için:
        K_tile, V_tile'ı SRAM'e yükle
        S_tile = Q_tile @ K_tile^T hesapla     (SRAM)
        çalışan softmax aggregation             (SRAM)
        O_tile'a biriktir                       (SRAM)
    O_tile'ı HBM'e yaz
```

Tile başına bir HBM gezisi. Toplam bellek ayak izi `O(N²)`'den `O(N)`'e düşer. Backward pass değerleri saklamak yerine forward pass'ten bazılarını yeniden hesaplar — başka bir bellek kazanımı.

**Sayısal numara.** Çalışan softmax, son normalizasyon kesin olsun diye tile'lar arasında `(max, sum)` korur. Yaklaştırma değil — Flash Attention standart attention'ın bit-aynı çıktısını hesaplar (fp16 non-associativity modulo).

**Versiyon evrimi:**

| Versiyon | Yıl | Anahtar değişiklik | Referans donanımda hızlanma |
|---------|------|-----------|-------------------------------|
| Flash 1 | 2022 | Tile'lı SRAM kernel | A100'de 2× |
| Flash 2 | 2023 | Daha iyi paralellik, causal-first sıralama | A100'de 3× |
| Flash 3 | 2024 | Hopper asynchrony, FP8 | H100'de 1.5–2× (~740 TFLOPs FP16) |
| Flash 4 | 2026 | Blackwell 5-stage pipeline, software exp2 | Çıkarım-öncelikli (başlangıçta yalnız forward) |

Flash 4 lansmanda yalnız forward-pass. Eğitim hâlâ Flash 3 kullanıyor. Flash 4 için GQA ve varlen desteği beklemede (2026 ortası).

### Speculative decoding — diğer latency kazancı

Ucuz model N token önerir. Büyük model N'in hepsini paralel doğrular. Doğrulama k token kabul ederse, k üretim için 1 büyük-model forward pass ödedin. Kod ve prose'da tipik k=3–5.

2026 varsayılanları:
- **EAGLE 2 / Medusa.** Doğrulayıcının hidden state'lerini paylaşan entegre draft head'leri. Kalite kaybı olmadan 2–3× hızlanma.
- **Draft model'li speculative decoding.** Tüketici donanımında 2–4× hızlanma.
- **Lookahead decoding.** Jacobi iterasyonu; draft model'e gerek yok. Niş ama bedava.

### Continuous batching

Klasik batched çıkarım: en yavaş dizinin bitmesini bekle, sonra yeni bir batch başlat. Kısa yanıtlar erken bittiğinde GPU'yu israf eder.

Continuous batching (önce Orca'da gönderildi, şimdi vLLM, TensorRT-LLM, SGLang'de): eskiler bitince yeni istekleri batch'e takas et. Tipik sohbet workload'ları için 5–10× throughput kazancı.

### PagedAttention — sanal bellek olarak KV cache

vLLM'in başlık özelliği. KV cache 16 token'lık bloklarda allocate edilir; bir page table mantıksal pozisyonları fiziksel bloklara eşler. Paralel sample'lar (beam search, paralel örnekleme) arasında KV paylaşmana, prompt caching için prefix'leri hot-swap yapmana ve belleği defrag etmene izin verir. Naif contiguous allocation'a göre 4× throughput iyileştirmesi.

## İnşa Et

`code/main.py`'a bak. Şunları implement ediyoruz:

1. Naif bir `O(N²)` incremental decoder.
2. `O(N)` KV-cache'li bir decoder.
3. Flash Attention'ın running-max algoritmasını simüle eden tile'lı bir softmax.

### Adım 1: KV cache

```python
class KVCache:
    def __init__(self, n_layers, n_heads, d_head):
        self.K = [[[] for _ in range(n_heads)] for _ in range(n_layers)]
        self.V = [[[] for _ in range(n_heads)] for _ in range(n_layers)]

    def append(self, layer, head, k, v):
        self.K[layer][head].append(k)
        self.V[layer][head].append(v)

    def read(self, layer, head):
        return self.K[layer][head], self.V[layer][head]
```

Basit: katman başına, head başına listelerde token başına büyüyen K, V vektörleri tut.

### Adım 2: tile'lı softmax

```python
def tiled_softmax_dot(q, K, V, tile=4):
    """Running max/sum ile Flash-attention tarzı softmax(qK^T)V."""
    m = float("-inf")
    s = 0.0
    out = [0.0] * len(V[0])
    for start in range(0, len(K), tile):
        k_block = K[start:start + tile]
        v_block = V[start:start + tile]
        scores = [sum(qi * ki for qi, ki in zip(q, k)) for k in k_block]
        new_m = max(m, *scores)
        exp_old = math.exp(m - new_m) if m != float("-inf") else 0.0
        exp_new = [math.exp(sc - new_m) for sc in scores]
        s = s * exp_old + sum(exp_new)
        for j in range(len(out)):
            out[j] = out[j] * exp_old + sum(e * v[j] for e, v in zip(exp_new, v_block))
        m = new_m
    return [o / s for o in out]
```

Tek seferlik `softmax(qK) V` ile bit-aynı çıktı, ama herhangi bir anda çalışma seti `tile × d_head` blok, tam `N × d_head` değil.

### Adım 3: 100 token üretmede naif vs cache'li decoding'i karşılaştır

Attention operasyonlarını say. Naif: `O(N²)` = 5050. Cache'li: `O(N)` = 100. Kod ikisini de yazdırır.

## Kullan

```python
# HuggingFace transformers, decoder-only generate()'te KV cache'i otomatik etkinleştirir.
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    attn_implementation="flash_attention_2",  # Hopper ise FA3 kullan
    torch_dtype="bfloat16",
)
# generate() KV cache'i otomatik kullanır
```

vLLM production:

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 4 \
    --max-model-len 32768 \
    --enable-prefix-caching \
    --kv-cache-dtype fp8
```

İstekler arası prefix caching büyük bir 2026 kazancı — aynı system prompt, few-shot örnekler veya uzun context belgesi çağrılar arasında KV'yi yeniden kullanır. Tekrar eden tool prompt'lu agent workload'larında, prefix caching rutin olarak 5× throughput kazancı.

## Yayınla

`outputs/skill-inference-optimizer.md`'ye bak. Skill, yeni bir çıkarım dağıtımı için attention implementasyonu, KV cache stratejisi, quantization ve speculative decoding seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. Naif ve cache'li decoder'ların aynı çıktıyı ürettiğini doğrula; op-count farkını not et.
2. **Orta.** Prefix caching implement et: bir P prompt'u ve birkaç tamamlama verildiğinde, KV cache'i doldurmak için P üzerinde bir forward pass çalıştır, sonra tamamlama başına dalla. P'yi her biri için yeniden encode etmeye karşı hızlanmayı ölç.
3. **Zor.** Oyuncak bir PagedAttention implement et: free-list'li sabit 16 token'lık bloklarda KV cache. Bir dizi bittiğinde, bloklarını havuza geri ver. Değişken uzunluklarla 1.000 sohbet tamamlamasını simüle et. Contiguous allocation'a karşı bellek fragmentation'ı karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| KV cache | "Decoding'i hızlı yapan numara" | Her prefix token'ından saklanmış K ve V; yeni query'ler yeniden hesaplamak yerine onlara attention yapar. |
| HBM | "GPU ana belleği" | High Bandwidth Memory; H100'de 80 GB, B200'de 192 GB. ~3 TB/s bant genişliği. |
| SRAM | "Chip üzerinde bellek" | SM başına hızlı bellek, H100'de SM başına ~256 KB. ~30 TB/s bant genişliği. |
| Flash Attention | "Tile'lı attention kernel'i" | HBM'de N×N materyalize etmeden attention hesaplar. |
| Continuous batching | "Beklemesiz batching" | Biten dizileri dışarı, yenileri içeri takas et, batch'i boşaltmadan. |
| PagedAttention | "vLLM'in başlığı" | Page table'lı sabit bloklarda allocate edilmiş KV cache; fragmentation'ı eler. |
| Prefix caching | "Uzun prompt'ları yeniden kullan" | İstekler arasında paylaşılan prefix için KV cache; agent'lar için büyük maliyet kesintisi. |
| Speculative decoding | "Draft + doğrula" | Ucuz draft model token önerir; büyük model k token'ı tek pass'ta doğrular. |

## İleri Okuma

- [Dao et al. (2022). FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) — Flash 1.
- [Dao (2023). FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) — Flash 2.
- [Shah et al. (2024). FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) — Flash 3.
- [FlashAttention-4 release notes (Dao-AILab, 2026)](https://github.com/Dao-AILab/flash-attention) — Blackwell 5-stage pipeline ve software-exp2 numarası; bu dersin bahsettiği forward-only lansman uyarıları için repo README'sini oku.
- [Kwon et al. (2023). Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) — vLLM makalesi.
- [Leviathan et al. (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — spec decoding.
- [Li et al. (2024). EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — dersin atıfta bulunduğu entegre-draft yaklaşımı için EAGLE-1/2 makalesi.
- [Cai et al. (2024). Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — EAGLE ile birlikte atıfta bulunulan Medusa yaklaşımı.
- [vLLM docs — PagedAttention](https://docs.vllm.ai/en/latest/design/kernel/paged_attention.html) — 16 token'lık blok ve page-table tasarımında kanonik derinlik.
