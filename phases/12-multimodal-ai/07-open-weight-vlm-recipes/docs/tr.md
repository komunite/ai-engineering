# Open-Weight VLM Tarifleri: Gerçekte Ne Önemli

> 2024-2026 open-weight VLM literatürü bir ablasyon tablosu ormanı. Apple'ın MM1'i image encoder, connector ve veri karışımının 13 kombinasyonunu test etti. Allen AI'ın Molmo'su detaylı insan caption'larının GPT-4V distillation'ı yendiğini kanıtladı. Cambrian-1 20+ encoder karşılaştırması çalıştırdı. Idefics2 beş eksenli tasarım uzayını formalize etti. Prismatic VLMs kontrollü bir benchmark üzerinde 27 eğitim tarifini karşılaştırdı. Tüm o gürültüden, küçük bir sonuç seti makaleler boyunca tutar: image encoder connector mimarisinden daha çok önemli, veri karışımı ikisinden de daha çok önemli ve detaylı insan caption'ları distille edilmiş sentetik veriyi yener. Bu ders o tabloları okur ki sen okumak zorunda kalmayasın.

**Tür:** Öğrenim + lab
**Diller:** Python (stdlib, ablasyon tablo parser + recipe picker)
**Ön koşullar:** Faz 12 · 05 (LLaVA baseline)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Beş eksenli VLM tasarım uzayını söyle: image encoder, connector, LLM, veri karışımı, çözünürlük programı.
- Bir MM1 / Idefics2 / Cambrian-1 ablasyon tablosunu oku ve hangi ayarın verili bir benchmark'ı hareket ettirdiğini tahmin et.
- Bir compute bütçesi ve görev karışımı verildiğinde yeni bir VLM için bir tarif (encoder, connector, veri, çözünürlük) seç.
- Aynı token sayısında detaylı insan caption'larının GPT-4V distillation'ı neden yendiğini açıkla.

## Sorun

Yüzlerce open-weight VLM var. "İyi" ile "state-of-the-art" arasındaki farkın çoğu mimari değil. Veri, çözünürlük programı ve encoder seçimi. Modelin yetersiz performans gösterdiğinde önce hangi ayarı çevireceğini bilmek seni 5 milyon GPU-saatlik hatadan kurtarır.

2023 dalgası (LLaVA-1.5, InstructBLIP, MiniGPT-4) caption-çift pretraining + LLaVA-Instruct-150k üzerinde koştu. İyi baseline. MMMU %35 civarında tepe yaptı.

2024 dalgası (MM1, Idefics2, Molmo, Cambrian-1, Prismatic VLMs) kapsamlı ablasyonlar çalıştırdı. Sonuçlar şaşırtıcı ve pratikti.

## Kavram

### Beş eksenli tasarım uzayı

Idefics2 (Laurençon et al., 2024) eksenleri adlandırdı:

1. Image encoder. CLIP ViT-L/14, SigLIP SO400m/14, DINOv2 ViT-g/14, InternViT-6B. Encoder'lar patch boyutu, çözünürlük ve pretraining objective'inde farklılaşır.
2. Connector. MLP (2-4 katman), Q-Former (32 query + cross-attn), Perceiver Resampler (64 query), C-Abstractor (convolutional + bilinear pooling).
3. Language model. Llama-3 8B / 70B, Mistral 7B, Phi-3, Gemma-2, Qwen2.5. LLM boyutu baskın param maliyetidir.
4. Eğitim verisi. Caption çiftleri (CC3M, LAION), interleaved (OBELICS, MMC4), instruction (LLaVA-Instruct, ShareGPT4V, PixMo, Cauldron).
5. Çözünürlük programı. Sabit 224/336/448, AnyRes, native dinamik. Eğitim sırasında rampalı ya da sabit.

Her üretim VLM'i her eksende bir seçim yapar. MMMU skorlarındaki varyansın çoğu 1, 4 ve 5. eksenlerle açıklanıyor — hangi connector seçtiğinle değil.

### 1. eksen: encoder > connector

MM1 Bölüm 3.2 gösterdi: CLIP ViT-L/14'ten SigLIP SO400m/14'e geçmek 3+ MMMU puanı ekledi. Connector'ı MLP'den Perceiver Resampler'a değiştirmek 1 puandan az ekledi. Idefics2 tekrarladı: SigLIP > CLIP, aynı token sayısında Q-Former ≈ MLP ≈ Perceiver.

Cambrian-1'in "Cambrian Vision Encoders Match-Up" (Tong et al., 2024) vision-centric bir benchmark (CV-Bench) üzerinde 20+ encoder çalıştırdı. Liderlik tablosunun tepesi DINOv2 ve SigLIP karışımı; CLIP grubun ortası; ImageBind ve ViT-MAE daha düşük. CV-Bench'te CLIP ViT-L'den DINOv2 ViT-g/14'e fark ~5-7 puan.

Açık VLM'ler için 2026 varsayılan encoder'ı semantik + dense feature'lar için SigLIP 2 SO400m/14, bazen dense feature'lar için DINOv2 ViT-g/14 ile birleştirilmiş (Cambrian'ın "Spatial Vision Aggregator"u bunu yapar).

### 2. eksen: connector tasarımı pat

MM1, Idefics2, Prismatic ve MM-Interleaved hepsi aynı sonuca vardı: sabit görsel-token sayısında, connector mimarisi neredeyse hiç önemli değil. Mean-pooled patch'ler üzerinde 2 katmanlı MLP, aynı token bütçesinde 32-query Q-Former'dan 1 puan içinde performans gösterir.

Önemli olan token sayısı. Daha çok görsel token = daha çok LLM compute = bir noktaya kadar daha iyi performans, sonra azalan getiriler. Görsel başına 64 token OCR için çok az. Çoğu açık VLM için 576-1024 token tatlı nokta. 2048+ yalnızca belgeler ve chart'lar için yardımcı.

Q-Former vs MLP bir maliyet sorusu, bir kalite sorusu değil: Q-Former görsel çözünürlüğünden bağımsız token'ları 32-64'te sınırlar; MLP tüm patch token'larını yayar. Yüksek-çözünürlüklü input'lar için Q-Former LLM context'i kazandırır; düşük-çözünürlüklü için fark gürültü.

### 3. eksen: LLM boyutu tavanı belirler

LLM'i 7B'den 13B'ye iki katlamak her VLM makalesinde MMMU'da güvenilir şekilde 2-4 puan ekler. 70B'de çoğu benchmark'ı doyurursun. VLM'in multimodal akıl yürütme tavanı LLM'in metin akıl yürütme tavanıdır — görsel encoder yalnızca onu besleyebilir, onun için akıl yürütemez.

Qwen2.5-VL-72B ve Claude Opus 4.7'nin MMMU-Pro ve ScreenSpot-Pro'yu ezmesinin nedeni bu: dil beyni dev. 7B bir VLM 70B bir VLM'in yerini akıllı connector tasarımıyla tutamaz.

### 4. eksen: veri — detaylı insan caption'ları distillation'ı yener

Molmo + PixMo (Deitke et al., 2024) herkesin okuması gereken 2024 sonucu. Allen AI insan annotator'larına görselleri 1-3 dakikalık dense speech-to-text geçişleriyle betimletti, 712K dense-caption'lı görsel verdi. Eğitim verisinde hiçbir yerde GPT-4V distillation'ı yok.

Molmo-72B Llama-3.2-90B-Vision'ı 11/11 benchmark'ta yendi. Fark mimari değil — caption kalitesi. Detaylı insan caption'ları görsel başına kısa web caption'larından 5-10x daha çok bilgi içerir ve GPT-4V distillation'ı halüsinasyon yaparken olgusal olarak temellidir.

ShareGPT4V (Chen et al., 2023) ve Cauldron (Idefics2) aynı playbook'u karışık insan + GPT-4V caption'ları ile takip etti. Trend net: 2026 frontier'i için caption yoğunluğu > caption miktarı > distillation kolaylığı.

### 5. eksen: çözünürlük ve programı

Idefics2'nin ablasyonları: 384 -> 448 1-2 puan ekler. Image splitting (AnyRes) ile 448 -> 980 OCR benchmark'larında 3-5 daha ekler. Düz çözünürlük eğitimi orta doğrulukta plato yapar; çözünürlük rampası (224'le başla, 448 ya da native'de bitir) daha hızlı eğitir ve daha yüksek biter.

Cambrian-1 bir çözünürlük vs token trade-off'u çalıştırdı: sabit compute'ta, daha düşük çözünürlükte daha çok token ya da daha yüksek çözünürlükte daha az token alabilirsin. OCR için daha yüksek çözünürlük kazanır; genel sahne anlama için düşük-çözünürlük-daha-çok-token kazanır.

2026 üretim tarifi: Aşama 1'i sabit 384'te eğit, OCR-ağır görevler için 1280'e kadar dinamik çözünürlükle Aşama 2.

### Prismatic kontrollü karşılaştırma

Prismatic VLMs (Karamcheti et al., 2024) tüm eksenleri kontrol eden makaledir. Aynı 13B LLM, aynı instruction verisi, aynı değerlendirme — bir kerede yalnızca bir eksen değişir. Sonuçlar:

- Görsel başına görsel-token sayısı varyansın ~%60'ını açıklar.
- Encoder seçimi ~%20'sini açıklar.
- Connector mimarisi ~%5'ini açıklar.
- Her şey (veri karışımı, scheduler, LR) kalan ~%15'i.

Bu kaba bir ayrıştırma, ama literatürde "önce neyi ablate etmeliyim" sorusuna en temiz cevap.

### 2026 için bir picker

Kanıtı verildiğinde, 2026'da yeni bir proje için varsayılan açık-VLM tarifi:

- Encoder: NaFlex ile native çözünürlükte SigLIP 2 SO400m/14, segmentation/grounding'e ihtiyacın varsa dense feature'lar için DINOv2 ViT-g/14 ile birleştirilmiş.
- Connector: patch token'lar üzerinde 2 katmanlı MLP. Token-kısıtlı değilsen Q-Former'ı atla.
- LLM: Qwen2.5 / Llama-3.1 / Gemma 2, maliyet için 7B, kalite için 70B, hedef latency'ye göre seçilmiş.
- Veri: PixMo + ShareGPT4V + Cauldron, görev-spesifik instruction verisiyle takviye.
- Çözünürlük: dinamik (uzun kenar başına min 256, max 1280 piksel).
- Program: Aşama 1 hizalama (yalnızca projector), Aşama 2 tam fine-tune, Aşama 3 görev-spesifik fine-tune.

Bu varsayılanların her biri bu dersin sonunda alıntılanan makalelerdeki ölçülen bir ablasyona izlenir.

## Kullan

`code/main.py` bir ablasyon tablo parser ve tarif picker'ı. MM1 ve Idefics2 ablasyon tablolarını (özetlenmiş) kodlar ve sorgulamana izin verir:

- "Bütçe X ve görev Y verildiğinde hangi tarif kazanır?"
- "7B Llama'da SigLIP'i CLIP ile değiştirirsem beklenen MMMU farkı nedir?"
- "%80 güven cevabı için önce hangi ekseni ablate etmeliyim?"

Çıktı beklenen benchmark farkları ve "önce ablate" önerisi ile sıralanmış tarif listesi.

## Yayınla

Bu ders `outputs/skill-vlm-recipe-picker.md` üretir. Hedef görev karışımı, compute bütçesi ve latency hedefi verildiğinde, her seçimi haklı çıkaran ablasyona alıntılarla tam bir tarif (encoder, connector, LLM, veri karışımı, çözünürlük programı) yayar. Mühendislerin yeni bir VLM projesi başladığında her seferinde Idefics2 ablasyon tablosunu yeniden icat etmelerini engeller.

## Alıştırmalar

1. MM1 Bölüm 3.2'yi oku. 50M görsel bütçeli sabit 2B LLM için hangi encoder kazanır? Cevap 13B LLM'de ters döner mi? Neden?

2. Cambrian-1, DINOv2 + SigLIP'i birleştirmenin tek başına her ikisinden de daha iyi performans gösterdiğini ama MMMU'da hiçbir sinyal eklemediğini buluyor. Hangi benchmark'ların kazanacağını ve hangilerinin düz kalacağını tahmin et.

3. Hedefin 2B LLM üzerinde mobil UI agent'ı. Encoder, connector, çözünürlük ve veri karışımı seç. Her seçimi spesifik bir ablasyon tablosuyla haklı çıkar.

4. Molmo 4B ve 72B model gönderiyor. 4B kapalı 7B VLM'lerle rekabetçi; 72B Llama-3.2-90B-Vision'ı 11/11 benchmark'ta yener. Bu sana LLM-boyut platosu hipotezi hakkında ne söyler?

5. 7B bir VLM üzerinde veri-karışım kalitesini encoder kalitesinden izole etmek için bir ablasyon tablosu tasarla. Minimum kaç eğitim çalıştırması? Dört eksen ayarını öner.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Ablasyon | "Bir ayarı çevirmek" | Tam olarak tek tasarım-uzayı ekseninde farklılaşan, geri kalanı sabit tutan çoklu eğitim çalıştırması |
| Connector | "Köprü" / "projector" | Vision encoder çıktısını LLM'in token uzayına eşleyen eğitilebilir modül (MLP, Q-Former, Perceiver) |
| Detaylı insan caption'ı | "Dense caption" | Web alt text'inden daha zengin çok cümleli insan yazımı betimleme (tipik olarak 80-300 token) |
| Distillation | "GPT-4V caption'ları" | Daha güçlü proprietary bir VLM tarafından üretilen eğitim verisi; uygun ama miras kalan halüsinasyona yatkın |
| AnyRes / dinamik res | "Yüksek-res yolu" | Tile etme ya da M-RoPE ile encoder'ın native çözünürlüğünden daha büyük görselleri besleme stratejisi |
| Çözünürlük rampası | "Müfredat" | Düşük-çözünürlükten başlayıp artan, hizalama öğrenmeyi hızlandıran eğitim programı |
| Vision-centric bench | "CV-Bench / BLINK" | Dil-ağır akıl yürütme yerine ince taneli görsel algıyı stresleyen değerlendirme |
| PixMo | "Molmo'nun verisi" | Allen AI'ın 712K dense-caption'lı görsel dataset'i; insan konuşması dense caption'lara transcribe edilmiş |

## İleri Okuma

- [McKinzie et al. — MM1 (arXiv:2403.09611)](https://arxiv.org/abs/2403.09611)
- [Laurençon et al. — Idefics2 / What matters building VLMs (arXiv:2405.02246)](https://arxiv.org/abs/2405.02246)
- [Deitke et al. — Molmo and PixMo (arXiv:2409.17146)](https://arxiv.org/abs/2409.17146)
- [Tong et al. — Cambrian-1 (arXiv:2406.16860)](https://arxiv.org/abs/2406.16860)
- [Karamcheti et al. — Prismatic VLMs (arXiv:2402.07865)](https://arxiv.org/abs/2402.07865)
