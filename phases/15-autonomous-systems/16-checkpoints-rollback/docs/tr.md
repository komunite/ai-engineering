# Checkpoint'ler ve Rollback

> Her graph-state transition persist eder. Bir worker crash olduğunda, lease'i sona erer ve başka bir worker en son checkpoint'ten devam alır. Cloudflare Durable Objects state'i saatler veya haftalar boyunca tutar. Propose-then-commit (Ders 15) aksiyon başına bir rollback planı tanımlar. Aksiyon-sonrası verification döngüyü kapatır. EU AI Act Madde 14 yüksek-riskli sistemler için etkili human oversight'ı zorunlu kılar — pratikte bu, checkpoint'lerin sorgulanabilir olması, rollback'lerin prova edilmesi ve audit izinin bir deploy'dan sağ çıkması anlamına gelir. Keskin failure mode: idempotency key'leri ve precondition kontrolleri olmadan, geçici bir failure sonrası retry zaten-onaylanmış bir aksiyonu çift-yürütebilir. Aksiyon-sonrası verification onu yakalayan şeydir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, checkpoint ve rollback state machine)
**Ön koşullar:** Faz 15 · 12 (Durable execution), Faz 15 · 15 (Propose-then-commit)
**Süre:** ~60 dakika

## Sorun

Durable execution (Ders 12) crash olmuş bir agent'ı resumable yapar. Propose-then-commit (Ders 15) onaylanmış bir aksiyonu auditable yapar. Bu ders onları birleştirir: onaylanmış bir aksiyon kısmen yürütüldüğünde, crash olduğunda ve resume olduğunda ne olur? Rollback ne zaman çalışır ve hangi state'e karşı?

Gerçek sistemler bunu farklı şekilde wire eder:

- **LangGraph** her graph-state transition'ı PostgreSQL'e checkpoint eder. Worker crash'inde, lease serbest kalır ve başka bir worker en son checkpoint'te resume eder. Workflow'lar `interrupt()`'ta duraklar, ki bu kendi başına persist eder.
- **Cloudflare Durable Objects** key başına state'i saatler veya haftalar boyunca tutar. Hesaplamayı onaylanmış aksiyon için depolama ile birlikte yerleştir.
- **Microsoft Agent Framework** workflow API'sında `Checkpoint` primitif'lerini açığa çıkarır; replay artı idempotency retry'ları kapsar.

Her durumda, aslında işe yarayan kombinasyon: idempotency key (çift-yürütmeyi önler) + precondition kontrolü (state hâlâ onayladığımız şeydir) + aksiyon-sonrası verify (yan etki gerçekten gerçekleşti) + verify-fail'de rollback'tir.

## Kavram

### Her transition persist eder

Bir graph-state transition, workflow'u bir adlandırılmış state'ten diğerine hareket ettiren herhangi bir adımdır. Naive uygulamalar yalnızca belirli commit noktalarında persist eder; üretim uygulamaları her transition'ı persist eder. Maliyet (birkaç ekstra write) güvenilirlik kazancına göre küçüktür (replay her yere iner, lease kurtarması kesindir).

### Lease kurtarması

Bir worker crash olduğunda, workflow kaybolmaz; lease (bu worker'ın bu run'ı yürüttüğüne dair kısa-ömürlü bir iddia) basitçe sona erer. Başka bir worker en son checkpoint'i alır ve resume eder. Lease mekanizması üretim sistemlerinin in-flight iş kaybetmeden rolling deploy'lardan sağ çıkmasını sağlayan şeydir.

### Idempotency artı precondition'lar

Idempotency tek başına yeterli değildir. Düşün: bir workflow "balance > 1000 $ olduğunda A'dan B'ye 100 $ transfer et" için onaylandı. Workflow commit edildi, yürütme ortasında crash oldu ve resume oldu. Yalnızca idempotency key kontrol edilirse ve yürütme resume olursa, transfer bir kez çalışır (doğru). Ama crash ile resume arasında, A'nın balance'ının farklı bir workflow üzerinden 500 $'a düştüğünü düşün. Idempotency kontrolü hâlâ geçer; precondition geçmez. Precondition kontrolü olmadan, bir overdraft gönderiyoruz.

Her sonuçlu aksiyonun her ikisine de ihtiyacı vardır:

- **Idempotency key**: çift-yürütmeyi önler.
- **Precondition kontrolü**: state'in hâlâ onaylananla tutarlı olduğunu doğrular.

### Aksiyon-sonrası verification

"Tool 200 döndü" verification değildir. Gerçek verification hedef state'i yeniden okur ve yan etkinin gerçekten gerçekleştiğini doğrular. Desenler:

- Database update: `UPDATE ... RETURNING *` sonra dönen row'un amaçlanan state ile eşleştiğini assert et.
- Email gönderim: gönderimden sonra sent-folder'ı mesaj ID için kontrol et.
- Dosya yazma: dosyayı geri oku ve hash'le.
- API çağrısı: hedef kaynak üzerinde follow-up `GET`.

Verify başarısız olursa, workflow known-bad bir state'tedir. Rollback devreye girer.

### Rollback planları

Propose-then-commit'teki (Ders 15) her sonuçlu aksiyon bir rollback planı taşır. Tipler:

- **In-band rollback**: yan etkiyi doğrudan tersine çevir (`INSERT`'ten sonra `DELETE`, gönderim sonrası `Send-correction-email`).
- **Compensating transaction**: orijinali nötrleştiren yeni bir aksiyon (standart SAGA deseni).
- **Out-of-band rollback**: bir insanı uyar, workflow'u duraklat, kötü state'i araştırma için bırak.

No-op rollback ("bunu geri alamayız") öneride adlandırılmalıdır. Rollback'i olmayan aksiyonlar commit zamanında daha güçlü HITL gerektirir (Ders 15 challenge-and-response).

### EU AI Act Madde 14 operasyonel okuma

Madde 14 yüksek-riskli sistemler için "etkili human oversight" gerektirir. Operasyonel terimlerle, uygulayıcılar bunu şöyle okur:

- Checkpoint'ler bir auditor tarafından sorgulanabilir.
- Rollback'ler prova edilmiştir (en az bir kez uçtan uca test edilmiş).
- Audit izi bir deploy'dan sağ çıkar (checkpoint backend geçici değildir).
- Başarısız verification'lar sessizce loglanmaz, uyarı yapılır.

Commit ortasında crash olan, resume olan ve verify + rollback yolu olmadan yan etkiyi tamamlayan bir workflow Madde 14 testini geçemez.

### Keskin failure mode: çift-yürütme

Bu alandaki en yaygın üretim olayı:

1. Aksiyon onaylandı, idempotency key k.
2. Commit başlar, yürütür, 200 döner.
3. Workflow "committed" status'unu persist etmeden önce crash olur.
4. Workflow resume olur; "onaylandı ama commit edilmedi"yi görür; yeniden yürütür.
5. Yan etki iki kez ateşlenir.

Azaltma: yürütmeden önce "in-flight" intent'i persist et, bir idempotency key ile yürüt, sonra yalnızca aksiyon-sonrası verification başarılı olduktan sonra "committed" olarak işaretle. Aksiyon ateşlenir ve status write başarısız olursa, verify yapmayı ve (gerekirse) yeniden ateşlemeyi bilirsin. Status write başarılı olur ve aksiyon başarısız olursa, kurtarma yolu üzerinden verify yapar ve tam olarak bir kez ateşlersin.

## Kullan

`code/main.py` idempotency, precondition'lar, verify ve rollback ile checkpoint'lenmiş bir workflow uygular. Driver dört senaryoyu simüle eder: temiz koşu, crash sonrası retry (idempotency yakalar), precondition fail (workflow ateşlemeden iptal eder), verify fail (rollback ateşler).

## Yayınla

`outputs/skill-rollback-rehearsal.md`, önerilen bir workflow için bir rollback-rehearsal testi tasarlar ve checkpoint backend'ini audit-iz persistence'ı için audit eder.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Dört senaryoyu doğrula. Commit-sırası-crash vakası için, aksiyonun retry'lar boyunca tam olarak bir kez ateşlendiğini doğrula.

2. "Önce yapıldı olarak işaretle, sonra yap" desenini, status write aksiyon sonrası ateşlenecek şekilde modifiye et. Crash senaryosunu yeniden çalıştır. Kaç duplicate aksiyonun ateşlendiğini ölç.

3. Belirli bir üretim aksiyonu (örn. "bir Slack kanalına post atma") için bir rollback planı tasarla. In-band, compensating veya out-of-band olarak sınıflandır. Seçimi gerekçelendir.

4. Bildiğin bir workflow'u al. Her state transition'ı belirle. Her birini bir durability gereksinimi ile (persist / persist etme) işaretle. Şu an persist etmediklerini say.

5. Prova edilmiş-rollback testi: gerçek bir workflow'u çalıştıran, onu crash eden ve rollback yolunun ateşlendiğini doğrulayan uçtan uca bir test tasarla. Test neyi assert ediyor?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Checkpoint | "Kayıt noktası" | Her graph-state transition durable bir store'a persist eder |
| Lease | "Worker iddiası" | Bir worker'ın bir run yürüttüğüne dair kısa-ömürlü iddia; crash'te sona erer |
| Precondition | "State gate'i" | State'in hâlâ onaylanan aksiyon ile tutarlı olduğunun assertion'ı |
| Aksiyon-sonrası verify | "Yeniden-okuma kontrolü" | Yan etkinin hedef sistemde gerçekten gerçekleştiğini doğrula |
| In-band rollback | "Doğrudan undo" | Yan etkiyi ters operasyonla geri al |
| Compensating transaction | "SAGA undo" | Orijinali nötrleştiren yeni bir aksiyon |
| Mark-as-done-first | "Status write sırası" | Commit'ten dönmeden önce commit edilmiş status'u persist et |
| Madde 14 | "EU AI Act human oversight" | Operasyonel: sorgulanabilir checkpoint'ler, prova edilmiş rollback'ler, auditable iz |

## İleri Okuma

- [Microsoft Agent Framework — Checkpointing and HITL](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) — checkpoint primitif'leri ve lease kurtarması.
- [Cloudflare Agents — Human in the loop](https://developers.cloudflare.com/agents/concepts/human-in-the-loop/) — bir state substrate olarak Durable Objects.
- [EU AI Act — Article 14: Human oversight](https://artificialintelligenceact.eu/article/14/) — düzenleyici baseline.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — uzun-horizon workflow'lar için güvenilirlik çerçevesi.
- [Anthropic — Claude Code Agent SDK: agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) — Claude Code Routines için workflow şekli.
