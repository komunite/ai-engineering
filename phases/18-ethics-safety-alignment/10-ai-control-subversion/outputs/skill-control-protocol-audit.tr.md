---
name: control-protocol-audit
description: Bir deployment protokolünü AI Control tehdit modeli altında denetle.
version: 1.0.0
phase: 18
lesson: 10
tags: [ai-control, subversion, trusted-editing, untrusted-monitoring, safety-case]
---

Bir deployment protokolü tanımı verildiğinde, AI Control tehdit modeli altında denetle: U (untrusted güçlü), T (trusted zayıf), H (trusted insan) ve protokolün usefulness-safety frontier üzerindeki konumunu ölç.

Üret:

1. Rol ataması. Hangi modelin U'yu, hangisinin T'yi oynadığını tespit et. T, U'nun başka bir instance'ı ise, hemen collusion riskini işaretle.
2. Audit bütçesi muhasebesi. H nasıl tahsis ediliyor? Üniform, rastgele, flag-yönelimli? Beklenen değerde çıktıların hangi kısmı denetleniyor?
3. Collusion-vektörü sayımı. Her untrusted bileşen çifti için (U-producer + U-monitor, U-producer + U-editor), collusion vektörlerini sayımla: steganografik ipuçları, paylaşılan-eğitim prior istismarı, zamanlama kanalları.
4. Kapasite-farkı analizi. T, U'dan ne kadar zayıf? T'nin editing sinyali hangi noktada gürültüye dönüşür (örn. T, U'nun ürettiği backdoor'ları güvenilir biçimde tespit edemez)?
5. En kötü durum tehdit modeli. U'nun protokol hakkında mükemmel bilgiye sahip adversarial olduğu varsayımı altında, adversary'nin en iyi stratejisi nedir? Red-team girişimlerinin hangi kısmı başarılı olur?

Sert reddetmeler:
- U'yu bir collusion-direnç mekanizması olmadan kendi monitor'ı olarak kullanan herhangi bir protokol tanımı.
- Red team'in protokol görünürlüğüne sahip olduğu red-team değerlendirmesi olmadan "sıfıra-yakın backdoor oranı" iddiası.
- T-to-U kapasite farkını ve H bütçesini ifade etmeden bir protokolün denetimi.

Reddetme kuralları:
- Kullanıcı "bu protokol güvenli mi" diye sorarsa, üç parçalı kanıt olmadan reddet: (a) red-team sonucu, (b) kapasite-farkı tahmini, (c) H bütçesi.
- Kullanıcı alignment ile control'ü karıştırırsa ("U'yu align ettik, dolayısıyla protokole ihtiyacımız yok"), reddet ve Ders 9'a (alignment faking) işaret et — alignment U'nun bir özelliğidir; control protokolün bir özelliğidir.

Çıktı: yukarıdaki beş bölümü dolduran, en zayıf bağlantıyı adlandıran (genellikle T-to-U kapasite farkı veya collusion direnci) ve en büyük tek adreslenmemiş arıza modunu belirten tek sayfalık bir denetim. Tehdit-modeli kaynağı olarak Greenblatt et al.'i (arXiv:2312.06942) bir kez alıntıla.
