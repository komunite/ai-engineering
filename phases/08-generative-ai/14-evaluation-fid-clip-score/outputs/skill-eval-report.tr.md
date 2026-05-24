---
name: eval-report
description: Tam bir üretken model değerlendirmesi planla: örnek kalitesi, adherence, tercih, failure audit.
version: 1.0.0
phase: 8
lesson: 14
tags: [evaluation, fid, clip, elo]
---

Yeni bir üretken model checkpoint'i, bir referans baseline ve bir modalite (görsel / video / ses / 3D) verildiğinde, tam bir değerlendirme planı çıkar:

1. Örnek kalitesi. 10-30k örnekte tutulan gerçek sete karşı FID / FD-DINO / CMMD. Eşleşen çözünürlük. 3-seed ortalama +/- std raporla.
2. Adherence. Prompt-görsel çiftlerinde CLIP skoru / CMMD. Text-to-image için HPSv2 + ImageReward + PickScore dahil. Video için vision-language metrikleri ekle (V-Eval). Ses için CLAP + MOS.
3. İkili tercih. Baseline'a karşı 200-2000 prompt üzerinde kör A/B. Human + LLM-judge + PartiPrompts kapsamı.
4. Kategori dökümü. Prompt kategorisi başına performans (insanlar, hayvanlar, text rendering, kompozisyon, stil). Genel metrikler iyileşse bile kategori başına regression'ları flag'le.
5. Güvenlik / kötüye kullanım. NSFW classifier, deepfake detector, watermark kontrolü, top-K generation'larda telif benzerlik taraması.
6. Sign-off. Açık gate: FID baseline'ın +%5'i içinde VEYA &gt;%55 insan kazanma oranı VEYA belgelenmiş niteliksel avantaj. Tek-metrik iddiası yok.

N &lt; 5000'de FID raporlamayı reddet. Modelin eğitimde görmüş olabileceği prompt'lar üzerinde hesaplanan benchmark'ları shipping reddet. İnsan çapraz kontrolü olmadan yalnızca LLM-judge sonuçlarını raporlamayı reddet. Mutlak base değeri raporlamadan ve tek seed raporlayarak bir metriğin "%20 arttı" iddiasını flag'le.
