# Human-in-the-Loop: Propose-Then-Commit

> HITL üzerine 2026 konsensüsü spesifiktir. "Agent sorar, kullanıcı Onayla'yı tıklar" değildir. Propose-then-commit'tir: önerilen aksiyon idempotency key ile durable bir store'a persist edilir; intent, data lineage, dokunulan permission'lar, blast radius ve rollback planı ile bir reviewer'a yüzeye çıkarılır; yalnızca pozitif acknowledgement'tan sonra commit edilir; yürütmeden sonra yan etkinin gerçekten gerçekleştiğini doğrulamak için verify edilir. LangGraph'ın `interrupt()`'ı artı PostgreSQL checkpointing'i, Microsoft Agent Framework'ün `RequestInfoEvent`'i ve Cloudflare'ın `waitForApproval()`'u hepsi aynı şekli uygular. Kanonik failure mode rubber-stamp onayıdır: "Onayla?" inceleme olmadan tıklanır. Belgelenmiş azaltma açık bir checklist ile challenge-and-response'tur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, idempotency ile propose-then-commit state machine)
**Ön koşullar:** Faz 15 · 12 (Durable execution), Faz 15 · 14 (Tripwire'lar)
**Süre:** ~60 dakika

## Sorun

Bir agent bir aksiyon alır. Kullanıcı karar vermek zorundadır: onayla ya da onaylama. Karar anlıksa, muhtemelen bir inceleme değildir. Karar yapılandırılmışsa, yavaştır ama güvenilirdir. Mühendislik sorusu yapılandırılmış bir incelemeyi en az direnç yolu nasıl yapılacağıdır.

2023 dönemi HITL deseni senkron bir prompt'tu: "Agent X'e Y body'sinde email göndermek istiyor — onayla?" Kullanıcı Onayla'ya tıklar. Herkes sistemin safe olduğunu hisseder. Pratikte bu yüzey yoğun şekilde rubber-stamp'lanır: kullanıcılar hızlı onaylar, onaylar az şey öngörür ve agent yanlış gittiğinde, audit izi kullanıcının hatırlayamayacağı uzun bir onay geçmişi gösterir.

2026 deseni — propose-then-commit — HITL'yi durable bir substrate üzerine taşır, yapılandırılmış metadata iliştirir ve pozitif commit gerektirir. Her yönetilen agent SDK'sı bir versiyon yayınlar: LangGraph `interrupt()`, Microsoft Agent Framework `RequestInfoEvent`, Cloudflare `waitForApproval()`. API isimleri farklıdır; şekil değildir.

## Kavram

### Propose-then-commit state machine

1. **Propose.** Agent önerilen bir aksiyon üretir. Durable bir store'a persist edilir (PostgreSQL, Redis, Durable Object). Şunları içerir:
   - intent (agent bunu neden yapıyor)
   - data lineage (bu öneriye hangi kaynak götürdü)
   - dokunulan permission'lar (hangi scope'lar / dosyalar / endpoint'ler)
   - blast radius (en kötü durum nedir)
   - rollback planı (commit edilirse, nasıl geri alırız)
   - idempotency key (öneri başına unique; yeniden gönderim aynı kaydı döner)
2. **Surface.** Reviewer tüm metadata ile öneriyi görür. Reviewer bir kişidir (kendini inceleyen agent değil).
3. **Commit.** Pozitif acknowledgement. Aksiyon yürütülür.
4. **Verify.** Yürütmeden sonra, yan etki geri okunur ve doğrulanır. Verify adımı başarısız olursa, sistem bilinen kötü bir state'tedir ve alerting devreye girer.

### Idempotency key

Idempotency key olmadan, geçici bir failure sonrası retry onaylanmış bir aksiyonu çift-yürütebilir. Somut örnek: kullanıcı "A'dan B'ye 100 $ transfer et"i onaylar. Network glitch yaşar. Workflow retry yapar. Kullanıcı bir kez onayladı ama transfer iki kez yürütülür. Idempotency key onayı tek, unique bir yan etkiye bağlar; ikinci yürütme bir no-op'tur.

Bu, Stripe ve AWS API'lerinin kullandığı aynı idempotency desenidir. Bunu agent onayları için yeniden kullanmak Microsoft Agent Framework dokümanlarında açıktır.

### Durability: onaylar process'lerden neden daha uzun yaşar

Onay bekleme odası agent'ın sahip olmadığı bir state parçasıdır. Workflow duraklatılır (Ders 12). Onay geldiğinde, workflow tam olarak o noktadan devam eder. Bu yüzden LangGraph `interrupt()`'ı yalnızca in-memory state ile değil PostgreSQL checkpointing ile eşleştirir — iki gün sonraki bir onay hâlâ workflow'u sağlam bulur.

### Rubber-stamp onaylar ve challenge-and-response azaltması

HITL için varsayılan UI ("Onayla" / "Reddet" button'ları) gerçek inceleme olmadan hızlı onaylar üretir. Belgelenmiş azaltma: Onayla button'unu etkinleştirmeden önce belirli sorulara pozitif cevap gerektiren bir challenge-and-response checklist'i. Somut şekil:

- "Bunun hangi kaynağa dokunduğunu anlıyor musun? [ ]"
- "Blast radius'un kabul edilebilir olduğunu doğruladın mı? [ ]"
- "Bu başarısız olursa rollback planın var mı? [ ]"

Kendi başına bürokrasi değil — bir forcing function. Kutuları işaretleyemeyen reviewer ya açıklama ister (escalation) ya da reddeder (safe varsayılan). Anthropic agent-safety araştırması rubber-stamp onay desenleri için bir azaltma olarak checklist-driven HITL'yi açıkça referans verir.

### Sonuçlu olarak ne sayılır

Her aksiyonun propose-then-commit'e ihtiyacı yoktur. 2026 rehberliği:

- **Sonuçlu aksiyonlar** (her zaman HITL): geri alınamaz write'lar, finansal işlemler, dışa giden iletişim, üretim database değişiklikleri, yıkıcı dosya-sistemi işlemleri.
- **Geri alınabilir aksiyonlar** (bazen HITL): yerel dosya edit'leri, staging-env değişiklikleri, net rollback'li geri alınabilir write'lar.
- **Read'ler ve inspeksiyonlar** (asla HITL): bir dosya okuma, kaynakları listeleme, salt-okunur API çağırma.

### Aksiyon-sonrası verify

"Commit çalıştı" "yan etki gerçekleşti" ile aynı değildir. Network-partition ve race condition'lar workflow'un başarılı olduğunu düşündüğü ama backend'in persist etmediği bir durumu üretebilir. Verify adımı commit'ten sonra hedef kaynağı yeniden okur ve doğrular. Bu, `RETURNING` clause'lu database transaction'ları veya `PutObject`'ten sonra AWS `GetObject` ile aynı desendir.

### EU AI Act Madde 14

Madde 14 EU'da yüksek-riskli AI sistemleri için etkili human oversight'ı zorunlu kılar. "Etkili" dekoratif değildir. Düzenleyici dil özellikle rubber-stamp desenlerini hariç tutar. Challenge-and-response ile propose-then-commit Microsoft Agent Governance Toolkit uyum dokümanlarında Madde 14 incelemesinden sağ çıkan şekildir.

## Kullan

`code/main.py` stdlib Python'da bir propose-then-commit state machine uygular. Durable store bir JSON dosyasıdır. Idempotency key (thread_id, action_signature)'in hash'idir. Driver üç vakayı simüle eder: temiz bir onay flow'u, geçici failure sonrası retry (çift-yürütmemeli) ve rubber-stamp varsayılan vs challenge-and-response flow'u.

## Yayınla

`outputs/skill-hitl-design.md`, önerilen bir HITL workflow'unu propose-then-commit şekli için inceler ve eksik metadata, idempotency, verification veya challenge-and-response katmanlarını işaretler.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Onaylanmış bir önerinin retry'ının durable kaydı kullandığını ve yeniden yürütmediğini doğrula. Şimdi idempotency key'ini bir timestamp içerecek şekilde değiştir ve retry'ın çift-yürüttüğünü göster.

2. Öneri kaydını bir `rollback` field'ı ile genişlet. Verify adımı başarısız olan bir yürütme simüle et. Rollback'in otomatik ateşlendiğini göster.

3. Microsoft Agent Framework'ün `RequestInfoEvent` dokümanlarını oku. API'nin içerdiği ve oyuncak engine'in eksik olduğu bir metadata field'ı belirle. Onu ekle ve neye karşı koruduğunu açıkla.

4. Belirli bir aksiyon (örn. "public bir Twitter hesabına post atma") için bir challenge-and-response checklist'i tasarla. Reviewer hangi üç soruyu cevaplamak zorunda? Neden o üçü?

5. Senkron bir "Onayla?" prompt'unun yeterli olacağı bir vaka seç (durable store gerekmez). Neden olduğunu açıkla ve kabul ettiğin risk sınıfını adlandır.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Propose-then-commit | "İki-aşamalı onay" | Persist edilmiş öneri + pozitif commit + verify |
| Idempotency key | "Retry-safe token" | Öneri başına unique; ikinci yürütme no-op |
| Data lineage | "Nereden geldi" | Öneriye götüren belirli kaynak içerik |
| Blast radius | "En kötü durum" | Aksiyon yanlış giderse etki kapsamı |
| Rubber-stamp | "Hızlı onay" | Gerçek inceleme olmadan tıklanan "Onayla" |
| Challenge-and-response | "Forcing checklist" | Reviewer belirli soruları pozitif olarak acknowledge etmeli |
| RequestInfoEvent | "MS Agent Framework primitif'i" | Yapılandırılmış metadata'lı durable HITL request'i |
| `interrupt()` / `waitForApproval()` | "Framework primitif'leri" | Aynı şeklin LangGraph / Cloudflare karşılıkları |

## İleri Okuma

- [Microsoft Agent Framework — Human in the loop](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) — `RequestInfoEvent`, durable onaylar.
- [Cloudflare Agents — Human in the loop](https://developers.cloudflare.com/agents/concepts/human-in-the-loop/) — `waitForApproval()` ve Durable Objects.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — uzun-horizon risk için bir azaltma olarak HITL.
- [EU AI Act — Article 14: Human oversight](https://artificialintelligenceact.eu/article/14/) — yüksek-riskli sistemler için düzenleyici baseline.
- [Anthropic — Claude's Constitution (January 2026)](https://www.anthropic.com/news/claudes-constitution) — oversight etrafında anayasal çerçeve.
