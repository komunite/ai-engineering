# Browser Agent'lar ve Uzun-Horizon Web Görevleri

> ChatGPT agent (Temmuz 2025) Operator ve deep research'ü tek bir browser/terminal agent'ında birleştirdi ve BrowseComp SOTA'sını %68.9'a koydu. OpenAI Operator'ı 31 Ağustos 2025'te kapattı — ürün katmanında konsolidasyon. Anthropic'in Vercept satın alımı, OSWorld'de Claude Sonnet'i %15'in altından %72.5'e taşıdı. WebArena-Verified (ServiceNow, ICLR 2026), orijinal WebArena'daki 11.3 yüzde puanlık false-negative oranını düzeltti ve 258-görevli Hard altküme yayınladı. Rakamlar gerçek. Saldırı yüzeyi de öyle: OpenAI'ın preparedness başkanı, browser agent'lara indirect prompt injection'ın "tam yamalanabilen bir bug olmadığını" alenen belirtti. Belgelenmiş 2025-2026 saldırılar: Tainted Memories (Atlas CSRF), HashJack (Cato Networks) ve Perplexity Comet'te tek-tıklama hijack'ler.

**Tür:** Öğrenim
**Diller:** Python (stdlib, indirect prompt-injection saldırı yüzeyi modeli)
**Ön koşullar:** Faz 15 · 10 (Permission mode'ları), Faz 15 · 01 (Uzun-horizon agent'lar)
**Süre:** ~45 dakika

## Sorun

Bir browser agent, untrusted content okuyan ve sonuçlu aksiyonlar alan uzun-horizon bir agent'tır. Agent'ın ziyaret ettiği her sayfa, kullanıcının yazmadığı bir input'tur. Her sayfadaki her form potansiyel bir komut kanalıdır. 2025-2026 saldırı corpus'u bunun hipotetik olmadığını gösterir: Tainted Memories bir saldırgana hazırlanmış bir sayfa üzerinden agent'ın memory'sine kötü amaçlı talimatlar bağlamasına izin verir; HashJack komutları agent'ın ziyaret ettiği URL fragment'lerinde gizler; Perplexity Comet hijack'leri tek tıkla vurdu.

Savunma resmi rahatsız edici. OpenAI'ın preparedness başkanı sessiz kısmı yüksek sesle söyledi: indirect prompt injection "tam yamalanabilen bir bug değil." Bunun nedeni saldırının agent'ın okuma-vs-eyleme sınırında yaşamasıdır, ki bu mimari olarak bulanıktır — modelin okuduğu her token ilkesel olarak bir talimat olarak okunabilir.

Bu ders saldırı yüzeyini adlandırır, benchmark manzarasını (BrowseComp, OSWorld, WebArena-Verified) adlandırır ve minimal bir indirect-prompt-injection senaryosunu modeller, böylece Ders 14 ve 18'deki gerçek savunmalar hakkında akıl yürütebilirsin.

## Kavram

### 2026 manzarası, sistem başına bir paragraf

**ChatGPT agent (OpenAI).** Temmuz 2025'te başlatıldı. Operator'ı (tarama) ve Deep Research'ü (çoklu-saat araştırma) birleştirir. 31 Ağustos 2025'te bağımsız Operator'ı kapattı. BrowseComp'ta %68.9 ile SOTA; OSWorld ve WebArena-Verified'da güçlü rakamlar.

**Claude Sonnet + Vercept (Anthropic).** Anthropic'in Vercept satın alımı computer-use kapasitelerine odaklandı. OSWorld'de Claude Sonnet'i %15'in altından %72.5'e taşıdı. Claude Computer Use bir tool API olarak yayınlanır.

**Browser Use ile Gemini 3 Pro (DeepMind).** Browser Use entegrasyonu computer-use kontrollerini yayınlar; FSF v3 (Nisan 2026, Ders 20) otonomiyi özellikle ML R&D domain'inde izler.

**WebArena-Verified (ServiceNow, ICLR 2026).** İyi-belgelenmiş bir problemi düzeltir: orijinal WebArena ~%11.3 false-negative oranına sahipti (aslında çözülen ama failed olarak işaretlenen görevler). Verified yayını insan-küratörlü başarı kriterleriyle yeniden not verir ve 258-görevli bir Hard altküme ekler (ICLR 2026 makalesi, openreview.net/forum?id=94tlGxmqkN).

### BrowseComp vs OSWorld vs WebArena

| Benchmark | Neyi ölçer | Horizon |
|---|---|---|
| BrowseComp | Zaman baskısı altında açık web'de belirli gerçekleri bulma | dakikalar |
| OSWorld | Tam bir desktop'u işleten agent (fare, klavye, shell) | onlarca dakika |
| WebArena-Verified | Simüle edilmiş sitelerde işlemsel web görevleri | dakikalar |
| Hard altküme | Çoklu-sayfa state geçişleri olan WebArena-Verified görevleri | onlarca dakika |

Farklı eksenler. Yüksek bir BrowseComp skoru agent'ın gerçekleri bulduğunu söyler; bir uçuş rezervasyonu yapabileceğini söylemez. OSWorld skoru "desktop'umda çalışıyor mu"ya daha yakın. WebArena-Verified "bir flow'u bitirebilir mi"ye daha yakın. Herhangi bir üretim kararı görev dağılımına uyan benchmark'a ihtiyaç duyar.

### Saldırı yüzeyi, adlandırılmış

1. **Indirect prompt injection.** Untrusted sayfa içeriği talimatlar içerir. Agent onları okur. Agent onları yürütür. Kamuya açık örnekler: 2024 Kai Greshake vd., 2025 Tainted Memories makalesi, 2026 HashJack (Cato Networks).
2. **URL fragment / query injection.** Crawl edilen URL'nin `#fragment` veya query string'i komutlar içerir. Asla görünür şekilde render edilmez; hâlâ agent'ın context'i içinde.
3. **Memory-binding saldırıları.** Sayfa agent'a kalıcı bir memory yazmasını söyler (Ders 12 durable state'i kapsar). Sonraki oturum, memory görünür bir tetikleyici olmadan payload'u ateşler.
4. **Authenticated session'larda CSRF şekilli saldırılar.** Tainted Memories sınıfı: agent bir yerde login olmuş; saldırganın sayfası agent'ın kullanıcının cookie'leriyle yürüttüğü state-değiştiren request'leri yayınlar.
5. **Tek-tıklama hijack.** Görsel olarak masum bir button agent'ın takip ettiği bir payload'a biner. Comet sınıfı.
6. **Agent'ın host yüzeyinde Content-Security-Policy delikleri.** Rendering ve tool katmanları kendi başlarına saldırı vektörleri olabilir; browser-in-a-browser-agent yığını geniştir.

### Neden "tam yamalanabilir değil"

Saldırı agent'ın kapasitesine izomorftur. Agent işini yapmak için untrusted content okumalıdır. Agent'ın okuduğu herhangi bir içerik talimatlar içerebilir. Agent'ın takip ettiği herhangi bir talimat kullanıcının gerçek isteğiyle misaligned olabilir. Savunmalar (güven sınırları, classifier'lar, tool allowlist'leri, sonuçlu aksiyonlarda HITL) saldırının maliyetini yükseltir ve blast radius'u azaltır. Sınıfı kapatmazlar.

Bu Lob teoremiyle aynı akıl yürütme desenidir (Ders 8): agent bir sonraki token'ın safe olduğunu kanıtlayamaz; yalnızca unsafe token'ların daha tespit edilebilir olduğu bir sistem kurabilir.

### Aslında yayınlanan savunma duruşu

- **Okuma / yazma sınırı.** Okuma asla sonuçlu değildir. Yazma (form gönderme, içerik post etme, yan etkili bir tool çağırma), başlatıcı içerik güven sınırının dışından geldiyse taze insan onayı gerektirir.
- **Görev başına tool allowlist'i.** Agent göz atabilir; o tool görev için açıkça etkinleştirilmedikçe bir wire transfer başlatamaz. Ders 13 bütçeleri kapsar.
- **Session izolasyonu.** Browser agent oturumları yalnızca kapsamlı credential'larla çalışır. Production auth yok, kişisel email yok. Audit için her HTTP request'inin log'ları tutulur.
- **Content sanitizer.** Fetch edilen HTML, model context'ine birleştirilmeden önce bilinen-kötü desenlerden arındırılır. (Kolay saldırıları azaltır; sofistike payload'ları durdurmaz.)
- **Sonuçlu aksiyonlarda HITL.** Propose-then-commit deseni (Ders 15).
- **Memory üzerinde canary token'lar.** Bir memory girdisi ateşlenirse kullanıcı görür (Ders 14).

## Kullan

`code/main.py` üç sentetik sayfaya karşı küçük bir browser-agent koşusunu modeller. Bir sayfa benign, biri görünür metinde direct prompt-injection blob'una sahip, biri URL-fragment injection'a sahip (görünür değil ama agent'ın context'i içinde). Script (a) naive bir agent'ın ne yapacağını, (b) bir okuma/yazma sınırının neyi yakaladığını, (c) bir sanitizer'ın neyi yakaladığını, (d) hiçbirinin neyi yakalamadığını gösterir.

## Yayınla

`outputs/skill-browser-agent-trust-boundary.md`, önerilen bir browser-agent deployment'ını kapsar: hangi güven zonlarına dokunduğu, neyi yazma yetkisine sahip olduğu ve ilk koşudan önce hangi savunmaların hazır olması gerektiği.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Sanitizer'ın yakaladığı ama okuma/yazma sınırının yakalamadığı saldırıyı ve yalnızca okuma/yazma sınırının yakaladığı saldırıyı belirle.

2. Sanitizer'ı bir HashJack tarzı URL-fragment injection sınıfını tespit edecek şekilde genişlet. Meşru fragment'leri olan benign URL'lerde false-positive oranını ölç.

3. Bildiğin bir gerçek browser-agent workflow'unu (örn. "uçuş rezerve et") seç. Her read ve her write'ı listele. Hangi write'ların HITL gerektirdiğini ve nedenini işaretle.

4. WebArena-Verified ICLR 2026 makalesini oku. Orijinal WebArena'nın puanlamasının güvenilmez olduğu bir görev kategorisini belirle ve Verified altkümesinin onu nasıl çözdüğünü açıkla.

5. Bir browser-agent ortamı için bir memory canary tasarla. Ne, nerede saklayacaksın ve neyin alarmı tetiklediğini?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Indirect prompt injection | "Kötü sayfa metni" | Agent'ın okuduğu bir sayfadaki untrusted content, agent'ın yürüttüğü talimatlar içerir |
| Tainted Memories | "Memory saldırısı" | Agent saldırgan-sağlamalı bir talimatı durable memory'ye yazar; sonraki oturumda tetiklenir |
| HashJack | "URL fragment saldırısı" | URL fragment / query string'inde gizli payload, agent'ın context'inde ama görünür render edilmez |
| Tek-tıklama hijack | "Kötü button" | Görünür affordance, agent'ın yürüttüğü bir follow-on payload'a biner |
| BrowseComp | "Web arama benchmark'ı" | Açık web'de belirli gerçekleri bulma; dakika-ölçeği horizon |
| OSWorld | "Desktop benchmark'ı" | Tam OS kontrolü; çoklu-adımlı GUI görevleri |
| WebArena-Verified | "Düzeltilmiş web-görev benchmark'ı" | ServiceNow'un Hard altkümesi ile yeniden notlandırılmış WebArena |
| Okuma/yazma sınırı | "Yan-etki gate'i" | Okuma asla sonuçlu değil; içerik güven-dışıysa yazma taze onay gerektirir |

## İleri Okuma

- [OpenAI — Introducing ChatGPT agent](https://openai.com/index/introducing-chatgpt-agent/) — Operator ve deep research birleşimi; BrowseComp SOTA.
- [OpenAI — Computer-Using Agent](https://openai.com/index/computer-using-agent/) — Operator soyu ve ChatGPT agent'a dönüşen mimari.
- [Zhou et al. — WebArena](https://webarena.dev/) — orijinal benchmark.
- [WebArena-Verified (OpenReview)](https://openreview.net/forum?id=94tlGxmqkN) — ICLR 2026 düzeltilmiş altküme makalesi.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — computer-use agent'lar için saldırı-yüzey tartışmasını içerir.
