# Metin için CNN'ler ve RNN'ler

> Convolution'lar n-gram'ları öğrenir. Recurrence'lar hatırlar. İkisi de attention tarafından geçildi. İkisi de kısıtlı donanımda hâlâ önemli.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 3 · 11 (PyTorch Girişi), Faz 5 · 03 (Word Embedding'ler), Faz 4 · 02 (Sıfırdan Convolution'lar)
**Süre:** ~75 dakika

## Sorun

TF-IDF ve Word2Vec, kelime sırasını yok sayan düz vektörler üretti. Bunların üzerine kurulu bir sınıflandırıcı, `dog bites man`'i `man bites dog`'tan ayırt edemezdi. Kelime sırası bazen sinyali taşır.

Transformer'lar gelmeden önce iki mimari ailesi bu boşluğu doldurdu.

**Metin için convolutional ağlar (TextCNN).** Word embedding dizileri üzerinde 1D convolution'lar uygula. 3 genişliğindeki bir filtre öğrenilebilir bir trigram detektörüdür: üç kelimeyi kapsar ve bir skor verir. Çok ölçekli desenleri tespit etmek için farklı genişlikleri (2, 3, 4, 5) yığ. Sabit boyutlu bir temsile max-pool. Düz, paralel, hızlı.

**Recurrent ağlar (RNN, LSTM, GRU).** Token'ları her seferinde bir tane işle, bilgiyi ileri taşıyan bir hidden state tut. Sıralı, bellek taşıyan, esnek girdi uzunlukları. Sequence modelleme'ye 2014'ten 2017'ye kadar hâkim oldu, sonra attention oldu.

Bu ders ikisini de kurar, sonra attention'a motivasyon olan başarısızlığı adlandırır.

## Kavram

**TextCNN** (Kim, 2014). Token'lar gömülür. Genişliği `k` olan bir 1D convolution, ardışık `k`-gram embedding'ler üzerinde bir filtre kaydırır, bir feature map üretir. O map üzerinde global max-pooling en güçlü aktivasyonu seçer. Birkaç filtre genişliğinden gelen max-pool çıktılarını birleştir. Bir sınıflandırıcı head'e besle.

Neden işe yarar. Bir filtre öğrenilebilir bir n-gram'dır. Max-pooling pozisyon-değişmezdir, böylece "not good" bir değerlendirmenin başında ya da ortasında aynı feature'ı ateşler. Her biri 100 filtreli üç filtre genişliği sana 300 öğrenilmiş n-gram detektörü verir. Eğitim paraleldir; sıralı bağımlılık yok.

**RNN.** Her zaman adımı `t`'de hidden state `h_t = f(W * x_t + U * h_{t-1} + b)`. Zaman boyunca `W`, `U`, `b`'yi paylaş. `T` zamanındaki hidden state, tüm önceki kısmın özetidir. Sınıflandırma için, `h_1 ... h_T` üzerinde havuzla (max, mean ya da son).

Düz RNN'ler vanishing gradient çeker. **LSTM** neyi unutacağına, neyi saklayacağına ve neyi çıkaracağına karar veren gate'ler ekler, uzun diziler boyunca gradyanları stabilize eder. **GRU**, LSTM'i iki gate'e basitleştirir; daha az parametreyle benzer performans gösterir.

**Bidirectional RNN'ler** bir RNN'i ileri, diğerini geri çalıştırır, hidden state'leri birleştirir. Her token'ın temsili hem sol hem sağ bağlamı görür. Tagging görevleri için temeldir.

## İnşa Et

### Adım 1: PyTorch'ta TextCNN

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class TextCNN(nn.Module):
    def __init__(self, vocab_size, embed_dim, n_classes, filter_widths=(2, 3, 4), n_filters=64, dropout=0.3):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, n_filters, kernel_size=k)
            for k in filter_widths
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(n_filters * len(filter_widths), n_classes)

    def forward(self, token_ids):
        x = self.embed(token_ids).transpose(1, 2)
        pooled = []
        for conv in self.convs:
            c = F.relu(conv(x))
            p = F.max_pool1d(c, c.size(2)).squeeze(2)
            pooled.append(p)
        h = torch.cat(pooled, dim=1)
        return self.fc(self.dropout(h))
```

`transpose(1, 2)`, `[batch, seq_len, embed_dim]`'i `[batch, embed_dim, seq_len]`'e yeniden şekillendirir çünkü `nn.Conv1d` orta ekseni kanal olarak ele alır. Havuzlanmış çıktı, girdi uzunluğundan bağımsız olarak sabit boyutludur.

### Adım 2: LSTM sınıflandırıcı

```python
class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, n_classes, bidirectional=True, dropout=0.3):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
        factor = 2 if bidirectional else 1
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * factor, n_classes)

    def forward(self, token_ids):
        x = self.embed(token_ids)
        out, _ = self.lstm(x)
        pooled = out.max(dim=1).values
        return self.fc(self.dropout(pooled))
```

Last-state pool değil, dizi üzerinden max-pool. Sınıflandırma için, max-pooling genellikle son hidden state'i almaktan daha iyidir çünkü uzun bir dizinin sonundaki bilgi son state'e hâkim olma eğilimindedir.

### Adım 3: vanishing gradient demosu (sezgi)

Gating'siz düz bir RNN uzun mesafeli bağımlılıkları öğrenemez. Oyuncak bir görevi düşün: bir dizide token `A`'nın herhangi bir yerde geçip geçmediğini tahmin et. `A` pozisyon 1'deyse ve dizi 100 token uzunluğundaysa, loss'tan gelen gradyanın recurrent ağırlığın 99 çarpımı boyunca geri akması gerekir. Ağırlık 1'den küçükse, gradyan kaybolur. 1'den büyükse, patlar.

```python
def vanishing_gradient_sim(seq_len, recurrent_weight=0.9):
    import math
    return math.pow(recurrent_weight, seq_len)


# weight=0.9 ile 100 adım üzerinde:
#   0.9 ^ 100 ≈ 2.7e-5
# Adım 100'den adım 1'e gradyan etkili biçimde sıfırdır.
```

LSTM'ler bunu yalnızca toplamsal etkileşimlerle ağ boyunca akan bir **cell state** ile düzeltir (forget gate'i çarpımsal olarak ölçekler ama gradyanlar hâlâ "otoyol" boyunca akar). GRU'lar daha az parametreyle benzer bir şey yapar. İkisi de sana 100+ adım dizi boyunca stabil eğitim verir.

### Adım 4: bu hâlâ neden yeterli değildi

LSTM'lerle bile üç sorun devam etti.

1. **Sıralı darboğaz.** 1000 uzunluğundaki bir dizide bir RNN'i eğitmek 1000 seri forward/backward adım gerektirir. Zaman boyunca paralelleştirilemez.
2. **Encoder-decoder kurulumlarında sabit boyutlu bağlam vektörü.** Decoder, tüm girdi üzerinden sıkıştırılmış encoder'ın yalnızca son hidden state'ini görür. Uzun girdiler ayrıntı kaybeder. Ders 09 bunu doğrudan ele alır.
3. **Uzak bağımlılık doğruluk tavanı.** LSTM'ler düz RNN'leri geçer ama 200+ adım boyunca belirli bilgiyi yaymakta hâlâ zorlanır.

Attention üçünü de çözdü. Transformer'lar recurrence'ı tamamen attı. Ders 10 dönüm noktasıdır.

## Kullan

PyTorch'un `nn.LSTM`, `nn.GRU` ve `nn.Conv1d`'i üretim hazırdır. Eğitim kodu standarttır.

Hugging Face, girdi katmanı olarak takabileceğin önceden eğitilmiş embedding'ler içerir:

```python
from transformers import AutoModel

encoder = AutoModel.from_pretrained("bert-base-uncased")
for param in encoder.parameters():
    param.requires_grad = False


class BertCNN(nn.Module):
    def __init__(self, n_classes, filter_widths=(2, 3, 4), n_filters=64):
        super().__init__()
        self.encoder = encoder
        self.convs = nn.ModuleList([nn.Conv1d(768, n_filters, kernel_size=k) for k in filter_widths])
        self.fc = nn.Linear(n_filters * len(filter_widths), n_classes)

    def forward(self, input_ids, attention_mask):
        with torch.no_grad():
            out = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        x = out.transpose(1, 2)
        pooled = [F.max_pool1d(F.relu(conv(x)), kernel_size=conv(x).size(2)).squeeze(2) for conv in self.convs]
        return self.fc(torch.cat(pooled, dim=1))
```

Kısıtlamaya uyduğunda kullan checklist'i.

- **Edge / cihaz üzerinde çıkarım.** GloVe embedding'leriyle TextCNN bir transformer'dan 10-100 kat daha küçüktür. Deploy hedefin bir telefonsa, stack budur.
- **Streaming / online sınıflandırma.** RNN bir seferde bir token'ı işler; transformer'lar tam diziye ihtiyaç duyar. Gerçek zamanlı gelen metin için, LSTM'ler hâlâ kazanır.
- **Baseline'lar için minik modeller.** Yeni bir görevde hızlı yineleme. CPU'da 5 dakikada bir TextCNN eğit.
- **Sınırlı veriyle sequence labeling.** BiLSTM-CRF (ders 06), 1k-10k etiketli cümle için hâlâ üretim seviyesi bir NER mimarisidir.

Her şey transformer'a gider.

## Yayınla

`outputs/prompt-text-encoder-picker.md` olarak kaydet:

```markdown
---
name: text-encoder-picker
description: Pick a text encoder architecture for a given constraint set.
phase: 5
lesson: 08
---

Given constraints (task, data volume, latency budget, deploy target, compute budget), output:

1. Encoder architecture: TextCNN, BiLSTM, BiLSTM-CRF, transformer fine-tune, or "use a pretrained transformer as a frozen encoder + small head".
2. Embedding input: random init, GloVe / fastText frozen, or contextualized transformer embeddings.
3. Training recipe in 5 lines: optimizer, learning rate, batch size, epochs, regularization.
4. One monitoring signal. For RNN/CNN models: attention mechanism absence means they miss long-range deps; check per-length accuracy. For transformers: fine-tuning collapse if LR too high; check train loss.

Refuse to recommend fine-tuning a transformer when data is under ~500 labeled examples without showing that a TextCNN / BiLSTM baseline has plateaued. Flag edge deployment as needing architecture-before-everything.
```

## Alıştırmalar

1. **Kolay.** 3-sınıflı oyuncak bir veri seti üzerinde bir TextCNN eğit (veriyi sen icat et). Filtre genişliklerinin (2, 3, 4) ortalama F1'de tek bir genişliği (3) geçtiğini doğrula.
2. **Orta.** LSTM sınıflandırıcı için max-pool, mean-pool ve son-state pooling uygula. Küçük bir veri sette karşılaştır; hangi pooling'in kazandığını belgele ve neden olduğunu hipotezle.
3. **Zor.** Bir BiLSTM-CRF NER tagger kur (ders 06'yı ve bunu birleştir). CoNLL-2003 üzerinde eğit. Ders 06'daki yalnızca-CRF baseline ile ve bir BERT fine-tune ile karşılaştır. Eğitim süresini, belleği ve F1'i raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| TextCNN | Metin için CNN | Global max-pool ile word embedding'ler üzerinde 1D convolution yığını. Kim (2014). |
| RNN | Recurrent ağ | Her zaman adımında güncellenen hidden state: `h_t = f(W x_t + U h_{t-1})`. |
| LSTM | Gated RNN | Input / forget / output gate'leri + bir cell state ekler. Uzun diziler boyunca stabil eğitilir. |
| GRU | Daha basit LSTM | Üç yerine iki gate. Benzer doğruluk, daha az parametre. |
| Bidirectional | İki yönlü | İleri + geri RNN birleştirilmiş. Her token bağlamının her iki tarafını da görür. |
| Vanishing gradient | Eğitim sinyali ölür | Düz RNN'lerde <1 ağırlıklarla tekrarlanan çarpım erken adım gradyanlarını etkili biçimde sıfır yapar. |

## İleri Okuma

- [Kim, Y. (2014). Convolutional Neural Networks for Sentence Classification](https://arxiv.org/abs/1408.5882) — TextCNN makalesi. Sekiz sayfa. Okunaklı.
- [Hochreiter, S. and Schmidhuber, J. (1997). Long Short-Term Memory](https://www.bioinf.jku.at/publications/older/2604.pdf) — LSTM makalesi. Beklenmedik şekilde berrak.
- [Olah, C. (2015). Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/) — LSTM'leri herkes için erişilebilir kılan diyagramlar.
