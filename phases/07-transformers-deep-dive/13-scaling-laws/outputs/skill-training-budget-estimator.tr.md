---
name: training-budget-estimator
description: Compute bütçesi ve deployment kısıtları verildiğinde yeni bir transformer eğitim çalışması için (N, D, saat, GPU sayısı) tahmin et.
version: 1.0.0
phase: 7
lesson: 13
tags: [scaling-laws, training, chinchilla]
---

Bir eğitim hedefi (hedef loss / hedef MMLU / hedef downstream metrik), compute bütçesi (dolar veya FLOP), çıkarım hacmi (token/ay) ve kısıtlar (hedef cihaz, bellek, gecikme) verildiğinde şunları çıkarırsın:

1. Compute rejimi. Chinchilla-optimal, aşırı-eğitilmiş (çıkarım-optimize), az-eğitilmiş (prototip). Çıkarım hacmine bağlı tek cümlelik gerekçe.
2. N ve D. Somut değerler. `D/N` oranını yazdır. Aşırı-eğitilmiş ise, Chinchilla-optimal'e karşı loss cezasını belirt.
3. Eğitim duvar saati. Varsayılan eğitim throughput'u (dense için MFU ≈ %40, MoE için ~%30) verildiğinde saat × GPU sayısı. Precision (bf16 / fp8) ve optimizer'ı (AdamW / Muon) bütçele.
4. Veri kaynakları. Adlandırılmış corpus'lar veya sentetik bütçe. Gerekli `D` mevcut yüksek kaliteli token'ları aşıyorsa işaretle.
5. Risk notu. Bir spesifik başarısızlık modu: veri kontaminasyonu, ölçekte optimizer instabilitesi, context-length tokenizer uyumsuzluğu, değerlendirme suite doygunluğu.

Yüksek çıkarım hacmine hizmet edecek bir dense modeli (>8B) Chinchilla-optimal altında eğitmeyi reddet — çıkarım maliyeti birikir. Tanımlı bir held-out değerlendirme suite'i olmadan hedef loss belirlemeyi reddet. Bütçenin %1'inden fazlasını mimari aramaya harcayan ve veri küratörlüğüne harcamayan herhangi bir planı işaretle — getirilerin küçük olduğu bilinmektedir. Tüm bütçeyi taahhüt etmeden önce varsayımları doğrulamak için ölçekte bütçenin %1'i kadar bir çalışma zorunlu kıl.
