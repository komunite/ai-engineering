# ControlNet, LoRA ve Koşullama

> Tek başına metin hantal bir kontrol sinyali. ControlNet ön-eğitilmiş bir diffusion modelini klonlamana ve onu derinlik haritası, poz iskeleti, karalama ya da kenar görseliyle yönlendirmene izin verir. LoRA 10 milyon parametre eğiterek 2B parametreli bir modeli fine-tune etmene izin verir. Birlikte Stable Diffusion'ı bir oyuncaktan, her ajansta ship edilen 2026 görsel pipeline'ına dönüştürdüler.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 07 (Latent Diffusion), Faz 10 (Sıfırdan LLM'ler — LoRA temeli için)
**Süre:** ~75 dakika

## Sorun

"kırmızı elbiseli bir kadın yoğun bir caddede köpek yürütüyor" gibi bir prompt modele köpeğin *nerede* olduğu, kadının *hangi pozda* olduğu ya da caddenin *perspektifi* hakkında hiçbir bilgi vermez. Metin, bir görseli belirtmek için ihtiyacın olan şeyin yaklaşık %10'unu sabitler. Geri kalan görseldir ve kelimelerle verimli olarak tarif edilemez.

Her sinyal için (poz, derinlik, canny, segmentation) sıfırdan yeni bir koşullu model eğitmek çok pahalı. 2.6B-param SDXL omurgasını dondurulmuş tutmak, koşullamayı okuyan küçük bir yan-ağ takmak ve omurganın ara feature'larına dürtmesini sağlamak istiyorsun. Bu ControlNet'tir.

Ayrıca modele tüm modeli yeniden eğitmeden yeni kavramlar (yüzün, ürünün, stilin) öğretmek istiyorsun. 100x daha küçük bir delta istiyorsun. Bu LoRA'dır — mevcut attention ağırlıklarına bağlanan low-rank adapter'lar.

ControlNet + LoRA + metin = 2026 uygulayıcısının araç çantası. Çoğu üretim görsel pipeline'ı SDXL / SD3 / Flux tabanı üzerine 2-5 LoRA, 1-3 ControlNet ve bir IP-Adapter katmanlar.

## Kavram

![ControlNet encoder'ı klonlar; LoRA low-rank delta'lar ekler](../assets/controlnet-lora.svg)

### ControlNet (Zhang et al., 2023)

Ön-eğitilmiş bir SD al. U-Net'in encoder yarısını *klonla*. Orijinali dondur. Klonu ekstra bir koşullama girdisi (kenarlar, derinlik, poz) kabul edecek şekilde eğit. Klonu *zero-convolution* skip connection'larıyla (sıfır olarak başlatılan 1×1 conv'lar — no-op olarak başla, delta öğren) orijinalin decoder yarısına geri bağla.

```
SD U-Net decoder:   ... ← orig_enc_features + zero_conv(controlnet_enc(condition))
```

Zero-conv init, ControlNet'in identity olarak başlaması demek — eğitim öncesinde bile zarar yok. Standart diffusion loss'uyla 1M (prompt, koşul, görsel) üçlüsü üzerinde eğit.

Modalite başına ControlNet'ler küçük yan modeller olarak ship edilir (SDXL için ~360M, SD 1.5 için ~70M). Çıkarımda kompoze edebilirsin:

```
features += weight_a * control_a(depth) + weight_b * control_b(pose)
```

### LoRA (Hu et al., 2021)

Modeldeki herhangi bir lineer katman `W ∈ R^{d×d}` için, `W`'yi dondur ve low-rank bir delta ekle:

```
W' = W + ΔW,  ΔW = B @ A,  A ∈ R^{r×d},  B ∈ R^{d×r}
```

`r << d` ile. Attention için rank 4-16 standart, ağır fine-tune'lar için rank 64-128. Yeni parametre sayısı: `d²` yerine `2 · d · r`. `d=640`, `r=16` ile SDXL attention'ı için: adapter başına 410k yerine 20k param — 20x azalma. Tüm model boyunca: bir LoRA genelde temel 5GB'ye karşı 20-200MB.

Çıkarımda LoRA'yı ölçekleyebilirsin: `W' = W + α · B @ A`. `α = 0.5-1.5` normal. Birden çok LoRA additive yığılır (her zamanki uyarıyla: lineer olmayan şekillerde etkileşirler).

### IP-Adapter (Ye et al., 2023)

Koşullama olarak (metnin yanı sıra) bir *görsel* kabul eden minik bir adapter. CLIP image encoder'ı kullanarak görsel token'ları üretir, onları metin token'larıyla birlikte cross-attention'a enjekte eder. Temel model başına ~20MB. "Bu referansın stilinde bir görsel üret" yapmana LoRA olmadan izin verir.

## Kompoze edilebilirlik matrisi

| Araç | Neyi kontrol eder | Boyut | Ne zaman kullan |
|------|------------------|------|-------------|
| ControlNet | Uzamsal yapı (poz, derinlik, kenarlar) | 70-360MB | Kesin layout, kompozisyon |
| LoRA | Stil, özne, kavram | 20-200MB | Kişiselleştirme, stil |
| IP-Adapter | Referans görselden stil ya da özne | 20MB | Hiçbir metin görünüşü tarif edemiyor |
| Textual Inversion | Yeni bir token olarak tek bir kavram | 10KB | Eski, çoğunlukla LoRA ile değiştirildi |
| DreamBooth | Bir özne üzerinde tam fine-tune | 2-5GB | Güçlü kimlik, yüksek compute |
| T2I-Adapter | Daha hafif ControlNet alternatifi | 70MB | Edge cihazları, çıkarım bütçesi |

ControlNet ≈ uzamsal. LoRA ≈ semantik. İkisini de kullan.

## İnşa Et

`code/main.py` iki mekanizmayı 1-D'de simüle eder:

1. **LoRA.** Ön-eğitilmiş bir lineer katman `W`. Dondur. `W + BA` hedef bir lineer katmanı eşleyecek şekilde low-rank bir `B @ A` eğit. `r = 1`'in mükemmel bir rank-1 düzeltmesi öğrenmek için yeterli olduğunu göster.

2. **ControlNet-lite.** Bir "dondurulmuş baz" tahminci ve ekstra bir sinyali okuyan bir "yan ağ". Yan ağın çıktısı sıfır olarak başlatılan öğrenilebilir bir skalerle gate'lenir (zero-conv versiyonumuz). Eğit ve gate'in yükseldiğini izle.

### Adım 1: LoRA matematiği

```python
def lora(W, A, B, x, alpha=1.0):
    # W donduruldu; A, B eğitilebilir low-rank faktörler.
    return [W[i][j] * x[j] for i, j in ...] + alpha * (B @ (A @ x))
```

### Adım 2: sıfır-init yan ağ

```python
side_out = control_net(x, condition)
gated = gate * side_out  # gate 0 olarak başlatıldı
h = base(x) + gated
```

0. adımda çıktı bazla aynı. Erken eğitim `gate`'i yavaş günceller — katastrofik kayma yok.

## Tuzaklar

- **LoRA'ları aşırı ölçeklemek.** `α = 2` ya da `α = 3` "daha güçlü yap" yaygın bir hack; aşırı stilize / bozuk çıktılar üretir. `α ≤ 1.5` tut.
- **ControlNet ağırlık çatışması.** Bir Pose ControlNet'i ağırlık 1.0'da ve bir Depth ControlNet'i ağırlık 1.0'da kullanmak genelde aşar. Ağırlıkların toplamı ≈ 1.0 güvenli varsayılan.
- **Yanlış baz üzerinde LoRA.** SDXL LoRA'ları SD 1.5'te sessizce no-op olur çünkü attention boyutları eşleşmez. Diffusers 0.30+'da uyarır.
- **Textual Inversion kayması.** Bir checkpoint'te eğitilen token'lar diğerinde kötü kayar. LoRA daha taşınabilir.
- **LoRA ağırlık-merge ve depolama.** Daha hızlı çıkarım için (runtime ekleme yok) LoRA'yı baz model ağırlıklarına pişirebilirsin ama runtime'da `α`'yı ölçekleme yeteneğini kaybedersin. İki versiyonu da tut.

## Kullan

| Hedef | 2026 pipeline'ı |
|------|---------------|
| Bir markanın art stilini yeniden üret | ~30 küratörlü görsel üzerinde rank 32'de eğitilmiş LoRA |
| Üretilen görsele yüzümü koy | DreamBooth ya da LoRA + IP-Adapter-FaceID |
| Belirli poz + prompt | ControlNet-Openpose + SDXL + metin |
| Derinlik-bilinçli kompozisyon | ControlNet-Depth + SD3 |
| Referans + prompt | IP-Adapter + metin |
| Kesin layout | ControlNet-Scribble ya da ControlNet-Canny |
| Arka plan değiştirme | ControlNet-Seg + Inpainting (Ders 09) |
| Hızlı 1-adımlık stil | SDXL-Turbo'da LCM-LoRA |

## Yayınla

`outputs/skill-sd-toolkit-composer.md` olarak kaydet. Skill bir görev alır (girdi varlıkları: prompt, opsiyonel referans görsel, opsiyonel poz, opsiyonel derinlik, opsiyonel karalama) ve araç yığınını, ağırlıkları ve yeniden üretilebilir bir seed protokolü çıkarır.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'de LoRA rank `r`'sini 1'den 4'e değiştir. Hangi rank'ta LoRA bir rank-2 hedef delta'sını tam olarak eşler?
2. **(Orta)** İki ayrı hedef dönüşümde iki ayrı LoRA eğit. Onları birlikte yükle ve additive etkileşimlerini göster. Etkileşim ne zaman lineerliği bozar?
3. **(Zor)** diffusers ile yığ: SDXL-base + Canny-ControlNet (ağırlık 0.8) + bir stil LoRA (α 0.8) + IP-Adapter (ağırlık 0.6). Yığın ağırlıkları değiştikçe FID-vs-prompt-sadakati trade-off'unu ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| ControlNet | "Uzamsal kontrol" | Klonlanmış encoder + zero-conv skip'leri; bir koşullama görseli okur. |
| Zero convolution | "Identity olarak başlar" | Sıfır olarak başlatılan 1×1 conv; ControlNet no-op olarak başlar. |
| LoRA | "Low-rank adapter" | `W + B @ A`, `r << d`; tam fine-tune'dan 100x daha az param. |
| rank r | "Düğme" | LoRA sıkıştırması; 4-16 tipik, ağır kişiselleştirme için 64+. |
| α | "LoRA gücü" | LoRA delta'sının runtime ölçeklemesi. |
| IP-Adapter | "Referans görsel" | CLIP-image token'ları üzerinden küçük görsel-koşullama adapter'ı. |
| DreamBooth | "Tam özne fine-tune" | Tam modeli bir öznenin ~30 görseli üzerinde eğit. |
| Textual Inversion | "Yeni token" | Sadece yeni bir kelime embedding'i öğren; eski, çoğunlukla değiştirildi. |

## Üretim notu: LoRA takasları, ControlNet lane'leri, multi-tenant servis

Gerçek bir text-to-image SaaS aynı temel checkpoint üzerinde yüzlerce LoRA ve düzinelerce ControlNet sunar. Servis problemi LLM multi-tenancy'sine çok benzer görünür (üretim literatürü LLM durumunu sürekli batching ve LoRAX / S-LoRA altında işler):

- **LoRA'ları hot-swap, merge etme.** `W' = W + α·B·A`'yı temele merge etmek adım başına ~%3-5 daha hızlı çıkarım verir ama `α`'yı ve tabanı dondurur. LoRA'ları VRAM'de rank-r delta'lar olarak sıcak tut; diffusers istek başına aktivasyon için `pipe.load_lora_weights()` + `pipe.set_adapters([...], adapter_weights=[...])` sunar. Takas maliyeti `2 · d · r · num_layers` ağırlığıdır — MB-ölçeği, saniye altı.
- **İkinci attention lane'i olarak ControlNet.** Klonlanmış encoder bazla paralel çalışır. Her biri ağırlık 1.0'da iki ControlNet = adım başına bir merge edilmiş pass değil, iki ekstra forward pass. Batch-size tavanı karesel düşer. Aktif ControlNet başına ~1.5× adım maliyeti bütçele.
- **Quantize edilmiş LoRA'lar da.** Tabanı quantize ettiysen (bkz. Ders 07, 8GB'da Flux), LoRA delta'sı da 8-bit ya da 4-bit'e temiz şekilde quantize olur. QLoRA tarzı yükleme, 4-bit Flux temeli üzerine 5-10 LoRA yığmana belleği patlatmadan izin verir.

Flux-özel: Niels'in Flux-on-8GB notebook'u tabanı 4-bit'e quantize eder; o quantize tabana `weight_name="pytorch_lora_weights.safetensors"` ile bir stil LoRA'sı (`pipe.load_lora_weights("user/style-lora")`) yığmak hâlâ çalışır. Çoğu SaaS ajansının 2026'da ship ettiği reçete bu.

## İleri Okuma

- [Zhang, Rao, Agrawala (2023). Adding Conditional Control to Text-to-Image Diffusion Models](https://arxiv.org/abs/2302.05543) — ControlNet.
- [Hu et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — LoRA (orijinal olarak LLM'ler için; diffusion'a taşınır).
- [Ye et al. (2023). IP-Adapter: Text Compatible Image Prompt Adapter](https://arxiv.org/abs/2308.06721) — IP-Adapter.
- [Mou et al. (2023). T2I-Adapter: Learning Adapters to Dig Out More Controllable Ability](https://arxiv.org/abs/2302.08453) — ControlNet'e daha hafif alternatif.
- [Ruiz et al. (2023). DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation](https://arxiv.org/abs/2208.12242) — DreamBooth.
- [HuggingFace Diffusers — ControlNet / LoRA / IP-Adapter dokümanları](https://huggingface.co/docs/diffusers/training/controlnet) — referans pipeline'lar.
