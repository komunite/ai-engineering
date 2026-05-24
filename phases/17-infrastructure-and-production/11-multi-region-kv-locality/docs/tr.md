# Çoklu-Bölge LLM Serving ve KV Cache Yerelliği

> Round-robin load balancing cache'li LLM çıkarımı için aktif olarak zararlı. Prefix'ini tutan node'a düşmeyen bir istek tam prefill maliyetini öder — uzun bir prompt'ta P50'de kabaca 800 ms, cache hit ile ~80 ms'ye karşı. 2026'da üretim deseni KV-cache event'lerini tüketen ve prefix-hash eşleşmesinde yönlendiren cache-aware bir router (Rust'ta vLLM Router, llm-d router). Yakın araştırma (GORGO) cross-region network gecikmesini routing hedefinde açık bir terim yapar. Ticari "cross-region inference" teklifleri (Bedrock cross-region inference, GKE multi-cluster gateway'ler) çıkarımı opak olarak ele alır — TTFT'yi değil erişilebilirliği halleder. JPMorgan ve Mayo Clinic Kasım 2024'te us-east-1 failover'ını ~22 dakikada çalıştırdı. DR gerçeği: LLM DR başarısızlıklarının %32'si takımların ağırlıkları yedeklediği ama tokenizer dosyalarını ya da quantization config'lerini unuttuğu için.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak prefix-cache-aware router simülatörü)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving), Faz 17 · 06 (SGLang RadixAttention)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Round-robin load balancing'in cache'li çıkarımı neden bozduğunu açıkla ve TTFT cezasını sayısallaştır.
- Cache-aware bir router'ı diyagramla: input'lar (KV-cache event'leri), algoritma (prefix-hash eşleşmesi), tie-breaker (GPU utilization).
- LLM'ler için %32 DR başarısızlık sürücüsünü (eksik tokenizer dosyaları / quantization config'leri) adlandır ve üç-dosyalı bir DR checklist'i ifade et.
- Ticari cross-region tekliflerini (Bedrock CRI, GKE Multi-Cluster Gateway) KV-aware routing'den ayır.

## Sorun

Servisin us-east-1, us-west-2 ve eu-west-1'de çalışıyor. Önüne round-robin'li bir ALB koyuyorsun. Üretimde prefix cache hit oranı %8'e düşüyor. TTFT P50 üç katına çıkıyor. vLLM log'ların her isteğin tam prefill maliyetini ödediğini gösteriyor.

Round-robin stateless servisler için optimal. LLM çıkarımı tasarım gereği stateful — KV cache modelin gördüğü her şeyi encode eder. Kör yönlendirme yanlış cache'e yönlendirmektir.

Ayrı olarak, takımının bir DR planı var. Model ağırlıklarını S3'e cross-region yedekliyorsun. Bir bölgesel kesinti vuruyor; failover deniyorsun; replica başlamayı reddediyor. tokenizer.json'ı, quantization config'i ve RoPE scaling config'inin sync etmediğin ayrı bir bucket'ta olduğunu unuttun.

Çoklu-bölge LLM serving bir cache sorunu, bir routing sorunu ve bir DR-hijyen sorunu — load-balancer sorunu değil.

## Kavram

### Cache-aware routing

İstek bir prompt'la gelir. Router prefix'i hash'ler (örneğin ilk 512 token); her replica'ya "bu prefix'i cache'lemiş misin?" diye sorar. Replica'lar block tahsis edip tahliye ettikçe bir pub/sub kanalında KV-cache event'leri yayınlar. Router eşleşmeli replica'yı seçer, kimsede yoksa GPU-util-tabanlı tie-breaker'a düşer.

**vLLM Router** (Rust, 2026 production-stack): `kv.cache.block_added` event'lerine abone olur, prefix-hash → replica indeksi tutar, O(1) lookup'la yönlendirir. Eşleşme olmadığında en-az-queue-derinliğine düşer.

**llm-d router**: aynı desen, Kubernetes-native. Event'leri ControlPlane API üzerinden yayınlar.

**SGLang RadixAttention** (Faz 17 · 06) intra-replica eşdeğeri. Cross-replica routing kesin olarak upstream.

### Sayılar

2K-token prompt'ta TTFT P50, Llama 3.3 70B FP8, H100:
- Cache hit (aynı replica, prefix resident): ~80 ms.
- Cache miss (soğuk prefill): ~800 ms.

10x fark. Router'ın replica'lar arasında prefix cache'in %60-80'ine ulaşıyorsa, N-replica kapasitesinde tek-replica performansına yaklaşırsın. %10'a ulaşıyorsa, naif ölçeklendirmeye yaklaşırsın.

### Cross-region'ın yeni bir kısıtı var — network gecikmesi

Bölgeler arası RTT:
- us-east-1 ↔ us-west-2: ~65 ms.
- us-east-1 ↔ eu-west-1: ~75 ms.
- us-east-1 ↔ ap-southeast-1: ~220 ms.

Routing bir isteği us-east-1'den ap-southeast-1'deki sıcak bir prefix'e götürürse, tasarruf edilen prefill (800 → 80 ms) 440 ms gidiş-dönüş tarafından gölgede kalır. GORGO (2026 araştırması) bunu açık yapar — prefill'i tek başına değil, `prefill_time + network_latency`'yi birlikte minimize et. Cevap genelde, prefill'in domine ettiği büyük multi-MB prefix'ler dışında routing'i bölgesel tutmak.

### Ticari "cross-region inference" burada yardım etmiyor

AWS Bedrock cross-region inference kapasite baskısı sırasında istekleri otomatik olarak diğer bölgelere yönlendirir. Erişilebilirliği optimize eder, TTFT'yi değil ve çıkarımı opak olarak ele alır. GKE Multi-Cluster Gateway aynı — servis-seviyesi failover, KV cache farkındalığı yok.

Bunları kullanırken bile uygulama-katmanı cache-aware router'a hâlâ ihtiyacın var. Onlar "us-east-1 yanıyor" durumunu halleder. Cache-aware routing TTFT durumunu halleder.

### DR hijyeni — %32 eksik-dosya sorunu

Yaygın olarak alıntılanan 2026 istatistiği: LLM DR başarısızlıklarının %32'si takımların ağırlıkları yedeklediği ama şunları unuttuğu için olur:

- `tokenizer.json` ya da `tokenizer.model`
- Quantization config'leri (`quantize_config.json`, AWQ scale'leri, GPTQ zero-point'leri)
- Modele-özgü config'ler (RoPE scaling, attention mask'leri, chat template'leri)
- Motor config'i (`vllm_config.yaml`, sampling varsayılanları, LoRA adapter manifest'leri)

Çözüm üç-dosyalı minimum DR manifest'i:

1. HF model repo'su altındaki tüm dosyalar (ağırlıklar + config'ler + tokenizer).
2. Motor-spesifik serving config'i.
3. Deployment manifest'i (K8s YAML, Dockerfile, bağımlılık lock'u).

Artı: üç ayda bir DR tatbikatı çalıştır. JPMorgan'ın us-east-1 tatbikatı Kasım 2024'te 22 dakikada toparlandı yalnızca playbook prova edilmişti diye.

### Veri ikametgâhı ortogonal

AB müşteri PHI'si AB'den çıkamaz. Cache-aware router'ın bir Paris-orijinli isteği prefix eşleşmesi için us-east-1'e gönderiyorsa, TTFT kazancına bakılmaksızın GDPR'yi ihlal ettin. Cache için optimize etmeden önce router'ları ikametgâh sınırına göre partition'la.

### Hatırlaman gereken sayılar

- Cache hit vs miss TTFT farkı: ~10x (2K prompt'ta 80 ms vs 800 ms).
- ABD-AB bölgeler arası RTT: ~75 ms.
- DR başarısızlığı: %32 tokenizer/quant config'lerini kaçırır.
- JPMorgan us-east-1 failover Kasım 2024: 22 dakika (30 dakikalık SLA).

## Kullan

`code/main.py` çoklu-bölge bir iş yükünde üç routing stratejisi (round-robin, cache-aware bölgesel, cache-aware global) simüle eder. Cache hit oranı, TTFT P50/P99 ve cross-region faturayı raporlar.

## Yayınla

Bu ders `outputs/skill-multi-region-router.md` üretir. Bölgeler, ikametgâh kısıtları ve SLA verildiğinde, bir routing planı tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. 75 ms RTT verildiğinde, cross-region routing local-only routing'i hangi prompt uzunluğunda yener?
2. Cache hit oranın %70'ten %12'ye düşüyor. Üç olası sebep ve her birini doğrulayacak gözlenebilirleri teşhis et.
3. 5 LoRA adapter'lı vLLM'de servis edilen bir 70B AWQ-quantize edilmiş model için bir DR manifest'i tasarla. Her dosyayı ve config'i listele.
4. Sıkı TTFT SLO'lu bir fintech için Bedrock cross-region inference'ın "yeterli" olup olmadığını savun. Spesifik davranışlara atıfla.
5. Bir Paris-orijinli istek us-east-1'deki bir prefix'le eşleşiyor. Onu yönlendirir misin? Politikayı yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Cache-aware routing | "akıllı LB" | KV-cache-tutan replica'ya prefix-hash eşleşmesinde yönlendir |
| KV-cache event'leri | "cache pub-sub" | Replica'lar block ekle/tahliye yayınlar; router indeksler |
| Prefix hash | "cache anahtarı" | İlk N token'ın router lookup'ı olarak kullanılan hash'i |
| GORGO | "cross-region routing araştırması" | arXiv 2602.11688; network gecikmesi açık terim olarak |
| Cross-region inference | "Bedrock CRI" | AWS ürünü; erişilebilirlik failover'ı, TTFT farkındalığı değil |
| DR manifest | "yedek listesi" | Geri yüklemek için gereken her dosya — yalnız ağırlıklar değil |
| Veri ikametgâhı | "GDPR sınırı" | Hangi bölgenin kullanıcı verisini gördüğü üzerine yasal kısıt |
| RTT | "round-trip time" | Network gecikmesi; ABD-AB 75 ms, ABD-APAC 220 ms |
| LLM-aware LB | "cache-hit LB" | Ürün kategorisi olarak cache-aware router |

## İleri Okuma

- [BentoML — Multi-cloud and cross-region inference](https://bentoml.com/llm/infrastructure-and-operations/multi-cloud-and-cross-region-inference)
- [arXiv — GORGO (2602.11688)](https://arxiv.org/html/2602.11688v1) — network gecikme terimli cross-region KV-cache yeniden kullanımı.
- [TianPan — Multi-Region LLM Serving Cache Locality](https://tianpan.co/blog/2026-04-17-multi-region-llm-serving-data-residency-routing)
- [AWS Bedrock Cross-Region Inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html) — erişilebilirlik failover dokümantasyonu.
- [vLLM Production Stack Router](https://github.com/vllm-project/production-stack) — cache-aware router kaynağı.
