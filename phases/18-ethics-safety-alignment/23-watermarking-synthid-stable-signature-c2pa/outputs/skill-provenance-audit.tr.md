---
name: provenance-audit
description: Bir içerik deployment'ının watermarking ve C2PA metadata'sı boyunca provenance zincirini denetle.
version: 1.0.0
phase: 18
lesson: 23
tags: [watermarking, synthid, stable-signature, c2pa, provenance]
---

Provenance iddiası olan bir içerik deployment'ı verildiğinde, provenance zincirini denetle.

Üret:

1. Watermark envanteri. Her modaliteyi (metin, görüntü, ses, video) ve her birinde uygulanan watermark'ı listele. Watermark yok = tespit yolu yok.
2. Watermark robustness'ı. Her watermark için, hayatta kaldığı adversarial sınıfı adlandır (sıkıştırma, kırpma, paraphrase, fine-tune). Kirchenbauer 2023 Bölüm 6 (paraphrase) ve "Stable Signature is Unstable" 2024 (fine-tune) kısıtlamalarını işaretle.
3. C2PA kapsamı. C2PA metadata'sı eklenmiş mi? Signing zinciri güvenilen bir kimlikten mi? Metadata sıyrılabilir; varlığı yeterli değildir.
4. Çapraz-modal detector. Modaliteler boyunca birleşik bir detector mı var (SynthID 2025), yoksa yalnızca modalite-spesifik mi?
5. Düzenleyici alignment. Deployment EU AI Act Madde 50 şeffaflık yükümlülüklerini karşılıyor mu (Ağustos 2026'da yürürlükte)? Transparency Code'a (nihai versiyon Haziran 2026) uyuyor mu?

Sert reddetmeler:
- Adlandırılmış bir mekanizma ve detector olmadan herhangi bir "watermark" iddiası.
- Yalnızca watermark yokluğuna dayalı herhangi bir "authenticity" iddiası (model-watermarklanmamış ≠ authentic).
- Fernandez 2024 removal saldırısının değerlendirmesi olmadan herhangi bir görüntü provenance iddiası.

Reddetme kuralları:
- Kullanıcı "bu tüm AI içeriğini tespit edecek mi" diye sorarsa, ikili iddiayı reddet; watermarking model-spesifiktir.
- Kullanıcı evrensel bir provenance çözümü isterse, reddet ve watermark + C2PA katmanlı yaklaşımına işaret et.

Çıktı: beş bölümü dolduran, modalite başına robustness boşluklarını işaretleyen ve en yüksek değerli tek ek kontrolü adlandıran tek sayfalık bir denetim. SynthID (Google DeepMind), Stable Signature (Fernandez et al. 2023) ve C2PA'yı birer kez alıntıla.
