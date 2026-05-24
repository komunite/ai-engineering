---
name: skill-recall-at-k-runner
description: Train/val/gallery split'leri ve uygun veri kontratı ile recall@K için temiz bir değerlendirme harness'ı yaz
version: 1.0.0
phase: 4
lesson: 20
tags: [retrieval, evaluation, recall, faiss]
---

# Recall@K Runner

Bir query ve gallery görsel klasörünü artı etiketleri tekrarlanabilir bir recall@K sayısına çevir.

## Ne zaman kullan

- Yeni bir backbone için ilk retrieval benchmark'ı.
- Fine-tune epoch'larında embedding kalitesini izlerken.
- Aynı dataset'te iki retrieval sistemini karşılaştırırken.

## Girdiler

- `query_images`: path listesi.
- `gallery_images`: path listesi (query çakışabilir ya da çakışmayabilir).
- `query_labels`, `gallery_labels`: sınıf ya da instance ID'leri.
- `encoder_fn`: `image -> embedding` callable'ı (önceden hesaplanmış ya da canlı).
- `ks`: `[1, 5, 10]` gibi liste.

## Adımlar

1. Her gallery görselini bir kez encode et. numpy array olarak kaydet.
2. Her query görselini encode et.
3. İki embedding setini de L2-normalize et.
4. Her query için, tüm gallery item'larına karşı similarity hesapla.
5. Azalan sırala, top max(ks) al.
6. Her K için, top-K gallery item'larından herhangi birinin query'nin etiketini paylaşıp paylaşmadığını kontrol et.
7. `recall@K = top K içinde en az bir doğru komşusu olan query oranı` raporla.

## Çıktı şablonu

```python
import numpy as np
from sklearn.preprocessing import normalize

def encode_all(images, encoder_fn, batch=32):
    out = []
    for i in range(0, len(images), batch):
        embs = encoder_fn(images[i:i + batch])
        out.append(embs)
    return np.concatenate(out)


def recall_at_k(query_emb, gallery_emb, q_labels, g_labels,
                ks=(1, 5, 10), query_ids=None, gallery_ids=None):
    if len(query_emb) == 0 or len(gallery_emb) == 0:
        return {f"recall@{k}": 0.0 for k in ks}

    g_label_set = set(g_labels.tolist())
    keep = np.array([lbl in g_label_set for lbl in q_labels])
    if not keep.any():
        return {f"recall@{k}": 0.0 for k in ks}

    q_emb_f = query_emb[keep]
    q_lab_f = q_labels[keep]
    q_id_f = query_ids[keep] if query_ids is not None else None

    q = normalize(q_emb_f)
    g = normalize(gallery_emb)
    sims = q @ g.T

    if q_id_f is not None and gallery_ids is not None:
        self_mask = q_id_f[:, None] == gallery_ids[None, :]
        sims = np.where(self_mask, -np.inf, sims)

    top_k_max = min(max(ks), g.shape[0])
    if top_k_max <= 0:
        return {f"recall@{k}": 0.0 for k in ks}

    top = np.argpartition(-sims, top_k_max - 1, axis=1)[:, :top_k_max]
    sorted_top = np.take_along_axis(
        top, np.argsort(-sims[np.arange(len(q))[:, None], top], axis=1), axis=1
    )
    out = {}
    for k in ks:
        k_eff = min(k, top_k_max)
        hits = np.any(g_labels[sorted_top[:, :k_eff]] == q_lab_f[:, None], axis=1)
        out[f"recall@{k}"] = float(hits.mean())
    return out


def evaluate(query_images, query_labels, gallery_images, gallery_labels, encoder_fn, ks=(1, 5, 10)):
    q_emb = encode_all(query_images, encoder_fn)
    g_emb = encode_all(gallery_images, encoder_fn)
    return recall_at_k(q_emb, g_emb, np.array(query_labels), np.array(gallery_labels), ks)
```

## Rapor

```
[evaluation]
  num queries:   <int>
  num gallery:   <int>
  embedding_dim: <int>

[recall]
  recall@1:  <float>
  recall@5:  <float>
  recall@10: <float>
```

## Kurallar

- Similarity hesaplamadan önce embedding'leri normalize et; normalize edilmiş vektörler üzerinde FAISS IndexFlatIP cosine'a eşit.
- Bir query'nin ground-truth etiketi gallery'de yoksa, hariç tut; aksi halde recall trivial olarak 1'in altında kapanır.
- Query ve gallery çakışıyorsa, kendi top-K'sından query'yi hariç tut yoksa retrieval değil self-similarity ölçersin.
- `num_queries > 10,000` için, OOM'dan kaçınmak için similarity matmul'unu batch'le.
```
