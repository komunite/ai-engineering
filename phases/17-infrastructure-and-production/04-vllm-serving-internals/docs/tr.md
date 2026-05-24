# vLLM Serving İçleri: PagedAttention, Continuous Batching, Chunked Prefill

> vLLM'in 2026'daki hakimiyeti tek bir hile değil, üç bileşik varsayılan üzerine kurulu. PagedAttention her zaman açık. Continuous batching decode iterasyonları arasında aktif batch'e yeni istekler enjekte eder. Chunked prefill uzun prompt'ları dilimler ki decode token'ları asla aç kalmasın. Üçünü de aç ve tek H100 SXM5'te bir Llama 3.3 70B FP8, 128 eşzamanlıda 2.200-2.400 tok/s'e ulaşır — bu vLLM'in kendi varsayılanından kabaca %25 daha yüksek ve naif bir PyTorch loop'unun 3-4 katı. Bu ders scheduler'ı ve attention kernel'ı diyagramlayabileceğin bir seviyede okur ve `code/main.py`'da prefill ve decode'u vLLM'in yaptığı şekilde schedule eden bir oyuncak continuous batcher ile biter.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak continuous batching scheduler)
**Ön koşullar:** Faz 17 · 01 (Model Serving), Faz 11 (LLM Engineering)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- PagedAttention'ı bir KV cache allocator'ı olarak açıkla: block'lar, block table'lar ve üretim yükünde fragmentasyonun neden %4'ün altında kaldığı.
- Continuous batching'i iterasyon seviyesinde diyagramla: bitmiş sequence'ler batch'ten nasıl çıkar ve yenileri drenaj olmadan nasıl katılır.
- Chunked prefill'i bir cümlede tarif et ve hangi gecikme metriğini koruduğunu adlandır (ipucu: ortalama throughput değil, TTFT kuyruğu).
- Her optimizasyonu aynı anda etkinleştiren takımları ısıran 2026 vLLM v0.18.0 sürprizini adlandır.

## Sorun

Naif bir PyTorch serve loop'u her seferinde bir istek çalıştırır: tokenize, prefill, EOS'a kadar decode, döndür. Tek kullanıcıda bu işe yarar. Yüzde, sabırlı insanlardan oluşan bir queue olur. Bariz çözüm — static batching — her isteği pencerede en uzun prompt'a kadar pad'ler, her decode'u en uzun beklenen output'a kadar pad'ler ve tüm batch'i en yavaş sequence'e takılır. Asla kullanmadığın padding için ödersin ve hızlı istekler yavaşları bekler.

vLLM aynı anda üç sorunu çözer. PagedAttention klasik contiguous tahsisin yaptığı gibi KV cache fragmentasyonunun GPU belleğinin %60-80'ini yemesini durdurur. Continuous batching her decode iterasyonu arasında isteklerin batch'e katılıp çıkmasına izin verir, böylece batch her zaman gerçek işle dolu olur. Chunked prefill 32k-token'lık bir prompt'u decode ile araya giren ~512-token'lık dilimlere böler, böylece uzun bir prompt GPU'daki her decode token'ını dondurmaz.

2026 üretim varsayılanı üçü de açık. Her birinin ne yaptığını anlaman gerek çünkü başarısızlık modları modelin değil, scheduler'ın üstünde.

## Kavram

### Sanal bellek sistemi olarak PagedAttention

Bir KV cache sequence başına `num_layers × 2 × num_heads × head_dim × seq_len × bytes_per_element` boyutundadır. Llama 3.3 70B'de 8192 token için bu BF16'da sequence başına kabaca 1.25 GB demektir. Her istek için önceden 8192 slot rezerve edersen ama ortalama istek yalnızca 1500 token kullanırsa, rezerve ettiğin HBM'in kabaca %82'sini boşa harcarsın. Klasik batching bu israfı öder.

PagedAttention fikri OS sanal belleğinden ödünç alır. KV cache sequence başına contiguous değildir. Sabit-boyutlu block'larda (varsayılan 16 token) tahsis edilir. Her sequence'in logical token pozisyonlarını physical block ID'lerine eşleyen bir block table'ı vardır. Bir sequence tahsis edilen block'larının ötesine büyüdüğünde, bir block daha eklenir. Bittiğinde, block'ları havuza döner.

Fragmentasyon %60-80'den (klasik) %4'ün altına (PagedAttention) düşer. PagedAttention'ı bir flag ile etkinleştirmezsin — vLLM'in sunduğu tek allocator. Düğme `--gpu-memory-utilization` (varsayılan 0.9), vLLM'e ağırlıkları ve aktivasyonları yükledikten sonra KV block'lar için ne kadar HBM rezerve edeceğini söyler.

### İterasyon seviyesinde continuous batching

Eski "dynamic batching" bir pencere (örneğin 10 ms) bekleyerek batch'i doldurur, sonra her sequence bitene kadar prefill + decode + decode + decode çalıştırırdı. Hızlı sequence'ler erken çıkar ve GPU yavaşları bitirirken boşta otururdu.

Continuous batching her decode adımı arasında çalışır. Çalışan sequence kümesine `RUNNING` listesi diyelim. Her iterasyonda:

1. `RUNNING`'de EOS'a ya da max_tokens'a yeni ulaşan herhangi bir sequence kaldırılır.
2. Scheduler bekleyen queue'ya bakar. Boş KV block varsa, yeni sequence'leri (prefill ya da resumed) kabul eder.
3. Forward pass `RUNNING`'de şimdi her ne varsa onun üzerinde çalışır, sequence başına bir yeni token yayınlar.

Batch boyutu sabit bir sayıya asla pad'lenmez. Output'larında farklı pozisyonlardaki sequence'ler tek bir fused forward'ı paylaşır. 2026 vLLM'inde buna `V1 scheduler` denir. Anahtar invariant: scheduler istek başına değil, decode iterasyonu başına bir kez çalışır.

### Chunked prefill TTFT kuyruğunu korur

Prefill compute-bağlı. Llama 3.3 70B üzerinde 32k-token'lık bir prompt tek H100'de saf prefill olarak ~800 ms alır. Prefill çalışırken, batch'teki diğer her sequence için decode token'ları bekler. Bir serving loop'unda, bir uzun prompt'un first-token gecikmesi (TTFT) düzinelerce diğer kullanıcı için inter-token gecikme (ITL) sıçraması olur.

Chunked prefill prefill'i sabit-boyutlu chunk'lara (varsayılan 512 token) böler ve her chunk'ı bir birim olarak schedule eder. Chunk'lar arasında scheduler decode sequence'lerini bir token ilerletebilir. Küçük bir mutlak prefill gecikme isabetini (chunk başına birkaç ms) çok daha düşük decode-time jitter ile takas edersin. Karma yük altında P99 ITL yayınlanmış benchmark'larda ~50 ms'den ~15 ms'ye düşer.

### Üç varsayılan birbirini etkiler

Her üç özellik birbirini varsayar. PagedAttention scheduler'a karşılığında takas edebileceği ince-granüllü bir KV kaynağı verir. Continuous batching o ince-granüllü kaynağa ihtiyaç duyar ki yeni bir sequence kabul etmek global bir reshuffle zorlamasın. Chunked prefill scheduler'ın aynı `RUNNING` listesinde verdiği bir karardır — ayrı bir sistem değil, bir scheduler politikası daha.

Her flag'i bilmen gerekmez. Scheduler'ın neyi optimize ettiğini bilmen gerek: chunked prefill dilimlemesine tabi, KV-block bütçesi altında goodput.

### 2026 v0.18.0 sürprizi

vLLM v0.18.0'da `--enable-chunked-prefill`'ı draft-model speculative decoding (`--speculative-model`) ile birleştiremezsin. Belgelenmiş istisna V1 scheduler'da N-gram GPU speculative decoding. Release notes'ları okumadan her flag'i çeviren takımlar bir soft regression değil, başlangıçta run-time hatası alır. Speculative kazancın chunked prefill'i etkinleştirmeye değdiyse, seçimi yeniden gözden geçir — 2026'da doğru cevap genelde compile etmeyen draft model artı chunked prefill değil, chunked prefill olmadan EAGLE-3.

### Hatırlaman gereken sayılar

- Llama 3.3 70B FP8, H100 SXM5, 128 eşzamanlı, üçü de açık: 2.200-2.400 tok/s.
- Aynı model, varsayılan vLLM (chunked prefill yok): ~1.800 tok/s.
- Aynı model, naif PyTorch forward loop'u: ~600 tok/s.
- Üretim yükünde PagedAttention altında KV fragmentasyon israfı: <%4.
- Karma yükte P99 ITL: chunked prefill ile ~15 ms, onsuz ~50 ms.

### Scheduler neye benzer

```
while True:
    finished = [s for s in RUNNING if s.is_done()]
    for s in finished: release_blocks(s); RUNNING.remove(s)

    while WAITING and have_free_blocks_for(WAITING[0]):
        s = WAITING.pop(0)
        allocate_initial_blocks(s)
        RUNNING.append(s)

    # tek bir batch içinde prefill chunk'larını + decode'u schedule et
    batch = []
    for s in RUNNING:
        if s.in_prefill:
            batch.append(next_prefill_chunk(s))   # örn. 512 token
        else:
            batch.append(decode_one_token(s))     # 1 token

    run_forward(batch)                            # tek fused GPU çağrısı
```

`code/main.py` stdlib Python'da sahte token sayıları ve sahte forward gecikmesiyle tam olarak bu loop'tur. Çalıştırmak chunked prefill'in uzun bir prefill sırasında decode sequence'lerini nasıl ayakta tuttuğunu gösterir.

## Kullan

`code/main.py` toggle-edilebilir özelliklerle vLLM-tarzı bir scheduler simüle eder. Çalıştır ve şunu gör:

- `NAIVE` modu: tek seferde bir istek, batching yok.
- `STATIC` modu: pad ve bekle, klasik batching.
- `CONTINUOUS` modu: iterasyon-seviyesi kabul ve serbest bırakma.
- `CONTINUOUS + CHUNKED` modu: decode ile araya giren prefill dilimleri.

Çıktı toplam throughput'u (virtual saniye başına token), TTFT ortalamasını ve P99 ITL'i gösterir. `CONTINUOUS + CHUNKED` satırı karma trafikte baskın olmalı.

## Yayınla

Bu ders `outputs/skill-vllm-scheduler-reader.md` üretir. Bir serving config'i verildiğinde (batch boyutu, KV bellek utilization'ı, chunked prefill boyutu, speculative config'i), üç varsayılandan hangisinin bottleneck olduğunu ve neyin ayarlanacağını adlandıran bir scheduler teşhisi üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Karma kısa ve uzun istekli bir iş yükünde `STATIC`'i `CONTINUOUS` ile karşılaştır. Throughput farkı nereden geliyor — prefill verimliliği, decode verimliliği ya da kuyruk gecikmesi?
2. Oyuncak scheduler'ı `--max-num-batched-tokens` eklemek için modifiye et. Llama 3.3 70B FP8 çalıştıran bir H100 için doğru değer nedir? (İpucu: ham HBM değil, KV block boyutunun ve boş block sayısının bir fonksiyonu.)
3. vLLM v0.18.0 release notes'larını yeniden oku. Hangi flag kombinasyonları karşılıklı dışlayıcı? Listele.
4. (a) 8192 max'ta contiguous per-request tahsisi ve (b) 16-token block'larla PagedAttention altında ortalama 1.500 output token, std 600 token olan 1.000 isteklik bir trace için KV cache fragmentasyon israfını hesapla.
5. Bir paragrafta chunked prefill'in neden izole P99 ITL'e yardım ettiğini ama throughput'a yardım etmediğini açıkla. Pratikte throughput kazancı nereden geliyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| PagedAttention | "KV hilesi" | KV cache için sabit-boyutlu block allocator'ı; fragmentasyon <%4 |
| Block table | "page table" | Logical token pozisyonundan physical KV block'a sequence başına eşleme |
| Continuous batching | "dynamic batching, ama doğru" | Her decode iterasyonunda alınan kabul/bırakma kararları |
| Chunked prefill | "prefill bölme" | Uzun prefill'i decode ile araya giren 512-token dilimlere böl |
| TTFT | "ilk token zamanı" | Prefill + queue + network; uzun prompt'larda prefill ile domine olur |
| ITL | "inter-token latency" | Ardışık decode token'ları arasındaki zaman; batch boyutuyla domine olur |
| Goodput | "SLO'yu karşılayan throughput" | Her isteğin hâlâ TTFT ve ITL hedeflerini tutturduğu token/saniye |
| V1 scheduler | "yeni scheduler" | vLLM'in 2026 scheduler'ı; N-gram spec decode chunked-prefill-uyumlu yol |
| `--gpu-memory-utilization` | "bellek düğmesi" | Ağırlıklar ve aktivasyonlardan sonra KV block'lar için rezerve edilen HBM fraksiyonu |

## İleri Okuma

- [vLLM documentation — Speculative Decoding](https://docs.vllm.ai/en/latest/features/spec_decode/) — chunked-prefill ve speculative-decoding uyumluluğu üzerine resmi kaynak.
- [vLLM Release Notes (NVIDIA)](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/index.html) — 2026 release ritmi ve sürüme-özgü davranış.
- [vLLM Blog — PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html) — allocator'ı nasıl düşüneceğini hâlâ tanımlayan orijinal yazı.
- [PagedAttention paper (arXiv:2309.06180)](https://arxiv.org/abs/2309.06180) — fragmentasyon analizi ve scheduler tasarımı.
- [Aleksa Gordic — Inside vLLM](https://www.aleksagordic.com/blog/vllm) — flame graph'lı detaylı V1 scheduler turu.
