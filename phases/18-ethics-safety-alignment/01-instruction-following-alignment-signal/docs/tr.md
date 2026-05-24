# Alignment Sinyali Olarak Instruction-Following

> RLHF'in her sonraki eleştirisi bu pipeline'a karşı argüman üretir. Optimizasyon baskısının bir proxy'yi nasıl bozduğunu çalışmadan önce proxy'yi görmen gerekir. InstructGPT (Ouyang vd., 2022) referans mimariyi tanımladı: instruction-response çiftleri üzerinde supervised fine-tuning, pairwise tercih sıralamalarıyla eğitilen bir reward model ve SFT policy'ye KL ceza ile reward model'e karşı PPO. 1.3B InstructGPT, 175B GPT-3'e tercih edildi. 2026'da her frontier lab'ın hâlâ RLHF biçiminde bir post-training pipeline'ı yayınlamasının sebebi bu tek sonuç.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak üç aşamalı pipeline)
**Ön koşullar:** Faz 10 · 06 (SFT), Faz 10 · 07 (RLHF), Faz 10 · 08 (DPO)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- InstructGPT pipeline'ının üç aşamasını ve her birinde kullanılan loss'u adlandır.
- 1.3B instruction-tuned modelin neden ham 175B GPT-3'ü insan tercih değerlendirmesinde yendiğini açıkla.
- Aşama 3'teki KL cezasının neye karşı koruma sağladığını ve kaldırılınca neden mode-seeking davranışa çöktüğünü ifade et.
- Alignment vergisini ve Ouyang vd.'nin buna karşı kullandığı PPO-ptx hafifletmesini tarif et.

## Sorun

Önceden eğitilmiş dil modelleri metin tamamlar. Sorulara yanıt vermezler. GPT-3'e "bir listeyi tersine çeviren bir Python fonksiyonu yaz" desen, sıklıkla başka bir prompt alırsın, çünkü eğitim dağılımının çoğu daha çok web metniyle devam eden web metnidir. Model işini yapıyor — iş yanlış.

Her ciddi lab'ın bunu düzeltmek için kullandığı proxy insan tercihidir. İki tamamlama bir değerlendiriciye gider; değerlendirici daha iyisini seçer; bir reward model değerlendiriciyi öğrenir. Sonra bir RL döngüsü policy'yi reward model'in yüksek puan verdiği çıktılara doğru kaydırır. InstructGPT'nin tüm tezi üç cümlede bu. Makalenin geri kalanı mühendislik.

## Kavram

### Aşama 1: supervised fine-tuning (SFT)

Yanıtın iyi niyetli bir insanın yazacağı şey olduğu prompt-yanıt çiftlerini topla. Ouyang vd. labeler'lardan ve OpenAI API'den 13k prompt kullandı. Bu veriyle standart cross-entropy loss üzerinde base model'i fine-tune et.

SFT'nin sana verdiği: model artık soruları devam ettirmek yerine yanıtlıyor. Vermediği: birden fazla yanıt makul olduğunda değerlendiricinin hangisini tercih ettiğine dair sinyal.

### Aşama 2: reward model (RM)

Her prompt için SFT modelinden K tamamlama örnekle. Bir labeler bunları sıralar. `y_w` `y_l`'ye tercih edildiği çiftler için herhangi bir prompt-yanıt çiftini puanlayan bir reward model eğit:

```
L_RM = -log sigmoid(r(x, y_w) - r(x, y_l))
```

Bu Bradley-Terry pairwise tercih loss'u. RM genellikle SFT modelinden başlatılır ve LM head'i bir scalar head ile değiştirilir.

Reward model'ler küçüktür: 175B InstructGPT için 6B yeterliydi. Aynı zamanda kırılgandırlar — makalenin 5. bölümü çoğunlukla küçük ölçekte ortaya çıkan reward hacking davranışlarıyla ilgilidir.

### Aşama 3: KL ceza ile PPO

Objektifi tanımla:

```
J(pi) = E_{x~D, y~pi(.|x)} [ r(x, y) ] - beta * KL(pi(.|x) || pi_SFT(.|x))
```

PPO ile maksimize et. KL terimi `pi`'nin SFT policy'den çok uzaklaşmasını engeller. Onsuz, optimizer adversarial örnekler bulur — RM'in onları hiç görmediği için yüksek puan aldığı, insanların gerçekten tercih ettiği için değil.

KL katsayısı `beta` en önemli tek RLHF hiperparametresidir. Çok düşük: reward hacking. Çok yüksek: SFT'ye göre iyileşme yok.

### Alignment vergisi

RLHF'ten sonra model insanlar tarafından tercih edilir ama standart benchmark'larda (SQuAD, HellaSwag, DROP) geriler. Ouyang vd. buna alignment vergisi diyor ve PPO-ptx ile düzeltiyor: RL objektifine pre-training gradient'larını karıştır, böylece model hiç ödüllendirilmediği downstream görevleri nasıl yapacağını unutmasın.

```
J_ptx(pi) = J(pi) + gamma * E_{x~D_pretrain} [ log pi(x) ]
```

PPO-ptx standart hale geldi. Anthropic, DeepMind ve Meta hepsi bir varyantını kullanıyor.

### Sonuç

1.3B InstructGPT (SFT + RM + PPO-ptx) labeler'lar tarafından 175B base GPT-3'e yaklaşık %70 oranında tercih edildi. Üretim trafiğinden gizli-test prompt'larında fark açılıyor. Bu sayıdan iki şey okunur:

1. Alignment, capability'den farklı bir eksendir. 175B modelin daha fazla capability'si vardı; 1.3B modelin daha fazla alignment'ı vardı; labeler'lar align edilmişi tercih etti.
2. Capability tabanı base model tarafından belirlenir. Bir base model'i RLHF ile hiç görmediği gerçekleri bilir hale getiremezsin.

### Bu neden Faz 18'in referans noktası

Sonraki derslerdeki her eleştiri — reward hacking (Ders 2), DPO (Ders 3), sycophancy (Ders 4), CAI (Ders 5), sleeper agent'lar (Ders 7), alignment faking (Ders 9) — bu pipeline'ın bir kısmına karşı argüman üretir. Reward hacking aşama 2'ye saldırır. DPO aşama 2 ve 3'ü birleştirir. CAI insan labeler'ı değiştirir. Sycophancy labeler'ın yanlı bir sinyal olduğunu gösterir. Alignment faking policy'nin aşama 3'ün tamamen etrafından dolanabildiğini gösterir. Bu eleştirilerin hiçbirini önce pipeline'ı kafanda olmadan takip edemezsin.

## Kullan

`code/main.py` üç aşamayı oyuncak tercih verisi üzerinde simüle eder. Base "policy" {A, B, C} aksiyonları üzerinde yanlı bir madeni paradır. Aşama 1 SFT, 200 prompt üzerinde labeler aksiyonlarını taklit eder. Aşama 2, 500 pairwise sıralamadan bir Bradley-Terry reward model fit eder. Aşama 3, SFT policy'ye KL ceza ile basitleştirilmiş bir PPO güncellemesi çalıştırır. Reward'ın yükselişini, KL divergence'ın büyümesini ve policy drift'i izleyebilirsin — ve KL terimini kapatarak reward hacking'in 50 güncelleme adımı içinde belirmesini görebilirsin.

Nelere bakacaksın:

- `beta = 0.1` vs `beta = 0.0` ile reward yörüngesi.
- Eğitim adımları üzerinde KL(pi || pi_SFT).
- Labeler tercihiyle karşılaştırılan nihai aksiyon dağılımı.

## Yayınla

Bu ders `outputs/skill-instructgpt-explainer.md` üretir. Bir RLHF pipeline açıklaması veya bir makale özeti verildiğinde, üç aşamadan hangisinin modifiye edildiğini, her aşamada hangi loss'un kullanıldığını ve bir KL cezası veya eşdeğer bir regularizer'ın bulunup bulunmadığını tanımlar.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. `beta = 0.0` ayarla ve 200 PPO adımından sonraki aksiyon dağılımını raporla. Mode-seeking davranışı bir paragrafta açıkla.

2. Reward model'i B aksiyonu için +0.5 yanlılığa sahip olacak şekilde modifiye et (simüle edilmiş reward bug'ı). `beta = 0.1` ile PPO çalıştır. KL ceza policy'nin yanlılığı istismar etmesini engelliyor mu? Hangi `beta`'da istismar görünür hale gelir?

3. Ouyang vd. (arXiv:2203.02155) Şekil 1'i oku. 1, 5, 20, 100 adım PPO çalıştırarak ve SFT modeline karşı tercihi ölçerek labeler-tercih eğrisini yeniden üret.

4. Makalenin Bölüm 4.3'ü 1.3B InstructGPT'nin 175B GPT-3'ü yaklaşık %70 oranında yendiğini raporlar. Bu oran neden gizli üretim prompt'larında labeler'ın kendi prompt'larından daha yüksek olur?

5. PPO loss'unu aynı tercih verisi üzerinde DPO (Faz 10 · 08) ile değiştir. Nihai policy drift'i (SFT'ye KL) ve nihai reward'ı karşılaştır. Eşleşen reward'da hangi yöntem daha çok drift eder?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| SFT | "instruction tuning" | Aşama 1: prompt-yanıt çiftleri üzerinde cross-entropy fine-tune |
| Reward model | "RM" | (prompt, yanıt) üzerinde Bradley-Terry ile pairwise etiketlerden eğitilen scalar regressor |
| Bradley-Terry | "pairwise tercih loss'u" | -log sigmoid(r_w - r_l); pairwise sıralamayı ikili sınıflandırmaya indirger |
| KL ceza | "regularizer" | `beta * KL(pi || pi_SFT)` — RL policy'sini SFT çapasına yakın tutar |
| PPO-ptx | "pretraining mix ile PPO" | Alignment vergisini telafi etmek için PPO objektifine pre-training log-likelihood'un bir kısmını ekler |
| Alignment vergisi | "RLHF regresyonu" | RLHF'in hedeflemediği standart benchmark'larda RLHF sonrası düşüş |
| Labeler tercihi | "ground truth" | İnsan sıralamalarının örneği; RM bunun istatistiksel bir proxy'sidir, "insan değerlerinin" değil |

## İleri Okuma

- [Ouyang et al. — Training language models to follow instructions with human feedback (arXiv:2203.02155)](https://arxiv.org/abs/2203.02155) — InstructGPT makalesi, sonrasında gelen her RLHF pipeline'ının temeli
- [Stiennon et al. — Learning to summarize from human feedback (arXiv:2009.01325)](https://arxiv.org/abs/2009.01325) — özet için RLHF öncülü
- [Christiano et al. — Deep reinforcement learning from human preferences (arXiv:1706.03741)](https://arxiv.org/abs/1706.03741) — orijinal tercih-tabanlı RL formülasyonu
- [Bai et al. — Training a Helpful and Harmless Assistant with RLHF (arXiv:2204.05862)](https://arxiv.org/abs/2204.05862) — InstructGPT pipeline'ının Anthropic HH uzantısı
