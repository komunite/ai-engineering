# AI için SRE — Multi-Agent Incident Response, Runbook'lar, Predictive Detection

> AI SRE altyapı verilerine (log'lar, runbook'lar, servis topolojisi) RAG üzerinden grounded LLM'ler kullanarak araştırma, dokümantasyon ve koordinasyon fazlarını otomatize eder. 2026 mimari deseni multi-agent orkestrasyon — bir supervisor tarafından koordine edilen özelleşmiş agent'lar (log'lar, metrikler, runbook'lar); AI hipotezler ve sorgular önerir, insanlar yargı kararlarını onaylar. Datadog Bits AI ve Azure SRE Agent bunu yönetilen ürünler olarak yayınlar. Runbook'lar evrim geçiriyor: NeuBird Hawkeye adversarial değerlendirme kullanır (iki model aynı olayı analiz eder; anlaşma = güven, anlaşmazlık = belirsizlik); operasyonel bellek takım değişiklikleri arasında kalıcı. Auto-remediation temkinli kalır: AI önerir, insanlar onaylar. Tamamen otonom eylem dar (pod'u restart et, spesifik deploy'u rollback et), sıkı guardrail'lerle — "kur ve unut" satan herkes abartıyor. Beliren frontier: pre-incident tahmin. MIT araştırması tarihsel log'lar + GPU sıcaklıkları + API hata desenlerinde eğitilen bir LLM'in outage'ların %89'unu 10-15 dakika erken tahmin ettiğini bildiriyor. Projeksiyon: 2026 sonuna kadar enterprise LLM'lerin %95'i otomatik failover'a sahip.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak multi-agent incident triage simülatörü)
**Ön koşullar:** Faz 17 · 13 (Observability), Faz 17 · 24 (Chaos Engineering)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Multi-agent AI SRE mimarisini diyagramla: supervisor + özelleşmiş agent'lar (log'lar, metrikler, runbook'lar) + insan onay gate'i.
- Auto-remediation'ın neden geniş (servisi yeniden mimarisi) değil dar (pod'u restart et, deploy'u geri al) olduğunu açıkla.
- Adversarial değerlendirme desenini (NeuBird Hawkeye) adlandır: iki model anlaşır = güven; anlaşmaz = eskale.
- MIT %89 erken-tespit sonucunu alıntıla ve operasyonel kısıtı söyle: aktüasyon olmadan tahminler sadece dashboard'tur.

## Sorun

Bir on-call mühendis gece 3'te page alır. "Checkout'ta yüksek hata oranı." Datadog'u, Loki'yi, üç runbook'u, deploy log'unu kontrol eder. 30 dakika sonra kök sebebin KV cache sıçramasından bir vLLM OOM olduğunu fark eder. Pod'u restart eder; hata temizlenir.

2026'da o araştırmanın ilk 20 dakikası otomatize edilebilir. Log'ları servise göre gruplama, son deploy'larla korelasyon, runbook'larla eşleştirme — hepsi RAG + tool-use. Supervised bir agent ilk-pass triage yapabilir ve insan Datadog'u açmadan önce bir hipotez sunabilir.

Tamamen otonom remediation farklı bir sorun. Pod restart: güvenli. GPU pool ölçeklendir: politika izin verirse güvenli. Servisi yeniden mimarisi: kesinlikle hayır. Disiplin dar çizgiyi çizmek.

## Kavram

### Multi-agent mimari

```
            Olay
             │
             ▼
        Supervisor
        /    |    \
       ▼     ▼     ▼
  Log agent  Metrik agent  Runbook agent
       │     │     │
       └─────┴─────┘
             │
             ▼
        Hipotez + kanıt
             │
             ▼
        İnsan onayı
             │
             ▼
        Eylem (dar küme)
```

Supervisor olayı alt-sorgulara böler. Özelleşmiş agent'ların tool erişimi var (log arama, PromQL, doc retrieval). Supervisor sentezler, hipotez + kanıtı insana sunar. İnsan onaylar ya da yönlendirir.

### Auto-remediation kapsamı

**Güvenli (dar)**: pod restart et, spesifik deploy'u geri al, önceden-onaylanmış sınırlar içinde pool ölçeklendir, önceden-onaylanmış feature flag etkinleştir.

**Güvenli değil (geniş)**: servis topolojisini değiştir, kaynak limitlerini değiştir, yeni kod deploy et, IAM değiştir, veritabanlarını değiştir.

"Kur ve unut" satan herkes abartıyor. Güvenli küme AI SRE olgunlaştıkça büyür, ama sınır gerçek.

### Adversarial değerlendirme (NeuBird Hawkeye)

İki model aynı olayı bağımsız olarak analiz eder. Kök sebepte anlaşırlarsa, güven yüksek. Anlaşmazlarsa, iki hipotez görünür şekilde insana eskale et. Basit desen, hallucinated kök sebeplere karşı etkili filtre.

### Operasyonel bellek

Takım turnover'ı geleneksel SRE'nin sessiz katili — tribal bilgi gider. AI SRE runbook'ları + post-mortem'leri vektör DB'de saklar; agent'lar her yeni olayda retrieve eder. Yeni mühendisler katıldığında, AI'nın tam geçmişi var.

### Pre-incident tahmin

MIT 2025 araştırması: tarihsel log'lar, GPU sıcaklıkları, API hata desenlerinde eğitilen LLM test setinde outage'ların %89'unu olmadan 10-15 dakika önce tahmin etti.

Gerçeklik kontrolü: aktüasyon olmadan tahminler dashboard'tur. Operasyonel soru "tahmin ettiğimizde ne yapıyoruz?" Önleyici drain? Pager? Auto-scale? Cevap politikaya özgü.

### 2026'da ürünler

- **Datadog Bits AI** — Datadog içinde yönetilen SRE copilot'u.
- **Azure SRE Agent** — Azure-native.
- **NeuBird Hawkeye** — adversarial değerlendirme + operasyonel bellek.
- **PagerDuty AIOps** — triage + dedüplikasyon.
- **Incident.io Autopilot** — incident commander + koordinasyon.

### Kod olarak runbook'lar

Runbook'lar Confluence sayfalarından yapılandırılmış bölümlü (semptom, hipotez, doğrula, eyleme geç) sürümlü markdown'a evrim geçiriyor. Yapılandırılmış runbook'lar daha iyi RAG retrieval besler. Herhangi bir AI-SRE rollout'una yapılandırılmamış runbook'ları yapılandırılmış'a çevirerek başla.

### Hatırlaman gereken sayılar

- MIT erken-tespit: outage'ların %89'u, 10-15 dakika lead time.
- Multi-agent triage: supervisor + (log'lar, metrikler, runbook'lar) + insan.
- Güvenli auto-remediation kümesi: pod restart, deploy geri al, sınırlar içinde ölçeklendir.
- Adversarial değerlendirme: iki model bağımsız; anlaşma = güven.

## Kullan

`code/main.py` bir multi-agent triage simüle eder: log agent hata bulur, metrik agent CPU sıçraması bulur, runbook agent bilinen soruna eşler. Supervisor hipotezleri sıralar.

## Yayınla

Bu ders `outputs/skill-ai-sre-plan.md` üretir. Mevcut on-call, olay hacmi, takım olgunluğu verildiğinde, bir AI SRE rollout'u tasarlar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Log ve metrik agent'lar anlaşmazsa ne olur? Supervisor nasıl çözer?
2. Servisin için üç "güvenli" auto-remediation eylemi tanımla. Her birini gerekçelendir.
3. Yapılandırılmış bir runbook template'i yaz: bölümler, gereken alanlar, doğrulama komutları.
4. Predictive detection 12 dakika lead'de ateşliyor. Politikan ne — pager, ön-drain ya da ikisi?
5. 2026'da 3-kişilik bir takım AI SRE benimsemeli mi yoksa beklemeli mi savun. Olgunluğu, hacmi, riski değerlendir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| AI SRE | "on-call için agent" | LLM-destekli olay araştırma + koordinasyon |
| Supervisor agent | "orkestratör" | Olayları alt-sorgulara bölen üst-seviye agent |
| Özelleşmiş agent | "alan agent'ı" | Tool erişimli alt-agent (log'lar, metrikler, runbook'lar) |
| Auto-remediation | "AI düzeltir" | Önceden-onaylanmış dar eylem; geniş yeniden mimari DEĞİL |
| Operasyonel bellek | "vektör runbook'lar" | RAG için vektör DB'de post-mortem'ler + runbook'lar |
| Adversarial değerlendirme | "iki-model kontrolü" | Bağımsız analizler; anlaşma = güven |
| NeuBird Hawkeye | "adversarial olan" | Adversarial-değerlendirme + bellek deseniyle ürün |
| Bits AI | "Datadog'un SRE agent'ı" | Datadog-yönetilen AI SRE |
| Pre-incident tahmin | "erken tespit" | Outage tahmininde 10-15 dakika lead time |

## İleri Okuma

- [incident.io — AI SRE Complete Guide 2026](https://incident.io/blog/what-is-ai-sre-complete-guide-2026)
- [InfoQ — Human-Centred AI for SRE](https://www.infoq.com/news/2026/01/opsworker-ai-sre/)
- [DZone — AI in SRE 2026](https://dzone.com/articles/ai-in-sre-whats-actually-coming-in-2026)
- [Datadog Bits AI](https://www.datadoghq.com/product/bits-ai/)
- [NeuBird Hawkeye](https://www.neubird.ai/)
- [awesome-ai-sre](https://github.com/agamm/awesome-ai-sre)
