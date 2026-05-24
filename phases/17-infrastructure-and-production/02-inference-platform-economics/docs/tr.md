# Çıkarım Platformu Ekonomisi — Fireworks, Together, Baseten, Modal, Replicate, Anyscale

> 2026 çıkarım pazarı artık GPU zaman kiralaması değil. Custom silikona (Groq, Cerebras, SambaNova), GPU platformlarına (Baseten, Together, Fireworks, Modal) ve API-öncelikli marketplace'lere (Replicate, DeepInfra) bölünüyor. Fireworks 1 Mayıs 2026'da GPU başına saatte $1 zam yaptı; günlük 10T+ token üzerinden $4B değerlemesi, hacim-güdümlü modelin işlediğini söylüyor. Baseten Ocak 2026'da $5B'da $300M Series E kapattı. Rekabetçi pozisyonlama kuralı basit: Fireworks gecikmeyi optimize eder, Together katalog genişliğini optimize eder, Baseten enterprise cilasını optimize eder, Modal Python-native DX'i optimize eder, Replicate multimodal erişimi optimize eder, Anyscale dağıtık Python'u optimize eder. Bu ders sana bir kurucuya verebileceğin bir matris veriyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak çağrı-başı ekonomi karşılaştırıcı)
**Ön koşullar:** Faz 17 · 01 (Yönetilen LLM Platformları), Faz 17 · 04 (vLLM Serving İçleri)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Üç pazar segmentini (custom silikon, GPU platformları, API-öncelikli) adlandır ve her vendor'u bir segmente eşle.
- "Per-token" API fiyatlandırma modelinin neden donanımın değil serving motorunun maliyet eğrisine doğru sıkıştığını açıkla.
- En az üç vendor için istek başına etkin maliyeti hesapla ve per-minute'ın (Baseten, Modal) per-token'ı ne zaman yendiğini açıkla.
- Verilen bir iş yükü için (serverless bursty, kararlı yüksek-throughput, fine-tuned varyantlar, multimodal) hangi platformun doğru varsayılan olduğunu tanımla.

## Sorun

Yönetilen hyperscaler platformları değerlendirdin. Daha dar, daha hızlı bir sağlayıcıya ihtiyacın olduğuna karar verdin — gecikme için Fireworks, genişlik için Together, fine-tuned bir custom model için Baseten. Şimdi altı gerçek seçeneğin var ve fiyatlandırma sayfaları hizalanmıyor. Fireworks $/M token gösteriyor; Baseten $/dakika gösteriyor; Modal $/saniye gösteriyor; Replicate $/tahmin gösteriyor. İş yükünü modellemeden onları kafa kafaya karşılaştıramazsın.

Daha kötüsü, her fiyatlandırma sayfasının arkasındaki iş modeli farklı. Fireworks kendi custom motorunu (FireAttention) shared GPU'larda çalıştırır; per-token oranı utilization eğrilerini yansıtır. Baseten sana Truss + dedicated GPU verir; per-minute exclusivity'yi yansıtır. Modal gerçek Python serverless — alt-saniye cold start'larla per-second faturalama. Aynı çıktı (bir LLM yanıtı), üç farklı maliyet fonksiyonu.

Bu ders altısını modeller ve her birinin ne zaman kazandığını söyler.

## Kavram

### Üç segment

**Custom silikon** — Groq (LPU), Cerebras (WSE), SambaNova (RDU). Aynı modelde tipik olarak GPU-tabanlı bir cluster'dan 5-10x daha hızlı decode. Daha yüksek per-token fiyatı (Groq 2025 sonlarında Llama-70B'de ~$0.99/M idi) ama gecikme-hassas kullanım senaryolarında yenilmez. Groq sesli agent'lar ve gerçek zamanlı çeviri için üretim seçimi.

**GPU platformları** — Baseten, Together, Fireworks, Modal, Anyscale. NVIDIA üzerinde (2026'da H100, H200, B200) ya da bazen AMD üzerinde çalışır. "Çıplak GPU kiralama" (RunPod, Lambda) ile "hyperscaler yönetilen servis" (Bedrock) arasındaki ekonomik katman.

**API-öncelikli marketplace'ler** — Replicate, DeepInfra, OpenRouter, Fal. Geniş katalog, tahmin başına ya da saniye başına ödeme, ilk-çağrıya-zamanı vurgular.

### Fireworks — gecikme-optimize edilmiş GPU platformu

- FireAttention motoru (custom); eşdeğer config'lerde vLLM'den 4 kat daha düşük gecikme olarak pazarlanır.
- Etkileşimsiz iş yükleri için serverless oranının ~%50'sinde batch tier.
- Fine-tuned model base model'la aynı oranda servis edilir — LoRA'n için premium isteyen sağlayıcılara karşı gerçek bir farklılaştırıcı.
- 2026 ortası: on-demand GPU kiralama 1 Mayıs 2026'dan itibaren saatte $1 zam. Ölçekte hacim fiyatlandırması müzakere edilebilir.
- Finansal sinyal: $4B değerleme, günlük 10T+ token işleniyor.

### Together — genişlik-optimize edilmiş

- Upstream yayından sonra günler içinde open-source sürümler dahil 200+ model.
- Eşdeğer LLM modellerinde Replicate'ten %50-70 daha ucuz — "AI Native Cloud" konumlandırması hacim ve katalog.
- Tek API'da çıkarım + fine-tuning + eğitim.

### Baseten — enterprise-cila-optimize edilmiş

- Truss framework'ü: bağımlılıklar, secret'lar, serving config tek bir manifest'te paket olarak model.
- T4'ten B200'e kadar GPU yelpazesi. Makul cold-start mitigasyonuyla per-minute faturalama.
- SOC 2 Type II, HIPAA-hazır. Yaygın fintech ve sağlık tercihi.
- $5B değerleme, Ocak 2026 Series E ($300M; CapitalG, IVP, NVIDIA'dan).

### Modal — Python-native-optimize edilmiş

- Saf Python'da infrastructure-as-code. Bir fonksiyonu `@modal.function(gpu="A100")` ile dekore et ve tek komutla deploy et.
- Per-second faturalama. Pre-warming'le 2-4s cold start; küçük modeller için <1s.
- $1.1B değerlemede $87M Series B (2025). Bağımsız anketlerde en güçlü geliştirici deneyimi skoru.

### Replicate — multimodal genişlik

- Per-prediction ödeme. Görüntü, video ve ses modelleri için varsayılan platform.
- Entegrasyon ekosistemi (Zapier, Vercel, CMS plugin'leri).
- LLM per-token oranlarında daha az rekabetçi ama multimodal çeşitlilikte kazanır.

### Anyscale — Ray-native

- Ray üzerine kurulu; RayTurbo Anyscale'in tescilli çıkarım motoru (vLLM ile yarışır).
- Çıkarım adımının daha büyük bir grafikteki bir node olduğu dağıtık Python iş yükleri için en iyi.
- Yönetilen Ray cluster'ları; Ray AIR ve Ray Serve ile sıkı entegrasyon.

### Per-token vs per-minute — her biri ne zaman kazanır

Per-token, iş yükü gecikme-duyarsız ve bursty olduğunda mantıklı — yalnızca kullandığın için ödersin. Per-minute, utilization yüksek ve öngörülebilir olduğunda mantıklı — GPU'yu doyurduğunda per-token'ı yenersin.

Kabaca kural: dedicated bir GPU'nun ~%30 sürdürülen utilization'ının üzerindeki iş yükleri için, per-minute (Baseten, Modal) per-token'ı (Fireworks, Together) yenmeye başlar. Onun altında, per-token kazanır çünkü boşa ödemekten kaçınırsın.

### Gerçek hendek custom motor

vLLM ve SGLang'in üzerindeki her platform custom motor iddia eder. FireAttention, RayTurbo, Baseten'in çıkarım stack'i. Custom-motor iddiaları pazarlamayı gölgeler — dürüst çerçeveleme, vLLM + SGLang'in üretim open-source çıkarımının yaklaşık %80'ini temsil ettiği ve platform katmanındaki farklılaştırıcıların DX, atıf ve SLA olduğu.

### Hatırlaman gereken sayılar

- Fireworks GPU kiralama: 1 Mayıs 2026'dan itibaren saatte $1 zam.
- Fireworks iddiası: eşdeğer config'lerde vLLM'den 4 kat daha düşük gecikme.
- Together: LLM'lerde Replicate'ten %50-70 daha ucuz.
- Baseten değerlemesi: $5B (Series E, Ocak 2026, $300M tur).
- Modal değerlemesi: $1.1B (Series B, 2025).
- Per-minute, ~%30 sürdürülen utilization'ın üstünde per-token'ı yener.

## Kullan

`code/main.py` altı vendor'u fiyatlandırma modelleri arasında sentetik bir iş yükünde karşılaştırır. $/gün ve etkin $/M token raporlar. Çalıştır, per-token ile per-minute arasındaki break-even'ı bul.

## Yayınla

Bu ders `outputs/skill-inference-platform-picker.md` üretir. İş yükü profili, SLA ve bütçe verildiğinde, birincil çıkarım platformunu seçer ve ikinciyi adlandırır.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Tek H100'de 70B model için Baseten (per-minute) Fireworks'ü (per-token) hangi sürdürülen utilization'da yener? Crossover'ı kendin türet ve kural-ı kaba ile karşılaştır.
2. Ürünün görüntü üretimi + sohbet + speech-to-text servis ediyor. Her modalite için platform seç ve onları birleştiren gateway desenini adlandır.
3. Fireworks birincil modelinde saatte $1 zam yapar. Trafiğinin %40'ı batch tier'a (%50 indirim) geçerse harmanlanmış maliyet etkisini modelle.
4. Regüle bir müşteri SOC 2 Type II + HIPAA + dedicated GPU gerektiriyor. Hangi üç platform yaşayabilir ve hangisi FinOps'ta kazanır?
5. Llama 3.1 70B için 1.000 tahmin başına maliyeti Fireworks serverless, Together on-demand, Baseten dedicated ve Replicate API'da karşılaştır. Günde 10 tahminde hangisi en ucuz? 10.000'de?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Custom silikon | "GPU olmayan çipler" | Groq LPU, Cerebras WSE, SambaNova RDU — decode için optimize edilmiş |
| FireAttention | "Fireworks motoru" | Custom attention kernel'i; vLLM'den 4 kat daha düşük gecikme olarak pazarlanır |
| Truss | "Baseten'in formatı" | Model paketleme manifest'i; bağımlılıklar + secret'lar + serving config |
| Per-token | "API fiyatlandırması" | Tüketilen token'a göre ücretlendir; boşa ödeme yok |
| Per-minute | "dedicated fiyatlandırma" | Wall-clock GPU zamanına göre ücretlendir; yüksek utilization'da kazanır |
| Per-prediction | "Replicate fiyatlandırması" | Model çağrısı başına ücretlendir; görüntü/video için yaygın |
| RayTurbo | "Anyscale motoru" | Ray üzerinde tescilli çıkarım; Ray cluster'larında vLLM ile yarışır |
| Batch tier | "%50 indirim" | İndirimli oranda etkileşimsiz queue; Fireworks, OpenAI'da yaygın |
| Fine-tuned at base rate | "Fireworks LoRA" | LoRA-servis edilen istekleri base model oranında ücretlendir (farklılaştırıcı) |

## İleri Okuma

- [Fireworks Pricing](https://fireworks.ai/pricing) — per-token oranları, batch tier, GPU kiralama.
- [Baseten Pricing](https://www.baseten.co/pricing/) — per-minute oranları, taahhütlü kapasite, enterprise tier'lar.
- [Modal Pricing](https://modal.com/pricing) — per-second GPU oranları ve ücretsiz tier.
- [Together AI Pricing](https://www.together.ai/pricing) — model kataloğu ve per-token oranları.
- [Anyscale Pricing](https://www.anyscale.com/pricing) — RayTurbo ve yönetilen Ray fiyatlandırması.
- [Northflank — Fireworks AI Alternatives](https://northflank.com/blog/7-best-fireworks-ai-alternatives-for-inference) — karşılaştırmalı değerlendirme.
- [Infrabase — AI Inference API Providers 2026](https://infrabase.ai/blog/ai-inference-api-providers-compared) — vendor manzarası.
