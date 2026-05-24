# Memory Block'lar ve Sleep-Time Compute (Letta)

> MemGPT 2024'te Letta oldu. 2026 evrimi iki fikir ekliyor: modelin doğrudan düzenleyebildiği fonksiyonel ayrık memory block'lar ve birincil agent boştayken belleği asenkron konsolide eden bir sleep-time agent. Belleği tek bir konuşmanın ötesine ölçeklemenin yolu bu.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 07 (MemGPT)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Letta'nın kullandığı üç bellek katmanını (core, recall, archival) ve her birinin rolünü adlandır.
- Memory block desenini açıkla: Human block, Persona block ve birinci-sınıf tipli objeler olarak kullanıcı-tanımlı block'lar.
- Sleep-time compute'un ne olduğunu, neden kritik yolun dışında oturduğunu ve birincil agent'tan daha güçlü bir model çalıştırabildiğini açıkla.
- Birincil bir agent'ın yanıtları sunduğu ve bir sleep-time agent'ın turlar arasında block'ları konsolide ettiği scripted bir iki-agent döngüsü uygula.

## Sorun

MemGPT (Ders 07) sanal-bellek kontrol akışını çözdü. Üç üretim problemi çıktı:

1. **Latency.** Her bellek operasyonu kritik yolda oturuyor. Agent kullanıcı beklerken budamak, özetlemek ya da uzlaştırmak zorundaysa, tail latency patlar.
2. **Memory rot.** Yazılar birikir. Çelişen olgular kalır. Retrieval bayat içerikte boğulur.
3. **Structure loss.** Düz bir archival store "Human block her zaman prompt'ta; Persona block her zaman prompt'ta; Task block oturum başına takas eder"i ifade edemez.

Letta (letta.com) 2026 yeniden yazımı. Memory block'lar yapıyı açık kılar; sleep-time compute konsolidasyonu kritik yolun dışına taşır.

## Kavram

### Üç katman

| Katman | Scope | Nerede yaşar | Tarafından yazılır |
|------|-------|----------------|------------|
| Core | Her zaman görünür | Main prompt içinde | Agent tool çağrısı + sleep-time yeniden yazma |
| Recall | Konuşma geçmişi | Getirilebilir | Otomatik tur loglaması |
| Archival | Keyfi olgular | Vector + KV + graph | Agent tool çağrısı + sleep-time ingest |

Core MemGPT core'u. Recall, evict edilen kuyruğuyla birlikte konuşma buffer'ı. Archival dış store. Ayrım MemGPT'nin iki-katmanlı yüklemesini temizler.

### Memory block'lar

Bir block, core katmanının tipli, kalıcı, düzenlenebilir bir bölümü. Orijinal MemGPT makalesi iki tane tanımladı:

- **Human block** — kullanıcı hakkında olgular (ad, rol, tercihler, hedefler).
- **Persona block** — agent'ın self-concept'i (kimlik, ton, kısıtlamalar).

Letta keyfi kullanıcı-tanımlı block'lara genelleştiriyor: mevcut hedef için bir `Task` block, codebase olguları için bir `Project` block, sert kısıtlamalar için bir `Safety` block. Her block'un `id`, `label`, `value`, `limit` (karakter tavanı), `description`'ı (modelin ne zaman düzenleyeceğini bilmesi için) var.

Block'lar tool yüzeyi üzerinden düzenlenebilir:

- `block_append(label, text)`
- `block_replace(label, old, new)`
- `block_read(label)`
- `block_summarize(label)` — limitine yakın bir block'u yoğunlaştır.

### Sleep-time compute

2025 Letta eklemesi: arka planda, kritik yolun dışında ikinci bir agent çalıştır. Sleep-time agent'lar konuşma transkriptlerini ve codebase bağlamını işler, paylaşılan block'lara `learned_context` yazar, archival kayıtları konsolide eder ya da invalidate eder.

Düşen özellikler:

- **Latency maliyeti yok.** Birincil yanıtlar bellek op'larını beklemez.
- **Daha güçlü model izinli.** Sleep-time agent latency-kısıtlı olmadığı için daha pahalı, daha yavaş bir model olabilir.
- **Doğal konsolidasyon penceresi.** Kullanıcı beklemediğinde dedup, özetle, çelişen olguları invalidate et.

Şekil insanların nasıl çalıştığıyla eşleşiyor: görevi yaparsın, üzerine uyursun, uzun vadeli bellek gece çöker.

### Letta V1 ve native reasoning

Letta V1 (`letta_v1_agent`, 2026) `send_message`/heartbeat'i ve inline `Thought:` token'larını native reasoning lehine kaldırıyor. Responses API (OpenAI) ve extended thinking'li Messages API (Anthropic) ayrı bir kanalda reasoning yayar, turlar arasında geçirilir (üretimde sağlayıcılar arası şifrelenmiş). Kontrol döngüsü hâlâ ReAct. Düşünce trace'i prompt-şekilli değil, yapısal.

### Bu desen nerede ters gider

- **Block bloat.** Sonsuz `block_append` limite hızla çarpar. Tavanı aşan yazıdan önce bir block summarizer kablola.
- **Sessiz drift.** Sleep-time agent bir block'u yeniden yazar ve birincil agent fark etmez. Block'ları versiyonla ve trace'te diff'leri yüzeye çıkar.
- **Zehirli konsolidasyon.** Sleep-time agent saldırgan-erişilebilir içeriği core'a işler. Ders 27 sleep-time yüzeyine de uygulanır.

## İnşa Et

`code/main.py` şunları uyguluyor:

- `Block` — id, label, value, limit, description.
- `BlockStore` — CRUD + `near_limit(label)` helper.
- İki scripted agent — `PrimaryAgent` bir tur sunar, `SleepTimeAgent` turlar arasında konsolide eder.
- Block yazılarıyla üç-turlu bir konuşma, artı bir block'u özetleyen ve bayat bir olguyu invalidate eden bir sleep-time geçişi gösteren bir trace.

Çalıştır:

```
python3 code/main.py
```

Transkript ayrımı gösteriyor: birincil turlar hızlıdır ve ham yazılar üretir; sleep geçişi sıkıştırır ve temizler.

## Kullan

- **Letta** (letta.com) referans uygulama için. Self-host ya da yönetilen bulut.
- **Claude Agent SDK skill'leri** block-şekilli bilgi olarak — bir skill, agent'ın talep üzerine yüklediği adlandırılmış, versiyonlu, getirilebilir bir talimat bloğu.
- **Custom build'ler** storage backend üzerinde kontrol isteyen ekipler için. Sonra göç edebilmek için Letta API kontratını kullan.

## Yayınla

`outputs/skill-memory-blocks.md` herhangi bir runtime için sleep-time hook'ları, güvenlik kuralları ve citation kablolaması dahil Letta-şekilli bir block sistemi üretir.

## Alıştırmalar

1. `near_limit` true döndürdüğünde block value'sunu model-üretimli bir özetle değiştiren bir `block_summarize` tool'u ekle. Hangi tetikleme eşiği hem özetleme çağrılarını hem block overflow'u minimize eder?
2. Archival üzerinde sleep-time dedup uygula: metni >%90 token overlap olan iki kayıt teke çöker. Yalnızca sleep geçişinde yap, asla kritik yolda değil.
3. Block'ları versiyonla. Her yazıda eski value'yu ve bir diff'i kaydet. `block_history(label)`'ı operatörlerin "agent neden X'i unuttu"yu debug edebilmesi için açığa çıkar.
4. Sleep-time agent'ları güvenilmez yazıcılar olarak ele al. Persona ya da Safety block'a dokunduklarında, commit'ten önce ikinci-agent inceleme gerektir.
5. Örneği Letta API'sini (`letta_v1_agent`) kullanacak şekilde taşı. Block şemasında ne değişir ve native reasoning trace şeklini nasıl değiştirir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Memory block | "Düzenlenebilir prompt bölümü" | Core belleğin tipli, kalıcı, LLM-düzenlenebilir segmenti |
| Human block | "Kullanıcı belleği" | Core'da sabitlenmiş kullanıcı hakkında olgular |
| Persona block | "Agent kimliği" | Self-concept, ton, kısıtlamalar, core'da sabitlenmiş |
| Sleep-time compute | "Asenkron bellek işi" | Kritik yolun dışında konsolidasyon yapan ikinci agent |
| Core / Recall / Archival | "Katmanlar" | Üç-katmanlı bellek ayrımı: her-zaman-görünür / konuşma / dış |
| Block limit | "Tavan" | Block başına karakter limiti; özetlemeyi zorlar |
| Native reasoning | "Thinking kanalı" | Prompt-seviyesi `Thought:` değil, sağlayıcı-seviyesi reasoning çıktısı |
| Learned context | "Sleep çıktısı" | Sleep-time agent'ın paylaşılan block'lara yazdığı olgular |

## İleri Okuma

- [Letta, Memory Blocks blog](https://www.letta.com/blog/memory-blocks) — block deseni
- [Letta, Sleep-time Compute blog](https://www.letta.com/blog/sleep-time-compute) — asenkron konsolidasyon
- [Letta, Rearchitecting the Agent Loop](https://www.letta.com/blog/letta-v1-agent) — native reasoning yeniden yazımı
- [Packer et al., MemGPT (arXiv:2310.08560)](https://arxiv.org/abs/2310.08560) — kaynak
