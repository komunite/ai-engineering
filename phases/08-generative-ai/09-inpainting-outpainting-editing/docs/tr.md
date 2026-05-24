# Inpainting, Outpainting ve Görsel Düzenleme

> Text-to-image yeni şeyler üretir. Inpainting eskileri düzeltir. Üretimde, faturalanabilir görsel işinin %70'i düzenleme — arka planı değiştir, logo kaldır, canvas'ı uzat, eli yeniden üret. Diffusion'ın ekmek parasını kazandığı yer inpainting.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 07 (Latent Diffusion), Faz 8 · 08 (ControlNet ve LoRA)
**Süre:** ~75 dakika

## Sorun

Bir müşteri arka planda dikkat dağıtıcı bir tabela olan mükemmel bir ürün fotoğrafı gönderiyor. Tabelayı silmek ve geri kalan her şeyi piksel-aynı bırakmak istiyorsun. Sıfırdan text-to-image çalıştıramazsın — sonuç farklı renge, farklı aydınlatmaya, farklı ürün açısına sahip olur. *Sadece* maskelenen bölgeyi yeniden üretmek ve yeniden üretimin çevredeki bağlama saygı duymasını istiyorsun.

Bu inpainting. Varyantlar:

- **Inpainting.** Mask içini yeniden üret, dış pikselleri koru.
- **Outpainting.** Mask dışını (ya da canvas'ın ötesini) yeniden üret, içi koru.
- **Görsel düzenleme.** Tüm görseli yeniden üret ama orijinale semantik ya da yapısal sadakati koru (SDEdit, InstructPix2Pix).

2026'da her diffusion pipeline'ı bir inpainting modu ship eder. Flux.1-Fill, Stable Diffusion Inpaint, SDXL-Inpaint, DALL-E 3 Edit. Aynı prensipte çalışırlar.

## Kavram

![Inpainting: bağlam koruyan yeniden enjeksiyonlu mask-bilinçli denoising](../assets/inpainting.svg)

### Naif yaklaşım (ve neden yanlış)

Mask ile standart text-to-image çalıştır. Her sampling adımında, gürültülü latent'in maskelenmemiş bölgesini temiz görselin forward-diffused versiyonuyla değiştir. Çalışır... kötü. Sınır artefaktları sızar çünkü modelin maskelenmiş bölgede ne olduğu hakkında bilgisi yok.

### Düzgün inpainting modeli

4 yerine 9 girdi kanalı alan modifiye edilmiş bir U-Net eğit:

```
input = concat([ noisy_latent (4ch), encoded_image (4ch), mask (1ch) ], dim=channel)
```

Ekstra kanallar VAE-encode edilmiş kaynak görselin bir kopyası artı tek kanallı bir mask. Eğitim zamanında, görselin bölgelerini rastgele maskelersin ve modeli sadece maskelenen bölgeyi denoise edecek şekilde eğitirsin, maskelenmeyen bölge temiz bir koşullama sinyali olarak verilir. Çıkarımda model maskelenen bölgenin etrafında ne olduğunu "görebilir" ve tutarlı tamamlamalar üretir.

SD-Inpaint, SDXL-Inpaint, Flux-Fill hepsi bu 9 kanallı (ya da analog) girdiyi kullanır. Diffusers `StableDiffusionInpaintPipeline`, `FluxFillPipeline`.

### SDEdit (Meng et al., 2022) — bedava düzenleme

Kaynak görsele bir ara `t`'ye kadar gürültü ekle, sonra reverse chain'i `t`'den 0'a yeni bir prompt ile çalıştır. Yeniden eğitim yok. Başlangıç `t`'sinin seçimi sadakati yaratıcı özgürlükle takas eder:

- `t/T = 0.3` → kaynağa neredeyse aynı, küçük stilistik değişiklikler
- `t/T = 0.6` → orta düzeyde düzenleme, kaba yapıyı korur
- `t/T = 0.9` → neredeyse gürültüden üretilmiş, minimal kaynak koruması

### InstructPix2Pix (Brooks et al., 2023)

`(girdi_görseli, talimat, çıktı_görseli)` üçlüleri üzerinde bir diffusion modelini fine-tune et. Çıkarımda hem girdi görseli hem metin talimatı üzerinde koşulla ("gün batımı yap", "bir ejderha ekle"). İki CFG scale: görsel scale ve metin scale.

### RePaint (Lugmayr et al., 2022)

Standart koşulsuz bir diffusion modelini tut. Her reverse adımda yeniden örnekle — ara sıra daha gürültülü bir duruma geri zıpla ve yeniden üret. Sınır artefaktlarını önler. Eğitilmiş bir inpainting modelin olmadığında kullanılır.

## İnşa Et

`code/main.py` 5 boyutlu veri üzerinde 1-D bir oyuncak inpainting şeması uygular. Her örneğin iki cluster'dan birinden 5 float olduğu 5-D karışım verisi üzerinde bir DDPM eğitiriz. Çıkarımda 5'in 2'sini "mask"leriz, her adımda maskelenmeyen üçün gürültülü-forward versiyonunu enjekte ederiz ve sadece maskelenen boyutları yeniden üretiriz.

### Adım 1: 5-D DDPM verisi

```python
def sample_data(rng):
    cluster = rng.choice([0, 1])
    center = [-1.0] * 5 if cluster == 0 else [1.0] * 5
    return [c + rng.gauss(0, 0.2) for c in center], cluster
```

### Adım 2: tüm 5 boyut üzerinde denoiser eğit

Standart DDPM. Net 5-D gürültülü girdi için 5-D gürültü tahmini çıkarır.

### Adım 3: çıkarımda mask-bilinçli reverse

```python
def inpaint_step(x_t, mask, clean_image, alpha_bars, t, rng):
    # maskelenmemiş boyutları temiz kaynağın taze gürültülenmiş versiyonuyla değiştir
    a_bar = alpha_bars[t]
    for i in range(len(x_t)):
        if not mask[i]:
            x_t[i] = math.sqrt(a_bar) * clean_image[i] + math.sqrt(1 - a_bar) * rng.gauss(0, 1)
    # ...sonra x_t üzerinde normal reverse adımı çalıştır
```

Bu naif yaklaşım ve oyuncak 1-D veride çalışır. Gerçek görsel inpainting 9 kanallı girdiyi kullanır çünkü doku tutarlılığı daha çok önemli.

### Adım 4: outpainting

Outpainting ters mask ile inpainting'dir: yeni (önceden var olmayan) canvas'ı maskele, geri kalanını orijinalle doldur. Birebir aynı eğitim hedefi.

## Tuzaklar

- **Dikişler.** Naif yaklaşım görünür sınırlar bırakır çünkü gradyan bilgisi mask boyunca akmaz. Çözüm: mask'i 8-16 piksel genişlet ya da düzgün bir inpainting modeli kullan.
- **Mask sızıntısı.** Eğer koşullama görselinin maskelenmemiş bölgesi düşük kaliteli ya da gürültülüyse, mask içindeki üretimi kirletir. Hafif denoise et ya da blur'la.
- **CFG mask boyutuyla etkileşir.** Küçük mask üzerinde yüksek CFG = doygun yama. Küçük düzenlemeler için CFG'yi düşür.
- **SDEdit sadakat uçurumu.** `t/T = 0.5`'ten `t/T = 0.6`'ya gitmek öznenin kimliğini kaybedebilir. Tara ve checkpoint al.
- **Prompt uyumsuzluğu.** Prompt sadece yeni içeriği değil, *tüm* görseli tarif etmeli. "Sandalyede oturan bir kedi", "bir kedi" değil.

## Kullan

| Görev | Pipeline |
|------|----------|
| Nesne kaldır, küçük mask | SD-Inpaint ya da Flux-Fill, standart prompt |
| Gökyüzünü değiştir | SD-Inpaint + "gün batımında mavi gökyüzü" |
| Canvas'ı uzat | SDXL outpaint modu (8px feather) ya da outpaint mask'li Flux-Fill |
| El / yüz yeniden üret | Özneyi yeniden tarif eden prompt + ControlNet-Openpose ile SD-Inpaint |
| Bir bölgenin stilini değiştir | Maskelenen bölgede `t/T=0.5`'te SDEdit |
| "Gün batımı yap" | InstructPix2Pix ya da Flux-Kontext |
| Arka plan değiştirme | SAM mask → SD-Inpaint |
| Ultra-yüksek sadakat | En zor durumlar için Flux-Fill ya da GPT-Image (hosted) |

SAM (Meta'nın Segment Anything'i, 2023) + diffusion inpaint 2026 arka plan kaldırma pipeline'ı. SAM 2 (2024) videoda çalışır.

## Yayınla

`outputs/skill-editing-pipeline.md` olarak kaydet. Skill orijinal bir görsel + düzenleme tanımı + opsiyonel mask (ya da SAM prompt) alır ve şunu çıkarır: mask-üretim yaklaşımı, baz model, CFG scale'leri (görsel + metin), SDEdit-t ya da inpainting modu ve QA checklist.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'de maskelenen boyutların oranını 0.2'den 0.8'e değiştir. Hangi oranda inpaint kalitesi (maskelenen boyutlardaki residual) koşulsuz üretime eşit olur?
2. **(Orta)** RePaint uygula: her 10. reverse adımında 5 adım geri zıpla (gürültü ekle) ve yeniden denoise et. Mask kenarında sınır residual'ı azaltıp azaltmadığını ölç.
3. **(Zor)** Hugging Face diffusers ile karşılaştır: 20 yüz-yeniden üretim görevinde SD 1.5 Inpaint + ControlNet-Openpose vs Flux.1-Fill. Poz sadakati ve kimlik korumasını ayrı puanla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Inpainting | "Deliği doldur" | Mask içini yeniden üret; dış pikselleri koru. |
| Outpainting | "Canvas'ı uzat" | Canvas dışını yeniden üret; içi koru. |
| 9 kanallı U-Net | "Düzgün inpainting modeli" | Girdi olarak `noisy | encoded-source | mask` alan U-Net. |
| SDEdit | "Gürültü seviyeli img2img" | `t` zamanına gürültü, yeni prompt ile denoise. |
| InstructPix2Pix | "Sadece metin düzenlemeleri" | (görsel, talimat, çıktı) üçlüleri üzerinde fine-tune edilmiş diffusion. |
| RePaint | "Yeniden eğitim yok" | Dikişleri azaltmak için reverse sırasında periyodik yeniden gürültüleme. |
| SAM | "Segment Anything" | Tıklamalar ya da kutularla mask generator'ı; inpaint ile eşleşir. |
| Flux-Kontext | "Bağlamla düzenleme" | Düzenlemeler için referans görsel + talimat kabul eden Flux varyantı. |

## Üretim notu: düzenleme pipeline'ları latency-hassas

Bir görseli düzenleyen kullanıcılar 5 saniye altı tur süresi bekler. 1024²'de 30 adımlık SDXL-Inpaint L4'te 3-4 sn, artı SAM mask üretimi (~200 ms) ve VAE encode/decode (~500 ms birleşik). Üretim çerçevelemesinde, bu throughput-bağlı değil TTFT-bağlı — batch 1, düşük eşzamanlılık, her aşamayı minimize et:

- **SAM-H yavaş olan.** 1024²'de SAM-H ~200 ms; SAM-ViT-B küçük kalite kaybıyla ~40 ms. SAM 2 (video) zamansal yük ekler; tek-görsel düzenlemeleri için kullanma.
- **Mümkün olduğunda encode'u atla.** `pipe.image_processor.preprocess(img)` latent'lere encode eder. Eğer önceki üretimden latent'lerin varsa (iteratif-düzenleme UI'larında tipik), bir VAE encode'u atlamak için doğrudan `latents=...` ile geç.
- **Mask dilation throughput için de önemli.** Küçük bir mask, U-Net forward pass'inin çoğunun boşa gittiği anlamına gelir (maskelenmemiş pikseller zaten clamp'lenir). `diffusers`'ın `StableDiffusionInpaintPipeline`'ı tam U-Net'i mask'ten bağımsız çalıştırır; sadece 9 kanallı düzgün-inpaint varyantları maskelenmiş hesabı kullanır.
- **Flux-Kontext 2025 cevabı.** `(source_image, instruction)` üzerinde tek forward pass — ayrı mask yok, SDEdit gürültü taraması yok. H100'de bir düzenlemeyi ~1.5 sn'de ship eder. Mimari ders: aşamaları çöktür.

## İleri Okuma

- [Lugmayr et al. (2022). RePaint: Inpainting using Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2201.09865) — eğitimsiz inpainting.
- [Meng et al. (2022). SDEdit: Guided Image Synthesis and Editing with Stochastic Differential Equations](https://arxiv.org/abs/2108.01073) — SDEdit.
- [Brooks, Holynski, Efros (2023). InstructPix2Pix](https://arxiv.org/abs/2211.09800) — metin-talimatlı düzenleme.
- [Kirillov et al. (2023). Segment Anything](https://arxiv.org/abs/2304.02643) — SAM, mask kaynağı.
- [Ravi et al. (2024). SAM 2: Segment Anything in Images and Videos](https://arxiv.org/abs/2408.00714) — video SAM.
- [Hertz et al. (2022). Prompt-to-Prompt Image Editing with Cross-Attention Control](https://arxiv.org/abs/2208.01626) — attention-seviyesi düzenleme.
- [Black Forest Labs (2024). Flux.1-Fill ve Flux.1-Kontext](https://blackforestlabs.ai/flux-1-tools/) — 2024 araçları.
