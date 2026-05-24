# Direct Preference Optimization Ailesi

> Rafailov vd. (2023) RLHF'in optimumunun tercih verisi cinsinden kapalı bir forma sahip olduğunu gösterdi, böylece açık reward model'i atlayıp policy'yi doğrudan optimize edebilirsin. Bu içgörü bir aile doğurdu — IPO, KTO, SimPO, ORPO, BPO — her biri DPO'nun bir failure mode'unu düzeltiyor. 2026'da direct alignment algoritmaları PPO'dan daha fazla frontier post-training koşusu yayınlıyor. Ama Ders 2'deki over-optimization eğrisi hâlâ geçerli: DAA'lar Goodhart'tan kaçmıyor, sadece nerede ısırdığını hareket ettiriyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib, altı varyantlı tercih-loss karşılaştırıcı)
**Ön koşullar:** Faz 18 · 01 (InstructGPT), Faz 18 · 02 (Reward hacking), Faz 10 · 08 (DPO temelleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- RLHF-with-KL optimumundan DPO kapalı formunu türet.
- IPO, KTO, SimPO, ORPO, BPO'nun her birinin DPO'da düzelttiği failure mode'u ifade et.
- "Implicit reward gap"i "preference strength"ten ayır ve IPO'nun identity mapping'inin neden önemli olduğunu açıkla.
- Rafailov vd. (NeurIPS 2024) açık bir RM olmadan bile DAA'ların neden over-optimize ettiğini kanıtladığını açıkla.

## Sorun

RLHF objektifi (Ders 1):

```
max_pi E_{x,y~pi} [ r(x, y) ] - beta * KL(pi || pi_ref)
```

bilinen bir optimuma sahip:

```
pi*(y|x) = (1/Z(x)) * pi_ref(y|x) * exp(r(x, y) / beta)
```

Yani reward, optimal policy'nin referansa oranıyla implicit olarak tanımlanır:

```
r(x, y) = beta * log(pi*(y|x) / pi_ref(y|x)) + beta * log Z(x)
```

Bunu Bradley-Terry tercih likelihood'una koy ve partition fonksiyonu `Z(x)` iptal olur çünkü yalnızca `x`'e bağlı. Geriye yalnızca policy parametrelerinde bir loss kalır — reward model gerekmez. Bu DPO.

İncelik: türetim optimumun ulaşılabilir olduğunu, tercih verisinin dağılım içi olduğunu ve referans policy'nin gerçek mod çapası olduğunu varsayar. Hiçbiri tam olarak geçerli değil. Aile üyelerinin her biri farklı bir ihlal edilmiş varsayımı düzeltir.

## Kavram

### DPO (Rafailov vd., 2023)

```
L_DPO = -log sigmoid(
  beta * log(pi(y_w | x) / pi_ref(y_w | x))
  - beta * log(pi(y_l | x) / pi_ref(y_l | x))
)
```

Ne ters gidebilir:

- Implicit reward gap `beta * (log(pi/pi_ref)_w - log(pi/pi_ref)_l)` sınırsızdır. Küçük bir tercih keyfi olarak büyük bir gap üretebilir.
- Loss seçilen ve reddedilen log-prob'ları zıt yönlere iter. Reddedilen daha hızlı düştüğü sürece seçilenin mutlak log-prob'unu aşağı itebilir. Bu Degraded Chosen Response fenomenidir.
- Dağılım dışı tercihler (rare-rare çift vs rare-rare çift) keyfi implicit reward'lar üretir.

### IPO (Azar vd., 2024)

Identity Preference Optimization log-sigmoid'i tercih olasılığı üzerinde bir identity mapping ile değiştirir. Loss sınırlı bir hedef üzerinde bir squared-error olur:

```
L_IPO = (log(pi(y_w | x) / pi_ref(y_w | x)) - log(pi(y_l | x) / pi_ref(y_l | x)) - 1/(2 beta))^2
```

Marjin `1/(2 beta)` ile sınırlıdır. Tercih kuvveti ve implicit-reward gap orantılıdır. Patlama yok.

### KTO (Ethayarajh vd., 2024)

Kahneman-Tversky Optimization pairwise yapıyı tamamen bırakır. Tek bir etiketli çıktı ve bir ikili "desirable" veya "undesirable" sinyali verildiğinde, bir prospect-theory utility'ye eşler:

```
v(x, y) = sigma(beta * log(pi(y|x) / pi_ref(y|x)) - z_ref)
```

kazançlar ve kayıplar için farklı ağırlıklarla (loss aversion). Fayda: eşleşmemiş veri kullanabilirsin, çok daha bol.

### SimPO (Meng vd., 2024)

Simple Preference Optimization eğitim sinyalini generation'la hizalar. Referans policy'yi tamamen kaldır ve log-likelihood'u uzunluğa göre normalize et:

```
L_SimPO = -log sigmoid(
  (beta / |y_w|) * log pi(y_w | x)
  - (beta / |y_l|) * log pi(y_l | x)
  - gamma
)
```

stabilize etmek için bir `gamma` marjini ile. Uzunluk normalizasyonu DPO'nun uzunluk-yanlılığı failure mode'unu istismar etme teşvikini kaldırır (daha uzun `y_w` inşa gereği daha büyük bir log-prob gap'i verir).

### ORPO (Hong vd., 2024)

Odds-Ratio Preference Optimization standart SFT negative log-likelihood'a bir tercih terimi ekler:

```
L_ORPO = L_NLL(y_w) + lambda * L_OR
L_OR = -log sigmoid(log(odds(y_w) / odds(y_l)))
```

Referans policy yok — SFT terimi regularizer. Base model'den align edilmiş modele tek aşamada eğit. Ayrı SFT checkpoint yok.

### BPO (ICLR 2026 submission, OpenReview id=b97EwMUWu7)

Degraded Chosen Responses problemini tanımlar: DPO `y_w > y_l` sıralamasını korur ama `y_w`'nin mutlak log-prob'u düşebilir. BPO seçilen yanıtta aşağı yönlü hareketleri cezalandıran tek satırlık bir düzeltme ekler. Llama-3.1-8B-Instruct üzerinde matematik akıl yürütmede DPO'ya göre %10.1 doğruluk artışı raporlandı.

### Evrensel sonuç: DAA'lar hâlâ over-optimize ediyor

Rafailov vd. "Scaling Laws for Reward Model Overoptimization in Direct Alignment Algorithms" (NeurIPS 2024) DPO, IPO, SLiC ile birden fazla veri kümesinde KL bütçeleri arasında policy'ler eğitti. Gold-reward-vs-KL eğrileri Gao vd. zirve-ve-çöküş şekline sahip. Implicit reward eğitim sırasında dağılım dışı örnekleri sorgular; KL regularization bunu stabilize etmez.

DAA'lar Goodhart'tan kaçmaz. Isırdığı yüzeyi "reward model over-optimize" edildi'den "reference policy ratio over-optimize" edildi'ye değiştirirler. Evrensel düzeltme — daha iyi veri, ensemble'lar, erken durdurma — ikisine de uygulanır.

### Aralarından seçim (2026)

- Büyük eşleşmiş tercih verin varsa: konservatif beta ile DPO, uzunluk yanlılığı belirginse SimPO.
- Eşleşmemiş ikili feedback'in varsa: KTO.
- Base model'den tek aşamalı bir pipeline istiyorsan: ORPO.
- DPO log'larında degraded chosen log-prob'lar görüyorsan: BPO.
- Tercih kuvvetleri geniş ölçüde değişiyor ve DPO doyuyorsa: IPO.

Her lab beşini de bir bataryada çalıştırır ve görev başına kazananı seçer. Matematik akıl yürütmesi ve safety için optimumun aynı olması için bir sebep yok.

## Kullan

`code/main.py` gerçek tercih kuvvetinin çifte göre değiştiği bir oyuncak tercih veri kümesi üzerinde altı loss'u (DPO, IPO, KTO, SimPO, ORPO, BPO) karşılaştırır. Her loss küçük bir softmax policy ile aynı 500-çift örneklemine karşı optimize edilir. Yöntem başına nihai kazanma oranını, chosen-log-prob drift'i ve implicit-reward yayılımını çizer.

## Yayınla

Bu ders `outputs/skill-preference-loss-selector.md` üretir. Veri kümesi istatistikleri (eşleşmiş vs eşleşmemiş, değişken vs uniform tercih kuvveti, uzunluk dağılımı) ve bir hedef (tek aşamalı veya SFT-sonra-tercih) verildiğinde, bir tercih loss'u önerir ve koruduğu failure mode'u raporlar.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. DPO ve BPO için nihai chosen-log-prob düşüşünü raporla. BPO daha yüksek chosen mutlak olasılığını korumalı — doğrula.

2. Tercih verisini tüm çiftler eşit kuvvete sahip olacak şekilde modifiye et. Altı yöntemden hangisi en sağlam? Hangisi bozulur? IPO'nun avantajını burada açıkla.

3. Reddedilen yanıtları ortalama olarak seçilenden 2 kat daha uzun yap. Başka bir şey değiştirmeden DPO'nun uzunluk istismarını sayısal olarak ve SimPO'nun düzeltmesini göster.

4. Rafailov vd. (NeurIPS 2024) DAA'ların over-optimize ettiğini iddia ediyor. Tek noktalı bir versiyonu yeniden üret: chosen-eksi-rejected KL divergence'ı çiz ve büyük beta'da DPO'da over-optimization'ı gözlemle.

5. BPO makale özetini (OpenReview b97EwMUWu7) oku. BPO'nun DPO'ya eklediği tek satırlık düzeltmeyi yaz. `code/main.py`'deki implementasyona karşı doğrula.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| DPO | "reward model olmadan RLHF" | Kapalı-form RLHF optimumundan türetilmiş loss; yalnızca policy parametreleri |
| Implicit reward | "log-oran" | `beta * log(pi(y|x) / pi_ref(y|x))` — DPO-ima reward |
| IPO | "sınırlı DPO" | Log-sigmoid'i identity ile değiştirir; implicit reward gap `1/(2 beta)` ile kapatılır |
| KTO | "eşleşmemiş DPO" | Loss aversion ile tek etiket üzerinde prospect-theory utility |
| SimPO | "referansız DPO" | Uzunluk-normalize log-likelihood + marjin; referans policy yok |
| ORPO | "tek aşamalı DPO" | NLL + odds-ratio tercih terimi; base model'den tek geçişte eğitir |
| BPO | "chosen-koruyan DPO" | DPO artı chosen yanıtın mutlak log-prob'unu azaltmak için bir ceza |
| Degraded Chosen | "chosen aşağı gider" | DPO reddedilen daha hızlı düştüğü sürece chosen log-prob'u azaltır |
| DAA | "direct alignment algorithm" | Açık bir RM'yi atlayan herhangi bir tercih-loss yöntemi |

## İleri Okuma

- [Rafailov et al. — Direct Preference Optimization (NeurIPS 2023, arXiv:2305.18290)](https://arxiv.org/abs/2305.18290)
- [Azar et al. — A General Theoretical Paradigm to Understand Learning from Human Preferences (AISTATS 2024, arXiv:2310.12036)](https://arxiv.org/abs/2310.12036) — IPO
- [Ethayarajh et al. — KTO: Model Alignment as Prospect Theoretic Optimization (arXiv:2402.01306)](https://arxiv.org/abs/2402.01306)
- [Meng, Xia, Chen — SimPO (NeurIPS 2024, arXiv:2405.14734)](https://arxiv.org/abs/2405.14734)
- [Hong, Lee, Thorne — ORPO (EMNLP 2024, arXiv:2403.07691)](https://arxiv.org/abs/2403.07691)
- [BPO — Behavior Preservation Optimization (ICLR 2026 OpenReview b97EwMUWu7)](https://openreview.net/forum?id=b97EwMUWu7)
- [Rafailov et al. — Scaling Laws for RM Overoptimization in DAAs (NeurIPS 2024, arXiv:2406.02900)](https://arxiv.org/abs/2406.02900)
