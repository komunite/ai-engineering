# Batch API'lar — Endüstri Standardı Olarak %50 İndirim

> Her büyük sağlayıcı %50 indirim ve ~24 saat turnaround ile bir async batch API yayınlıyor. OpenAI, Anthropic, Google ve çıkarım platformlarının çoğu (Fireworks batch tier, Together batch) aynı deseni uyguluyor. Batch'i prompt caching ile yığarsan gece pipeline'ları senkron-cache'siz maliyetin ~%10'una düşer. Kural acımasız basit: etkileşimli değilse, batch'e ait. İçerik üretim pipeline'ları, belge sınıflandırma, veri çıkarma, rapor üretimi, toplu etiketleme, katalog tag'leme — 24-saat gecikmeye toleranslı her şey batch'e taşınana kadar masada bırakılan paradır. 2026 üretim deseni her yeni LLM iş yükünü üç şeritte triyaj etmek: etkileşimli (caching'li senkron), yarı-etkileşimli (fallback'li async queue), batch (gecelik, cache'lenmiş input yığılı). Etkileşimli gibi davranan ama dakikalarca gecikmeye toleranslı iş yükleri en çok israfı yapar.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak batch-vs-sync maliyet simülatörü)
**Ön koşullar:** Faz 17 · 14 (Prompt & Semantic Caching)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Üç sağlayıcı batch API'sını (OpenAI, Anthropic, Google) ve ortak %50 indirim + 24s turnaround garantilerini adlandır.
- Gecelik bir sınıflandırma iş yükünde batch + cache'lenmiş input yığma maliyetini hesapla ve senkron-cache'siz baseline ile karşılaştır.
- Bir iş yükünü etkileşimli / yarı-etkileşimli / batch olarak triyaj et ve şeridi gerekçelendir.
- İki tuzağı adlandır: kısmi etkileşimlilik (kullanıcı 24s'den hızlı bekler) ve output-schema drift (batch dosya formatı sağlayıcıya göre farklı).

## Sorun

Takımın gecelik bir rapor üretim pipeline'ı yayınlıyor. 50.000 belge, her birini özetle, özetleri kümele, bir yönetici brifi taslakla. Senkron çalışırsa gece başına $2.000'a 4 saat alır. Batch API'lardan duyuyorsun.

Batch sana %50 indirim sağlıyor. Ayrıca system prompt'ta (50k çağrıda paylaşılan) prompt caching'i etkinleştiriyorsun. Yığılı, fatura gece başına $180'a düşüyor — baseline'ın ~%9'u. Aynı pipeline, üç config değişikliği.

Batch hiç kimsenin çekmediği LLM maliyet toolkit'inde en ucuz manivela. Sebep çoğunlukla organizasyonel: SLA gerçekte "sabah ile" olduğunda takımlar "gerçek-zamanlı" düşünür. Bu ders faturanın %90'ını masada bırakmamak hakkında.

## Kavram

### Üç batch API'sı

**OpenAI Batch API**: istek listesiyle JSONL dosya upload. Söz verilen 24-saat turnaround (pratikte genelde ~2-8 saat). Input ve output token'larında %50 indirim. `/v1/batches` endpoint'i. Cache-uygun input'lar üstüne cache'lenmiş-input fiyatlandırması da alır.

**Anthropic Message Batches**: JSONL upload. 24-saat turnaround. %50 indirim. `cache_control` destekler — cache yazımları açık, okumalar batch içinde otomatik olur.

**Google Vertex AI Batch Prediction**: BigQuery ya da GCS input. Gemini için benzer %50 indirim. Vertex pipeline'larıyla entegre olur.

### Semantik: asenkron, yavaş değil

Batch "24 saat içinde dönmeye söz veriyorum" — "bu 24 saat alacak" değil. Tipik P50 2-6 saat. Sağlayıcı batch'ini GPU envanterinin az kullanıldığı tepe-dışı pencerelerde schedule eder.

### Caching ile yığ

Aynı 4K-token'lık system prompt'lu 50k-belgelik bir özetleme:

- Senkron cache'siz: tam oranlarda 50000 × ($input × 4000 + $output × 200).
- Senkron cache'li: system prompt ilk yazımdan sonra cache'lenir; kalan 49999 10x daha ucuz input alır.
- Batch cache'li: yukarıdakilerin hepsi artı hem okuma hem yazmada %50 indirim.

Yığın: batch + cache = sync cache'siz faturanın ~%10'u. Gece çalışan ve paylaşılan bir system prompt'u olan herhangi bir iş yükü bunu kullanmalı.

### İş yükü triyajı

**Etkileşimli** — kullanıcı yanıt için bekler. TTFT önemli. Prompt caching'li senkron çağrı. Batch'lenemez.

**Yarı-etkileşimli** — kullanıcı bir görev sunar, dakikalarca sonra kontrol eder. Batch mevcut değilse sync'e fallback'li async queue. Orta-hacimli RAG indeksleme düşün.

**Batch** — kullanıcı sonuçları "sabah ile" ya da "sonraki saat" bekler. İçerik pipeline'ları, ölçekte sınıflandırma, offline analiz. Her zaman batch, her zaman caching yığ.

Yaygın hata: pipeline üretim olduğu için her şeyi etkileşimli sınıflandırmak. Üretim bir gecikme spec'i değil — SLA spec.

### Kısmi-etkileşimlilik tuzağı

Bazı özellikler etkileşimli görünür ama 5-10 dakikaya toleranslıdır. Örnek: "yenile" butonlu gecelik bir müşteri sağlık raporu. Kullanıcı yenile'yi tıklar; 10 dakika beklemek tamam. Takım onu senkron olarak yayınlar. 50 eşzamanlı yenileme batch'lenip-e-mail-üzerinden-teslim edilenin 10x maliyetine sahip.

Sorulacak soru: "Bu kullanıcı için 24 saat ne demek?" Cevap "fark etmezdi" ise, batch'le.

### Output-schema tuzağı

Batch dosya formatları sağlayıcıya göre farklı:

- OpenAI: JSONL, satır başına bir istek.
- Anthropic: JSONL, satır başına bir mesaj; yanıt formatı gömülü.
- Vertex: BigQuery tablosu ya da TFRecord'lu GCS prefix.

Sağlayıcılar arasında "tek batch client" yazmak sağlayıcı başına adapter kodu demek. Multi-sağlayıcı batch reklamı yapan gateway'ler (Portkey, bazı LiteLLM tier'ları) hâlâ ham formatı ince-sarar.

### Hatırlaman gereken sayılar

- Sağlayıcılar arasında batch indirimi: input + output'ta düz %50.
- Turnaround SLA: 24 saat garanti, tipik P50 2-6 saat.
- Yığılı batch + cache'lenmiş input: sync cache'siz maliyetin ~%10'u.
- İş yükü triyaj kuralı: 24s gecikme kabul edilebilirse, her zaman batch.

## Kullan

`code/main.py` 50k-belge iş yükü için sync, sync+cache, batch ve batch+cache arasında maliyetleri hesaplar. Tasarrufları $ ve yüzde olarak raporlar.

## Yayınla

Bu ders `outputs/skill-batch-triager.md` üretir. İş yükü karakteristikleri verildiğinde, interactive/semi/batch'e triyaj eder ve tasarrufları tahmin eder.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. 3K-token'lık system prompt ve 500-token output'lu 100k-belge pipeline'ı için, tam stack'in (batch + cache) sync baseline'a karşı tasarruflarını hesapla.
2. Bildiğin gerçek bir üründe üç özellik seç. Her birini interactive/semi/batch'e triyaj et.
3. Bir kullanıcı raporunun 3 saat aldığını şikayet ediyor. Bu bir batch mis-triyaj mı yoksa meşru bir interactive mi? Karar kriterini yaz.
4. Batch API dönüş SLA'in 24s ama P99 20 saat. Bunu kullanıcıya nasıl iletirsin — kenar durumda downstream sistem davranışı ne?
5. Break-even'ı hesapla: hangi paylaşılan-prefix uzunluğunda batch + cache kendi rezerve edilmiş GPU'nda gecelik çalıştırmaktan daha ucuz hale gelir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Batch API | "async indirim" | 24s turnaround ile %50 indirim |
| JSONL | "batch formatı" | Satır başına bir JSON istek; OpenAI/Anthropic standardı |
| Message Batches | "Anthropic batch" | Anthropic'in batch API ürün adı |
| Batch prediction | "Vertex batch" | Vertex AI'ın batch API ürünü |
| Turnaround SLA | "24s sözü" | Garanti, tipik değil; tipik 2-6s |
| İş yükü triyajı | "etkileşim kararı" | Interactive / semi / batch yönlendirme kararı |
| Output schema | "yanıt formatı" | Sağlayıcı başına JSONL layout'u; taşınabilir değil |
| Yığılı indirim | "batch + cache" | İkisi de uygulanırsa cache'siz sync faturasının ~%10'u |

## İleri Okuma

- [OpenAI Batch API](https://platform.openai.com/docs/guides/batch) — JSONL formatı ve `/v1/batches` semantiği.
- [Anthropic Message Batches](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing) — batch formatı ve `cache_control` etkileşimi.
- [Vertex AI Batch Prediction](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/batch-prediction) — Gemini batch semantiği.
- [Finout — OpenAI vs Anthropic API Pricing 2026](https://www.finout.io/blog/openai-vs-anthropic-api-pricing-comparison)
- [Zen Van Riel — LLM API Cost Comparison 2026](https://zenvanriel.com/ai-engineer-blog/llm-api-cost-comparison-2026/)
