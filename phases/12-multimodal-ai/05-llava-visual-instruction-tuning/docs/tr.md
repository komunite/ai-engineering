# LLaVA ve Visual Instruction Tuning

> LLaVA (Nisan 2023) gezegendeki en çok kopyalanan multimodal mimari. BLIP-2'nin Q-Former'ını 2 katmanlı MLP ile, Flamingo'nun gated cross-attention'ını naif token birleştirme ile değiştirdi ve GPT-4'ün yalnızca metinli caption'lardan ürettiği 158k görsel-instruction turn üzerinde eğitildi. 2023 ile 2026 arasında VLM inşa eden her uygulamacı LLaVA'nın bir varyantını inşa etti. LLaVA-1.5 AnyRes ekledi. LLaVA-NeXT çözünürlüğü artırdı. LLaVA-OneVision görseli, çoklu görseli ve videoyu tek tarifte birleştirdi. Bu ders tarifi okuyor, projector'ı uyguluyor ve "daha basit kazandı"yı açıklıyor.

**Tür:** Yapım
**Diller:** Python (stdlib, projector + instruction-template builder)
**Ön koşullar:** Faz 12 · 02 (CLIP), Faz 11 (LLM Mühendisliği — instruction tuning)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- ViT patch embedding'lerini (dim 1024) LLM'in embedding dim'ine (dim 4096) eşleyen 2 katmanlı MLP projector inşa et.
- LLaVA iki aşamalı tarifinden yürü: (1) 558k caption çifti üzerinde projector hizalama, (2) 158k GPT-4 üretimi turn üzerinde visual instruction tuning.
- Image token placeholder, system prompt ve user/assistant turn'leri ile LLaVA-formatlı prompt inşa et.
- Q-Former'ın token-bütçe avantajına rağmen topluluğun Q-Former'dan MLP'ye neden geçtiğini açıkla.

## Sorun

BLIP-2'nin Q-Former'ı (Ders 12.03) bir görseli 32 token'a sıkıştırır. Temiz, verimli, benchmark'lar için iyi. Ama iki sorunu var.

Birincisi, Q-Former eğitilebilir ama loss'u nihai görev değil. Aşama 1 ITC+ITM+ITG eğitiyor. Aşama 2 LM loss eğitiyor. Query'ler LLM'in sonra decode etmesi gereken bir ara temsil öğrenir. Bottleneck'te bilgi kaybolur.

İkincisi, Q-Former 188M param alır ve LLaVA'nın 2023 ölçeğinde onu hedef LLM'inle birlikte tasarlamak zorundaydın. LLM'i değiştir, Q-Former'ı yeniden eğit. Vision encoder'ı değiştir, yeniden eğit. Her kombinasyon ayrı bir AR&GE projesiydi.

LLaVA cevabı basitliğiyle utandırıcıydı: ViT'in 576 patch token'ını al, her birini 2 katmanlı MLP'den (`1024 → 4096 → 4096`) geçir ve hepsini 576 olarak LLM'in input dizisine dök. Bottleneck yok. Tuhaf objective'lerde aşama 1 pretraining yok. Sadece MLP'yi doğrudan LM loss üzerinde eğit.

Veri nereden gelir? LLaVA'nın ikinci içgörüsü: instruction verisi üretmek için GPT-4'ü (yalnızca metin) kullan. GPT-4'e bir görsel için COCO caption ve bounding-box verisini besle, konuşmalar, betimlemeler ve karmaşık akıl yürütme soruları üretmesini iste. 158k instruction-response turn bedava. İnsan annotation'ı yok.

Sonuç: 8 A100'de bir gün koşan, MMMU'da Flamingo'yu yenen ve topluluğun genişletebileceği bir açık checkpoint gönderen bir VLM. 2023 sonlarına kadar 50+ fork doğurdu.

## Kavram

### Mimari

13B'de LLaVA-1.5:
- Vision encoder: CLIP ViT-L/14 @ 336 (aşama 1'de donmuş, opsiyonel aşama 2'de açılır).
- Projector: GELU activation ile 2 katmanlı MLP, `1024 → 4096 → 4096`.
- LLM: Vicuna-13B (sonra Llama-3.1-8B).

Bir görsel + metin prompt'ta forward pass:

```
görsel -> ViT -> dim 1024'lü 576 patch
patch'ler -> MLP -> dim 4096'lı 576 token
prompt: system + "<image>" placeholder + user sorusu
<image> token'ını 576 projekte edilmiş token ile değiştir
tam diziyi LLM'e besle
yanıtı decode et
```

Görsel LLM context'inin 576 token'ını işgal eder. 2048 context'te bu metin için 1472 token bırakır. 32k context'te bir yuvarlama hatası.

### Aşama 1: projector hizalama

ViT'i dondur. LLM'i dondur. Yalnızca 2 katmanlı MLP'yi eğit. Dataset: 558k görsel-caption çifti (LAION-CC-SBU). Loss: caption üzerinde language modeling, projekte edilmiş görsel token'larına koşullu.

Batch 128'de tek epoch'ta bu birkaç saatte biter. Projector ViT-uzayı LLM-uzayına eşlemeyi öğrenir. Görev özel gözetim yok.

### Aşama 2: visual instruction tuning

Projector'ı (hâlâ eğitilebilir) açma. LLM'i aç (genellikle tam, bazen LoRA). 158k görsel-instruction turn üzerinde eğit.

Instruction verisi hilenin ta kendisi. Liu et al. şu şekilde üretti:
1. Bir COCO görseli al.
2. Metin betimlemesini çıkar (5 insan caption'ı + bounding-box listesi).
3. Üç prompt şablonu ile GPT-4'e gönder:
   - Conversation: "Bu görsel hakkında user ve assistant arasında bir ileri-geri diyalog üret."
   - Detailed description: "Görselin zengin, detaylı bir betimlemesini ver."
   - Complex reasoning: "Görsel hakkında akıl yürütme gerektiren bir soru sor, sonra onu cevapla."
4. GPT-4 çıktısını (instruction, response) çiftlerine ayrıştır.

Hiçbiri doğrudan görsele dokunmaz — yalnızca metin betimlemesine. GPT-4 makul görsel içeriği halüsinasyon ediyor. Biraz gürültü, ama çalıştı: 158k turn diyaloğu açmaya yetti.

### Topluluk bunu neden kopyaladı

- Tune edilecek aşama-1-spesifik loss yok. Baştan sona LM loss.
- Projector günlerce değil saatlerce eğitir.
- LLM yalnızca projector'ı yeniden eğiterek değiştirilebilir (LLaVA-Llama2, LLaVA-Mistral, LLaVA-Llama3).
- Görsel-instruction veri pipeline'ı GPT-4 kullanır ve yeni bir domain için ucuza yeniden üretilir.

### LLaVA-1.5 ve LLaVA-NeXT

LLaVA-1.5 (Ekim 2023) ekledi:
- Instruction tuning'e karıştırılan akademik-görev verisi (VQA, OKVQA, RefCOCO).
- Daha iyi system prompt.
- 2048 → 32k context.

LLaVA-NeXT (Ocak 2024) ekledi:
- AnyRes: yüksek çözünürlüklü görselleri 2x2 ya da 1x3 grid'inde 336x336 crop'lara böl, artı bir global düşük-çözünürlüklü thumbnail. Her crop 576 token olur; görsel başına toplam yaklaşık 2880 görsel token. OCR ve chart görevleri sıçradı.
- ShareGPT4V (yüksek kaliteli GPT-4V caption'ları) ile daha iyi instruction veri karışımı.
- Daha güçlü base LLM'ler (Mistral-7B, Yi-34B).

### LLaVA-OneVision

Ders 12.08 OneVision'ı derinlemesine kapsar. Kısa versiyon: aynı projector, ama paylaşılan görsel-token bütçesi ile tek görsel, çoklu görsel ve videoyu tek modelde kapsayan bir müfredatla eğitildi.

### Q-Former'a göre karşılaştırma

| | Q-Former (BLIP-2) | MLP (LLaVA) |
|---|---|---|
| Görsel başına görsel token | 32 | 576 (base) ya da 2880 (AnyRes) |
| Eğitilebilir param | 188M + LM | 40M + LM |
| Aşama 1 loss | ITC+ITM+ITG | Yalnızca LM |
| LLM drop-in | Yeniden eğitim gerekir | Minimal yeniden eğitimle değiştir |
| Çoklu görsel | Sıkıntılı | Doğal (concat) |
| Video | Sıkıntılı | Doğal (frame başına concat) |
| Token bütçesi | Küçük | Büyük |

MLP basitlik ve token esnekliğinde kazanır. Q-Former token bütçesinde kazanır. 2023 sonlarına kadar token bütçesi artık bağlayıcı kısıt değildi (LLM context'leri 32k-128k+'ya büyüdü) ve basitlik baskın hale geldi.

### Prompt formatı

```
A chat between a curious human and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the human's questions. USER: <image> Describe this image in detail. ASSISTANT: The image shows ...
```

`<image>` bir placeholder token. Tokenization'dan önce 576 görsel token (ya da AnyRes ile 2880) ile değiştirilir. Tokenizer eğitildiğinden biraz daha uzun bir dizi görür, ama LLM yeni input'u halleder çünkü aşama 1 ona onu öğretti.

### Parametre ekonomisi

LLaVA-1.5-7B kırılımı:
- CLIP ViT-L/14 @ 336: 303M (aşama 1 donmuş, sıklıkla aşama 2 açılır).
- Projector (2x lineer): ~22M eğitilebilir.
- Llama-7B: 7B.
- Toplam: 7.3B param. Aşama 2 sırasında eğitilebilir: tam 7B + 22M projector.

Aşama 2 için eğitim maliyeti: 8xA100'de ~20 saat. Anahtar sayı bu — bir gün, bir node, yeniden üretilebilir. LLaVA'nın yayılma sebebi bu.

## Kullan

`code/main.py` şunları uygular:

1. 2 katmanlı MLP projector (oyuncak ölçek için dim 16 → 32 → 32) saf Python'da.
2. Prompt inşa pipeline'ı: system prompt + N projekte edilmiş token ile değiştirilen `<image>` + user turn'ü + assistant generation placeholder'ı.
3. 576-token görsel block'un LLM context'inde nasıl göründüğünü görselleştiren bir görselleştirici (tüketilen 2k / 32k / 128k context yüzdesi).

## Yayınla

Bu ders `outputs/skill-llava-vibes-eval.md` üretir. Bir LLaVA-family checkpoint verildiğinde, 10-prompt vibes-eval suite (3 captioning, 3 VQA, 2 reasoning, 2 refusal) çalıştırır ve insan-okunabilir skor kartı raporlar. Benchmark değil; projector ve LLM'in iyi bağlandığını doğrulayan bir smoke test.

## Alıştırmalar

1. `1024 → 4096 → 4096`'da 2 katmanlı MLP projector için eğitilebilir-parametre sayısını hesapla. GELU ve bias ile LLaVA-13B'nin ne kadarını temsil eder?

2. "Refusal" durumu için bir LLaVA prompt'u inşa et — görsel özel bir bireyi içeriyor. Beklenen assistant yanıtını yaz. LLaVA bunu neden zero-shot reddetmeli ve reddi pekiştirmek için hangi eğitim verisi gerekli olur?

3. LLaVA-NeXT blogunun AnyRes bölümünü oku. AnyRes'te 1344x672 bir görsel için görsel token sayısını hesapla. 336x336'da base 576 token ile karşılaştır.

4. LLaVA aşama-1 projector caption'lar üzerinde LM loss ile eğitilir. Aşama 1'i atlayıp doğrudan aşama 2'ye (visual instruction tuning) gidersen ne olur? Cevap için Prismatic VLMs ablasyonunu (arXiv:2402.07865) kaynak göster.

5. LLaVA-Instruct-150k GPT-4'ü COCO caption'ları ile instruction üretmek için kullanır. Yeni bir domain (tıbbi X-ışınları, uydu görüntüleri) için domain instruction'ları üretmek için dört adımlı veri pipeline'ını betimle. Her adımda ne ters gidebilir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Projector | "MLP köprü" | ViT dim'ini LLM dim'ine eşleyen GELU'lu 2 katmanlı MLP |
| Image token | "<image> placeholder" | Çıkarımdan önce N projekte edilmiş görsel token ile değiştirilen prompt marker'ı |
| Visual instruction tuning | "LLaVA aşama 2" | GPT-4 üretimi (görsel, instruction, response) üçlüleri üzerinde eğitim |
| Stage 1 alignment | "Projector pretraining" | ViT ve LLM'i dondur, caption'lar üzerinde LM loss ile projector'ı eğit |
| AnyRes | "Çoklu-crop tiling" | Yüksek çözünürlüklü görseli tile grid'ine böl ve her tile'ın görsel token'larını birleştir |
| LLaVA-Instruct | "GPT-4 üretimi" | COCO caption'ları + GPT-4'ten sentezlenmiş 158k instruction-response çifti |
| Vision encoder freeze | "Backbone kilitli" | CLIP ağırlıkları aşama 1'de, bazen aşama 2'de de güncellenmez |
| ShareGPT4V | "Daha iyi caption'lar" | GPT-4V tarafından üretilen 1M dense caption, daha yüksek kaliteli hizalama için kullanılır |
| VQA | "Visual question answering" | Bir görsel hakkında serbest-form soruyu cevaplama görevi |
| Prismatic VLMs | "Tasarım-uzayı makalesi" | Projector ve veri seçimlerini sistematik test eden Karamcheti 2024 ablasyonu |

## İleri Okuma

- [Liu et al. — Visual Instruction Tuning (arXiv:2304.08485)](https://arxiv.org/abs/2304.08485) — LLaVA makalesi.
- [Liu et al. — Improved Baselines with Visual Instruction Tuning (arXiv:2310.03744)](https://arxiv.org/abs/2310.03744) — LLaVA-1.5.
- [Chen et al. — ShareGPT4V (arXiv:2311.12793)](https://arxiv.org/abs/2311.12793) — dense caption dataset'i.
- [Karamcheti et al. — Prismatic VLMs (arXiv:2402.07865)](https://arxiv.org/abs/2402.07865) — tasarım-uzayı ablasyonları.
- [Li et al. — LLaVA-OneVision (arXiv:2408.03326)](https://arxiv.org/abs/2408.03326) — birleştirilmiş tek görsel, çoklu görsel, video.
