# LLM Üretimi için Chaos Engineering

> 2026'da LLM'ler için chaos engineering kendi disiplini. Üretimde deney çalıştırmadan önce ön koşullar: tanımlı SLI/SLO, trace+metric+log observability, otomatik rollback, runbook'lar, on-call. Mimari dört düzlemli: control (deney scheduler'ı), target (servisler, altyapı, veri store'ları), safety (guard'lar + abort + trafik filtreleri), observability (metrikler + trace'ler + log'lar), feedback (SLO ayarlamalarına). Guardrail'ler zorunlu: burn-rate alert'leri günlük error-budget burn'ü beklenenin 2x'inden büyükse deneyleri duraklatır; suppression window'ları + trace-ID korelasyonu alert gürültüsünü dedupe eder. Kadans: haftalık küçük canary + SLO inceleme; aylık game day + postmortem; üç aylık cross-team dayanıklılık denetimi + bağımlılık haritalama. LLM-spesifik deneyler: bellek aşırı yükü, network başarısızlıkları, sağlayıcı kesintileri, malformed prompt'lar, KV cache eviction storm'ları. Tooling: Harness Chaos Engineering (LLM-türetilmiş öneriler, blast-radius downscaling, MCP tool entegrasyonu); LitmusChaos (CNCF); Chaos Mesh (CNCF Kubernetes-native).

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak chaos deneyi çalıştırıcı)
**Ön koşullar:** Faz 17 · 23 (AI için SRE), Faz 17 · 13 (Observability)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Beş chaos engineering ön koşulunu (SLI/SLO, observability, rollback, runbook'lar, on-call) adlandır ve herhangi birinin atlanmasının uygulamayı neden bozduğunu açıkla.
- Dört düzlemi (control, target, safety, observability) ve SLO'ya feedback loop'unu diyagramla.
- Beş LLM-spesifik deneyi (bellek aşırı yükü, network fail, sağlayıcı kesintisi, malformed prompt, KV eviction storm) say.
- Verilen stack için bir araç — Harness, LitmusChaos, Chaos Mesh — seç.

## Sorun

Geleneksel stack'lerde chaos testing yerleşik. LLM stack'leri yeni başarısızlık modları ekler. Zehirli karakterli 4K-token'lık bir prompt tokenizer'ı 12 saniye durdurur. Upstream bir sağlayıcı 429 verir; gateway'in retry yapar; servisin retry-amplifiye eşzamanlılıkta OOM olur. Burst yük altında bir KV cache eviction storm'u compute'u doyuran yeniden-prefill cascade'leri tetikler.

Bunların hiçbiri unit test'lerde görünmez. Chaos engineering bunları kullanıcılardan önce nasıl keşfettiğindir.

## Kavram

### Ön koşullar

Üretimde chaos çalıştırma:

1. **SLI/SLO** — tanımlı service-level indicator'lar ve objective'ler.
2. **Observability** — trace'ler, metrikler, log'lar, dashboard'lara bağlı.
3. **Otomatik rollback** — Faz 17 · 20 policy-flag rollback.
4. **Runbook'lar** — yapılandırılmış, Faz 17 · 23.
5. **On-call** — yanıt verecek biri.

Herhangi birinin eksik olması chaos'un gerçek olaya dönüşmesi demek.

### Dört düzlem + feedback

**Control plane** — deney scheduler'ı (Litmus workflow, Chaos Mesh schedule, Harness UI).

**Target plane** — servisler, pod'lar, node'lar, load balancer'lar, veri store'ları.

**Safety plane** — kill switch, suppression window'ları, blast-radius limitleri, error-budget gate'leri.

**Observability plane** — chaos-tetiklenmiş ve doğal başarısızlıkları ayırt etmek için normal metrikler + trace-ID korelasyonu.

**Feedback loop** — bulgular SLO ayarlamasına, runbook güncellemelerine, kod düzeltmelerine geri besler.

### Guardrail'ler zorunlu

- **Burn-rate alert'i**: günlük error-budget burn beklenenin 2x'ini aşarsa deneyi duraklat.
- **Suppression window'ları**: deney sırasında blast radius'taki deney-dışı alert'leri sustur.
- **Trace-ID korelasyonu**: tüm deney-tetiklenmiş hatalar bir tag taşır, böylece on-call dedupe edebilir.

### Beş LLM-spesifik deney

1. **Bellek aşırı yükü** — yüksek eşzamanlılıkla long-context istekler göndererek KV cache preemption storm'u zorla. Gözle: servis zarafetle düşürüyor mu yoksa çöküyor mu?

2. **Network başarısızlığı** — çıkarım gateway'i ile sağlayıcı arasındaki bağlantıyı kes. Gözle: fallback SLA içinde devreye giriyor mu? (Faz 17 · 19)

3. **Sağlayıcı kesintisi simülasyonu** — OpenAI'dan %100 429. Gözle: routing Anthropic'e failover ediyor mu? (Faz 17 · 16, 19)

4. **Malformed prompt** — tokenizer-durduran payload enjekte et (örn. derin iç içe unicode, dev UTF-8 codepoint). Gözle: tek bir istek bir worker'ı kilitliyor mu?

5. **KV eviction storm** — vLLM block bütçesini doyurarak eviction zorla. Gözle: LMCache toparlıyor mu yoksa servis bozuluyor mu?

### Kadans

- **Haftalık** — staging'de küçük canary deneyler, belki prod'da %5.
- **Aylık** — spesifik bir senaryoda zamanlanmış game day; cross-team katılım; postmortem.
- **Üç aylık** — cross-team dayanıklılık denetimi; bağımlılık haritası güncellemesi.

### Tooling

- **Harness Chaos Engineering** — ticari; AI-türetilmiş deney önerileri; blast-radius downscaling; MCP tool entegrasyonu.
- **LitmusChaos** — CNCF mezun; Kubernetes workflow-tabanlı.
- **Chaos Mesh** — CNCF sandbox; Kubernetes-native CRD stili.
- **Gremlin** — ticari; geniş destek.
- **AWS FIS** / **Azure Chaos Studio** — yönetilen cloud teklifleri.

### Küçük başlamak

İlk deney: sabit trafik altında bir decode replica'sını pod-kill et. Yeniden yönlendirmeyi ve toparlanmayı gözle. Bu işe yarar ve güvenli görünürse, network chaos'a mezun ol.

İlk LLM-spesifik deney: 5 dakikalığına bir sağlayıcı 429 enjekte et. Fallback'i gözle. Çoğu takım fallback'lerinin tamamen test edilmediğini keşfeder.

### Hatırlaman gereken sayılar

- Dört düzlem: control, target, safety, observability.
- Burn-rate pause: beklenen günlük bütçe burn'ünün 2x'i.
- Kadans: haftalık canary, aylık game day, üç aylık denetim.
- Beş LLM deneyi: bellek, network, sağlayıcı, malformed prompt, KV storm.

## Kullan

`code/main.py` safety plane gate'leriyle üç chaos deneyi simüle eder. Hangi deneylerin burn-rate abort'unu tripleyeceğini raporlar.

## Yayınla

Bu ders `outputs/skill-chaos-plan.md` üretir. Stack ve olgunluk verildiğinde, ilk üç deneyi ve tooling'i seçer.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Hangi deney burn-rate gate'ini tripler ve neden?
2. vLLM-tabanlı bir RAG servisi için ilk beş chaos deneyini tasarla. Başarı kriterlerini dahil et.
3. Burn-rate alert'in bir deneyi duraklattı. Kök sebebi nasıl belirlersin — chaos ya da doğal?
4. Chaos'un üretimde mi yoksa yalnız staging'de mi çalışması gerektiğini savun. Üretim ne zaman doğru cevap?
5. Genel network-chaos'un yeniden üretemeyeceği üç LLM-spesifik başarısızlık modu adlandır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| SLI / SLO | "servis hedefleri" | Indicator + objective; gerekli ön koşul |
| Blast radius | "kapsam" | Deneyden etkilenen servis / kullanıcı kümesi |
| Burn-rate alert'i | "bütçe gate'i" | Error-budget burn oranı beklenenin 2x'ini aştığında ateşlenir |
| Game day | "aylık tatbikat" | Zamanlanmış cross-team chaos egzersizi |
| LitmusChaos | "CNCF workflow" | Mezun CNCF Kubernetes chaos aracı |
| Chaos Mesh | "CNCF CRD" | CNCF sandbox Kubernetes-native chaos |
| Harness CE | "ticari AI-yardımlı" | AI önerileriyle Harness chaos |
| Malformed prompt | "tokenizer bombası" | Tokenization'ı durduran input |
| KV eviction storm | "preemption cascade'i" | Yeniden-prefill tetikleyen toplu eviction |

## İleri Okuma

- [DevSecOps School — Chaos Engineering 2026 Guide](https://devsecopsschool.com/blog/chaos-engineering/)
- [Ankush Sharma — Observability for LLMs (book)](https://www.amazon.com/Observability-Large-Language-Models-Engineering-ebook/dp/B0DJSR65TR)
- [LitmusChaos (CNCF)](https://litmuschaos.io/)
- [Chaos Mesh (CNCF)](https://chaos-mesh.org/)
- [Harness Chaos Engineering](https://www.harness.io/products/chaos-engineering)
- [AWS FIS](https://aws.amazon.com/fis/)
