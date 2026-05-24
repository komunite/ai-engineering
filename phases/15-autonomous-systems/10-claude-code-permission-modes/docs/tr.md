# Otonom Agent Olarak Claude Code: Permission Mode'ları ve Auto Mode

> Claude Code yedi permission mode'unu açığa çıkarır. "plan" her aksiyondan önce sorar, "default" yalnızca riskli olanlar için sorar, "acceptEdits" dosya write'larını otomatik onaylar ama shell yürütmeyi hâlâ doğrular ve "bypassPermissions" her şeyi onaylar. Auto Mode (24 Mart 2026) aksiyon başına onayı iki-aşamalı paralel bir safety classifier ile değiştirir: tek-token hızlı kontrol her aksiyonda çalışır; işaretlenen aksiyonlar bir chain-of-thought derin incelemeyi tetikler. Aksiyon bütçeleri `max_turns` ve `max_budget_usd` ile zorlanır. Auto Mode bir araştırma preview'u olarak yayınlandı — Anthropic, classifier'ın tek başına yeterli olmadığını açıkça belirtti.

**Tür:** Öğrenim
**Diller:** Python (stdlib, iki-aşamalı classifier simülatörü)
**Ön koşullar:** Faz 15 · 01 (Uzun-horizon agent'lar), Faz 15 · 09 (Coding-agent manzarası)
**Süre:** ~45 dakika

## Sorun

Makinendeki otonom bir coding agent ayrı bir güvenlik kategorisidir. Saldırı yüzeyi agent'ın ulaşabildiği her şeydir — dosya sistemi, network, credential'lar, clipboard, herhangi bir browser tab, herhangi bir açık terminal. Bruce Schneier ve diğerleri bunu alenen işaretledi: computer-use agent'ları chatbot'ların bir "özellik güncellemesi" değil, yeni bir risk profili olan yeni bir tool türüdür.

Claude Code'un permission sistemi Anthropic'in cevabıdır. Bir "otonom / otonom değil" anahtarı yerine, bir kapasite merdiveni üzerinde yedi mode vardır: plan → default → acceptEdits → … → bypassPermissions. Her mode hız ile aksiyon başına inceleme arasında farklı bir trade-off'tur. Auto Mode (Mart 2026), classifier'ın safe olarak yargıladığı aksiyonlar için onayı kullanıcının kritik yolundan çıkaran ve classifier'ın işaretlediği aksiyonlar için bir inceleme katmanı koruyan iki-aşamalı bir classifier ekler.

Mühendislik sorusu: bu sistem neyi yakalıyor, neyi kaçırıyor ve belirli bir görev hangi mode'u hak ediyor?

## Kavram

### Yedi permission mode'u

| Mode | Davranış | Ne zaman kullanılır |
|---|---|---|
| `plan` | Agent bir plan önerir; kullanıcı tüm planı onaylar; her aksiyon yürütmeden önce incelenir | Bilinmeyen görev; prod-bitişik kod; bir repo'da agent'ı ilk kez kullanma |
| `default` | Agent aksiyonları çalıştırır; herhangi "riskli" bir aksiyon (shell exec, yıkıcı işlemler, network çağrıları) için kullanıcıya prompt'lar | Çoğu interaktif coding oturumu |
| `acceptEdits` | Dosya write'ları otomatik onaylar; shell exec ve network çağrıları hâlâ prompt'lar | Birçok dosya boyunca refactoring pass'i |
| `acceptExec` | Shell komutları küratörlü bir allowlist içinde otomatik onaylar; write'lar otomatik onaylar | Her shell komutunun `npm test` veya benzeri olduğu sıkı iç döngüler |
| `autoMode` | İki-aşamalı safety classifier; işaretlenen aksiyonlar incelemeye yükselir | Kısıtlı bir workspace'te uzun-horizon gözetimsiz koşular |
| `yolo` | Çoğu prompt'u atlar; hâlâ tool allowlist / denylist çalıştırır | Geçici sandbox'lar, CI işleri, araştırma script'leri |
| `bypassPermissions` | Her şeyi onaylar | "Yalnızca atmaya hazır olduğun geçici container'ların içinde" olarak belgelenmiş |

(Yukarıdaki adlar kamuya açık Claude Code dokümanlarıyla eşleşir; "yolo" izin verici orta yer için informal kısaltmadır.)

### Bir sayfada Auto Mode

Auto Mode (24 Mart 2026'da başlatıldı), aksiyon başına onayı bir modele delege eden ilk permission mode'udur. Yapı:

1. **Aşama 1 — tek-token classifier.** Önerilen her aksiyonda çalışır. Ucuz. "safe" veya "flag" döner. Ana agent döngüsüyle paralel çalışacak şekilde tasarlanmış, böylece onaylanan aksiyonlar bir kuyrukta oturmaz.
2. **Aşama 2 — ikincil politika/safety incelemesi.** Yalnızca işaretlenen aksiyonlarda çalışır. Aksiyon, oturumun mevcut state'i ve beyan edilen görev üzerinde odaklı bir politika ve safety değerlendirmesi yapar. Güven düşükse kullanıcı HITL'sine yükseltir.

Bütçe kontrolleri classifier'ın yanında oturur:

- `max_turns` — bir oturumda toplam iterasyon.
- `max_budget_usd` — oturumu iptal eden dolar tavanı.
- tool başına aksiyon-sayım limitleri (N'den fazla `WebFetch` çağrısı yok, vb.).

### Sistemin yakaladığı

- Enjekte edilen talimatın bilinen-riskli bir aksiyon şekline eşlendiği tool input'larına doğrudan prompt injection.
- Tekrarlı tool döngüleri — classifier aksiyon N+1'in aksiyon N ile neredeyse aynı olduğunu görebilir, üst üste beş kez.
- Aksi takdirde dosya-edit-yalnız bir oturumda açıkça kapsam-dışı shell komutları.

### Sistemin kaçırabileceği

- **İncelikli prompt injection** tek bir işaretlenmiş aksiyon üretmeden davranışı modüle eden. Indirect prompt injection tam olarak yamalanabilir bir açık değildir (OpenAI preparedness başkanı, 2025, browser agent'lar üzerine — Ders 11'e bak).
- **Anlamsal-seviye yanlış davranış.** Her bireysel aksiyon safe görünürken oluşturulan trajectory zararlı olabilir. Classifier aksiyonu yargılar; kullanıcının niyetini yeniden türetmez.
- **Meşru kanallar üzerinden exfiltration.** Sahip olduğun bir dosyaya veri yazmak, sonra public bir repo'ya `git push` etmek, kompozisyonu problem olan izin verilen aksiyonlar dizisidir.

### Araştırma preview çerçevesi

Anthropic Auto Mode'u bir araştırma preview olarak yayınladı. Dokümantasyon classifier'ın bir çözüm değil bir katman olduğu konusunda açıktır: kullanıcılardan Auto Mode'u bütçeler, allowlist'ler, izole edilmiş workspace'ler ve trajectory audit'leri (Ders 12-16) ile birleştirmeleri beklenir. Preview çerçevesi aynı zamanda belgelenmiş değerlendirme-vs-deployment farkını da yansıtır (Ders 1) — offline eval'leri geçen bir classifier, kullanıcı bağlamının belirsiz olduğu gerçek bir oturumda farklı davranabilir.

### Bu merdiven workflow'unda nerede yaşar

- Bilinmeyen görev: `plan` ile başla. Planı okumak kötü bir koşuyu rollback etmekten ucuzdur.
- Bilinen refactor: `acceptEdits` çok onay tıklamasını kurtarır.
- Gözetimsiz arka plan koşusu: blast radius'unu ölçtüğün bir workspace içinde yalnızca `autoMode` (credential yok, production mount yok, opt-in etmediğin egress yok).
- Geçici container'lar: container ve credential'ları atılabilirse ancak ve ancak `yolo` / `bypassPermissions` kabul edilebilir.

## Kullan

`code/main.py` iki-aşamalı classifier'ı simüle eder. Aşama 1 önerilen aksiyonlar üzerinde ucuz bir keyword kuralıdır; Aşama 2 daha yavaş çoklu-kurallı bir inceleyicidir. Driver kısa sentetik bir trajectory (safe aksiyonlar, bir prompt-injection denemesi, bir tekrarlı döngü) besler ve classifier'ın nerede yakaladığı ve nerede kaçırdığını gösterir.

## Yayınla

`outputs/skill-permission-mode-picker.md`, bir görev tanımını doğru permission mode'u, bütçe tavanları ve gerekli izolasyon ile eşleştirir.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Hangi sentetik aksiyon tipi Aşama 1 tarafından asla işaretlenmez ama her zaman Aşama 2 tarafından yakalanır? Hangisi hiçbiri tarafından yakalanmaz?

2. Aşama 1 kural setini belirli bir bilinen-kötü şekli (örn. `curl $ATTACKER/exfil`) yakalayacak şekilde genişlet. Benign-aksiyon örneklemde false-positive oranını ölç.

3. Anthropic'in "How the agent loop works" dokümanını oku. `default` mode'da agent'ın varsayılan olarak dokunduğu her harici state'i listele. `autoMode`'u gözetimsiz çalıştırmadan önce hangilerini ayrı olarak gate etmen gerekir?

4. 24 saatlik gözetimsiz koşu bütçesi tasarla: `max_turns`, `max_budget_usd`, tool başına tavanlar, allowlist'ler. Her sayıyı gerekçelendir.

5. Her bireysel aksiyonun Aşama 1 ve Aşama 2 tarafından onaylandığı ama oluşturulan davranışın misaligned olduğu bir trajectory tarif et. (Ders 14 kill switch'lerin ve canary token'ların bunu nasıl ele aldığını kapsar.)

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Permission mode | "Agent ne kadar şey yapabilir" | Aksiyon başına onayı kontrol eden yedi adlandırılmış politikadan biri |
| plan mode | "Her şeyden önce sor" | Agent bir plan yazar; kullanıcı yürütmeden önce onaylar |
| acceptEdits | "Dosya yazmasına izin ver" | Dosya write'ları otomatik onaylar; shell exec hâlâ prompt'lar |
| autoMode | "Otomatik onaylar" | İki-aşamalı safety classifier; işaretlenen aksiyonlar yükselir |
| bypassPermissions | "Tam YOLO" | Her şeyi onaylar; geçici container'lar için tasarlanmış |
| Aşama 1 classifier | "Hızlı token kontrolü" | Önerilen aksiyon üzerinde tek-token kural; paralel çalışır |
| Aşama 2 classifier | "Derin inceleme" | İşaretlenen aksiyonlar üzerinde chain-of-thought akıl yürütme |
| Araştırma preview | "GA değil" | Failure mode'u hâlâ haritalandırılan özellikler için Anthropic çerçevesi |

## İleri Okuma

- [Anthropic — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — permission mode'ları, bütçeler, aksiyon formatı.
- [Anthropic — Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) — yönetilen-servis yürütme modeli.
- [Anthropic — Claude Code product page](https://www.anthropic.com/product/claude-code) — özellik yüzeyi ve Auto Mode duyurusu.
- [Anthropic — Claude's Constitution (January 2026)](https://www.anthropic.com/news/claudes-constitution) — classifier yargılarını şekillendiren reason-based katman.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — uzun-horizon permission tasarımı üzerine içeriden perspektif.
