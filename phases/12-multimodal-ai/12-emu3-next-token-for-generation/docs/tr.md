# Emu3: Görsel ve Video Üretimi için Next-Token Prediction

> BAAI'nin Emu3'ü (Wang et al., Eylül 2024) diffusion-vs-autoregressive tartışmasını bitirmesi gereken 2024 sonucu. Tek bir Llama tarzı decoder-only transformer, yalnızca next-token-prediction objective'inde eğitildi, metin + VQ görsel token'ları + 3D VQ video token'ları birleştirilmiş sözcüğü boyunca, görsel üretiminde SDXL'i ve algıda LLaVA-1.6'yı yener. CLIP loss yok. Diffusion programı yok. Kalite için çıkarımda classifier-free guidance kullanılır ama çekirdek eğitim objective'i teacher forcing ile next-token prediction'dır. Nature'da yayınlandı. Bu ders Emu3 tezini okur — daha iyi bir tokenizer artı ölçek tek ihtiyaçtır — ve diffusion yaklaşımlarıyla karşıtlık kurar.

**Tür:** Öğrenim
**Diller:** Python (stdlib, 3D video tokenizer matematiği + autoregressive sampler iskeleti)
**Ön koşullar:** Faz 12 · 11 (Chameleon)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Görsel kalitesi için diffusion'ın gerektiği uzun süredir tutulan varsayıma rağmen Emu3'ün tek-loss next-token objective'inin neden çalıştığını açıkla.
- 3D video tokenizer'ı betimle: spatiotemporal VQ codebook'unun neye benzediği, patch'lerin neden zamanı kapsadığı.
- Emu3'ü Stable Diffusion XL ile (eğitim compute'u, çıkarım maliyeti, kalite tavanı) karşılaştır.
- Aynı Emu3 modelinin oynadığı üç rolü söyle: Emu3-Gen (image gen), Emu3-Chat (algı), Emu3-Stage2 (video gen).

## Sorun

2024 boyunca geleneksel bilgi: görsel üretimi diffusion gerektirir. Argüman: ayrık görsel token'lar detayı yeniden inşa etmek için çok fazla bilgi kaybeder ve autoregressive sampling binlerce token boyunca hata biriktirir. Stable Diffusion, DALL-E 3, Imagen, Midjourney hepsi diffusion'ın bir formunu kullanıyor. Chameleon (Ders 12.11) bunu küçük ölçekte kısmen çürüttü ama kalitede SDXL'i eşleyemedi.

Emu3 argümana doğrudan saldırdı. İddia: daha iyi görsel tokenizer + yeterli ölçek + next-token loss = aynı modelde algı da yapan diffusion-yenen görsel üretimi.

Yayınlandığında bahis tartışmalıydı. İki yıl sonra, açık-kaynak birleştirilmiş-üretim ailesi (Emu3, Show-o, Janus-Pro, Transfusion) araştırma için varsayılan yol; üretim frontier modellerinin bir varyantını kullandığı görünüyor.

## Kavram

### Emu3 tokenizer

Anahtar bileşen görsel tokenizer. Emu3 token başına 8x8 çözünürlük azaltma ile özel bir IBQ sınıfı tokenizer (Inverse Bottleneck Quantizer, SBER-MoVQGAN ailesi) eğitir. 512x512 bir görsel codebook boyutu 32768'de 64x64 = 4096 token olur.

Bu Chameleon'ın K=8192'de 512x512 başına 1024 token'ından daha büyük ama token başına daha ucuz (daha küçük codebook lookup'ları, daha basit codec). Anahtar metrik: 30.5 dB yeniden inşa PSNR, Stable Diffusion'ın 32 dB sürekli latent uzayı ile rekabetçi.

Video için: 3D VQ tokenizer bir spatiotemporal patch'i (4x4x4 piksel) bir integer'a kodlar. 4s klip 8 FPS'te 32 frame'e sahip; 4x spatial ve 4x temporal azaltma ile 256x256'da, token sayısı (256/4) * (256/4) * (32/4) = 64 * 64 * 8 = 32,768 token.

Tokenizer kalitesi tavandır. Emu3'ün katkısı kısmen "çok iyi bir tokenizer eğittik."

### Tek-loss eğitim

Emu3 tek bir objective kullanır: metin token'ları, 2D görsel token'ları ve 3D video token'ları boyunca paylaşılan bir sözcükte next-token prediction. Eğitim sırasında katkıyı dengelemek için ağırlıklar modalite-spesifik faktörlerle çarpılır ama loss fonksiyonu özdeştir.

Şunların karışımında eğitir:
- Görsel gen: `<text caption> <image> image_tokens </image>`
- Görsel algı: `<image> image_tokens </image> <question> text_tokens`
- Video gen: `<text caption> <video> video_tokens </video>`
- Video algı: benzer.
- Yalnızca metin: standart NTP.

Model veri dağılımından metin token'ları vs görsel token'ları ne zaman yayacağını öğrenir. Üretim, modelin `<image>` etiketinden sonra görsel token'ları tahmin etmesinden emerge eder.

### Classifier-free guidance ve temperature

Autoregressive görsel üretimi çıkarımda classifier-free guidance (CFG) ile çok daha iyi olur. Emu3 kullanır: iki kere üret, bir kere tam caption ile, bir kere boş caption ile, logit'leri bir guidance ağırlığı (tipik 3.0-7.0) ile karıştır. Bu, diffusion'ın kullandığı aynı CFG hilesi, autoregressive ortama ödünç alındı.

Temperature önemli: çok yüksek, artifact'lar; çok düşük, mod collapse. Emu3'ün önerdiği temperature algı için 1.0, görsel üretimi için 0.8.

### Üç rol, tek model

Emu3 fonksiyonel olarak farklı üç API olarak gönderiliyor ama tek bir altta yatan ağırlık seti:

- Emu3-Gen. Görsel üretimi. Metin girer, görsel token çıkar.
- Emu3-Chat. VQA ve captioning. Görsel (token'lar) girer, metin çıkar.
- Emu3-Stage2. Video üretimi ve video VQA. Metin ya da video girer, metin ya da video çıkar.

Görev-spesifik head yok. Sadece farklı prompt şablonları. Aynı checkpoint.

### Benchmark'lar

Emu3 makalesinden (Eylül 2024):

- Görsel üretimi: MJHQ-30K FID'de SDXL'i yener (5.4 vs 5.6), GenEval genel (0.54 vs 0.55 — istatistiksel berabere) ve Deep-Eval'in compozite eş düzeyde.
- Görsel algı: VQAv2'de LLaVA-1.6'yı yener (75.1 vs 72.4) ve MMMU'da kabaca eşleşir.
- Video üretimi: Sora-çağı kamuya benchmark edilmiş modellerle rekabetçi FVD'de 4 saniyelik klip kalitesi.

Sayılar her zaman kazanmıyor — Emu3 burada bir puanı oradaki bir puanla takas ediyor — ama "next-token prediction tek ihtiyaçtır" iddiası modaliteler boyunca savunulabilir.

### Compute maliyeti

Emu3 7B parametreli bir modelle ~300 milyar multimodal token üzerinde eğitildi. GPU-saat kabaca Llama-2-7B pretraining'iyle karşılaştırılabilir (A100 sınıfı silikon üzerinde 2k-4k GPU-yıl). Stable Diffusion 3 gibi diffusion modelleri benzer bütçelerde eğitir ama ayrı metin encoder'lar ve daha karmaşık pipeline'lara ihtiyaç duyarlar.

Çıkarımda Emu3 görsel başına SDXL'den daha yavaş: 30 tok/s'de 4096 görsel token 512x512 görsel başına ~2 dakika, SDXL için 2-5 saniyeye karşı. Speculative decoding ve KV-cache optimizasyonu farkı daraltır ama kapatmaz. Autoregressive görsel gen compute-ağır; bu duran trade-off.

### Neden önemli

Emu3'ün derin katkısı kavramsal. Next-token prediction görsel üretiminde diffusion'ı eşleyecek kadar ölçeklenirse, birleştirilmiş-model yolu (tek loss, tek backbone, herhangi modalite) yapılabilir. Gelecek modellerin ayrı metin encoder'larına, ayrı diffusion scheduler'larına, ayrı VAE'lere ihtiyacı yok. Tek transformer, modalite başına tek tokenizer, ölçek.

Show-o, Janus-Pro ve InternVL-U hepsi bu teze inşa ediyor ya da meydan okuyor. Çinli lab'ler (BAAI, DeepSeek) 2025 boyunca bu yönde US lab'lerinden daha agresif yayınlıyor.

## Kullan

`code/main.py` iki oyuncak parça inşa eder:

- 2D vs 3D VQ tokenizer sayım hesaplayıcı: (resolution, patch, clip_length, FPS) verildiğinde görsel vs video için token sayılarını hesapla.
- Temperature'da classifier-free guidance ile autoregressive image-token sampler.

CFG implementasyonu Emu3'ün tarifiyle eşleşir — koşullu ve koşulsuz logit'leri bir guidance ağırlığıyla karıştır.

## Yayınla

Bu ders `outputs/skill-token-gen-cost-analyzer.md` üretir. Bir üretim ürünü spec'i (görsel ya da video, hedef çözünürlük, kalite katmanı, latency bütçesi) verildiğinde token sayılarını, çıkarım maliyetini hesaplar ve Emu3-family vs diffusion seçer.

## Alıştırmalar

1. Emu3 8x8 azaltmada 512x512 görsel başına 4096 token üretir. 1024x1024 ve 2048x2048 için eşdeğeri hesapla. Çıkarım latency'sine ne olur?

2. Video tokenizer üzerine Emu3 Bölüm 3.3'ü oku. 3D VQ patch shape'ini ve neden 8x8x1 değil 4x4x4 olduğunu betimle.

3. Classifier-free guidance ağırlığı 5.0 vs 3.0: hangi görsel etki? `code/main.py`'de matematiği izle.

4. 300B token'da Emu3-7B için eğitim FLOPs'unu hesapla ve Stable Diffusion 3 ile karşılaştır. Hangisi eğitmek için daha pahalıydı?

5. Emu3 FID'de SDXL'i yener ama uzmanlaşmış VLM'lere karşı VQAv2'de yenmez. Birleştirilmiş-loss yaklaşımının farklı benchmark'larda uzmanlara karşı neden farklı güçler gösterdiğini açıkla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Next-token prediction | "NTP" | Standart autoregressive loss: token[0..i] verildiğinde token[i+1]'i tahmin et; tokenize edildiğinde her modalite için çalışır |
| IBQ tokenizer | "Inverse bottleneck quantizer" | Chameleon'ınkinden daha büyük codebook'lar (32768+) ve daha iyi yeniden inşa içeren VQ-VAE sınıfı |
| 3D VQ | "Spatiotemporal quantizer" | (zaman, satır, sütun) ile indekslenmiş codebook; tek token 4x4x4 piksel küpünü kapsar |
| Classifier-free guidance | "CFG" | Koşullu ve koşulsuz logit'leri gamma ağırlığı ile karıştır; çıkarımda görsel kalitesini artırır |
| Birleştirilmiş sözcük | "Paylaşılan token'lar" | Metin + görsel + video hepsi aynı integer uzayından çekilir; model hangi modalite gelirse onu tahmin eder |
| MJHQ-30K | "Görsel gen benchmark'ı" | 30k prompt'lu Midjourney-kalite benchmark'ı; Emu3 burada FID raporluyor |

## İleri Okuma

- [Wang et al. — Emu3: Next-Token Prediction is All You Need (arXiv:2409.18869)](https://arxiv.org/abs/2409.18869)
- [Sun et al. — Emu: Generative Pretraining in Multimodality (arXiv:2307.05222)](https://arxiv.org/abs/2307.05222)
- [Liu et al. — LWM (arXiv:2402.08268)](https://arxiv.org/abs/2402.08268)
- [Yu et al. — MAGVIT-v2 (arXiv:2310.05737)](https://arxiv.org/abs/2310.05737)
- [Tian et al. — VAR (arXiv:2404.02905)](https://arxiv.org/abs/2404.02905)
