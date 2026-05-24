# Native Sparse Attention (DeepSeek NSA)

> 64k token'da, attention decode latency'sinin %70-80'ini yer. Her açık-model lab'ının düzeltmek için bir planı var. DeepSeek'in NSA'sı (ACL 2025 en iyi makale) yapışan oldu: üç paralel attention dalı — sıkıştırılmış kaba-grain token'lar, seçici olarak tutulan ince-grain token'lar ve yerel context için sliding window'lar — öğrenilmiş bir gate üzerinden birleştirilmiş. Hardware-aligned (kernel-friendly), natively trainable (pretraining'de çalışır, çıkarımda cıvatalanmaz) ve 64k decode'larda FlashAttention'dan daha hızlı çalışır, tam attention kalitesini eşler veya geçer. Bu ders üç dalı uçtan uca inşa eder ve sparsity'nin neden uçtan uca türevlenebilir olduğunu gösterir.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 7 · 12 (KV cache, flash-attention), Faz 7 · 15 (attention variants), Faz 10 · 16 (differential attention)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Üç NSA attention dalını ve her birinin neyi yakaladığını ifade et.
- Önceki sparse-attention yöntemleri inference-only iken NSA'nın neden "natively trainable" olduğunu açıkla.
- 64k context'te NSA'nın tam attention'a karşı attention compute tasarrufunu compression block boyutu ve seçim top-k'ı fonksiyonu olarak hesapla.
- Kısa bir sentetik sequence üzerinde stdlib Python'da üç-dal kombinasyonunu implement et ve gating ağırlıklarının davranışını doğrula.

## Sorun

Sequence uzunluğu N'de tam attention zamanda `O(N^2)` ve katman başına KV cache'te `O(N)` maliyetlidir. 64k token'da, compute ve memory bandwidth sayıları felakettir. NSA makalesinden ölçülen teorik tahmin: attention 64k'da toplam decode latency'sinin %70-80'ini oluşturur. Aşağı yöndeki her şey — TTFT, token/sn, milyon token başına maliyet — attention maliyeti tarafından baskındır.

Sparse attention bariz cevaptır. Önceki girişimler iki kovaya düşer. Fixed-pattern sparsity (sliding-window, strided, block-local) bilgiyi atar ve uzun-mesafe recall görevlerinde başarısız olur. Inference-time sparsity (KV cache pruning, H2O, StreamingLLM) dense attention üzerinde pretrain edilmiş bir modele uygulanır ve potansiyel hızlanmanın sadece bir kısmını kurtarır çünkü modelden asla bilgiyi sparse desen üzerinden yönlendirmesi istenmedi.

Native Sparse Attention (Yuan et al., DeepSeek + PKU + UW, ACL 2025 en iyi makale, arXiv:2502.11089) her ikisini de yapar: modelin pretraining sırasında öğrendiği bir sparsity deseni, çıkarımda compute tasarrufunu gerçekten sağlayan kernel-aligned bir algoritma olarak implement edilmiş. İki yıl sonra, NSA veya doğrudan bir torunu her frontier uzun-context modelinde varsayılan attention olacak.

## Kavram

### Üç Paralel Dal

Her query için, NSA attention'ı KV cache'in üç farklı görünümüne karşı üç kez çalıştırır:

1. **Compressed dal.** Token'lar `l` boyutunda bloklar halinde gruplanır (tipik 32 veya 64). Her blok küçük öğrenilmiş bir MLP üzerinden tek bir summary token'a sıkıştırılır. Query bu compressed token'lara attention yapar, tüm sequence'in kaba-grain bir görünümünü elde eder.

2. **Selected dal.** Compressed dalın attention skorlarını kullanarak, mevcut query ile en alakalı top-k blok tanımlanır. O bloklardan ince-grain (sıkıştırılmamış) token'lar okunur ve query hepsine attention yapar. Compressed-dal attention'ı seçim için yönlendirme sinyali olarak düşün.

3. **Sliding-window dal.** Query yerel context için en son `W` token'a (tipik 512) attention yapar. Bu dal diğer ikisinin kaçırabileceği yapı-ağırlıklı kısa-mesafe desenleri (syntax, yerel coreference) yakalar.

Üç dal output'u öğrenilmiş per-pozisyon bir gate üzerinden birleştirilir:

```
out = g_cmp * out_cmp + g_sel * out_sel + g_win * out_win
```

`g_cmp, g_sel, g_win` query üzerinde küçük bir MLP'den gate ağırlıkları. 1'e toplanmak zorunda değiller — dalları bağımsız ağırlıklayabilirler.

### Neden "Natively Trainable"

Seçim adımı (top-k blok) discrete'tir. Discrete operasyonlar gradient akışını bozar. Önceki sparse-attention çalışmaları ya seçim üzerinden backprop'u atladı (eğitimi sınırladı) ya da çıkarımda gerçek sparsity vermeyen sürekli relaxation'lar kullandı.

NSA bunu atlatır: compressed-dal attention'ı kendisi tüm sequence üzerinde türevlenebilir kaba-grain bir attention'dır. Top-k operasyonu sadece hangi ince-grain blokların yüklenileceğini seçmek için compressed daldan en yüksek attention skorlarını yeniden kullanır. Gradient'lar compressed-dal skorları üzerinden akar (hem compressed output'u HEM seçim mantığını etkilerler) ve seçilen blokların final output'a katkısı da türevlenebilir. Türevlenebilir olmayan `top_k` operasyonu forward computational graph üzerinde bir no-op'tur — sadece hangi blokların memory'den yüklendiğini kontrol eder.

Bu yüzden NSA pretraining'de uçtan uca kullanılabilir. Model bilgiyi üç dal üzerinden ortak yönlendirmeyi öğrenir, çıkarımda vaat edilen hızlanmayı sağlayan bir sparse desen üretir.

### Hardware-Aligned Kernel

NSA'nın kernel'i modern GPU memory hiyerarşileri için tasarlandı. Kernel query'leri GQA grupları başına yükler (dış döngü), karşılık gelen sparse KV bloklarını grup başına fetch eder (iç döngü) ve attention'ı SRAM'de çalıştırır. Her query grubu aynı seçili blokları gördüğü için (seçim per-query-grup, per-query-head değil), KV yüklemeleri grup boyunca amortize edilir. Arithmetic intensity yüksek kalır.

Makale 64k decode'larda FlashAttention'dan 9x daha hızlı çalışan Triton kernel'leri raporluyor, hızlanma oranı sequence uzunluğuyla büyür. Forward ve backward kernel'lerin her ikisi de sağlanmış.

### Compute Bütçesi

`N` sequence uzunluğu olsun, `l` compression block boyutu, `k` top-k seçim sayısı, `w` sliding window, `b` seçili block boyutu (tipik `l`'ye eşittir).

- Compressed dal: query başına `O(N/l)` key, dolayısıyla toplam `O(N * N / l)`.
- Selected dal: query başına `O(k * b)` key, dolayısıyla `O(N * k * b)`.
- Sliding dal: query başına `O(w)` key, dolayısıyla `O(N * w)`.

Toplam: `O(N * (N/l + k*b + w))`.

`N = 64k, l = 64, k = 16, b = 64, w = 512` ile: query başına maliyet `1000 + 1024 + 512 = 2536 key`. Tam attention `64000 key`. 25x compute azalması.

`N = 128k, l = 64, k = 16, b = 64, w = 512` ile: query başına maliyet `2000 + 1024 + 512 = 3536 key`. Tam attention `128000 key`. 36x azalma. Fayda sequence uzunluğuyla büyür, ki bu tüm amaç.

### Nasıl Karşılaştırılır

| Yöntem | Türevlenebilir | Gerçek inference hızlanması | Uzun-mesafe recall |
|--------|---------------|----------------------|-------------------|
| Sadece sliding window | evet | evet | başarısız |
| Strided / block-sparse | evet | evet | kısmi |
| KV pruning (H2O, StreamingLLM) | N/A (inference-time) | evet | kısmi |
| MoBA (Moonshot) | kısmi | evet | iyi |
| NSA | evet (natively) | evet (64k'da 9x) | tam attention'ı eşler |

MoBA (Moonshot, arXiv:2502.13189) eşzamanlı yayınlandı ve benzer bir three-is-better-than-one yaklaşımı alır, MoE prensibini attention bloklarına uygular. NSA ve MoBA 2026 uzun-context pretraining için bilinmesi gereken iki mimaridir.

## İnşa Et

`code/main.py` kısa bir sentetik sequence üzerinde üç dalı implement eder ve şunları gösterir:

- Compression MLP (pedagojik netlik için basit bir mean-pool baseline kullanılıyor; gerçek NSA öğrenilmiş bir MLP kullanır).
- Compressed-dal skorları tarafından yönlendirilen top-k block seçimi.
- Son `w` token üzerinde sliding-window attention.
- Gated kombinasyon.
- Tam attention ile karşılaştıran compute-count yazdırması.

### Adım 1: Token'ları Bloklara Sıkıştır

```python
def compress(K, l):
    n = len(K)
    n_blocks = (n + l - 1) // l
    out = []
    for b in range(n_blocks):
        start, end = b * l, min((b + 1) * l, n)
        block = K[start:end]
        summary = [sum(row[d] for row in block) / len(block) for d in range(len(K[0]))]
        out.append(summary)
    return out
```

### Adım 2: Compressed-Dal Attention

Compressed key'lere karşı query'nin softmax attention'ını çalıştır. Compressed-dal skorları top-k seçimi için sinyal olarak ikiye katlanır.

### Adım 3: Top-k Block Seçimi

`k` en yüksek-skorlu compressed bloğun indislerini seç. O bloklardan orijinal sıkıştırılmamış token'ları yükle ve onlar üzerinde attention çalıştır.

### Adım 4: Sliding-Window Attention

Son `w` token'ı al ve onlara karşı standart attention çalıştır.

### Adım 5: Gate + Birleştir

Query üzerinde küçük bir MLP üç gate ağırlığı üretir. Final output üç dal output'unun ağırlıklı toplamıdır.

### Adım 6: Compute Sayma

Her dal için query başına attend edilen key sayısını ve toplamı yazdır. `N` (tam attention) ile karşılaştır. `l = 32, k = 4, w = 128` ile 1024-token sentetik üzerinde, NSA tam attention için 1024'e karşı query başına `32 + 128 + 128 = 288` key görür — 3.5x daha az.

## Kullan

NSA DeepSeek'in kendi uzun-context pretraining pipeline'ında yayınlanıyor. Nisan 2026 itibarıyla public inference stack'lerinde entegrasyon durumu:

- **DeepSeek iç**: native, yayınlanmış ağırlıklar NSA veya halefi DSA'yı (Deepseek Sparse Attention) kullanır.
- **vLLM**: DeepSeek-V3.x ağırlıkları için geliştirme aşamasında deneysel NSA desteği.
- **SGLang**: NSA benchmark'ları yayınlandı; production yolu vLLM'i takip eder.
- **llama.cpp / CPU**: desteklenmiyor; kernel ayrışmasının overhead'i CPU throughput'unda değerli değil.

NSA için ne zaman uzanmalı:

- Ciddi bir compute bütçesi ile 64k-plus context hedefleyen pretraining veya continued-training koşusu.
- DeepSeek'in kendi uzun-context checkpoint'lerinin çıkarımı. Ağırlıklar NSA-native.

Ne zaman değil:

- Mevcut bir dense-attention pretrained modeli servis ediyorsun. Continued training olmadan NSA'yı retrofit edemezsin.
- 16k altı context. Üç-dal overhead'i tasarrufları baskıda eder.
- Batch-1 etkileşimli chat. Latency-hassas decode yararlanır, ama sadece uzun context'lerde.

## Yayınla

Bu ders `outputs/skill-nsa-integrator.md` üretir. Uzun-context bir pretraining koşu spesifikasyonu verildiğinde, bir NSA entegrasyon planı üretir: compression block boyutu, top-k, sliding window, gate MLP genişliği, kernel seçimi ve mimari değişikliği gerekçelendirecek spesifik uzun-context eval'lar.

## Alıştırmalar

1. `code/main.py`'ı 1024-token sentetik üzerinde çalıştır. `(l, k, w)`'yi üç preset boyunca sweep et ve compute count'larını yazdır. Bir needle-in-haystack testi üzerinde tam attention'a karşı %95 recall korurken query başına en düşük key-count'u elde eden preset'i tanımla.

2. Mean-pool compressor'ı minik öğrenilmiş bir MLP (2-katmanlı, hidden 32) ile değiştir. Sinyalin bir bloğun ortalaması olduğu sentetik bir görevde eğit. Held-out veride mean-pool baseline'a karşı perplexity boşluğunu ölç.

3. Gate MLP'i implement et. Query'i input olarak alır ve üç scalar üretir. Gate'in mantıklı davrandığını göster: rastgele query'lerde neredeyse-uniform ağırlıklama, query uzak-arka bir bloğa vurduğunda seçili dal üzerinde ağır ağırlık.

4. 128k context'te NSA-etkin 70B model için KV cache memory bütçesini hesapla. KV head'leri 8, head dim 128, BF16. Tam attention'a ve MLA'ya karşılaştır (Faz 10 · 14 MLA'nın sayılarını gösterdi). NSA'nın ince-grain dal KV cache'inin tam attention'a eşit olduğu sequence uzunluğunu tanımla.

5. NSA makalesinin Bölüm 4'ünü (arXiv:2502.11089) oku ve compressed dalın attention skorlarının ayrı bir routing skoru hesaplamak yerine top-k seçimi için neden yeniden kullanıldığını üç cümlede açıkla. Cevabı gradient akışına bağla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Compressed branch | "Kaba görünüm" | Query başına O(N/l) key'de global context sağlayan block-ortalanmış key'ler üzerinde attention |
| Selected branch | "Top-k blok" | En yüksek compressed-dal skorlu `k` blok üzerinde ince-grain attention |
| Sliding window | "Yerel context" | Kısa-mesafe desenler için son `W` token üzerinde attention |
| Native trainability | "Sparsity açıkken pretrain" | Sparsity deseni pretraining sırasında öğrenilir, çıkarımda cıvatalanmaz |
| Compression block size l | "Kaba görünüm için grup boyutu" | Kaç token tek bir summary'ye birleştirilir; 32-64 tipik |
| Top-k | "Tutulacak blok" | Sıkıştırılmamış token'ları okunan compressed blok sayısı; 16 tipik |
| Sliding window W | "Yerel attention yarıçapı" | Tipik 512; daha kısa yerel coherence'ı zedeler, daha uzun compute israf eder |
| Branch gate | "Üçünü nasıl karıştırır" | Üç dalın katkılarını ağırlıklayan per-pozisyon MLP output'u |
| Hardware alignment | "Kernel-friendly sparsity" | Gerçek GPU kernel'inin teorik hızlanmayı elde ettiği şekilde seçilmiş sparse desen |
| DSA | "NSA'nın halefi" | Deepseek Sparse Attention, DeepSeek'in soy çizgisinde NSA'yı takip eden mimari |

## İleri Okuma

- [Yuan et al. -- Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention (arXiv:2502.11089, ACL 2025 Best Paper)](https://arxiv.org/abs/2502.11089) -- makale
- [DeepSeek-V3 Technical Report (arXiv:2412.19437)](https://arxiv.org/abs/2412.19437) -- NSA'nın hedeflediği mimari aile
- [Moonshot AI -- MoBA: Mixture of Block Attention for Long-Context LLMs (arXiv:2502.13189)](https://arxiv.org/abs/2502.13189) -- eşzamanlı çalışma, blok üzerinde MoE-tarzı attention
- [Beltagy et al. -- Longformer: The Long-Document Transformer (arXiv:2004.05150)](https://arxiv.org/abs/2004.05150) -- sliding-window kökenleri
- [Xiao et al. -- StreamingLLM: Efficient Streaming Language Models with Attention Sinks (arXiv:2309.17453)](https://arxiv.org/abs/2309.17453) -- NSA'nın geliştirdiği inference-time sparsity baseline
- [Dao et al. -- FlashAttention-2 (arXiv:2307.08691)](https://arxiv.org/abs/2307.08691) -- NSA kernel'lerinin 64k'da yendiği tam-attention baseline
