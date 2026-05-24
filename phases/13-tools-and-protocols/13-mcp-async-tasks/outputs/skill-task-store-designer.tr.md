---
name: task-store-designer
description: Uzun süreli bir MCP tool'u için task store tasarla: state şekli, ttl, dayanıklılık, iptal, çökme kurtarma.
version: 1.0.0
phase: 13
lesson: 13
tags: [mcp, tasks, durable-store, long-running, sep-1686]
---

Uzun süreli bir tool (araştırma, build, export, rapor üretimi) verildiğinde, SEP-1686 task augmentation'ı destekleyen task store'u tasarla.

Şunları üret:

1. State şekli. Minimum alanlar: `id`, `state`, `progress`, `result`, `error`, `ttl`, `created_at`. Opsiyonel: `request_meta`, `parent_task_id` (gelecekteki subtask'ler için).
2. Dayanıklılık seçimi. Oyuncak için filesystem; tek process için SQLite; çok replikalı için Redis. Gerekçelendir.
3. taskSupport bayrağı. Tool başına `forbidden`, `optional` ya da `required`; tek satırlık gerekçe.
4. İptal planı. Worker'ın cancel sinyalini nasıl kontrol ettiği; kısmi ilerlemede ne olacağı.
5. Çökme kurtarma. Boot zamanı reload kuralı; `CRASH_RECOVERY` başarısızlıklarının client'a nasıl göründüğü.

Sert retler:
- Tamamlanmış sonuçları ttl içinde kaybeden herhangi bir store.
- Açık terminal state'lere (`completed`, `failed`, `cancelled`) sahip olmayan herhangi bir task state'i.
- Idempotent olmayan herhangi bir iptal.

Reddetme kuralları:
- Tool 5 saniyenin altında çalışıyorsa task'a yükseltmeyi reddet. Senkron daha basittir.
- Task 10 MB'tan fazla sonuç üretecekse reddet ve streaming content block'ları öner.
- Server state persist edebilen bir process'e sahip değilse (stateless edge function), reddet ve dayanıklı bir runtime'a geçişi öner.

Çıktı: state şekli, dayanıklılık seçimi, taskSupport bayrağı, iptal planı ve çökme kurtarma kuralı içeren tek sayfalık bir store tasarımı. SEP-1686 subtask'lerinin yayınlandığında bu tasarımı etkileyip etkilemeyeceği konusunda tek satırlık bir tavsiyeyle bitir.
