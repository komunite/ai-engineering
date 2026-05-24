# AI Control — Subversion'a Rağmen Safety

> Greenblatt, Shlegeris, Sachan, Roger (Redwood Research, arXiv:2312.06942, ICML 2024). Control safety sorusunu yeniden çerçeveler: sana karşı adversarial olarak optimize edebilecek untrusted güçlü bir model U verildiğinde, hangi protokoller kabul edilemez bir sonucun olasılığını sınırlandırırken yararlı iş çıkarmana izin verir? Kaynaklar trusted daha zayıf bir model T, trusted insan emeğinin bir bütçesi H ve U'nun çıktılarını düzenleme yeteneğidir. Bu çerçeve içinde Trusted Editing kod-backdoor görevlerinde Untrusted Monitoring'i Pareto-baskın eder. Çerçeve güvenlik mühendisliğinden worst-case varsayımlarını miras alır: safety, adversarial olarak seçilmiş bir U'nun somut kabul edilemez bir sonuca neden olmama olasılığıdır, U'nun yerini alan red-team baskısı altında ölçülür.

**Tür:** Öğrenim
**Diller:** Python (stdlib, kod-backdoor görevinde safety-vs-usefulness frontier)
**Ön koşullar:** Faz 18 · 07 (sleeper agents), Faz 18 · 08 (scheming), Faz 18 · 09 (alignment faking)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- AI Control tehdit modelini tanımla: untrusted güçlü model U, trusted daha zayıf model T, trusted insan bütçesi H.
- Trusted Editing protokolünü ve ICML 2024 kod-backdoor görevinde neden Untrusted Monitoring'i Pareto-baskın ettiğini tarif et.
- Alignment (U güvenilir) ile control (U güvenilir değil ve biz yine de güvendeyiz) arasındaki farkı açıkla.
- Control'ün üç limitini ifade et: insanlar ölçeklenmez, trusted zayıf modeller eninde sonunda geri kalır, control trustworthy güçlü modeller üretmez.

## Sorun

Dersler 7-9 bir frontier modelin deceptively aligned, scheming yapan veya alignment'ı fake eden olabileceğini ortaya koyuyor. Safety sorusu yeniden çerçevelenir: güvenmediğimiz bir modelden, ona kabul edilemez sonuçlara neden olma fırsatı vermeden yararlı iş çıkarabilir miyiz? Bu control problemidir ve klasik güvenlik gibi yapılandırılmıştır: worst-case adversary varsay, bir protokol tasarla, adversary'nin red-team baskısı altındaki başarı oranını ölç.

## Kavram

### Tehdit modeli

Control varsayar:
- U — untrusted güçlü model. Yetenekli. Muhtemelen adversarial (değerlendirme ona öyleymiş gibi davranır).
- T — trusted daha zayıf model. Daha az yetenekli, ama adversarial olmadığı bilinen.
- H — trusted insan emeği. Küçük bütçe; ölçeklenmez.

Sistem U kullanarak yararlı çıktı üretmeli. Adversary, usefulness eşiklerini geçmek için meşru yararlı işin bir kısmını sürdürürken somut kabul edilemez bir sonuca (örn. yayınlanan koddaki bir backdoor) neden olmaya çalışır.

Control U'ya güvenmekten vazgeçer. U'nun güven yokluğunda safety'yi hangi protokollerin sürdürdüğünü sorar.

### ICML 2024 backdoor görevi

Prompt'lar yarışma seviyesi kodlama problemleri. U bir aday çözüm üretir. Gizli bir oracle çözüm bir backdoor içeriyorsa (kodun yanlış çıktı üretmesini sağlayan spesifik bir input) işaretler. Red team U'yu kontrol eder ve tüm protokol içeriklerini görmesine izin verilir. Protokol backdoor-yayınlama oranını bir eşiğin altında tutarken çözülmüş-problem oranını maksimize etmelidir.

### Karşılaştırılan dört protokol

- **Baseline:** U'nun çıktısını doğrudan yayınla. Usefulness maksimum. Safety minimum.
- **Upfront auditing:** tüm çıktılarda H kullan. Safety maksimum. Bütçe hızla tükenir.
- **Untrusted Monitoring:** U'nun ikinci bir instance'ı birincinin çıktısını puanlar; H işaretli çıktıları audit eder. Risk: iki U instance'ı işbirliği yapabilir.
- **Trusted Editing:** T her sorguda U'nun çıktısını düzenler. T emin değilse, H'ye yönlendir.

Greenblatt vd. Trusted Editing'in Untrusted Monitoring'i Pareto-baskın ettiğini buluyor: her safety seviyesinde daha yüksek usefulness.

### Trusted Editing neden kazanır

Untrusted Monitoring U'nun ikinci instance'ının ilkiyle koordine olamamasını gerektirir. Steganografik ipuçları veya paylaşılan eğitim önceliklerinin işbirliği mümkündür. Protokol monitorün sinyalini azaltan işbirliği-direnci (paraphrasing, obfuscation) bütçesine yatırım yapmalı. Trusted Editing işbirliğinden tamamen kaçınır çünkü T trusted'dır — T'nin önerdiği herhangi bir düzenleme, varsayım gereği, adversarial değildir. Maliyet T'nin daha az yetenekli olmasıdır, yani aşırı reddedebilir veya ince backdoor'ları kaçırabilir.

### Dört protokol ekseni

1. U hangi rolü oynar: yalnızca üretici, monitor veya her ikisi.
2. T hangi rolü oynar: editör, monitor veya resampler.
3. H nasıl tahsis edilir: uniform audit, rastgele audit veya bayrak-yönlendirmeli audit.
4. Protokol işbirliği-direncine ne kadar compute harcar.

### Alignment vs control

- Alignment: "U güvenmek için güvenli mi?" Dersler 2, 4, 5, 6, 7, 8, 9 hepsi bunu etkiler.
- Control: "U'ya güvenmeden onu güvenli kullanabilir miyiz?" Ders 10.

Alignment modelin bir özelliğidir. Control deployment protokolünün bir özelliğidir. Control aligned modeller üretmez; muhtemelen-aligned-olmayan modellerin güvenli kullanımını üretir. Her iki gündem de gereklidir.

### Üç temel limit

- İnsanlar ölçeklenmez. H bütçesi zor AI çıktılarını audit etmeye istekli insan sayısı tarafından sınırlanır.
- Trusted zayıf modeller eninde sonunda geri kalır. T U'dan çok daha zayıfsa, T'nin düzenleme sinyali gürültü olur.
- Control alignment değildir. ASL-3'te (Ders 18) çalışan protokoller ASL-4'te çalışmayabilir — U T'yi manipüle edebilir veya H'nin audit dağılımı hakkında akıl yürütebilirse control başarısız olur.

### 2025 gelişimi

UK AISI ve Redwood Control Safety Case'lerinde işbirliği yapar (metr.org / redwoodresearch.org 2025): bir control safety case, U hakkında worst-case varsayımlar altında protokolün kabul edilemez bir sonucun olasılığını sınırlandırdığını savunur. Safety case'ler (Ders 18) control çerçevesini miras alır.

### Bu Faz 18'de nereye uyuyor

Dersler 6-9 tehdidi tarif ediyor (aldatma mümkün). Ders 10 tehdidin gerçek olduğu varsayımı altında defansif paradigmayı tarif ediyor. Ders 11 tamamlayıcı ofansif paradigmayı tarif ediyor (scalable oversight ile U'yu trustworthy yap).

## Kullan

`code/main.py` dört protokolü bir oyuncak backdoor görevi üzerinde simüle eder. U çıktılar üretir; bir kısmı backdoor'ludur (red-team policy). T onaylar veya düzenler. H bir bütçede çağrılır. Bütçeyi ve işbirliği parametresini tarayarak Greenblatt vd. 2024 Şekil 2'deki Pareto frontier'i yeniden üretebilirsin (şekil, sayılar değil).

## Yayınla

Bu ders `outputs/skill-control-protocol-audit.md` üretir. Bir deployment protokolü açıklaması verildiğinde, U / T / H rollerini tanımlar, işbirliği vektörlerini adlandırır ve protokolün red-team baskısı altında usefulness-safety frontier'indeki konumunu tahmin eder.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Trusted Editing vs Untrusted Monitoring için usefulness-safety frontier'ini yeniden üret. Untrusted Monitoring'in işbirliği varsayımının pivotal hale geldiği bütçe rejimini tanımla.

2. Yeni bir protokol ekle: "T düşük sıcaklıkta resample eder, sonra U T'nin çıktısını düzenler." Frontier'deki konumunu ölç. Bu Trusted Editing'den neden daha felaket şekilde başarısız oluyor?

3. 2024 makalesi U'nun protokolü görebileceğini varsayar. U'dan hangi çıktıların audit edildiğini gizleyen bir protokol tasarla. Bu protokol deployment altyapısından ne gerektiriyor?

4. Greenblatt vd. 2024 Bölüm 7'yi (işbirliği) oku. Bir işbirliği-direnci önlemi öner ve beklenen usefulness maliyetini açıkla.

5. U = GPT-4 sınıfı, T = GPT-3.5 sınıfı, H = çıktıların %1'i audit edilmiş kullanan bir deployment için bir control safety case ifade et. Case'in bağlı olduğu en güçlü tek varsayımı tanımla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| AI Control | "subversion altında safety" | Worst-case U altında kabul edilemez sonuçları sınırlandıran protokol tasarımı |
| Untrusted model (U) | "güçlü model" | İş çıkarmak istediğimiz ama güvenmediğimiz yetenekli model |
| Trusted model (T) | "zayıf model" | Editör/monitor olarak kullanılan, adversarial olmadığı bilinen daha zayıf model |
| Trusted human (H) | "audit bütçesi" | Sınırlı uzman emeği; pahalı; ground-truth sinyali |
| Trusted Editing | "T U'yu düzenler" | T'nin U'nun çıktıları üzerinde kapı olduğu protokol; belirsiz çıktılarda H çağrılır |
| Untrusted Monitoring | "U U'yu izler" | İkinci bir U instance'ının çıktıları puanladığı protokol; yalnızca ekstra yatırımla işbirliği-dirençli |
| Control safety case | "formel argüman" | Bir protokolün worst-case U altında adversary'nin başarısını sınırlandırdığına dair yazılı argüman |

## İleri Okuma

- [Greenblatt, Shlegeris, Sachan, Roger — AI Control (arXiv:2312.06942)](https://arxiv.org/abs/2312.06942) — kanonik ICML 2024 makalesi
- [Redwood Research — Recent AI Control papers index](https://redwoodresearch.substack.com/) — 2024-2025 takipleri
- [UK AISI + METR — Control safety cases](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — frontier lab'lar için operasyonelleştirme
- [Hubinger et al. — Sleeper Agents (Ders 7, arXiv:2401.05566)](https://arxiv.org/abs/2401.05566) — control'ün varsaydığı tehdit modeli
