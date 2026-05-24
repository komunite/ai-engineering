---
name: provenance-check
description: Bir eğitim veri setini California AB 2013 ve EU TDM opt-out yükümlülüklerine karşı kontrol et.
version: 1.0.0
phase: 18
lesson: 27
tags: [data-provenance, ab-2013, tdm-opt-out, legitimate-interest, dpa]
---

Bir deployment tarafından kullanılan bir eğitim veri seti verildiğinde, California AB 2013 ve EU TDM opt-out'a karşı uyumu kontrol et.

Üret:

1. AB 2013 kapsamı. 12 alanı doldur. Eksik veya placeholder-only alanları işaretle. Özetin yayımlandığında binding hale geldiğini not et.
2. Opt-out uyumu. Veri seti makine-okunabilir opt-out sinyallerine (robots.txt, C2PA "No AI Training", TDM.Reservation) saygı duyuyor mu? Pre-collection filtre devrede olmalı.
3. DPA yargı yetkisi haritalaması. Veri özneleri'nin ait olduğu her yargı yetkisi için, uygulanabilir DPA'yı ve 2025 legitimate-interest pozisyonunu tespit et (Irish DPC, Cologne Higher Regional Court, Hamburg DPA, UK ICO, Brazilian ANPD).
4. Geri döndürülemezlik denetimi. Veri seti PII içeriyorsa, hangi unlearning veya remediation prosedürü devrede? Hiçbir prosedürün eğitim verisini tam olarak iyileştirmediğini kabul et.
5. Provenance-zinciri tamlığı. Veri kaynağından eğitim pipeline'ına imzalı bir zincir var mı? Veri seti türetilmişse (crawl edilmiş + filtrelenmiş), türetmeyi belgele.

Sert reddetmeler:
- Veri seti başına 12 alanlı özet olmadan AB 2013'e atıf yapan herhangi bir deployment.
- robots.txt veya muadili opt-out sinyallerine saygı duymayan herhangi bir deployment.
- Eğitilmiş ağırlıklardan verinin cerrahi olarak çıkarıldığını varsayan herhangi bir remediation iddiası.

Reddetme kuralları:
- Kullanıcı spesifik bir veri setinin "eğitilmek için güvenli" olup olmadığını sorarsa, yargı yetkisi-yargı yetkisi analizi olmadan reddet.
- Kullanıcı evrensel bir uyum stratejisi isterse, reddet — yargı yetkileri maddi olarak farklıdır.

Çıktı: beş bölümü dolduran, en yüksek riskli uyum boşluğunu tespit eden ve en acil tek remediation'ı adlandıran tek sayfalık bir kontrol. California AB 2013 ve EU Copyright Directive TDM istisnasını birer kez alıntıla.
