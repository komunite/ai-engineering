# Few-Shot VLM'ler için Flamingo ve Gated Cross-Attention

> DeepMind'ın Flamingo'su (2022) kimseden önce iki şey yaptı. Tek bir modelin keyfi olarak interleave edilmiş görsel, video ve metin dizilerini işleyebileceğini gösterdi. Ve VLM'lerin in-context öğrenebileceğini gösterdi — üç örnek (görsel, caption) çiftli few-shot bir prompt ver ve model bir gradyan adımı olmadan yeni bir görseli caption'lar. Mekanizma: donmuş LLM'in mevcut katmanları arasına eklenen, başlangıçta LLM'in metin yeteneği korunsun diye sıfırdan başlayan öğrenilmiş bir tanh gate ile gated cross-attention katmanları. Bu ders Flamingo'nun Perceiver resampler ve gated cross-attention mimarisinde yürüyor — Gemini'nin interleaved input'larının ve Idefics2'nin görsel token'larının atası.

**Tür:** Öğrenim
**Diller:** Python (stdlib, gated cross-attention + Perceiver resampler demosu)
**Ön koşullar:** Faz 12 · 03 (BLIP-2 Q-Former)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Gated cross-attention'ın donmuş bir LLM'in metin yeteneğini başlangıçta tanh(gate) = 0 üzerinden nasıl koruduğunu açıkla.
- Bir Perceiver resampler'dan yürü: N görsel patch → cross-attention üzerinden K sabit "latent" query.
- Flamingo'nun görsel yerleşimine saygı duyan causal masking ile interleaved image-text dizilerini nasıl ele aldığını betimle.
- Few-shot multimodal prompt yapısını yeniden üret (3 image-caption örneği sonra bir query görsel).

## Sorun

BLIP-2 donmuş bir LLM'in input katmanına 32 görsel token besler. Prompt başına bir görsel için çalışır. Ama "işte görsel A, caption'la; işte görsel B, caption'la; şimdi işte görsel C, caption'la" gibi metinle interleave edilmiş *çok* görsel beslemek istersen? LLM'in self-attention'ı görsel token'ları ve metin token'ları tek akışta ele almalı ve hangi pozisyonların hangi görsellere attend edebileceği sorusu sinir bozucu olur.

Flamingo'nun cevabı: LLM'in input akışını hiç değiştirme. Mevcut LLM block'ları arasına ekstra cross-attention katmanları ekle. Metin token'ları hâlâ her zamanki gibi LLM'in causal self-attention'ından akar. Her birkaç LLM block'u arasında, metin token'ları yeni bir gated katman üzerinden görsel feature'larına da cross-attend eder. Gate (sıfıra initialize edilmiş), adım sıfırda yeni katmanların no-op olduğu anlamına gelir — model tam olarak pretrained LLM gibi davranır. Eğitim ilerledikçe gate açılır ve görsel bilgi akmaya başlar.

Flamingo'nun cevapladığı ikinci soru: prompt başına değişken sayıda görseli (0, 1 ya da çok) nasıl ele alırsın? Bir Perceiver resampler — ne kadar patch'in olursa olsun alıp sabit sayıda görsel latent token üreten küçük bir cross-attention modülü. LLM cross-attention katmanı prompt'ta kaç görsel olduğundan bağımsız aynı shape'i görür.

## Kavram

### Donmuş LLM

Flamingo donmuş bir Chinchilla 70B LLM ile başlar. Tüm 70B ağırlık dokunulmamış. Mevcut metin self-attention ve FFN normal çalışır.

### Perceiver resampler

Prompt'taki her görsel için ViT N patch token üretir. Perceiver resampler K sabit öğrenilebilir latent'a sahiptir (Flamingo K=64 kullanır). Her resampler block iki alt-adım:

1. Cross-attention: K latent N patch token'ı üzerinde attend eder (latent'lardan Q, patch'lerden K/V).
2. Latent'lar içinde self-attention + FFN.

6 resampler block sonrası çıktı dim 1024'lü K=64 görsel token, ViT'in kaç patch ürettiğinden bağımsız. 224x224 bir görsel (196 patch) ve 480x480 bir görsel (900 patch) ikisi de 64 resampler token olarak çıkar.

Video için resampler temporal olarak uygulanır: her frame'in patch'leri 64 latent üretir ve bir temporal positional encoding modelin t=0'ı t=N'den ayırt etmesini sağlar. Tam video T * 64 görsel token olur.

### Gated cross-attention

Donmuş LLM'in her M katmanı arasına (Flamingo M=4 kullanır) yeni bir gated cross-attention block ekle:

```
x_after_llm_block = llm_block(x_before)
cross = cross_attn(x_after, resampler_output)
gated = tanh(alpha) * cross + x_after
x_before_next_block = gated
```

- `alpha` sıfıra initialize edilmiş öğrenilebilir bir scalar.
- `tanh(0) = 0`, yani init'te gated dal sıfır katkıda bulunur.
- `alpha` sıfırdan uzaklaştıkça cross-attention katkısı yumuşakça büyür.
- Residual bağlantı tam açık bir gate'in bile LLM'in metin temsilini üzerine yazmadığı anlamına gelir; üzerine yalnızca görsel bilgi ekler.

Flamingo'daki en önemli tek tasarım seçimi bu: görsel koşullama eklemeli, gated ve başlangıçta sıfır. Adım 0'daki bir Flamingo, yalnızca metin input'larında mükemmel bir Chinchilla 70B'dir.

### Interleaved input'lar için masked cross-attention

"<görsel A> caption A <görsel B> caption B <görsel C> ?" gibi bir prompt'ta her metin token'ı yalnızca dizide ondan önce gelen görselleri görmeli. Cross-attention mask zorlar: `t` pozisyonundaki metin token'ı yalnızca `i < i_t` görsel indeksli görsel resampler token'larına attend eder, burada `i_t` `t` pozisyonundan önceki en yakın görsel. "Yalnızca son önceki görseli görür" ya da "tüm önceki görselleri görür" ikisi de geçerli seçim; Flamingo birinciyi seçti.

### In-context few-shot learning

Bir Flamingo prompt'u şöyle:

```
<image1> A photo of a cat. <image2> A photo of a dog. <image3> A photo of a
```

Model tamamlama kalıbını görür ve "bird" çıktılar (ya da image3 ne gösteriyorsa). Gradyan adımı yok. Donmuş LLM'in in-context öğrenme yeteneği gated cross-attention üzerinden geçer — bu makalenin püf noktası ve neden önemli olduğu.

### Eğitim verisi

Flamingo üç dataset üzerinde eğitti:

1. MultiModal MassiveWeb (M3W): okuma sırasını yeniden inşa eden, görsel ve metin interleave edilmiş 43M web sayfası.
2. Image-Text Pairs (ALIGN + LTIP): 4.4B çift.
3. Video-Text Pairs (VTP): 27M kısa video klibi.

OBELICS (2023) interleaved web corpus'unun açık reprodüksiyonu, Idefics, Idefics2 ve çoğu açık "Flamingo benzeri" modelin eğitildiği.

### OpenFlamingo ve Otter

OpenFlamingo (2023) açık reprodüksiyon. Mimari aynı (donmuş LLaMA ya da MPT üzerinde Perceiver resampler + gated cross-attention). 3B, 4B, 9B checkpoint'ler. Daha küçük base LLM ve daha az veri nedeniyle kalite Flamingo'nun gerisinde.

Otter (2023) OpenFlamingo üzerine MIMIC-IT'de (multimodal instruction'lar dataset'i) instruction tuning ile inşa edilir, gated cross-attention'ın instruction following için de çalıştığını gösterir.

### Descendant'lar

- Idefics / Idefics2 / Idefics3: Hugging Face'in gated cross-attention soyu, kademeli olarak daha basit (Idefics2 resampler'ı adaptive pooling ile doğrudan patch token'lar lehine düşürdü).
- Flamingo-to-Chameleon geçişi: 2024'e kadar çoğu ekip early-fusion'a geçti (Ders 12.11); Flamingo tarzı gated cross-attention backbone donması gerektiği yerde üretimde kalıyor.
- Gemini'nin interleaved input'u: kavramsal olarak Flamingo'nun interleaved-format esnekliğini miras alır, mekanizma proprietary olsa da.

### BLIP-2'ye göre karşılaştırma

| | BLIP-2 | Flamingo |
|---|---|---|
| Görsel köprü | Input'ta bir kere Q-Former | Her M katmanda gated cross-attention |
| Görsel token | Görsel başına 32 | Cross-attn katmanı başına görsel başına 64 |
| Donmuş LLM | Evet | Evet |
| Few-shot in-context | Zayıf | Güçlü — makalenin merkezi |
| Interleaved input'lar | Native destek yok | Evet, tasarım hedefi |
| Eğitim verisi | 130M çift | 1.3B çift + 43M interleaved sayfa |
| Parametre sayısı | 188M eğitilmiş | ~10B eğitilmiş (cross-attn katmanları) |
| Compute | 8 A100'de günler | Binlerce TPUv4'te haftalar |

Bütçede tek görsel VQA için BLIP-2 seç. Interleaved, few-shot ya da çok görsel akıl yürütme için Flamingo/Idefics2 seç.

## Kullan

`code/main.py` şunları gösterir:

1. 8 öğrenilebilir latent ile 36 sahte patch token üzerinde bir Perceiver resampler (saf Python cross-attention).
2. `alpha = 0` ile bir gated cross-attention adımı → çıktı input'a eşit (LLM değişmemiş), sonra `alpha = 2.0` → görsel katkı karıştırılmış.
3. "(görsel 1) (metin 1) (görsel 2) (metin 2)" dizisi için 2D attention mask üreten bir interleaved-mask builder.

## Yayınla

Bu ders `outputs/skill-gated-bridge-diagnostic.md` üretir. Açık bir VLM config'i (resampler E/H, cross-attn sıklığı, gate scheme) verildiğinde, Flamingo soy öğelerini tanımlar ve donma stratejisini açıklar. Bir fine-tune'un metin performansını neden bozduğunu debug etmek için yararlı (cevap: gate çok geniş çok hızlı açıldı).

## Alıştırmalar

1. Flamingo-9B'nin görsel parametre sayısını hesapla: 9B LLM + 1.4B gated cross-attention katmanı + 64M resampler. Toplam param'ın ne kadarı eğitilmiş?

2. Gated residual `y = tanh(alpha) * cross + x`'i PyTorch'ta uygula. `alpha=0` ile init'te `y==x`'in tam olarak olduğunu deneysel olarak göster.

3. OpenFlamingo Bölüm 3.2'yi (arXiv:2308.01390) her prompt'un farklı görsel sayısına sahip olduğu bir batch'te çoklu görseli nasıl ele aldıklarına dair oku. Padding stratejisini betimle.

4. Flamingo'nun cross-attention mask'i neden bir metin token'ının tüm önceki görseller yerine *yalnızca en yakın* önceki görsele attend etmesine izin verir? Flamingo makalesi Bölüm 2.4'ü oku ve trade-off'u açıkla.

5. In-context few-shot: yeni bir Flamingo varyantı için "görsel → ana nesnenin rengi" 4 örnekli bir prompt inşa et. Örnek sayısını 0'dan 8'e değiştirirken beklenen doğruluk kalıbını betimle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Perceiver resampler | "Sabit-latent cross-attention" | Değişken sayıda input patch'ten K sabit token üreten modül |
| Gated cross-attention | "Tanh-gated köprü" | Residual katman `y = tanh(alpha)*cross + x`, öğrenilebilir alpha, init 0 |
| Interleaved input | "Karışık dizi" | Görsel ve metnin okuma sırasında özgürce karıştığı prompt formatı |
| Donmuş LLM | "LLM gradient'i yok" | Metin LLM'in ağırlıkları güncellenmez; yalnızca resampler + cross-attn katmanları eğitilir |
| Few-shot | "In-context örnekler" | Prompt'ta birkaç (görsel, cevap) çifti ver; model fine-tuning olmadan genelleştirir |
| OBELICS | "Interleaved web corpus" | Okuma sırasında görsel ve metinle 141M web sayfalı açık dataset |
| Chinchilla | "70B donmuş base" | Flamingo'nun donmuş metin LLM'i, DeepMind'ın Chinchilla makalesinden |
| Gate schedule | "Alpha nasıl hareket eder" | Cross-attention gate'inin eğitim sırasında açılma hızı |
| Cross-attn frequency | "Her M katmanda" | Bir gated cross-attention block'unun ne sıklıkla eklendiği; Flamingo M=4 kullanır |
| OpenFlamingo | "Açık reprodüksiyon" | 3-9B'de MosaicML/LAION açık checkpoint'i; Flamingo ile mimari-aynı |

## İleri Okuma

- [Alayrac et al. — Flamingo (arXiv:2204.14198)](https://arxiv.org/abs/2204.14198) — orijinal makale.
- [Awadalla et al. — OpenFlamingo (arXiv:2308.01390)](https://arxiv.org/abs/2308.01390) — açık reprodüksiyon.
- [Laurençon et al. — OBELICS (arXiv:2306.16527)](https://arxiv.org/abs/2306.16527) — interleaved web corpus.
- [Jaegle et al. — Perceiver IO (arXiv:2107.14795)](https://arxiv.org/abs/2107.14795) — genel Perceiver mimarisi.
- [Li et al. — Otter (arXiv:2305.03726)](https://arxiv.org/abs/2305.03726) — instruction-tuned Flamingo descendant'ı.
- [Laurençon et al. — Idefics2 (arXiv:2405.02246)](https://arxiv.org/abs/2405.02246) — Flamingo yaklaşımının modern basitleştirmesi.
