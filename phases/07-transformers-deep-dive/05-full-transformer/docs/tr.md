# Tam Transformer — Encoder + Decoder

> Attention yıldız. Diğer her şey — residual'lar, normalization, feed-forward, cross-attention — onu derinlemesine yığmana izin veren iskele.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 02 (Self-Attention), Faz 7 · 03 (Multi-Head Attention), Faz 7 · 04 (Positional Encoding)
**Süre:** ~75 dakika

## Sorun

Tek bir attention katmanı bir özellik çıkarıcıdır, model değil. Katman başına tek bir matmul dil için yeterli kapasite değil. Derinliğe ihtiyacın var — ve derinlik doğru tesisat olmadan kırılır.

2017 Vaswani makalesi, bir attention katmanını yığılabilir bir bloğa çeviren altı tasarım kararını paketledi. O zamandan beri her transformer — encoder-only (BERT), decoder-only (GPT), encoder-decoder (T5) — aynı iskeleti miras alır. 2026'da bloklar rafine edildi (RMSNorm, SwiGLU, pre-norm, RoPE) ama iskelet aynı.

Bu ders iskelet hakkında. Sonraki dersler onu özelleştiriyor — encoder'lar için 06, decoder'lar için 07, encoder-decoder için 08.

## Kavram

![Encoder ve decoder blok iç yapıları, bağlı](../assets/full-transformer.svg)

### Altı parça

1. **Embedding + pozisyon sinyali.** Token'lar → vektörler. Pozisyon RoPE (modern) veya sinusoidal (klasik) ile enjekte edilir.
2. **Self-attention.** Her pozisyon diğer her pozisyona attention yapar. Decoder'larda mask'lenir.
3. **Feed-forward network (FFN).** Pozisyon bazında iki katmanlı MLP: `W_2 · activation(W_1 · x)`. Varsayılan genişleme oranı 4×.
4. **Residual connection.** `x + sublayer(x)`. Bu olmadan, gradient'lar ~6 katmandan sonra kaybolur.
5. **Layer normalization.** `LayerNorm` veya `RMSNorm` (modern). Residual akışını stabilize eder.
6. **Cross-attention (yalnız decoder).** Query'ler decoder'dan gelir, key'ler ve value'lar encoder çıktısından.

### Encoder bloğu (BERT, T5 encoder tarafından kullanılır)

```
x → LN → MHA(self) → + → LN → FFN → + → out
                     ^              ^
                     |              |
                     └── residual ──┘
```

Encoder çift yönlüdür. Mask'leme yok. Tüm pozisyonlar tüm pozisyonları görür.

### Decoder bloğu (GPT, T5 decoder tarafından kullanılır)

```
x → LN → MHA(masked self) → + → LN → MHA(encoder'a cross) → + → LN → FFN → + → out
```

Decoder'ın blok başına üç alt katmanı vardır. Ortadaki — cross-attention — bilginin encoder'dan decoder'a aktığı tek yerdir. Saf decoder-only mimaride (GPT), cross-attention atlanır ve elinde sadece mask'li self-attention + FFN olur.

### Pre-norm vs post-norm

Orijinal makale: `x + sublayer(LN(x))` vs `LN(x + sublayer(x))`. Post-norm 2019 civarında gözden düştü — dikkatli warmup olmadan derinlemesine eğitmek daha zor. Pre-norm (alt katmandan *önce* `LN`) 2026 varsayılanıdır: Llama, Qwen, GPT-3+, Mistral'ın hepsi kullanır.

### 2026 modernleştirilmiş blok

Vaswani 2017 LayerNorm + ReLU gönderdi. Modern yığınlar her ikisini de değiştirdi. Production blokları gerçekte nasıl görünüyor:

| Bileşen | 2017 | 2026 |
|-----------|------|------|
| Normalization | LayerNorm | RMSNorm |
| FFN activation | ReLU | SwiGLU |
| FFN genişleme | 4× | 2.6× (SwiGLU üç matris kullanır, toplam parametreler eşleşir) |
| Pozisyon | Sinusoidal absolute | RoPE |
| Attention | Full MHA | GQA (veya MLA) |
| Bias terimleri | Var | Yok |

RMSNorm, LayerNorm'un mean-centering'ini düşürür (bir çıkarma daha az), bu hesaplama tasarrufu sağlar ve ampirik olarak en az o kadar stabildir. SwiGLU (`Swish(W1 x) ⊙ W3 x`) Llama, PaLM ve Qwen makalelerinde ReLU/GELU FFN'i tutarlı şekilde ~0.5 puan ppl ile geçer.

### Parametre sayısı

`d_model = d` ve FFN genişlemesi `r` olan bir blok için:

- MHA: `4 · d²` (Q, K, V, O projeksiyonları)
- FFN (SwiGLU): `3 · d · (r · d)` ≈ `3rd²`
- Norm'lar: önemsiz

`d = 4096, r = 2.6, layers = 32`'de (kabaca Llama 3 8B), toplam: `32 · (4·4096² + 3·2.6·4096²) ≈ 32 · (16 + 32) M = ~katman başına 1.5B parametre × 32 ≈ 7B` (artı embedding'ler ve head). Yayınlanan sayılarla eşleşir.

## İnşa Et

### Adım 1: yapı blokları

Ders 03'teki minik `Matrix` sınıfını kullanarak (bağımsızlık için bu dosyaya kopyalandı):

- `layer_norm(x, eps=1e-5)` — mean'i çıkar, std'ye böl.
- `rms_norm(x, eps=1e-6)` — RMS'ye böl. Mean çıkarımı yok.
- `gelu(x)` ve `silu(x) * W3 x` (SwiGLU).
- `ffn_swiglu(x, W1, W2, W3)`.
- `encoder_block(x, params)` ve `decoder_block(x, enc_out, params)`.

Tam tesisat için `code/main.py`'a bak.

### Adım 2: 2 katmanlı bir encoder ve 2 katmanlı bir decoder bağla

Onları yığ. Encoder çıktısını her decoder cross-attention'a geçir. Çıktı projeksiyonundan önce son bir LN ekle.

```python
def encode(tokens, params):
    x = embed(tokens, params.emb) + sinusoidal(len(tokens), params.d)
    for block in params.encoder_blocks:
        x = encoder_block(x, block)
    return x

def decode(target_tokens, encoder_out, params):
    x = embed(target_tokens, params.emb) + sinusoidal(len(target_tokens), params.d)
    for block in params.decoder_blocks:
        x = decoder_block(x, encoder_out, block)
    return x
```

### Adım 3: oyuncak bir örnekte forward çalıştır

6 token'lık bir kaynağı ve 5 token'lık bir hedefi içinden geçir. Çıktı şeklinin `(5, vocab)` olduğunu doğrula. Eğitim yok — bu ders mimari hakkında, loss hakkında değil.

### Adım 4: RMSNorm + SwiGLU ile değiştir

LayerNorm ve ReLU-FFN'i RMSNorm ve SwiGLU ile değiştir. Şekillerin hâlâ eşleştiğini doğrula. Bu bir fonksiyon ikamesiyle 2026 modernleştirmesidir.

## Kullan

PyTorch/TF referans implementasyonları: `nn.TransformerEncoderLayer`, `nn.TransformerDecoderLayer`. Ancak 2026'daki production kodun çoğu kendi bloğunu yazar çünkü:

- Flash Attention `nn.MultiheadAttention` üzerinden değil, attention'ın içinde çağrılır.
- GQA / MLA stdlib referansında yok.
- RoPE, RMSNorm, SwiGLU PyTorch varsayılanları değil.

HF `transformers` okumalısın temiz referans bloklarına sahip: `modeling_llama.py` kanonik 2026 decoder-only bloğudur. ~500 satır ve bir kere baştan sona gezmeye değer.

**Encoder vs decoder vs encoder-decoder — ne zaman seçilir:**

| İhtiyaç | Seç | Örnek |
|------|------|---------|
| Sınıflandırma, embedding, metin üzerinde QA | Encoder-only | BERT, DeBERTa, ModernBERT |
| Metin üretimi, sohbet, kod, akıl yürütme | Decoder-only | GPT, Llama, Claude, Qwen |
| Yapılandırılmış input → yapılandırılmış output (çeviri, özetleme) | Encoder-decoder | T5, BART, Whisper |

Decoder-only dili kazandı çünkü en temiz şekilde ölçeklenir ve hem anlama hem üretmeyi ele alır. Encoder-decoder, input net bir "kaynak dizi" kimliğine sahip olduğunda hâlâ en iyisidir (çeviri, konuşma tanıma, yapılandırılmış görevler).

## Yayınla

`outputs/skill-transformer-block-reviewer.md`'ye bak. Skill, yeni bir transformer blok implementasyonunu 2026 varsayılanlarına karşı inceler ve eksik parçaları (pre-norm, RoPE, RMSNorm, GQA, FFN genişleme oranı) flag'ler.

## Alıştırmalar

1. **Kolay.** `d_model=512, n_heads=8, ffn_expansion=4, swiglu=True`'da encoder_block'undaki parametreleri say. Bloğu implement edip `sum(p.numel() for p in block.parameters())` kullanarak doğrula.
2. **Orta.** Post-norm'dan pre-norm'a geç. Her ikisini de initialize et ve rastgele input'ta 12 yığılmış katmandan sonra aktivasyon norm'unu ölç. Post-norm'un aktivasyonları patlamalı; pre-norm'un sınırlı kalmalı.
3. **Zor.** Oyuncak bir copy görevinde (ters çevrilmiş `x`'i kopyala) 4 katmanlı bir encoder-decoder implement et. 100 adım eğit. Loss'u rapor et. RMSNorm + SwiGLU + RoPE ile değiştir — loss düşer mi?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Blok | "Bir transformer katmanı" | Residual connection'larla sarılmış norm + attention + norm + FFN yığını. |
| Residual | "Atlama bağlantısı" | `x + f(x)` çıktısı; derin yığınlar boyunca gradient akışını sağlar. |
| Pre-norm | "Önce normalize et, sonra değil" | Modern: `x + sublayer(LN(x))`. Warmup jimnastiği olmadan daha derin eğitir. |
| RMSNorm | "Mean'siz LayerNorm" | RMS'ye böl; bir op daha az, aynı ampirik kararlılık. |
| SwiGLU | "Herkesin geçtiği FFN" | `Swish(W1 x) ⊙ W3 x → W2`. LM ppl'de ReLU/GELU'yu yener. |
| Cross-attention | "Decoder encoder'ı nasıl görür" | Q decoder'dan, K/V encoder çıktılarından gelen MHA. |
| FFN genişleme | "Ortadaki MLP ne kadar geniş" | Hidden-size'ın d_model'a oranı, genelde 4 (LayerNorm) veya 2.6 (SwiGLU). |
| Bias-free | "+b terimlerini düşür" | Modern yığınlar linear katmanlarda bias'ları atlar; ufak ppl iyileşmesi, daha küçük model. |

## İleri Okuma

- [Vaswani et al. (2017). Attention Is All You Need](https://arxiv.org/abs/1706.03762) — orijinal blok spec.
- [Xiong et al. (2020). On Layer Normalization in the Transformer Architecture](https://arxiv.org/abs/2002.04745) — pre-norm'un post-norm'u derinlemesine neden yendiği.
- [Zhang, Sennrich (2019). Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467) — RMSNorm.
- [Shazeer (2020). GLU Variants Improve Transformer](https://arxiv.org/abs/2002.05202) — SwiGLU makalesi.
- [HuggingFace `modeling_llama.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py) — kanonik 2026 decoder-only bloğu.
