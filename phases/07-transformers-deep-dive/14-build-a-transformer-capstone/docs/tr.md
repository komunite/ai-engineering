# Sıfırdan bir Transformer İnşa Et — Bitirme

> On üç ders. Tek model. Kestirme yok.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 01'den 13'e kadar. Atlama.
**Süre:** ~120 dakika

## Sorun

Her makaleyi okudun. Attention'ı, multi-head bölmelerini, positional encoding'leri, encoder ve decoder bloklarını, BERT ve GPT loss'larını, MoE'yi, KV cache'i implement ettin. Şimdi bunları gerçek bir görevde birlikte çalıştır.

Bitirme projesi: küçük bir decoder-only transformer'ı karakter-seviyesi dil modelleme görevinde end-to-end eğit. Shakespeare okur. Yeni Shakespeare üretir. Bir laptop'ta 10 dakikadan az sürede eğitilecek kadar küçük. Daha büyük bir veri seti ve daha uzun eğitimle değiştirilince sana gerçek bir LM verecek kadar doğru.

Bu kursun "nanoGPT"sidir. Orijinal değil — Karpathy'nin 2023 nanoGPT tutorial'ı her öğrencinin en az bir kere yazdığı referans implementasyondur. Şekli kaldırıyoruz ve kapsadığımız şeyler etrafında yeniden araçlandırıyoruz.

## Kavram

![Sıfırdan-transformer blok diyagramı](../assets/capstone.svg)

Mimari, açıklamalı:

```
input token'ları (B, N)
   │
   ▼
token embedding + positional embedding  ◀── Ders 04 (RoPE opsiyonu)
   │
   ▼
┌──── blok × L ─────────────────────┐
│  RMSNorm                          │  ◀── Ders 05
│  MultiHeadAttention (causal)      │  ◀── Ders 03 + 07 (causal mask)
│  residual                         │
│  RMSNorm                          │
│  SwiGLU FFN                       │  ◀── Ders 05
│  residual                         │
└────────────────────────────────── ┘
   │
   ▼
son RMSNorm
   │
   ▼
lm_head (token embedding'e bağlı)
   │
   ▼
logit'ler (B, N, V)
   │
   ▼
bir kaydırarak cross-entropy           ◀── Ders 07
```

### Gönderdiğimiz

- `GPTConfig` — tüm hyperparametreleri yapılandırmak için tek yer.
- `MultiHeadAttention` — causal, batched, opsiyonel Flash tarzı yolla (PyTorch'un `scaled_dot_product_attention`'ı).
- `SwiGLUFFN` — modern FFN.
- `Block` — pre-norm, residual-sarılı attention + FFN.
- `GPT` — embedding'ler, yığılmış bloklar, LM head, generate().
- AdamW, cosine LR, gradient clipping ile eğitim döngüsü.
- Shakespeare metni üzerinde char-seviyesi tokenizer.

### Göndermediğimiz

- RoPE — Ders 04'te kavramsal olarak implement edildi. Burada basitlik için öğrenilmiş positional embedding'ler kullanıyoruz. Alıştırmalar RoPE'a geçmeni ister.
- Üretim sırasında KV cache — her üretim adımı tam prefix üzerinde attention'ı yeniden hesaplar. Daha yavaş ama daha basit. Alıştırmalar bir KV cache eklemeni ister.
- Flash Attention — PyTorch 2.0+ input'lar eşleşirse otomatik dispatch eder; `F.scaled_dot_product_attention` kullanıyoruz.
- MoE — blok başına tek FFN. MoE'yi Ders 11'de gördün.

### Hedef metrikler

Mac M2 laptop'unda, `tinyshakespeare.txt` üzerinde 2.000 adım eğitilmiş 4 katmanlı, 4 head'li, d_model=128 GPT:

- Eğitim loss'u yaklaşık 6 dakikada ~4.2'den (rastgele) ~1.5'e yakınsar.
- Sample'lanan çıktı Shakespeare-biçimli görünür: arkaik kelimeler, satır araları, "ROMEO:" gibi özel adlar ortaya çıkar.
- Val loss (metnin tutulan son %10'u) eğitim loss'unu yakından takip eder; bu boyut/bütçede overfitting yok.

## İnşa Et

Bu ders PyTorch kullanıyor. `torch` kur (CPU build iyi). `code/main.py`'a bak. Script şunları halleder:

- Yoksa `tinyshakespeare.txt`'i indirir (veya yerel kopyayı okur).
- Byte-seviyesi char tokenizer.
- 90/10'da train/val ayrımı.
- Desteklenen donanımda bf16 autocast ile eğitim döngüsü.
- Eğitim bitince sample'lama.

### Adım 1: veri

```python
text = open("tinyshakespeare.txt").read()
chars = sorted(set(text))
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for c, i in stoi.items()}
encode = lambda s: [stoi[c] for c in s]
decode = lambda xs: "".join(itos[x] for x in xs)
```

65 benzersiz karakter. Minik vocabulary. 4-byte vocab_size'a sığar. BPE yok, tokenizer dramı yok.

### Adım 2: model

`code/main.py`'a bak. Blok Ders 05'ten textbook — pre-norm, RMSNorm, SwiGLU, causal MHA. 4/4/128 için parametre sayısı: ~800K.

### Adım 3: eğitim döngüsü

Uzunluk-256 token pencerelerinin rastgele bir batch'ini al. Forward. Bir kaydırarak cross-entropy. Backward. AdamW adımı. Log. Tekrar et.

```python
for step in range(max_steps):
    x, y = get_batch("train")
    logits = model(x)
    loss = F.cross_entropy(logits.view(-1, vocab_size), y.view(-1))
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    opt.zero_grad()
```

### Adım 4: sample

Bir prompt verildiğinde, tekrar tekrar forward et, top-p logit'lerden sample al, ekle ve devam et. 500 token sonra dur.

### Adım 5: çıktıyı oku

2.000 adımdan sonra:

```
ROMEO:
Away and mild will not thy friend, that thou shalt wit:
The chief that well shame and hath been his friends,
...
```

Shakespeare değil. Ama Shakespeare-biçimli. ~800K parametre ve laptop'ta 6 dakika için net bir kazanç.

## Kullan

Bu bitirme projesi bir referans mimarisidir. Gerçek bir şeye göndermek için üç uzantı:

1. **Tokenizer'ı değiştir.** BPE kullan (örn. `tiktoken.get_encoding("cl100k_base")`). Vocab size 65'ten ~50.000'e fırlar. Model kapasitesi telafi için ölçeklenmeli.
2. **Daha büyük bir corpus'ta eğit.** `OpenWebText` veya `fineweb-edu` (HuggingFace) kullan. Tek bir A100'de 10B token, 125M-param GPT için ~24 saat sürer.
3. **RoPE + KV cache + Flash Attention ekle.** Aşağıdaki alıştırmalar her birinden seni yürütür.

Bu, akıcı İngilizce üreten 125M-parametreli bir GPT olur. Frontier model değil. Ama aynı kod yolu — sadece daha büyük — Karpathy, EleutherAI ve Allen Institute'un 2026'da araştırma checkpoint'lerini eğitmek için kullandığı şeydir.

## Yayınla

`outputs/skill-transformer-review.md`'ye bak. Skill, önceki 13 dersin tamamı boyunca sıfırdan-transformer implementasyonunu doğruluk için inceler.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. Eğitilmiş modelinin son-adım validation loss'unun 2.0'ın altında olduğunu doğrula. `max_steps`'i 2.000'den 5.000'e değiştir — val loss iyileşmeye devam ediyor mu?
2. **Orta.** Öğrenilmiş positional embedding'leri RoPE ile değiştir. `MultiHeadAttention` içinde Q ve K'ya rotasyonu uygula. Eğit ve val loss'un en az o kadar düşük olduğunu doğrula.
3. **Orta.** Sample'lama döngüsünde bir KV cache implement et. Cache'li ve cache'siz 500 token üret. Duvar-saati laptop'ta 5–20× iyileşmeli.
4. **Zor.** Modele next-plus-one token'ı tahmin eden ikinci bir head ekle (DeepSeek-V3'ten MTP — Multi-Token Prediction). Birlikte eğit. Yardım ediyor mu?
5. **Zor.** Blok başına tek FFN'i 4 uzmanlı bir MoE ile değiştir. Router + top-2 routing. Eşleşen aktif parametrelerde val loss'un nasıl değiştiğini gör.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| nanoGPT | "Karpathy'nin tutorial repo'su" | Minimal decoder-only transformer eğitim kodu, ~300 LOC; kanonik referans. |
| tinyshakespeare | "Standart oyuncak corpus" | ~1.1 MB metin; 2015'ten beri her character-LM tutorial'ı bunu kullanır. |
| Tied embeddings | "Input/output matrisi paylaş" | LM head ağırlığı = token embedding matrisinin transpozu; parametre tasarrufu, kalite iyileşmesi. |
| bf16 autocast | "Eğitim hassasiyet numarası" | Forward/back'i bf16'da çalıştır, optimizer state'i fp32'de tut; 2021'den beri standart. |
| Gradient clipping | "Sıçramaları durdurur" | Global grad norm'unu 1.0'da kap; eğitim patlamalarını önler. |
| Cosine LR schedule | "2020+ varsayılan" | LR lineer rampa yukarı (warmup) sonra cosine-biçimli olarak tepe'nin %10'una iner. |
| MFU | "Model FLOP Utilization" | Elde edilen FLOPs / teorik tepe; 2026'da yoğun %40, MoE %30 güçlüdür. |
| Val loss | "Tutulan loss" | Modelin asla görmediği veri üzerinde cross-entropy; overfit dedektörü. |

## İleri Okuma

- [The Annotated Transformer (Harvard NLP)](https://nlp.seas.harvard.edu/annotated-transformer/) — klasik açıklamalı implementasyon.
