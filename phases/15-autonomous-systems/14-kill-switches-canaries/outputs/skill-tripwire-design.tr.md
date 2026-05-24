---
name: tripwire-design
description: Önerilen bir agent detector stack'ini (kill switch, circuit breaker'lar, canary token'ları) incele ve ilk otonom run'dan önce eksik tripwire'ları işaretle.
version: 1.0.0
phase: 15
lesson: 14
tags: [kill-switch, circuit-breaker, canary, honeytoken, detection-and-response]
---

Bir agent deployment'ı için önerilen detector stack'i verildiğinde, üç-detector referansına (kill switch, circuit breaker, canary) karşı denetle ve neyin eksik, yanlış-ayarlanmış veya agent'a maruz kaldığını işaretle.

Üret:

1. **Kill-switch denetimi.** Switch nerede yaşıyor (feature flag, Redis, signed config)? Agent'ın credential'larının onu kapatamadığını doğrula. Her sonuçsal eylemin switch'i kontrol ettiğini doğrula, sadece startup'ta değil. Yeniden etkinleştirmenin açık bir insan eylemi olduğunu doğrula.
2. **Circuit-breaker envanteri.** Bir breaker'ın izlediği her pattern'ı listele (tekrar, ardışık failure, oran, out-of-trust read sonrası spesifik tool). Her biri için eşik ve cool-down belirt. 10'un üzerindeki eşikler genellikle çok gevşektir.
3. **Canary tasarımı.** Ortamdaki her canary token'ını listele. Her biri için: ne olduğu (sahte credential, sahte DB record'u, sahte dosya, sahte memory entry'si), nerede yaşadığı, hangi erişimin alarm tetiklediği, kimin page'lendiği. Hiçbir canary'nin dokunulması için meşru bir sebep olmadığını doğrula.
4. **İstatistiksel + hard katmanlama.** Stack'in herhangi bir istatistiksel detector'a (EWMA, z-score) ek olarak en az bir hard limit (Lesson 17 anayasa stili) kullandığını doğrula. Yalnızca istatistiksel detector'lar yavaş drift'i kabul eder.
5. **Quarantine yolu.** Bir detector tetiklendiğinde ne olur? Tam agent durdurma, path-özel pause, traffic redirect (eBPF / Cilium honeypot), yalnızca alert. Yolun en az bir kez uçtan uca test edildiğini doğrula.

Sert reddetmeler:
- Harici kill switch olmayan herhangi bir deployment.
- Agent'ın write erişimine sahip olduğu sistemlerde saklanan canary token'lar.
- Hard limit olmayan yalnızca istatistiksel tespit.
- Cool-down'ları insan incelemesi olmadan otomatik-yeniden-etkinleşen circuit breaker'lar.
- Kill switch'in yalnızca startup'ta kontrol edildiği unattended run'lar, eylem başına değil.

Reddetme kuralları:
- Kullanıcı kill switch'i barındıran agent credential'larının dışındaki spesifik sistemleri adlandıramazsa, reddet. "Agent'ın okuduğu bir config file kullanıyoruz" agent config file yazabiliyorsa kill switch değildir.
- Kullanıcı Auto Mode classifier'ını (Lesson 10) tripwire'ların yerine geçen bir şey olarak ele alıyorsa, reddet. Classifier detection-and-response'a ortogonaldır.
- Önerilen canary'ler agent'ın okumak için meşru sebebi olan sistemlerde duruyorsa, reddet ve yeniden tasarım iste.

Çıktı formatı:

Şunları içeren bir tripwire denetimi döndür:
- **Kill-switch satırı** (konum, kontrol frekansı, yeniden etkinleştirme prosedürü)
- **Circuit-breaker tablosu** (pattern, eşik, cool-down)
- **Canary tablosu** (token, konum, alarm, sahip)
- **Katmanlama notu** (istatistiksel + hard limit'ler mevcut y/n)
- **Quarantine akışı** (ne tetikler, ne olur, test edildi y/n)
- **Hazırlık** (production / staging / yalnızca araştırma)
