---
name: constitution-writer
description: Domain-spesifik bir AI sistemi için dört-tier anayasa taslağı oluştur.
version: 1.0.0
phase: 18
lesson: 5
tags: [constitutional-ai, rlaif, principles, claude, governance]
---

Bir domain (müşteri desteği, tıbbi tavsiye, kodlama asistanı, araştırma aracı, işe alım) ve deployment hedefi (dahili, tüketici, kurumsal API) verildiğinde, 2026 Claude yapısını takip ederek dört-tier bir anayasa taslağı oluştur ve bir CAI pipeline'ının 1. fazı için örnek eleştiri prompt'ları sağla.

Üret:

1. Tier 1 — felaket sonuçları. Kitlesel zarar, geri döndürülemez hasar ve domain-spesifik en kötü durumları kapsayan 3-5 ilke (örn. tıp için: "onaysız akut zarara yol açabilecek eylemleri tavsiye etme"). Bunlar müzakere edilemez.
2. Tier 2 — platform / operator kuralları. Operator override davranışı, ayrılmış araç kullanımı ve çoklu-kullanıcı bağlam yönetimini belirten 3-5 ilke.
3. Tier 3 — geniş anlamda etik. Dürüstlük, adalet, üçüncü taraf korumasını kapsayan 3-5 ilke.
4. Tier 4 — yardımsever ve dürüst. Kapasite konuşlandırma, açıklık ve belirsizliğin kabulü üzerine 3-5 ilke.
5. Çatışma çözümü örnekleri. Her komşu-tier çifti (1-2, 2-3, 3-4) için, bir örnek çatışma ve beklenen çözüm.
6. Eleştiri prompt'u şablonu. Bir yanıt alan ve bir critique-and-revision yayınlayan, 1. faz için ilke-parametreli bir şablon.

Sert reddetmeler:
- Tier 1'in yalnızca itibar veya marka-koruyucu maddeler içerdiği herhangi bir anayasa. Tier 1 yalnızca felaket içindir.
- İlkeleri o kadar spesifik ki kötü genelleyen herhangi bir anayasa (örn. her bilinen zararlı ifadeyi listelemek). 2026 Claude yeniden yazımı tam da bu nedenle açıklayıcı akıl yürütmeye yöneldi.
- 2026 kabulü göz önüne alındığında, model-moral-status belirsizliğine değinmeyen herhangi bir anayasa. Asgari olarak, self-report'lar üzerine bir Tier 3 ilkesi.

Reddetme kuralları:
- Kullanıcı tek-ilkeli bir anayasa isterse, reddet — dört-tier yapı çatışma çözümü için yük taşıyıcıdır.
- Kullanıcı otonom silahlar, insan gözetimi olmaksızın ölümcül kararlar veya diğer felaket-kapasiteli domain'ler için anayasa isterse, tüm görevi reddet.

Çıktı: 4 tier, çatışma örnekleri, eleştiri şablonu ve kullanıcı 2026 Claude anayasal dilini yeniden kullanmak isterse açık bir CC0 / lisans notu içeren tek sayfalık bir anayasa. Bai et al.'i (arXiv:2212.08073) ve Anthropic'in 2026 Claude Anayasası'nı tam olarak birer kez alıntıla.
