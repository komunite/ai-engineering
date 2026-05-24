# Attention Mekanizması — Atılım

> Decoder, sıkıştırılmış bir özete gözlerini kısarak bakmayı bırakıp tüm kaynağa bakmaya başlar. Bundan sonrası attention artı mühendisliktir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 09 (Seq2seq Modeller)
**Süre:** ~45 dakika

## Sorun

Ders 09 ölçülü bir başarısızlıkla bitti. Oyuncak bir kopyalama görevinde eğitilmiş bir GRU encoder-decoder, uzunluk 5'te %89 doğruluktan uzunluk 80'de şansa-yakına gider. Sebep yapısaldır, bir eğitim bug'ı değil: encoder'ın derlediği her bilgi parçası tek bir sabit boyutlu hidden state'e sığmak zorunda ve decoder başka hiçbir şey görmez.

Bahdanau, Cho ve Bengio 2014'te üç satırlık bir düzeltme yayınladı. Decoder'a yalnızca final encoder state'ini vermek yerine, her encoder state'ini tut. Her decoder adımında, ağırlıkların "decoder şu anda encoder pozisyonu `i`'ye ne kadar bakmalı?" dediği encoder state'lerinin ağırlıklı ortalamasını hesapla. Bu ağırlıklı ortalama bağlamdır ve her decoder adımında değişir.

Tüm fikir budur. Transformer'lar onu genişletti. Self-attention onu tek bir diziye uyguladı. Multi-head attention onu paralel çalıştırdı. Ama 2014 versiyonu darboğazı zaten kırdı ve ona sahip olduğunda transformer'lara dönüş kavramsal değil mühendislik işidir.

## Kavram

![Bahdanau attention: decoder tüm encoder state'lerine sorgu yapar](../assets/attention.svg)

Her decoder adımı `t`'de:

1. Önceki decoder hidden state'i `s_{t-1}`'i **query** olarak kullan.
2. Onu her encoder hidden state'i `h_1, ..., h_T`'ye karşı puanla. Encoder pozisyonu başına bir skaler.
3. Skorları softmax'la, toplamı 1 olan attention ağırlıkları `α_{t,1}, ..., α_{t,T}` elde et.
4. Context vektörü `c_t = Σ α_{t,i} * h_i`. Encoder state'lerinin ağırlıklı ortalaması.
5. Decoder, `c_t` artı önceki çıktı token'ını alır, sonraki token'ı üretir.

Ağırlıklı ortalama mevzu. Decoder "Je"yi "I"a çevirmesi gerektiğinde, encoder state'ini "Je" üzerinde yüksek, diğerlerini düşük ağırlıklandırır. "not"a ihtiyaç duyduğunda, "pas"ı yüksek ağırlıklandırır. Context vektörü her adımı yeniden şekillendirir.

## Şekiller (herkesi ısıran şey)

Her attention implementasyonunun ilk seferde yanlış gittiği yer burası. Yavaşça oku.

| Şey | Şekil | Notlar |
|-------|-------|-------|
| Encoder hidden state'leri `H` | `(T_enc, d_h)` | BiLSTM ise, `d_h = 2 * d_hidden` |
| Decoder hidden state'i `s_{t-1}` | `(d_s,)` | Bir vektör |
| Attention skoru `e_{t,i}` | skaler | Encoder pozisyonu başına bir |
| Attention ağırlığı `α_{t,i}` | skaler | Tüm `i` üzerinde softmax sonrası |
| Context vektörü `c_t` | `(d_h,)` | Bir encoder state'iyle aynı şekil |

**Bahdanau (additive) skor.** `e_{t,i} = v_α^T * tanh(W_a * s_{t-1} + U_a * h_i)`.

- `s_{t-1}` şekli `(d_s,)`, `h_i` şekli `(d_h,)`.
- `W_a` şekli `(d_attn, d_s)`. `U_a` şekli `(d_attn, d_h)`.
- Toplamları tanh'ın içinde şekli `(d_attn,)`.
- `v_α` şekli `(d_attn,)`. `v_α` ile iç çarpım bir skalere çöker. **`v_α`'nın yaptığı budur.** Sihir değil. Attention-boyutlu bir vektörü bir skaler skora çeviren projeksiyondur.

**Luong (multiplicative) skor.** Üç varyant:

- `dot`: `e_{t,i} = s_t^T * h_i`. `d_s == d_h` gerektirir. Sert kısıtlama. Encoder'ın bidirectional ise atla.
- `general`: `e_{t,i} = s_t^T * W * h_i`, `W` şekli `(d_s, d_h)`. Eşit boyut kısıtlamasını kaldırır.
- `concat`: esasen Bahdanau formu. İlk ikisi daha ucuz olduğu için nadiren kullanılır.

**Adı anılmaya değer bir Bahdanau / Luong tuzağı.** Bahdanau `s_{t-1}`'i (mevcut kelimeyi üretmeden *önceki* decoder state'i) kullanır. Luong `s_t`'yi (üretildikten *sonraki* state) kullanır. Bunları karıştırmak, debug edilmesi son derece zor incelikli yanlış gradyanlar üretir. Bir makale seç ve onun konvansiyonuna sadık kal.

## İnşa Et

### Adım 1: additive (Bahdanau) attention

```python
import numpy as np


def additive_attention(decoder_state, encoder_states, W_a, U_a, v_a):
    projected_dec = W_a @ decoder_state
    projected_enc = encoder_states @ U_a.T
    combined = np.tanh(projected_enc + projected_dec)
    scores = combined @ v_a
    weights = softmax(scores)
    context = weights @ encoder_states
    return context, weights


def softmax(x):
    x = x - np.max(x)
    e = np.exp(x)
    return e / e.sum()
```

Şekillerini yukarıdaki tabloyla karşılaştır. `encoder_states` şekli `(T_enc, d_h)`. `projected_enc` şekli `(T_enc, d_attn)`. `projected_dec` şekli `(d_attn,)` ve broadcast eder. `combined` şekli `(T_enc, d_attn)`. `scores` şekli `(T_enc,)`. `weights` şekli `(T_enc,)`. `context` şekli `(d_h,)`. Gönder.

### Adım 2: Luong dot ve general

```python
def dot_attention(decoder_state, encoder_states):
    scores = encoder_states @ decoder_state
    weights = softmax(scores)
    return weights @ encoder_states, weights


def general_attention(decoder_state, encoder_states, W):
    projected = W.T @ decoder_state
    scores = encoder_states @ projected
    weights = softmax(scores)
    return weights @ encoder_states, weights
```

Her biri üç satır. Bu, Luong'un makalesinin yerini bulduğu yer. Çoğu görevde aynı doğruluk, çok daha az kod.

### Adım 3: işlenmiş sayısal bir örnek

Üç encoder state'i (kabaca "cat", "sat", "mat") ve ilkiyle en çok hizalanan bir decoder state'i verildiğinde, attention dağılımı pozisyon 0'a yoğunlaşır. Decoder state'i sonuncuyla hizalanacak şekilde kayarsa, attention pozisyon 2'ye gider. Context vektörü takip eder.

```python
H = np.array([
    [1.0, 0.0, 0.2],
    [0.5, 0.5, 0.1],
    [0.1, 0.9, 0.3],
])

s_close_to_cat = np.array([0.9, 0.1, 0.2])
ctx, w = dot_attention(s_close_to_cat, H)
print("weights:", w.round(3))
```

```
weights: [0.464 0.305 0.231]
```

İlk satır kazanır. Sonra decoder state'ini üçüncü encoder state'ine yaklaştır ve ağırlıkların kaydığını izle. Hepsi bu. Attention açık hizalamadır.

### Adım 4: transformer'lara köprü neden bu

Yukarıdaki dili Q/K/V'ye çevir:

- **Query** = decoder state `s_{t-1}`
- **Key** = encoder state'leri (karşılaştırdığımız)
- **Value** = encoder state'leri (ağırlıklandırıp topladığımız)

Klasik attention'da key'ler ve value'lar aynı şeydir. Self-attention onları ayırır: bir diziyi kendisine karşı sorgulayabilirsin, K ve V için farklı öğrenilmiş projeksiyonlarla. Multi-head attention onu farklı öğrenilmiş projeksiyonlarla paralel çalıştırır. Transformer'lar tüm aşamayı çok kez yığar ve RNN'leri bırakır.

Matematik aynı. Şekiller aynı. Bahdanau attention'dan scaled dot-product attention'a pedagojik sıçrama çoğunlukla notasyondur.

## Kullan

PyTorch ve TensorFlow doğrudan attention içerir.

```python
import torch
import torch.nn as nn

mha = nn.MultiheadAttention(embed_dim=128, num_heads=8, batch_first=True)
query = torch.randn(2, 5, 128)
key = torch.randn(2, 10, 128)
value = torch.randn(2, 10, 128)

output, weights = mha(query, key, value)
print(output.shape, weights.shape)
```

```
torch.Size([2, 5, 128]) torch.Size([2, 5, 10])
```

Bu bir transformer attention katmanıdır. 5 pozisyonluk query batch'i, 10 pozisyonluk key/value batch'i, her biri 128 boyutlu, 8 head. `output` yeni context-zenginleştirilmiş query'ler. `weights` görselleştirebileceğin 5x10 alignment matrisi.

### Klasik attention hâlâ ne zaman önemli

- Pedagoji. Tek head, tek katman, RNN tabanlı sürüm her kavramı görünür kılar.
- Transformer'ların sığmadığı cihaz üzerinde dizi görevleri.
- 2014-2017'den herhangi bir makale. Bahdanau'nun konvansiyonunu bilmeden onu yanlış okursun.
- MT'de ince-taneli hizalama analizi. Ham attention ağırlıkları transformer modellerinde bile bir yorumlanabilirlik aracıdır ve onları okumak ne olduklarını bilmeyi gerektirir.

### Açıklama olarak attention ağırlığı tuzağı

Attention ağırlıkları yorumlanabilir görünür. Pozisyonlar arasında toplamı bir olan ağırlıklardır; çizebilirsin; yüksek "buna baktı" anlamına gelir. Reviewer'lar onları sever.

Göründükleri kadar yorumlanabilir değiller. Jain ve Wallace (2019), bazı görevlerde attention dağılımlarının model tahminlerini değiştirmeden permute edilip rastgele alternatiflerle değiştirilebileceğini gösterdi. Bir ablation ya da counterfactual kontrolü olmadan attention ağırlıklarını mantık kanıtı olarak asla raporlama.

## Yayınla

`outputs/prompt-attention-shapes.md` olarak kaydet:

```markdown
---
name: attention-shapes
description: Debug shape bugs in attention implementations.
phase: 5
lesson: 10
---

Given a broken attention implementation, you identify the shape mismatch. Output:

1. Which matrix has the wrong shape. Name the tensor.
2. What its shape should be, derived from (d_s, d_h, d_attn, T_enc, T_dec, batch_size).
3. One-line fix. Transpose, reshape, or project.
4. A test to catch regressions. Typically: assert `output.shape == (batch, T_dec, d_h)` and `weights.shape == (batch, T_dec, T_enc)` and `weights.sum(dim=-1) close to 1`.

Refuse to recommend fixes that silently broadcast. Broadcast-hiding bugs surface later as silent accuracy degradation, the worst kind of attention bug.

For Bahdanau confusion, insist the decoder input is `s_{t-1}` (pre-step state). For Luong, `s_t` (post-step state). For dot-product, flag dimension mismatch between query and key as the most common first-time error.
```

## Alıştırmalar

1. **Kolay.** Encoder'daki padding token'ları sıfır attention ağırlığı alacak şekilde `softmax` mask'leme uygula. Değişken uzunluklu dizilerden oluşan bir batch'te test et.
2. **Orta.** Luong `general` formuna multi-head attention ekle. `d_h`'i `n_heads` gruba böl, head başına attention çalıştır, birleştir. Single-head durumunun önceki implementasyonunla eşleştiğini doğrula.
3. **Zor.** Ders 09'daki oyuncak kopyalama görevinde Bahdanau attention ile bir GRU encoder-decoder eğit. Doğruluk vs dizi uzunluğunu çiz. Attention'sız baseline ile karşılaştır. Uzunluk arttıkça açığın genişlediğini görmelisin, bu attention'ın darboğazı kaldırdığını doğrular.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Attention | Bir şeylere bakma | Bir value dizisinin ağırlıklı ortalaması, ağırlıklar bir query-key benzerliğinden hesaplanır. |
| Query, Key, Value | QKV | Üç projeksiyon: Q sorar, K eşleşecek olan, V dönecek olan. |
| Additive attention | Bahdanau | Feed-forward skor: `v^T tanh(W q + U k)`. |
| Multiplicative attention | Luong dot / general | Skor `q^T k` ya da `q^T W k`. Daha ucuz, çoğu görevde aynı doğruluk. |
| Alignment matrisi | Güzel resim | `(T_dec, T_enc)` grid'i olarak attention ağırlıkları. Modelin neye dikkat ettiğini görmek için oku. |

## İleri Okuma

- [Bahdanau, Cho, Bengio (2014). Neural Machine Translation by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473) — makale.
- [Luong, Pham, Manning (2015). Effective Approaches to Attention-based Neural Machine Translation](https://arxiv.org/abs/1508.04025) — üç skor varyantı ve karşılaştırması.
- [Jain and Wallace (2019). Attention is not Explanation](https://arxiv.org/abs/1902.10186) — yorumlanabilirlik uyarısı.
- [Dive into Deep Learning — Bahdanau Attention](https://d2l.ai/chapter_attention-mechanisms-and-transformers/bahdanau-attention.html) — PyTorch ile çalıştırılabilir gezinti.
