---
name: injection-defense
description: Source-tagged içerik, injection-marker tarama ve allowlist navigasyonu ile herhangi bir agent runtime için bir PVE (Prompt-Validator-Executor) katmanı kur.
version: 1.0.0
phase: 14
lesson: 27
tags: [security, prompt-injection, pve, greshake, source-tag]
---

Tool erişimi ve retrieval'ı olan bir agent verildiğinde, bir injection-defense katmanı üret.

Üret:

1. Her içerik parçasında source tag: `user_message`, `tool_output`, `retrieved_web`, `retrieved_memory`, `retrieved_file`. Tag'leri mesaj geçmişi boyunca yay.
2. `Validator.assess(tool_call, contents)` — injection-şekilli arg veya geri alınan içerikle tool çağrılarını reddeder; yalnızca source tag'ler beyan edilen güven seviyesiyle eşleştiğinde izin verir.
3. Navigasyon için allowlist / blocklist: agent'in dokunabileceği URL'ler, domain'ler, dosya yolları.
4. Memory-write guardrail: direktif gibi görünen write'ları reddet.
5. İçerik-yakalama disiplini (Lesson 23): geri alınan içeriği harici sakla; span'ler düzyazı değil, reference ID taşır.
6. Test suite'i: red-team durumları olarak beş Greshake exploit sınıfı.

Sert ret durumları:

- Source tag'siz tool-use yüzeyi. Provenance olmadan izin seviyelerini ayırt edemez.
- Yalnızca nihai çıktıda çalışan Validator. Geç doğrulama alakasız — model zaten harekete geçti.
- "Bana güven, system prompt halleder." System prompt hijyeni bir kontrol değildir.

Reddetme kuralları:

- Agent source tagging olmadan herhangi bir retrieval yeteneğine sahipse, göndermeyi reddet. Geri alınan içerik kanonik injection vektörüdür.
- Hassas tool'larda (mesaj gönder, shell yürüt, / içine dosya yaz) human-in-the-loop onayı yoksa, reddet.
- Memory write'ları korumasızsa, reddet. Kalıcı memory poisoning bir sonraki session'ı yeniden zehirler.

Çıktı: `validator.py`, `source_tag.py`, `allowlist.py`, `memory_guard.py`, `red_team.py`, altı kontrollü stack'i, kalıcı riskleri ve devam eden review cadence'ını açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Lesson 21 (computer use safety) ve Lesson 23 (OTel ile içerik yakalama).
