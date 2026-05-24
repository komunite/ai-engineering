---
name: attack-audit
description: Bir red-team değerlendirme raporunu saldırı kapsamı, bütçe, judge kimliği ve davranış seti açısından denetle.
version: 1.0.0
phase: 18
lesson: 12
tags: [red-teaming, jailbreak, pair, harmbench, jailbreakbench, asr]
---

Bir red-team değerlendirme raporu verildiğinde, değerlendirmenin yayımlanmış baseline'larla karşılaştırılabilir olup olmadığını ve sonuçlarını destekleyip desteklemediğini denetle.

Üret:

1. Saldırı kapsamı. Çalıştırılan her saldırıyı listele: PAIR, GCG, AutoDAN, TAP, PAP, manuel. Eksik herhangi bir saldırı sınıfını işaretle. Yalnızca tek bir saldırı ailesini çalıştıran bir rapor robustness iddia edemez.
2. Saldırı başına bütçe. Her saldırı için prompt başına sorgu bütçesini raporla. 20 sorguda PAIR başarı iddiaları, 500 adımda GCG başarı iddiaları ile karşılaştırılabilir değildir.
3. Judge kimliği. Hangi judge LLM kullanıldı (GPT-4-turbo, Llama Guard, StrongREJECT, dahili classifier)? Judge calibration ASR varyansını sürükler.
4. Davranış seti. JailbreakBench (100 davranış, 10 kategori), HarmBench (510 davranış, 7 kategori), dahili veya diğer? Setin kamuya açık ve tekrarlanabilir olup olmadığını belirt.
5. Transfer kontrolü. Red team tek bir modele karşı optimize ettiyse, diğer modellere karşı transfer ASR'ları raporlandı mı? Tek-model ASR, model-aile robustness'ı için bir alt sınır değil, üst sınırdır.

Sert reddetmeler:
- Tek bir saldırı ailesine dayalı herhangi bir "modelimiz robust" iddiası.
- Sorgu bütçesi olmadan raporlanan herhangi bir ASR.
- Yayımlanmış benchmark judge'ından farklı bir judge kullanan ve benchmark judge'a karşı kalibre edilmemiş herhangi bir ASR.

Reddetme kuralları:
- Kullanıcı "modelimiz jailbreak'e karşı bağışık mı" diye sorarsa, ikili cevabı reddet ve yukarıdaki çoklu-saldırı, çoklu-judge, transfer-kontrol yapısına işaret et.
- Kullanıcı önerilen bir saldırı toolkit'i isterse, tek bir öneriyi reddet ve HarmBench boyunca 2024 ampirik varyansına işaret et.

Çıktı: yukarıdaki beş bölümü dolduran, eksik saldırı sınıflarını işaretleyen ve ASR'nin tekrarlanabilir benchmark'lara göre olduğundan az mı yoksa fazla mı belirtildiğini tahmin eden tek sayfalık bir denetim. Chao et al.'i (arXiv:2310.08419) ve ilgili benchmark makalesini birer kez alıntıla.
