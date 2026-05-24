# LMCache KV Offloading'li vLLM Production Stack

> vLLM'in production-stack'i referans Kubernetes deployment'ı — router, motorlar ve observability birbirine bağlı. LMCache, KV cache'i GPU belleğinin dışına çıkaran ve sorgular ile motorlar arasında yeniden kullanılır kılan KV-offloading katmanı (CPU DRAM, sonra disk/Ceph). vLLM 0.11.0 KV Offloading Connector'ı (Ocak 2026) bunu Connector API (v0.9.0+) üzerinden asenkron ve takılabilir yapar. Offload gecikmesi kullanıcıya görünmez. LMCache paylaşılan prefix'ler olmadan bile değerli — bir GPU KV slot'larını tükettiğinde, preempt edilen istekler prefill'i yeniden hesaplamak yerine CPU'dan restore edilebilir. 4 a3-highgpu-4g üzerinde 16x H100 (80GB HBM) üzerinde yayınlanmış benchmark'lar: KV cache HBM'i aştığında, hem native CPU offload hem LMCache throughput'u önemli ölçüde iyileştiriyor; düşük KV ayak izinde, tüm config'ler küçük overhead ile baseline'a eşitleniyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak KV-spill simülatörü)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 17 · 06 (SGLang/RadixAttention)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- vLLM production-stack katmanlarını diyagramla: router, motorlar, KV offload, observability.
- KV Offloading Connector API'ını (v0.9.0+) ve 0.11.0 asenkron yolunun offload gecikmesini nasıl gizlediğini açıkla.
- LMCache CPU-DRAM'ın ne zaman yardım ettiğini (KV > HBM) vs ne zaman overhead eklediğini (KV HBM'e sığacak kadar küçük) sayısallaştır.
- Deployment kısıtları verildiğinde native vLLM CPU offload ile LMCache connector arasında seç.

## Sorun

vLLM serving'in eşzamanlılık her tırmandığında preemption event'leriyle GPU'ları %100 HBM'de gösteriyor. İstekler tahliye ediliyor, yeniden queue'lanıyor ve aynı 2K-token'lık prompt'u bir dakikada dört kez yeniden-prefill ediyorsun. GPU compute redundant prefill'lere harcanıyor; goodput ham throughput'un çok altında.

Daha fazla GPU eklemek lineer maliyetler. Daha fazla HBM eklemek mümkün değil. Ama CPU DRAM ucuz — bir soket HBM'den birkaç mertebe daha kötü gecikmede ama "geçici sıcak" KV cache için iyi olan 512 GB+'a sahip.

LMCache KV cache'i CPU DRAM'a çıkarır ki preempt edilen istekler hızlı toparlansın ve motorlar arasında tekrarlanan prefix'ler her motorun yeniden-prefill etmesine gerek kalmadan cache'i paylaşsın.

## Kavram

### vLLM production-stack

`github.com/vllm-project/production-stack` referans Kubernetes deployment'ı:

- **Router** — cache-aware (Faz 17 · 11). KV event'lerini tüketir.
- **Motorlar** — vLLM worker'ları. GPU başına ya da TP/PP grubu başına bir.
- **KV cache offload** — LMCache deployment'ı ya da native connector.
- **Observability** — Prometheus scrape, Grafana dashboard'ları, OTel trace'leri.
- **Control plane** — service discovery, config, rolling update'ler.

Helm chart + operator olarak yayınlanır.

### KV Offloading Connector API (v0.9.0+)

vLLM 0.9.0 takılabilir KV cache backend'leri için bir Connector API tanıttı. Motorun block'ları connector'a offload eder; connector onları saklar (RAM, disk, object storage, LMCache). İstek bir block'a ihtiyaç duyduğunda, connector onu geri yükler.

vLLM 0.11.0 (Ocak 2026) asenkron bir offload yolu ekler — offload arka planda olabilir, böylece motor yaygın durumda buna takılmaz. End-to-end gecikme ve throughput hâlâ iş yükü şekline, KV cache hit oranına ve sistem basıncına bağlı; vLLM'in kendi notları custom-kernel offload'un düşük hit oranlarında throughput'u bozabileceğini ve async scheduling'in speculative decoding ile bilinen etkileşim sorunları olduğunu söylüyor.

### Native CPU offload vs LMCache

**Native vLLM CPU offload**: motor-yerel. KV block'larını host RAM'inde saklar. Uygulaması hızlı, sıfır network hop'u. Motorları aşmaz.

**LMCache connector**: cluster-ölçeği. Block'ları paylaşılan bir LMCache sunucusunda (CPU DRAM + Ceph/S3 tier'ı) saklar. Block'lar herhangi bir motora erişilebilir. 16x H100 benchmark'ları yayınlandı.

Tek bir motor HBM basıncı altındaysa native seç. Birden fazla motor prefix paylaşıyorsa (yaygın system prompt'lu RAG, paylaşılan şablonlu multi-tenant) LMCache seç.

### Benchmark davranışı

4 a3-highgpu-4g'ye yayılan 16x H100 (80 GB HBM) testi:

- Düşük KV ayak izi (kısa prompt'lar, düşük eşzamanlılık): tüm config'ler baseline'a eşit, LMCache ~%3-5 overhead ekler.
- Orta ayak izi: LMCache motorlar arası prefix yeniden kullanımında yardım etmeye başlar.
- KV HBM'i aşar: native CPU offload ve LMCache ikisi de throughput'u önemli ölçüde iyileştirir; cross-engine paylaşım nedeniyle LMCache daha büyük kazanç.

### LMCache ne zaman belirleyici

- System prompt'larının tenant'lar arası paylaşıldığı multi-tenant serving.
- Belge chunk'larının sorgular arası tekrarlandığı RAG.
- Aynı base'de fine-tuned varyantlar (LoRA) — base-model KV yeniden kullanımı redundant işi keser.
- Preemption-ağırlıklı iş yükleri: CPU'dan toparlanma yeniden-prefill'den daha ucuz.

### Ne zaman etkinleştirme

- Küçük HBM basıncı — faydası olmadan overhead ödersin.
- Kısa context'ler (<1K token) — transfer zamanı > yeniden-prefill.
- Tek-tenant tek-prompt iş yükü — yakalanacak yeniden kullanım yok.

### Disaggregated serving ile entegrasyon

Faz 17 · 17 disaggregated serving + LMCache bileşik: KV'ler prefill pool'undan decode pool'una transfer edilirken kullanılmazsa LMCache'e iner; sonraki sorgular LMCache'ten çeker. Faz 17 · 11 cache-aware router yerel YA DA LMCache-paylaşılan cache'i eşleşen motora yönlendirebilir.

### Hatırlaman gereken sayılar

- vLLM 0.9.0: Connector API yayınlandı.
- vLLM 0.11.0 (Oca 2026): asenkron offload yolu; end-to-end gecikme etkisi iş yüküne, KV hit oranına ve sistem basıncına bağlı (mutlak garanti değil).
- 16x H100 benchmark: KV ayak izi HBM'i aştığında LMCache yardım eder.
- Küçük HBM basıncı: faydası olmadan %3-5 overhead.

## Kullan

`code/main.py` LMCache'li ve onsuz preemption-ağırlıklı bir iş yükü simüle eder. Önlenen yeniden-prefill'leri, throughput kazancını ve break-even HBM utilization'ını raporlar.

## Yayınla

Bu ders `outputs/skill-vllm-stack-decider.md` üretir. İş yükü şekli ve vLLM deployment'ı verildiğinde, native vs LMCache vs ikisi de değil arasında karar verir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. LMCache hangi HBM utilization'ında ödemeye başlar?
2. Bir tenant saatte 200 sorgu arasında 6K-token'lık bir system prompt paylaşıyor. Tenant başına beklenen LMCache tasarrufunu hesapla.
3. LMCache sunucusu tek başarısızlık noktası. HA stratejisini tasarla (replica'lar, native'e fallback).
4. LMCache dönen disk'te Ceph'e saklar. 70B FP8'de 4K-token KV (500 MB) için, okuma zamanı vs yeniden-prefill ne?
5. vLLM 0.11.0 asenkron yolunun "bedava" olup olmadığını savun — overhead nerede saklanıyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Production-stack | "referans deployment" | vLLM'in Kubernetes Helm chart'ı + operator'ı |
| Connector API | "KV backend arayüzü" | vLLM 0.9.0+ takılabilir KV store arayüzü |
| Native CPU offload | "motor-yerel spill" | Aynı motorun host RAM'inde KV sakla |
| LMCache | "cluster KV cache'i" | CPU DRAM + disk üzerinde motorlar-arası KV cache sunucusu |
| 0.11.0 async | "blocking-olmayan offload" | Motor stream'inin arkasında gizlenmiş offload |
| Preemption | "yer açmak için tahliye" | HBM dolu olduğunda KV cache karıştırma |
| Prefix yeniden kullanım | "aynı system prompt" | Birden fazla sorgu başlangıcı paylaşır; cache hit |
| Ceph tier'ı | "disk tier'ı" | Cache hiyerarşisinde DRAM'in altında dayanıklı depolama |

## İleri Okuma

- [vLLM Blog — KV Offloading Connector (Oca 2026)](https://blog.vllm.ai/2026/01/08/kv-offloading-connector.html)
- [vLLM Production Stack GitHub](https://github.com/vllm-project/production-stack) — Helm chart + operator.
- [LMCache for Enterprise-Scale LLM Inference (arXiv:2510.09665)](https://arxiv.org/html/2510.09665v2)
- [LMCache GitHub](https://github.com/LMCache/LMCache) — Connector uygulaması.
- [vLLM 0.11.0 release notes](https://github.com/vllm-project/vllm/releases) — asenkron yol detayları.
