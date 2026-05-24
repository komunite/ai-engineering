---
name: role-designer
description: Çoklu-agent sistem için rol roster'ı üret; belirli bir görev için planner/executor/critic/verifier'ı açık I/O şemalarıyla adlandır.
version: 1.0.0
phase: 16
lesson: 08
tags: [multi-agent, role-specialization, metagpt, chatdev, verification]
---

Bir görev verildiğinde, I/O şemaları ve deterministik bir verifier ile uzmanlaşmış rol roster'ı üret. CrewAI, LangGraph, AutoGen ya da custom loop'lara eşlemeye hazır.

Üret:

1. **Rol roster'ı.** 3-5 rol. Her birini adlandır. Minimum: planner, executor, verifier. Critic isteğe bağlı.
2. **Rol başına I/O şeması.** Her rol için: ne tükettiği (yukarı akış rolden) ve ne ürettiği (şema, düz metin değil). Dataclass tarzı notasyon kullan.
3. **Verifier spesifikasyonu.** Deterministik kontrolü adlandır: test suite, type checker, schema validator, linter. Pass/fail kriterlerini tanımla.
4. **Critic spesifikasyonu (isteğe bağlı).** Dahil edilirse, hangi öznel kaliteyi yargıladığını adlandır. Somut bir checklist, "iyi kod" değil.
5. **Communicative dehallucination kuralları.** Bir detay eksik olduğunda her aşağı akış rolünün yukarı akışa gönderebileceği soruları adlandır; böylece icat etmesinler.
6. **Revizyon döngüsü bütçesi.** İnsana eskalasyondan önce maksimum round. Varsayılan 2.
7. **Framework eşlemesi.** Her biri bir satır: bu roster'ı CrewAI, LangGraph, AutoGen'de nasıl ifade edersin.

Sert ret durumları:

- Deterministik verifier'ı olmayan herhangi bir roster. Tamamen LLM roster'ları MAST kontrolünden geçemez.
- Bulanık I/O ("executor çıktı döner"). Her zaman şemayı belirt.
- Critic ve verifier'ın karıştırılması. Farklı bug'ları yakalarlar; her ikisi de gerekliyse her ikisi de olmalı.

Reddetme kuralları:

- Görev deterministik bir doğruluk kontrolüne sahip değilse (saf üretken iş, yaratıcı yazı), reddet ve onun yerine ya insan reviewer döngüsü ya da çoklu-agent debate (Ders 07) öner.
- Görev 3+ rol için fazla küçükse (insan işinin 10 dakikası altında), reddet ve tek-agent öner.

Çıktı: bir sayfalık rol-tasarım brief'i. MAST hata-boşluk kontrolüyle kapat: en az bir deterministik verifier'ın varlığını teyit et.
