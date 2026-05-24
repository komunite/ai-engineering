# Açık Modeller: Mimari Walkthrough'ları

> Ders 04'te sıfırdan GPT-2 Small inşa ettin. 2026'daki frontier açık modeller beş veya altı somut değişiklikle aynı ailedir. LayerNorm yerine RMSNorm. GELU yerine SwiGLU. Öğrenilmiş pozisyon yerine RoPE. Tam MHA yerine GQA veya MLA. Ölçekte Mixture-of-Experts. Zaten bildiğin matematik onların %95'ini kapsar. Bu ders Llama 3, DeepSeek-V3, Mixtral, Qwen ve Gemma'yı yan yana okur ve her mimarinin diverge ettiği tam satırı adlandırır.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 10, Ders 04, 05, 12 (Pretraining, Scaling, Inference)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Llama 3, Mistral, Mixtral, Gemma 2, Qwen 2.5 ve DeepSeek-V3'ün config.json'unu oku ve her alanı açıkla
- Her modelin GPT-2 Small'a karşı yaptığı spesifik mimari değişikliği adlandır ve ilk prensiplerden gerekçelendir
- Sadece config'inden herhangi bir açık model için parametre sayısı, KV cache boyutu ve activation memory hesapla
- Latency, memory ve yetenek kısıtları verildiğinde bir deployment hedefi için doğru açık modeli seç

## Sorun

Ders 04'te 350 satır numpy yazdın ve GPT-2-şekilli bir modelin oldu. Llama 3 405B'nin 200-sayfalık teknik raporu var. İçgüdün bunların farklı canavarlar olduğu yönünde. Değiller. 200 sayfa aynı objeyi beş veya altı iyi-motive edilmiş modifikasyonla ve scaling hakkında bin implementasyon detayıyla tanımlar. İskelet — embedding, transformer blokları, attention, MLP, norm, head — değişmedi.

Bu ders bir diff'tir. Her büyük açık model ailesi için, GPT-2'den tam olarak neyin değiştiğini, neden ve maliyetinin ne olduğunu listeliyoruz. Bittiğinde, taze bir model card okuyabilir ve onu zihninde GPT-2 baseline'ına geri çevirebilirsin.

Pratik kazanç şu: Meta Llama 5 veya DeepSeek V4 yayınladığında, yeni bir zihinsel modele ihtiyacın olmayacak. Config'e bakacaksın, iyi-bilinen knob'lardan hangilerinin hareket ettiğini göreceksin ve downstream etkilerinin ne olduğunu bileceksin. 2026 mimarileri sonlu bir toolbox. Her yeni model farklı bir alt küme seçer.

## Kavram

### Değişmez Çekirdek

Tüm autoregressive açık modeller şunları paylaşır:

- Token embedding matrisi (vocab_size x hidden_dim).
- N decoder bloğu yığını: norm, self-attention, residual, norm, MLP, residual.
- Son norm ve vocab_size'a projeksiyon yapan linear head (genellikle embedding'lerle weight-tied).
- Causal mask, next-token cross-entropy loss.

Şekil bu. Geri kalan knob'lar.

### Gerçekten Hareket Eden Altı Knob

Tüm 2024-2026 frontier açık modellerinde, aynı altı tasarım seçimi tekrar tekrar seçilir:

1. **Normalizasyon.** LayerNorm -> RMSNorm.
2. **Pozisyonel encoding.** Öğrenilmiş absolute -> RoPE (artı varyantlar: YaRN, NTK).
3. **Aktivasyon.** GELU -> SwiGLU (veya GeGLU).
4. **Attention head paylaşımı.** MHA -> GQA -> MQA -> MLA.
5. **Dense vs sparse MLP.** Dense -> Mixture-of-Experts.
6. **Pre-norm yerleşimi.** Pre-norm kalır. Post-norm gitti.

Diğer her şey (learning rate schedule, data mix, batch size, context length) eğitim config'inde yaşar, mimaride değil. Altı knob.

### Knob 1: RMSNorm

LayerNorm ortalamayı çıkarır, std'ye böler, scale eder ve shift eder. RMSNorm sadece scale'i tutar:

```
RMSNorm(x) = x / sqrt(mean(x^2) + eps) * gamma
```

Ortalama çıkarma yok. Bias yok. Token başına bir matmul daha az. Zhang ve Sennrich (2019) makine çevirisinde LayerNorm ile eşleştiğini ve %10 daha hızlı olduğunu savundu. Her modern açık model bunu çalıştırır.

Maliyet: yok. Fayda: küçük throughput kazancı, daha basit kod.

### Knob 2: RoPE

Öğrenilmiş pozisyon embedding'leri GPT-2'de 1024-slot'luk bir lookup tablosu idi. Context 1025 tablonun sonundan dışarı. Modeller eğitim uzunluğunun ötesine ekstrapolasyon yapamaz.

Rotary Position Embedding (RoPE, Su et al. 2021), attention nokta çarpımından önce her Q ve K vektörünü çiftler halinde döndürerek pozisyon enjekte eder. Dönme açısı pozisyonun deterministik bir fonksiyonudur, dolayısıyla öğrenilen hiçbir şey yok ve tükenecek hiçbir şey yok. Scaling hileleriyle (NTK-aware interpolation, YaRN), 8k context üzerinde eğitilmiş bir model çıkarımda mütevazı accuracy kaybı ile 128k'ya gerilebilir.

```
q_rotated = rotate(q, angle(pos))
k_rotated = rotate(k, angle(pos))
score = q_rotated . k_rotated
```

Her Llama, Mistral, Qwen, DeepSeek ve Gemma RoPE kullanır. Gemma 2 bir hibrit kullanır (çoğu katmanda RoPE, diğerlerinde local sliding-window attention).

### Knob 3: SwiGLU

GPT-2'nin MLP'si `x -> gelu(xW1 + b1) -> (...)W2 + b2`. SwiGLU (Shazeer 2020) aktivasyonu gated bir ürün ile değiştirir:

```
SwiGLU(x) = (xW1) * sigmoid(xW1) * xV
```

Bir yerine iki projeksiyon paralel, Swish aktivasyonu ile gate'lenmiş. Parametre başına perplexity'de empirik olarak daha güçlü. Llama 2 benimsedi, herkes takip etti. MLP'nin hidden size'ı genellikle toplam parametre sayısı orijinal dense MLP ile eşleşecek şekilde ayarlanır: GPT-2 `ff_dim = 4 * hidden` kullandıysa, SwiGLU `ff_dim = (2/3) * 4 * hidden = 8/3 * hidden` kullanır.

### Knob 4: Attention Head Paylaşımı

GPT-2 **Multi-Head Attention (MHA)** kullandı: her head'in kendi Q, K, V projeksiyonu var.

**Multi-Query Attention (MQA, Shazeer 2019)** tüm head'ler arasında bir K ve bir V paylaşır. KV cache'i num_heads kadar keser, bu tipik bir modelde 12x ila 32x bir azalmadır. Zor benchmark'larda accuracy biraz düşer.

**Grouped-Query Attention (GQA, Ainslie et al. 2023)** orta yoldur: G grup Q head bir K ve bir V paylaşır. Llama 3 8B 32 Q head ve 8 KV head (G=8) ile GQA kullanır, dolayısıyla KV cache tam MHA'ya karşı 4x küçülür.

**Multi-Head Latent Attention (MLA, DeepSeek 2024)** K ve V'yi paylaşılan low-rank bir latent'e sıkıştırır ve head başına geri projekte eder. Per-head expressiveness'i koruyarak KV cache'i daha da azaltır. DeepSeek-V2 ve V3 uzun-context performansları için buna güvenir.

| Şema | KV Heads | KV Cache | Accuracy |
|--------|----------|----------|----------|
| MHA    | num_heads | tam | en iyi |
| GQA    | num_groups (G < num_heads) | num_heads / G azalma | MHA-yakın |
| MQA    | 1 | num_heads azalma | küçük kayıp |
| MLA    | latent, head başına decompression | MQA'dan küçük | MHA-yakın |

~13B parametrenin üzerindeki herhangi bir model için, GQA veya MLA etkili olarak zorunludur. Ölçekte tam MHA bir KV cache felaketidir.

### Knob 5: Mixture of Experts

Bir dense MLP her token için tüm parametrelerini aktive eder. Bir MoE MLP blok başına K expert ve token başına top-k expert seçen bir router'a sahiptir (tipik top-2). Sadece o expert'lerin ağırlıkları o token için forward pass görür.

```
router_logits = xW_r
indices, weights = top_k(router_logits, k=2)
output = sum_i weights[i] * expert[indices[i]](x)
```

Cazibesi: her biri 7B boyutunda 64 expert'in olabilir (yani toplam parametre sayısı büyük) ama token başına sadece 2'sini çalıştırırsın (yani token başına compute dense bir 7B model ile eşleşir). Mixtral 8x7B 47B toplam parametreye sahip ama token başına sadece 13B aktive eder. DeepSeek-V3 671B toplam parametreye sahip ama token başına sadece 37B aktive eder.

Artılar: aynı compute, daha fazla parametre, daha iyi kapasite. Eksiler: expert memory'sinin hala bir yerde yaşaması gerekir (dolayısıyla serving dense eşdeğerinden daha fazla VRAM gerektirir), router'ı load-balancing zordur ve alignment sırasında router'ı fine-tune etmek kendi araştırma alanıdır.

### Knob 6: Pre-norm Kalır

Orijinal transformer her sublayer'dan sonra layer norm uyguladı. GPT-2'den beri her açık model bunu her sublayer'dan *önce* koyar. Pre-norm derinlikte eğitmek kesinlikle daha kolaydır. Tartışılacak bir şey yok.

### Model-Model Diff

İşte tüm bunları somut yapan tablo.

| Model | Yıl | Toplam Param | Aktif Param | Norm | Aktivasyon | Pozisyon | Attention | MoE | Context |
|-------|------|-------------|---------------|------|-----------|----------|-----------|-----|---------|
| GPT-2 Small | 2019 | 124M | 124M | LayerNorm | GELU | Öğrenilmiş | MHA (12 head) | hayır | 1k |
| Llama 3 8B | 2024 | 8B | 8B | RMSNorm | SwiGLU | RoPE | GQA (32/8) | hayır | 128k |
| Llama 3 70B | 2024 | 70B | 70B | RMSNorm | SwiGLU | RoPE | GQA (64/8) | hayır | 128k |
| Llama 3 405B | 2024 | 405B | 405B | RMSNorm | SwiGLU | RoPE | GQA (128/16) | hayır | 128k |
| Mistral 7B | 2023 | 7.2B | 7.2B | RMSNorm | SwiGLU | RoPE | GQA | hayır | 32k |
| Mixtral 8x7B | 2023 | 47B | 13B | RMSNorm | SwiGLU | RoPE | GQA | evet (8 expert, top-2) | 32k |
| Gemma 2 9B | 2024 | 9B | 9B | RMSNorm (pre+post) | GeGLU | RoPE + sliding | GQA | hayır | 8k |
| Qwen 2.5 72B | 2024 | 72B | 72B | RMSNorm | SwiGLU | RoPE (YaRN) | GQA (64/8) | hayır | 128k |
| DeepSeek V2 236B | 2024 | 236B | 21B | RMSNorm | SwiGLU | RoPE | MLA | evet (160 expert, top-6) | 128k |
| DeepSeek V3 | 2024 | 671B | 37B | RMSNorm | SwiGLU | RoPE | MLA | evet (256 expert, top-8) | 128k |

Sütunları tara. RMSNorm evrensel. SwiGLU veya GeGLU kuzeni evrensel. RoPE evrensel. 7B üzerinde MLA ile değiştirilmedikçe GQA evrensel. MoE üst uçta differansiyatör.

### Bir config.json Okuma

Llama 3 8B config:

```
{
  "hidden_size": 4096,
  "intermediate_size": 14336,
  "num_hidden_layers": 32,
  "num_attention_heads": 32,
  "num_key_value_heads": 8,
  "max_position_embeddings": 131072,
  "rope_theta": 500000.0,
  "rms_norm_eps": 1e-5,
  "vocab_size": 128256
}
```

Her alan zaten implement ettiğin bir şeye karşılık gelir.

- `hidden_size`: embedding boyutu.
- `intermediate_size`: MLP hidden size (3.5x hidden -- SwiGLU matematiği).
- `num_hidden_layers`: yığın derinliği.
- `num_attention_heads`: Q head'leri.
- `num_key_value_heads`: KV head'leri (GQA).
- `max_position_embeddings`: eğitim context uzunluğu.
- `rope_theta`: RoPE temel frekansı. Meta uzun-context ekstrapolasyonu için varsayılan 10k'dan 500k'ya ölçekledi.
- `rms_norm_eps`: sayısal kararlılık.
- `vocab_size`: token'lar.

Sadece bunlardan toplam parametreleri, KV cache'i ve tepe activation memory'i hesaplarsın. Tam formüller için `code/main.py`'a bak.

### Activation Memory Bütçesi

Activation'lar birkaç milyar parametrenin üzerinde eğitim memory'sini baskıda eder. Pretraining için pratik kural (gradient checkpointing ile):

```
activation_mem ~ batch_size * seq_len * hidden_size * num_layers * bytes_per_element
```

Batch 1, seq 8192, BF16, 32 katman, hidden 4096 ile Llama 3 8B için: checkpointing ile sadece activation'lar için kabaca 8 GB, onsuz 40 GB. Bu yüzden flash-attention ve ring-attention önemlidir — attention hesabını activation'ların sığacağı şekilde yeniden yazarlar.

### KV Cache Bütçesi

Max context'te çıkarım için:

```
kv_cache = 2 * num_layers * num_kv_heads * head_dim * max_seq_len * bytes_per_element
```

128k context, BF16, head_dim = hidden / num_heads = 128 ile Llama 3 8B:
`2 * 32 * 8 * 128 * 131072 * 2 = 17.2 GB` sequence başına.

8B ağırlıkları BF16'da 16 GB. Tek bir 128k sequence için KV cache ağırlıklardan büyük. GQA, MLA ve KV cache quantization araştırmasını yönlendiren memory baskısı budur.

### Her Model Ne Zaman Kazanır

- **Tek 80GB GPU, MoE yok**: Llama 3 8B, Mistral 7B, Gemma 2 9B. Servis etmesi kolay, geniş tooling.
- **Tek node (8x80GB), büyük kapasite**: Llama 3 70B, Qwen 2.5 72B. En yüksek dense açık yetenek.
- **En büyük açık yetenek, MoE karmaşıklığını kabul et**: DeepSeek V3, Mixtral 8x22B. Aktif FLOP başına en iyi yetenek.
- **Uzun-context ihtiyaçları**: Llama 3 (RoPE scaling ile 128k), DeepSeek (MLA avantajı).
- **Düşük-latency serving**: Gemma 2 9B (sliding window uzun-context compute'unu keser).

## İnşa Et

Dersin kodu bir hesap makinesi. Herhangi bir config.json verildiğinde, bileşen başına parametre sayısı, max context'te KV cache, SwiGLU MLP oranı ve mimari hakkında kısa bir karar (dense / GQA / MLA / MoE) yazdırır.

```python
config = {
    "hidden_size": 4096, "intermediate_size": 14336,
    "num_hidden_layers": 32, "num_attention_heads": 32,
    "num_key_value_heads": 8, "vocab_size": 128256,
    "max_position_embeddings": 131072,
}
```

Script mimariyi alan alan yürür, embedding, attention (GQA azalmasıyla), MLP (SwiGLU genişlemesiyle), layernorm'lar ve head için param sayılarını hesaplar. Sonra belirtilen context uzunluğunda KV cache'i hesaplar ve bir özet yazdırır.

Implementasyon için `code/main.py`'a bak.

## Kullan

Hesap makinesini script'e paketlenmiş Llama 3 8B, Mistral 7B, Mixtral 8x7B ve DeepSeek V3 config'lerinde çalıştır. Parametre dökümlerini karşılaştır. MoE modellerinin dense modelleri gölgede bırakan bir toplam param sayısına sahip olduğunu ama genellikle daha küçük bir aktif param sayısına sahip olduğunu fark et. DeepSeek V3'ün KV cache'inin daha fazla toplam parametreye sahip olmasına rağmen Llama 3 405B'ninkinden küçük olduğunu fark et — bu MLA iş başında.

Sonra local olarak sahip olduğun herhangi bir model için bir config plug-in et, özeti oku ve GPU'na sığıp sığmadığına karar ver.

## Yayınla

Bu ders `outputs/skill-open-model-picker.md` üretir. Bir deployment hedefi (GPU tipi, VRAM, context uzunluğu, latency bütçesi) ve bir görev profili (chat, kod, reasoning, uzun-context) verildiğinde, altı mimari knob hakkında açık akıl yürütmeyle Ders 11'den bir quantization şeması ve Ders 12'den bir inference stack ile bir açık model önerir.

## Alıştırmalar

1. HuggingFace'ten Qwen 2.5 72B config'ini oku. Toplam parametreleri sıfırdan hesapla. HF-raporlanan değerle karşılaştır ve herhangi bir delta'nın nereden geldiğini tanımla (head dim yuvarlama, KV paylaşım faktörü vb.).

2. DeepSeek V3 256 expert ile top-8 routing kullanır. Aktive edilen expert'lerin toplam expert'lere oranını hesapla ve Mixtral 8x7B'nin 8'den top-2'sine karşılaştır. Sparse'den (%25) daha yoğun sparse'a (%3) kayma FLOP başına kapasite hakkında ne ima eder?

3. Llama 3 405B için 128k context'te KV cache'i FP8 ve BF16'da hesapla. FP8'de BF16 sayısının yarısıdır. Tek bir 8xH100 node üzerinde (her biri 80GB = toplam 640GB, eksi ağırlık memory'si) kaç paralel sequence servis edebilirsin?

4. Gemma 2 full-attention ve sliding-window-attention katmanlarını alternatif kullanır. Katmanların yarısı tam context yerine 4096-token sliding window kullandığında KV cache için matematiği yaz. Bu 8k toplam context'te ne kadar memory tasarruf eder?

5. Bu ders yazıldıktan sonra yayınlanan yeni bir frontier açık model bul. Altı knob'dan hangisini seçtiğini ve yedinci bir knob tanıtıp tanıtmadığını tanımla. Yeni bir mimari yayınlandığı an müfredat eski hissettirecek — hedef zihinsel modelini yeniden inşa etmeden tablonu güncellemek.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| RMSNorm | "Ortalamasız LayerNorm" | Sadece root mean square ile normalize, öğrenilmiş bir scale ile — daha ucuz ve LayerNorm ile karşılaştırılabilir |
| RoPE | "Rotary pozisyonlar" | Her Q ve K vektörünü pozisyona bağlı bir açıyla 2D çiftler halinde döndür — scaling hileleriyle eğitim uzunluğunun ötesine ekstrapolasyon yapar |
| SwiGLU | "Yeni MLP aktivasyonu" | Swish ile gated linear unit: `(xW1) * sigmoid(xW1) * xV` — her 2024+ açık modelde standart |
| GQA | "Orta yol attention" | Grouped-Query Attention: G grup Q head bir K ve bir V head paylaşır — MQA'nın accuracy kaybı olmadan KV cache'i küçültür |
| MLA | "DeepSeek'in attention'ı" | Multi-Head Latent Attention: K/V'i paylaşılan low-rank bir latent'e sıkıştır, head başına dekompres et — büyük modeller için en küçük KV cache |
| MoE | "Sparse expert'ler" | Mixture of Experts: blok başına N MLP, router token başına top-k seçer — devasa toplam param, küçük aktif param |
| Top-k routing | "Token başına k expert seç" | Router expert başına bir skor hesaplar ve en yüksek k'yı aktive eder — tipik k 2 (Mixtral) ila 8 (DeepSeek) |
| YaRN | "RoPE'u ger" | Yet another RoPE extension — rotary açıları interpolasyon yaparak context'i çıkarım zamanında 8k'dan 128k+'a uzatır |
| Sliding-window attention | "Her şeye attention yapma" | Her token sadece son W token'a attention yapar — token başına attention maliyetini O(W)'ya cap'ler, Gemma 2 ve erken Mistral'da kullanılır |
| Active params | "Token başına ne çalışır" | MoE modeller için, token başına forward pass gören parametre sayısı (toplam param'dan çok daha küçük) — token başına FLOP'ları yönetir |

## İleri Okuma

- [Dubey et al., 2024 -- "The Llama 3 Herd of Models"](https://arxiv.org/abs/2407.21783) -- dense Llama 3 ailesi için mimari ve eğitim referansı
- [DeepSeek-AI, 2024 -- "DeepSeek-V3 Technical Report"](https://arxiv.org/abs/2412.19437) -- MLA artı auxiliary-loss-free load balancing artı 671B MoE
- [Jiang et al., 2024 -- "Mixtral of Experts"](https://arxiv.org/abs/2401.04088) -- standart MoE açık model makalesi
- [Su et al., 2021 -- "RoFormer: Enhanced Transformer with Rotary Position Embedding"](https://arxiv.org/abs/2104.09864) -- RoPE makalesi
- [Shazeer, 2020 -- "GLU Variants Improve Transformer"](https://arxiv.org/abs/2002.05202) -- SwiGLU, GeGLU ve arkadaşları
- [Ainslie et al., 2023 -- "GQA: Training Generalized Multi-Query Transformer Models"](https://arxiv.org/abs/2305.13245) -- GQA makalesi
- [Gemma 2 Team, 2024 -- "Gemma 2: Improving Open Language Models at a Practical Size"](https://arxiv.org/abs/2408.00118) -- hibrit full+sliding attention, pre+post-norm
- [Qwen Team, 2024 -- "Qwen 2.5 Technical Report"](https://arxiv.org/abs/2412.15115) -- YaRN context uzatması ve uzun-context eğitim reçeteleri
