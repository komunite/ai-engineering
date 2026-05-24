# Scaling Laws

> 2020 Kaplan makalesi dedi ki: daha büyük model, daha düşük loss. 2022 Hoffmann makalesi dedi ki: az eğitiyordun. Compute iki kovaya gider — parametreler ve token'lar — ve ayırım barız değil.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 7 · 05 (Tam Transformer), Faz 7 · 07 (GPT)
**Süre:** ~45 dakika

## Sorun

C FLOPs eğitim compute'una sahipsen ve en iyi modeli istiyorsan, iki düğmeyle karşı karşıyasın:

1. **Kaç parametre (N)?** Daha büyük model, daha yüksek kapasite.
2. **Kaç eğitim token'ı (D)?** Daha çok veri, kapasitenin daha iyi kullanımı.

FLOPs yaklaşık olarak `6 × N × D` olarak ölçeklenir. N'i yukarı D'yi aşağı veya D'yi yukarı N'i aşağı itebilirsin. Hangisi daha iyi?

2022'den önce, cevap "N'i sert it"ti. GPT-3 (2020), ~300B token üzerinde eğitilen 175B parametreydi. Parametre başına yaklaşık 1.7 token oranı. Kaplan scaling laws bunu destekledi.

Hoffmann et al. (2022), Chinchilla denen küçük bir model ailesini eğiterek farklı bir şey buldu: optimal oran **parametre başına 20 token**'a daha yakın. GPT-3 10× az eğitilmişti. Chinchilla (70B param, 1.4T token), 2.5× daha az çıkarım maliyetinde her benchmark'ta GPT-3'ü (175B, 300B token) yendi.

2026 Chinchilla'nın dünyasıdır — bir önemli kıvrımla. Llama 3 8B, parametre başına 1.875 token oranıyla 15 trilyon token üzerinde eğitildi. Chinchilla-optimal'in doksan dört katı ötesi. Ölçekte kullanılacak modeller için çıkarım maliyeti eğitim maliyetinden daha önemli, dolayısıyla daha küçük dağıtılabilir bir ayak izi için aşırı-eğitim (Chinchilla'nın ötesinde) 2026 varsayılanıdır.

## Kavram

![Chinchilla eğrileri: çeşitli N/D oranlarında loss vs compute](../assets/scaling-laws.svg)

### Hoffmann yasası

Chinchilla makalesinden, loss şunu takip eder:

```
L(N, D) = A / N^α + B / D^β + E
```

- `N` = parametreler (embedding-dışı).
- `D` = eğitim token'ları.
- `α ≈ 0.34`, `β ≈ 0.28` (kabaca simetrik).
- `E ≈ 1.69`, indirgenemez loss tavanı.
- `A ≈ 406`, `B ≈ 411`.

Ölçeklendikçe iki terim birbiriyle takas yapar. Sabit compute'ta (C = 6ND) `N`'e göre türevi al ve çöz:

```
N_opt ≈ 0.6 × (C/6)^0.5
D_opt ≈ 0.6 × (C/6)^0.5
D_opt / N_opt ≈ 20
```

Compute-optimal: parametre başına 20 token.

### Yine de neden aşırı-eğitim

Chinchilla-optimal, eğitim FLOP başına eğitim loss'unu minimize eder. Ama eğitim maliyetini bir kere ödersin; çıkarım maliyetini sonsuza dek.

Ayda trilyon token serve eden bir sohbet botu için, çıkarım toplam maliyete hakimdir. Llama'nın yaklaşımı: daha küçük, daha uzun eğit. 15T token'da 8B derinlemesine çıkarım-optimize edilmiştir:

- Tüketici GPU'larına sığar.
- Latency, 70B Chinchilla-optimal'in bir kesridir.
- Çoğu görev için kalite yeterince yakındır.

DeepMind'ın 2024 makalesi ("Aşırı-eğitim yeni optimaldir") bunu formalize etti. Çıkarım-baskın workload'lar için, doğru oran serving hacmine bağlı olarak parametre başına 100–500 token'a daha yakındır.

### Emergence vs düzgünlük

İddia: belirli yetenekler (aritmetik, çok adımlı akıl yürütme, chain-of-thought takibi) bir ölçekte aniden "ortaya çıkar".

Schaeffer et al. (2023) bunun bir ölçüm artefaktı olduğunu savundu: emergent metrikler, alttaki logit'lerdeki düzgün iyileşmeyi gizleyen kesintili skorlama (exact match, eşikte doğruluk) kullanır. Sürekli metrikler (cross-entropy) düzgün eğriler gösterir.

2026'da konsensüs: sürekli loss üzerinden tahminler güvenilirdir. Benchmark sıçramaları genellikle scorer artefaktlarıdır. Bütçeleri sürekli metriklere karşı planla.

### 2026 resmi

Scaling laws hâlâ çalışıyor, ama:

| Faktör | Nasıl değişti |
|--------|-------------|
| Veri kalitesi | "İyi" token'ları küratörlemek (Phi tarzı) eğrileri >2× efektif compute kadar kaydırır |
| MoE | Toplam parametreler aktif FLOPs'tan ayrılır; aktif-FLOP başına scaling laws |
| Post-training | Bazı yetenekler (instruction following, kod) pretraining'den çok SFT+RLHF ile kayar |
| Multimodalite | Görüntü + metin token'ları birlikte ölçeklenir; modalite başına ayrı eğriler |
| Sentetik veri | Modeller eğitim verisi üretir; efektif compute artabilir |

Muon optimizer (Kimi Moonlight, 2024) eşleşen veride AdamW üzerinde ~2× efektif-compute kazancı gösterdi. Bazı 2026 eğitim koşuları Muon'u varsayılan olarak kullanır. Scaling law'un mutlak sabitini değiştirir, şeklini değil.

## İnşa Et

`code/main.py`'a bak. Chinchilla loss denklemini implement ediyoruz ve birkaç compute bütçesinin her birinde compute-optimal `(N, D)` için çözüyoruz.

### Adım 1: Chinchilla loss

```python
def chinchilla_loss(N, D, A=406.4, B=410.7, alpha=0.34, beta=0.28, E=1.69):
    return A / N ** alpha + B / D ** beta + E
```

Sabit `C = 6ND`'de `(N, D)` üzerinde `L`'yi bir kontur olarak çiz. Minimum'u bul.

### Adım 2: compute-optimal frontier

`1e17`'den `1e25` FLOPs'a compute bütçeleri için, `6ND = C` kısıtlamasına tabi olarak loss'u minimize eden `(N, D)`'yi bul. Oran `D/N ≈ 20`'yi doğrula.

### Adım 3: aşırı-eğitim maliyeti

10× daha küçük bir model (optimal N'in 1/10'u, optimal D'nin 10×'i) eğitmek için ödediğin ekstra loss'u hesapla. Karşılığında çıkarım FLOP tasarrufunu (N ile orantılı) raporlar.

### Adım 4: gerçek modellerle karşılaştır

GPT-3, Chinchilla, Llama 3 8B, DeepSeek-V3 (aktif parametre) için bilinen `(N, D)` çiftlerini sok ve tahmin edilen vs raporlanan loss'u karşılaştır.

## Kullan

Kendin bir frontier model eğitmen olası değil. Ama scaling laws sana söyler:

1. **Fine-tune'un yeterli veriye sahip mi.** Göreve özgü verin temel modelin parametre başına 20 token'ın altındaysa, bir loss tabanında doygunluk bekle.
2. **Daha büyük bir base model seçilip seçilmeyeceği.** Tüm bütçeni çıkarımda harcıyorsan, daha küçük, daha uzun eğitilmiş bir modeli tercih et.
3. **Getirilerin azaldığı yer.** Chinchilla-optimal'in 1000× ötesinde, log-loss değişimleri gürültü olur.

**2026'da araştırma trajektörisi:**

- **Veri-kısıtlı rejim.** Web'in sınırlı sayıda yüksek-kalite token'ı var (filtrelemeden sonra ~5–10 trilyon İngilizce). Frontier pretraining bu tavana yaklaşıyor. Sentetik veri, çok dilli, çok modal ve RLHF-ölçeklenmiş fine-tuning sonraki manivelalardır.
- **Compute-çarpan numaraları.** Muon optimizer, MoE, daha iyi veri küratörleme — her biri mutlak sabitleri kaydırır, asimptotu değil.
- **RL için scaling laws.** Açık soru. Erken kanıt RL sample'larında power-law öneriyor ama pretraining'den çok farklı üslerle.

## Yayınla

`outputs/skill-training-budget-estimator.md`'ye bak. Skill, compute bütçesi, dağıtım kısıtları ve hedef loss verilen yeni bir eğitim koşusu için `(N, D, saat, GPU)` seçer.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır. `1e20`, `1e22`, `1e24` compute bütçeleri için Chinchilla-optimal `(N, D)`'yi yazdır. Gerçek model tablosuyla karşılaştır.
2. **Orta.** Hoffmann compute'un fonksiyonu olarak loss eğrisini implement et. Compute-optimal frontier için loss vs `log10(C)` çiz. Yasanın cross-entropy'de bir sonraki 0.1 indirim için `>10^28` FLOPs gerekeceğini tahmin ettiği yeri tanımla.
3. **Zor.** Aynı veri setinde eğitilmiş 5 minik modelde (100K'dan 10M parametreye) kendi scaling law'ını fit et. `α` ve `E`'yi tahmin et. Üslerin yayınlanmış olanlarla ne kadar iyi eşleşiyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Parametreler (N) | "Model boyutu" | Embedding-dışı ağırlık sayısı; kapasiteyi belirler. |
| Token'lar (D) | "Eğitim verisi" | Görülen eğitim token'ı sayısı; parametrelerin ne kadar iyi kullanıldığını belirler. |
| Compute (C) | "Harcanan FLOPs" | Standart transformer için yaklaşık `6 × N × D`. |
| Chinchilla-optimal | "D/N ≈ 20" | Pretraining FLOP başına loss'u minimize eden oran. |
| Aşırı-eğitim | "Chinchilla'nın ötesi" | Çıkarım FLOPs'unu tasarruf etmek için ekstra eğitim FLOPs'u harca; D/N >> 20. |
| İndirgenemez loss | "Taban" | Scaling law'daki `E` terimi; verinin kendi entropisi. |
| Emergent yetenek | "Ölçekte ani sıçramalar" | Genelde scorer artefaktı; sürekli loss düzgündür. |
| Efektif compute | "Eğitim-verimliliği çarpanı" | Daha iyi veri / optimizer / mimari bir FLOP'un ne kadar gideceğini çarpar. |

## İleri Okuma

- [Kaplan et al. (2020). Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) — ilk scaling law makalesi; az eğitilmiş.
- [Hoffmann et al. (2022). Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556) — Chinchilla.
- [Schaeffer et al. (2023). Are Emergent Abilities of Large Language Models a Mirage?](https://arxiv.org/abs/2304.15004) — ölçüm artefaktı olarak emergence.
- [Sardana, Frankle (2024). Beyond Chinchilla-Optimal: Accounting for Inference in Language Model Scaling Laws](https://arxiv.org/abs/2401.00448) — Llama'nın aşırı-eğitiminin workload'u için neden doğru olduğu.
- [Jordan et al. (2024). Muon: An optimizer for hidden layers in neural networks](https://kellerjordan.github.io/posts/muon/) — 2× compute çarpanı.
