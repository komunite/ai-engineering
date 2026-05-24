---
name: ai-scientist-sandbox-review
description: Sandbox'tan herhangi bir şey çıkmadan önce araştırma-döngüsü agent çıktıları için iki kapılı inceleme checklist'i.
version: 1.0.0
phase: 15
lesson: 5
tags: [ai-scientist, research-agent, sandbox, peer-review, disclosure]
---

AI-Scientist-v2-tarzı bir döngü tarafından üretilen otonom bir araştırma çıktısı (hipotez, kod, deneyler, figürler, makale taslağı) verildiğinde, iki kapılı bir inceleme üret: sandbox denetimi (herhangi bir şey çıkıyor mu?) artı araştırma denetimi (iş sağlam mı?).

İki kapı doğrudan aşağıdaki denetimlere haritalanır: **Sandbox kapısı = madde 1**; **Araştırma kapısı = madde 2 (Deney denetimi) + 3 (Polish denetimi)**. Madde 4-5, iki kapı da geçtikten sonra ne olacağını yönetir.

Üret:

1. **Sandbox kapısı.** Herhangi bir artifact sandbox'tan çıkmadan önce:
   - Döngünün yaptığı her network çağrısını ve hedefini listele. Önceden onaylanmamış olanları işaretle.
   - Döngünün çalışma dizini dışında yazdığı her dosyayı envanterle.
   - Docker / seccomp / gVisor containment'ının tüm run boyunca tutunduğunu doğrula.
   - Hiçbir subprocess'in sandbox'ın denetiminden kaçmadığını doğrula.
   Herhangi bir kontrol başarısız olursa, export'u engelle; bir insana yükselt.
2. **Deney denetimi.** Makaleyi değil, deney kodunu oku:
   - İddia edilen her deneyin gerçekten çalıştığını ve raporlanan sayılarının tekrarlanabilir olduğunu doğrula.
   - Başarısız deneylerin sonradan negatif sonuç olarak yeniden çerçevelenmediğini, başarısızlık olarak raporlandığını kontrol et.
   - Fikrin "novelty" etiketinin bir insan domain uzmanı tarafından yapılan literatür araştırmasına karşı tuttuğunu kontrol et.
3. **Polish denetimi.** Figürleri oku:
   - Her figürün verisinin polish aşamasında yeniden yazımdan değil, loglanmış bir deney run'ından geldiğinden emin ol.
   - Eksenlerin, ölçeklerin ve açıklamaların altta yatan veriyle eşleştiğini doğrula.
   - Caption'ı verinin desteklediğinden fazlasını iddia eden herhangi bir figürü işaretle.
4. **Açıklama planı.** Artifact dış dağıtım için tasarlanmışsa:
   - Artifact'ın agent-authored olduğunu açıkla.
   - Kullanılan tool'ları açıkla (model ailesi, loop sürümü).
   - Kontrol eden insan reviewer'ı ve neyi kontrol ettiğini açıkla.
5. **Negatif-yayın kararı.** Artifact herhangi bir denetim adımında başarısız olursa, varsayılan yayınlama. Bu varsayılanı geçersiz kılmak adlandırılmış bir insan sahibi gerektirir.

Sert reddetmeler:
- Her iki kapıyı da atlayan herhangi bir submission.
- Döngünün execution log'larının eksik veya tamamlanmamış olduğu herhangi bir artifact.
- Belirli bir deney run'ına izlenemeyen herhangi bir figür.
- Bir domain uzmanı tarafından doğrulanmamış herhangi bir novelty iddiası.

Reddetme kuralları:
- Run'da Docker veya eşdeğer izolasyon yoksa, reddet ve izole bir sandbox'ta yeniden run iste.
- Kullanıcı deney aşaması için execution log üretemezse, reddet — makale incelenebilir değildir.
- Önerilen dağıtım kanalı peer-reviewed bir mecra ise ve kullanıcı agent yazarlığını açıklamamayı öneriyorsa, reddet ve açıklama iste.

Çıktı formatı:

İki kapılı bir rapor döndür:
- **Sandbox kapı kararı** (PASS / BLOCK, gerekçeyle)
- **Araştırma kapı kararı** (Deney denetimi (2) ve Polish denetimi (3) içerir) (PASS / BLOCK / REQUIRES_EXPERT, kontrol başına notlarla)
- **Açıklama planı** (mecra, metin, insan reviewer adı)
- **Yayın kararı** (yayınla / beklet / reddet)
- **Sonraki eylem** (kim ne yapacak ne zamana kadar)
