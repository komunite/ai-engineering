# LLM'lerde Bias ve Temsili Zarar

> Gallegos, Rossi, Barrow, Tanjim, Kim, Dernoncourt, Yu, Zhang, Ahmed (Computational Linguistics 2024, arXiv:2309.00770). Temsili zararları (stereotipler, silme) tahsisat zararlarından (eşitsiz kaynak dağılımı) ayıran ve değerlendirme metriklerini embedding-tabanlı, olasılık-tabanlı veya üretilen-metin-tabanlı olarak kategorize eden temel 2024 survey'i. 2024-2025 ampirik: An vd. (PNAS Nexus, Mart 2025) 20 entry-level iş için otomatik özgeçmiş değerlendirmesinde GPT-3.5 Turbo, GPT-4o, Gemini 1.5 Flash, Claude 3.5 Sonnet, Llama 3-70B arasında kesişimsel cinsiyet x ırk bias'ını ölçer. WinoIdentity (COLM 2025, arXiv:2508.07111) kesişimsel kimlikler için belirsizlik-tabanlı fairness değerlendirmesi tanıtır. Yu & Ananiadou 2025 MLP katmanlarında gender neuron'ları tanımlar; Ahsan & Wallace 2025 klinik ırk bias'ını ortaya çıkarmak için SAE'leri kullanır; Zhou vd. 2024 (UniBias) debiasing için attention head'leri manipüle eder. Meta-eleştiri (arXiv:2508.11067): 10 yıllık literatür orantısız olarak ikili-cinsiyet bias'ına odaklanır.

**Tür:** Yapım
**Diller:** Python (stdlib, oyuncak embedding-tabanlı bias probe'u)
**Ön koşullar:** Faz 05 (word embedding'ler), Faz 18 · 01 (instruction following)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Temsili vs tahsisat zararını tanımla ve her birinin bir LLM deployment'ında bir örneğini ver.
- Gallegos vd. 2024'ten üç değerlendirme-metriği kategorisini adlandır ve her birinden bir metriği tarif et.
- Kesişimselliği ve WinoIdentity'nin belirsizlik-tabanlı fairness ölçümünün tek-eksenli bias değerlendirmesindeki boşlukları neden ele aldığını tarif et.
- Bias'a iki mechanistic-interpretability yaklaşımını (gender neuron'ları, SAE özellikleri, attention-head manipülasyonu) tarif et.

## Sorun

Önceki dersler kasıtlı zararı (jailbreak'ler, scheming) ve safety yönetişimini kapsar. Bias niyet olmadan ortaya çıkan zarardır — eğitim verisi dağılımlarından, prompt çerçevelemesinden, birikmiş tasarım seçimlerinden. Onu ölçmek ve azaltmak adversarial sağlamlıktan farklı metodolojik bir zorluktur.

## Kavram

### Temsili vs tahsisat

- **Temsili zarar.** Stereotipler, silme, küçük düşürücü tasvirler. Hemşireleri yalnızca kadın olarak tasvir eden bir LLM temsili zarar üretiyor.
- **Tahsisat zararı.** Eşitsiz maddi sonuçlar. Siyah başvuranların özgeçmişlerini sistematik olarak daha düşük puanlayan bir LLM tahsisat zararı üretiyor.

Bunlar aynı değil. Bir model "temsili olarak yanlılıksız" (çeşitli tasvirler üretir) iken "tahsisat olarak yanlı" (eşitsiz öneriler yapar) olabilir. Değerlendirmeler her ikisini de ölçmeli.

### Üç değerlendirme-metriği kategorisi (Gallegos vd. 2024)

- **Embedding-tabanlı.** Pre-RLHF embedding'lerde WEAT-tarzı testler. Kimlik terimleri ve nitelik terimleri arasındaki istatistiksel ilişkileri ölçer. Limitli: temsili ölçer, davranışı değil.
- **Olasılık-tabanlı.** Stereotipi doğrulayıcı vs stereotipi ihlal edici tamamlamaların log-likelihood'u. Decoder-tarafı ölçüm. Bazı davranışsal bias'ı yakalar.
- **Üretilen-metin-tabanlı.** Üretilen metinde downstream-görev ölçümü. Özgeçmiş puanlama, tavsiye yazma, diyalog. En çok ekolojik olarak geçerli; tekrar üretmesi en zor.

### Kesişimsellik

"Cinsiyet"te bias değerlendirmesi yalnızca (cinsiyet, ırk) çiftlerinde ateşlenen bias'ı kaçırır. An vd. 2025 GPT-4o'nun özgeçmiş puanlamasında Siyah kadınları Siyah erkeklerden ve beyaz kadınlardan ayrı ayrı daha fazla cezalandırdığını buluyor. Tek-eksenli değerlendirme bunu yakalayamaz.

WinoIdentity (COLM 2025) belirsizlik-tabanlı kesişimsel fairness tanıtır. Modelin sonuçlar üzerindeki belirsizliğinin kesişimsel kimlik tuple'ları arasında farklı olup olmadığını ölçer — yalnızca nokta tahmini değil. Bu modelin gruplar arasında eşit yanlış olduğu ama bazıları için daha belirsiz olduğu durumları yakalar, ki bu farklı downstream tahsisat davranışı üretir.

### Mechanistic yaklaşımlar

2024-2025 interpretability çalışması bias'ı mechanistic müdahaleye açar:

- **Gender neuron'lar (Yu & Ananiadou 2025).** Spesifik MLP nöronları cinsiyet-özgü davranışlarla korele. Bu nöronları ablate etmek sınırlı capability maliyetiyle gender-gap metriklerini azaltır.
- **SAE'lerle klinik ırk bias'ı (Ahsan & Wallace 2025).** Sparse autoencoder özellikleri internal temsili yorumlanabilir boyutlara ayrıştırır; ırk-korele özellikler tanımlanabilir ve bastırılabilir.
- **UniBias (Zhou vd. 2024).** Zero-shot debiasing için attention-head manipülasyonu. Spesifik head'ler kimlik-sınıfı duyarlılığını amplifiye eder; bu head'leri sıfırlamak veya yeniden ağırlıklandırmak fine-tuning olmadan bias'ı azaltır.

### Meta-eleştiri

10 yıllık literatür incelemesi (arXiv:2508.11067, 2025) alanın orantısız olarak ikili-cinsiyet bias'ına odaklandığını buluyor. Diğer eksenler — engellilik, din, göç durumu, çok-dilli kimlik — çok daha az dikkat alır. Meta-eleştiri dar odaklılığın ihmal yoluyla marjinalleştirilmiş gruplara zarar verebileceğini savunur: ikili cinsiyette iyi debiased bir model kimsenin kontrol etmediği boyutlarda kötü yanlı olabilir.

### Bu Faz 18'de nereye uyuyor

Dersler 20-21 bias ve fairness'ı formel olarak kapsar. Ders 22 gizliliği kapsar. Ders 23 watermarking'i kapsar. Bunlar önceki aldatma/safety katmanını tamamlayan kullanıcı-zarar katmanıdır.

## Kullan

`code/main.py` oyuncak bir embedding-tabanlı bias probe'u inşa eder: basit bir co-occurrence embedding'de kimlik terimleri ve nitelik terimleri arasında WEAT-tarzı mesafeyi ölç. Bir bias enjekte edebilir ve metriğin ateşlendiğini gözlemleyebilirsin; basit bir debiasing operasyonu uygulayabilir ve kısmi kurtarmayı gözlemleyebilirsin.

## Yayınla

Bu ders `outputs/skill-bias-eval.md` üretir. Bir model card veya fairness iddiası verildiğinde, üç metrik kategorisi (embedding, olasılık, üretilen-metin) arasında değerlendirmeyi, kesişimsellik kapsamını ve herhangi bir debiasing müdahalesinin mekanizmasını audit eder.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Debiasing adımından önce ve sonra WEAT-tarzı bias skorlarını raporla. Metriğin neden sıfıra düşmediğini açıkla.

2. Probe'u kesişimsel bir testle genişlet: (cinsiyet, ırk) x (kariyer, aile). Cross-eksen bias skorlarını raporla.

3. An vd. 2025'i (PNAS Nexus) oku. Tek-eksenli cinsiyet değerlendirmesinin kaçıracağı iki kesişimsel etkiyi raporladıkları tanımla.

4. Yu & Ananiadou 2025 gender neuron'lar tanımlar. "Bu nöronlar gender bias'a neden olur"u "bu nöronlar gender bias ile koreledir"den ayıracak bir yanlışlama deneyi çiz.

5. Meta-eleştiri alanın ikili cinsiyete çok dar odaklandığını savunur. Az çalışılmış bir eksen seç ve onun için bir temsili-zarar ölçüm protokolü tarif et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| Temsili zarar | "stereotipler / silme" | Bir grubun yanlı tasviri |
| Tahsisat zararı | "eşitsiz kararlar" | Bir grup için yanlı maddi sonuç |
| WEAT | "embedding testi" | Word Embedding Association Test; co-occurrence-tabanlı bias probe'u |
| Kesişimsellik | "birleşik kimlik etkileri" | Birden çok kimlik ekseninin kesişiminde ortaya çıkan bias |
| Gender neuron'lar | "MLP bias nöronları" | Aktivasyonları cinsiyet-özgü davranışla korele olan spesifik nöronlar |
| SAE özelliği | "yorumlanabilir boyut" | Sparse-autoencoder-tanımlı özellik; mechanistic bias analizi için yararlı |
| UniBias | "attention-head debiasing'i" | Attention head'leri yeniden ağırlıklandırarak zero-shot debiasing |

## İleri Okuma

- [Gallegos et al. — Bias and Fairness in LLMs: A Survey (arXiv:2309.00770, Computational Linguistics 2024)](https://arxiv.org/abs/2309.00770) — kanonik survey
- [An et al. — Intersectional resume-evaluation bias (PNAS Nexus, March 2025)](https://academic.oup.com/pnasnexus/article/4/3/pgaf089/8111343) — beş-modelli kesişimsel çalışma
- [WinoIdentity — uncertainty-based intersectional fairness (arXiv:2508.07111, COLM 2025)](https://arxiv.org/abs/2508.07111) — yeni benchmark
- [UniBias — attention-head manipulation (Zhou et al. 2024, ACL)](https://arxiv.org/abs/2405.20612) — zero-shot debiasing
