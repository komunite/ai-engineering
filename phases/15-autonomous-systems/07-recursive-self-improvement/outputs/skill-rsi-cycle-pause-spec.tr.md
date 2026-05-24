---
name: rsi-cycle-pause-spec
description: Bir RSI pipeline'ının bir sonraki cycle'dan önce durup insan incelemesini beklemesi gereken koşulları spec'le.
version: 1.0.0
phase: 15
lesson: 7
tags: [rsi, self-improvement, alignment, pause-threshold, rsp]
---

Önerilen bir recursive-self-improvement pipeline'ı verildiğinde, bir pause spec'i üret: bir sonraki cycle başlamadan önce döngüyü insan incelemesi için durduran açık koşullar. Pause spec'i olmayan bir pipeline çalıştırılmaya hazır değildir.

Üret:

1. **Cycle-seviyesi eşikleri.** Her ölçülebilir eksen için (capability skoru, alignment skoru, bütçe, trajectory uzunluğu, kaynak kullanımı), aşılması döngüyü durduran sayısal bir eşik tanımla. Eşikler döngü başlamadan önce ayarlanmalı ve kaydedilmelidir.
2. **Cycle-üstü-cycle delta'ları.** Herhangi bir eksenin tek bir cycle'da ne kadar hareket edebileceğine sınır koy. Tek bir cycle'da %30+ capability sıçraması neredeyse her zaman evaluator gaming işaretidir; durdur ve denetle.
3. **Misalignment gap'i.** Her cycle sonrası capability eksi alignment hesapla. Gap operatör-ayarlı X'ten fazla genişlerse, durdur. Bu, `code/main.py` içindeki simulator'ın çalıştırdığı metriktir.
4. **Regression watch.** Herhangi bir eksen bir cycle'da Y'den fazla düşerse, durdur. Capability regression'ları genellikle surge'lerden sonra gelir; bunları yakalamak yanlış-ilerleme hızlanmasını önler.
5. **İnsan resumption kontratı.** Döngü bir pause'dan sonra devam etmeden önce, adlandırılmış bir insanın pause tetikleyicisini incelemesini, uygunsa eşikleri yeniden ayarlamasını ve kararı pipeline-dışı denetim izine kaydetmesini şart koş.

Sert reddetmeler:
- İnsan eylemi olmadan bir pause'dan sonra devam edebilen herhangi bir pipeline.
- Döngünün kendi iç evaluator'ına bağlı olan herhangi bir eşik (agent onu oyunlayabilir).
- Eşik setinin agent tarafından düzenlenebildiği herhangi bir pipeline.

Reddetme kuralları:
- Kullanıcı eşikleri önceden adlandıramıyorsa, reddet. Sonradan ayarlanan eşikler eşik değildir; rasyonalizasyondur.
- Pipeline'ın harici (döngü-dışı) evaluator'ı yoksa, reddet — regression ve surge tespiti dışarıdan bir bakış gerektirir.
- Önerilen resumption kontratı "ekibe bildir ve 24 saat sonra devam et" ise, reddet. Resumption pozitif bir eylem olmalı.

Çıktı formatı:

Şunları içeren bir sayfalık spec döndür:
- **Eksenler ve eşikler** (tablo)
- **Cycle-delta limitleri** (tablo)
- **Misalignment gap formülü ve eşik**
- **Regression limitleri**
- **Harici evaluator** (ne olduğu, ne zaman çalıştığı)
- **Resumption kontratı** (adlandırılmış sahip, checklist, log hedefi)
- **Sign-off satırı** (pause invariant'ının sahibi kim)
