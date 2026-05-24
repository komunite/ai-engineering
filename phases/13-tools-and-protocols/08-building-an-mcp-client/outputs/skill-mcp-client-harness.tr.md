---
name: mcp-client-harness
description: MCP server'larının deklaratif bir listesi (name, command, args) verildiğinde, handshake, namespace birleştirme ve routing ile çok sunuculu bir client'ı iskelele.
version: 1.0.0
phase: 13
lesson: 08
tags: [mcp, client, multi-server, routing, namespace]
---

Çalıştırılacak MCP server'ların bir konfigürasyonu verildiğinde, her birini spawn eden, her biriyle handshake yapan, tool listelerini tek bir namespace'te birleştiren ve her çağrıyı sahip olan server'a yönlendiren bir client harness'i üret.

Şunları üret:

1. Server konfigürasyon parser'ı. `name -> {command, args, env}` eşleştir. Command'ların path üzerinde var olduğunu doğrula.
2. Spawn planı. subprocess.Popen ile stdin/stdout/stderr pipe'ları, `bufsize=1`, text mode kullan. Server başına bir arka plan reader thread'i.
3. Handshake pipeline. Her oturum için: `initialize` gönder, yanıtı bekle, kabiliyetleri persist et, `notifications/initialized` gönder.
4. Namespace birleştirme. Bir çakışma policy'si seç: `prefix-on-collision` (varsayılan), `reject-on-collision` ya da `silent-overwrite` (yasak). Başlangıçta birleşik tool listesini yazdır.
5. Routing fonksiyonu. `client.call(canonical_name, arguments)` sahibi olan oturumu bulur ve bir `tools/call` mesajı yazar. Eşleşen id'li yanıtı pending request tablosundaki bir future üzerinden bekler.

Sert retler:
- Her server'ı kendi process'inde spawn etmeyen herhangi bir harness. In-process multiplex'leme izolasyon modelini bozar.
- Varsayılan çakışma policy'si olarak `silent-overwrite` içeren herhangi bir harness. Güvenlik riski.
- Main thread'i stdout okumalarında bloklayan herhangi bir harness. Notification'lar takılır.

Reddetme kuralları:
- Bir server'ın command'ı güvensizse (pinned allowlist'te yoksa), spawn etmeyi reddet ve güvenlik kontrolü için Phase 13 · 15'e yönlendir.
- Kullanıcı bir gerekçe olmadan 10'dan fazla server konfigüre ederse uyar ve bir gateway öner (Phase 13 · 17).
- OAuth'u burada işlemen istenirse reddet ve Phase 13 · 16'ya yönlendir.

Çıktı: Session, birleştirme mantığı, routing ve her konfigüre edilen server'ı egzersiz eden bir main loop içeren tam bir client harness Python dosyası (~150 satır). Çakışma policy'sini ve birleştirilen tool sayısını adlandıran tek satırlık bir özetle bitir.
