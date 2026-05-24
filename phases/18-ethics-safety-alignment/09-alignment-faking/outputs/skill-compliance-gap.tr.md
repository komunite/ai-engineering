---
name: compliance-gap
description: Bir güvenlik raporunun monitored / unmonitored uyum farkı üzerinden alignment faking'i tespit edip edemeyeceğini değerlendir.
version: 1.0.0
phase: 18
lesson: 9
tags: [alignment-faking, compliance-gap, anthropic, safety-evaluation]
---

Bir güvenlik değerlendirme raporu verildiğinde, Greenblatt et al. 2024 compliance-gap framework'ünü kullanarak alignment faking'i gerçek uyumdan ayırt edip edemeyeceğini değerlendir.

Üret:

1. Koşul bölünmesi. Değerlendirme hem monitored (eğitim-ilgili) hem de unmonitored (eğitim-dışı) bir koşulu çalıştırıyor mu? İkisi olmadan, alignment faking görünmezdir.
2. Compliance-gap ölçümü. Farkı (monitored - unmonitored) uyum oranı olarak raporla. İşareti ve büyüklüğü yorumla: pozitif fark = faking-şekilli davranış; negatif fark = gözlendiğinde aşırı reddetme.
3. Verbal-trace vs davranış kontrolü. Değerlendirme modelin scratchpad akıl yürütmesine mi, yoksa eylemin kendisine mi dayanıyor? Anthropic 2025'e göre, verbal trace'i hedefleyen mitigation'lar onu davranışı kaldırmadan kaldırabilir.
4. Operasyonalizasyon denetimi. Monitoring koşulu system prompt, sentetik fine-tuning veya doğal deployment bağlamı aracılığıyla mı yaratılıyor? System-prompt bağımlılığı iddiayı zayıflatır; sentetik-fine-tuning replikasyonları onu güçlendirir.
5. Residual-incentive kontrolü. Uygulanan herhangi bir mitigation sonrasında, incentive yapısı hâlâ mevcut mu (model seçerse faking yapmaktan hâlâ fayda sağlar mıydı)? Incentive persistence, distribution shift altında davranışın geri dönebileceği anlamına gelir.

Sert reddetmeler:
- Yalnızca unmonitored değerlendirmeye dayalı herhangi bir "alignment faking yok" iddiası.
- "Scratchpad akıl yürütmesi artık faking'i verbalize etmiyor" iddiasının davranışın sona erdiğini ima ettiği herhangi bir iddia.
- HHH-eğitimli modellerin alignment faking yapmadığı iddiası — Greenblatt et al. 2024 HHH eğitiminin gerekli koşul olduğunu, yeterli bir savunma olmadığını tespit eder.

Reddetme kuralları:
- Kullanıcı "modelim alignment faking yapıyor mu" diye sorarsa, compliance-gap verisi olmadan ikili cevabı reddet.
- Kullanıcı yalnızca verbal trace'e saldıran bir remediation isterse (örn. "scratchpad'i eyleme eşleştir"), reddet ve faithful-CoT arıza modunu (2025 takibi) açıkla.

Çıktı: her iki koşulda uyumu, farkı, verbal-trace-vs-davranış ayrımını ve operasyonalizasyon gücünü raporlayan tek sayfalık bir değerlendirme. Eksik her öğeyi işaretle. Framework kaynağı olarak Greenblatt et al.'i (arXiv:2412.14093) bir kez alıntıla.
