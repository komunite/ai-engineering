---
name: skill-cmer-monitor
description: Bir production VLM endpoint'ini Cross-Modal Error Rate monitoring, dashboard ve alert'lerle enstrüman et
version: 1.0.0
phase: 4
lesson: 25
tags: [vlm, production, monitoring, hallucination]
---

# CMER Monitor

Cross-modal alignment'ı first-class production KPI olarak ele al.

## Ne zaman kullan

- Görseller üzerine grounding'li metin üreten herhangi bir VLM endpoint'i deploy ederken.
- Halüsinasyon yanıt raporlarını araştırırken.
- Bir girdi dağılım kaymasının model grounding'ini bozup bozmadığını izlerken.

## Girdiler

- `vlm_output`: üretilen metin.
- `text_confidence`: softmax sonrası ortalama token başına olasılık, `[0, 1]`'de. `exp(mean(log_probs))` olarak hesapla. Ham logit geçirme; ham logitler sınırsızdır ve `conf_threshold` bir olasılığı varsayar.
- `image_embedding`: görselin CLIP ailesi embedding'i (DINOv3, SigLIP, CLIP).
- `text_embedding`: üretilen metnin CLIP ailesi embedding'i.
- Opsiyonel `prompt_type`: gruplama için etiket (vqa / ocr / captioning / agent).

## Request başına hesaplama

```python
import torch

def cmer_flag(image_emb, text_emb, text_conf, sim_thr=0.25, conf_thr=0.8):
    if image_emb.shape != text_emb.shape:
        raise ValueError(f"emb shape mismatch: {image_emb.shape} vs {text_emb.shape}")
    image_emb = image_emb / (image_emb.norm() + 1e-8)
    text_emb = text_emb / (text_emb.norm() + 1e-8)
    sim = float((image_emb * text_emb).sum())
    flagged = (text_conf > conf_thr) and (sim < sim_thr)
    return {"sim": sim, "flagged": flagged}
```

Embedding'ler bağımsız bir CLIP ailesi encoder'dan 1-D PyTorch tensor'ları (`torch.float32`). NumPy array kullanırsan, `.norm()`'u `np.linalg.norm(...)` ile değiştir ve çıktıyı uygun şekilde cast et.

`sim`, `text_conf`, `flagged`, `prompt_type`, `timestamp`, `model_version`, `request_id`'yi monitoring pipeline'ına (Prometheus, DataDog, OpenTelemetry) kaydet.

## Toplam metrik

```
CMER = (pencerede flag'lenmiş request) / (pencerede toplam request)
```

Endpoint başına, prompt_type başına, model versiyonu başına raporla.

## Alert eşikleri

- Baseline CMER: 7 gün normal trafik üzerinde kur.
- Warning: 1 saat boyunca CMER >= 1.5x baseline.
- Critical: 30 dakika boyunca CMER >= 2x baseline ya da herhangi pencerede > %15 mutlak.

## Dashboard panelleri

1. Zaman üzerinde CMER (5 dakika bucket, 7 gün pencere).
2. prompt_type'a göre CMER (stacked bar).
3. Saat başına `sim` dağılımı (histogram).
4. En çok halüsinasyon olan çıktılar (gün başına 20 flag'li yanıtı insan incelemesi için örnekle).

## CMER zirve yaptığında aksiyonlar

1. Flag'lenmiş request'leri örnekle.
2. Model versiyonunun istemsiz değişmediğini doğrula.
3. Girdi dağılımını kontrol et (yeni dosya formatı? yeni görsel kaynağı? farklı sıkıştırılmış?).
4. Zirve çözülene kadar etkilenen trafiği insan incelemesine yönlendir.
5. Zirve kalıcıysa, modeli fine-tune et ya da değiştir; alert'i bastırma.

## Kurallar

- CMER'i asla VLM'in kendi embedding'leriyle hesaplama; bağımsız bir encoder (DINOv3, SigLIP ya da CLIP-L/14) kullan. Aksi halde alignment'ı değil modelin kendi tutarlılığını ölçersin.
- Sadece `flagged` bit'ini değil, ham `sim` değerini her zaman logla; dağılım kaymaları flag oranı değişmeden önce alt çeyrekte görünür.
- CMER monitoring olmadan VLM endpoint ship etme; halüsinasyonlar baskın production failure mode ve bu metrik olmadan sessizdir.
- Hassas alanlar için (medikal, hukuki, finansal), `sim_threshold`'u 0.35 ya da daha yükseğe yükselt; flag koşulu `sim < sim_threshold`, dolayısıyla daha yüksek eşik daha çok çıktıyı potansiyel olarak grounding'siz yakalar — yüksek riskli kullanım için doğru varsayılan.
