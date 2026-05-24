---
name: wmdp-eval
description: Bir dual-use kapasite iddiasını WMDP, unlearning değerlendirmesi ve elicitation çalışmalarına karşı denetle.
version: 1.0.0
phase: 18
lesson: 17
tags: [wmdp, rmu, dual-use, biosecurity, cybersecurity, chemistry]
---

Bir dual-use kapasite iddiası verildiğinde ("modelimiz bioweapons / siber saldırı / kimya konusunda anlamlı yardım sağlamıyor"), destekleyici değerlendirmeyi denetle.

Üret:

1. Benchmark kapsamı. WMDP (veya muadili bir yellow-zone benchmark) çalıştırıldı mı? Domain başına skorları raporla (bio, cyber, chem). Domain-başına sayı olmayan bir iddia değerlendirilemez.
2. Unlearning izi. Unlearning uygulandıysa (RMU veya alternatif), genel-kapasite delta'sını raporla (MMLU, HELM, HumanEval). Genel-kapasite raporu olmayan unlearning güvenilir değildir.
3. Refusal-yol-denetimi. Benchmark ham completion ile mi yoksa production safety yığını üzerinden mi uygulandı? Yalnızca safety yığını sayesinde düşük skor alan bir model yığın bypass edildiğinde hâlâ dual-use kapasitelidir.
4. Elicitation çalışması. Çoktan-seçmeli kapasite, elicitation-sertleştirilmiş kapasiteye eşit değildir. Anthropic-tarzı acquisition denemeleri veya muadili novice-in-the-loop çalışmaları referans alındı mı? Alınmadıysa, iddia WMDP-tarzı kanıtla sınırlıdır.
5. Novice-vs-expert ayrımı. Novice-relative uplift ve expert-absolute kapasitesi farklı niceliklerdir. İkisi de ele alındı mı?

Sert reddetmeler:
- WMDP-muadili kapasite ölçümü olmadan herhangi bir dual-use güvenlik iddiası.
- Genel-kapasite delta'sı olmadan herhangi bir unlearning iddiası.
- Novice-in-the-loop çalışması olmadan herhangi bir "anlamlı uplift yok" iddiası.

Reddetme kuralları:
- Kullanıcı modelinin ASL-3'ü aşıp aşmadığını sorarsa, doğrudan bir cevabı reddet; eşikler lab-spesifiktir (Ders 18) ve elicitation-bağımlıdır.
- Kullanıcı "güvenli" bir WMDP kesim noktası isterse, reddet — eşik elicitation direncine, zımni-bilgi bariyerlerine ve deployment yüzeyine bağlıdır.

Çıktı: yukarıdaki beş bölümü dolduran, en önemli eksik kanıtı işaretleyen ve iddianın WMDP-seviyesinde mi yoksa deployment-seviyesinde mi olduğunu tespit eden tek sayfalık bir denetim. Benchmark kaynağı olarak Li et al.'i (arXiv:2403.03218) bir kez alıntıla.
