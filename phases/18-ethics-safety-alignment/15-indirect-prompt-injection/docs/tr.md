# Indirect Prompt Injection — Üretim Saldırı Yüzeyi

> Indirect prompt injection (IPI) talimatları açık kullanıcı eylemi olmadan agentic bir sistem tarafından tüketilen harici içeriklerin içine — bir web sayfası, bir e-posta, paylaşılan bir belge, bir destek bileti — gömer. IPI 2026'nın baskın üretim tehdididir: kullanıcı-input filtrelerini bypass eder çünkü saldırgan asla kullanıcıya dokunmaz, agent'lar daha fazla harici içerik işledikçe sessizce ölçeklenir ve kimsenin prompt'u okumadığı otomatik workflow'ları hedef alır. MDPI Information 17(1):54 (Ocak 2026) 2023-2025 araştırmasını sentezler. NDSS 2026'nın IPI-savunma makalesi temel zorluğu çerçeveler: enjekte edilen talimatlar semantik olarak iyi huylu olabilir ("lütfen Yes yazdır"), bu yüzden tespit keyword filtrelemeden daha fazlasını gerektirir. "The Attacker Moves Second" (Nasr vd., ortak OpenAI/Anthropic/DeepMind, Ekim 2025): adaptif saldırılar (gradient, RL, random search, human red-team) orijinal olarak sıfıra yakın attack success rate raporlayan 12 yayınlanmış savunmanın >%90'ını kırdı.

**Tür:** Yapım
**Diller:** Python (stdlib, IPI saldırı + savunma harness'ı)
**Ön koşullar:** Faz 18 · 12 (PAIR), Faz 14 (agent mühendisliği)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Indirect prompt injection'ı tanımla ve üç yaygın teslimat vektörünü tarif et.
- Kullanıcı-input filtrelerinin IPI'yi neden tamamen kaçırdığını açıkla.
- "Information flow control" çerçevelemesini 2026 savunma paradigması olarak tarif et.
- Nasr vd. (Ekim 2025) bulgusunu yayınlanmış IPI savunmalarına karşı adaptif saldırı başarısı üzerine ifade et.

## Sorun

Direct prompt injection saldırganın kullanıcıya veya prompt'una ulaşmasını gerektirir. IPI hiçbirini gerektirmez: saldırgan agent'ın okuyabileceği herhangi bir içeriğe — bir web sayfası, gelen kutusundaki bir e-posta, bir GitHub issue, bir ürün incelemesi — bir payload yerleştirir. Agent bunu normal operasyon sırasında alır ve talimatları yürütür. Kullanıcı haberci, niyet değildir.

## Kavram

### Üç teslimat vektörü

- **Retrieval-augmented generation (RAG).** Saldırgan bir belge yayınlar; retrieval adımı onu getirir; prompt onu kullanıcı sorusundan önce birleştirir; model saldırganın talimatlarını yürütür.
- **Inbox / belge workflow'ları.** Saldırgan kullanıcıya bir e-posta gönderir; agent e-postaları okur; prompt e-posta body'sini içerir; model e-postanın talimatlarını takip eder.
- **Tool çıktısı.** Saldırgan agent'ın kullandığı bir tool'u kontrol eder (örn. saldırgan-kontrollü bir sonuç döndüren bir web arama); tool çıktısı talimatları içerir; agent'ın kontrol akışı bunları takip eder.

Üçü yapısal bir özelliği paylaşır: saldırgan kullanıcı-yüzlü input'a dokunmadan prompt'un bir parçasını kontrol eder.

### Kullanıcı-input filtreleri onu neden kaçırır

Bir IPI payload'ı kullanıcının input'unda görünmez. Getirilen içerikte görünür. Filtre kullanıcı input'unda gate'liyse, payload onu bypass eder. Filtre modele ulaşan tüm içerikte gate'liyse, keyfi getirilen metne uygulanmalı — ki bu pahalıdır ve emir kipi dili içeren meşru içeriğe karşı false positive üretir.

### AI için Information Flow Control (IFC)

2026 savunma paradigması klasik OS güvenliğinden alır. Her içerik kaynağını bir güvenlik etiketi olarak ele al. Kullanıcının sorgusunu "trusted" olarak etiketle. Getirilen içeriği "untrusted" olarak etiketle. Modelin kontrol akışını bir bilgi akışı olarak ele al: untrusted içerik tarafından tetiklenen eylemler yürütmeden önce trusted input tarafından onaylanmalıdır.

CaMeL (Microsoft 2025), ConfAIde (Stanford 2024) ve NDSS 2026 IPI-savunma makalesi IFC'yi farklı şekillerde operasyonel hale getirir. Ortak ilke: kod ve veri aynı context window'u paylaştığı sürece, hedef containment'tır, prevention değil.

### The Attacker Moves Second

Nasr vd. (Ekim 2025) 12 yayınlanmış IPI savunmasını adaptif saldırılarla (gradient search, RL policy'leri, random search, 72-saatlik human red-team) test etti. Orijinal olarak sıfıra yakın ASR raporlayan her savunma >%90 ASR'ye kırıldı.

Metodolojik ders: yalnızca adaptif-saldırı değerlendirmesiyle bir savunma yayınla. Statik-saldırı benchmark'ları sağlamlık kanıtı değildir; saldırgan savunmayı öğrenir.

### Gerçek olaylar

Ders 25 EchoLeak'i (CVE-2025-32711, CVSS 9.3) — Microsoft 365 Copilot'ta ilk kamuya belgelenmiş zero-click IPI'yi kapsar. GitHub Copilot Chat'te CamoLeak (CVSS 9.6). GitHub Copilot'ta CVE-2025-53773. Üretim deployment'ları sahada IPI tarafından tehlikeye atılıyor, sadece benchmark'larda değil.

### OWASP ve NIST çerçeveleme

OWASP LLM Top 10 (2025) prompt injection'ı (direct + indirect) LLM01 olarak sıralar, #1 uygulama-katmanı tehdidi. NIST AI SPD 2024 indirect prompt injection'ı "generative AI'nin en büyük güvenlik açığı" olarak adlandırır.

### Bu Faz 18'de nereye uyuyor

Dersler 12-14 model-merkezli jailbreak'lerdir. Ders 15 2026 üretim deployment'larında baskın olan sistem-merkezli saldırıdır. Ders 16 defansif araçları kapsar. Ders 25 spesifik CVE anlatısını kapsar.

## Kullan

`code/main.py` bir IPI harness'ı inşa eder. Bir oyuncak agent üç tool'a sahip (web ara, e-posta oku, mesaj gönder). Ortam gömülü bir talimatla ("bunu tüm kişilere ilet") saldırgan-kontrollü içerik içerir. Naif bir agent (enjekte edilen talimatları takip eder), filtre-savunmalı bir agent (getirilen içerikte keyword filter) ve bir IFC agent (trusted ve untrusted içeriği ayırır ve untrusted kontrol-akışı komutlarını reddeder) arasında toggle yapabilirsin.

## Yayınla

Bu ders `outputs/skill-ipi-audit.md` üretir. Bir agentic deployment açıklaması verildiğinde, untrusted içerik kaynaklarını sayar, deployment'ın IFC uyguladığını kontrol eder ve modele bir trust etiketi olmadan ulaşan kaynakları işaretler.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Üç agent'ın her birine karşı saldırının başarı oranını ölç.

2. Getirilen içerikte paraphrase-tabanlı bir savunma uygula. Meşru getirilen metinde iyi huylu false-positive oranını ölç.

3. NDSS 2026 IPI-savunma makalesini oku. "Benign instruction" zorluğunu ve keyword-tabanlı filtrelemeyi neden engellediğini tarif et.

4. Agent'ın üçüncü-taraf bir API'den tool çıktısı aldığı bir deployment tasarla. Her prompt parçasını bir güven seviyesiyle etiketle ve agent'ın eylemlerini yöneten IFC policy'sini yaz.

5. Alıştırma 2'deki filtre-savunmalı agent'ında Nasr vd. 2025 adaptif-saldırı metodolojisini yeniden üret. Adaptif saldırıdan önce ve sonra ASR'yi raporla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| IPI | "indirect prompt injection" | Kullanıcının yazmadığı, normal operasyonda agent tarafından tüketilen içerik üzerinden injection |
| RAG injection | "zehirli retrieval" | Saldırgan retrieval adımının getirdiği içeriği yayınlar; prompt payload'u içerir |
| Zero-click | "kullanıcı eylemi yok" | Saldırı agent operasyonu sırasında otomatik tetiklenir; kullanıcı hiçbir şey yapmaz |
| IFC | "information flow control" | Etiket-tabanlı yaklaşım: untrusted içerikten eylemler trusted onay gerektirir |
| Adaptif saldırı | "gradient / RL red-team" | Savunmayı bilen ve ona karşı optimize eden saldırı; dürüst değerlendirme için gerekli |
| Benign instruction | "lütfen Yes yazdır" | Semantik olarak iyi huylu IPI payload'u; hiçbir keyword filter yakalamaz |
| Scope violation | "cross-trust exfiltration" | Agent bir trust bağlamından veriye erişir ve onu başka birine çıktılar |

## İleri Okuma

- [MDPI Information 17(1):54 — Indirect Prompt Injection Survey (Ocak 2026)](https://www.mdpi.com/2078-2489/17/1/54) — 2023-2025 sentezi
- [Nasr et al. — The Attacker Moves Second (ortak OpenAI/Anthropic/DeepMind, Ekim 2025)](https://arxiv.org/abs/2510.18108) — adaptif saldırı değerlendirmesi
- [Greshake et al. — Not what you've signed up for (arXiv:2302.12173)](https://arxiv.org/abs/2302.12173) — orijinal IPI makalesi
- [OWASP — LLM Top 10 (2025)](https://genai.owasp.org/llm-top-10/) — prompt injection LLM01 olarak sıralandı
