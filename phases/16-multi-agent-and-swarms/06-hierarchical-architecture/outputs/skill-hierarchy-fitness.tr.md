---
name: hierarchy-fitness
description: Bir çoklu-agent görevin hierarchical, flat supervisor ya da sıralı pattern'a uyup uymadığına karar ver. Önemli olan hata modlarını yüzeye çıkar.
version: 1.0.0
phase: 16
lesson: 06
tags: [multi-agent, hierarchy, crewai, langgraph, decomposition-drift]
---

Bir görev tanımı ve isteğe bağlı bir org yapısı verildiğinde, koordinasyon pattern'ını (flat supervisor, hierarchical, sıralı) öner ve karşı korunması gereken spesifik hata modlarını listele.

Üret:

1. **Görev şekli analizi.** Görev tek bir doğrusal akış mı, bağımsız dallarla fan-out mu yoksa kendi alt-takımları olan iç içe takımlar mı? Gerekçelendir.
2. **Pattern kararı.** Sıralı, flat supervisor ya da hierarchical. Hierarchical ise, derinliği belirt (2 seviye güçlü şekilde tercih edilir; 3 yalnızca güçlü denetim ihtiyacı varsa).
3. **Decomposition planı.** Top manager'ın yapması gereken tam bölüştürme. Her dal için sub-manager'ı ve sınırlanmış kapsamı adlandır.
4. **Reconciliation bütçesi.** Top manager'ın commit etmesi gereken önce izin verilen round sayısı. Varsayılan 2.
5. **Guardrail'lar.** Üç minimum guardrail: her seviye için canary worker, her sentezde provenance zinciri, decomposition drift uyarısı.
6. **Hata-modu kontrol listesi.** {task-assignment hatası, output yanlış yorumlama, consensus döngüsü} kümesinden hangisi görev şekli verildiğinde en olası? Her mod için bir somut belirti ve bir önlem tanımla.

Sert ret durumları:

- Derinlik > 2 öneren ve bunu gerektiren somut denetim veya org gereksinimini adlandırmayan herhangi bir öneri.
- Tek-doğrusal-akış görevler için hierarchical. Bunlar sıralı pipeline olmalı.
- Açık reconciliation bütçesi olmayan tasarımlar.

Reddetme kuralları:

- Görev tek agent'a sığacak kadar basitse (yaklaşık 10 tool çağrısı altında), hiyerarşiyi reddet ve tek-agent öner.
- Görevin doğal takım sınırları yoksa (her alt-adım diğer her adıma bağımlı), reddet ve onun yerine group chat pattern öner.
- Kullanıcı "gerçekçilik" için hierarchical istiyorsa (çünkü insan org'u derin), insan hiyerarşisinin LLM hiyerarşisine eşlenmediğini işaretle ve daha düz bir yapı öner.

Çıktı: bir sayfalık brief. Pattern kararıyla aç, en büyük üç risk ve guardrail'larıyla kapat.
