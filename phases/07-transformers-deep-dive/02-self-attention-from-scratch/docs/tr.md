# Sıfırdan Self-Attention

> Attention, her kelimenin "kim benim için önemli?" diye sorduğu ve cevabı öğrendiği bir lookup tablosudur.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 (Deep Learning Core), Faz 5 Ders 10 (Sequence-to-Sequence)
**Süre:** ~90 dakika

## Öğrenme Hedefleri

- Sıfırdan, yalnızca NumPy ile scaled dot-product self-attention'ı implement et; query/key/value projeksiyonları ve softmax-ağırlıklı toplam dahil
- Head'leri bölen, paralel attention hesaplayan ve sonuçları birleştiren bir multi-head attention katmanı kur
- Attention matrisinin token ilişkilerini nasıl yakaladığını izle ve sqrt(d_k) ile ölçeklemenin softmax doygunluğunu neden önlediğini açıkla
- Çift yönlü attention'ı autoregressive (decoder tarzı) attention'a çevirmek için causal mask uygula

## Sorun

RNN'ler dizileri teker teker token işler. Token 50'ye ulaştığında, token 1'den gelen bilgi 50 sıkıştırma adımından sıkılıp geçmiştir. Uzun-mesafe bağımlılıkları sabit boyutlu bir hidden state'e ezilir — hiç bir miktar LSTM gating'in tam olarak çözmediği bir darboğaz.

2014 Bahdanau attention makalesi çözümü gösterdi: decoder'ın geriye, her encoder pozisyonuna bakmasına ve mevcut adım için hangilerinin önemli olduğuna karar vermesine izin ver. Ama hâlâ bir RNN'in üstüne cıvatalanmıştı. 2017 "Attention Is All You Need" makalesi daha keskin bir soru sordu: ya attention *tek* mekanizma olsa? Recurrence yok. Convolution yok. Sadece attention.

Self-attention, bir dizideki her pozisyonun tek bir paralel adımda diğer her pozisyona attention yapmasına izin verir. Transformer'ları hızlı, ölçeklenebilir ve baskın yapan şey budur.

## Kavram

### Veritabanı Lookup Analojisi

Attention'ı yumuşak bir veritabanı lookup'ı olarak düşün:

```
Geleneksel veritabanı:
  Query: "Fransa'nın başkenti"  -->  birebir eşleşme  -->  "Paris"

Attention:
  Query: "Fransa'nın başkenti"  -->  TÜM key'lere benzerlik  -->  TÜM value'ların ağırlıklı karışımı
```

Her token üç vektör üretir:
- **Query (Q)**: "Ne arıyorum?"
- **Key (K)**: "Ne içeriyorum?"
- **Value (V)**: "Seçilirsem hangi bilgiyi sunarım?"

Bir query ile tüm key'ler arasındaki nokta çarpımı attention skorları üretir. Yüksek skor "bu key benim query'imle eşleşiyor" demektir. Bu skorlar value'ları ağırlıklandırır. Çıktı value'ların ağırlıklı bir toplamıdır.

### Q, K, V Hesaplaması

Her token embedding'i üç öğrenilmiş ağırlık matrisi üzerinden projeksiyona uğrar:

```
Input embeddings (n token'lık dizi, her biri d boyutlu):

  X = [x1, x2, x3, ..., xn]       şekil: (n, d)

Üç ağırlık matrisi:

  Wq  şekil: (d, dk)
  Wk  şekil: (d, dk)
  Wv  şekil: (d, dv)

Projeksiyonlar:

  Q = X @ Wq    şekil: (n, dk)      her token'ın query'si
  K = X @ Wk    şekil: (n, dk)      her token'ın key'i
  V = X @ Wv    şekil: (n, dv)      her token'ın value'su
```

Görsel olarak, bir token için:

```
             Wq
  x_i ------[*]------> q_i    "Ne arıyorum?"
       |
       |     Wk
       +----[*]------> k_i    "Ne içeriyorum?"
       |
       |     Wv
       +----[*]------> v_i    "Ne sunuyorum?"
```

### Attention Matrisi

Tüm token'lar için Q, K, V'ye sahip olduğunda, attention skorları bir matris oluşturur:

```
Skorlar = Q @ K^T    şekil: (n, n)

              k1    k2    k3    k4    k5
        +-----+-----+-----+-----+-----+
   q1   | 2.1 | 0.3 | 0.1 | 0.8 | 0.2 |   <- q1'in her key'e ne kadar attention yaptığı
        +-----+-----+-----+-----+-----+
   q2   | 0.4 | 1.9 | 0.7 | 0.1 | 0.3 |
        +-----+-----+-----+-----+-----+
   q3   | 0.2 | 0.6 | 2.3 | 0.5 | 0.1 |
        +-----+-----+-----+-----+-----+
   q4   | 0.9 | 0.1 | 0.4 | 1.7 | 0.6 |
        +-----+-----+-----+-----+-----+
   q5   | 0.1 | 0.3 | 0.2 | 0.5 | 2.0 |
        +-----+-----+-----+-----+-----+

Her satır: bir token'ın tüm dizi üzerindeki attention'ı
```

### Neden Ölçekleyelim?

Nokta çarpımları boyut dk ile büyür. dk = 64 ise, nokta çarpımları onlar mertebesinde olabilir ve softmax'ı gradient'ların kaybolduğu bölgelere iter. Çözüm: sqrt(dk)'ya böl.

```
Ölçeklenmiş skorlar = (Q @ K^T) / sqrt(dk)
```

Bu, değerleri softmax'ın yararlı gradient'lar ürettiği bir aralıkta tutar.

### Softmax Skorları Ağırlıklara Çevirir

Softmax ham skorları her satır boyunca bir olasılık dağılımına çevirir:

```
q1 için ham skorlar:   [2.1, 0.3, 0.1, 0.8, 0.2]
                            |
                         softmax
                            |
Attention ağırlıkları:   [0.52, 0.09, 0.07, 0.14, 0.08]   (toplamı ~1.0)
```

Şimdi her token'ın diğer her token'a ne kadar attention yapacağını söyleyen bir ağırlık seti var.

### Value'ların Ağırlıklı Toplamı

Her token için son çıktı, tüm value vektörlerinin ağırlıklı bir toplamıdır:

```
output_i = sum( attention_weight[i][j] * v_j  tüm j için )

Token 1 için:
  output_1 = 0.52 * v1 + 0.09 * v2 + 0.07 * v3 + 0.14 * v4 + 0.08 * v5
```

### Tam Pipeline

```
                    +-------+
  X (input)  ----->|  @ Wq  |-----> Q
                    +-------+
                    +-------+
  X (input)  ----->|  @ Wk  |-----> K
                    +-------+                     +----------+
                    +-------+                     |          |
  X (input)  ----->|  @ Wv  |-----> V ---------->| ağırlıklı |----> output
                    +-------+          ^          |   toplam |
                                       |          +----------+
                              +--------+--------+
                              |    softmax      |
                              +---------+-------+
                                        ^
                              +---------+-------+
                              | Q @ K^T / sqrt  |
                              +-----------------+
```

Tek satırda formül:

```
Attention(Q, K, V) = softmax( Q @ K^T / sqrt(dk) ) @ V
```

## İnşa Et

### Adım 1: Sıfırdan softmax

Softmax ham logit'leri olasılıklara çevirir. Sayısal kararlılık için max'ı çıkar.

```python
import numpy as np

def softmax(x):
    shifted = x - np.max(x, axis=-1, keepdims=True)
    exp_x = np.exp(shifted)
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

logits = np.array([2.0, 1.0, 0.1])
print(f"logits:  {logits}")
print(f"softmax: {softmax(logits)}")
print(f"sum:     {softmax(logits).sum():.4f}")
```

### Adım 2: Scaled dot-product attention

Çekirdek fonksiyon. Q, K, V matrislerini alır ve attention çıktısını artı ağırlık matrisini döndürür.

```python
def scaled_dot_product_attention(Q, K, V):
    dk = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(dk)
    weights = softmax(scores)
    output = weights @ V
    return output, weights
```

### Adım 3: Öğrenilmiş projeksiyonlu self-attention sınıfı

Xavier benzeri ölçeklemeyle initialize edilen Wq, Wk, Wv ağırlık matrislerine sahip tam bir self-attention modülü.

```python
class SelfAttention:
    def __init__(self, d_model, dk, dv, seed=42):
        rng = np.random.default_rng(seed)
        scale = np.sqrt(2.0 / (d_model + dk))
        self.Wq = rng.normal(0, scale, (d_model, dk))
        self.Wk = rng.normal(0, scale, (d_model, dk))
        scale_v = np.sqrt(2.0 / (d_model + dv))
        self.Wv = rng.normal(0, scale_v, (d_model, dv))
        self.dk = dk

    def forward(self, X):
        Q = X @ self.Wq
        K = X @ self.Wk
        V = X @ self.Wv
        output, weights = scaled_dot_product_attention(Q, K, V)
        return output, weights
```

### Adım 4: Bir cümlede çalıştır

Bir cümle için sahte embedding'ler oluştur ve attention ağırlıklarını izle.

```python
sentence = ["The", "cat", "sat", "on", "the", "mat"]
n_tokens = len(sentence)
d_model = 8
dk = 4
dv = 4

rng = np.random.default_rng(42)
X = rng.normal(0, 1, (n_tokens, d_model))

attn = SelfAttention(d_model, dk, dv, seed=42)
output, weights = attn.forward(X)

print("Attention ağırlıkları (her satır: o token nereye bakıyor):\n")
print(f"{'':>6}", end="")
for token in sentence:
    print(f"{token:>6}", end="")
print()

for i, token in enumerate(sentence):
    print(f"{token:>6}", end="")
    for j in range(n_tokens):
        w = weights[i][j]
        print(f"{w:6.3f}", end="")
    print()
```

### Adım 5: ASCII heatmap ile attention'ı görselleştir

Hızlı bir görsel için attention ağırlıklarını karakterlere eşle.

```python
def ascii_heatmap(weights, tokens, chars=" ░▒▓█"):
    n = len(tokens)
    print(f"\n{'':>6}", end="")
    for t in tokens:
        print(f"{t:>6}", end="")
    print()

    for i in range(n):
        print(f"{tokens[i]:>6}", end="")
        for j in range(n):
            level = int(weights[i][j] * (len(chars) - 1) / weights.max())
            level = min(level, len(chars) - 1)
            print(f"{'  ' + chars[level] + '   '}", end="")
        print()

ascii_heatmap(weights, sentence)
```

## Kullan

PyTorch'un `nn.MultiheadAttention`'ı tam olarak inşa ettiğimiz şeyi yapar, artı multi-head bölme ve çıktı projeksiyonu:

```python
import torch
import torch.nn as nn

d_model = 8
n_heads = 2
seq_len = 6

mha = nn.MultiheadAttention(embed_dim=d_model, num_heads=n_heads, batch_first=True)

X_torch = torch.randn(1, seq_len, d_model)

output, attn_weights = mha(X_torch, X_torch, X_torch)

print(f"Input şekli:            {X_torch.shape}")
print(f"Output şekli:           {output.shape}")
print(f"Attention ağırlık şekli: {attn_weights.shape}")
print(f"\nAttn ağırlıkları (head'ler üzerinde ortalanmış):")
print(attn_weights[0].detach().numpy().round(3))
```

Anahtar fark: multi-head attention, her biri dk = d_model / n_heads boyutunda kendi Q, K, V projeksiyonlarına sahip birden fazla attention fonksiyonunu paralel çalıştırır, sonra sonuçları birleştirir. Bu, modelin farklı ilişki tiplerine aynı anda attention yapmasına izin verir.

## Yayınla

Bu ders şunu üretir:
- `outputs/prompt-attention-explainer.md` - veritabanı lookup analojisi üzerinden attention'ı açıklamak için bir prompt

## Alıştırmalar

1. `scaled_dot_product_attention`'ı, softmax'tan önce belirli pozisyonları negatif sonsuza set eden opsiyonel bir mask matrisi kabul edecek şekilde değiştir (causal/decoder mask'lemenin çalışma şekli budur)
2. Multi-head attention'ı sıfırdan implement et: Q, K, V'yi `n_heads` parçaya böl, her birinde attention çalıştır, birleştir ve son bir Wo ağırlık matrisi üzerinden projeksiyona uğrat
3. Aynı uzunlukta iki farklı cümle al, aynı SelfAttention instance'ından geçir ve attention pattern'lerini karşılaştır. Ne değişir? Ne aynı kalır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| Query (Q) | "Soru vektörü" | Bu token'ın hangi bilgiyi aradığını temsil eden, input'un öğrenilmiş projeksiyonu |
| Key (K) | "Etiket vektörü" | Bu token'ın hangi bilgiyi içerdiğini temsil eden, query'lere karşı eşleştirilen öğrenilmiş projeksiyon |
| Value (V) | "İçerik vektörü" | Attention skorlarına göre toplanan gerçek bilgiyi taşıyan öğrenilmiş projeksiyon |
| Scaled dot-product attention | "Attention formülü" | softmax(QK^T / sqrt(dk)) @ V - ölçekleme, yüksek boyutlarda softmax doygunluğunu önler |
| Self-attention | "Token kendine ve diğerlerine bakar" | Q, K, V'nin hepsinin aynı diziden geldiği, her pozisyonun diğer her pozisyona attention yapmasına izin veren attention |
| Attention ağırlıkları | "Ne kadar odak" | Ölçeklenmiş nokta çarpımları üzerindeki softmax tarafından üretilen, pozisyonlar üzerinde bir olasılık dağılımı |
| Multi-head attention | "Paralel attention" | Farklı projeksiyonlarla birden fazla attention fonksiyonu çalıştırma, sonra daha zengin temsiller için sonuçları birleştirme |

## İleri Okuma

- [Attention Is All You Need (Vaswani et al., 2017)](https://arxiv.org/abs/1706.03762) - orijinal transformer makalesi
- [The Illustrated Transformer (Jay Alammar)](https://jalammar.github.io/illustrated-transformer/) - tam mimarinin en iyi görsel gezintisi
- [The Annotated Transformer (Harvard NLP)](https://nlp.seas.harvard.edu/annotated-transformer/) - açıklamalarla satır-satır PyTorch implementasyonu
