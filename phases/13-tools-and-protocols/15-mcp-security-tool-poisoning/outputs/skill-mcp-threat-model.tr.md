---
name: mcp-threat-model
description: Geçerli saldırı sınıflarını, yerleşik savunmaları ve Rule-of-Two ihlallerini adlandıran bir MCP deployment için tehdit modeli üret.
version: 1.0.0
phase: 13
lesson: 15
tags: [mcp, security, tool-poisoning, threat-model, rule-of-two]
---

Bir MCP deployment (server listesi, tool listesi, izin listesi) verildiğinde, bir tehdit modeli üret.

Şunları üret:

1. Saldırı uygulanabilirliği. Yedi saldırı sınıfının (tool poisoning, rug pull, shadowing, MPMA, parasitic toolchain, sampling saldırıları, supply chain masquerade) her biri için uygulanabilirliği yüksek / orta / düşük olarak tek cümlelik bir gerekçeyle derecelendir.
2. Savunma envanteri. Hâlihazırda yerleşik savunmaları listele (hash pinning, statik dedektör, gateway, imzalanmış registry, MELON, Rule-of-Two enforcement).
3. Rule of Two denetimi. Her tool için untrusted / sensitive / consequential olarak sınıflandır ve tek bir turda üçünün herhangi bir kombinasyonunu işaretle.
4. Eksik savunmalar. Tehdit profili göz önüne alındığında henüz uygulanmamış en yüksek kaldıraçlı savunmayı adlandır.
5. Runbook. Ekibin güvenlik duruşunu iyileştirmek için önümüzdeki hafta yapması gereken üç eylem.

Sert retler:
- "X saldırı sınıfı geçerli değil çünkü bu server'a güveniyoruz" diyen herhangi bir tehdit modeli. Bir server'ın ele geçirileceğini varsay.
- Silent-overwrite namespace çözümlemesi kullanan herhangi bir deployment.
- Sampling etkin ama oturum başına rate limiter olmayan herhangi bir deployment.

Reddetme kuralları:
- Deployment onaylanmış tool description'larının dokümantasyonuna sahip değilse reddet ve önce hash pinning'i zorunlu kıl.
- Deployment public imzasız MCP registry'leri kullanıyorsa supply chain riskini işaretle ve doğrulanmış bir registry'ye geçişi öner.
- Herhangi bir tool güvensiz girdi, hassas veri ve sonuç doğurucu eylemi birleştiriyorsa onaylamayı reddet ve bir bölme talep et.

Çıktı: saldırı uygulanabilirliği tablosu, savunma envanteri, Rule-of-Two bayrak listesi ve üç eylemli runbook içeren tek sayfalık bir tehdit modeli. Bu deployment için en yüksek değerli tek bir güvenlik eklemesiyle bitir.
