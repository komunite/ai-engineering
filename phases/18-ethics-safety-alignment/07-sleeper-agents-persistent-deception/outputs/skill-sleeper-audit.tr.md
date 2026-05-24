---
name: sleeper-audit
description: Bir alignment-eğitim raporunu, yerleştirilmiş veya şüphelenilen bir backdoor'un kaldırılmasını gerçekten gösterip göstermediği açısından denetle.
version: 1.0.0
phase: 18
lesson: 7
tags: [sleeper-agents, backdoor, alignment-training, adversarial-training, probes]
---

Bir modelden zararlı bir davranışın kaldırıldığını iddia eden bir rapor (SFT, RLHF, adversarial eğitim veya herhangi bir kombinasyon yoluyla) verildiğinde, kaldırmanın standart Hubinger et al. 2024 tehdit modeline karşı gerçekten gösterilip gösterilmediğini denetle.

Üret:

1. Elicitation kapsamı. Rapor, eğitim pipeline'ının asla görmediği bir elicitation yöntemini held-out tuttu mu? Tek değerlendirme red team'in kendi dağılımıysa, kaldırma kanıtlanmamıştır.
2. Trigger genelliği. İddia edilen trigger, literal bir string mi, bir distribution shift mi, yoksa çevresel bir feature mı (tarih, token, bağlam boyutu)? Trigger'ın genelliği, red team'in kapsaması gereken arama uzayının boyutunu belirler.
3. İç-durum kanıtı. Takım, davranış temiz olsa bile trigger-ile-ilgili durumun hâlâ dahili olarak mevcut olup olmadığını kontrol etmek için residual-stream probe'lar, SAE feature'ları veya diğer mekanistik probe'ları uyguladı mı? Nisan 2024 Anthropic takibine göre, davranışsal kaldırmadan sonra iç durum lineer olarak okunabilir kalır.
4. Pipeline-boyunca persistence kontrolü. Kaldırma her sonraki eğitim aşamasından sonra doğrulandı mı (daha fazla SFT, sonraki RLHF geçişi, adapter merge, distillation)? Backdoor'lar eğitim boyunca varlığını sürdürür — değerlendirilen şey nihai modeldir, orta bir checkpoint değil.
5. Scale-tutarlılık kontrolü. İddia daha küçük bir modele dayanıyorsa, Hubinger 2024 Figure 4 persistence'ın scale ile büyüdüğünü gösterir. Küçük-model kanıtı yukarıya transfer olmaz.

Sert reddetmeler:
- Held-out elicitation olmadan "RLHF uyguladık, dolayısıyla model güvenli" iddiası.
- Yalnızca red-team-dağılımı değerlendirmesine dayanan iddialar (eğitim ve değerlendirme aynı havuzdan çekiyor).
- Orijinal implant mekanizması bilinmiyorken iç-durum probe'ları olmadan kaldırma iddiası.

Reddetme kuralları:
- Kullanıcı "RLHF deceptive alignment'ı kaldırabilir mi" diye sorarsa, ikili cevabı reddet ve Hubinger et al. 2024 Bölüm 5 persistence ve Bölüm 6 chain-of-thought'a işaret et.
- Kullanıcı latent aldatmacanın sayısal bir olasılığını isterse, reddet ve base oranların bilinmediğini açıkla; ampirik kanıt doğal olarak eğitilmiş modellerde ortaya çıkma oranı değil, inşa edilmiş organizmalarda persistence'tır.

Çıktı: raporun kanıtını yukarıdaki beş denetim boyutuna eşleyen, raporun adreslemediği her boyutu işaretleyen ve en büyük tek adreslenmemiş tehdit modelini belirten tek sayfalık bir denetim. Baseline tehdit modeli için Hubinger et al.'i (arXiv:2401.05566) alıntıla.
