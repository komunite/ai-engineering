# Differential Attention (V2)

> Softmax attention her eşleşmeyen token üzerinde küçük miktarda olasılığı yayar. 100k token boyunca o gürültü birikir ve sinyali boğar. Differential Transformer (Ye et al., ICLR 2025) bunu attention'ı iki softmax'in farkı olarak hesaplayarak, paylaşılan gürültü tabanını çıkararak düzeltir. DIFF V2 (Microsoft, Ocak 2026) production-stack yeniden yazımıdır: baseline Transformer ile eşleşen decode latency, custom kernel yok, FlashAttention-uyumlu. Bu ders V1'den V2'ye uçtan uca, stdlib Python'da çalıştırabileceğin fark operasyonunun çalışan bir oyuncak implementasyonuyla.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 7 · 02 (self-attention), Faz 7 · 15 (attention variants), Faz 10 · 14 (mimari walkthrough)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Softmax attention'ın neden bir gürültü tabanı olduğunu ve neden context uzunluğuyla büyüdüğünü kesin olarak ifade et.
- Differential attention formülünü türet ve çıkarmanın sinyali korurken paylaşılan gürültü bileşenini neden iptal ettiğini açıkla.
- V1-V2 diff'ini yürü: ne hızlandı, ne basitleşti, ne daha kararlı oldu ve her değişiklik production pretraining için neden gerekliydi.
- Differential attention'ı saf Python'da sıfırdan implement et ve sentetik bir signal-plus-noise query'sinde noise-cancellation özelliğini empirik olarak doğrula.

## Sorun

Standart softmax attention'ın ölçekte operasyonel bir baş ağrısına dönüşen matematiksel bir özelliği var. Bir query `q` için, attention ağırlıkları `softmax(qK^T / sqrt(d))`. Softmax asla tam sıfır üretemez — her eşleşmeyen token bir pozitif kütle alır. O artık kütle gürültüdür ve context uzunluğuyla ölçeklenir. 128k token'da, her eşleşmeyen token sadece %0.001 olasılık alsa bile, 127.999'unun toplamı toplamın yaklaşık %12'sini katkı sağlar. Modelin context'le büyüyen bir gürültü tabanını dolaşmayı öğrenmesi gerekiyor.

Empirik olarak bu attention-head interference olarak ortaya çıkar: uzun-context RAG'ta halüsine edilmiş alıntılar, 100k-token retrieval görevlerinde lost-in-the-middle başarısızlıkları ve 32k'nın ötesinde needle-in-haystack benchmark'larında ince accuracy bozulması. Differential Transformer makalesi (arXiv:2410.05258, ICLR 2025) boşluğu ölçtü: DIFF Transformer'lar aynı boyutta baseline'lardan daha düşük perplexity, daha yüksek uzun-context accuracy ve daha az halüsinasyon elde etti.

DIFF V1'in frontier pretraining pipeline'larından dışarıda tutan üç problemi vardı. Value cache'i decode adımı başına iki kez yüklenmek zorundaydı, FlashAttention uyumluluğunu bozan custom CUDA kernel gerektiriyordu ve per-head RMSNorm'u 70B-plus ölçeğinde uzun-koşu eğitimini dengesizleştiriyordu. DIFF V2 (Microsoft unilm blog, 20 Ocak 2026) üçünü de düzeltti. Bu ders her iki versiyonu yürür, fark operatörünü inşa eder ve bir oyuncak query üzerinde noise cancellation'ı benchmark eder.

## Kavram

### Softmax'in Gürültü Tabanı

Bir query `q` ve `K = [k_1, ..., k_N]` keys için, attention ağırlıkları:

```
w_i = exp(q . k_i / sqrt(d)) / sum_j exp(q . k_j / sqrt(d))
```

Hiçbir `w_i` asla sıfır değildir. `k_i` `q` ile tamamen ilgisizse, skor `q . k_i` 0 değildir — varyans `||q||^2 / d` ile sıfır etrafında dalgalanır. Softmax normalizasyonundan sonra, her ilgisiz token hala ağırlıklı toplama `O(1/N)` katkı sağlar. İlgisiz token'ların toplam katkısı `O((N-1)/N) = O(1)` — küçük bir miktar değil.

Modelin istediği sert bir top-k gibi bir şey: eşleşen token'larda yüksek ağırlık, her yerde sıfıra yakın ağırlık. Softmax bunu doğrudan yapmak için çok düz.

### Differential Fikir

Her head'in Q ve K projeksiyonlarını ikiye böl: Q = (Q_1, Q_2) ve K = (K_1, K_2). İki attention map hesapla:

```
A_1 = softmax(Q_1 K_1^T / sqrt(d))
A_2 = softmax(Q_2 K_2^T / sqrt(d))
```

Output:

```
DiffAttn = (A_1 - lambda * A_2) V
```

Çıkarma iki map'in paylaştığı gürültü dağılımını iptal eder. Her iki map'in 127k ilgisiz token üzerinde kabaca uniform ağırlığı varsa (random initialization'da olacağı gibi), bunlar iptal olur. Sinyal — gerçekten alakalı birkaç token üzerindeki tepe ağırlık — her iki map'te aynı büyüklükte göründüğünde ancak iptal olur, ki model eğitildikten sonra olmayacaktır.

`lambda` per-head öğrenilebilir bir scalar'dır, `lambda = exp(lambda_q1 dot lambda_k1) - exp(lambda_q2 dot lambda_k2) + lambda_init` olarak parametrize edilir. Negatif olabilir. `lambda_init` varsayılan olarak 0.8 gibi küçük pozitif bir sayıdır.

### Bu Headed Noise-Cancelling ile Neden Eşleşir

Aynı sesi kaydeden iki gürültülü mikrofonu düşün. Her ikisi de konuşmacıyı artı korele arkaplan gürültüsünü alır. Birini diğerinden çıkar ve paylaşılan gürültü düşer. Ses hayatta kalır çünkü iki sinyal tam iptali engelleyecek kadar phase veya genlikte farklıdır. Per-head `lambda` tam olarak bu dengeyi öğrenir.

### V1 vs V2: Diff

V1 parametre sayısını baseline Transformer'a eşit tuttu. Head başına iki query almak için head dimension'ı yarıladı. Bu head expressiveness'e — ve daha acı verici şekilde — head başına value cache'i yarıladı. Decode adım başına value cache'i iki kez yüklemek zorundaydı (softmax dalı başına bir kez). Sonuç: parametre sayısı eşleşmesine rağmen decode baseline'dan daha yavaş.

V2 query head sayısını iki katına çıkarır ve KV head'lerini aynı tutar (up-projeksiyondan parametre ödünç alarak). Head dimension baseline ile aynı kalır. Çıkarmadan sonra, ekstra dimension baseline Transformer'ın O_W projeksiyonu ile eşleşmek için geri projekte edilir. Üç şey aynı anda gerçekleşir:

1. Decode hızı baseline ile eşleşir (KV cache bir kez yüklenir).
2. FlashAttention değişiklik olmadan çalışır (custom kernel yok).
3. Decode'da arithmetic intensity yükselir (HBM'den yüklenen byte başına daha fazla compute).

V2 ayrıca V1'in çıkarmayı dengelemek için kullandığı per-head RMSNorm'u kaldırır. 70B-sınıfı pretraining ölçeklerinde, o RMSNorm geç eğitimi dengesizleştiriyordu. V2 bunu ek modül olmadan eğitimi kararlı tutan daha basit bir initialization şeması ile değiştirir.

### Ne Zaman Uzanmalı

| İş Yükü | Fayda |
|----------|---------|
| Uzun-context RAG (64k+) | Daha temiz attention map'ler, daha az halüsine edilmiş alıntı |
| Needle-in-haystack benchmark'lar | 32k ötesinde önemli accuracy artışı |
| Çok-dokümanlı QA | Daha az çapraz-doküman parazit |
| 8k'da kod completion | Marjinal, mimari değişikliğine değmez |
| Kısa chat (< 4k) | Baseline'dan esasen ayırt edilemez |

Değer context uzunluğuyla büyür. 4k token'da gürültü tabanı standart attention için yeterince küçüktür. 128k'da seni yaralıyor.

### Diğer 2026 Knob'larıyla Nasıl Yığılır

| Özellik | DIFF V2 ile uyumlu mu? |
|---------|------------------------|
| GQA | Evet (V2 Q head'leri artırır, KV head'leri değil) |
| MLA (DeepSeek) | Prensipte evet, birleştiren yayınlanmış makale yok |
| MoE | Evet (attention MLP blok'tan bağımsızdır) |
| RoPE | Evet (değişmemiş) |
| YaRN / uzun-context scaling | Evet (DIFF'in en çok yardım ettiği yer) |
| FlashAttention | V2'de evet (V1'de hayırdı) |
| Speculative decoding | Evet (attention değişikliği spec-decode döngüsüne görünmez) |

## İnşa Et

`code/main.py` differential attention'ı saf Python'da implement eder. Bilinen signal-plus-noise yapılı bir oyuncak query noise-cancellation oranını doğrudan ölçmene izin verir.

### Adım 1: Standart Softmax Attention

Stdlib matris ops: listelerin listeleri, manual matmul, max'ın sayısal-kararlılık çıkarması ile softmax.

```python
def softmax(row):
    m = max(row)
    exps = [math.exp(x - m) for x in row]
    s = sum(exps)
    return [e / s for e in exps]
```

### Adım 2: Q, K'yı İki Yarıya Böl

V1 tarzı: head dimension'ı yarıla. V2 tarzı: head dimension'ı koru ve head sayısını iki katına çıkar. Oyuncak implementasyon pedagojik netlik için V1 kullanır — matematik özdeştir, sadece defter tutması farklıdır.

### Adım 3: İki Softmax Dalı + Çıkarma

```python
A1 = [softmax([dot(q1, k) / scale for k in K1]) for q1 in Q1]
A2 = [softmax([dot(q2, k) / scale for k in K2]) for q2 in Q2]
diff_weights = [[a1 - lam * a2 for a1, a2 in zip(r1, r2)] for r1, r2 in zip(A1, A2)]
out = [[sum(w * v[j] for w, v in zip(row, V)) for j in range(d_v)] for row in diff_weights]
```

Not: output ağırlıkları negatif olabilir. Bu sorun değil — value cache hala işaretli katkıları halleder. Sonraki V projeksiyonu işareti emer.

### Adım 4: Noise Cancellation Ölçümü

1024 uzunluğunda sentetik bir sequence inşa et. Sinyal token'ını bilinen bir pozisyona yerleştir, geri kalanı gürültüyle doldur. Şunları hesapla: (a) sinyal pozisyonundaki standart softmax attention ağırlığı ve (b) differential attention ağırlığı. Her birinde signal-to-noise oranını ölç. DIFF attention güvenilir şekilde iki dalın ne kadar farklı olmaya eğitildiğine bağlı olarak 3x-10x faktörle daha yüksek bir signal-to-noise oranı üretir.

### Adım 5: V1 vs V2 Parametre Muhasebesi

Bir config verildiğinde (hidden=4096, heads=32, d_head=128), yazdır:

- Baseline Transformer: Q, K, V her biri `hidden * hidden` boyutunda, MLP 4 * hidden'da.
- DIFF V1: Q, K her biri `hidden * hidden` boyutunda, V `hidden * hidden` boyutunda (değişmemiş), head dim dahili olarak yarılanmış. Per-head `lambda` parametreleri ekler (O(heads * d_head)).
- DIFF V2: Q boyutu `2 * hidden * hidden`, K boyutu `hidden * hidden`, V boyutu `hidden * hidden`. O_W'den önce ekstra dim geri projekte edilmiş. Aynı `lambda` parametrelerini ekler.

Oyuncak V2 için ekstra parametre maliyetini ölçer (attention bloğu başına kabaca `hidden * hidden` ekstra) ve yazdırır.

## Kullan

DIFF V2 Nisan 2026 itibarıyla her production inference server'da henüz yayınlanmıyor, ama entegrasyon vLLM ve SGLang'da devam ediyor. Bu arada desen şurada görünür:

- Microsoft iç uzun-context production modelleri.
- 256k-plus context hedefleyen birkaç açık model eğitim koşusunda araştırma replikasyonları.
- Alternatif katmanlarda DIFF attention ile sliding-window attention'ı birleştiren hibrit mimariler.

2026'da bunu ne zaman uzanırdın:

- 64k-plus etkili context hedefleyen sıfırdan yeni bir model eğitirken. Baştan differential attention ekle; sonra yeniden eğitmek pahalı.
- Uzun-context bir modeli fine-tune ederken lost-in-the-middle başarısızlıklarının eval'ında baskın olduğu yerde. Q projeksiyonları üzerinde bir LoRA DIFF yapısını yaklaşık verebilir.

Ne zaman değil:

- Kararlı uzun-context performansa sahip pretrained dense bir model servis ediyorsun. Yeniden eğitim maliyeti mevcut ağırlıklarda nadiren öder.
- Context'in her zaman 16k'nın altında. Gürültü tabanı ihmal edilebilir.

## Yayınla

Bu ders `outputs/skill-diff-attention-integrator.md` üretir. Bir model mimarisi, hedef context uzunluğu, halüsinasyon profili ve eğitim bütçesi verildiğinde, yeni bir pretraining koşusu veya LoRA fine-tune'a differential attention ekleme için bir entegrasyon planı üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Sentetik query üzerinde differential attention için raporlanan signal-to-noise oranının standart softmax attention'dan daha yüksek olduğunu doğrula. Gürültü genliğini değiştir ve standart attention'ın kullanılamaz hale geldiği geçiş noktasını göster.

2. 7B-sınıfı bir model için (hidden=4096, heads=32, d_head=128, 32 katman) baseline'dan DIFF V1'e ve baseline'dan DIFF V2'ye parametre-sayı delta'sını hesapla. Hangi bileşenlerin parametre kazandığını ve hangilerinin aynı kaldığını göster.

3. DIFF V1 makalesinin Bölüm 3'ünü (arXiv:2410.05258) ve DIFF V2 Hugging Face blogunun Bölüm 2'sini oku. İki cümlede, V1 per-head RMSNorm'unun neden gerekli olduğunu ve V2'nin neden eğitim divergence'ına neden olmadan kaldırabildiğini açıkla.

4. Bir ablation implement et: `lambda = 0` (saf ilk softmax) ve `lambda = 1` (tam çıkarma) ile differential attention hesapla. Sentetik query üzerinde, sweep boyunca signal-to-noise'un nasıl değiştiğini ölç. Signal-to-noise'u maksimize eden `lambda`'yı tanımla.

5. Oyuncağı GQA + DIFF V2'ye genişlet. 8 KV head ve 32 Q head seç. KV cache boyutunun aynı (8, 32) konfigürasyonlu baseline GQA modeli ile eşleştiğini göster.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Differential attention | "Birbirinden çıkarılan iki softmax" | Q, K'yı iki yarıya böl, iki softmax map'i hesapla, ikinciyi (lambda ile ölçeklenmiş) birinciden çıkar, sonra V ile çarp |
| Noise floor | "Softmax'in sıfır olmayan kuyruğu" | Softmax'in her ilgisiz token üzerine koyduğu, uzun context'lerde O(1)'e toplanan O(1/N) ağırlık |
| lambda | "Çıkarma scale'i" | `exp(lq1.lk1) - exp(lq2.lk2) + lambda_init` olarak parametrize edilmiş per-head öğrenilebilir scalar; negatif olabilir |
| DIFF V1 | "ICLR 2025 versiyonu" | Orijinal Differential Transformer; parametre sayısını korumak için head dim'i yarılar, custom kernel ister, daha yavaş decode |
| DIFF V2 | "Ocak 2026 düzeltmesi" | KV head'lerini koruyarak Q head'lerini iki katına çıkarır; baseline decode hızıyla eşleşir ve FlashAttention ile çalışır |
| Per-head RMSNorm | "V1 stabilizer'ı" | V1'in farktan sonra uyguladığı ekstra norm; V2 geç-eğitim kararsızlığını önlemek için kaldırdı |
| Signal-to-noise ratio | "Ne kadar attention israf edildi" | Gerçek sinyal pozisyonundaki ağırlığın ilgisiz pozisyonlardaki ortalama ağırlığa oranı |
| Lost in the middle | "Uzun-context başarısızlık modu" | Uzun bir context'in ortasındaki dokümanlar için retrieval accuracy'sinin düştüğü empirik fenomen — DIFF attention bunu azaltır |
| Arithmetic intensity | "Yüklenen byte başına FLOP" | V2'nin decode'da KV yükü başına query'leri iki katına çıkararak artırdığı oran; memory-bound decode için önemli |

## İleri Okuma

- [Ye et al. -- Differential Transformer (arXiv:2410.05258, ICLR 2025)](https://arxiv.org/abs/2410.05258) -- noise-cancellation teorisi ve uzun-context ablation'larıyla orijinal makale
- [Microsoft unilm -- Differential Transformer V2 (Hugging Face blog, Ocak 2026)](https://huggingface.co/blog/microsoft/diff-attn-v2) -- baseline decode ile eşleşen, FlashAttention-uyumlu production-stack yeniden yazımı
- [Understanding Differential Transformer Unchains Pretrained Self-Attentions (arXiv:2505.16333)](https://arxiv.org/abs/2505.16333) -- çıkarmanın neden pretrained attention yapısını kurtardığının teorik analizi
- [Shared DIFF Transformer (arXiv:2501.17900)](https://arxiv.org/html/2501.17900) -- parametre-paylaşma varyantı
- [Vaswani et al. -- Attention Is All You Need (arXiv:1706.03762)](https://arxiv.org/abs/1706.03762) -- DIFF'in çıkardığı baseline Transformer
- [Liu et al. -- Lost in the Middle (arXiv:2307.03172)](https://arxiv.org/abs/2307.03172) -- DIFF attention'ın hedeflediği uzun-context benchmark
