# Janus-Pro: Birleştirilmiş Multimodal Modeller için Decoupled Encoder'lar

> Birleştirilmiş multimodal modellerin kaçınılmaz bir gerilimi var. Anlama semantik feature'lar ister — kavram-seviye bilgi ile zengin SigLIP ya da DINOv2 çıkış vektörleri. Üretim reconstruction-dostu kodlar ister — net piksellere geri compose olan VQ token'ları. İki amaç tek encoder'da uyumlu değil. Janus (DeepSeek, Ekim 2024) ve Janus-Pro (DeepSeek, Ocak 2025) çözümün denemeyi bırakmak olduğunu savunur: iki encoder'ı decouple et. Görevler arası transformer gövdesini paylaş, ama anlamayı SigLIP üzerinden ve üretimi bir VQ tokenizer üzerinden yönlendir. 7B'de Janus-Pro GenEval'de DALL-E 3'ü yener, MMMU'da LLaVA'yı eşler. Bu ders bir encoder'ın başarısız olduğu yerde iki encoder'ın neden çalıştığını okur.

**Tür:** Yapım
**Diller:** Python (stdlib, dual-encoder routing + paylaşılan-gövde sinyali)
**Ön koşullar:** Faz 12 · 13 (Transfusion), Faz 12 · 14 (Show-o)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Tek paylaşılan encoder'ın anlama ya da üretim kalitesini neden taviz verdiğini açıkla.
- Janus-Pro'nun yönlendirmesini betimle: anlama için input tarafında SigLIP feature'ları, üretim için hem input hem output'ta VQ token'ları.
- Janus-Pro'nun Janus'un başaramadığı yerde başarılı olmasını sağlayan veri-karışım ölçeklemesini izle.
- Decoupled (Janus-Pro), coupled-continuous (Transfusion) ve coupled-discrete (Show-o) mimarileri karşılaştır.

## Sorun

Birleştirilmiş modeller anlama ve üretim boyunca transformer gövdesini paylaşır. Önceki denemeler (Chameleon, Show-o, Transfusion) hepsi iki yön için tek görsel tokenizer kullanır. Tokenizer bir taviz:

- Reconstruction (üretim) için optimize: VQ-VAE ince taneli piksel detayını yakalar ama zayıf semantik tutarlılığa sahip token üretir.
- Semantik (anlama) için optimize: SigLIP embedding'leri "kedi" görsellerini "kedi" token'larının yanına gruplar ama iyi reconstruction'a izin vermez.

Show-o ve Transfusion bunun için bir yönde görünür kalite vergisi öder. Janus-Pro soruyor: görevlerin farklı ihtiyaçları varsa neden tek tokenizer gerektir?

## Kavram

### Decoupled görsel kodlama

Janus-Pro'nun mimarisi iki encoder'ı ayırır:

- Anlama yolu. Input görsel → SigLIP-SO400m → 2 katmanlı MLP → transformer gövdesi.
- Üretim yolu. Input görsel (mevcut görsele koşulluysa) → VQ tokenizer → token ID'leri → transformer gövdesi.
- Output üretimi. Transformer tarafından tahmin edilen görsel token'ları → VQ decoder → pikseller.

Transformer gövdesi paylaşılıyor. Gövdenin yukarı ve aşağı akışındaki her şey görev-spesifik.

Input'lar prompt formatı tarafından ayrıştırılır: `<understand>` etiketi SigLIP üzerinden yönlendirir; `<generate>` VQ üzerinden yönlendirir. Ya da yönlendirme görevden implicit.

### Bu neden çalışır

Anlama loss'u SigLIP feature'ları alır, CLIP tarzı pretraining'in semantik benzerlik için tune ettiği. Modelin algı benchmark'ları Show-o / Transfusion üzerine iyileşir çünkü input feature'lar görev için daha iyi.

Üretim loss'u VQ token'ları alır, tokenizer'ın reconstruction için tune ettiği. Görsel kalitesi Show-o üzerine iyileşir çünkü VQ kodlar piksellere temiz compose olur.

Paylaşılan transformer gövdesi iki input dağılımı (SigLIP ve VQ) görür ve ikisiyle de çalışmayı öğrenir. İddia: yeterli veri + yeterli parametre, gövde değişimi emer.

### Veri ölçekleme — Janus vs Janus-Pro

Janus (orijinal, arXiv 2410.13848) decoupling'i tanıttı ama küçük ölçekte (1.3B param, sınırlı veri). Janus-Pro (arXiv 2501.17811) ölçekledi:

- 7B param (vs 1.3B).
- Aşama 1 (hizalama) için 72M'den 90M image-text çiftine.
- Aşama 2 (birleştirilmiş) için 26M'den 72M'ye.
- Aşama 3 için 200k image-gen instruction örneği ekledi.

Sonuç: Janus-Pro-7B MMMU'da LLaVA'yı eşler (60.3 vs ~58) ve GenEval'de DALL-E 3'ü yener (0.80 vs 0.67). Tek açık model, birleştirilmiş spektrumun iki tarafında da rekabetçi.

### JanusFlow — rectified flow varyantı

JanusFlow (arXiv 2411.07975) VQ üretim yolunu rectified-flow üretim yolu (sürekli) ile değiştirir. Bölünme SigLIP-for-understanding + rectified-flow-for-generation olur. Kalite tavanları daha da yükselir. Mimari decoupled-encoder-paylaşılan-gövde kalır.

### Paylaşılan gövdenin işi

Transformer gövdesi birleştirilmiş diziyi işler ama iki input dağılımıyla. İşi:

- Anlama için: SigLIP feature'ları + metin token'ları tüket → metni autoregressive yay.
- Üretim için: metin token'ları + (opsiyonel görsel VQ token'ları) tüket → görsel VQ token'larını autoregressive yay.

Gövdenin block başına modalite-spesifik ağırlığı yok. Qwen ya da Llama içinde bulmayı beklediğin metin tarzı transformer, artı iki input adapter'ı.

İlginç bir şekilde, bu Janus-Pro'nun gövdesinin pretrained bir LLM'den initialize edilebileceği anlamına gelir. Janus-Pro DeepSeek-MoE-7B'den initialize ediyor. O seçim önemli: LLM saf-sıfırdan birleştirilmiş modellerin erişmekte zorlandığı akıl yürütme yeteneğine katkıda bulunur.

### InternVL-U ile karşılaştırıldığında

InternVL-U (Ders 12.10) 2026 takibi. Şunları birleştirir:

- Native multimodal pretraining (InternVL3 backbone).
- Decoupled-encoder yönlendirmesi (SigLIP girer, VQ + diffusion head'leri çıkar).
- Birleştirilmiş anlama + üretim + düzenleme.

InternVL-U Janus-Pro'nun mimari seçimini daha büyük bir çerçeveye dahil eder. Decoupled-encoder fikri artık ölçekte birleştirilmiş modeller için varsayılan.

### Sınırlamalar

Decoupled encoder'lar mimari karmaşıklık ekler. Eğitilecek iki tokenizer, sürdürülecek iki input yolu, iki set fail mode. Üretime ihtiyacı olmayan ürünler için Janus-Pro fazla mühendislik ürünü — bir LLaVA-family anlama modeli seç.

Anlamaya ihtiyacı olmayan ürünler için Janus-Pro fazla nitelikli — bir Stable Diffusion 3 / Flux modeli seç.

İkisine birden ihtiyacı olan ürünler için Janus-Pro artık referans açık mimari.

## Kullan

`code/main.py` Janus-Pro yönlendirmesini simüle eder:

- İki mock encoder: SigLIP benzeri (256 boyutlu semantik vektör üretir) ve VQ benzeri (integer kod üretir).
- Bir görev etiketine göre encoder seçen prompt router.
- Hangi encoder'ın ürettiğinden bağımsız olarak token dizilerini işleyen paylaşılan gövde (yerine geçer).
- Aşama 1'den (hizalama) aşama 3'e (instruction tune) ağırlıklı-örnek programı geçiş.

3 örnek için yönlendirilen yolları yazdır: image QA, T2I, image editing.

## Yayınla

Bu ders `outputs/skill-decoupled-encoder-picker.md` üretir. Frontier-ish kalitede birleştirilmiş üretim + anlama isteyen bir ürün verildiğinde, Janus-Pro, JanusFlow ya da InternVL-U'yu somut bir veri-ölçek önerisiyle seçer.

## Alıştırmalar

1. Janus-Pro-7B GenEval'de DALL-E 3'ü yener. 7B açık modelin üretimde frontier bir proprietary modeli eşleyebilmesinin ama anlamada eşleyemiyor olmasının nedenini açıkla.

2. Bir router fonksiyonu uygula: prompt metni verildiğinde, `understand` ya da `generate` olarak sınıflandır. "Betimle ve sonra çiz" gibi belirsiz prompt'ları nasıl ele alıyorsun?

3. JanusFlow VQ yolunu rectified flow ile değiştirir. Transformer gövdesi şimdi ne çıkarır ve loss'ta ne değişir?

4. Bir decoupled encoder daha ile Janus-Pro mimarisinin ele alabileceği dördüncü bir görev öner. Örnekler: görsel segmentasyon (DINO tarzı), derinlik (MiDaS tarzı).

5. Janus-Pro Bölüm 4.2'yi veri ölçekleme üzerine oku. Hangi veri aşaması Janus'a karşı T2I kalite kazanımına en çok katkıda bulunuyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Decoupled encoding | "İki görsel encoder" | Yön başına ayrı tokenizer ya da encoder: anlama için semantik, üretim için reconstruction |
| Paylaşılan gövde | "Tek transformer" | Tek transformer her encoder'ın çıktısını işler; modalite-spesifik ağırlık yok |
| Anlama için SigLIP | "Semantik feature'lar" | Zengin kavramsal feature'lar sağlayan ama zayıf reconstruction'lı CLIP-family vision tower |
| Üretim için VQ | "Reconstruction kodları" | Piksellere temiz decode olan vector-quantized token'lar |
| JanusFlow | "Rectified-flow varyantı" | VQ yerine sürekli flow-matching generation head'li Janus-Pro |
| Routing tag | "Görev etiketi" | Input encoder'ı seçen prompt marker'ı (`<understand>` / `<generate>`) |

## İleri Okuma

- [Wu et al. — Janus (arXiv:2410.13848)](https://arxiv.org/abs/2410.13848)
- [Chen et al. — Janus-Pro (arXiv:2501.17811)](https://arxiv.org/abs/2501.17811)
- [Ma et al. — JanusFlow (arXiv:2411.07975)](https://arxiv.org/abs/2411.07975)
- [InternVL-U (arXiv:2603.09877)](https://arxiv.org/abs/2603.09877)
- [Dong et al. — DreamLLM (arXiv:2309.11499)](https://arxiv.org/abs/2309.11499)
