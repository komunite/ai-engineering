# Positional Encoding — Sinusoidal, RoPE, ALiBi

> Attention permütasyon-değişmezdir. "The cat sat on the mat" ve "mat the on sat cat the" pozisyon sinyali olmadan aynı çıktıyı üretir. Üç algoritma bunu çözer — her biri "pozisyon"un ne anlama geldiğine farklı bahis koyar.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 02 (Self-Attention), Faz 7 · 03 (Multi-Head Attention)
**Süre:** ~45 dakika

## Sorun

Scaled dot-product attention sıra-körüdür. `softmax(Q K^T / √d) V` attention matrisi ikili benzerliklerden hesaplanır. `X`'in satırlarını karıştır, çıktının satırları aynı şekilde karışmış olarak gelsin. Attention'ın içinde hiçbir şey pozisyonu umursamaz.

Bu bag-of-words modelde bir bug değildir. Dil, kod, ses, video — sıranın anlam taşıdığı her şey için — ölümcüldür.

Çözüm pozisyonu bir şekilde embedding'lere enjekte etmektir. Üç dönem cevap:

1. **Absolute sinusoidal** (Vaswani 2017). Pozisyonun `sin/cos`'unu embedding'e ekle. Basit, öğrenilebilir-değil, eğitilmiş uzunlukların ötesine zayıf ekstrapolasyon yapar.
2. **RoPE — Rotary Position Embeddings** (Su 2021). Q ve K vektörlerini pozisyonla orantılı bir açıyla döndür. *Göreli* pozisyonu doğrudan nokta çarpımına kodlar. 2026'da baskın.
3. **ALiBi — Attention with Linear Biases** (Press 2022). Embedding'leri tamamen atla; uzaklığa dayalı olarak attention skorlarına head başına lineer bir ceza ekle. Mükemmel uzunluk ekstrapolasyonu.

2026 itibarıyla, esasen her frontier açık model RoPE kullanıyor: Llama 2/3/4, Qwen 2/3, Mistral, Mixtral, DeepSeek-V3, Kimi. Bir avuç uzun-context modeli ALiBi'yi veya onun modern varyantlarını kullanıyor. Absolute sinusoidal tarihseldir.

## Kavram

![Sinusoidal absolute vs RoPE rotasyonları vs ALiBi uzaklık bias'ı](../assets/positional-encoding.svg)

### Absolute sinusoidal

`(max_len, d_model)` şeklinde sabit bir `PE` matrisini önceden hesapla:

```
PE[pos, 2i]   = sin(pos / 10000^(2i / d_model))
PE[pos, 2i+1] = cos(pos / 10000^(2i / d_model))
```

Sonra attention'dan önce `X' = X + PE[:N]`. Her boyut farklı bir frekansta bir sinüzoidtir. Model, pozisyonu faz pattern'inden okumayı öğrenir. `max_len`'in ötesinde başarısız olur: 0–2047 pozisyonlarını gördüyse, hiçbir şey modele pozisyon 2048'de ne olacağını söylemedi.

### RoPE

Q ve K vektörlerini (embedding'leri değil) döndür. Bir boyut çifti `(2i, 2i+1)` için:

```
[q'_2i    ]   [ cos(pos·θ_i)  -sin(pos·θ_i) ] [q_2i   ]
[q'_2i+1  ] = [ sin(pos·θ_i)   cos(pos·θ_i) ] [q_2i+1 ]

θ_i = base^(-2i / d_head),  varsayılan base = 10000
```

Aynı rotasyonu pozisyon `pos_k` ile key'lere uygula. Nokta çarpımı `q'_m · k'_n` yalnız `(m - n)`'in bir fonksiyonu olur. Yani: **attention skoru yalnızca göreli uzaklığa bağlıdır**, rotasyon mutlak pozisyonlardan key'lendiği halde. Güzel numara.

RoPE'u uzatmak: `base`, yeniden eğitim olmadan daha uzun context'lere ekstrapolasyon yapmak için ölçeklenebilir (NTK-aware, YaRN, LongRoPE). Llama 3 bu yolla 8K'dan 128K context'e uzandı.

### ALiBi

Embedding numarasını atla. Attention skorlarını doğrudan bias'la:

```
attn_score[i, j] = (q_i · k_j) / √d  -  m_h · |i - j|
```

Burada `m_h` head'e özel bir eğim (örn. `1 / 2^(8·h/H)`). Daha yakın token'lar boost alır; uzak token'lar ceza alır. Eğitim zamanı maliyeti yok. Makale, uzunluk ekstrapolasyonunun sinusoidal'ı yendiğini ve RoPE'u orijinal eğitilmiş uzunluğunda eşleştirdiğini gösteriyor.

### 2026'da ne seçilmeli

| Varyant | Ekstrapolasyon | Eğitim maliyeti | Kullanan |
|---------|---------------|---------------|---------|
| Absolute sinusoidal | zayıf | bedava | orijinal transformer, erken BERT |
| Learned absolute | yok | minik | GPT-2, GPT-3 |
| RoPE | ölçeklemeyle iyi | bedava | Llama 2/3/4, Qwen 2/3, Mistral, DeepSeek-V3, Kimi |
| RoPE + YaRN | mükemmel | fine-tune aşaması | Qwen2-1M, Llama 3.1 128K |
| ALiBi | mükemmel | bedava | BLOOM, MPT, Baichuan |

RoPE kazandı çünkü mimariyi değiştirmeden attention'a yerleşiyor, göreli pozisyonu kodluyor ve `base` hyperparametresi uzun-context fine-tuning için temiz bir kontrol veriyor.

## İnşa Et

### Adım 1: sinusoidal encoding

`code/main.py`'a bak. 4 satırlık bir hesaplama:

```python
def sinusoidal(N, d):
    pe = [[0.0] * d for _ in range(N)]
    for pos in range(N):
        for i in range(d // 2):
            theta = pos / (10000 ** (2 * i / d))
            pe[pos][2 * i]     = math.sin(theta)
            pe[pos][2 * i + 1] = math.cos(theta)
    return pe
```

Bunu ilk attention katmanından önce embedding matrisine ekle.

### Adım 2: Q, K'ya uygulanan RoPE

RoPE Q ve K üzerinde yerinde çalışır. Her boyut çifti için:

```python
def apply_rope(x, pos, base=10000):
    d = len(x)
    out = list(x)
    for i in range(d // 2):
        theta = pos / (base ** (2 * i / d))
        c, s = math.cos(theta), math.sin(theta)
        a, b = x[2 * i], x[2 * i + 1]
        out[2 * i]     = a * c - b * s
        out[2 * i + 1] = a * s + b * c
    return out
```

Kritik: aynı fonksiyonu `m` pozisyonundaki Q'ya ve `n` pozisyonundaki K'ya uygula. Nokta çarpımları her koordinat çiftinde bir `cos((m-n)·θ_i)` faktörü alır. Attention göreli pozisyonu bedavaya öğrenir.

### Adım 3: ALiBi eğimleri ve bias

```python
def alibi_bias(n_heads, seq_len):
    # h = 1..n_heads için slope_h = 2 ** (-8 * h / n_heads)
    slopes = [2 ** (-8 * (h + 1) / n_heads) for h in range(n_heads)]
    bias = []
    for m in slopes:
        row = [[-m * abs(i - j) for j in range(seq_len)] for i in range(seq_len)]
        bias.append(row)
    return bias  # softmax'tan önce attention skorlarına ekle
```

`bias[h]`'yi head `h`'in `(seq_len, seq_len)` attention skor matrisine ekle, sonra softmax.

### Adım 4: RoPE'un göreli-uzaklık özelliğini doğrula

İki rastgele vektör `a, b` al. `(pos_a, pos_b)` ile döndür. Sonra `(pos_a + k, pos_b + k)` ile. Her iki nokta çarpımı floating-point hatası içinde eşleşmeli. Bu özellik RoPE'un tüm amacıdır — mutlak offset'e değişmezdir, yalnızca göreli boşluk önemlidir.

## Kullan

PyTorch 2.5+, `torch.nn.functional`'da RoPE araçları gönderir. Production kodun çoğu, RoPE'un attention kernel'inin içinde uygulandığı `flash_attn` veya `xformers` kullanır.

```python
from transformers import AutoModel
model = AutoModel.from_pretrained("meta-llama/Llama-3.2-3B")
# model.config.rope_scaling → {"type": "yarn", "factor": 32.0, "original_max_position_embeddings": 8192}
```

**2026'da uzun-context numaraları:**

- **NTK-aware interpolation.** 4K'dan 16K+'a uzatırken `base`'i `base * (scale_factor)^(d/(d-2))`'e yeniden ölçekle.
- **YaRN.** Uzun context'lerde attention entropisini koruyan daha akıllı interpolasyon. Llama 3.1 128K bunu kullanıyor.
- **LongRoPE.** Boyut başına ölçek faktörleri seçmek için evrimsel arama kullanan Microsoft'un 2024 metodu. Phi-3-Long bunu kullanıyor.
- **Position interpolation + fine-tuning.** Sadece pozisyonları uzatma faktörüyle daralt ve 1–5B token için fine-tune et. Şaşırtıcı derecede etkili.

## Yayınla

`outputs/skill-positional-encoding-picker.md`'ye bak. Skill, hedef context length, ekstrapolasyon ihtiyaçları ve eğitim bütçesi verilen yeni bir model için bir encoding stratejisi seçer.

## Alıştırmalar

1. **Kolay.** `max_len=512, d=128` için sinusoidal `PE` matrisini bir heatmap olarak çiz. "Boyut indeksi büyüdükçe çizgiler genişler" pattern'ini doğrula.
2. **Orta.** NTK-aware RoPE ölçeklemesini implement et. Uzunluk 256'da küçük bir LM eğit, sonra ölçeklemeli ve ölçeklemesiz uzunluk 1024'te test et. Perplexity'i ölç.
3. **Zor.** ALiBi ve RoPE'u aynı attention modülünde implement et. Uzunluk 512'lik dizilerle bir copy görevinde 4-katmanlı bir transformer eğit. Test zamanında 2048'e ekstrapole et. Bozulmayı karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Positional encoding | "Attention'a sırayı söyler" | Embedding'lere veya attention'a eklenen pozisyonu kodlayan herhangi bir sinyal. |
| Sinusoidal | "Orijinal olan" | Embedding'lere eklenen geometrik frekanslarda `sin/cos`; ekstrapole etmez. |
| RoPE | "Rotary embeddings" | Q, K'yı pozisyona bağlı açıyla döndür; nokta çarpımı göreli uzaklığı kodlar. |
| ALiBi | "Lineer bias numarası" | Attention skorlarına `-m·|i-j|` ekle; embedding'e ihtiyaç yok, harika ekstrapolasyon. |
| base | "RoPE'un düğmesi" | RoPE'taki frekans ölçekleyicisi; çıkarımda context'i uzatmak için arttır. |
| NTK-aware | "Bir RoPE ölçekleme numarası" | Context genişlediğinde yüksek-frekans boyutlarının sıkışmaması için `base`'i yeniden ölçekle. |
| YaRN | "Şık olan" | Attention entropisini koruyan boyut başına interpolasyon+ekstrapolasyon. |
| Ekstrapolasyon | "Eğitilmiş uzunluğun ötesinde çalışır" | Pozisyon şeması eğitimde görülen `max_len`'in ötesinde doğru çıktı verebilir mi? |

## İleri Okuma

- [Vaswani et al. (2017). Attention Is All You Need §3.5](https://arxiv.org/abs/1706.03762) — orijinal sinusoidal.
- [Su et al. (2021). RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864) — RoPE makalesi.
- [Press, Smith, Lewis (2021). Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation](https://arxiv.org/abs/2108.12409) — ALiBi.
- [Peng et al. (2023). YaRN: Efficient Context Window Extension of Large Language Models](https://arxiv.org/abs/2309.00071) — state of the art RoPE ölçeklemesi.
- [Chen et al. (2023). Extending Context Window of Large Language Models via Positional Interpolation](https://arxiv.org/abs/2306.15595) — Meta'nın Llama 2 uzun-context makalesi.
- [Ding et al. (2024). LongRoPE: Extending LLM Context Window Beyond 2 Million Tokens](https://arxiv.org/abs/2402.13753) — Phi-3-Long tarafından kullanılan ve Kullan bölümünde atıfta bulunulan Microsoft metodu.
- [HuggingFace Transformers — `modeling_rope_utils.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/modeling_rope_utils.py) — her RoPE ölçekleme şemasının production sınıfı implementasyonları (default, linear, dynamic, YaRN, LongRoPE, Llama-3).
