---
name: skill-ctc-decoder
description: Length normalization dahil sıfırdan greedy ve beam-search CTC decoder yaz
version: 1.0.0
phase: 4
lesson: 19
tags: [ocr, ctc, decoding, sequence-models]
---

# CTC Decoder

CTC çıktıları için iki decoding rutini üret: greedy (hızlı) ve beam (gürültülü girdilerde daha iyi).

## Ne zaman kullan

- Custom CRNN çıktıları üzerinde OCR çıkarımı çalıştırırken.
- Pretrained bir OCR modelini farklı decoder'lara karşı benchmark ederken.
- ctcdecode çekmeden basit bir beam search implement ederken.

## Girdiler

- `log_probs`: (T, N, C) vocab üzerinde log-softmax (konvansiyonel olarak index 0 = blank).
- `vocab`: C karakter listesi.
- `beam_width` (sadece beam): tipik 5-10.

## Greedy decoder

```python
def greedy_ctc_decode(log_probs, vocab, blank=0):
    preds = log_probs.argmax(dim=-1).transpose(0, 1).cpu().tolist()
    out = []
    for seq in preds:
        decoded = []
        prev = None
        for idx in seq:
            if idx != prev and idx != blank:
                decoded.append(vocab[idx])
            prev = idx
        out.append("".join(decoded))
    return out
```

## Beam search decoder

```python
import heapq
import math

def beam_ctc_decode(log_probs, vocab, beam_width=5, blank=0):
    T, N, C = log_probs.shape
    lp = log_probs.cpu()
    results = []
    for n in range(N):
        beams = {("",): (0.0, -math.inf)}  # (prefix_tuple) -> (p_blank, p_nonblank)
        for t in range(T):
            logits_t = lp[t, n]
            new_beams = {}
            for prefix, (p_b, p_nb) in beams.items():
                for c in range(C):
                    p = logits_t[c].item()
                    if c == blank:
                        nb = p_b + p
                        nnb = p_nb + p
                        upd = new_beams.get(prefix, (-math.inf, -math.inf))
                        new_beams[prefix] = (
                            _logsumexp(upd[0], _logsumexp(nb, nnb)),
                            upd[1],
                        )
                    else:
                        last = prefix[-1] if prefix else ""
                        char = vocab[c]
                        if char == last:
                            # Case 1: aynı prefix'te kal (p_nb'den collapse)
                            upd = new_beams.get(prefix, (-math.inf, -math.inf))
                            new_beams[prefix] = (upd[0], _logsumexp(upd[1], p_nb + p))
                            # Case 2: blank-ayrımlı tekrarla prefix'i genişlet ("a_a" -> "aa")
                            new_prefix = prefix + (char,)
                            upd = new_beams.get(new_prefix, (-math.inf, -math.inf))
                            new_beams[new_prefix] = (upd[0], _logsumexp(upd[1], p_b + p))
                        else:
                            new_prefix = prefix + (char,)
                            upd = new_beams.get(new_prefix, (-math.inf, -math.inf))
                            nb = _logsumexp(p_b, p_nb) + p
                            new_beams[new_prefix] = (upd[0], _logsumexp(upd[1], nb))
            beams = dict(heapq.nlargest(
                beam_width,
                new_beams.items(),
                key=lambda kv: _logsumexp(kv[1][0], kv[1][1]),
            ))
        best = max(beams.items(), key=lambda kv: _logsumexp(kv[1][0], kv[1][1]))[0]
        results.append("".join(best))
    return results


def _logsumexp(a, b):
    if a == -math.inf: return b
    if b == -math.inf: return a
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))
```

## Kurallar

- CTC'deki blank index PyTorch'un `nn.CTCLoss`'unda konvansiyonel olarak 0'dır.
- Beam search düşük güvenli girdilerde accuracy'yi iyileştirir; temiz girdilerde iyileşme <%1 CER'dir.
- Beam'i asla 5'in altına budama; accuracy-latency trade'i altında düzleşir.
- Sıkı bir latency bütçesi içinde beam search çalıştırırken, greedy'e düş; çoğu production OCR verisinde kalite kaybı küçüktür.
- Büyük vocabulary'ler için (3000+ karakter olan CJK), yukarıdaki saf Python yerine `ctcdecode` (C++)'a geç; Python beam hızla darboğaz olur.
