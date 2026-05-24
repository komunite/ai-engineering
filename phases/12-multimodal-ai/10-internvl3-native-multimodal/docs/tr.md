# InternVL3: Native Multimodal Pretraining

> InternVL3'ten önce her açık VLM aynı üç adımlı tarifi takip etti: trilyonlarca metin token'ında eğitilmiş bir metin LLM al, üzerine bir vision encoder cıvatala, sonra dikişleri fine-tune et. Bu çalışıyor ama hizalama borcu var — metin LLM tüm pretraining bütçesini saf metne harcadı ve görsel token'ları natively anlamıyor. Vision'ı post-hoc eklediğinde, LLM metni unutmadan görsel input'u metin akıl yürütmesine nasıl bağlayacağını yeniden öğrenmek zorunda. InternVL3 (Zhu et al., Nisan 2025) post-hoc yaklaşımı reddediyor: tek pretraining çalıştırması, metin ve multimodal birinci adımdan interleaved. Sonuç 78B param'da MMMU-Pro'da Gemini 2.5 Pro'yu eşliyor, açık. Bu ders native pretraining argümanını ve yaptığında neyin değiştiğini okur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, eğitim corpus mixer)
**Ön koşullar:** Faz 12 · 05, Faz 12 · 07 (tarifler)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Post-hoc VLM eğitiminin neden hizalama borcu biriktirdiğini, ölçülebilir üç semptomu (catastrophic forgetting, cevap kayması, görsel-metin tutarsızlığı) kaynak göstererek açıkla.
- InternVL3'ün native pretraining corpus karışımını ve metin : interleaved : caption oranının neden önemli olduğunu betimle.
- V2PE'yi (variable visual position encoding) Qwen2-VL'in M-RoPE'si ile karşılaştır.
- Visual Resolution Router (ViR) ve Decoupled Vision-Language (DvD) deployment optimizasyonlarını söyle.

## Sorun

Post-hoc VLM eğitimi varsayılan. LLaVA, BLIP-2, Qwen-VL, Idefics — hepsi zaten pretrained bir LLM (Llama, Vicuna, Qwen, Mistral) alıp vision ekliyor. Eğitim aşamaları tipik olarak şöyle:

1. Donmuş LLM + donmuş vision encoder + eğitilebilir projector, embedding'leri hizalamak için caption çiftleri üzerinde eğitildi.
2. LLM'i aç, instruction verisi (LLaVA-Instruct, ShareGPT4V) üzerinde eğit.
3. Opsiyonel görev-spesifik fine-tune.

Hizalama borcunun üç semptomu görünüyor:

- Catastrophic forgetting. Post-hoc VLM yalnızca metin becerilerini unutuyor. GSM8K skorları 5-10 puan düşüyor. Hellaswag skorları düşüyor. Saf-metin agent'ları geriliyor.
- Cevap kayması. Aynı görsel sorunun küçük ifade farklılıkları farklı cevap alıyor. Vision encoder LLM'e LLM'in kendi token'larından daha zayıf bağlarla bağlanıyor.
- Görsel-metin tutarsızlığı. VLM bir görseli doğru betimleyebilir ve sonra kendi betimlemesiyle çelişen bir soruyu cevaplayabilir. Görsel token'lar LLM'in iç tutarlılık kontrollerine metnin yaptığı gibi katılmıyor.

Bu semptomlar iyi belgelenmiş. MM1.5 Bölüm 4 onları nicelendiriyor. LLaVA-OneVision'ın ablasyonları onlara işaret ediyor. Native pretraining cevap.

## Kavram

### Native multimodal pretraining

InternVL3 birinci adımdan native multimodal olan bir corpus üzerinde sıfırdan eğitiyor. Karışım:

- %40 yalnızca metin verisi (FineWeb, Proof-Pile-2, vb.)
- %35 interleaved image-text verisi (OBELICS, MMC4 tarzı)
- %20 eşli image-caption verisi
- %5 video-text verisi

Görsel token'lar, metin token'lar ve cross-modal etkileşimlerin hepsi ilk gradient adımından itibaren aynı loss'a katılıyor. Hizalama pretraining yok, projector dondurma aşaması yok, kurtulunacak catastrophic forgetting yok.

Eğitim base model için tek aşama. Instruction tuning takip eder, ama base model zaten görsel token'ları birinci sınıf vatandaş olarak anlıyor.

### V2PE (variable visual position encoding)

Qwen2-VL sabit eksen tahsisi ile M-RoPE kullanıyor. InternVL3 V2PE'yi tanıtıyor: pozisyon kodlaması modalite türüne (metin, görsel, video) göre öğrenilebilir scaling ile değişiyor. Pratikte:

- Metin token'ları 1D pozisyon alır (metin indeksi).
- Görsel patch'leri 2D pozisyon alır (satır, sütun).
- Video frame'leri 3D pozisyon alır (zaman, satır, sütun).

Üçü aynı RoPE frekans tabanını paylaşır, ama bant başına hidden-dim tahsisi sabit bölme yerine öğrenilen bir parametre. Pretraining sırasında temporal vs spatial frekans çözünürlüğünü trade off etme özgürlüğü.

V2PE'nin ablasyon iddiası: aynı compute'ta M-RoPE üzerinde video benchmark'larında 1-2 puan. Devrim değil, ama daha temiz.

### Visual Resolution Router (ViR)

Deployment optimizasyonu. Her görselin tam çözünürlüklü kodlamaya ihtiyacı yok. Düşük detayda tek nesneli bir fotoğraf 1280px native'de kodlandığında token harcıyor. ViR, kodlamadan önce soruyu cevaplamak için gereken minimum çözünürlüğü tahmin eden küçük bir sınıflandırıcı.

Yönlendirmenin üç katmanı var: düşük-res (256 token), orta (576), yüksek (2048+). Üretim trafiğinde sorguların %60'ı için düşük ya da orta yeterli. Net etki: eşit kalitede 2-3x throughput.

### Decoupled Vision-Language deployment (DvD)

Büyük bir VLM serve ederken, vision encoder görsel başına bir kez çalışır ama LLM her çıkış token'ı için autoregressive çalışır. İki bileşenin farklı bottleneck'leri var (vision = conv + attention için GPU bellek bandwidth'i; LLM = KV cache). DvD onları streaming ile ayrı GPU'lara böler.

8B + 400M encoder model için DvD co-located'a kıyasla node başına throughput'u kabaca iki katlar.

### Tek aşama vs çoklu aşama kalitesi

InternVL3'ün birincil benchmark iddiası: 78B param'da, Gemini 2.5 Pro'nun MMMU-Pro'sunu eşle. 38B'de, GPT-4o'yu eşle. 8B'de, açık-8B liderlik tablosunu yönet. Hepsi tek-aşamalı pretrain + instruction-tune tarifinde.

Hizalama-borç hipotezi ölçülebilir: InternVL3-8B vision-benchmark kazanım birimi başına Qwen2.5-VL-7B'den daha az metin-benchmark puanı (MMLU, GSM8K) kaybeder. Model daha çok genelci çünkü eğitim iki parça değil bir parçaydı.

### InternVL3.5 ve InternVL-U

InternVL3.5 (Ağustos 2025) tarifi ölçekler. Aynı native-pretrain yaklaşımı, daha çok veri, daha çok param. MMMU iyileştirmeleri artımlı.

InternVL-U (2026) birleştirilmiş üretim ekler — aynı backbone üstüne MMDiT head'leri üzerinden görsel çıktı. "U" "Understanding + generation"u temsil ediyor, Transfusion tarzı birleştirilmiş modelleri kovalıyor (Ders 12.13). Aynı native-pretrain backbone hem understanding hem generation head'lerini destekler.

### Native pretraining'in trade-off'ları

Native pretraining bedava değil:

- Compute. Yeni bir VLM'i sıfırdan eğitmek metin LLM eğitmekle aynı maliyettir — milyonlarca GPU-saati. Post-hoc adaptation mevcut LLM ağırlıklarını yeniden kullanır, maliyetin çoğunu kurtarır.
- Veri. Ölçekte interleaved image-text corpus'ları nadir. OBELICS 141M belge; MMC4 571M. Yalnız metin 15T token'da gönderilir. Multimodal pretraining veri kıtlığı sert kısıt.
- Base-LLM yeniden kullanım. Native pretraining sonra yeni bir LLM drop in etme seçeneğini bırakıyor. Post-hoc Llama-3.1'i Llama-4 ile yalnızca adapter'ı yeniden eğiterek değiştirmene izin verir.

InternVL3'ün yaptığı bahis: hizalama borcu yeniden kullanım kaybından daha kötü. Benchmark'lar iddiayı destekliyor. Üretme maliyeti gelecek lab'leri ucuza tekrar etmekten alıkoyuyor. Post-hoc VLM'ler var olmaya devam edecek çünkü çoğu proje için daha ucuz kalıyorlar.

## Kullan

`code/main.py` bir eğitim-corpus mixer ve ViR router simülatörü. Şunları yapar:

- Bir hedef corpus karışımı (%text, %interleaved, %caption, %video) alır ve modalite başına beklenen adımları hesaplar.
- Bir sorgu batch'i üzerinde ViR yönlendirmesini simüle eder (dağılım: %50 düşük-detay, %30 orta, %20 yüksek-detay) ve ortalama token sayısını raporlar.
- Encoder vs LLM FLOPs verildiğinde DvD throughput tahminlerini raporlar.
- Post-hoc vs native pretraining'i param, compute, veri ve beklenen hizalama-borç semptomlarında yan yana yazdırır.

## Yayınla

Bu ders `outputs/skill-native-vs-posthoc-auditor.md` üretir. Önerilen bir VLM eğitim planı verildiğinde, native mi post-hoc mu gideceğini denetler, hizalama-borç riskini işaretler ve corpus karışımı önerir. Yeni bir açık-VLM projesi boyutlandırırken ve eğitim stratejisi seçmen gerektiğinde kullan.

## Alıştırmalar

1. InternVL3-8B (native pretrain) ile LLaVA-OneVision-7B (post-hoc) arasındaki compute farkını tahmin et. GPU-saat oranı yaklaşık? Farkı ne açıklıyor?

2. InternVL3 %40 metin / %35 interleaved / %20 caption / %5 video raporluyor. Hedef görevin video-ağırsa, yeni bir oran öner ve base modelin neden hâlâ önemli metin ve caption verisine ihtiyacı olduğunu savun.

3. Unutma üzerine MM1.5 Bölüm 4'ü oku. Post-hoc eğitimin en büyük gerilemeyi gösterdiği tam benchmark'ı söyle. Gerileme ne kadar maliyetli oldu?

4. ViR trafiğin %60'ını düşük-çözünürlüklü kodlamaya yönlendiriyor. Hangi tür sorguları yanlış yönlendiriyor (yüksek-res gerekliyken düşük-res'e gönderiyor)? Üç router-başarısızlık modu öner.

5. DvD vision ve LLM'i ayrı GPU'lara böler. Hangi trafik kalıbında DvD throughput'a yardım etmek yerine zarar verir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Native multimodal pretraining | "Birlikte sıfırdan" | Metin + görsel + video token'ları sonradan cıvatalanmak yerine 1. adımdan loss'a katılır |
| Hizalama borcu | "Post-hoc cezası" | Vision'ı donmuş bir LLM'e cıvatalamaktan gelen metin becerilerinde ve cevap tutarlılığında ölçülebilir gerileme |
| V2PE | "Variable visual pos encoding" | Modalite başına öğrenilebilir pozisyon kodlaması tahsisi; InternVL3'ün M-RoPE halefi |
| ViR | "Resolution router" | Kodlamadan önce sorgu başına gereken minimum çözünürlüğü seçen küçük sınıflandırıcı, çıkarım token'ı tasarrufu sağlar |
| DvD | "Decoupled deployment" | Bir GPU'da vision encoder, başka birinde LLM, stream handoff ile; büyük VLM'ler için throughput'u iki katlar |
| InternVL-U | "Unified understanding + generation" | Native-pretrain backbone'una image-generation head'leri ekleyen 2026 takibi |
| Interleaved corpus | "OBELICS / MMC4" | Doğal okuma sırasında metin ve görsellerle belgeler; native pretraining için ham malzeme |

## İleri Okuma

- [Chen et al. — InternVL 1 (arXiv:2312.14238)](https://arxiv.org/abs/2312.14238)
- [Zhu et al. — InternVL3 (arXiv:2504.10479)](https://arxiv.org/abs/2504.10479)
- [InternVL3.5 (arXiv:2508.18265)](https://arxiv.org/abs/2508.18265)
- [InternVL-U (arXiv:2603.09877)](https://arxiv.org/abs/2603.09877)
- [Zhang et al. — MM1.5 (arXiv:2409.20566)](https://arxiv.org/abs/2409.20566)
