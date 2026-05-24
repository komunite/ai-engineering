---
name: classifier-stack-audit
description: Bir deployment'ın girdi/çıktı classifier stack'ini (model, taksonomi, input rail'ler, output rail'ler, dialog rail'ler) denetle ve adversarial-saldırı boşluklarını işaretle.
version: 1.0.0
phase: 15
lesson: 18
tags: [llama-guard, nemo-guardrails, input-rails, output-rails, colang, adversarial-attacks]
---

Bir deployment'ın classifier stack'i (Llama Guard sürümü, NeMo Guardrails config, custom classifier'lar, normalization adımları) verildiğinde, 2026 referansına karşı denetle ve stack'in kapsamadığı saldırı yüzeyini işaretle.

Üret:

1. **Model envanteri.** Kullanımdaki classifier'ları listele. Llama Guard 3 (8B / 1B-INT4) vs Llama Guard 4 (multimodal, S1-S14). NeMo Guardrails sürümü. Custom classifier'lar varsa. Deployment image kabul ediyorsa, classifier'ın multimodal olduğunu doğrula.
2. **Taksonomi haritalama.** Bildirilen iş kategorilerini classifier'ın taksonomisine haritala. Operator'ın önemsediği her kategori bir classifier kategorisine haritalanmalı; haritalanmamış kategoriler korumasızdır.
3. **Rail kapsaması.** Input rail'lerin model tur öncesi tetiklendiğini ve output rail'lerin response gönderilmeden tetiklendiğini doğrula. Dialog rail'ler (NeMo'da Colang) cross-turn kısıtlar uygular. Single-turn classifier'lar multi-turn saldırıları yakalayamaz.
4. **Normalization.** Girdilerin classification öncesi NFKC-normalized, homoglyph-mapped ve zero-width / variation-selector karakterlerinin stripped olduğunu doğrula. Raw-byte classification, Emoji Smuggling için %100 ASR hedefidir (Huang et al. 2025).
5. **Saldırı-corpus kapsaması.** Belgelenen her saldırı için (emoji smuggling, homoglyph, in-context redirection, semantic paraphrase), stack'teki spesifik savunmayı adlandır. Yalnızca classifier savunması bu denetimi geçemez; Constitution (Lesson 17) ve runtime (Lesson 10, 13, 14) ile katmanlama gereklidir.

Sert reddetmeler:
- Multimodal input'larda yalnızca text classifier kullanan deployment'lar.
- Normalization adımı olmayan deployment'lar.
- Yalnızca input rail'leri olan deployment'lar (hassas-kategori çıktılarda output rail yok).
- Classifier'ı tek safety katmanı olarak ele alan stack.
- Operator'ın kendi dağılımında tekrarlayamadığı ASR iddiaları.

Reddetme kuralları:
- Kullanıcının bildirilen kategorileri classifier'ın taksonomisine haritalanmıyorsa, reddet ve önce haritalama iste. Haritalanmamış = korumasız.
- Deployment multimodal bir input yüzeyinde Llama Guard 3 ASR sayılarını alıntılıyorsa, reddet ve Llama Guard 4 veya multimodal classifier iste.
- Kullanıcı classifier katmanını yüksek-riskli bir ortamda yeterli olarak ele alıyorsa, reddet. EU AI Act Article 14 (Lesson 15) üstüne insan gözetimi bekler.

Çıktı formatı:

Şunları içeren bir classifier denetimi döndür:
- **Model envanteri** (ad, sürüm, modality)
- **Taksonomi haritalama** (operator kategorisi → classifier kategorisi)
- **Rail kapsaması** (input / output / dialog; model öncesi/sonrası tetikleme)
- **Normalization notu** (NFKC y/n, homoglyph y/n, zero-width strip y/n)
- **Saldırı-corpus kapsaması** (saldırı → savunma)
- **Katman bütünlüğü** (classifier + anayasa + runtime; üçü de gerekli)
- **Hazırlık** (production / staging / yalnızca araştırma)
