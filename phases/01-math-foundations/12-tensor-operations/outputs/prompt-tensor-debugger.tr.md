---
name: prompt-tensor-debugger
description: Deep learning kodundaki tensor shape hatalarını adım adım debug etme prompt'u
phase: 1
lesson: 12
---

Deep learning kodumda bir tensor shape hatası var. Düzeltmeme yardım et.

**Hata mesajı:** [hatayı buraya yapıştır]

**Tensor shape'lerim:**
- [isim]: [shape]
- [isim]: [shape]

**Yapmaya çalıştığım operasyon:** [açıkla]

---

Debug ederken bu kesin süreci izle:

**Adım 1: Operasyon tipini belirle.**
Hangi operasyon hata üretti? Şunlardan birine eşle:
- Matris çarpımı / Linear katman (iç boyutlar eşleşmeli)
- Broadcasting (sağdan hizala, her boyut eşit ya da 1 olmalı)
- Concatenation (cat boyutu hariç tüm boyutlar eşleşmeli)
- Convolution (spesifik rank ve kanal pozisyonu bekler)
- Reshape (toplam eleman sayısı korunmalı)

**Adım 2: Shape kontratını yaz.**
Belirlenen operasyon için beklenen shape'leri açıkça yaz:
```
matmul(A, B): A (..., m, k), B (..., k, n) -> (..., m, n)
broadcast(A, B): sağdan hizala, her çift (eşit) ya da (biri 1) olmalı
cat([A, B], dim=d): dim d hariç tüm boyutlar eşleşmeli
Linear(in_f, out_f): girdinin son boyutu in_f'e eşit olmalı
Conv2d(in_c, out_c, k): girdi (B, in_c, H, W) olmalı
```

**Adım 3: Uyumsuzluğu bul.**
Gerçek shape'leri kontratla karşılaştır. Kuralı ihlal eden tam boyutu belirle.

**Adım 4: Minimal çözümü seç.**
Şu tablodan seç:

| Belirti | Çözüm |
|---|---|
| Eksik batch boyutu | `.unsqueeze(0)` |
| Eksik channel boyutu | `.unsqueeze(1)` |
| Fazladan size-1 boyut | `.squeeze(dim)` |
| matmul için iç boyutlar yanlış | `.transpose(-1, -2)` ya da weight shape'i kontrol et |
| NHWC'den NCHW gerek | `.permute(0, 3, 1, 2)` |
| NCHW'den NHWC gerek | `.permute(0, 2, 3, 1)` |
| Linear için spatial boyutları düzleştir | `.flatten(1)` ya da `.reshape(B, -1)` |
| Head'leri böl: (B,T,D)'den (B,H,T,D/H)'ye | `.reshape(B, T, H, D//H).transpose(1, 2)` |
| Head'leri birleştir: (B,H,T,D/H)'den (B,T,D)'ye | `.transpose(1, 2).reshape(B, T, H*(D//H))` |
| Non-contiguous tensor ile .view() | `.contiguous().view(...)` ya da `.reshape(...)` kullan |

**Adım 5: Çözümü doğrula.**
Her adımda ortaya çıkan shape'leri göster. Reshape boyunca toplam elemanların korunduğunu doğrula. Operasyonun shape kontratının artık sağlandığını doğrula.

**Adım 6: Sessiz (silent) bug'ları kontrol et.**
Shape'ler eşleşse bile şunları doğrula:
- Broadcasting istenen eksen boyunca oluyor (kazara değil)
- Reduction doğru boyut üzerinde toplam alıyor
- Batch boyutu (dim 0) tüm forward pass boyunca sağ kalıyor
- Boyut sıralaması önemli olduğunda transpose + reshape kullanılıyor (sadece reshape değil)

Yanıtını şu formatla ver:
```
OPERATION: [hangi operasyon başarısız oldu]
EXPECTED: [shape kontratı]
ACTUAL: [verilen shape'ler]
MISMATCH: [hangi boyut, neden]
FIX: [tam kod]
RESULT: [çözümden sonraki shape'ler]
```
