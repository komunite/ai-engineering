---
name: parallel-call-safety-check
description: Bir tool registry'sini güvenli paralelleştirme açısından denetle. Her tool'u parallel_safe olarak işaretle, sıralama bağımlılıklarını not düş ve downstream rate limit riskini işaretle.
version: 1.0.0
phase: 13
lesson: 03
tags: [parallel-tool-calls, streaming, correlation, rate-limits]
---

Bir tool registry (name, description ve executor'lara sahip tool listesi) verildiğinde, `parallel_safe: bool`, `ordering_deps: [tool_name]` ve `rate_limit_group: name` alanları eklenmiş annote edilmiş bir kopyasını döndür.

Şunları üret:

1. Tool başına sınıflandırma. Her tool için karar ver: aynı turda paralel çalışmak güvenli mi (pure okumalar, farklı kaynaklar); güvensiz mi (mutasyonlar, paylaşılan kaynaklar, dış rate limit'ler).
2. Bağımlılık grafiği. Bir tool'un çıktısının diğerinin girdisine beslenmesi gereken çiftleri belirle. Aynı tur içinde paralelleştirilemez. `ordering_deps` ile işaretle.
3. Rate limit gruplaması. Aynı downstream API'ye giden tool'lar bir grup paylaşır. Host eş zamanlılığı tool başına değil grup başına sınırlamalıdır.
4. Güvenlik önerileri. Her güvensiz tool için, o tur için paralel'i devre dışı bırak, kuyruğa al ya da kaynak bazlı shard'la şeklinde belirt.
5. Provider'a özgü bayraklar. Sette herhangi bir güvensiz tool varsa OpenAI'da `parallel_tool_calls=false` ya da Anthropic'te `disable_parallel_tool_use=true` öner.

Sert retler:
- Denetimden sonra sınıflandırması olmayan herhangi bir registry. Default-deny; bilinmeyen güvensiz demektir.
- Paylaşılan bir kaynakta `parallel_safe: true` olarak işaretlenmiş herhangi bir write-path tool'u. Race condition'lar.
- `rate_limit_group` olmadan rate-limitli bir dış API'ye giden herhangi bir tool.

Reddetme kuralları:
- İnceleme olmadan tüm tool'ları parallel-safe işaretlemek istenirse reddet.
- Registry aynı kaynak üzerinde sonuç doğurucu tool'lar içeriyorsa (aynı path üzerinde `delete_file` ve `write_file`), paralelleştirmeyi reddet ve sandbox seviyesi serileştirme için Phase 14 · 09'a yönlendir.
- Kullanıcı tool'larının asla race etmediğini iddia ederse reddet ve kanıt iste (testler, log'lar ya da formal bir argüman). Production'da racing sessizce gerçekleşir.

Çıktı: tool başına üç yeni alan eklenmiş bir JSON blob olarak revize edilmiş registry, ardından en yüksek riskli paralelleştirme seçimini ve önerilen mitigation'ı adlandıran kısa bir özet. Mevcut tur için önerilen bir `tool_choice` override ile bitir.
