# Gradient Checkpointing ve Activation Recomputation

> Backprop her ara activation'ı tutar. 70B parametre ve 128K context'te bu rank başına 3 TB activation. Checkpointing FLOP'ları memory için takas eder: kaydetmek yerine yeniden hesapla. Soru hangi segmentlerin düşürüleceği ve cevap "hepsi" değil.

**Tür:** Yapım
**Diller:** Python (numpy ile, opsiyonel torch)
**Ön koşullar:** Faz 10 Ders 04 (Mini-GPT Pretraining), Faz 10 Ders 05 (Scaling & Distributed)
**Süre:** ~70 dakika

## Sorun

Bir transformer eğitirken, her katman için, backward'da differansiyate edilen her op'un input'larını saklarsın: attention input'ları, Q/K/V projeksiyonları, softmax output'u, FFN input'ları, norm output'ları ve residual stream. Hidden size `d`, sequence uzunluğu `L`, batch `B` olan bir katman için, bu katman başına `12 * B * L * d` float mertebesindedir.

`d=8192, L=8192, B=1` için, bu BF16'da katman başına 800 MB. 64-katmanlı bir model 51 GB activation'dır — ve bu microbatch boyutuyla çarpmadan, attention-softmax ara ürünleri (head başına `L^2`) eklemeden ve tensor-parallel kısmi kopyaları hesaplamadan önce.

İki taraflı fatura: BF16 ağırlıkları artı optimizer state 80GB'a sığabilir, ama activation'lar seni öteye iter. Gradient checkpointing (aka activation recomputation) standart düzeltmedir. Activation'ların çoğunu düşür; geri almak için backward sırasında forward'ı yeniden yap. Maliyet: ekstra FLOP. Fayda: memory checkpoint segmentlerinin toplam katmanlara oranıyla düşer.

Naif yapıldığında, checkpointing adım başına kabaca %33 daha fazla forward-pass FLOP maliyetlidir. İyi yapıldığında — Korthikanti et al.'in "smart selection"u başına selective checkpointing — %5 altı FLOP overhead için 5x memory tasarruf edersin. Ve FP8 matmul, FSDP offload ve expert-parallel MoE ile bu gerçekten önemli: ne memory'i ne de israf edilen compute'u karşılayamazsın.

## Kavram

### Backward Aslında Neye İhtiyaç Duyar

`output = layer(input)`. Backward `grad_input` ve `grad_params` ister. Onları hesaplamak için:

- `input` (lineer katmanlar için `grad_params = input.T @ grad_output`'u hesaplamak için)
- bazı activation türev ara ürünleri (ReLU/GELU/softmax'in türevi activation değerine bağlıdır)

Forward pass bunları otomatik olarak autograd graph'ında saklar. Her `tensor.retain_grad()` ve input'una ihtiyaç duyan her op bir referans tutar.

### Naif Full Checkpointing

Ağı `N` segment'e böl. Forward sırasında, sadece her segment'in *input*'unu sakla. Backward ara ürünlere ihtiyaç duyduğunda, segment'in forward pass'ını ara ürünleri materialize etmek için yeniden çalıştır, sonra differansiyate et.

Örnek: 32-katmanlı transformer her biri 1 katmanlı 32 segment'e bölünmüş.

- Memory: 32 katman-input (küçük) vs 32 * (katman başına activation hacmi) (devasa).
- Ekstra compute: segment başına 1 ekstra forward, yani toplam ~%33 daha fazla forward FLOP (backward 2x forward olduğu için, tam adım 1 + 2 = 3 yerine 1 + 1 + 2 = 4 birim olur).

Bu orijinal Chen et al. 2016 reçetesidir: memory ve compute'u dengelemek için her `sqrt(L)` katmanda bir checkpoint. L=64 için, bu 8 checkpoint.

### Selective Checkpointing (Korthikanti 2022)

Tüm activation'lar aynı maliyetli değildir. Attention softmax output'u `B*L*L*heads`'tir ve sequence uzunluğuyla *kuadratik* büyür. FFN hidden activation'ı `B*L*4d`'dir ve lineer büyür. Uzun sequence'ler için softmax baskındır.

Selective checkpointing saklaması ucuz activation'ları (lineer projeksiyonlar, residual'ler) tutar ve sadece pahalı olanları (attention) yeniden hesaplar. Yeniden hesaplamak için minimal FLOP ödersin ama O(L^2) memory'yi tasarruf edersin.

Megatron-Core bunu "selective" activation recomputation olarak implement eder. Çoğu 2024+ frontier eğitim koşusunda kullanılır.

### Offload

Yeniden hesaplamaya alternatif: activation'ları forward ve backward arasında CPU RAM'e gönder. PCIe bandwidth gerektirir; boş bandwidth rematerialization maliyetini aştığında faydalıdır. Karışık stratejiler yaygındır: bazı katmanları checkpoint et, diğerlerini offload et.

FSDP2 offload'u birinci-sınıf bir seçenek olarak yayınlar. Offload GPU memory'de darboğaz olduğunda ama CPU-GPU transferinde headroom olduğunda parlar.

### Recompute Maliyet Modeli

`L` katmanın her `k`'sında naif checkpointing ile adım başına FLOP:

```
flops_fwd_normal = L * f_layer
flops_bwd_normal = 2 * L * f_layer
flops_total_normal = 3 * L * f_layer

flops_fwd_ckpt = L * f_layer
flops_recompute = L * f_layer  # segment'teki katman başına bir ekstra forward
flops_bwd_ckpt = 2 * L * f_layer
flops_total_ckpt = 4 * L * f_layer
overhead = 4 / 3 - 1 = 0.33 = %33
```

Selective checkpointing ile sadece attention kernel'i yeniden hesaplarsın, tüm katmanı değil:

```
flops_recompute_selective = L * f_attention ~= L * f_layer * 0.15
overhead_selective = (3 + 0.15) / 3 - 1 = 0.05 = %5
```

### Memory Tasarrufu Modeli

Katman başına activation hacmi: `A`. `L` katman için, toplam activation memory'si: `L * A`.

Full checkpoint (segment boyutu 1): sadece `L * input_volume` sakla (~`L * 1/10 A` standart bir transformer için). ~`9 * L * A * 1/10` tasarruf eder.

Her `k` katmanda checkpoint: `L/k * A` artı aktif segment içinde `k-1` katman değerinde sakla.

`k = sqrt(L)`'de, memory ve recompute maliyeti her ikisi de `sqrt(L)` ile ölçeklenir — uniform-maliyetli katmanlar için optimal tradeoff.

### Ne Zaman Checkpoint Etmeme

- Bir pipeline aşamasının uçuştaki en içteki katmanları. Yine de bitirmek zorunda.
- Aşamanın compute'unu baskıda eden ilk ve son katmanlar (transformer'larda nadir).
- Zaten FlashAttention kullanan attention kernel'leri — Flash softmax'i hızlı yeniden hesaplar, dolayısıyla ek katman-seviyesi checkpointing üstüne az ekler.

### Implementasyon Desenleri

1. **Function wrapper:** bir segment'i `torch.utils.checkpoint.checkpoint(fn, input)` içine sar. PyTorch sadece `input`'u saklar, backward'da diğer her şeyi yeniden hesaplar.

2. **Decorator-tabanlı:** katmanları checkpointable olarak etiketle; trainer config zamanında hangi segmentlerin sarılacağına karar verir.

3. **Manual explicit recompute:** backward pass'ı kendin yaz, saklanmış input ile forward'ı duplicate eden custom bir `recompute_forward` çağır.

Üçü de aynı fonksiyonel sonucu verir. Wrapper'lar standart idiom.

### TP / PP / FP8 ile Etkileşim

- **Tensor parallel:** checkpoint input'ları recompute'ta gather veya rescatter edilmeli; iletişim maliyetini halle.
- **Pipeline parallel:** tipik desen, ters-sıralı microbatch'ler activation memory'sini yeniden kullanabilsin diye her pipeline-aşamasının forward'ını checkpoint etmektir.
- **FP8 recompute:** recompute sırasında güncellenen amax history'leri orijinal forward'ınkiyle eşleşmeli, yoksa FP8 scale drift eder. Çoğu framework scale'i snapshot eder.

## İnşa Et

### Adım 1: Segmentli Bir Oyuncak Model

```python
import numpy as np


def linear_forward(x, w, b):
    return x @ w + b


def relu(x):
    return np.maximum(x, 0)


def layer_forward(x, w1, b1, w2, b2):
    h = relu(linear_forward(x, w1, b1))
    return linear_forward(h, w2, b2)


def model_forward(x, params):
    activations = [x]
    h = x
    for w1, b1, w2, b2 in params:
        h = layer_forward(h, w1, b1, w2, b2)
        activations.append(h)
    return h, activations
```

### Adım 2: Tüm Activation'lara İhtiyaç Duyan Naif Backward

```python
def model_backward(grad_output, activations, params):
    grads = [None] * len(params)
    g = grad_output
    for i in range(len(params) - 1, -1, -1):
        w1, b1, w2, b2 = params[i]
        x_in = activations[i]
        h_pre = linear_forward(x_in, w1, b1)
        h = relu(h_pre)
        gh = g @ w2.T
        gw2 = h.T @ g
        gb2 = g.sum(axis=0)
        g_pre = gh * (h_pre > 0)
        gx = g_pre @ w1.T
        gw1 = x_in.T @ g_pre
        gb1 = g_pre.sum(axis=0)
        grads[i] = (gw1, gb1, gw2, gb2)
        g = gx
    return g, grads
```

### Adım 3: Her k'da Checkpoint Memory

```python
def model_forward_checkpointed(x, params, k=4):
    saved_inputs = [x]
    h = x
    for i, (w1, b1, w2, b2) in enumerate(params):
        h = layer_forward(h, w1, b1, w2, b2)
        if (i + 1) % k == 0:
            saved_inputs.append(h)
    return h, saved_inputs


def model_backward_checkpointed(grad_output, saved_inputs, params, k=4):
    grads = [None] * len(params)
    g = grad_output
    segments = [(j * k, min((j + 1) * k, len(params))) for j in range(len(saved_inputs))]
    for seg_idx in range(len(saved_inputs) - 1, -1, -1):
        start, end = segments[seg_idx]
        if start >= end:
            continue
        x_in = saved_inputs[seg_idx]
        _, seg_acts = model_forward(x_in, params[start:end])
        g, seg_grads = model_backward(g, seg_acts, params[start:end])
        for j, gr in enumerate(seg_grads):
            grads[start + j] = gr
    return g, grads
```

### Adım 4: Maliyet Modeli

```python
def checkpoint_cost(n_layers, segment_size, flops_per_layer=1.0):
    fwd = n_layers * flops_per_layer
    recompute = n_layers * flops_per_layer
    bwd = 2 * n_layers * flops_per_layer
    return {
        "fwd": fwd,
        "recompute": recompute,
        "bwd": bwd,
        "total": fwd + recompute + bwd,
        "overhead_vs_no_ckpt": (fwd + recompute + bwd) / (fwd + bwd) - 1.0,
    }


def selective_checkpoint_cost(n_layers, attention_fraction=0.15,
                              flops_per_layer=1.0):
    fwd = n_layers * flops_per_layer
    recompute = n_layers * attention_fraction * flops_per_layer
    bwd = 2 * n_layers * flops_per_layer
    return {
        "fwd": fwd,
        "recompute": recompute,
        "bwd": bwd,
        "total": fwd + recompute + bwd,
        "overhead_vs_no_ckpt": (fwd + recompute + bwd) / (fwd + bwd) - 1.0,
    }
```

### Adım 5: Memory Tahminci

```python
def activation_memory_mb(n_layers, hidden=8192, seq=8192,
                        batch=1, bytes_per_value=2):
    per_layer = 12 * batch * seq * hidden * bytes_per_value
    return n_layers * per_layer / 1e6


def memory_after_checkpoint(n_layers, segment_size, hidden=8192,
                           seq=8192, batch=1, bytes_per_value=2):
    n_seg = max(1, n_layers // segment_size)
    saved = (n_seg + segment_size) * 1 * batch * seq * hidden * bytes_per_value
    return saved / 1e6
```

### Adım 6: Optimal Segment Boyutu

```python
def optimal_segment(n_layers):
    return int(round(np.sqrt(n_layers)))
```

### Adım 7: Selective Checkpoint Kararı

```python
def should_recompute(layer_type, activation_bytes, recompute_flops_ratio):
    if layer_type == "attention" and activation_bytes > 100 * 1e6:
        return True
    if layer_type == "ffn" and activation_bytes > 500 * 1e6:
        return recompute_flops_ratio < 0.1
    return False
```

## Kullan

- **torch.utils.checkpoint**: `from torch.utils.checkpoint import checkpoint` -- PyTorch'taki standart wrapper. Bir fonksiyonu sarar; sadece input'ları saklar, backward'da yeniden hesaplar.
- **Megatron-Core activation recomputation**: `selective`, `full` ve `block` modlarını destekler. 2024+ frontier eğitiminde standart.
- **FSDP2 offload**: FSDP2'de `offload_policy` ile `module.to_empty(device="cpu")` activation'ları yeniden hesaplamak yerine CPU'ya shard eder.
- **DeepSpeed ZeRO-Offload**: optimizer state'ler ve activation'lar için CPU offload, checkpointing'i tamamlar.

## Yayınla

Bu ders `outputs/prompt-activation-recompute-policy.md` üretir — model config'ini (katmanlar, hidden, seq, batch) ve mevcut GPU memory'i alan ve katman başına recompute policy (none / selective / full / offload) yayan bir prompt.

## Alıştırmalar

1. Doğruluğu doğrula. `model_forward` + `model_backward` (full activation'lar) vs `model_forward_checkpointed` + `model_backward_checkpointed` (segment'ler) çalıştır. Parametre gradient'leri machine precision'a kadar özdeş olmalı.

2. `k` segment boyutunu 1'den `L`'ye sweep et. FLOP overhead ve memory çiz. Eğrinin dizini bul.

3. Selective checkpointing implement et: attention-modülü input'unu sakla ama ara ürünleri saklama. Seq=8192'de 32-katmanlı model için full-layer checkpointing'e karşı FLOP overhead'i ölç.

4. Offload ekle. Segment input'larını simüle edilmiş bir "CPU buffer"a (ayrı bir liste) kaydet. "PCIe bandwidth"i byte/zaman olarak ölç ve offload ile recompute arasındaki breakeven noktasını bul.

5. `torch.utils.checkpoint` ile ve olmadan gerçek bir PyTorch transformer benchmark et. Memory (`torch.cuda.max_memory_allocated` yoluyla) ve adım zamanını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| Gradient checkpointing | "Forward'ı yeniden yaparak memory tasarruf et" | Sadece segment input'larını sakla; gradient-destek tensorlarını almak için backward sırasında ara ürünleri yeniden hesapla |
| Activation recomputation | "Checkpointing ile aynı" | Aynı tekniğin HPC-tatlı adı |
| Segment size (k) | "Checkpoint başına kaç katman" | Ara ürünleri düşürülen ve birlikte rematerialize edilen katman sayısı |
| Selective checkpointing | "Korthikanti'nin hilesi" | Sadece saklaması pahalı activation'ları (attention softmax) yeniden hesapla; ucuz olanları tut |
| Full checkpointing | "Naif versiyon" | Her segment'te her katmanın ara ürünlerini yeniden hesapla |
| Block checkpointing | "Coarse-grained" | Tüm transformer bloklarını checkpoint et; en büyük granülerlik |
| FLOP overhead | "Compute vergisi" | Adım başına ekstra FLOP = (recompute FLOP) / (fwd + bwd FLOP); naif %33, selective %5 |
| Activation offload | "CPU'ya gönder" | Activation'ları forward->backward boyunca CPU RAM'e taşı; recompute'a alternatif |
| sqrt-L rule | "Klasik optimum" | Uniform-maliyetli katmanlar için, optimal checkpoint aralığı sqrt(L) katman |
| Attention-softmax volume | "O(L^2) problemi" | L^2 * heads * batch float; uzun context'lerde activation memory'sini baskıda eder |

## İleri Okuma

- [Chen et al., 2016 -- "Training Deep Nets with Sublinear Memory Cost"](https://arxiv.org/abs/1604.06174) -- gradient checkpointing'i formalize eden orijinal makale
- [Korthikanti et al., 2022 -- "Reducing Activation Recomputation in Large Transformer Models"](https://arxiv.org/abs/2205.05198) -- selective activation recomputation ve resmi maliyet analizi
- [Pudipeddi et al., 2020 -- "Training Large Neural Networks with Constant Memory using a New Execution Algorithm"](https://arxiv.org/abs/2002.05645) -- reverse-mode rematerialization yoluyla alternatif sabit-memory yaklaşımı
- [Ren et al., 2021 -- "ZeRO-Offload: Democratizing Billion-Scale Model Training"](https://arxiv.org/abs/2101.06840) -- ölçekte activation offload
- [PyTorch torch.utils.checkpoint docs](https://pytorch.org/docs/stable/checkpoint.html) -- standart API
- [Megatron-Core activation recomputation documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/features/memory_optimizations.html) -- selective, full ve block modları
