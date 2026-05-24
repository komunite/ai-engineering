# Chameleon ve Early-Fusion Token-Only Multimodal Modelleri

> Şimdiye kadar gördüğümüz her VLM görseli ve metni ayrı tutuyor. Görsel token'lar bir vision encoder'dan geliyor, projector'a akıyor, sonra LLM içinde metinle buluşuyor. Vision ve metin sözcükleri hiç örtüşmüyor. Chameleon (Meta, Mayıs 2024) sordu: ya örtüşselerdi? Görseli paylaşılan sözcükten bir ayrık token dizisine çeviren bir VQ-VAE eğit. Her multimodal belge artık tek dizi — metin token'ları ve görsel token'ları interleaved, tek bir autoregressive loss. Yan etki: model karışık-modalite çıktısı üretebilir — tek bir çıkarım çağrısında değişen metin ve görsel token'ları. Bu ders early-fusion tezini okur ve oyuncak bir versiyonu uçtan uca inşa eder.

**Tür:** Yapım
**Diller:** Python (stdlib, VQ-VAE tokenizer + interleaved decoder)
**Ön koşullar:** Faz 12 · 05, Faz 8 (Generative AI)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Paylaşılan sözcük + tek loss'un modelin ne yapabileceğini neden değiştirdiğini açıkla.
- Bir VQ-VAE'nin bir görseli bir transformer'ın next-token objective'iyle uyumlu ayrık bir diziye nasıl tokenize ettiğini betimle.
- Chameleon'ın eğitim-kararlılık hilelerini söyle: QK-Norm, dropout yerleşimi, LayerNorm sıralaması.
- Chameleon'ı BLIP-2'nin Q-Former yaklaşımı ile karşılaştır ve her birinin ne zaman doğru seçim olduğunu betimle.

## Sorun

Adapter tabanlı VLM'ler (LLaVA, BLIP-2, Qwen-VL) metni ve görseli iki farklı şey olarak ele alıyor. Metin token'ı `embed(text_token)`'dan geçer; görsel `visual_encoder(image) → projector → ... pseudo_tokens`'dan geçer. Modelin yolda birleşen iki input yolu var.

Üç sonuç:

1. LLM yalnızca görselleri tüketebilir, yayamaz. Çıktı yalnızca metin.
2. Karışık-modalite belgeler (makaledeki gibi paragraflar ve görseller dönüşümlü) sıkıntılı — multimodal input'u ya modelin dışında ayrıştırıyorsun ya da üretimleri zincirliyorsun.
3. Dağılım uyumsuzluğu. Görsel token'lar ve metin token'lar hidden uzayın farklı bölgelerinde yaşar, ince hizalama sorunları yaratır.

Chameleon önermeyi reddediyor: görseller paylaşılan bir sözcükten ayrık token dizilerinden başka bir şey değil. Modeli interleaved belgeler üzerinde eğit, tek loss, tek autoregressive decoder ve karışık-modalite üretimini bedava açıyorsun.

## Kavram

### Görsel tokenizer olarak VQ-VAE

Tokenizer vektör-kuantize edilmiş bir variational autoencoder. Mimari:

- Encoder: görseli spatial feature map'e, mesela dim 256'lı 32x32 feature'a eşleyen CNN + ViT.
- Codebook: K vektörden öğrenilmiş bir sözcük (Chameleon 8192 kullanır), dim 256 da.
- Quantization: her spatial feature için L2 mesafesi ile en yakın codebook girişini ara. Sürekli feature'ı integer indeks ile değiştir.
- Decoder: kuantize edilmiş feature'ları piksellere geri götüren CNN.

Eğitim: VAE reconstruction loss + commitment loss + codebook loss. Codebook indeksleri görseller için ayrık bir alfabe oluşturur.

Chameleon için: bir görsel 32*32 = 1024 token olur, 8192 sözcükten çekilir. Metin token'larıyla (LLM'in BPE sözcüğünden, mesela 32000) birleştir. Son sözcük: 40192. Transformer tek bir dizi, tek bir loss görür.

### Paylaşılan sözcük

Chameleon'ın sözcüğü metin token'ları, görsel token'ları ve modalite ayırıcılarını birleştirir. Her token'ın tek bir ID'si var. Input embedding katmanı her ID'yi D-boyutlu hidden vektöre eşler. Çıkış projeksiyonu hidden'ı vocab logit'lerine geri eşler. Softmax sonraki token'ı seçer, hangi modalite olursa olsun.

Ayırıcılar önemli: `<image>` ve `</image>` etiketleri görsel-token dizisini bracketler. Üretim zamanında, model `<image>` yayarsa, aşağı akış yazılımı sonraki 1024 token'ın piksel render için decoder'a gönderilecek VQ indeksleri olduğunu bilir.

### Karışık-modalite üretimi

Çıkarım, paylaşılan sözcükte next-token tahmini. Örnek prompt: "Bir kedi çiz ve betimle." Chameleon yayar:

```
<image> 4821 1029 2891 ... (1024 görsel token) </image>
The cat is orange, sitting on a windowsill...
```

Model sırayı otonom seçer — önce görsel sonra metin, önce metin sonra görsel ya da interleave üretebilir. Aynı decoder, aynı loss.

Üretimin yalnızca metin olduğu adapter VLM'lerle karşılaştır. Chameleon model çıktı modalitelerinin sorusunu yeniden açıyor.

### Eğitim kararlılığı — QK-Norm, dropout, LayerNorm sıralaması

Early-fusion eğitimi ölçekte kararsız. Chameleon'ın makalesi üç hile belgeliyor:

- QK-Norm. Attention içindeki query ve key projeksiyonlarına dot product'tan önce LayerNorm uygula. Derinlikte logit büyüklüğü patlamasını engeller. Birden çok 2024-sonrası büyük model tarafından kullanılır.
- Dropout yerleşimi. Yalnızca attention ve MLP'den sonra değil, her residual-add'den sonra dropout. Görsel token'lardan gelen gradient'ler baskın olabildiğinde daha çok regularization gerekir.
- LayerNorm sıralaması. Residual dalında pre-LN (standart), artı son block'un skip bağlantısında ekstra LN. Son katman gradient akışını kararlılaştırır.

Bu hileler olmadan 34B-param Chameleon eğitimi birden çok checkpoint'te diverge etti. Onlarla yakınsadı. Eğitim tarifi mimari kadar katkıdır.

### Tokenizer'ın yeniden inşa tavanı

VQ-VAE kayıplıdır. 8192 codebook girişi ve 512x512 görsel başına 1024 token'da yeniden inşa PSNR 26-28 dB civarında sınırlanır. Bu tanınabilir görsel gen için yeterli ama sürekli-uzay diffusion'dan görünür biçimde daha kötü (Stable Diffusion 3 32+ dB'ye ulaşır).

Tokenizer bottleneck. Daha iyi tokenizer'lar (MAGVIT-v2, IBQ, SBER-MoVQGAN) tavanı yükseltir. Emu3 (Ders 12.12) yalnızca daha iyi bir tokenizer üzerinden SDXL-kalitesinde üretim elde eder.

### Chameleon vs BLIP-2 / LLaVA

Chameleon (early fusion, paylaşılan vocab):
- Tek loss, tek decoder.
- Karışık-modalite çıktısı üretir.
- Tokenizer kalite tavanıdır.
- Pahalı: çıkarım yolunda üretilen görsel başına VQ-VAE decoder.

BLIP-2 / LLaVA (late fusion, ayrı kuleler):
- Görsel girer, yalnızca metin çıkar.
- Pretrained LLM'i yeniden kullanır.
- Anlamak için tokenizer bottleneck'i yok.
- Ucuz: tek forward pass.

Göreve göre seç. Görsel üretimine ihtiyacın varsa, Chameleon ailesi. Yalnızca anlamaya ihtiyacın varsa, adapter-VLM daha basit ve daha çok pretrained compute'u yeniden kullanır.

### Fuyu ve AnyGPT

Fuyu (Adept, 2023) ilgili bir yaklaşım: ayrı vision encoder'ı tamamen atla, ham görsel patch'leri LLM'in input projeksiyonundan token'larmış gibi besle, tokenizer yok. Chameleon'dan daha basit, paylaşılan-vocab çıkış üretimini kaybeder.

AnyGPT (Zhan et al., 2024) Chameleon'ı dört modaliteye genişletiyor: metin, görsel, konuşma, müzik. Her biri için aynı VQ-VAE hilesi, paylaşılan transformer. Any-to-any üretim. Ders 12.16'da daha çok kapsanır.

## Kullan

`code/main.py` uçtan uca oyuncak bir early-fusion modeli inşa eder:

- 8x8 patch'leri codebook indekslerine (K=16) eşleyen ufak VQ-VAE tarzı bir quantizer.
- (text ids 0..31) + (image ids 32..47) + (ayırıcılar 48, 49) paylaşılan sözcük.
- Sentetik caption'lar + görsel-token dizileri üzerinde eğitilmiş oyuncak bir autoregressive decoder (bigram tablo).
- Verilen prompt'a göre değişen metin + görsel token yayan sampling döngüsü.

Kod kasıtlı olarak transformer'ı ufak tutar (bigram'lar) böylece sinyal akışını uçtan uca izleyebilirsin.

## Yayınla

Bu ders `outputs/skill-tokenizer-vs-adapter-picker.md` üretir. Bir ürün spec'i (yalnızca anlama vs anlama + üretim, gerekli görsel kalitesi, maliyet bütçesi) verildiğinde, Chameleon-family (early fusion) ile LLaVA-family (late fusion) arasından seçer ve nicel başparmak kurallarıyla haklı çıkarır.

## Alıştırmalar

1. Chameleon K=8192 codebook girişi ve 512x512 görsel başına 1024 token kullanır. 24-bit RGB görsele kıyasla sıkıştırma oranını tahmin et. Kayıplı mı? Ne kadar kayıplı?

2. Aynı VQ-VAE yoğunluğunda 4K bir görsel (3840x2160) kaç görsel token üretir? Chameleon tarzı bir model 4K bir görseli tek çıkarım çağrısında üretebilir mi? Önce ne kırılır — context, tokenizer kalitesi ya da KV cache?

3. QK-Norm'u saf Python'da uygula. 64 boyutlu query ve key verildiğinde, LayerNorm'dan önce ve sonra dot product'ı göster. Büyüklük kontrolü derinlikte neden önemli?

4. Chameleon Bölüm 2.3'ü eğitim kararlılığı üzerine oku. QK-Norm olmadan 34B'de makalenin gözlemlediği tam başarısızlık modunu betimle. "Norm patlaması" imzası neydi?

5. Yalnızca metin prompt verildiğinde karışık-modalite cevap yayması için oyuncak decoder'ı genişlet. Eğitim-veri dağılımı %60 metin-first / %40 görsel-first verildiğinde modelin önce görsel vs önce metin seçme sıklığını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Early fusion | "Birleştirilmiş token'lar" | Birinci adımdan transformer'ın sözcüğünü paylaşan ayrık token'lara çevrilmiş görseller |
| VQ-VAE | "Görsel tokenizer" | Görselleri transformer'ın tahmin edebileceği integer indekslere eşleyen CNN + ViT + codebook |
| Paylaşılan sözcük | "Tek sözlük" | Metin + görsel + modalite ayırıcılarını kapsayan tek token ID uzayı |
| QK-Norm | "Attention kararlılaştırıcısı" | Dot product'larından önce query ve key'e uygulanan LayerNorm, norm patlamasını engeller |
| Karışık-modalite üretim | "Metin + görsel çıktı" | Tek pass'te otonom interleaved metin ve görsel token üreten çıkarım |
| Codebook boyutu | "K giriş" | VQ-VAE'nin kuantize edebileceği ayrık vektör sayısı; sadakat için sıkıştırmayı takas eder |
| Tokenizer tavanı | "Yeniden inşa sınırı" | VQ token'larını decode ederek elde edilebilecek en iyi PSNR; modelin görsel kalitesini sınırlar |

## İleri Okuma

- [Chameleon Team — Chameleon: Mixed-Modal Early-Fusion Foundation Models (arXiv:2405.09818)](https://arxiv.org/abs/2405.09818)
- [Aghajanyan et al. — CM3 (arXiv:2201.07520)](https://arxiv.org/abs/2201.07520)
- [Yu et al. — CM3Leon (arXiv:2309.02591)](https://arxiv.org/abs/2309.02591)
- [Zhan et al. — AnyGPT (arXiv:2402.12226)](https://arxiv.org/abs/2402.12226)
- [Adept — Fuyu-8B blog (adept.ai)](https://www.adept.ai/blog/fuyu-8b)
