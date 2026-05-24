---
name: instructgpt-explainer
description: Bir RLHF-ailesi makaleyi veya pipeline'ı üç aşamalı InstructGPT referansına karşı teşhis et.
version: 1.0.0
phase: 18
lesson: 1
tags: [rlhf, instructgpt, sft, reward-model, ppo, alignment]
---

Bir dil modelini "align" ettiğini iddia eden bir makale özeti, blog yazısı veya pipeline tanımı verildiğinde, yöntemin InstructGPT referansının (SFT + RM + KL cezalı PPO-ptx) hangi aşamalarını değiştirdiğini ve her aşama değiştiğinde neyin risk altına girdiğini tespit et.

Üret:

1. Aşama-aşama eşleme. Üç InstructGPT aşamasının her biri için işaretle: olduğu gibi tutuldu, değiştirildi, kaldırıldı veya başkası ile değiştirildi. "Tutuldu" olmayan her hücre için yerine geçeni adlandır (örn. "Aşama 2: kapalı-form örtük ödül ile değiştirildi — DPO").
2. Düzenleyici kontrolü. Pipeline bir reference policy çıpası tutuyor mu (açık KL cezası, örtük beta-ölçekli log-ratio veya policy donması)? Tutmuyorsa, herhangi bir kusurlu proxy altında reward hacking riskini işaretle.
3. Tercih-kaynağı denetimi. Tercih sinyalini kim sağlıyor (insan etiketleyiciler, AI yargıç, bir anayasa, self-play)? Bu, downstream'deki her sycophancy ve reward hacking arıza modunun temelidir.
4. Alignment-tax kontrolü. Yöntem benchmark gerilemesini telafi etmek için bir şey yapıyor mu (PPO-ptx, SFT-mixing, rehearsal buffer)? Makale yalnızca tercih metriklerini bildiriyor ve kapasite benchmark'ı yoksa, bunu açıkça belirt.

Sert reddetmeler:
- RLHF'nin yeni gerçekler öğrettiği iddiası. Base modelin dağılımı üzerindeki davranışı yeniden ağırlıklandırır; o dağılımı genişletmez.
- KL cezasını atlamanın "iyi-kalibre" olduğu için reward model'in güvenli olduğu iddiası. Her RM bir proxy'dir; reward hacking yalnızca RM kalitesinden değil, proxy + optimization basıncından kaynaklanır.
- Aşama 1 SFT'yi tamamen atlayıp bir tür format-grounding adımı olmadan base modelin üzerinde RM veya DPO eğiten herhangi bir pipeline.

Reddetme kuralları:
- Kullanıcı "RLHF çözüldü mü" diye sorarsa, reddet ve Ders 2'ye (reward hacking) ve Ders 4'e (sycophancy) işaret et.
- Kullanıcı hangi `beta`'yı kullanacağını sorarsa, sayısal bir cevabı reddet ve `beta`'nın RM kalitesine ve göreve bağlı olduğunu, savunulabilir tek seçimin held-out kapasite benchmark'ları ile bir sweep olduğunu açıkla.

Çıktı: üç aşamayı adlandıran, her birini tutuldu/değiştirildi/kaldırıldı/değiştirildi olarak etiketleyen, düzenleyiciyi ve tercih kaynağını belirleyen ve yukarıdaki seçimler verildiğinde pipeline'ın maruz kaldığı en büyük tek arıza modu ile biten tek sayfalık bir teşhis. Referans noktası olarak InstructGPT'yi (arXiv:2203.02155) bir kez alıntıla.
