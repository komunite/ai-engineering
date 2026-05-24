# Agent Observability: Langfuse, Phoenix, Opik

> Üç açık-kaynak agent observability platformu 2026'ya hakim. Langfuse (MIT) — ayda 6M+ install, tracing + prompt management + eval'ler + session replay. Arize Phoenix (Elastic 2.0) — derin agent-spesifik eval'ler, RAG relevancy, OpenInference auto-instrumentation. Comet Opik (Apache 2.0) — otomatik prompt optimization, guardrail'ler, LLM-judge hallucination tespiti.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 23 (OTel GenAI)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Üç en iyi açık-kaynak agent observability platformunu ve lisanslarını adlandır.
- Her birinin neyde en güçlü olduğunu ayır: Langfuse (prompt mgmt + session'lar), Phoenix (RAG + auto-instrumentation), Opik (optimization + guardrail'ler).
- 2026'ya kadar organizasyonların %89'unun neden agent observability'sine sahip olduklarını rapor ettiğini açıkla.
- LLM-judge değerlendirmesi ile bir stdlib trace-to-dashboard pipeline'ı uygula.

## Sorun

OTel GenAI (Ders 23) sana şemayı verir. Hâlâ span'leri ingest eden, değerlendirmeleri çalıştıran, prompt versiyonlarını saklayan ve regresyonları yüzeye çıkaran platforma ihtiyacın var. Üç aday her biri lifecycle'ın farklı kısımlarını vurguluyor.

## Kavram

### Langfuse (MIT)

- Ayda 6M+ SDK install, 19k+ GitHub yıldızı.
- Özellikler: tracing, versiyonlama + playground'lu prompt management, değerlendirmeler (LLM-as-judge, kullanıcı feedback, custom), session replay'leri.
- Haziran 2025: eskiden ticari modüller (LLM-as-a-judge, annotation queue'lar, prompt experiment'lar, Playground) MIT altında açık kaynaklandı.
- En güçlü olduğu: sıkı prompt-management döngülü uçtan-uca observability.

### Arize Phoenix (Elastic License 2.0)

- Daha derin agent-spesifik değerlendirme: trace clustering, anomali tespiti, RAG için retrieval relevancy.
- Native OpenInference auto-instrumentation.
- Üretim için yönetilen Arize AX ile eşleşir.
- Prompt versiyonlama yok — daha geniş platformların yanında drift/davranışsal-regresyon tool'u olarak konumlanmış.
- En güçlü olduğu: RAG relevancy, davranışsal drift, anomali tespiti.

### Comet Opik (Apache 2.0)

- A/B experiment'lar üzerinden otomatik prompt optimization.
- Guardrail'ler (PII redaction, konusal kısıtlamalar).
- LLM-judge hallucination tespiti.
- Comet'in kendi ölçümünden benchmark: Opik 23.44sn'de log + eval vs Langfuse 327.15sn (~14x uçurum) — vendor benchmark'larını yönsel olarak ele al.
- En güçlü olduğu: optimization döngüsü, otomatik deney, guardrail enforcement.

### Endüstri verisi

Maxim (2026 saha analizi)'e göre: organizasyonların %89'u agent observability'sine sahip; kalite sorunları en yüksek üretim engeli (%32 respondent cite ediyor).

### Birini seçme

| İhtiyaç | Seç |
|------|------|
| Prompt management'lı all-in-one | Langfuse |
| Derin RAG değerlendirmesi + drift | Phoenix |
| Otomatik optimization + guardrail'ler | Opik |
| Açık lisans, ELv2 yok | Langfuse (MIT) ya da Opik (Apache 2.0) |
| Datadog / New Relic entegrasyonu | Herhangi biri — hepsi OTel export eder |

### Bu desen nerede ters gider

- **Eval stratejisi yok.** Değerlendirme olmadan tracing yalnızca pahalı logging.
- **Topraklamasız self-roll LLM-judge.** CRITIC deseni (Ders 05) uygulanır — judge'lar factual doğrulama için dış tool'lara ihtiyaç duyar.
- **Trace'lere bağlı olmayan prompt versiyonları.** Prod regresyon yaptığında, ona sebep olan prompt'a bisect edemezsin.

## İnşa Et

`code/main.py` bir stdlib trace collector + LLM-judge evaluator uyguluyor:

- GenAI-şekilli span'leri ingest et.
- Session'a göre grupla, başarısız koşuları (guardrail tetiklenmeleri, düşük-güven eval'ler) etiketle.
- Bir rubric'te agent yanıtlarını puanlayan scripted bir LLM-judge.
- Dashboard-benzeri bir özet: başarısızlık oranı, en yüksek başarısızlık nedenleri, eval skor dağılımı.

Çalıştır:

```
python3 code/main.py
```

Çıktı: Langfuse/Phoenix/Opik'in göstereceğine eşleşen session-başına eval skorları ve başarısızlık kategorilemesi.

## Kullan

- **Langfuse** self-hosted ya da bulut; OTel ya da SDK'ları üzerinden kablola.
- **Arize Phoenix** self-hosted; OpenInference auto-instrument et.
- **Comet Opik** self-hosted ya da bulut; otomatik optimization döngüsü.
- **Datadog LLM Observability** zaten Datadog çalıştıran karma ops+ML ekipleri için.

## Yayınla

`outputs/skill-obs-platform-wiring.md` bir platform seçer ve mevcut bir agent'a trace'leri + eval'leri + prompt versiyonlarını kablolar.

## Alıştırmalar

1. Bir haftalık OTel trace'i Langfuse cloud'a (free tier) export et. Hangi session'lar başarısız oldu? Neden?
2. Domain'in için bir LLM-judge rubric'i yaz (factual doğruluk, ton, scope uyumu). 50 trace üzerinde test et.
3. Langfuse prompt versiyonlamayı Phoenix'in trace clustering'ine karşı karşılaştır. Hangisi neyin daha hızlı bozulduğunu söylüyor?
4. Opik'in guardrail dokümanlarını oku. Agent koşularından birine bir PII redaction guardrail'i kablola.
5. Üçünü corpus'unda benchmark et. Vendor-yayınlı sayıları yoksay; kendi ölçümünü yap.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Tracing | "Span'ler toplayıcısı" | OTel / SDK span'leri ingest et; session ile indeksle |
| Prompt management | "Prompt CMS" | Trace'lere bağlı versiyonlu prompt'lar |
| LLM-as-judge | "Otomatik eval" | Ayrı LLM agent çıktısını bir rubric'e karşı puanlar |
| Session replay | "Trace playback" | Hata ayıklama için geçmiş koşuları adım adım gez |
| RAG relevancy | "Retrieval kalitesi" | Getirilen context sorgu ile eşleşiyor mu |
| Trace clustering | "Davranışsal gruplama" | Drift tespiti için benzer koşuları cluster'la |
| Guardrail enforcement | "Log zamanında policy" | Loglanan içerikte PII/toxicity/scope check'leri |

## İleri Okuma

- [Langfuse docs](https://langfuse.com/) — tracing, eval'ler, prompt mgmt
- [Arize Phoenix docs](https://docs.arize.com/phoenix) — auto-instrumentation, drift
- [Comet Opik](https://www.comet.com/site/products/opik/) — optimization + guardrail'ler
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — üçünün de tükettiği şema
