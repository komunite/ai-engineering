# Değerlendirme — FID, CLIP Score, İnsan Tercihi

> Her üretken model leaderboard'u FID, CLIP score ve bir insan-tercihi arenasından bir win rate alıntılar. Her sayının kararlı bir araştırmacının game edebileceği bir başarısızlık modu vardır. Başarısızlık modlarını bilmiyorsan, gerçek bir iyileşmeyi bir gaming koşusundan ayıramazsın.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 8 · 01 (Taksonomi), Faz 2 · 04 (Değerlendirme Metrikleri)
**Süre:** ~45 dakika

## Sorun

Bir üretken model *örnek kalitesi* ve *koşullama sadakati* üzerinden yargılanır. Hiçbirinin closed-form ölçüsü yok. Modelin 10,000 görsel render etmek zorunda; bir şeyin onlara sayı atfetmesi gerek; bu sayılara model aileleri, çözünürlükler, mimariler boyunca güvenmen lazım. 2014-2026 sınamasını üç metrik atlattı:

- **FID (Fréchet Inception Distance).** Bir Inception ağının feature uzayında iki dağılım arasındaki uzaklık — gerçek ve üretilen. Düşük daha iyi.
- **CLIP score.** Üretilen bir görselin CLIP-image embedding'i ile bir prompt'un CLIP-text embedding'i arasındaki kosinüs benzerliği. Yüksek daha iyi. Prompt sadakatini ölçer.
- **İnsan tercihi.** İki modeli aynı prompt üzerinde kafa kafaya yarıştır, insanlara (ya da bir GPT-4 sınıfı modele) daha iyisini seçtir, bir Elo skoruna topla.

Ayrıca şunları göreceksin: IS (inception score, büyük ölçüde emekli), KID, CMMD, ImageReward, PickScore, HPSv2, MJHQ-30k. Her biri öncekinin bir başarısızlığını düzeltir.

## Kavram

![FID, CLIP ve tercih: üç eksen, farklı başarısızlık modları](../assets/evaluation.svg)

### FID — örnek kalitesi

Heusel et al. (2017). Adımlar:

1. N gerçek görsel ve N üretilen için Inception-v3 feature'ları (2048-D) çıkar.
2. Her havuza bir Gaussian fit et: ortalama `μ_r, μ_g` ve kovaryans `Σ_r, Σ_g` hesapla.
3. FID = `||μ_r - μ_g||² + Tr(Σ_r + Σ_g - 2 · (Σ_r · Σ_g)^0.5)`.

Yorum: feature uzayında iki çok değişkenli Gaussian arasında Fréchet uzaklığı. Daha düşük = daha benzer dağılımlar.

Başarısızlık modları:
- **Küçük N'de yanlı.** FID feature dağılımı üzerinde mean-squared'dır — küçük N kovaryansı eksik tahmin eder, yanlış düşük FID verir. Her zaman N ≥ 10,000 kullan.
- **Inception'a bağımlı.** Inception-v3 ImageNet üzerinde eğitildi. ImageNet'ten uzak alanlar (yüzler, sanat, metin görselleri) anlamsız FID üretir. Alana özgü bir feature extractor kullan.
- **Gaming.** Inception prior'una overfitting görsel kalite iyileşmesi olmadan düşük FID verir. CMMD ile (aşağıda) yen.

### CLIP score — prompt sadakati

Radford et al. (2021). Üretilen bir görsel + prompt için:

```
clip_score = cos_sim( CLIP_image(x_gen), CLIP_text(prompt) )
```

30k üretilen görselde ortala → modeller arasında karşılaştırılabilir bir skaler.

Başarısızlık modları:
- **CLIP'in kendi kör noktaları.** CLIP zayıf kompozisyonel akıl yürütmeye sahip ("mavi bir küre üzerinde kırmızı bir küp" sık başarısız olur). Modeller karmaşık prompt'ları gerçekten takip etmeden CLIP score'da iyi sıralanabilir.
- **Kısa prompt yanlılığı.** Kısa prompt'ların vahşi doğada daha fazla CLIP-image eşleşmesi var. Daha uzun prompt'lar mekanik olarak daha düşük CLIP score'a sahip.
- **Prompt gaming.** Prompt'a "yüksek kalite, 4k, başyapıt" eklemek görsel-metin bağlamasını iyileştirmeden CLIP score'u şişirir.

CMMD (Jayasumana et al., 2024) bunların bazılarını düzeltir: Inception yerine CLIP feature'ları, Fréchet yerine maximum-mean discrepancy kullanır. İnce kalite farklarını tespit etmekte daha iyi.

### İnsan tercihi — ground truth

Bir prompt havuzu seç. Model A ve model B ile üret. Çiftleri insanlara (ya da güçlü bir LLM yargıca) göster. Zaferleri bir Elo ya da Bradley-Terry skoruna topla. Benchmark'lar:

- **PartiPrompts (Google)**: 1,600 çeşitli prompt, 12 kategori.
- **HPSv2**: 107k insan anotasyonu, otomatik proxy olarak yaygın kullanılır.
- **ImageReward**: 137k prompt-görsel tercih çifti, MIT lisanslı.
- **PickScore**: Pick-a-Pic 2.6M tercih üzerinde eğitildi.
- **Chatbot-Arena tarzı görsel arenalar**: https://imagearena.ai/ ve diğerleri.

Başarısızlık modları:
- **Yargıç varyansı.** Uzman olmayanların uzmanlardan farklı tercihleri var. İkisini de kullan.
- **Prompt dağılımı.** Cherry-pick edilmiş prompt'lar bir aileyi kayırır. Her zaman belgele.
- **LLM-yargıç reward hacking.** GPT-4-yargıç güzel-ama-yanlış çıktılar tarafından kandırılır. İnsanla triangüle et.

## Birlikte kullan

Bir üretim eval raporu şunları içermeli:

1. Held-out gerçek dağılıma karşı 10-30k örnek üzerinde FID (örnek kalitesi).
2. Aynı örnekler üzerinde prompt'larına karşı CLIP score / CMMD (sadakat).
3. Önceki modele karşı blinded bir arenada win rate (genel tercih).
4. Başarısızlık modu analizi: rastgele örneklenmiş 50 çıktı, bilinen sorunlar için işaretlenmiş (el anatomisi, metin rendering'i, tutarlı nesne sayısı).

Herhangi bir tek metrik yalandır. Üç destekleyici metrik + niteliksel inceleme bir iddia.

## İnşa Et

`code/main.py` sentetik "feature vektörleri" üzerinde FID, CLIP-score benzeri ve Elo toplamı uygular (Inception feature'ları yerine 4-D vektörler kullanıyoruz). Şunları görürsün:

- Küçük N'de ve büyük N'de FID hesabı — yanlılık.
- Feature havuzları arasında kosinüs benzerliği olarak "CLIP score".
- Sentetik bir tercih stream'inden Elo güncelleme kuralı.

### Adım 1: dört satırda FID

```python
def fid(real_features, gen_features):
    mu_r, cov_r = mean_and_cov(real_features)
    mu_g, cov_g = mean_and_cov(gen_features)
    mean_diff = sum((a - b) ** 2 for a, b in zip(mu_r, mu_g))
    trace_term = trace(cov_r) + trace(cov_g) - 2 * sqrt_cov_product(cov_r, cov_g)
    return mean_diff + trace_term
```

### Adım 2: CLIP-stil kosinüs benzerliği

```python
def clip_like(image_feat, text_feat):
    dot = sum(a * b for a, b in zip(image_feat, text_feat))
    norm = math.sqrt(dot_self(image_feat) * dot_self(text_feat))
    return dot / max(norm, 1e-8)
```

### Adım 3: Elo toplama

```python
def elo_update(r_a, r_b, winner, k=32):
    expected_a = 1 / (1 + 10 ** ((r_b - r_a) / 400))
    actual_a = 1.0 if winner == "a" else 0.0
    r_a_new = r_a + k * (actual_a - expected_a)
    r_b_new = r_b - k * (actual_a - expected_a)
    return r_a_new, r_b_new
```

## Tuzaklar

- **N=1000'de FID.** Sezgi N=10k altında güvenilmez. Düşük-N FID raporlayan makaleler gaming yapıyor.
- **Çözünürlükler arası FID karşılaştırması.** Inception'ın 299×299 resize'ı feature dağılımını değiştirir. Sadece eşleşen çözünürlükte karşılaştır.
- **Tek seed raporlamak.** Minimum 3 seed çalıştır. Std raporla.
- **Negative prompt ile CLIP score şişirme.** Bazı pipeline'lar prompt'a overfit ederek CLIP'i yükseltir. Görsel doygunluk için kontrol et.
- **Prompt çakışmasından Elo yanlılığı.** Her iki model de eğitim sırasında bir benchmark prompt'u gördüyse, Elo anlamsız. Held-out prompt setleri kullan.
- **Ücretli kalabalık insan eval kayması.** Prolific, MTurk anotatörleri daha genç / tekno-dostuna kayar. İşe alınan sanat/tasarım uzmanlarıyla karıştır.

## Kullan

2026'da üretim eval protokolü:

| Sütun | Minimum | Önerilen |
|--------|---------|-------------|
| Örnek kalitesi | Held-out gerçeğe karşı 10k FID | + 5k CMMD + kategori başına alt-küme FID |
| Prompt sadakati | 30k CLIP score | + HPSv2 + ImageReward + VQA-stil soru cevaplama |
| Tercih | Baseline'a karşı 200 blinded çift | + 2000 eşli insan + LLM-yargıç + Chatbot Arena |
| Başarısızlık analizi | Elle işaretlenmiş 50 | Elle işaretlenmiş 500 + otomatik güvenlik sınıflandırıcısı |

Tek raporda dört sütun = iddia. Tek başına herhangi biri = pazarlama.

## Yayınla

`outputs/skill-eval-report.md` olarak kaydet. Skill yeni bir model checkpoint + baseline alır ve tam eval planını çıkarır: örnek boyutları, metrikler, başarısızlık-modu probe'ları, sign-off kriterleri.

## Alıştırmalar

1. **(Kolay)** `code/main.py`'yi çalıştır. Aynı sentetik dağılımlarda N=100 vs N=1000'de FID'yi karşılaştır. Yanlılık büyüklüğünü raporla.
2. **(Orta)** Sentetik CLIP-stil feature'lardan CMMD uygula (formül için Jayasumana et al., 2024). FID'ye karşı kalite farklarına olan hassasiyeti karşılaştır.
3. **(Zor)** HPSv2 kurulumunu çoğalt: Pick-a-Pic'in bir alt-kümesinden 1000 görsel-prompt çifti al, tercihler üzerinde küçük bir CLIP-tabanlı scorer fine-tune et ve held-out bir setle anlaşmasını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| FID | "Fréchet Inception Distance" | Gerçek vs üretilen Inception feature'larına Gaussian fit'lerinin Fréchet uzaklığı. |
| CLIP score | "Metin-görsel benzerliği" | CLIP image ve text embedding'leri arasında kosinüs benzerliği. |
| CMMD | "FID'nin yerine geçen" | CLIP-feature MMD; daha az yanlı, Gaussian varsayımı yok. |
| IS | "Inception score" | Exp KL(p(y|x) || p(y)); modern modellerde kötü korele, emekli. |
| HPSv2 / ImageReward / PickScore | "Öğrenilmiş tercih proxy'leri" | İnsan tercihleri üzerinde eğitilmiş küçük modeller; otomatik yargıç olarak kullanılır. |
| Elo | "Satranç derecesi" | İkili kazançların Bradley-Terry toplamı. |
| PartiPrompts | "Benchmark prompt seti" | 12 kategoride Google küratörlü 1,600 prompt. |
| FD-DINO | "Self-sup yerine geçen" | DINOv2 feature'larını kullanan FD; ImageNet-dışı alanlar için daha iyi. |

## Üretim notu: değerlendirme de bir çıkarım iş yüküdür

10k örnek üzerinde FID çalıştırmak 10k görsel üretmek demek. Tek L4'te 1024²'de 50-adımlık SDXL base için bu ~11 saatlik tek-istek çıkarımı. Eval bütçeleri gerçek ve çerçeveleme tam olarak offline-çıkarım senaryosu (throughput'u maksimize et, TTFT'yi yok say):

- **Sıkı batch'le, latency'yi unut.** Offline eval = belleğe sığan en büyük boyutta statik batching. 80GB H100 üzerinde `pipe(...).images` `num_images_per_prompt=8` ile tek-istek'ten 4-6× daha hızlı duvar-saati çalışır.
- **Gerçek feature'ları cache'le.** Gerçek referans seti üzerinde Inception (FID) ya da CLIP (CLIP-score, CMMD) feature çıkarımı *bir kez* çalıştırılır, bir `.npz`'ye saklanır. Eval başına yeniden hesaplama.

CI / regression kapıları için: PR başına 500 örneklik alt küme üzerinde FID + CLIP score çalıştır (~30 dk); gecelik tam 10k FID + HPSv2 + Elo çalıştır.

## İleri Okuma

- [Heusel et al. (2017). GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID)](https://arxiv.org/abs/1706.08500) — FID makalesi.
- [Jayasumana et al. (2024). Rethinking FID: Towards a Better Evaluation Metric for Image Generation (CMMD)](https://arxiv.org/abs/2401.09603) — CMMD.
- [Radford et al. (2021). Learning Transferable Visual Models from Natural Language Supervision (CLIP)](https://arxiv.org/abs/2103.00020) — CLIP.
- [Wu et al. (2023). HPSv2: A Comprehensive Human Preference Score](https://arxiv.org/abs/2306.09341) — HPSv2.
- [Xu et al. (2023). ImageReward: Learning and Evaluating Human Preferences for Text-to-Image Generation](https://arxiv.org/abs/2304.05977) — ImageReward.
- [Yu et al. (2023). Scaling Autoregressive Models for Content-Rich Text-to-Image Generation (Parti + PartiPrompts)](https://arxiv.org/abs/2206.10789) — PartiPrompts.
- [Stein et al. (2023). Exposing flaws of generative model evaluation metrics](https://arxiv.org/abs/2306.04675) — başarısızlık-modu araştırması.
