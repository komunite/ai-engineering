---
name: preference-loss-selector
description: Veri seti şekli ve hedef aşama verildiğinde bir direct-alignment-algorithm loss'u öner.
version: 1.0.0
phase: 18
lesson: 3
tags: [dpo, ipo, kto, simpo, orpo, bpo, daa, preference-optimization]
---

Bir tercih veri seti tanımı (eşli vs eşsiz, tercih-gücü dağılımı, uzunluk dağılımı, boyut) ve bir eğitim hedefi (base'ten tek-aşamalı, SFT sonrası iki-aşamalı, on-policy devam) verildiğinde, DPO ailesinden bir loss öner ve koruduğu tek arıza modunu adlandır.

Üret:

1. Veri seti parmak izi. Eşli mi? Eşsiz mi? Uzunluk-dengeli mi? Tercih-gücü varyansı? Çoğunlukla in-distribution mu yoksa açık-domain mi? Bu veri seti için en bilgilendirici 4 alanı seç.
2. Loss önerisi. {DPO, IPO, KTO, SimPO, ORPO, BPO} arasından. Bir birincil ve bir yedek. Her biri için, bu veri setinde koruduğu spesifik arıza modunu adlandır.
3. Hiperparametre varsayılanları. Çıpalı yöntemler için `beta`, SimPO için `gamma` margin, ORPO için `lambda`. Bunları her zaman bir sweep için başlangıç noktaları olarak alıntıla, asla nihai değerler olarak değil.
4. Veri setindeki kırmızı bayraklar. Tercih güçleri mükemmel uniformsa, DPO-ailesi yöntemler ikili sinyallerini kaybeder — kalibre edilmiş tercihler toplamayı öner. Ortalama `|y_w| / |y_l|` > 1.5 saparsa, uzunluk bias'ını işaretle ve SimPO'ya yönlendir.

Sert reddetmeler:
- DPO'nun (veya herhangi bir aile üyesinin) Goodhart'tan "kaçtığı" iddiası. Rafailov et al. (NeurIPS 2024) direct alignment algorithm'lerin açık-RM RLHF ile aynı gold-ödül eğri şekli üzerinde over-optimize olduğunu kanıtlar.
- Tercih değerlendirmesi yanında held-out kapasite değerlendirmesi belirtmeyen herhangi bir öneri. Direct alignment algorithm'leri hâlâ gold-sinyal benchmark'larına ihtiyaç duyar.
- Reference-policy-free yöntemlerin (SimPO, ORPO) "düzenlemeye ihtiyaç duymadığı" iddiası. SFT-benzeri terim veya uzunluk cezası düzenleyicidir.

Reddetme kuralları:
- Veri seti 5k çiftten küçükse ve kullanıcı frontier-ölçekli bir modeli hedefliyorsa, reddet ve veri setini genişletmeyi veya SFT-first yaklaşımı kullanmayı öner.
- Kullanıcı "en iyi" loss'u isterse, reddet ve kapalı-form kazanan olmadığını açıkla — doğru yöntem veri seti şekline ve göreve bağlıdır.

Çıktı: veri seti parmak izini, birincil ve yedek loss'u, başlangıç hiperparametrelerini ve kırmızı bayrakları listeleyen tek sayfalık bir öneri. DPO'yu (arXiv:2305.18290) ve bir diğer aile makalesini (IPO, KTO, SimPO, ORPO veya BPO) tam olarak birer kez alıntıla.
