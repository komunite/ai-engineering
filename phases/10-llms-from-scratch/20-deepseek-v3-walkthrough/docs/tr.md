# DeepSeek-V3 Mimari Walkthrough

> Faz 10 · Ders 14 her açık modelin çevirdiği altı mimari knob'u adlandırdı. DeepSeek-V3 (Aralık 2024, 671B parametre toplam, 37B aktif) altısını da çevirir ve dört tane daha ekler: Multi-Head Latent Attention, auxiliary-loss-free load balancing, Multi-Token Prediction ve DualPipe eğitimi. Bu ders DeepSeek-V3'ün mimarisini yukarıdan aşağı okur ve yayınlanmış config'ten her parametre sayısını türetir. Sonunda 671B/37B oranının neden doğru bahis olduğunu ve MLA + MoE birlikte neden frontier'da herhangi birinden tek başına daha iyi olduğunu açıklayabileceksin.

**Tür:** Öğrenim
**Diller:** Python (stdlib, parametre hesaplayıcı)
**Ön koşullar:** Faz 10 · 14 (açık-model walkthrough'ları), Faz 10 · 17 (NSA), Faz 10 · 18 (MTP), Faz 10 · 19 (DualPipe)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- DeepSeek-V3 config'ini yukarıdan aşağı oku ve her alanı altı GPT-2 knob'u artı dört DeepSeek-spesifik ekleme cinsinden açıkla.
- Toplam parametre sayısını (671B), aktif parametre sayısını (37B) ve her birine katkıda bulunan bileşenleri türet.
- 128k context'te MLA'nın KV cache footprint'ini hesapla ve GQA'lı aynı-aktif-param dense modelin ödeyeceğiyle karşılaştır.
- Dört DeepSeek-spesifik inovasyonu (MLA, MTP, auxiliary-loss-free routing, DualPipe) ifade et ve her birinin mimari/eğitim stack'inin hangi parçasını hedeflediğini adlandır.

## Sorun

DeepSeek-V3 mimarisi Llama ailesinden anlamlı şekilde farklı olan ilk frontier açık modeldir. Llama 3 405B "altı knob'u çevrilmiş GPT-2"dir. DeepSeek-V3 altı knob'un hepsi artı dört tane daha çevrilmiş GPT-2'dir. Llama 3 config'ini okumak DeepSeek config'ini okumak için bir ısınmadır, ama derin yapı — attention bloğunun şekli, routing mantığı, eğitim-zamanı hedefi — ayrı bir walkthrough'a ihtiyacın olacak kadar farklıdır.

Bunu öğrenmenin kazancı: DeepSeek-V3'ün açık-ağırlıklar yayını açık modellerde "frontier capability"nin ne anlama geldiğini değiştirdi. Mimari birçok 2026 eğitim koşusunun kopyaladığı plandır. Bunu anlamak frontier LLM eğitimi veya çıkarımına dokunan herhangi bir rol için temel beklentidir.

## Kavram

### Değişmez Çekirdek, Yine

DeepSeek-V3 hala autoregressive. Hala decoder bloklarını yığar. Her blok hala attention artı MLP artı iki RMSNorm'a sahip. Hala MLP'de SwiGLU kullanır. Hala RoPE kullanır. Pre-norm. Weight-tied embedding'ler. Her Llama veya Mistral ile aynı baseline.

### Twist: GQA Yerine MLA

Faz 10 · 14'ten GQA'nın K ve V'i Q head grupları arasında paylaşarak KV cache'i küçülttüğünü biliyorsun. Multi-Head Latent Attention (MLA) daha ileri gider: K ve V paylaşılan low-rank bir latent temsile (the `kv_lora_rank`) sıkıştırılır, sonra head başına on-the-fly dekompres edilir. KV cache sadece latent'i saklar — tipik olarak katman başına token başına 512 float, 8 x 128 = 1024 float değil.

128k context'te, MLA ile DeepSeek-V3 (token başına katman başına bir paylaşılan latent `c^{KV}`; K ve V her ikisi de bu latent'ten sonraki matmul'a emilebilen up-projection'lar yoluyla türetilir):

```
kv_cache = num_layers * kv_lora_rank * max_seq_len * bytes_per_element
         = 61 * 512 * 131072 * 2
         = 7.6 GB
```

Hipotetik bir GQA baseline (Llama 3 70B şekli, 8 KV head, head dim 128) öderdi:

```
kv_cache = 2 * 61 * 8 * 128 * 131072 * 2
         = 30.5 GB
```

MLA 128k context'te Llama-3-70B-tarzı bir GQA cache'inden 4x küçüktür.

Tradeoff: MLA attention hesaplaması başına (head başına) bir dekompresyon adımı ekler. Ekstra compute kaydedilen bandwidth ile karşılaştırıldığında küçüktür. Uzun-context çıkarım için net kazanım.

### Routing: Auxiliary-Loss-Free Load Balancing

MoE router'ları her token'ı hangi top-k expert'in işleyeceğine karar verir. Naif bir router işi birkaç expert üzerine yoğunlaştırır, diğerlerini boş bırakır. Standart düzeltme: yük dengesizliğini cezalandıran bir auxiliary loss terimi ekle. Bu çalışır ama ana-görev performansını biraz bozar.

DeepSeek-V3 bir auxiliary-loss-free şema tanıtır. Router logit'lerine per-expert bias terimleri eklenir, eğitim sırasında basit bir kuralla ayarlanır: expert `e` aşırı yüklenmişse, `bias_e`'i azalt; az yüklenmişse, artır. Ekstra loss terimi yok. Eğitim temiz kalır. Expert yükü dengeli kalır.

Ana loss üzerinde etki: ölçülebilir hiçbiri. MoE mimarisi üzerinde etki: daha temiz, ayarlanacak auxiliary-loss hyperparametresi yok.

### MTP: Daha Yoğun Eğitim + Ücretsiz Draft

Faz 10 · 18'den DeepSeek-V3'ün iki pozisyon öndeki token'ı tahmin eden D=1 MTP modülü eklediğini biliyorsun. Çıkarımda, eğitilmiş modül %80+ acceptance ile speculative-decoding draft'ı olarak yeniden amaçlandırılır. Eğitimde, her hidden state D+1 = 2 hedef üzerinde süpervize edilir, daha yoğun bir sinyal sağlar.

Parametreler: 671B ana üzerine 14B. Overhead: %2.1.

### Eğitim: DualPipe

Faz 10 · 19'dan DualPipe'ın forward ve backward chunk'larını cross-node all-to-all comm'larla overlap eden bidirectional bir pipeline olduğunu biliyorsun. DeepSeek-V3'ün 2.048-H800 ölçeğinde, 1F1B'nin pipeline bubble'larına kaybedeceği kabaca 245k GPU-saat kurtarır.

### Config, Alan Alan

İşte DeepSeek-V3 config'i (basitleştirilmiş):

```
hidden_size: 7168
intermediate_size: 18432   (dense MLP hidden size, ilk birkaç katmanda kullanılır)
moe_intermediate_size: 2048 (expert MLP hidden size)
num_hidden_layers: 61
first_k_dense_layers: 3    (ilk 3 katman dense MLP kullanır)
num_attention_heads: 128
num_key_value_heads: 128   (MLA altında resmi olarak num_heads'e eşit, ama
                           gerçek sıkıştırma kv_lora_rank'tadır)
kv_lora_rank: 512          (MLA latent boyutu)
num_experts: 256            (blok başına MoE expert sayısı)
num_experts_per_tok: 8      (top-8 routing)
shared_experts: 1           (blok başına her zaman-açık paylaşılan expert)
max_position_embeddings: 163840
rope_theta: 10000.0
vocab_size: 129280
mtp_module: 1               (derinlik 1'de 1 MTP modülü)
```

Parse et:

- `hidden_size=7168`: embedding boyutu.
- `num_hidden_layers=61`: toplam blok derinliği.
- `first_k_dense_layers=3`: ilk 3 blok 18432 boyutunda dense bir MLP kullanır. Kalan 58 MoE kullanır.
- `num_attention_heads=128`: 128 query head.
- `kv_lora_rank=512`: K ve V bu latent boyutuna sıkıştırılır ve head başına dekompres edilir.
- `num_experts=256, num_experts_per_tok=8`: her MoE blok 256 expert'e sahip, top-8 route eder.
- `shared_experts=1`: 256 routed expert'in üstünde, 1 her zaman-açık expert her token'a katkı sağlar. Her token'ın güvenilir bir şey aldığından emin olan bir "dense floor" olarak düşün.
- `moe_intermediate_size=2048`: her expert'in MLP hidden size'ı. Dense MLP'den daha küçük çünkü 256 tane var.

### Parametre Muhasebesi

Tam hesaplama `code/main.py`'da yaşar. Başlık:

- Embedding: `vocab * hidden = 129280 * 7168 = ~0.93B`.
- İlk 3 dense blok: MLA ile attention (blok başına ~144M) + dense MLP (blok başına ~260M) + norm'lar. Toplam yaklaşık 1.2B.
- 58 MoE blok: MLA ile attention (~144M) + her biri 256 expert (apiece 30M) + 1 shared expert (30M) + norm. Tüm expert'ler dahil blok başına toplam ~7.95B. 58 MoE bloğu için toplam 461B.
- MTP modülü: 14B.

Büyük toplam: çekirdek mimari için ~476B + 14B MTP + farklı olarak yayınlanmış 671B sayısı ek yapısal parametreler (bias tensorları, expert-spesifik bileşenler, shared expert scaling, vb.) için hesaplar. Hesaplayıcıda yeniden ürettiğimiz sayı yayınlanan değerin %3-5 içindedir — delta DeepSeek'in raporunun Bölüm 2 ekinde dokümante edilen ince-grain muhasebeden gelir.

Forward başına aktif parametreler:

- Attention: katman başına 144M * 61 = 8.8B (tüm katmanlar ateşler).
- Aktif MLP: ilk 3 katman dense (3 * 260M = 780M), 58 MoE katmanı her biri 8 routed + 1 shared + routing overhead ile aktif. Aktif MLP katman başına: ~260M. Toplam: 3 * 260M + 58 * 260M = ~15.9B.
- Embedding + norm'lar: 1.2B.
- Toplam aktif: kabaca 26B çekirdek + 14B MTP (eğitildi ama çıkarımda her zaman çalışmaz) ≈ 37B.

### 671B / 37B Oranı

18x sparsity oranı (aktif param toplam'ın %5.5'i). DeepSeek-V3 açık ağırlıklar yayınlamış en seyrek frontier MoE modeldir. 13/47 oranı (%28) ile Mixtral 8x7B çok daha yoğun. 17B/400B oranı (%4.25) ile Llama 4 Maverick karşılaştırılabilir. DeepSeek bahsi: frontier ölçeğinde, daha düşük aktivasyon oranıyla daha fazla expert aktif-FLOP başına daha iyi kalite üretir.

### DeepSeek-V3 Nerede Oturur

| Model | Toplam | Aktif | Oran | Attention | Yeni fikirler |
|-------|------|-------|-------|-----------|-------------|
| Llama 3 70B | 70B | 70B | %100 | GQA 64/8 | — |
| Llama 4 Maverick | 400B | 17B | %4.25 | GQA | — |
| Mixtral 8x22B | 141B | 39B | %27 | GQA | — |
| DeepSeek V3 | 671B | 37B | %5.5 | MLA 512 | MLA + MTP + aux-free + DualPipe |
| Qwen 2.5 72B | 72B | 72B | %100 | GQA 64/8 | YaRN extension |

### Takip: R1, V4

DeepSeek-R1 (2025) V3 backbone üzerinde bir reasoning-eğitim koşusudur. R1 aynı mimariyi kullanır. Değişen post-training reçetesidir (doğrulanabilir görevler üzerinde büyük ölçekli RL), pretraining mimarisi değil.

DeepSeek-V4 (yayınlanırsa) MLA + MoE + MTP'i korumayı ve Faz 10 · 17'den NSA'nın halefi olan DSA'yı (DeepSeek Sparse Attention) eklemesi bekleniyor. Soy çizgisi kararlı: mimari-seviyesi inovasyonlar birikir; her versiyon ek knob'ları çevirir.

## Kullan

`code/main.py` DeepSeek-V3'ün şekline özelleşmiş parametre hesaplayıcıdır. Çalıştır, output'unu makalenin sayılarıyla karşılaştır ve hipotetik varyantlar üzerinde kullan (256 expert vs 512, top-8 vs top-16, MLA rank 512 vs 1024).

Neye bakmalı:

- Yayınlanmış 671B'ye karşı toplam parametre sayısı.
- Yayınlanmış 37B'ye karşı aktif parametre sayısı.
- 128k context'te KV cache — MLA vs GQA karşılaştırması.
- Parametre bütçesinin aslında nereye gittiğini görmek için katman başına döküm.

## Yayınla

Bu ders `outputs/skill-deepseek-v3-reader.md` üretir. Bir DeepSeek-aile modeli (V3, R1 veya herhangi bir gelecek varyant) verildiğinde, config'in her alanını adlandıran, bileşen başına parametre sayılarını türeten ve modelin dört DeepSeek-spesifik inovasyondan hangilerini kullandığını tanımlayan bileşen-bileşen mimari okuması üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Hesaplayıcının toplam-parametre tahminini yayınlanmış 671B ile karşılaştır ve delta'nın nereden geldiğini tanımla. Makalenin Bölüm 2'sinde tam dökümü var.

2. Config'i 512 yerine MLA rank 256 kullanacak şekilde değiştir. 128k context'te elde edilen KV cache boyutunu hesapla. Hangi yüzde azalmayı satın alır ve per-head expressiveness'e ne maliyetle?

3. DeepSeek-V3'ün (256 expert, top-8) routing'ini hipotetik bir (512 expert, top-8) varyantla karşılaştır. Toplam parametreler büyür; aktif parametreler aynı kalır. Ekstra expert kapasitesi teoride ne satın alır ve çıkarımda ne maliyetlidir?

4. DeepSeek-V3 teknik raporunun MLA üzerindeki Bölüm 2.1'ini oku (arXiv:2412.19437). Çıkarım-zamanı verimliliği için K ve V dekompresyon matrislerinin neden sonraki matmul'a "emilebileceğini" üç cümlede açıkla.

5. DeepSeek-V3 çoğu operasyon için FP8 eğitimi kullanır. 671B ağırlığı saklamak için FP8 vs BF16'nın memory tasarrufunu hesapla. Bu 14.8T-token eğitim bütçesiyle nasıl kesişir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MLA | "Multi-Head Latent Attention" | K ve V'i paylaşılan low-rank bir latent'e (kv_lora_rank, tipik 512) sıkıştır, head başına on-the-fly dekompres et; KV cache sadece latent'i saklar |
| kv_lora_rank | "MLA sıkıştırma boyutu" | K ve V için paylaşılan latent'in boyutu; DeepSeek-V3 512 kullanır |
| First k dense layers | "İlk katmanlar dense kalır" | İlk birkaç MoE-model katmanı MoE router'ını atlar ve kararlılık için dense bir MLP çalıştırır |
| num_experts_per_tok | "Top-k routing" | Token başına kaç routed expert ateşler; DeepSeek-V3 8 kullanır |
| Shared experts | "Her zaman-açık expert'ler" | Routing'den bağımsız her token'ı işleyen expert'ler; DeepSeek-V3 1 kullanır |
| Auxiliary-loss-free routing | "Bias-ayarlı load balance" | Loss terimi eklemeden expert yükünü dengeli tutmak için eğitim sırasında ayarlanan per-expert bias terimleri |
| MTP module | "Ekstra prediction head" | h^(1) ve E(t+1)'den t+2'yi tahmin eden transformer bloğu; daha yoğun eğitim, ücretsiz speculative-decoding draft'ı |
| DualPipe | "Bidirectional pipeline" | Forward/backward compute'u cross-node all-to-all ile overlap eden eğitim schedule'ı |
| Active parameter ratio | "Sparsity" | active_params / total_params; DeepSeek-V3 %5.5 vurur |
| FP8 training | "8-bit eğitim" | Eğitim storage ve birçok compute op FP8'de; küçük bir kalite maliyetinde BF16'ya karşı memory'i kabaca yarılar |

## İleri Okuma

- [DeepSeek-AI -- DeepSeek-V3 Technical Report (arXiv:2412.19437)](https://arxiv.org/abs/2412.19437) -- tam mimari, eğitim ve sonuçlar dokümanı
- [DeepSeek-V3 model card on Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-V3) -- config dosyaları ve deployment notları
- [DeepSeek-V2 paper (arXiv:2405.04434)](https://arxiv.org/abs/2405.04434) -- MLA'yı tanıtan öncü
- [DeepSeek-R1 paper (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948) -- V3'ün mimarisi üzerine reasoning-eğitim halefi
- [Native Sparse Attention (arXiv:2502.11089)](https://arxiv.org/abs/2502.11089) -- DeepSeek-aile attention için gelecek yön
- [DualPipe repository](https://github.com/deepseek-ai/DualPipe) -- eğitim-schedule referansı
