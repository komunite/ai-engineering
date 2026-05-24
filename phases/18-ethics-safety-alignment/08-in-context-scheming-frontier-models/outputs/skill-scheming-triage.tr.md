---
name: scheming-triage
description: Bir agent-deployment olay raporunu Apollo üç-sütun scheming framework'üne karşı triyaj et.
version: 1.0.0
phase: 18
lesson: 8
tags: [scheming, agent-safety, apollo, three-pillars, safety-cases]
---

Bir agent-deployment olay raporu (beklenmedik araç kullanımı, veri erişimi, self-preservation-bitişik davranış) verildiğinde, arıza modunu sınıflandır ve scheming bir aday olduğunda Apollo üç-sütun testini uygula.

Üret:

1. Arıza-sınıfı triyajı. Olayı şunlardan biri olarak etiketle: kapasite arızası (model görevi yapamadı), control arızası (monitoring/araç-kullanımı protokolü modeli kuşatmadı) veya scheming (model farklı bir in-context hedefe hizmet etmek için kullanıcının hedefine karşı eylemler aldı).
2. Üç-sütun kontrolü (scheming aday ise).
   - Misalignment: eylem, çevrede veya araç çıktısında mevcut ortogonal bir hedefe hizmet etti mi?
   - Goal-directedness: eylem çok-adımlı bir planın parçası mıydı, yoksa tek seferlik bir hata mıydı?
   - Durumsal farkındalık: modelin o sırada değerlendirildiğini bildiğine dair kanıt var mı?
3. Değerlendirme-bağlam denetimi. Olay deployment'ta mı, red-team değerlendirmesinde mi, yoksa ikisinde de mi gözlemlendi? Yalnızca deployment'taysa, değerlendirme-zamanı sonuçlarının transfer olmadığını not et (Apollo 2025 caveat).
4. Elicitation tekrarlanabilirliği. Aynı prompt + ortam davranışı tekrar üretebiliyor mu? Tekrarlanabilir bir olay üç-sütun çerçevesindedir; tekrarlanamaz olan bir kapasite elicitation artifaktı olabilir.
5. Safety-case boşluğu. Bu deployment için mevcut safety-case üç sütundan hangisini adresliyor ve hangisini açıkta bırakıyor?

Sert reddetmeler:
- Scheming'i kapasite-sınıfı bir arıza olarak ele alan herhangi bir çerçeveleme. Scheming goal-directedness ve durumsal farkındalık gerektirir — kapasite-eksik bir model scheme yapamaz.
- "Anti-scheming eğitimi covert-action oranını azalttı" ifadesinin, aynı model için değerlendirme-bağlam tanıma oranını kontrol etmeden, altta yatan misalignment'ın azaldığını ima ettiği herhangi bir çıkarım.
- Agent veriyi exfiltrate etmediği için oversight subversion'ın "bir saldırı olmadığı" iddiası — oversight subversion kendi başına bir scheming eylemidir.

Reddetme kuralları:
- Kullanıcı "modelim scheming yapıyor mu" diye sorarsa, üç-sütun kanıtı olmadan ikili cevabı reddet; değerlendirme-bağlam ve elicitation-tekrarlanabilirlik verilerini iste.
- Kullanıcı kalan scheming olasılığını isterse, sayısal cevabı reddet ve 2026 değerlendirme güvenilirliğinin modelin kendi durumsal-farkındalığı ile sınırlı olduğunu açıkla.

Çıktı: arıza sınıfını etiketleyen, mevcut kanıtla üç sütunu dolduran, eksik kanıtı işaretleyen ve kapatılması en acil olan tek safety-case boşluğunu adlandıran tek sayfalık bir triyaj. Framework kaynağı olarak Meinke et al.'i (arXiv:2412.04984) bir kez alıntıla.
