---
name: actor-runtime
description: Özel state, actor başına inbox, yalnızca mesaj-IPC, fault isolation ve dead-letter queue ile AutoGen v0.4-şekilli actor runtime kur.
version: 1.0.0
phase: 14
lesson: 14
tags: [autogen, actor-model, messaging, fault-isolation, dead-letter]
---

Bir çoklu-agent görevi verildiğinde, bir actor runtime ve gerekli agent actor'larını üret.

Üret:

1. `sender`, `recipient`, `topic`, `body`, `mid` içeren bir `Message` tipi.
2. `receive(message, runtime)` içeren bir `Actor` base class. Actor state'i özeldir.
3. Paylaşılan bir queue, `send()`, `run_until_idle()` ve bir dead-letter queue içeren bir `Runtime`. Handler'lardaki exception'lar DLQ'ya gider; yayılmasın.
4. Bir topoloji helper'ı: RoundRobin (sabit rotasyon), Selector (LLM sıradakini seçer) veya custom broadcast.
5. Mesaj başına observability kancaları: Lesson 23'e göre `gen_ai.agent.name` ve `gen_ai.operation.name` ile OTel span'leri yay.

Sert ret durumları:

- Alıcı dönene kadar göndereni bloklayan senkron mesaj iletimi. Bu v0.2 modelidir; fault isolation'ı kırar.
- Actor'lar arası paylaşılan değiştirilebilir state. Actor'lar state'i mesajlarla okur veya hiç okumaz.
- Handler exception'larını yayan bir runtime. Başarısızlıklar DLQ'ya aittir; diğer actor'ların çalışmaya devam etmesine izin ver.

Reddetme kuralları:

- Görev yalnızca sabit ileri-geri ile iki actor'a sahipse, actor çerçevesini reddet ve bir prompt chain öner (Lesson 12). Actor'lar >=3 actor veya async eşzamanlılık olduğunda maliyetini kazanır.
- Kullanıcı "daha kolay hata ayıklama" için "senkron mod" isterse, reddet. Bunun yerine logging + tracing (Lesson 23) öner.
- Alan tek bir uzmanla tam olarak request/response ise, actor takımı yerine routing (Lesson 12) öner.

Çıktı: `message.py`, `actor.py`, `runtime.py`, `teams.py`, DLQ politikasını, topoloji seçimini ve OTel span'lerinin nasıl bağlandığını açıklayan `README.md`. "Bundan sonra ne okumalı" notu ile bitir: actor'lar müzakere ederse Lesson 25 (multi-agent debate), tracing gerekiyorsa Lesson 23 (OTel) veya ileriye dönük runtime istiyorsan Microsoft Agent Framework.
