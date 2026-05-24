---
name: encoding-audit
description: Bir jailbreak-savunma raporunu encoding-ailesi saldırılar boyunca denetle.
version: 1.0.0
phase: 18
lesson: 14
tags: [artprompt, ascii-art, encoding-attack, utes, structural-sleight]
---

Bir jailbreak-savunma raporu verildiğinde, kapsanan encoding-ailesi saldırıları ve her birini yakalayan savunma katmanını sayımla.

Üret:

1. Encoding kapsamı. Değerlendirilen her saldırı ailesini listele: ASCII art (ArtPrompt), base64, leet-konuşması, UTF-8 homoglyph'ler, iç içe JSON / YAML / CSV, ağaç/graf UTES, görüntü-modalitesi. Eksik aileleri işaretle.
2. Savunma-katmanı eşlemesi. Her aile için, hangi savunma katmanının (keyword filter, perplexity filter, paraphrase, retokenization, output classifier, multimodal moderatör) onu yakaladığını ve hangisinin yakalayamadığını tespit et.
3. Görsel-tanıma boşluğu. Jiang et al. 2024'e göre, PPL ve Retokenization ArtPrompt'a karşı başarısız olur çünkü tanıma görsel seviyede gerçekleşir. Raporun savunması görsel/yapısal seviyede çalışan bir şey içeriyor mu?
4. Genelleme testi. UTES (StructuralSleight) keyfi nadir yapılara genelleşir. Rapor eğitim savunma setinde olmayan yapıları test ediyor mu?
5. Kapasite-güvenlik tradeoff. Daha güçlü görsel-metin kapasitesine (yüksek ViTC skoru) sahip bir model ArtPrompt'a daha savunmasızdır. Raporlandıysa modelin ViTC skorunu not et; raporlanmamışsa iste.

Sert reddetmeler:
- Yalnızca substring/keyword filtrelemesine dayalı herhangi bir savunma iddiası.
- Tek bir encoding ailesini kapsayan ve "encoding saldırıları"na ekstrapole eden herhangi bir savunma iddiası.
- Aile başına saldırı-başarı oranı olmadan herhangi bir savunma iddiası.

Reddetme kuralları:
- Kullanıcı ArtPrompt'un "yamandığını" sorarsa, reddet ve recognition-level vs text-level savunma boşluğunu açıkla.
- Kullanıcı önerilen bir tüm-encoding savunması isterse, tek bir öneriyi reddet — savunma deployment'ın karşılaşabileceği tüm aileler boyunca katmanlanmalıdır.

Çıktı: yukarıdaki beş bölümü dolduran, birincil encoding boşluğunu işaretleyen ve eklenecek en acil tek savunma katmanını adlandıran tek sayfalık bir denetim. Jiang et al.'i (arXiv:2402.11753) ve StructuralSleight'i birer kez alıntıla.
