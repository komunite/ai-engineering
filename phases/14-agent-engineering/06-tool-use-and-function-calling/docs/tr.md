# Tool Use ve Function Calling

> Toolformer (Schick et al., 2023) self-supervised tool annotation'ı başlattı. Berkeley Function Calling Leaderboard V4 (Patil et al., 2025) 2026 çıtasını belirliyor: %40 agentic, %30 multi-turn, %10 live, %10 non-live, %10 hallucination. Single-turn çözüldü. Bellek, dinamik karar verme ve uzun-ufuk tool zincirleri çözülmedi.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 13 · 01 (Function Calling Deep Dive)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Toolformer'ın self-supervised eğitim sinyalini açıkla: tool annotation'larını yalnızca yürütme bir-sonraki-token kaybını azaltırsa tut.
- BFCL V4'ün beş değerlendirme kategorisini ve her birinin ne ölçtüğünü adlandır.
- Şema doğrulama, argüman coercion'ı ve yürütme sandbox'ı ile bir stdlib tool registry uygula.
- Üç 2026 açık problemini teşhis et: uzun-ufuk tool zincirleme, dinamik karar verme ve bellek.

## Sorun

Erken tool use şunu sordu: model doğru bir function call'u tahmin edebilir mi? Modern tool use şunu soruyor: model 40 adım boyunca, bellekle, kısmi gözlemlenebilirlikle, tool başarısızlıklarından kurtuluşla, var olmayan tool'lar halüsine etmeden tool zincirleyebilir mi?

Toolformer baseline'ı kurdu: modeller tool çağrısı zamanını self-supervision ile öğrenebilir. BFCL V4 2026 değerlendirme hedefini tanımlar. Aralarındaki uçurum üretim agent'larının yaşadığı alan.

## Kavram

### Toolformer (Schick et al., NeurIPS 2023)

Fikir: modelin kendi pretraining corpus'unu aday API çağrılarıyla annotate etmesine izin ver. Her aday için onu yürüt. Annotation'ı yalnızca tool sonucunu dahil etmek bir-sonraki-token kaybını azaltıyorsa tut. Filtrelenmiş corpus üzerinde fine-tune et.

Kapsanan tool'lar: calculator, QA sistem, search engine'ler, translator, calendar. Self-supervision sinyali yalnızca tool'un metin tahminine yardım edip etmediğiyle ilgili — insan etiketi yok.

Ölçek sonucu: tool use ölçekte ortaya çıkıyor. Küçük modeller tool annotation'larından zarar görür; daha büyük modeller kazanır. 2026 frontier modellerinin neden güçlü tool use'a sahip olduğu, çoğu 7B modelinin güvenilir olması için neden açık tool-use fine-tuning gerektirdiği bu yüzden.

### Berkeley Function Calling Leaderboard V4 (Patil et al., ICML 2025)

BFCL 2026 fiili değerlendirme. V4 komposizyonu:

- **Agentic (%40)** — tam agent trajectory'leri: bellek, multi-turn, dinamik kararlar.
- **Multi-Turn (%30)** — tool zincirli interaktif konuşmalar.
- **Live (%10)** — kullanıcı-gönderimi gerçek prompt'lar (daha zor dağılım).
- **Non-Live (%10)** — sentetik test caseler.
- **Hallucination (%10)** — hiçbir tool çağrılmaması gerektiğini tespit et.

V3 state-based değerlendirmeyi tanıttı: bir tool dizisinden sonra, tool çağrılarının AST'sini eşleştirmek yerine API'nin gerçek state'ini kontrol et (örn. "dosya oluşturuldu mu?"). V4 web search, bellek ve format hassasiyet kategorilerini ekledi.

Ana 2026 bulgusu: single-turn function calling neredeyse çözüldü. Başarısızlıklar bellekte (turlar arasında bağlam taşıma), dinamik karar vermede (önceki sonuçlara göre tool seçimi), uzun-ufuk zincirlerde (20+ adımdan sonra drift) ve hallucination tespitinde (hiçbir tool uymadığında çağrıyı reddetme) yoğunlaşır.

### Tool şeması

Her sağlayıcının bir şeması var. Detaylarda farklılar ama aynı şekli paylaşırlar:

```
name: string
description: string (ne yaptığı, ne zaman kullanılacağı)
input_schema: JSON Schema (properties, required, types, enums)
```

Anthropic `input_schema`'yı doğrudan kullanır. OpenAI `function.parameters` kullanır. Her ikisi de JSON Schema kabul eder. Açıklamalar taşıyıcı — model doğru tool'u seçmek için onları okur. Kötü tool açıklamaları yanlış-tool-seçildi başarısızlıklarının 1 numaralı kök nedeni.

### Argüman doğrulama

Hiçbir tool çağrısına güvenme. Doğrula:

1. **Type coercion.** Model şema int derken "5" string'i döndürebilir. Belirsizlik yoksa coerce et; varsa reddet.
2. **Enum doğrulama.** Şema `status in {"open", "closed"}` derse ve model `"in_progress"` yayarsa, açıklayıcı bir hata ile reddet.
3. **Zorunlu alanlar.** Eksik zorunlu alan -> crash değil, modele anında geri hata gözlemi.
4. **Format doğrulama.** Tarihler, e-postalar, URL'ler — regex değil, somut parser'larla doğrula.

Her doğrulama başarısızlığı yapılandırılmış bir gözlem döndürmeli, böylece model doğru şekille yeniden deneyebilir.

### Paralel tool çağrıları

Modern sağlayıcılar tek bir assistant turunda paralel tool çağrılarını destekler. Döngü:

1. Model farklı `tool_use_id`'lerle 3 tool çağrısı yayar.
2. Runtime onları yürütür (bağımsızsa paralel).
3. Her sonuç `tool_use_id` ile korele edilmiş bir `tool_result` bloğu olarak geri döner.

Mühendislik kuralı: korelasyon ID'lerini taşıyıcı olarak ele al. Onları takas et ve yanlış-tool-yanlış-sonuca routing alırsın.

### Sandboxing

Tool yürütmesi sandbox sınırı. Detay için Ders 09'a bak. Kısa versiyon: her tool read/write yüzeyi, ağ erişimi, timeout, bellek tavanı belirtmeli. Jenerik `run_shell(cmd)` kırmızı bayrak; spesifik `git_status()` daha güvenli.

## İnşa Et

`code/main.py` üretim-şekilli bir tool registry uyguluyor:

- JSON Schema alt-küme doğrulayıcı (yalnızca stdlib).
- Açıklama, input schema, timeout ve executor ile tool registration.
- Argüman coercion ve enum doğrulama.
- Korelasyon ID'leriyle paralel tool dispatch.
- Yapılandırılmış string olarak hata gözlemleri.

Çalıştır:

```
python3 code/main.py
```

Trace bir mini agent'ın tek turda üç tool çağırdığını gösteriyor; modelin işleyebileceği açıklayıcı bir hatayla reddedilen kasten bozulmuş bir çağrı dahil.

## Kullan

Her sağlayıcının kendi tool şeması var — Anthropic, OpenAI, Gemini, Bedrock. Multi-provider gerekirse bir çeviri katmanı (OpenAI Agents SDK, Vercel AI SDK, LangChain tool adapter) kullan. BFCL referans benchmark — tool use üründe merkezi ise yayınlamadan önce agent'ına karşı çalıştır.

## Yayınla

`outputs/skill-tool-registry.md` belirli bir görev domain'i için tool kataloğu, şema ve registry üretir. Açıklama-kalite kontrolleri dahil (her tool'un açıklaması modele ne zaman kullanacağını söylüyor mu?).

## Alıştırmalar

1. Modelin açıkça başka herhangi bir tool kullanmayı reddetmesine izin veren bir "no-op" tool ekle. BFCL-benzeri bir hallucination testinde ölç.
2. Int-as-string ve float-as-string için argüman coercion uygula. Coercion gerçek bug'ları gizlemeye nerede başlar?
3. Tool başına timeout ve circuit breaker ekle (3 ardışık başarısızlıktan sonra 60sn tool'u reddet). Bu modelin nasıl kurtulduğu hakkında neyi değiştirir?
4. BFCL V4 açıklamasını oku. Bir kategori seç (örn. "multi-turn") ve agent'ından 10 örnek prompt çalıştır. Geçiş oranını raporla.
5. Stdlib doğrulayıcıyı Pydantic ya da Zod'a taşı. Pydantic/Zod oyuncağın kaçırdığı neyi yakaladı?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Function calling | "Tool use" | Doğrulanmış şemayla yapılandırılmış-çıktı tool invocation |
| Toolformer | "Self-supervised tool annotation" | Schick 2023 — sonuçları bir-sonraki-token kaybını azaltan tool çağrılarını tut |
| BFCL | "Berkeley Function Calling Leaderboard" | 2026 benchmark: %40 agentic, %30 multi-turn, %10 live, %10 non-live, %10 hallucination |
| Tool schema | "Model için function signature" | name, description, argümanların JSON Schema'sı |
| tool_use_id | "Korelasyon ID'si" | Bir tool çağrısını sonucuna bağlar; paralel dispatch için zorunlu |
| Hallucination tespiti | "Çağırmamayı bil" | V4 kategorisi: hiçbir tool uymadığında çağırmayı reddet |
| Argüman coercion'ı | "String-to-int onarımı" | Tahmin edilebilir şema-uyumsuzluğu için dar düzeltmeler; belirsizse reddet |
| Sandboxing | "Tool yürütme sınırı" | Tool başına read/write yüzeyi, ağ, timeout, bellek tavanı |

## İleri Okuma

- [Schick et al., Toolformer (arXiv:2302.04761)](https://arxiv.org/abs/2302.04761) — self-supervised tool annotation
- [Berkeley Function Calling Leaderboard (V4)](https://gorilla.cs.berkeley.edu/leaderboard.html) — 2026 eval benchmark
- [Anthropic, Tool use documentation](https://platform.claude.com/docs/en/agent-sdk/overview) — Claude Agent SDK'da üretim tool şeması
- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) — function tool type ve Guardrails
