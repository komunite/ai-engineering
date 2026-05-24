# Show-o ve Discrete-Diffusion Birleştirilmiş Modeller

> Transfusion sürekli ve ayrık temsilleri karıştırır. Show-o (Xie et al., Ağustos 2024) diğer yöne gider: metin token'ları causal next-token prediction kullanır, görsel token'ları MaskGIT ruhunda masked discrete diffusion kullanır. İkisi de hibrit attention mask'ı ile tek transformer içinde oturur. Sonuç VQA, text-to-image, inpainting ve karışık-modalite üretimini tek backbone'da, modalite başına tek tokenizer'da, tek loss formülasyonunda (masked prediction'a genişletilmiş next-token) birleştirir. Bu ders Show-o tasarımını yürüyor — masked discrete diffusion'ın neden paralel, az adımlı bir görsel üretici olduğu — ve Transfusion ve Emu3 ile karşıtlık kurar.

**Tür:** Öğrenim
**Diller:** Python (stdlib, masked-discrete-diffusion sampler)
**Ön koşullar:** Faz 12 · 13 (Transfusion)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Masked discrete diffusion'ı açıkla: token'ları uniform mask'leyen sonra transformer'dan onları kurtarmasını isteyen program.
- Paralel görsel decoding'i (Show-o, MaskGIT) autoregressive görsel decoding (Chameleon, Emu3) ile hız ve kalitede karşılaştır.
- Show-o'nun tek checkpoint'te ele aldığı üç görevi söyle: T2I, VQA, image inpainting.
- Bir masking programı (cosine, linear, truncated) seç ve örnek kalitesine etkisi hakkında akıl yürüt.

## Sorun

Transfusion'ın iki-loss eğitimi çalışır ama daha zor dinamiklere sahip — sürekli diffusion loss ayrık NTP loss'tan farklı bir sayısal ölçekte yaşar. Loss ağırlıklarını dengelemek bir hyperparameter aramasıdır. Mimari etkili ama karmaşık.

Show-o'nun cevabı: iki modaliteyi de ayrık tut (Chameleon gibi), ama görselleri sıralı yerine masked discrete diffusion üzerinden paralel üret. Eğitim objective'i next-token prediction'ı doğal olarak genelleyen tek bir masked-token-prediction olur.

## Kavram

### Masked discrete diffusion (MaskGIT)

Orijinal Chang et al. (2022) MaskGIT hilesi zarif. Tamamen mask'lenmiş bir görselden başla (her token özel `<MASK>` id'si). Her adımda tüm mask'lenmiş token'ları paralel tahmin et, sonra en güvenli K tahmini tut ve geri kalanı yeniden mask'le. ~8-16 iterasyon sonra tüm token'lar doldurulur. Adım başına kaç token unmask edileceğinin programı tune edilir — cosine program iyi çalışır.

Eğitim basit: [0, 1]'den uniform bir masking oranı örnekle, görselin VQ token'larına uygula, transformer'ı mask'lenenleri kurtarmak için eğit. Tam olarak BERT'in metin için yaptığı, görsel üretimine ölçeklenmiş.

### Show-o: tek transformer, hibrit mask

Show-o MaskGIT'i causal-language-model bir transformer içine koyar. Attention mask:

- Metin token'ları: causal (standart LLM).
- Görsel token'ları: görsel block içinde tam bidirectional (böylece mask'lenmiş token'lar tahmin sırasında her diğer görsel token'ı görebilir).
- Text-to-image: metin önceki görsellere attend eder, görsel önceki metne attend eder.

Eğitim şunlar arasında değişir:
1. Metin dizilerinde standart NTP.
2. T2I örnekleri: mask'lenmiş görsel token'lar ile metin → görsel, masked-token-prediction loss.
3. VQA örnekleri: mask'lenmiş metin token'ları ile görsel → metin (gerçekten yalnızca NTP).

Birleştirilmiş loss `<MASK>` token'larında cross-entropy, hem metin NTP'sini (yalnızca son token "mask'li") hem görsel masked-diffusion'ı (rastgele alt küme mask'li) kapsar.

### Paralel sampling

Show-o bir görseli ~1000 yerine (token başına autoregressive) ya da ~20 (diffusion) yerine ~16 adımda üretir. Her adımda tüm mask'lenmiş token'ları paralel tahmin et; en güvenli K'yı commit et; tekrarla.

Karşılaştır:
- Chameleon / Emu3 (token üzerinde autoregressive): N_tokens forward pass, görsel başına tipik 1024-4096.
- Transfusion (sürekli diffusion): ~20 adım, her biri tam transformer pass'i.
- Show-o (masked discrete diffusion): ~16 adım, her biri tam transformer pass'i.

Show-o benzer ölçek modellerde Chameleon'dan daha hızlı, kabaca Transfusion adım sayısını eşler, adım başına daha düşük maliyetle (sürekli MSE loss yerine ayrık vocab logit'leri).

### Tek checkpoint'te görevler

Show-o çıkarımda prompt formatı tarafından seçilen dört görevi destekler:

- Metin üretimi: standart autoregressive metin çıkışı.
- VQA: görsel girer, metin çıkar.
- T2I: metin girer, masked discrete diffusion üzerinden görsel çıkar.
- Inpainting: bazı token'ları mask'li görsel, doldur.

Inpainting yeteneği masked-prediction eğitiminden bedava gelir. VQ-token grid'inin bir bölgesini mask'le, geri kalanını artı bir metin prompt'unu besle, mask'lenmiş token'ları tahmin et.

### Masking programı

Adım başına kaç token unmask edileceğinin programı kaliteyi şekillendirir. Show-o cosine öneriyor:

```
mask_ratio(t) = cos(pi * t / (2 * T))   # t = 0..T
```

Adım 0'da tüm token'lar mask'li (oran 1.0). Adım T'de hiçbiri mask'li değil. Cosine kütleyi tahminin en bilgilendirici olduğu orta-aralık oranlara yoğunlaştırır. Lineer programlar da çalışır ama daha hızlı plato yapar.

### Show-o2

Show-o2 (2025 takibi, arXiv 2506.15564) Show-o'yu ölçekler: daha büyük LLM base, daha iyi tokenizer, geliştirilmiş mask programı. Aynı mimari kalıp.

### Show-o nerede oturur

2026 taksonomisinde:

- Ayrık token + NTP: Chameleon, Emu3. Basit ama yavaş çıkarım.
- Ayrık token + masked diffusion: Show-o, MaskGIT, LlamaGen, Muse. Paralel sampling, hâlâ tokenizer ile kayıplı.
- Sürekli + diffusion: Transfusion, MMDiT, DiT. En yüksek kalite, daha karmaşık eğitim.
- VLM'de sürekli + flow matching: JanusFlow, InternVL-U. En yeni.

Göreve göre seç: tek açık modelde T2I + inpainting + VQA'ya makul hızda istediğinde Show-o; kalite önceliklendiğinde ve iki-loss tesisatı karşılayabildiğinde Transfusion.

## Kullan

`code/main.py` Show-o sampling'i simüle eder:

- 16 VQ token'lı oyuncak grid.
- Bir prompt ve şu an unmask edilmiş token'lara göre logit tahmin eden mock "transformer".
- 8 adım üzerinde cosine program ile paralel masked sampling.
- Ara durumları (mask kalıbı evrimi) ve son token'ları yazdırır.

Çalıştır, mask'ın adım adım eridiğini izle.

## Yayınla

Bu ders `outputs/skill-unified-gen-model-picker.md` üretir. Hem anlama (VQA, captioning) hem üretim (T2I, inpainting) gerektiren açık-ağırlık kısıtlı bir ürün verildiğinde, Show-o ailesi, Transfusion/MMDiT ailesi ve Emu3 / Chameleon ailesi arasından somut trade-off'larla seçer.

## Alıştırmalar

1. Masked discrete diffusion ~16 adımda örnek alır. Neden 1 değil? Adım 0'da her şeyi unmask edersen ne kırılır?

2. Inpainting masked diffusion ile bedava. Show-o'nun inpainting'inin uzman bir modeli yendiği bir ürün kullanım durumu (gerçek ya da hipotetik) öner.

3. Cosine program vs lineer program: T=8 için adım başına unmask edilen token sayısını izle. Hangisi daha dengeli?

4. 512x512 bir Show-o görseli 1024 token. K=16384 vocab'ta, model 1024 * log2(16384) = 14,336 bit (~1.75 KiB) veri yayar. Stable Diffusion 512*512*24 bit = 6,291,456 bit (~768 KiB) ham piksel çıkarır. Sıkıştırma oranı nedir ve hangi kaliteyi satın alır?

5. LlamaGen'i (arXiv:2406.06525) oku. LlamaGen'in sınıf-koşullu autoregressive görsel modeli Show-o'nun masked yaklaşımından nasıl farklı?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Masked discrete diffusion | "MaskGIT tarzı" | Mask'lenmiş token'ları tahmin etmek için eğitim; çıkarımda en güvenli tahminleri iteratif unmask et |
| Cosine program | "Unmask programı" | Çıkarım adımları üzerinde mask oranı azalması; güven büyümesini orta-aralıkta yoğunlaştırır |
| Paralel decoding | "Tüm token'lar bir kerede" | Her adım mask'lenmiş token'ların tam dizisini tek forward pass'te tahmin eder, sonra top-K commit eder |
| Hibrit attention | "Causal + bidirectional" | Metin token'ları üzerinde causal, görsel block'lar içinde bidirectional olan mask |
| Inpainting | "Doldur üretimi" | Bazı token'ları mask'li görsele koşullu, eksik olanları tahmin et; eğitim objective'inden bedava |
| Commitment rate | "Adım başına top-K" | İterasyon başına "tamam" ilan edilen token sayısı; çıkarım vs kalite trade-off'unu kontrol eder |

## İleri Okuma

- [Xie et al. — Show-o (arXiv:2408.12528)](https://arxiv.org/abs/2408.12528)
- [Show-o2 (arXiv:2506.15564)](https://arxiv.org/abs/2506.15564)
- [Chang et al. — MaskGIT (arXiv:2202.04200)](https://arxiv.org/abs/2202.04200)
- [Sun et al. — LlamaGen (arXiv:2406.06525)](https://arxiv.org/abs/2406.06525)
- [Chang et al. — Muse (arXiv:2301.00704)](https://arxiv.org/abs/2301.00704)
