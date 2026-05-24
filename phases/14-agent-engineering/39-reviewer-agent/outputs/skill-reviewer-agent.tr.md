---
name: reviewer-agent
description: Builder artifact'larını okuyan, yapılandırılmış bir review raporu üreten ve insan review'unu boş bir sayfa yerine yazılı bir sayfadan başlatan beş boyutlu rubric ile bir reviewer agent rolü ayağa kaldır.
version: 1.0.0
phase: 14
lesson: 39
tags: [reviewer, rubric, role-separation, second-loop, review-report]
---

Zaten workbench artifact'ları üreten bir builder agent verildiğinde, onları okuyan ve yapılandırılmış raporlar yazan bir reviewer ayağa kaldır.

Üret:

1. Reviewer system prompt'u ile `agents/reviewer.md`: read-only erişim, beş boyutlu rubric, her skor için artifact yolunu alıntılamalı.
2. Workbench'ten `ReviewerInputs` yükleyen ve boyut başına LLM scorer'ı çalıştıran `tools/reviewer.py`.
3. Kanonik review raporu yolu olarak `outputs/review/<task_id>.json`.
4. Beş boyutu, her birinin cevapladığı soruyu ve 0-1-2 anchor açıklamalarını listeleyen `docs/reviewer-rubric.md`.
5. Bir builder görevi kapandığında review raporunu PR yorumu olarak gönderen CI adımı.

Sert ret durumları:

- Diff üzerinde write erişimi olan bir reviewer. Builder ve reviewer arasındaki boşluk tüm sinyaldir; daraltmak güvenilirliği yok eder.
- Skor başına anchor açıklamaları olmayan bir rubric. Anchor'sız "0'dan 2'ye skor" vibe'a düşer.
- Citation'ı atlayan review raporları. Her skor bir dosyaya veya trace girdisine işaret etmeli.
- Builder'ın system prompt'unu paylaşmak. Aynı model tamam; aynı prompt değil.

Reddetme kuralları:

- Builder verification raporu üretmiyorsa, reviewer'ı çalıştırmayı reddet. Yargı istenmeden önce kabul tutmalı.
- Projenin kapalı üç görevden azı varsa, rubric'in kalibre edildiğini iddia etmeyi reddet. İlk raporları kalibrasyon seti olarak sakla.
- Reviewer minimum güvenin altında skorlama isteniyorsa, reddet ve belirsiz boyutu bir insana yüzdür.

Çıktı yapısı:

```
<repo>/
├── agents/reviewer.md
├── tools/reviewer.py
├── outputs/review/
│   └── <task_id>.json
├── docs/reviewer-rubric.md
└── .github/workflows/review.yml
```

"Bundan sonra ne okumalı" notu ile bitir:

- Verification + review birleştiren handoff paketi için Lesson 40.
- Builder/reviewer ayrımını uçtan uca egzersiz eden real-style görev için Lesson 41.
- Bu dersin geliştirdiği tek-agent self-review baseline için Lesson 05 (Self-Refine ve CRITIC).
