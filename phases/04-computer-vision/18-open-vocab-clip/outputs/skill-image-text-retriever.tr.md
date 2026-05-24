---
name: skill-image-text-retriever
description: Herhangi bir CLIP checkpoint ile bir görsel embedding index'i inşa et; metinle ve görselle sorguyu destekle
version: 1.0.0
phase: 4
lesson: 18
tags: [clip, retrieval, faiss, zero-shot]
---

# Image-Text Retriever

Bir görsel klasörünü CLIP embedding'ler kullanarak aranabilir bir index'e çevir.

## Ne zaman kullan

- İç bir katalog üzerinde zero-shot görsel arama inşa ederken.
- Embedding mesafesine göre neredeyse aynı görselleri deduplicate ederken.
- Etiketli dataset olmadan hızlı bir "benzer bul" bileşeni inşa ederken.

## Girdiler

- `image_folder`: görsel dosya dizini.
- `clip_model`: `openai/clip-vit-base-patch32` ya da `google/siglip-base-patch16-224` gibi HuggingFace id.
- `index_type`: flat | IVF | HNSW.
- `embedding_dim`: modelden çıkarılır.

## Adımlar

1. CLIP modelini ve preprocessor'ı yükle.
2. Klasördeki her görseli batch-encode et. Embedding'leri (N, D) float32 + dosya adı listesi olarak kaydet.
3. Embedding'ler üzerinde FAISS index inşa et. Cosine similarity için L2-normalize edilmiş vektörler üzerinde inner-product kullan.
4. İki sorgu arayüzü sun:
   - `search_by_text(text, k)` — metni embed et, ara.
   - `search_by_image(image_path, k)` — görseli embed et, ara.

## Çıktı şablonu

```python
import os
import glob
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
import faiss


class ImageTextRetriever:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.dim = self.model.config.projection_dim
        self.index = None
        self.filenames = []

    @torch.no_grad()
    def _encode_images(self, paths, batch=16):
        embs = []
        for i in range(0, len(paths), batch):
            imgs = [Image.open(p).convert("RGB") for p in paths[i:i + batch]]
            inputs = self.processor(images=imgs, return_tensors="pt")
            out = self.model.get_image_features(**inputs)
            out = out / out.norm(dim=-1, keepdim=True)
            embs.append(out.cpu().numpy())
        return np.concatenate(embs).astype(np.float32)

    @torch.no_grad()
    def _encode_text(self, texts):
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        out = self.model.get_text_features(**inputs)
        out = out / out.norm(dim=-1, keepdim=True)
        return out.cpu().numpy().astype(np.float32)

    def build_index(self, folder, index_type="flat"):
        exts = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(folder, ext)))
        self.filenames = sorted(files)
        embs = self._encode_images(self.filenames)
        if index_type == "IVF":
            quantizer = faiss.IndexFlatIP(self.dim)
            nlist = min(256, max(4, len(embs) // 32))
            self.index = faiss.IndexIVFFlat(quantizer, self.dim, nlist)
            self.index.train(embs)
        elif index_type == "HNSW":
            self.index = faiss.IndexHNSWFlat(self.dim, 32, faiss.METRIC_INNER_PRODUCT)
        else:
            self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embs)

    def search_by_text(self, text, k=5):
        q = self._encode_text([text])
        dist, idx = self.index.search(q, k)
        return [(self.filenames[i], float(d)) for d, i in zip(dist[0], idx[0])]

    def search_by_image(self, image_path, k=5):
        q = self._encode_images([image_path])
        dist, idx = self.index.search(q, k)
        return [(self.filenames[i], float(d)) for d, i in zip(dist[0], idx[0])]
```

## Rapor

```
[retriever]
  model:          <name>
  num_images:     <int>
  dim:            <int>
  index_type:     flat | IVF | HNSW
  index_size_mb:  <float>
```

## Kurallar

- Index'leme öncesi embedding'leri her zaman L2-normalize et; normalize edilmiş vektörler üzerinde FAISS'in inner product'ı cosine similarity'ye eşit.
- < 100k görsel için, `IndexFlatIP` (exact) en basit ve en hızlı.
- 100k-10M için, `IndexIVFFlat` standart trade-off.
- > 10M için, HNSW ya da product-quantised bir varyant kullan.
- Her sorguda index'i asla yeniden inşa etme; bir kez embed et, birçok kez ara.
