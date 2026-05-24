# Serverless LLM'ler için Cold Start Mitigation

> 20 GB'lık bir model image'ı soğuktan servise gitmek için 5-10 dakika (7B) ila 20+ dakika (70B) sürer. Gerçek bir serverless dünyada bu bir warm-up değil — bir outage. Mitigasyonlar beş katmanda çalışır: önceden-hazırlanmış node image'ları (AWS'de Bottlerocket, dual-volume mimarisi), model streaming (NVIDIA Run:ai Model Streamer, vLLM'de yerel), GPU memory snapshot'ları (Modal checkpoint'ları, 10x'e kadar daha hızlı restart), warm pool'lar (`min_workers=1`), tiered loading (ServerlessLLM'in NVMe→DRAM→HBM pipeline'ı, 10-200x gecikme azaltma) ve KV cache (GB) yerine input token'ları (KB) taşıyan live migration. Modal 2-4s cold start'ları taban olarak yayınlıyor; Baseten varsayılan 5-10s, pre-warming ile alt-saniye. Bu ders sana beş katmanı ölçmeyi, bütçelemeyi ve yığmayı öğretir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak cold-start yolu simülatörü)
**Ön koşullar:** Faz 17 · 02 (Çıkarım Platformu Ekonomisi), Faz 17 · 03 (GPU Autoscaling)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Cold-start mitigation'ın beş katmanını say ve her katmanda bir araç ya da desen adlandır.
- 70B model için toplam cold-start zamanını (node sağlama) + (ağırlık indirme) + (HBM'e ağırlık yükleme) + (motor init) toplamı olarak hesapla.
- Live migration'ın neden KV cache'i (GB) değil input token'larını (KB) transfer ettiğini ve cezanın ne olduğunu (yeniden hesaplama) açıkla.
- Warm-pool tradeoff'unu (boşta GPU için öde ya da cold-start kuyruğunu kabul et) ve `min_workers > 0`'ın zorunlu olduğu SLA eşiğini adlandır.

## Sorun

Serverless LLM endpoint'in gece sıfıra ölçeklenir. Sabah 8'de trafik sıçrar. İlk istek beklerken:

1. Karpenter bir GPU node sağlar: 45-60s.
2. Container 30 GB'lık bir image'ı ağırlıklarla çeker: 120-300s.
3. Motor ağırlıkları HBM'e yükler: model boyutu ve depolama hızına bağlı 45-120s.
4. vLLM ya da TRT-LLM CUDA graph'ları, KV cache pool'u, tokenizer'ı başlatır: 10-30s.

Toplam: bir token geri gelmeden önce 220-510s (kabaca 3-8 dakika). SLA'in 2s. Bir warm-pool (`min_workers=1`) yayınlıyorsun ve sorun yok oluyor gibi — ama şimdi 24x7 boşta bir GPU için ödüyorsun. Servisin her biri bir warm replica'lı 5 ürünü varsa, bu tek bir kullanıcı çağırmasa bile 5 × 24 × 30 = aylık 3.600 GPU-saat.

Cold-start mitigation, her zaman-açık'ın gecikmesine yaklaşırken serverless ekonomisini nasıl koruyacağındır.

## Kavram

### Katman 1 — önceden-hazırlanmış node image'ları (Bottlerocket)

AWS'de, Bottlerocket'in dual-volume mimarisi OS'u veriden ayırır. Container image'ın önceden-çekilmiş olarak data volume'unu snapshot al; `EC2NodeClass`'ında snapshot ID'yi referansla. Yeni node'lar ağırlıklar zaten yerel NVMe'de boot eder — adım 2 ve adım 3'ün bir kısmı yok olur. Karpenter ile yerel olarak çalışır. Tipik tasarruflar: büyük modeller için cold start başına 2-4 dakika.

GCP'de eşdeğer: önceden-pişirilmiş container katmanlı custom VM image'ları. Azure'da: aynı desende yönetilen disk snapshot'ları.

### Katman 2 — model streaming (Run:ai Model Streamer)

İlk isteğe yanıt vermeden önce tam dosyayı yüklemek yerine, ağırlıkları katman katman GPU belleğine stream et ve ilk transformer block resident olur olmaz işlemeye başla. NVIDIA Run:ai Model Streamer 2026 vLLM'de yerel olarak gelir. S3, GCS ve yerel NVMe ile çalışır. I/O'yu compute setup'la üst üste binerek büyük modeller için ağırlık-yükleme zamanını kabaca yarıya keser.

### Katman 3 — GPU memory snapshot'ları (Modal)

Modal ilk yüklemeden sonra GPU durumunun (ağırlıklar, CUDA graph'lar, KV cache bölgesi) bir checkpoint'ini alır. Sonraki restart'lar doğrudan HBM'e deserialize eder — yeniden başlatmaktan 10x daha hızlı. "2 saniyede sıcak bir GPU boot et"e en yakın şey bu. Tradeoff: snapshot'lar GPU-topolojisi başına, dolayısıyla Karpenter seni farklı bir SKU'ya göç ettirirse, yeniden checkpoint yaparsın.

### Katman 4 — warm pool'lar (min_workers=1)

En basit mitigasyon: bir replica'yı her zaman hazır tut. Maliyet 24x7 bir GPU'nun saatlik oranı. Aritmetik küçük modellerde zalim (30s cold start'ı önlemek için saatte $0.85-$1.50 ödersin) ve büyük olanlarda nazik (5-dakikalık cold start'ı önlemek için saatte $4 öde). Warm pool'ların zorunlu olduğu SLA eşiği: tipik olarak 70B+ modelde TTFT P99 < 60s.

### Katman 5 — tiered loading (ServerlessLLM)

ServerlessLLM depolamayı bir hiyerarşi olarak ele alır: NVMe (hızlı ama büyük), DRAM (orta ama tier'lı), HBM (küçük ama anlık). Ağırlıklar DRAM'a önceden-yüklenir; HBM'e talep-üzerine yükle. Makale naif disk-to-HBM'e karşı cold load'larda 10-200x gecikme azaltma raporlar. Üretim benimsemesi erken ama vLLM ile entegrasyonlar var.

### Katman 6 — live migration (bonus desen)

Bir node kullanılamaz hale geldiğinde (spot eviction, node drain), geleneksel desen başka bir replica cold-start etmek ve istek queue'sunu drain etmektir. Live migration input token'larını (kilobyte) modelin yüklü olduğu bir hedefe taşır ve KV cache'i hedefte yeniden hesaplar. Yeniden hesaplama GB KV cache'i network üzerinden transfer etmekten daha ucuz. Disaggregated deployment'lara uygulanabilir.

### Warm-pool matematiği

P99 TTFT SLA'i 2s olan bir servis için, soru "warm pool evet/hayır" değil, "kaç warm replica ve hangi yollar bunları alır" sorusu.

- Yüksek-değerli etkileşimli yollar (canlı sohbet, voice agent): `min_workers=1-2`.
- Background batch yolları (gecelik sınıflandırma): scale-to-zero kabul edilir, 5-10 dakikalık cold start tolere edilebilir.
- Premium tier: dedicated kapasiteli tenant başına `min_workers`.

### Optimize etmeden önce ölç

Taze bir node'da 70B model için cold-start anatomisi (örneklendirici):

| Faz | Süre | Mitigasyon |
|-------|------|-----------|
| Node sağlama | 50s | Bottlerocket + önceden-hazırlanmış image, warm pool |
| Image pull | 180s | Önceden-hazırlanmış data volume (elimine et) |
| HBM'e ağırlıklar | 75s | Model streamer (yarıya); GPU snapshot (elimine et) |
| Motor init | 20s | Kalıcı CUDA graph cache'i |
| İlk forward | 3s | Minimum içsel gecikme |
| **Toplam soğuk** | **328s** | |
| **Mitigasyonlarla toplam** | **~15s** | 22x azaltma |

### Hatırlaman gereken sayılar

- Modal cold start: 2-4s (GPU snapshot'larla).
- Baseten varsayılan cold start: 5-10s; pre-warming ile alt-saniye.
- Ham 70B cold start: 3-8 dakika.
- Run:ai Model Streamer: ~2x ağırlık-yükleme speedup.
- ServerlessLLM tiered loading: 10-200x gecikme azaltma (makale sayıları).

## Kullan

`code/main.py` her mitigasyonla ve onsuz bir cold-start yolunu modeller. Toplam cold-start zamanını, warm-pool maliyetini ve üstünde warm pool'un kendini ödediği break-even istek oranını raporlar.

## Yayınla

Bu ders `outputs/skill-cold-start-planner.md` üretir. SLA, model boyutu ve trafik şekli verildiğinde, hangi mitigasyonları yığacağını seçer.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. SLO'da extra istek düşüşleri yoluyla cold-start vergisini ödemekten warm bir replica'nın daha ucuz olduğu break-even istek oranını hesapla.
2. P99 TTFT SLA'i 3s olan bir 13B modeli deploy ediyorsun. Bunu başaran minimum mitigasyon yığınını (en az katman) seç.
3. Bottlerocket önceden-hazırlama image pull'u elimine eder ama ağırlıklar hâlâ snapshot'tan HBM'e yüklenir. Snapshot-destekli NVMe 7 GB/s'de okursa 70B model için wall-clock'u hesapla.
4. Serverless sağlayıcın GPU snapshot'ları (Modal) sunuyor ve takımın "snapshot'lar PII sızdırır" diye reddediyor. İki tarafı da savun — gerçekçi risk ne ve mitigasyon ne (ephemeral snapshot'lar, encryption, namespace izolasyonu)?
5. Tier'lı bir warm-pool politikası tasarla: ücretli kullanıcılar, deneme kullanıcıları ve batch iş yükleri için kaç warm replica? Matematiği göster.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Cold start | "büyük duraklama" | Taze bir replica'da istekten ilk token'a süre |
| Warm pool | "her zaman-açık minimum" | En az bir replica'yı hazır tutmak için `min_workers >= 1` |
| Önceden-hazırlanmış image | "pişmiş AMI" | Container ağırlıkları önceden-resident node image'ı |
| Bottlerocket | "AWS node OS" | Dual-volume snapshot destekli AWS container-optimize edilmiş OS |
| Model streamer | "streaming yükleme" | Ağırlık I/O'sunu compute setup'la üst üste bindir |
| GPU snapshot | "HBM'e checkpoint" | Yükleme-sonrası GPU durumunu serialize et; restart'ta deserialize et |
| Tiered loading | "NVMe + DRAM + HBM" | Depolama tier'ları hiyerarşisi; talep üzerine yükle |
| Live migration | "token'ları taşı" | Input (KB) transfer et, hedefte KV yeniden hesapla |
| `min_workers` | "warm replica'lar" | Serverless minimum keep-alive sayısı |
| Scale-to-zero | "tam serverless" | Boştayken maliyet yok; tam cold-start vergisini kabul et |

## İleri Okuma

- [Modal — Cold start performance](https://modal.com/docs/guide/cold-start) — Modal'ın yayınlanmış benchmark'ları ve checkpoint mimarisi.
- [AWS Bottlerocket](https://github.com/bottlerocket-os/bottlerocket) — önceden-hazırlanmış data volume snapshot deseni.
- [NVIDIA Run:ai Model Streamer](https://github.com/run-ai/runai-model-streamer) — ağırlık yüklemesini compute setup'la üst üste bindir.
- [Baseten — Cold-start mitigation](https://www.baseten.co/blog/cold-start-mitigation/) — pre-warming playbook'u.
- [ServerlessLLM paper (USENIX OSDI'24)](https://www.usenix.org/conference/osdi24/presentation/fu) — tiered loading tasarımı.
- [NVIDIA — Disaggregated LLM Inference on Kubernetes](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/) — disaggregated deployment'lar için live migration.
