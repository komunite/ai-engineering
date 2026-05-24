# Seq2seq Modeller

> Çevirmen taklidi yapan iki RNN. Vurdukları darboğaz, attention'ın var olma sebebidir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 08 (Metin için CNN'ler + RNN'ler), Faz 3 · 11 (PyTorch Girişi)
**Süre:** ~75 dakika

## Sorun

Sınıflandırma, değişken uzunluklu bir diziyi tek bir etikete eşler. Çeviri, değişken uzunluklu bir diziyi başka bir değişken uzunluklu diziye eşler. Girdi ve çıktı farklı vocabulary'lerde, muhtemelen farklı dillerde, uzunluk eşitliği garantisi olmadan yaşar.

seq2seq mimarisi (Sutskever, Vinyals, Le, 2014) bunu kasıtlı olarak basit bir tarifle kırdı. İki RNN. Biri kaynak cümleyi okur ve sabit boyutlu bir context vektörü üretir. Diğeri o vektörü okur ve hedef cümleyi token token üretir. Ders 08 için yazdığın aynı kod, farklı şekilde birbirine yapıştırılmış.

Bunu çalışmak iki nedenle değerli. Birincisi, context-vector darboğazı NLP'deki pedagojik olarak en yararlı başarısızlıktır. Attention'ın ve transformer'ların iyi olduğu her şeye motivasyon olur. İkincisi, eğitim tarifi (teacher forcing, scheduled sampling, çıkarımda beam search) LLM'ler dahil her modern üretim sistemine hâlâ uygulanır.

## Kavram

**Encoder.** Kaynak cümleyi okuyan bir RNN. Final hidden state'i **context vektörü**dür — tüm girdinin sabit boyutlu özeti. Sözde kaynaktan başka hiçbir şey kaybetme.

**Decoder.** Context vektöründen başlatılan başka bir RNN. Her adımda önceden üretilmiş token'ı girdi olarak alır ve hedef vocabulary üzerinde bir dağılım üretir. Sonraki token'ı seçmek için örnekle ya da argmax al. Geri besle. `<EOS>` token'ı üretilene ya da max uzunluğa vurulana kadar tekrarla.

**Eğitim:** Her decoder adımında cross-entropy loss, dizi üzerinde toplanmış. Her iki ağ boyunca standart zamanla backprop.

**Teacher forcing.** Eğitim sırasında, decoder'ın `t` adımındaki girdisi, decoder'ın kendi önceki tahmini değil, `t-1` pozisyonundaki *gerçek* token'dır. Bu eğitimi stabilize eder; o olmadan erken hatalar çığ olur ve model asla öğrenmez. Çıkarımda modelin kendi tahminlerini kullanmak zorundasın, bu yüzden her zaman bir eğitim/çıkarım dağılım açığı vardır. O açığa **exposure bias** denir.

**Darboğaz.** Encoder'ın kaynak hakkında öğrendiği her şey o tek context vektörüne sıkıştırılmak zorunda. Uzun cümleler ayrıntı kaybeder. Nadir kelimeler bulanıklaşır. Yeniden sıralama (chat noir vs black cat) hesaplanmak değil ezberlenmek zorundadır.

Attention (ders 10) bunu, decoder'ın yalnızca sonuncusunu değil *her* encoder hidden state'ini görmesine izin vererek düzeltir. Tüm tezahürü budur.

## İnşa Et

### Adım 1: bir encoder

```python
import torch
import torch.nn as nn


class Encoder(nn.Module):
    def __init__(self, src_vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embed = nn.Embedding(src_vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)

    def forward(self, src):
        e = self.embed(src)
        outputs, hidden = self.gru(e)
        return outputs, hidden
```

`outputs`, `[batch, seq_len, hidden_dim]` şekline sahiptir — girdi pozisyonu başına bir hidden state. `hidden`, `[1, batch, hidden_dim]` şekline sahiptir — son adım. Ders 08 "sınıflandırma için outputs üzerinde havuzla" dedi. Burada son hidden state'i context vektörü olarak tutuyoruz ve adım başına outputs'u görmezden geliyoruz.

### Adım 2: bir decoder

```python
class Decoder(nn.Module):
    def __init__(self, tgt_vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embed = nn.Embedding(tgt_vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, tgt_vocab_size)

    def forward(self, token, hidden):
        e = self.embed(token)
        out, hidden = self.gru(e, hidden)
        logits = self.fc(out)
        return logits, hidden
```

Decoder bir seferde tek adım çağrılır. Girdi: tek token'lardan oluşan bir batch ve mevcut hidden state. Çıktı: sonraki token için vocabulary logits'i ve güncellenmiş hidden state.

### Adım 3: teacher forcing ile eğitim döngüsü

```python
def train_batch(encoder, decoder, src, tgt, bos_id, optimizer, teacher_forcing_ratio=0.9):
    optimizer.zero_grad()
    _, hidden = encoder(src)
    batch_size, tgt_len = tgt.shape
    input_token = torch.full((batch_size, 1), bos_id, dtype=torch.long)
    loss = 0.0
    loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    for t in range(tgt_len):
        logits, hidden = decoder(input_token, hidden)
        step_loss = loss_fn(logits.squeeze(1), tgt[:, t])
        loss += step_loss
        use_teacher = torch.rand(1).item() < teacher_forcing_ratio
        if use_teacher:
            input_token = tgt[:, t].unsqueeze(1)
        else:
            input_token = logits.argmax(dim=-1)

    loss.backward()
    optimizer.step()
    return loss.item() / tgt_len
```

Adı anılmaya değer iki knob. `ignore_index=0` padding token'larında loss'u atlar. `teacher_forcing_ratio`, her adımda gerçek token'ı vs modelin tahminini kullanma olasılığıdır. 1.0'dan (tam teacher forcing) başla ve exposure-bias açığını kapatmak için eğitim boyunca ~0.5'e kadar yumuşat.

### Adım 4: çıkarım döngüsü (greedy)

```python
@torch.no_grad()
def greedy_decode(encoder, decoder, src, bos_id, eos_id, max_len=50):
    _, hidden = encoder(src)
    batch_size = src.shape[0]
    input_token = torch.full((batch_size, 1), bos_id, dtype=torch.long)
    output_ids = []
    for _ in range(max_len):
        logits, hidden = decoder(input_token, hidden)
        next_token = logits.argmax(dim=-1)
        output_ids.append(next_token)
        input_token = next_token
        if (next_token == eos_id).all():
            break
    return torch.cat(output_ids, dim=1)
```

Greedy decoding her adımda en yüksek olasılıklı token'ı seçer. Yoldan çıkabilir: bir token'a bir kez bağlandın mı, geri alamazsın. **Beam search** en üst `k` parçalı diziyi canlı tutar ve sonda en yüksek skorlu tamamı seçer. Beam genişliği 3-5 standarttır.

### Adım 5: darboğaz, gösterimi

Modeli oyuncak bir kopyalama görevinde eğit: kaynak `[a, b, c, d, e]`, hedef `[a, b, c, d, e]`. Dizi uzunluğunu artır. Doğruluğu gözlemle.

```
seq_len=5   kopyalama doğruluğu: %98
seq_len=10  kopyalama doğruluğu: %91
seq_len=20  kopyalama doğruluğu: %62
seq_len=40  kopyalama doğruluğu: %23
```

Tek bir GRU hidden state, 40 token'lık girdiyi kayıpsız ezberleyemez. Bilgi her encoder adımında oradadır ama decoder yalnızca son state'i görür. Attention bunu doğrudan düzeltir.

## Kullan

PyTorch'un `nn.Transformer` ve `nn.LSTM` tabanlı seq2seq şablonları vardır. Hugging Face'in `transformers` kütüphanesi milyarlarca token üzerinde eğitilmiş tam encoder-decoder modeller (BART, T5, mBART, NLLB) içerir.

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tok = AutoTokenizer.from_pretrained("facebook/bart-base")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-base")

src = tok("Translate this to French: Hello, how are you?", return_tensors="pt")
out = model.generate(**src, max_new_tokens=50, num_beams=4)
print(tok.decode(out[0], skip_special_tokens=True))
```

Modern encoder-decoder'lar RNN'leri transformer'lara bıraktı. Yüksek seviyeli şekil (encoder, decoder, token-token üretim) 2014 seq2seq makalesiyle özdeştir. Her bloğun içindeki mekanizma farklıdır.

### RNN tabanlı seq2seq'e hâlâ ne zaman uzanmalı

Yeni projeler için neredeyse hiç. Belirli istisnalar:

- Girdiyi sınırlı bellekle her seferinde bir token tükettiğin streaming çeviri.
- Transformer bellek maliyetinin yasak olduğu cihaz üzerinde metin üretimi.
- Pedagoji. Encoder-decoder darboğazını anlamak, transformer'ların neden kazandığını anlamanın en hızlı yoludur.

### Exposure bias ve azaltımları

- **Scheduled sampling.** Teacher forcing oranını eğitim sırasında yumuşat, böylece model kendi hatalarından toparlanmayı öğrenir.
- **Minimum risk training.** Token seviyesi cross-entropy yerine cümle seviyesi BLEU skoru üzerinde eğit. Gerçekten istediğine daha yakın.
- **Reinforcement learning fine-tuning.** Dizi üreticisini bir metrikle ödüllendir. Modern LLM RLHF'inde kullanılır.

Üçü de transformer tabanlı üretime hâlâ uygulanır.

## Yayınla

`outputs/prompt-seq2seq-design.md` olarak kaydet:

```markdown
---
name: seq2seq-design
description: Design a sequence-to-sequence pipeline for a given task.
phase: 5
lesson: 09
---

Given a task (translation, summarization, paraphrase, question rewrite), output:

1. Architecture. Pretrained transformer encoder-decoder (BART, T5, mBART, NLLB) is the default. RNN-based seq2seq only for specific constraints.
2. Starting checkpoint. Name it (`facebook/bart-base`, `google/flan-t5-base`, `facebook/nllb-200-distilled-600M`). Match the checkpoint to task and language coverage.
3. Decoding strategy. Greedy for deterministic output, beam search (width 4-5) for quality, sampling with temperature for diversity. One sentence justification.
4. One failure mode to verify before shipping. Exposure bias manifests as generation drift on longer outputs; sample 20 outputs at the 90th-percentile length and eyeball.

Refuse to recommend training a seq2seq from scratch for under a million parallel examples. Flag any pipeline that uses greedy decoding for user-facing content as fragile (greedy repeats and loops).
```

## Alıştırmalar

1. **Kolay.** Oyuncak kopyalama görevini uygula. Hedefin kaynağa eşit olduğu input-output çiftleri üzerinde bir GRU seq2seq eğit. 5, 10, 20 uzunluklarında doğruluğu ölç. Darboğazı yeniden üret.
2. **Orta.** 3 beam genişliğinde beam search decoding ekle. Küçük bir paralel corpus üzerinde greedy'ye karşı BLEU ölç. Beam search'ün nerede kazandığını (genellikle son token'lar) ve nerede fark yaratmadığını belgele.
3. **Zor.** `facebook/bart-base`'i 10k çiftlik bir paraphrase veri setinde fine-tune et. Fine-tune edilmiş modelin beam-4 çıktısını held-out girdilerde base modelininkiyle karşılaştır. BLEU raporla ve 10 niteliksel örnek seç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Encoder | Girdi RNN'i | Kaynağı okur. Adım başına hidden state'ler ve bir final context vektörü üretir. |
| Decoder | Çıktı RNN'i | Context vektöründen başlatılır. Hedef token'ları teker teker üretir. |
| Context vektörü | Özet | Final encoder hidden state'i. Sabit boyut. Attention'ın çözdüğü darboğaz. |
| Teacher forcing | Gerçek token'ları kullan | Eğitim zamanında ground-truth önceki token'ı besle. Öğrenmeyi stabilize eder. |
| Exposure bias | Train/test açığı | Gerçek token'larda eğitilmiş model kendi hatalarından toparlanmayı asla pratik etmedi. |
| Beam search | Daha iyi decoding | Greedy şekilde bağlanmak yerine her adımda top-k parçalı diziyi canlı tut. |

## İleri Okuma

- [Sutskever, Vinyals, Le (2014). Sequence to Sequence Learning with Neural Networks](https://arxiv.org/abs/1409.3215) — orijinal seq2seq makalesi. Dört sayfa.
- [Cho et al. (2014). Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation](https://arxiv.org/abs/1406.1078) — GRU'yu ve encoder-decoder çerçevesini tanıttı.
- [Bahdanau, Cho, Bengio (2014). Neural Machine Translation by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473) — attention makalesi. Bu dersten hemen sonra oku.
- [PyTorch NLP from Scratch tutorial](https://pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html) — inşa edilebilir seq2seq + attention kodu.
