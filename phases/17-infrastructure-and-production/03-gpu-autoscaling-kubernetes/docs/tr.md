# Kubernetes'te GPU Autoscaling — Karpenter, KAI Scheduler, Gang Scheduling

> Üç katman, bir değil. Karpenter node'ları dinamik olarak sağlar (bir dakikanın altında, Cluster Autoscaler'dan %40 daha hızlı). KAI Scheduler gang scheduling, topology awareness ve hierarchical queue'ları halleder — yedi node'un bir eksik GPU için bekleyip yandığı 7-of-8 kısmi tahsis tuzağını önler. Uygulama-seviyesi autoscaler'lar (NVIDIA Dynamo Planner, llm-d Workload Variant Autoscaler) CPU/DCGM duty cycle değil, çıkarıma-özel sinyallere — queue derinliği, KV cache kullanımı — göre ölçeklenir. Klasik HPA tuzağı: `DCGM_FI_DEV_GPU_UTIL` bir duty-cycle ölçümüdür: %100 ya 10 ya da 100 istek olabilir. vLLM KV cache belleğini önceden tahsis eder, yani bellek scale-down'ı asla tetiklemez. Bu ders sana üç katmanı bestelemeyi ve çalışan GPU job'larını çıkarım ortasında sonlandıran varsayılan Karpenter `WhenEmptyOrUnderutilized` politikasından kaçınmayı öğretir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak queue-depth autoscaler simülatörü)
**Ön koşullar:** Faz 17 · 02 (Çıkarım Platformu Ekonomisi), Faz 17 · 04 (vLLM Serving İçleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Üç autoscaling katmanını (node sağlama, gang scheduling, uygulama-seviyesi) diyagramla ve her katmanda kullanılan aracı adlandır.
- vLLM için `DCGM_FI_DEV_GPU_UTIL`'in neden yanlış HPA sinyali olduğunu açıkla ve iki yedek adlandır (queue derinliği, KV cache kullanımı).
- Gang scheduling'i ve KAI Scheduler'ın önlediği kısmi-tahsis başarısızlık modunu (8 GPU'dan 7'si boşta) tarif et.
- Çalışan GPU job'larını sonlandıran Karpenter consolidation politikasını (`WhenEmptyOrUnderutilized`) adlandır ve 2026 güvenli alternatifini söyle.

## Sorun

Takımın Kubernetes üzerinde bir LLM-serving servisi yayınlıyor. HPA'yı `DCGM_FI_DEV_GPU_UTIL` sinyaliyle kuruyorsun. Servis iş saatlerinde %100 utilization'da sabitleniyor. HPA hiçbir zaman scale-up yapmıyor — zaten dolu olduğunu düşünüyor. Manuel olarak bir replica ekliyorsun; TTFT düşüyor. HPA hâlâ ölçeklenmiyor. Sinyal sana yalan söylüyor.

Ayrıca, node'lar için Cluster Autoscaler kullanıyorsun. Gece 2'de 1M-token'lık bir prompt geliyor; cluster bir node sağlamak için 3 dakika harcıyor ve istek timeout oluyor.

Bir kez daha ayrı olarak, 2 node üzerinde 8 GPU gerektiren bir 70B model deploy ediyorsun. Cluster'da 7 GPU boş ve 1 tanesi 3 node'a dağılmış. Cluster Autoscaler eksik 1 GPU için bir node sağlıyor. Kubernetes son GPU'yu ayağa kaldırırken yedi node 4 dakika para yakarak bekliyor.

Üç katman, üç farklı başarısızlık modu. 2026'da GPU-aware autoscaling "HPA'yı aç" değil. Node sağlamayı, gang scheduling'i ve uygulama-sinyalli autoscaling'i bestelemek.

## Kavram

### Katman 1 — node sağlama (Karpenter)

Karpenter pending pod'ları izler ve node'ları ~45-60 saniyede sağlar (Cluster Autoscaler GPU node'ları için tipik olarak 90-120 saniye alır). `NodePool` kısıtına göre instance tiplerini dinamik olarak seçer — pod'un 8 H100 gerektiriyorsa ve cluster'da eşleşen node yoksa, Karpenter mevcut bir grubu ölçeklemek yerine doğrudan bir tane sağlar.

**Consolidation tuzağı**: Karpenter'ın varsayılan `consolidationPolicy: WhenEmptyOrUnderutilized`'ı GPU pool'lar için tehlikelidir. Pod'ları daha ucuz right-sized bir instance'a göç ettirmek için çalışan bir GPU node'unu sonlandırır. Çıkarım iş yükleri için bu, çalışan istekleri tahliye etmek ve 70B'lik bir modeli yeni node'a yeniden yüklemek demektir. Kayıp, dakikalarca kapasite artı istek başarısızlıkları.

GPU pool'lar için güvenli ayar:

```yaml
disruption:
  consolidationPolicy: WhenEmpty
  consolidateAfter: 1h
```

Karpenter'ın gerçekten boş node'ları bir saat sonra konsolide etmesine izin verir ama çalışan bir job'u asla tahliye etmez.

### Katman 2 — gang scheduling (KAI Scheduler)

KAI Scheduler (önceden "Karp" projesi, sonra yeniden adlandırıldı) varsayılan kube-scheduler'ın yapmadığını halleder:

**Gang scheduling** — hepsi-ya da-hiçbiri scheduling. 8 GPU gerektiren dağıtık bir çıkarım pod'u ya 8'i de birlikte başlar ya da hiçbiri başlamaz. Bu olmadan, kısmi-tahsis tuzağına düşersin: 8 pod'dan 7'si başlar, süresiz bekler, para yakar.

**Topology awareness** — hangi GPU'ların NVLink paylaştığını, hangilerinin aynı rack'te oturduğunu, aralarında hangilerinin InfiniBand'i olduğunu bil. Pod'ları buna göre yerleştir. DeepSeek-V3 67B tensor-parallel bir iş yükü tek bir NVLink domain'inde kalmalı; KAI Scheduler buna saygı duyar.

**Hierarchical queue'lar** — birden fazla takım aynı GPU havuzu için öncelik ve kotayla yarışır. Takım A'nın üretim sıkışıklığı yalnızca öncelik kuralları izin verirse Takım B'nin eğitim job'u tarafından preempt edilir.

KAI ikincil bir scheduler olarak kube-scheduler ile birlikte deploy edilir; iş yüklerini onu kullanması için anote edersin. Ray ve vLLM production-stack ikisi de entegre olur.

### Katman 3 — uygulama-seviyesi sinyaller

**HPA tuzağı**: `DCGM_FI_DEV_GPU_UTIL` bir duty-cycle metriğidir — her örnekleme aralığında GPU'nun iş yapıp yapmadığını ölçer. %100 utilization ya 10 ya da 100 eşzamanlı istek demek olabilir; GPU her iki halde de meşguldü. Duty cycle üzerinden ölçeklemek körlemesine ölçeklemektir.

Daha kötüsü, vLLM ve benzer motorlar KV cache belleğini önceden tahsis eder (`--gpu-memory-utilization`'a kadar). Bellek kullanımı tek istek bile olsa %90 yakınında kalır. Bellek-tabanlı HPA asla scale-down yapmaz.

**2026 yedek sinyalleri**:

- Queue derinliği (prefill için bekleyen istek sayısı).
- KV cache kullanımı (block'ların hangi fraksiyonunun aktif sequence'lere tahsis edildiği).
- Replica başına P99 TTFT (SLA sinyalin).
- Goodput (saniyede tüm SLO'ları karşılayan istek).

NVIDIA Dynamo Planner ve llm-d Workload Variant Autoscaler bu sinyalleri tüketir ve replica'ları ölçekler. LLM serving için HPA'yı tamamen yerine geçirirler.

### Hangisi ne zaman

| Ölçek kararı | Araç |
|----------------|------|
| Node ekle/çıkar | Karpenter |
| Multi-GPU job schedule et | KAI Scheduler |
| Replica ekle/çıkar | Dynamo Planner / llm-d WVA (ya da queue derinliğinde custom HPA) |
| GPU tipi seç | Karpenter NodePool |
| Düşük öncelikli preempt et | KAI Scheduler queue'ları |

### Disaggregated prefill/decode her şeyi karmaşıklaştırır

Disaggregated prefill/decode çalıştırırsan (Faz 17 · 17), farklı scaling tetikleyicileriyle iki pod sınıfın olur: prefill pod'ları queue derinliğinde ölçeklenir, decode pod'ları KV cache basıncında ölçeklenir. llm-d bunları rol başına HPA'lı ayrı `Service`'ler olarak expose eder. İkisinin önüne tek bir HPA koymaya çalışma.

### Cold start burada da önemli

Cold-start mitigation'ı (Faz 17 · 10) node sağlama süresinin kullanıcıya görünür hale geldiği yerdir. Karpenter'ın 45-60 saniyelik warm-up'ı artı 20GB model yükleme artı motor init demek, sıfırdan bir istek 2-5 dakika sürer demektir. SLO-kritik yollar için sıcak bir havuz (`min_workers=1`) tut, ya da uygulama katmanında Modal-tarzı checkpointing kullan.

### Hatırlaman gereken sayılar

- Karpenter node sağlama: ~45-60s vs Cluster Autoscaler ~90-120s (GPU node'lar).
- KAI Scheduler kısmi-tahsis israfını önler — 8'de 7 tuzağı.
- HPA sinyali olarak `DCGM_FI_DEV_GPU_UTIL`: bozuk; queue derinliği ya da KV utilization kullan.
- Karpenter `WhenEmptyOrUnderutilized`: çalışan GPU job'larını sonlandırır. Çıkarım için `WhenEmpty + consolidateAfter: 1h` kullan.

## Kullan

`code/main.py` bursty bir GPU iş yükünde üç-katmanlı bir autoscaler simüle eder. Naif HPA'yı (duty cycle), queue-depth HPA'yı ve KAI-gang-scheduled ölçeklemeyi karşılaştırır. Karşılanmamış istekleri, boşta-GPU dakikalarını ve bir kompozit skoru raporlar.

## Yayınla

Bu ders `outputs/skill-gpu-autoscaler-plan.md` üretir. Cluster topolojisi, iş yükü şekli ve SLO verildiğinde, üç-katmanlı bir autoscaling planı tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Bursty bir iş yükünde naif duty-cycle HPA queue-depth HPA'nın yakaladığı kaç isteği düşürür? Fark nereden geliyor?
2. H100 SXM5'te Llama 3.3 70B FP8 servis eden bir cluster için bir Karpenter NodePool tasarla. `capacity-type`, `disruption.consolidationPolicy`, `consolidateAfter` ve GPU-olmayan iş yüklerini bu node'lardan uzak tutan bir taint belirt.
3. Takımın "GPU'lar mevcut ama pod schedule olmuyor" diye deployment'ların Pending'de takıldığını rapor ediyor. Teşhis et — bu Karpenter, kube-scheduler ya da KAI Scheduler mı? Hangi metrikler doğrular?
4. Disaggregated prefill pod'larını autoscale etmek için bir sinyal seç ve decode pod'ları için farklı bir sinyal. İkisini de gerekçelendir.
5. Günde 60 istek-düşüren olay (P99 TTFT > 10s) ortalamasıyla çalışan 24x7 bir üretim servisinde `WhenEmptyOrUnderutilized` consolidation tuzağının maliyetini hesapla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Karpenter | "node sağlayıcı" | Kubernetes node autoscaler'ı; alt-dakika sağlama |
| Cluster Autoscaler | "eski scaler" | Kubernetes node autoscaler'ın öncülü; daha yavaş, grup-tabanlı |
| KAI Scheduler | "GPU scheduler" | Gang + topology + queue'lar için ikincil scheduler |
| Gang scheduling | "hepsi ya da hiçbiri" | N pod'u atomik olarak schedule et ya da hepsini ertele |
| Topology awareness | "rack-aware" | NVLink/IB/rack yerleşimine göre pod yerleştir |
| `DCGM_FI_DEV_GPU_UTIL` | "GPU utilization" | Duty-cycle metriği; LLM'ler için scaling sinyali DEĞİL |
| Queue derinliği | "bekleyen istekler" | Prefill-bağlı ölçekleme için doğru HPA sinyali |
| KV cache utilization | "bellek basıncı" | Decode-bağlı ölçekleme için doğru HPA sinyali |
| Consolidation | "Karpenter consolidation" | Daha ucuz instance tipine node sonlandırma |
| `WhenEmpty + 1h` | "güvenli consolidation" | Çalışan GPU job'larını tahliye etmeyen politika |

## İleri Okuma

- [KAI Scheduler GitHub](https://github.com/kai-scheduler/KAI-Scheduler) — tasarım dokümanları ve config örnekleri.
- [Karpenter Disruption Controls](https://karpenter.sh/docs/concepts/disruption/) — consolidation politika semantiği ve GPU-güvenli varsayılanlar.
- [NVIDIA — Disaggregated LLM Inference on Kubernetes](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/) — Dynamo Planner scaling sinyalleri.
- [Ray docs — KAI Scheduler for RayClusters](https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/kai-scheduler.html) — Ray entegrasyon deseni.
- [AWS EKS Compute and Autoscaling Best Practices](https://docs.aws.amazon.com/eks/latest/best-practices/aiml-compute.html) — yönetilen-Kubernetes-spesifik rehber.
- [llm-d GitHub](https://github.com/llm-d/llm-d) — Workload Variant Autoscaler tasarımı.
