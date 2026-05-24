# Async Tasks (SEP-1686) — Uzun Süren İşler İçin Call-Now, Fetch-Later

> Gerçek agent işi dakikalar ila saatler alır: CI çalıştırmaları, deep-research sentezi, batch export'ları. Synchronous tool çağrıları bağlantıları düşürür, time out olur ya da UI'ı bloklar. 2025-11-25'te merge edilen SEP-1686 bir Tasks primitive'i ekler: herhangi bir request bir task olacak şekilde augment edilebilir ve sonuç daha sonra fetch edilebilir ya da state notification'ları üzerinden stream'lenebilir. Drift-risk notu: Task'lar H1 2026 boyunca deneyseldir; SDK yüzeyi spec etrafında hâlâ tasarlanmaktadır.

**Tür:** Yapım
**Diller:** Python (stdlib, async task state machine)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu), Faz 13 · 09 (transport'lar)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Bir tool'u senkrondan task-augmented'a ne zaman terfi edileceğini tanımla (>30 saniye sunucu-tarafı iş).
- Task lifecycle'ı gez: `working` → `input_required` → `completed` / `failed` / `cancelled`.
- Task state'ini persist et, böylece çökmeler in-flight işi kaybetmez.
- `tasks/status` poll et ve `tasks/result`'ı doğru şekilde fetch et.

## Sorun

Bir `generate_report` tool'u çok dakikalı bir çıkarım pipeline'ı çalıştırır. Synchronous model altında seçenekler:

1. Bağlantıyı üç dakika açık tut. Uzak transport'lar düşürür; client'lar time out olur; UI'lar donar.
2. Bir placeholder ile hemen dön; client'ın custom bir endpoint'i poll etmesini gerektir. MCP uniformitesini bozar.
3. Fire-and-forget; sonuç yok.

Hiçbiri iyi değil. SEP-1686 bir dördüncüsünü ekler: task augmentation. Herhangi bir request (tipik olarak `tools/call`) bir task olarak etiketlenebilir. Sunucu hemen bir task id döndürür. Client `tasks/status`'u poll eder ve bittiğinde `tasks/result`'ı fetch eder. Sunucu-tarafı state restart'ları hayatta kalır.

## Kavram

### Task augmentation

Bir request `params._meta.task.required: true` (ya da `optional: true`, sunucu karar verir) ayarlanarak task olur. Sunucu hemen şu şekilde yanıt verir:

```json
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "_meta": {
      "task": {
        "id": "tsk_9f7b...",
        "state": "working",
        "ttl": 900000
      }
    }
  }
}
```

`ttl` sunucunun state'i tutma sözüdür; ttl'den sonra task sonucu atılır.

### Tool başına opt-in

Tool annotation'ları task desteğini bildirebilir:

- `taskSupport: "forbidden"` — bu tool her zaman senkron çalışır. Hızlı tool'lar için güvenli.
- `taskSupport: "optional"` — client task-augmentation talep edebilir.
- `taskSupport: "required"` — client task augmentation kullanMALIDIR.

Bir `generate_report` tool'u `required` olurdu. Bir `notes_search` tool'u `forbidden` olurdu.

### State'ler

```
working  -> input_required -> working  (elicitation üzerinden döngü)
working  -> completed
working  -> failed
working  -> cancelled
```

State machine append-only'dir: `completed`, `failed` ya da `cancelled` olduğunda, task terminal'dir.

### Method'lar

- `tasks/status {taskId}` — mevcut state'i ve bir progress hint'i döndürür.
- `tasks/result {taskId}` — henüz bitmemişse blok'lar ya da 404 döndürür.
- `tasks/cancel {taskId}` — idempotent; terminal state'ler görmezden gelinir.
- `tasks/list` — opsiyonel; aktif ve yakın zamanda tamamlanmış task'ları enumerate eder.

### State değişikliklerini stream'leme

Sunucu desteklediğinde, client state notification'larına subscribe edebilir:

```
server -> notifications/tasks/updated {taskId, state, progress?}
```

Poll yerine stream'leyen client'lar daha iyi UX alır. Polling minimum yüzey olarak her zaman desteklenir.

### Durable state

Spec, task desteği bildiren sunucuların state persist etmesini gerektirir. Bir çökme, ttl içindeki tamamlanmış sonuçları kaybetmemelidir. Store'lar SQLite'tan Redis'e ve filesystem'a uzanır. Ders 13 harness'ı filesystem kullanır.

### Cancellation semantiği

`tasks/cancel` idempotent'tir. Task yürütme ortasındaysa, sunucu durdurmaya çalışır (executor-cooperative cancellation'ı kontrol et). Zaten terminal ise, request no-op'tur.

### Crash recovery

Sunucu process'i yeniden başladığında:

1. Tüm persisted task state'lerini yükle.
2. Process'i ölmüş olan herhangi `working` task'ı `CRASH_RECOVERY` hatasıyla `failed` olarak işaretle.
3. `completed` / `failed` / `cancelled`'ı ttl'leri için koru.

### Async task'lar artı sampling

Bir task kendisi `sampling/createMessage` çağırabilir. Uzun süren araştırma task'larının çalışma şekli budur: sunucunun task thread'i gerektiğinde client'ın modelini örnekler, client'ın UI'sı task'ı periyodik progress güncellemeleriyle `working` olarak gösterir.

### Bu neden deneysel

SEP-1686 2025-11-25'te yayınlandı ama daha geniş roadmap üç açık konuyu çağırıyor: durable subscription primitive'leri, subtask'lar (parent-child task ilişkileri) ve result-TTL standardizasyonu. Spec'in 2026 boyunca evrimleşmesini bekle. Üretim kodu Task'ları yalnızca yaygın durum için stabil olarak ele almalı ve subtask'lar için gelecek SDK değişikliklerine karşı guard'lamalıdır.

## Kullan

`code/main.py` durable bir task store (filesystem-destekli) ve arka plan thread'inde çalışan bir `generate_report` tool'u implemente eder. Client'lar tool'u çağırır, hemen bir task id alır, worker progress güncellerken `tasks/status`'u poll eder ve bittiğinde `tasks/result`'ı fetch eder. Cancellation çalışır; crash recovery worker thread'ini öldürerek ve state'i yeniden yükleyerek simüle edilir.

Bakılacak şeyler:

- Task state JSON'u `/tmp/lesson-13-tasks/<id>.json`'a persist edildi.
- Worker thread'i `progress` alanını günceller; poll ilerlediğini gösterir.
- Client tarafından cancellation bir event ayarlar; worker kontrol eder ve erken çıkar.
- "Çökme"de state reload, in-flight task'ı `CRASH_RECOVERY` ile `failed` olarak işaretler.

## Yayınla

Bu ders `outputs/skill-task-store-designer.md` üretir. Uzun süren bir tool (araştırma, build, export) verildiğinde, skill task store'u (state şekli, ttl, durability) tasarlar, doğru taskSupport bayrağını seçer ve progress notification'larını taslaklar.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Bir `generate_report` task'ı başlat, status poll et, sonra sonucu fetch et.

2. Çalışma ortasında bir `tasks/cancel` çağrısı ekle. Worker'ın buna uyduğunu ve state'in `cancelled` olduğunu doğrula.

3. Crash recovery simüle et: worker thread'ini öldür, loader'ı yeniden başlat ve `CRASH_RECOVERY` başarısızlık modunu gözlemle.

4. Store'u SQLite'a genişlet. Durability kazanımları aynı; query seçenekleri açılır (session X'ten tüm task'ları listele).

5. 2026 için MCP roadmap yazısını oku. Önümüzdeki yıl SDK API tasarımını etkilemesi en muhtemel Tasks-ilgili açık konuyu tanımla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Task | "Uzun süren tool çağrısı" | Async yürütme için `_meta.task` ile augment edilmiş request |
| SEP-1686 | "Tasks spec'i" | 2025-11-25'te Tasks ekleyen Spec Evolution Proposal |
| `_meta.task` | "Task zarfı" | id, state, ttl içeren request başına metadata |
| taskSupport | "Tool bayrağı" | Tool başına `forbidden` / `optional` / `required` |
| `tasks/status` | "Poll method'u" | Mevcut state ve opsiyonel progress hint'i fetch et |
| `tasks/result` | "Sonucu fetch et" | Tamamlanmış payload'u ya da henüz bitmemişse 404 döndürür |
| `tasks/cancel` | "Durdur" | Idempotent cancellation request'i |
| ttl | "Retention bütçesi" | Sunucunun task state'ini tutma sözü verdiği millisaniye |
| `notifications/tasks/updated` | "State push" | Sunucu-initiated state-change event'i |
| Durable store | "Crash-safe state" | Filesystem / SQLite / Redis persistence katmanı |

## İleri Okuma

- [MCP — GitHub SEP-1686 issue](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1686) — kaynaklanan öneri ve tam tartışma
- [WorkOS — MCP async tasks for AI agent workflows](https://workos.com/blog/mcp-async-tasks-ai-agent-workflows) — gerekçeyle tasarım gezintisi
- [DeepWiki — MCP task system and async operations](https://deepwiki.com/modelcontextprotocol/modelcontextprotocol/2.7-task-system-and-async-operations) — mekanik ve state machine
- [FastMCP — Tasks](https://gofastmcp.com/servers/tasks) — SDK-seviyesi task implementation desenleri
- [MCP blog — 2026 roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — açık konular ve subtask'lar dahil 2026 öncelikleri
