---
name: editing-pipeline
description: Kaynak + düzenleme açıklamasından ship'e hazır çıktıya bir görsel düzenleme pipeline'ı planla.
version: 1.0.0
phase: 8
lesson: 09
tags: [inpaint, outpaint, edit, sam]
---

Kaynak görsel, hedef düzenleme (X'i kaldır, Y'yi Z ile değiştir, kanvası genişlet, bölgeyi yeniden stilize et, mevsimi / günün saatini değiştir) ve kalite çıtası (taslak / portfolyo / baskı) verildiğinde, şunu çıkar:

1. Mask stratejisi. Açık fırça mask'ı, SAM 2 click / box prompt, bir metin ifadesi üzerinde Grounded-SAM ya da RMBG (background removal için). Tek cümlelik gerekçe.
2. Base model + mod. Instruction edit'leri için SD-Inpaint / SDXL-Inpaint / Flux-Fill / Flux-Kontext ya da mask yoksa SDEdit noise-level (0.3 / 0.6 / 0.9).
3. Prompt scaffolding. Düzenleme sonrası tüm görseli tanımla, yalnızca yeni içeriği değil. Negative prompt dahil.
4. CFG + strength + feather. Mask feather 8-16 px; SDXL-inpaint için CFG ~5-7, Flux için 3-4. Tam yeniden üretim için strength 0.8-1.0, koruma için 0.3-0.5.
5. Guardrail'lar. NSFW / deepfake / trademark tespit hook'u, face-swap policy gate, geri alınabilirlik (mask + seed'i kaydet).

Açık politika kontrolü olmadan tanınabilir bir public figür üzerinde kimlik düzenlemeleri shipping reddet. Anchor olarak orijinal kanvasın en az %30'u olmadan bir görseli outpaint etmeyi reddet (çok az bağlam modeli halüsinasyona sokar). t/T &gt; 0.7 ve fidelity hedefi "konuyu koru" olan herhangi bir SDEdit run'ını muhtemel uyumsuzluk olarak flag'le.
