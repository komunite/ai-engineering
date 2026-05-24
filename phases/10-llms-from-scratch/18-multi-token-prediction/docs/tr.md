# Multi-Token Prediction (MTP)

> GPT-2'den Llama 3'e her autoregressive LLM pozisyon başına bir loss üzerinde eğitilir: sonraki token'ı tahmin et. DeepSeek-V3 pozisyon başına ikinci bir loss ekledi: ondan sonraki token'ı tahmin et. 14B ekstra parametre (671B model üzerinde) gradient akışı yoluyla ana modele geri damıtıldı ve eğitilmiş MTP head'leri inference'ta %80+ acceptance ile speculative-decoding drafter'ları olarak yeniden amaçlandırıldı. 1.8× generation throughput ücretsiz geldi. Bu ders DeepSeek teknik raporundan sequential MTP modülünü inşa eder, loss'u ve paylaşılan-head parametre düzenini hesaplar ve Gloeckle et al.'in orijinal parallel MTP'si onu kırarken MTP'nin neden causal zinciri koruduğunu açıklar.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 10 · 04 (mini GPT pretraining), Faz 10 · 15 (speculative decoding)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- MTP eğitim hedefini ifade et ve tahmin derinlikleri boyunca ortak loss'u türet.
- Gloeckle et al.'in parallel MTP head'leri (2024) ile DeepSeek-V3'ün sequential MTP modülleri arasındaki farkı ve sequential tasarımın causal zinciri neden koruduğunu açıkla.
- Pretraining koşusuna MTP modülleri eklemenin parametre ve memory overhead'ini hesapla.
- Tek bir MTP modülünü sıfırdan implement et: paylaşılan embedding, derinlik başına transformer bloğu, projeksiyon ve paylaşılan output head.

## Sorun

Next-token prediction standart LLM eğitim hedefidir. Her hidden state tam olarak bir şeyi tahmin etmek için süpervize edilir: hemen sonraki token. Bu şaşırtıcı derecede zayıf bir sinyaldir. Bir sequence'deki bilginin çoğu bir token'ın ötesine uzanır — yapı, tutarlılık, factuality, aritmetik akış. Model bunları trilyonlarca token üzerinde birçok bir-token sinyalini biriktirerek öğrenmek zorundadır.

MTP sorar: ya her hidden state birden fazla gelecek token'ı aynı anda tahmin etmek için süpervize edilseydi? Gloeckle et al. (Meta, 2024) bunun yardım ettiğini gösterdi. Onların implementasyonu backbone üzerine birkaç bağımsız output head yerleştirdi, her biri farklı bir offset tahmin ediyordu. Paralel, basit, ama head'ler aynı hidden state'i hiyerarşik refinement olmadan gördü — ve tahminler causal şekilde zincirlenmedi, dolayısıyla speculative decoding için kullanılamadılar.

DeepSeek-V3 (Aralık 2024) MTP'yi her tahmin derinliğinde causal zinciri koruyan sequential modüller olarak yeniden tasarladı. Model `t+1`'i `h_i^(0)`'dan tahmin eder, sonra `h_i^(0)`'ı `E(t+1)` embedding'i ile birleştiren yeni bir hidden state `h_i^(1)`'den `t+2`'yi tahmin eder vb. Her derinlik kendi küçük transformer bloğudur. Paylaşılan embedding ve paylaşılan output head parametre overhead'ini mütevazı tutar. DeepSeek-V3 ölçeğinde, 671B ana-model ağırlıkları üzerine MTP modülleri boyunca 14B ekstra parametre. O %2 overhead daha yoğun eğitim sinyalleri VE inference'ta hazır bir speculative-decoding draft satın aldı.

Bu ders tek bir MTP modülü ve D-derinlik loss'unu sıfırdan inşa eder. Matematik temiz. Implementasyon 150 satır.

## Kavram

### Sequential MTP Reçetesi

DeepSeek-V3 ana modelin üstüne `D` MTP modülü ekler. Her modül `k` (`k = 1..D` için) derinlik `k`'da token tahmin eder — yani pozisyon `i`'ye kadar bir prefix verildiğinde `t_{i+k}`.

Modül `k` şunlardan oluşur:

- Kendi attention ve MLP'siyle bir transformer bloğu `T_k`.
- Önceki-derinlik hidden state'ini sonraki-derinlik ground-truth token'ının embedding'i ile birleştiren bir projeksiyon matrisi `M_k`.
- Paylaşılan embedding `E` (ana modelle aynı).
- Paylaşılan output head `Out` (ana modelle aynı).

Eğitimde, pozisyon `i`'ye kadar bir prefix için, derinlik başına hidden state:

```
h_i^(0) = pozisyon i'de ana model backbone
h_i^(k) = T_k( M_k * concat(RMSNorm(h_i^(k-1)), RMSNorm(E(t_{i+k}))) )   k >= 1 için
```

Derinlik başına tahmin:

```
logits_{i+k} = Out(h_i^(k-1))   k = 1..D için
```

Derinlik başına loss ground-truth `t_{i+k}`'ya karşı cross-entropy'dir:

```
L_k = CE(logits_{i+k}, t_{i+k})
```

Derinlikler boyunca ortak loss:

```
L_MTP = (lambda / D) * sum_{k=1..D} L_k
```

`lambda` küçük bir ağırlık faktörü — DeepSeek-V3 eğitimin ilk %10'unda 0.3 ve sonra 0.1 kullanır. Toplam eğitim loss'u `L_main + L_MTP`.

### Neden Sequential, Parallel Değil

Gloeckle'in orijinal parallel MTP'sinin D output head'i vardı, her biri doğrudan `h_i^(0)`'a uygulanıyordu. Her head aynı backbone hidden state'inden `t_{i+k}`'yı tahmin eder. Bu iyi eğitilir, ama tahminler birbirine koşullu değil. `head_2`'ye yardım etmek için `head_1`'in output'unu kullanamazsın — head'ler paralel ateşler.

DeepSeek-V3'ün sequential tasarımı `h_i^(k)`'yı `h_i^(k-1)` artı gerçek next-token embedding `E(t_{i+k})`'dan inşa eder. Bu causal zinciri korur: `t_{i+k+1}`'yi tahmin etmek için, derinlik `k+1`'deki modül `t_{i+k}`'da ne olduğunu görür. Bu yapısal olarak bir autoregressive decoder'ın kendi output'unu nasıl tükettiğiyle özdeştir — MTP modüllerini speculative-decoding drafter'ları olarak doğrudan kullanılabilir yapar.

İnferans'ta: `h_i^(k-1)` ve drafted `t_{i+k}`'yı modül `k+1`'e besle, `t_{i+k+1}` için bir tahmin al. Tekrarla. Bu tam olarak EAGLE-tarzı bir draft'tır, eğitilmiş MTP modülünü draft ağı olarak kullanır. DeepSeek-V3 ilk MTP modülünde %80+ acceptance ve ~1.8× hızlanma raporlar.

### Parametre Muhasebesi

Hidden `h` ve vocabulary `V` ile bir model için:

- Ana model: milyarlarca parametre, artı `V * h` boyutunda bir output head.
- Paylaşılan output head: ana modelin head'ini yeniden kullan. Ekstra param yok.
- Paylaşılan embedding: ana modelin embedding'ini yeniden kullan. Ekstra param yok.
- MTP modülü başına:
  - Projeksiyon `M_k`: `(2h) * h = 2h^2`.
  - Transformer bloğu `T_k`: attention (MHA için `4h^2`) artı MLP (tipik 8/3 oranıyla SwiGLU için `8h^2`). Blok başına yaklaşık `12h^2`.

Modül başına toplam ekstra: `~14h^2`. DeepSeek-V3'ün `h = 7168`, D = 1 modül'ü için: kağıt üzerinde `~14 * 7168^2 = ~720M` parametre. DeepSeek-V3 14B raporlar — fark çoğunlukla expert katmanlarının MTP modülünde de MoE olmasıdır.

### Speculative-Decoding Kazancı

Pretraining sırasında, MTP modülleri eğitimi yaklaşık %10 yavaşlatır (daha fazla forward compute, ekstra loss). Kazanç iki katlıdır:

1. Daha yoğun eğitim sinyali. Her hidden state D+1 supervision hedefi görür. MMLU, GSM8K, MATH, HumanEval üzerinde ölçülen etki: DeepSeek-V3'ün ablation'larında tutarlı birkaç-yüzde-puanlık iyileştirmeler.

2. İnferans'ta ücretsiz speculative decoding draft'ı. MTP modülü sonraki birkaç token'ı tahmin etmek için zaten eğitilmiştir. Draft ağı olarak yeniden amaçlandığında, %80+ acceptance rate sağlar. O seviyede, N=3 veya N=5 spec decoding 1.8× throughput verir. %10 eğitim-zamanı maliyeti çıkarımı ilk çalıştırdığında geri öder.

### EAGLE ile İlişki

EAGLE pretraining'den SONRA küçük bir draft modeli AYRI eğitir. MTP draft'ı pretraining'e pişirir. İki yaklaşım benzer acceptance rate'lere yakınsıyor ama farklı pipeline'lar üzerinden:

| Boyut | EAGLE-3 | MTP (DeepSeek-V3) |
|-----------|---------|------------------|
| Ne zaman eğitilir | Pretraining sonrası | Pretraining sırasında |
| Mevcut ağırlıklarla backward-uyumlu | Evet | Hayır (yeniden eğitmek gerekir) |
| Draft param | 1-2 transformer katmanı | 1 transformer bloğu + projeksiyon |
| Acceptance rate | 0.88-0.92 | derinlik 1'de 0.80+ |
| Hızlanmanın ötesinde fayda | Sadece speculative decoding | Daha yoğun eğitim sinyali + hızlanma |

## İnşa Et

`code/main.py` tek bir MTP modülünü uçtan uca inşa eder: paylaşılan embedding, projeksiyon, transformer bloğu, paylaşılan output head. Sonra kısa bir sentetik sequence üzerinde derinlik başına cross-entropy loss'u hesaplar ve bileşen başına parametre sayısını yazdırır. 32 token'lık bir oyuncak vocabulary sayıları okunabilir tutar.

### Adım 1: Paylaşılan Embedding Tablosu

Tek bir `vocab_size x hidden` tablo ana model VE her derinlikteki her MTP modülü tarafından kullanılır. İkinci bir kopya değil — kelimenin tam anlamıyla aynı tensor.

### Adım 2: Derinlik Başına Birleştirme

```python
def combine(prev_hidden, next_token_embed, M_k):
    # feature dim boyunca concat, sonra hidden'a projekte et
    concat = rms_norm(prev_hidden) + rms_norm(next_token_embed)  # vektör toplama stand-in
    projected = matvec(M_k, concat)
    return projected
```

Gerçek DeepSeek-V3 iki RMSNorm'lanmış vektörü `[2h]`'ye concat eder ve bir `h x 2h` matris ile projekte eder. Oyuncak stdlib kısalığı için vektör toplama kullanır.

### Adım 3: Derinlik k'daki Transformer Bloğu

Self-attention artı MLP. Oyuncakta, tek katmanlı bir linear attention bloğu ve bir SwiGLU MLP yapıyı numpy olmadan görünür tutar.

### Adım 4: Paylaşılan Output Head

Ana modelin output projeksiyonunu yeniden kullan. Vocabulary üzerinde logit'ler.

### Adım 5: Derinlik Başına Loss

Offset `k`'da ground-truth token'a karşı softmax(logits)'in cross-entropy'si. `lambda / D` ölçekleme faktörü ile derinlikler boyunca topla.

### Adım 6: Parametre Muhasebesi

Toplam parametre sayısını, paylaşılan (embedding, head) sayısını ve modül başına ekstra sayıyı yazdır. MTP ekstrasının ana-model boyutuna oranını göster.

## Kullan

MTP DeepSeek-V3 (Aralık 2024) ve DeepSeek-R1 serisine entegre edilmiştir. İnferans'ta:

- DeepSeek'in kendi serving stack'i MTP modüllerini speculative decoder olarak doğrudan tüketir.
- vLLM ve SGLang Nisan 2026 itibarıyla DeepSeek-V3 MTP için entegrasyon yollarına sahiptir.
- AMD'nin ROCm SGLang tutorial'ı V3 checkpoint'inde 1.8× hızlanma ölçülen spesifik bir MTP speculative-decoding config gösterir.

Yeni bir pretraining koşusunda MTP'yi ne zaman kullanmalı:

- Tam pretraining pipeline'ını kontrol ediyorsun ve daha yoğun eğitim sinyali biriktirmek istiyorsun.
- Modeli ölçekte servis edeceğini biliyorsun ve ücretsiz speculative decoding istiyorsun.
- Hidden size'ın en az 4096. 1B-ölçeğinde overhead kazançtan daha fazla zarar verir.

Ne zaman değil:

- Mevcut bir pretrained dense modeli fine-tuning. MTP modülü eğitilmemiş.
- Karşılaştırmak için temiz bir baseline istediğin araştırma modelleri. MTP mimariyi değiştirir.

## Yayınla

Bu ders `outputs/skill-mtp-planner.md` üretir. Bir pretraining koşu spesifikasyonu (model boyutu, veri, compute) verildiğinde, MTP entegrasyonu için bir plan döner: derinlik sayısı D, `lambda` schedule, memory overhead ve inference-zamanı speculative-decoding wiring.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Sentetik sinyal güçlendikçe derinlik başına loss'un monoton olarak azaldığını göster. Sentetiği sabit bir desen kullanacak şekilde değiştir ve hem derinlik-1 hem derinlik-2 loss'larının yakınsadığını doğrula.

2. D=1 MTP modülü ile dense 70B model (hidden 8192, 80 katman) için parametre overhead'ini hesapla. DeepSeek-V3 raporlanan 14B overhead'e karşılaştır. DeepSeek'in sayısının neden daha yüksek olduğunu açıkla: MTP transformer bloğu aynı MoE yapısını miras alır, modül başına parametre sayısını şişirir.

3. Oyuncakta D=2 implement et: h^(1)'i alan ve `t_{i+2}`'yi tahmin eden ikinci bir MTP modülü ekle. Ortak loss'un ve parametre muhasebesinin DeepSeek makalesinin 19-21 denklemlerine uyduğunu doğrula.

4. Oyuncağı parallel MTP'ye (Gloeckle-tarzı) çevir: ana hidden state üzerine D output head ekle, her biri farklı bir offset tahmin eder. Derinlik başına loss'ların aynı sentetik sinyal üzerinde sequential versiyona nasıl karşılaştırıldığını ölç. Sequential versiyon k > 1 için daha düşük derinlik-k loss üretmeli çünkü ara tahminlere koşulludur.

5. Eğitilmiş MTP modülünü EAGLE-tarzı bir draft olarak kullan: inference'ta `t_{i+k}` önermek için modül k'yı çağır. Held-out bir sequence üzerinde bu draft token'larının ana modelin tahminlerine karşı acceptance rate'ini ölç. Oyuncakta %50+ vurursan, MTP-as-draft empirik özelliğini yeniden ürettin.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MTP module | "Ekstra loss bloğu" | Ana modelin `k` pozisyon önündeki bir token'ı tahmin eden küçük bir transformer bloğu artı projeksiyon |
| Prediction depth | "Hangi offset" | Pozisyon `i`'ye kadar prefix'ten modül `k`'nın `t_{i+k}`'yı tahmin ettiği integer `k` |
| Parallel MTP | "Gloeckle-tarzı" | Aynı backbone hidden state üzerinde D bağımsız head, koşullu zincir yok |
| Sequential MTP | "DeepSeek-V3 tarzı" | Her modül önceki derinliğin hidden state'i artı sonraki token'ın embedding'ine koşulludur; causal zinciri korur |
| Shared output head | "Ana head'i yeniden kullan" | MTP modülleri ana modelin LM head'ini çağırır, ayrı bir output projeksiyonu değil |
| Shared embedding | "Ana tabloyu yeniden kullan" | Aynı vocabulary embedding tablosu her yerde kullanılır; duplicate parametre yok |
| Projection matrix M_k | "Hidden + next-token birleştir" | Önceki hidden state ve hedef-token embedding'ini sonraki derinliğin input'una katlayan bir `h x 2h` lineer katman |
| Joint loss L_MTP | "Ortalanmış ekstra loss'lar" | `lambda` ile ölçeklenmiş derinlik başına cross-entropy loss'larının aritmetik ortalaması |
| Acceptance rate at depth 1 | "MTP draft ne sıklıkla doğru" | D=1 MTP modülünün top-1 tahmininin ana modelin top-1 tahminine eşit olduğu oran; DeepSeek-V3'te %80+ |
| Lambda weighting | "Ekstra-loss önemi" | Derinlik başına ölçekleme faktörü; DeepSeek-V3'te eğitim başında 0.3, daha sonra 0.1 |

## İleri Okuma

- [DeepSeek-AI -- DeepSeek-V3 Technical Report (arXiv:2412.19437)](https://arxiv.org/abs/2412.19437) -- ortak-loss denklemleri ve inference'ta 1.8× hızlanma dahil tam sequential MTP açıklaması (Bölüm 2.2)
- [Gloeckle et al. -- Better & Faster Large Language Models via Multi-token Prediction (arXiv:2404.19737)](https://arxiv.org/abs/2404.19737) -- DeepSeek'in tasarımının üzerine geliştirdiği parallel MTP baseline
- [DeepSeek-V3 model card on Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-V3) -- 685B toplam (671B ana + 14B MTP), deployment notları
- [Leviathan et al. -- Fast Inference from Transformers via Speculative Decoding (arXiv:2211.17192)](https://arxiv.org/abs/2211.17192) -- MTP'nin uyduğu speculative-decoding framework'ü
- [Li et al. -- EAGLE-3 (arXiv:2503.01840)](https://arxiv.org/abs/2503.01840) -- EAGLE'ın 2025 draft mimarisi, MTP'nin rekabet ettiği muadil
