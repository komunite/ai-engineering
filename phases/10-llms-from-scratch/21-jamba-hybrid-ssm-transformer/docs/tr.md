# Jamba -- Hibrit SSM-Transformer

> State space modeller (SSM'ler) ve transformer'lar farklı şeyler ister. Transformer'lar attention üzerinden kuadratik maliyetle kalite satın alır. SSM'ler bir recurrence üzerinden lineer-zamanlı çıkarım ve sabit memory satın alır ama kalitede geride kalır. AI21'in Jamba'sı (Mart 2024) ve Jamba 1.5'i (Ağustos 2024) onları aynı modele koyar: her 7 Mamba katmanı için 1 Transformer katmanı, her diğer blokta MoE ve tek bir 80GB GPU'ya sığan 256k context window. Mamba-3 (ICLR 2026) complex-valued state space'ler ve MIMO projeksiyonlarla SSM tarafını sıkar. Bu ders her iki mimariyi uçtan uca okur ve hibrit reçetenin saf-SSM ve saf-Transformer uzun-context girişimleri yapamamışken üç yıllık scaling'i neden hayatta kaldığını açıklar.

**Tür:** Öğrenim
**Diller:** Python (stdlib, layer-mix hesaplayıcı)
**Ön koşullar:** Faz 10 · 14 (açık-model mimarileri), Faz 10 · 17 (native sparse attention)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Jamba bloğundaki üç ilkel'i — Transformer katmanları, Mamba katmanları, MoE — ve 1:7:even interleaving reçetesini açıkla.
- Bir SSM'nin recurrence'inin yüksek seviyede nasıl göründüğünü ve sabit-memory çıkarımını neden sağladığını ifade et.
- 256k context'te bir Jamba modelinin KV cache footprint'ini hesapla ve saf-Transformer modelinin ihtiyaç duyacağı ile karşılaştır.
- Üç Mamba-3 inovasyonunu (exponential-trapezoidal discretization, complex-valued state update, MIMO) ve her birinin hedeflediği problemi adlandır.

## Sorun

Attention sequence uzunluğunda kuadratiktir. State space modeller lineerdir. O fark birikir: 256k token'da, bir Transformer attention map'i head başına 65B giriş; bir SSM'nin recurrent state'i sequence uzunluğundan bağımsız sabit boyuttur.

Saf-SSM modeller (Mamba, Mamba-2) küçük ölçeklerde Transformer perplexity'i ile eşleşir ama state-tracking görevlerinde geride kalır ve bazı in-context retrieval kategorilerinde başarısız olur. Sezgi: SSM'ler history'i sabit bir state'e sıkıştırır ve history uzun olduğunda bilgi sızar. Attention her şeyi tam olarak hatırlar ama kuadratik maliyet öder.

Bariz düzeltme: ikisini de kullan. Tam recall'un önemli olduğu yere Transformer katmanları koy. Başka yerlerde SSM katmanları kullan. Oranı ayarla. Jamba bu hibrit reçeteyi ölçekte yayınlayan ilk production-seviyesi modeldir (52B toplam, 12B aktif, 256k context, tek 80GB GPU). Jamba 1.5 aileyi 398B toplam / 94B aktife uzatır. Mamba-3 (ICLR 2026) hibritlerin etrafında yeniden inşa edilebileceği şu anki-en-iyi saf-SSM baseline'dır.

Bu ders üç makaleyi de okur ve "doğru oranı seç" için zihinsel model üretir.

## Kavram

### Bir Sayfada Bir SSM

Bir state space modeli `x_1, ..., x_N` sequence'ini sabit boyutlu bir state `h` üzerinden işler:

```
h_t = A h_{t-1} + B x_t
y_t = C h_t
```

Her adımda state lineer dynamics `A` üzerinden evrilir, `B x_t` input'unu alır ve `C h_t` output'u yayar. `A, B, C` öğrenilebilir. Kritik özelliği not et: `y_t`'yi hesaplamak sadece `h_{t-1}` ve `x_t`'e ihtiyaç duyar, daha önceki herhangi bir `x`'a değil. Memory sabit. Çıkarım token başına O(1).

Modelleme kalitesi için hile `A`'nın yapısıdır. S4 (Gu 2021) eğitim sırasında uzun bir konvolüsyon olarak verimli değerlendirilebilen son derece yapılandırılmış bir matris kullandı. Mamba (Gu, Dao 2023) sabit `A, B, C`'i veri-bağımlı olanlarla değiştirdi ("selective" kısım). Mamba-2 (2024) yapıyı daha da basitleştirdi. Mamba-3 (2026) spesifik yerlerde karmaşıklığı yeniden ekler.

Anahtar özellik: bir decoder LLM için, bir SSM katmanı büyüyen bir KV cache yerine sabit-boyutlu per-katman state'le bir attention katmanı için drop-in bir yedektir.

### Jamba Bloğu

Bir Jamba bloğu katmanları iki sayıya göre interleave eder:

- `l`: attention-Mamba oranı. Jamba `l = 8` kullanır, her 7 Mamba katmanı için 1 Transformer katmanı (7 Mamba + 1 Attention = grup başına 8 katman) anlamına gelir.
- `e`: MoE frekansı. Jamba `e = 2` kullanır, her diğer katmanın MoE uyguladığı anlamına gelir.

Bir blok içindeki katman sequence'i:

```
M  M  M  M  M  M  M  A    (7 Mamba + 1 Attention)
|  M  |  M  |  M  |  M    (| MoE uygulandığını işaret eder)
```

Her Jamba bloğu 8 katman. 4 blok derinliğinde (toplam 32 katman), 28 Mamba ve 4 Attention katmanı elde edersin. Bunların 16'sı MoE kullanır.

### Neden 1:7 Oranı

AI21 ablation'lar çalıştırdı: attention-Mamba'nın hangi oranı parametre başına en iyi perplexity'i VE uzun-context eval'larında in-context recall'u verir?

- Çok fazla attention (1:1): kalite yükselir ama memory ve hız bozulur.
- Çok az attention (1:15): memory harika ama in-context retrieval başarısız olur.
- Tatlı nokta: 1:7 veya 1:8.

Sezgi: Transformer katmanları tam recall ve state tracking'i halleder. Mamba katmanları işlemenin ucuz kütlesini halleder.

### Pozisyonel Encoding

Mamba katmanları kendileri pozisyon-bilinçlidir (recurrence üzerinden). Orijinal Mamba-tabanlı hibritlerdeki attention katmanları RoPE kullanmadı — SSM katmanları pozisyon bilgisi sağladı. Jamba 1.5 daha uzun-context genelleme için attention katmanlarına RoPE ekler, empirik uzun-context değerlendirmeye dayanan post-hoc bir iyileştirme.

### Memory Bütçesi

Bir Jamba-1 şekli (32 katman: 28 Mamba + 4 Attention, hidden 4096, 32 attention head) için:

- KV cache (sadece attention katmanları): 256k BF16'da `2 * 4 * 32 * 128 * 256k * 2 = 8.4 GB`. Sadece 4 attention katmanı katkıda bulunur.
- SSM state: prefix token başına `28 * hidden * state_size`, ama bu katman başına sabit boyutludur, sequence uzunluğuyla ölçeklenmez. Tipik Mamba state feature başına 16, hidden 4096: toplam `28 * 4096 * 16 * 2 = 3.7 MB`.

32 katmanlı saf Transformer ile karşılaştır, aynı hidden, 32 head'de tam MHA: 256k BF16'da `2 * 32 * 32 * 128 * 256k * 2 = 128 GB`. KV cache'te 8x azalma. Çoğu 2024 modelinin kullandığı GQA(8) baseline'a karşı bile (`2 * 32 * 8 * 128 * 256k * 2 = 32 GB`), Jamba'nın 16 GB'taki 1:7 hibridi hala 2x küçüktür.

AI21'in "tek bir 80GB GPU'da 256k context" ile kastettiği budur. Tam-MHA saf Transformer'ın KV cache'i sığmazdı; GQA baseline bile ağırlıklar ve activation'lar için yer bırakmaz; Jamba'nınki yapar.

### Mamba-3: 2026'da Saf-SSM Baseline

Mamba-3 (ICLR 2026, arXiv:2603.15569) saf-SSM tarafında üç inovasyon tanıtır:

1. **Exponential-trapezoidal discretization.** Mamba-2'deki Euler-method discretization'ı daha expressive bir recurrence ile değiştirir. Konvolüsyon-benzeri operasyon `x_t` üzerinde dış konvolüsyon olarak değil, çekirdek recurrence içinde state-input üzerinde uygulanır.

2. **Complex-valued state update.** Önceki Mamba'lar state matrisini complex'ten (S4) real diagonal'a (Mamba) scaled identity'ye (Mamba-2) indirgemişti. Mamba-3 complex değerleri yeniden ekler — state üzerinde data-bağımlı bir rotary embedding'e eşdeğer. Bu önceki real-valued basitleştirmelerin maliyetli olduğu state-tracking yeteneklerini geri yükler.

3. **Multi-input multi-output (MIMO) projections.** Per-feature scalar projeksiyonlar yerine, matris-değerli projeksiyonlar kullan. Decode latency'sini artırmadan modelleme gücünü ve çıkarım-zamanı donanım kullanımını iyileştirir.

1.5B parametrede, Mamba-3 ortalama downstream accuracy'i Gated DeltaNet üzerinde 0.6 puan iyileştirir; MIMO varyantı toplam 1.8-puan kazanç için 1.2 daha ekler. Aynı state boyutunda, Mamba-3 yarı state ile Mamba-2 ile eşleşir.

Mamba-3 henüz ölçekte production hibridinde yayınlanmıyor — ama sonraki Jamba-sınıfı modelin SSM tarafı için bariz aday.

### Hibrit İçin Ne Zaman Uzanmalı

Hibritler kazanır:

- Context saf Transformer KV cache'inin acı verici hale geldiği kadar uzun (64k+).
- Görevler kısa-mesafe yapıyı (SSM için iyi) uzun-mesafe recall'la (Transformer ister) karıştırır.
- Transformer KV cache'inin tek başına sığmayacağı tek-GPU memory bütçelerinde deploy etmek istiyorsun.

Hibritler kaybeder:

- Context kısa (16k altı). SSM overhead'i israftır; saf Transformer iyi.
- Görevler her-yerden-her-yere attention gerektirir (derin reasoning, çok-dokümanlı çapraz-referans). Hibritte attention katmanlarının seyrekliği zarar verir.
- Trilyon-parametre frontier modellerine ölçekleniyorsun. Saf-Transformer + MLA + MoE (DeepSeek-V3 tarzı) şu anda yetenek yarışını kazanıyor.

### Rekabetçi Manzara

| Model | Aile | Ölçek | Benzersiz iddia |
|-------|--------|------|-------------|
| Mamba-2 | saf SSM | 3B | lineer zaman, sabit memory |
| Jamba | hibrit | 52B/12B | 80GB'ta 256k |
| Jamba 1.5 Large | hibrit | 398B/94B | enterprise-seviyesi uzun-context |
| Mamba-3 | saf SSM | 1.5B (makale) | state-tracking restored |
| DeepSeek-V3 | saf Transformer + MoE | 671B/37B | frontier yetenek |

2026 manzarası: saf-Transformer MoE frontier'da baskın, ama hibritler 256k-plus context niş'ine sahip. Mamba-3'ün state-tracking kazançları sonraki nesilde hibrit oranlarını daha düşüğe itebilir (daha fazla SSM, daha az attention).

## Kullan

`code/main.py` hibrit mimariler için bir memory hesaplayıcıdır. Bir SSM-Transformer oranı ve hidden-size / katman-sayısı config verildiğinde, şunları hesaplar:

- Hedef context'te KV cache.
- SSM state memory.
- Bir model şekilleri aralığı için context N'de toplam memory.

Hesaplayıcı destekler:

- Saf-Transformer baseline (KV cache N ile büyür).
- Jamba-tarzı 1:7 hibrit.
- Saf-SSM (hiç KV cache yok).

Sayılar yayınlanmış şekiller için Jamba-1 ve Jamba-1.5 makalelerinden doğrudan ve hipotetik varyantlar için ekstrapole edilmiş.

Gerçek bir deployment için entegrasyon değerlendirmeleri:

- Çoğu production inference server (vLLM, SGLang) Jamba ve Mamba'yı destekler. Spesifik versiyonu kontrol et.
- 256k context'te, Jamba'nın memory avantajı eşzamanlı-istek throughput'unda kendini gösterir. Aynı VRAM'de Transformer sequence'lerinden daha fazla Jamba sequence sığdırırsın.
- Bağımsız bir model olarak Mamba-3 henüz production'da yayınlanmıyor — 1.5B'de araştırma önizlemesi.

## Yayınla

Bu ders `outputs/skill-hybrid-picker.md` üretir. Bir iş yükü spesifikasyonu (context uzunluğu profili, görev karışımı, memory bütçesi) verildiğinde, memory ve kalite tradeoff'ları hakkında açık akıl yürütmeyle saf bir Transformer, Jamba-tarzı bir hibrit ve saf bir SSM arasında önerir.

## Alıştırmalar

1. 32 katmanlı saf Transformer (hidden 4096, 32 head) ve aynı şekilde bir Jamba-1 hibridi için 256k context'te KV cache hesaplamak için `code/main.py`'ı çalıştır. AI21 makalesinin iddia ettiği ~8x memory azalmasını doğrula.

2. Hesaplayıcıyı bir 1:3 hibrit (4 Mamba : 1 Attention) ve bir 1:15 hibrit (14 Mamba : 1 Attention) modellemek için değiştir. KV cache vs oran çiz. Hangi oranda KV cache SSM state memory'sine eşit olur?

3. Jamba makalesinin Bölüm 3'ünü oku (arXiv:2403.19887). Mamba-2 daha hızlı olmasına rağmen AI21'in neden Mamba-1 kullandığını açıkla. İpucu: hibrit ablation bölümü bunu dokümante eder.

4. Jamba 1.5 Large'da (398B toplam, 94B aktif) MoE-her-diğer-katman'ın parametre overhead'ini hesapla. Aktif oranı DeepSeek-V3 (37B/671B) ile karşılaştır ve Jamba'nın mimarisinin neden aktif oranı daha yükseğe ittiğini açıkla.

5. Mamba-3 makalesinin Bölüm 3'ünü oku (arXiv:2603.15569). Bir complex-valued state update'in neden data-bağımlı bir rotary embedding'e eşdeğer olduğunu üç cümlede açıkla. Cevabı Faz 7 · Ders 04'ün RoPE türetmesine bağla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| State space model (SSM) | "Sabit state'li recurrence" | Öğrenilmiş `h_t = A h_{t-1} + B x_t` recurrence'lı bir katman; token başına sabit memory |
| Selective SSM | "Mamba'nın hilesi" | Modeli lineer zamanda gating-benzeri selectivity veren data-bağımlı A, B, C parametreleri |
| Attention-to-Mamba ratio | "Kaç attention katmanı" | Jamba'da, `l = 8` her 7 Mamba katmanı için 1 attention katmanı demek |
| Jamba block | "8-katmanlı grup" | Bir attention + yedi Mamba + alternatif pozisyonlarda MoE |
| SSM state | "Hidden buffer" | Mamba katmanları için KV cache'i değiştiren katman başına sabit-boyutlu state |
| 256k context | "Jamba'nın amiral sayısı" | Jamba-1'in tek bir 80GB GPU'ya sığdırdığı sequence uzunluğu; o boyutta saf Transformer yapamaz |
| Mamba-3 | "2026 saf SSM" | Complex state + MIMO ile şu anki-en-iyi saf-SSM mimarisi; hibritlerin etrafında yeniden inşa ettiği baseline |
| MIMO | "Multi-input multi-output" | Scalar per-feature yerine matris-değerli projeksiyonlar kullanan Mamba-3 inovasyonu |
| Exponential-trapezoidal discretization | "Mamba-3'ün recurrence'i" | Mamba-2'nin Euler-method discretization'ını kapsayan daha expressive recurrence |
| Hybrid architecture | "Attention ve SSM'i karıştır" | Transformer ve SSM katmanlarını interleave eden herhangi bir model; Jamba production archetype'ı |

## İleri Okuma

- [Lieber et al. -- Jamba: A Hybrid Transformer-Mamba Language Model (arXiv:2403.19887)](https://arxiv.org/abs/2403.19887) -- orijinal Jamba makalesi, oran ablation'ları, 256k context iddiası
- [AI21 -- Jamba 1.5: Hybrid Transformer-Mamba at Scale (arXiv:2408.12570)](https://arxiv.org/abs/2408.12570) -- ölçeklenmiş aile, 398B/94B ve 12B/52B public release'ler
- [Gu, Dao -- Mamba: Linear-Time Sequence Modeling with Selective State Spaces (arXiv:2312.00752)](https://arxiv.org/abs/2312.00752) -- Jamba'nın üzerine inşa ettiği selective SSM makalesi
- [Dao, Gu -- Mamba-2 (arXiv:2405.21060)](https://arxiv.org/abs/2405.21060) -- basitleştirilmiş structured-state-space halefi
- [Lahoti et al. -- Mamba-3 (arXiv:2603.15569, ICLR 2026)](https://arxiv.org/abs/2603.15569) -- complex-valued state, MIMO, 2026 saf-SSM frontier'ı
- [Gu et al. -- Efficiently Modeling Long Sequences with Structured State Spaces (arXiv:2111.00396)](https://arxiv.org/abs/2111.00396) -- LLM'ler için SSM şecere başlangıç noktası olan S4 makalesi
