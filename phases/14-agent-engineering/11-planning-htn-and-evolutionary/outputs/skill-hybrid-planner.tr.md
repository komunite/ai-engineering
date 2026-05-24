---
name: hybrid-planner
description: Hybrid bir planner kur — kanıtlanabilir-doğru planlar için ChatHTN, makine-kontrol edilebilir evaluator ile kod araması için AlphaEvolve — ve probleme uygun olanı seç.
version: 1.0.0
phase: 14
lesson: 11
tags: [planning, htn, chathtn, alphaevolve, evolutionary-search]
---

Bir problem sınıfı (politika-bağlı workflow vs kod optimizasyonu vs açık uçlu görev) verildiğinde, bir planner seç ve doğru bir iskele üret.

Karar:

1. Problemin sert preconditions / politika / scheduling kısıtları var mı? -> HTN (ChatHTN).
2. Problemin deterministik, makine-kontrol edilebilir bir fitness fonksiyonu var mı? -> Evolutionary (AlphaEvolve).
3. Hiçbiri değil mi? -> Yerine ReAct (Lesson 01) veya ReWOO (Lesson 02) için uzan.

HTN için üret:

1. `preconditions`, `effects_add`, `effects_remove` içeren `Operator` tipi.
2. `task`, `preconditions`, `subtasks` içeren `Method` tipi.
3. Önce yöntemleri deneyen, LLM ayrıştırmasına geri dönen ve başarılı LLM ayrıştırmalarını cache'leyen bir planner.
4. Bilinmeyen operatorlere veya yöntemlere atıfta bulunan LLM ayrıştırmalarını reddeden bir doğrulama adımı.

Evolutionary için üret:

1. Aday programlardan oluşan bir tohum popülasyonu.
2. Skaler fitness döndüren deterministik bir evaluator.
3. Bir mutation operatörü (LLM-tabanlı veya kural-tabanlı).
4. Bir selection döngüsü (top-k tut, mutate et, tekrar et) erken durdurma ile.

Sert ret durumları:

- LLM çıktısının operator-schema doğrulaması olmadan doğrudan uygulandığı ChatHTN. Soundness iddiası başarısız olur.
- Evaluator'ın bir LLM judge çağırdığı AlphaEvolve. Fitness deterministik olmalıdır; LLM judge'lar döngünün geri kazanamayacağı stokastik gürültü ekler.
- Açık uçlu görevler için ("bir blog yazısı yaz") herhangi bir pattern. Evaluator yok, precondition yok -> ReAct kullan.

Reddetme kuralları:

- Alanın net bir operator schema'sı yoksa, ChatHTN'yi reddet. ReWOO veya düz ReAct öner.
- Alanın makine-kontrol edilebilir fitness'ı yoksa, AlphaEvolve'i reddet. Self-Refine (Lesson 05) öner.
- Kullanıcı "planner + LLM nihai kararı verir" isterse, reddet. Sembolik doğruluk ve LLM keşfi arasındaki ayrım load-bearing'dir.

Çıktı: `operators.py`, `methods.py`, `planner.py` (HTN) veya `evaluator.py`, `mutator.py`, `loop.py` (evolutionary), artı karar gerekçesi içeren `README.md`. "Bundan sonra ne okumalı" notu ile bitir: debate-stili doğrulama probleme uyuyorsa Lesson 25, görev gerçekten ReWOO-şekilli ise Lesson 02.
