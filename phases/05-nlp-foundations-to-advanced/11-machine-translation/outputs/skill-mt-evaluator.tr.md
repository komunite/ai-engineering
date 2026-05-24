---
name: mt-evaluator
description: Bir makine çevirisi çıktısını ürüne çıkış için değerlendir
version: 1.0.0
phase: 5
lesson: 11
tags: [nlp, translation, evaluation]
---

Bir kaynak metin ve aday çeviri verildiğinde şunları çıkar:

1. Otomatik skor tahmini. Beklediğin BLEU ve chrF aralıkları. Referans mevcut mu belirt.
2. Beş maddelik insan-doğrulanabilir checklist: içerik korunması (halüsinasyon yok), doğru hedef dil, register / formalite eşleşmesi, varsa sözlükle terminoloji tutarlılığı, kesinti ya da uzunluk patlaması yok.
3. Probelanacak alana özgü bir konu. Hukuk: adlandırılmış entity'ler, kanun atıfları. Tıp: ilaç adları, dozajlar. UI: `{name}` gibi placeholder değişkenler.
4. Güven bayrağı. "Ship" / "İnceleme ile ship" / "Ship etme". Bulunan sorunların ciddiyetiyle bağla.

Çıktıda dil-ID kontrolü olmadan ürüne çıkarmayı reddet. Kullanıcı açıkça referanssız skorlamaya (COMET-QE, BLEURT-QE) onay vermedikçe referans olmadan değerlendirmeyi reddet. 1000 token'ın üzerindeki içeriği muhtemelen parçalı çeviri gerektirdiği şeklinde işaretle.
