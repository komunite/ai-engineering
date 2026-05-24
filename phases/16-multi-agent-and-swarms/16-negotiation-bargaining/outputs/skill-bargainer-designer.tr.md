---
name: bargainer-designer
description: Bir müzakere protokolü tasarla: hangi agent anlatır, hangi bileşen teklif üretir, private scratchpad'ler public mesajlardan nasıl ayrılır, round üst sınırı nedir ve anlaşma oranı nasıl izlenir.
version: 1.0.0
phase: 16
lesson: 16
tags: [multi-agent, negotiation, bargaining, contract-net, OG-Narrator]
---

Bir müzakere veya görev-pazarı senaryosu verildiğinde (iki-taraflı pazarlık, N-taraflı açık artırma, contract-net görev dağılımı), protokolü tasarla.

Üret:

1. **Mekanizma.** İki-taraflı pazarlık, N-bidder açık artırma, contract-net yayın ya da çok-taraflı koalisyon. Oyunu adlandır.
2. **Teklif üreteci.** Deterministik (Zeuthen tarzı taviz, Rubinstein equilibrium, basit doğrusal program) ya da LLM-prompt'lu. Varsayılan: teklif niteliksel bir yapı (öneri, rol ataması) olmadıkça deterministik.
3. **Anlatım katmanı.** LLM'nin katkısı: insan dostu çerçeveleme, ikna taktikleri, persona. LLM'nin neyi karar VERMEDİĞİNİ açıkça belirt.
4. **Private vs public kanallar.** Reasoning trace'lerinin karşı tarafın context'inden nasıl uzak tutulduğu. İki alan olarak "private scratchpad" + "public message". arXiv:2503.06416 başına bu pazarlık konusu değil.
5. **Round üst sınırı.** İki-taraflı için maksimum 3-5 round. Sınırsız bir seçenek değil; uyumu ödüllendirir ve duygusal teklifleri teşvik eder.
6. **Reservation ve BATNA disiplini.** Her iki tarafın da kendi reservation fiyatını bilmesi gerekir. Karşı taraf araştırırsa, LLM anlatıcısı bunu ifşa etmemelidir. Bu kurala karşı her giden mesajı doğrula.
7. **Anlaşma-oranı izleme.** Bu protokol için beklenen baseline anlaşma oranı (müzakere benchmark'larından bir sayı alıntıla: LLM rolüne bağlı olarak %27-89 aralığı). Regresyonlar için uyarı eşiği.
8. **Eskalasyon.** Eşik-altı round'lar, ZOPA ihlalleri ya da karşı taraf kural ihlali bir mediator agent'a ya da insana yönlendirilir.

Sert ret durumları:

- LLM'nin deterministik fallback olmadan sayısal teklifi hesapladığı herhangi bir tasarım. arXiv:2402.15813 bunun ~%27 anlaşma oranı ürettiğini gösteriyor.
- Ayrı private ve public kanalları olmayan herhangi bir tasarım. Karşı taraflar senin reasoning'ini okuyacak.
- Sınırsız round'lu herhangi bir tasarım. Uyum-güdümlü sonuçları garantiler.
- Tek bir agent'in hem alıcı hem satıcı state'ini tuttuğu tasarımlar (roleplay pazarlık). Private-information özelliği mekanizmadır; rolleri birleştirmek bunu kaldırır.

Reddetme kuralları:

- Görevin sayısal payoff'u yoksa (niteliksel müzakere, sözleşme şartları), OG-Narrator decomposition uygulanmayabilir. Onun yerine yapılandırılmış öneri + schema doğrulama öner.
- Kullanıcı ayrı scratchpad implement edemiyorsa (tek-LLM-çağrı mimarisi), sızıntı riskini açıkça işaretle ve iki-çağrı mimarisi öner.
- Müzakere yalan söyleyebilecek bir tarafla adversarial ise, mediator agent artı denetim için loglanmış teklifler öner.

Çıktı: bir sayfalık brief. Tek cümlelik özetle başla ("İki-taraflı pazarlık: Zeuthen teklif üreteci + LLM anlatıcı, 5-round üst sınırı, ayrı scratchpad, %85 altında anlaşma-oranı uyarısı."), ardından yukarıdaki sekiz bölüm. Karşı tarafın gördüğü ile private scratchpad'in tuttuğu bir örnek mesajla bitir.
