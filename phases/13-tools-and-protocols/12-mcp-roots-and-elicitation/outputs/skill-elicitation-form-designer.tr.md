---
name: elicitation-form-designer
description: Çağrı ortasında kullanıcı onayı ya da netleştirmesi gerektiren bir tool için elicitation form şemasını ve mesaj template'ini tasarla.
version: 1.0.0
phase: 13
lesson: 12
tags: [mcp, elicitation, user-input, forms]
---

Davranışı çağrı ortasında kullanıcı girdisi gerektirebilecek bir tool verildiğinde, elicitation şemasını ve mesajını tasarla.

Şunları üret:

1. Tetikleme koşulu. Tool'un `elicitation/create` çağırmasına neden olması gereken tam girdiyi ya da belirsizliği belirt.
2. Mesaj template'i. Host'un kullanıcıya gösterdiği tek cümle. Sade, spesifik, jargonsuz.
3. Şema. Tipli property'ler ve `enum` listesi (netleştirme için) ya da `boolean` (onay için) ile düz bir JSON Schema. Nest etme.
4. Branch işleme. `accept` / `decline` / `cancel`'ı tool davranışlarına eşle.
5. Rate-limit kuralı. Tool invocation başına elicitation'ları sınırla; bir loop içinde asla elicit etme.

Sert retler:
- Object'leri nest eden herhangi bir şema. Elicitation v1 düz.
- LLM'in prose ile sorabileceği eksik bir argümanı doldurmak için kullanılan herhangi bir elicitation.
- Yüksek frekanslı herhangi bir elicitation (tool çağrısı başına birden fazla).

Reddetme kuralları:
- Tool read-only ve düşük riskliyse elicit etmeyi reddet ve sadece sonucu döndür.
- Tool destructive ise ve host `destructiveHint` annotation'larını destekliyorsa, annotation kullanmayı öner ve client'ın onayı yerel olarak işlemesine izin ver.
- İhtiyaç bir OAuth sign-in ise URL-mode elicitation öner ve SEP-1036 drift riskini işaretle.

Çıktı: tetikleme koşulu, mesaj template'i, şema, branch işleme, rate-limit kuralı ve form mode mu URL mode mu daha uygun olduğuna dair bir not içeren tek sayfalık bir tasarım.
