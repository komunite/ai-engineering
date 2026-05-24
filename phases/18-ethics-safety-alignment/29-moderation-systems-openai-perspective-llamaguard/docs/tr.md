# Moderation Sistemleri — OpenAI, Perspective, Llama Guard

> Üretim moderation sistemleri Ders 12-16'da tanımlanan safety policy'lerini operasyonel hale getirir. OpenAI Moderation API: `omni-moderation-latest` (2024) GPT-4o üzerine inşa edilmiş, tek bir çağrıda text + görüntüleri sınıflandırır; önceki versiyondan multilingual test setinde %42 daha iyi; yanıt şeması 13 kategori boolean döndürür — harassment, harassment/threatening, hate, hate/threatening, illicit, illicit/violent, self-harm, self-harm/intent, self-harm/instructions, sexual, sexual/minors, violence, violence/graphic; çoğu geliştirici için ücretsiz. Katmanlı desenler: Input moderation (pre-generation), Output moderation (post-generation), Custom moderation (alan kuralları). Async paralel çağrılar latency'yi saklar; flag'de placeholder yanıtlar. Llama Guard 3/4 (Ders 16): 14 MLCommons tehlike, Code Interpreter Abuse, 8 dil (v3), multi-image (v4). Perspective API (Google Jigsaw): LLM-as-moderator dalgasından önce gelen toxicity puanlaması; öncelikle severe-toxicity/insult/profanity varyantlarıyla tek-boyutlu toxicity; content-moderation araştırması için baseline. Deprecation'lar: Azure Content Moderator Şubat 2024'te deprecate edildi, Şubat 2027'de emekli olur, Azure AI Content Safety ile değiştirildi.

**Tür:** Yapım
**Diller:** Python (stdlib, üç-katmanlı moderation harness'ı)
**Ön koşullar:** Faz 18 · 16 (Llama Guard / Garak / PyRIT)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- OpenAI Moderation API'nin kategori taksonomisini ve Llama Guard 3'ün MLCommons setinden nasıl farklılaştığını tarif et.
- Üç moderation-katmanı desenini (input, output, custom) tarif et ve her birinin bir failure mode'unu adlandır.
- Perspective API'nin pre-LLM-era baseline olarak konumunu ve araştırmada neden kullanılmaya devam ettiğini tarif et.
- Azure deprecation zaman çizelgesini ifade et.

## Sorun

Dersler 12-16 saldırıları ve savunma araçlarını tarif eder. Ders 29 kullanıcıların ürüne dokunduğu yüzeyde savunmaları operasyonel hale getiren deploy edilmiş moderation sistemlerini kapsar. Üç-katmanlı desen 2026 varsayılan konfigürasyonudur.

## Kavram

### OpenAI Moderation API

`omni-moderation-latest` (2024). GPT-4o üzerine inşa edilmiş. Tek bir çağrıda text + görüntüleri sınıflandırır. Çoğu geliştirici için ücretsiz.

Kategoriler (yanıt şemasında 13 boolean):
- harassment, harassment/threatening
- hate, hate/threatening
- self-harm, self-harm/intent, self-harm/instructions
- sexual, sexual/minors
- violence, violence/graphic
- illicit, illicit/violent

Multimodal destek `violence`, `self-harm` ve `sexual`'a uygulanır ama `sexual/minors`'a değil; geri kalanı yalnızca text.

`code/main.py`'deki kod harness'ı için pedagojik basitlik adına `/threatening`, `/intent`, `/instructions` ve `/graphic` alt kategorilerini üst seviye ana kategorilerine birleştiriyoruz. Üretim kodu tam 13-kategori şemasını kullanmalı.

Önceki nesil moderation endpoint'inden multilingual test setinde %42 daha iyi. Kategori-başına skorlar; uygulamalar eşikleri belirler.

### Llama Guard 3/4

Ders 16'da kapsanır. 14 MLCommons tehlike kategorisi (OpenAI'nın 13 yanıt-şeması boolean'ından farklı şekilde organize edilmiş). 8 dili destekler (v3). Llama Guard 4 (Nisan 2025) nativ multimodal, 12B'dir.

OpenAI ve Llama Guard taksonomileri örtüşür ama ayrışır. OpenAI'nın geniş kategori olarak "illicit"i var; Llama Guard'ın ayrı ayrı "violent crimes" ve "non-violent crimes"i var. Deployment'lar policy-taksonomi uyumlarına göre seçer.

### Perspective API (Google Jigsaw)

LLM-as-moderator dalgasından önce gelen toxicity puanlama sistemi (2020 öncesi). Kategoriler: TOXICITY, SEVERE_TOXICITY, INSULT, PROFANITY, THREAT, IDENTITY_ATTACK. Tek-boyutlu birincil skor (TOXICITY) alt-boyut varyantlarıyla.

Content-moderation araştırma baseline'ı olarak geniş çapta kullanılır çünkü API stabil, belgelenmiş ve yıllarca kalibrasyon verisi var. Modern LLM-bitişik use case'leri için, Llama Guard veya OpenAI Moderation genellikle daha iyi uyumdur.

### Üç-katmanlı desen

1. **Input moderation.** Üretim öncesi kullanıcının prompt'unu sınıflandır. Flag'lenirse reddet. Latency: bir classifier çağrısı.
2. **Output moderation.** Teslim öncesi modelin çıktısını sınıflandır. Flag'lenirse bir reddetme ile değiştir. Latency: üretim sonrası bir classifier çağrısı.
3. **Custom moderation.** Alana-özgü kurallar (regex, allowlist, business policy). Input veya output'ta çalışır.

Üç katman tasarım gereği sıralıdır: input moderation üretimden önce tamamlanmalı ve output moderation üretimden sonra çalışmalıdır. Bir katman içinde paralellik uygulanır — aynı metinde birden çok classifier (örn. OpenAI Moderation + Llama Guard + Perspective) eş zamanlı çalıştırmak classifier-başına latency'yi saklar. Opsiyonel bir optimizasyon olarak, input moderation tamamlanırken ve token-1 streaming ertelenirken bir placeholder yanıtı ("bir saniye, kontrol ediliyor...") gösterilebilir. Flag davranışı konfigüre edilebilir: reddet, sanitize, insan incelemesine eskalasyon.

### Failure mode'lar

- **Yalnızca Input.** Çıktı hallucination'larını yakalamaz (Ders 12-14 kodlama saldırıları input classifier'larını bypass eder).
- **Yalnızca Output.** Herhangi bir input'un modele ulaşmasına izin verir; maliyeti artırır; internal akıl yürütmeyi saldırgana yüzeyler.
- **Yalnızca Custom.** Kategoriler arasında sağlam değil; regex'ler kırılgan.

Katmanlı varsayılandır. Belt-and-suspenders.

### Azure deprecation

Azure Content Moderator: Şubat 2024'te deprecate edildi, Şubat 2027'de emekli olur. LLM-tabanlı olan ve Azure OpenAI ile entegre olan Azure AI Content Safety ile değiştirildi. Geçiş Azure deployment'ları için 2024-2027 alan-seviyesi bir projedir.

### Bu Faz 18'de nereye uyuyor

Ders 16 red-team bağlamında moderation araçlarını kapsar. Ders 29 deploy edilmiş moderation'ı kapsar. Ders 30 mevcut dual-use capability kanıtıyla kapanır.

## Kullan

`code/main.py` üç-katmanlı bir moderation harness'ı inşa eder: input moderator (keyword + kategori skoru), output moderator (output'ta aynı classifier), custom moderator (alan kuralları). Input'ları çalıştırabilir ve hangi katmanın neyi yakaladığını gözlemleyebilirsin.

## Yayınla

Bu ders `outputs/skill-moderation-stack.md` üretir. Bir deployment verildiğinde, bir moderation stack konfigürasyonu önerir: input'ta hangi classifier, output'ta hangi, hangi custom kurallar ve edge case'ler için hangi yargıç.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Üç katmandan iyi huylu, sınırda ve zararlı bir input çalıştır. Her biri için hangi katmanın ateşlendiğini raporla.

2. Harness'ı spesifik bir kategori üzerinde Perspective-API-tarzı toxicity puanlama ile genişlet. Eşik davranışını kategori skoruyla karşılaştır.

3. OpenAI Moderation API docs'larını ve Llama Guard 3 kategori listesini oku. Her OpenAI kategorisini en yakın Llama Guard kategorilerine eşle. Temiz şekilde eşleşmeyen üç kategori tanımla.

4. Bir kod-asistan deployment'ı (örn. GitHub Copilot) için bir moderation stack tasarla. En ilgili ve en az ilgili kategorileri tanımla ve custom kurallar öner.

5. Azure Content Moderator Şubat 2027'de emekli olur. Azure AI Content Safety'ye bir geçiş planla. Geçişin en yüksek riskli elementini tanımla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| OpenAI Moderation | "omni-moderation-latest" | Kısmi multimodal destekle GPT-4o-tabanlı 13-kategori (text) classifier |
| Perspective API | "Google Jigsaw toxicity" | Pre-LLM-era toxicity puanlama baseline'ı |
| Llama Guard | "MLCommons 14-kategori" | Meta'nın tehlike classifier'ı (v3: 8B text, 8 dil; v4: 12B multimodal) |
| Input moderation | "üretim öncesi filtre" | Model çağrısı öncesi kullanıcı prompt'unda classifier |
| Output moderation | "üretim sonrası filtre" | Teslim öncesi model çıktısında classifier |
| Custom moderation | "alan kuralları" | Deployment-özgü kurallar (regex, allowlist, policy) |
| Katmanlı moderation | "üç katmanın hepsi" | Standart üretim deployment deseni |

## İleri Okuma

- [OpenAI Moderation API docs](https://platform.openai.com/docs/api-reference/moderations) — omni-moderation endpoint
- [Meta PurpleLlama + Llama Guard](https://github.com/meta-llama/PurpleLlama) — Llama Guard repo
- [Google Jigsaw Perspective API](https://perspectiveapi.com/) — toxicity puanlama
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/) — Azure yedeği
